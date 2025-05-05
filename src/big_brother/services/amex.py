import collections
import os
import httpx
import asyncio
from datetime import date
from dataclasses import dataclass
from typing import Dict, Optional
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from big_brother.parsers.common import Transaction
from big_brother.services.ynab_service import (
    convert_to_ynab_amount,
    create_transactions,
    get_ynab_transactions,
    find_account_id,
)


server = os.getenv("SELENIUM_SERVER", "http://localhost:4444")
username = os.getenv("AMEX_USERNAME")
password = os.getenv("AMEX_PASSWORD")
if not username or not password:
    raise ValueError("AMEX_USERNAME and AMEX_PASSWORD must be set")

accounts_url = "https://global.americanexpress.com/api/servicing/v1/member"
transactions_url = (
    "https://global.americanexpress.com/api/servicing/v1/financials/transactions"
)


@dataclass
class AmexAccount:
    account_token: str
    account_key: str


@dataclass
class AmexForeignDetails:
    amount: float
    iso_alpha_currency_code: str
    exchange_rate: float


@dataclass
class AmexTransaction:
    reference_id: str
    merchant_name: str
    # positive if expense, negative if income
    amount: float
    # Debit if expense, Credit if income
    type: str
    post_date: Optional[date]
    charge_date: date
    status: str
    foreign_details: Optional[AmexForeignDetails]


def get_amex_cookies() -> Dict[str, str]:
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--start-maximized")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
    )
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    driver = webdriver.Remote(command_executor=server, options=options)
    try:
        driver.get(
            "https://www.americanexpress.com/en-us/account/login/?inav=iNavLnkLog"
        )

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "eliloUserID"))
        )
        driver.find_element(By.ID, "eliloUserID").send_keys(username)
        driver.find_element(By.ID, "eliloPassword").send_keys(password)

        driver.find_element(By.ID, "loginSubmit").click()

        WebDriverWait(driver, 30).until(
            EC.url_contains("global.americanexpress.com/dashboard")
        )
        cookies = {cookie["name"]: cookie["value"] for cookie in driver.get_cookies()}
    finally:
        driver.quit()
    return cookies


def get_amex_accounts(cookies: Dict[str, str]):
    response = httpx.get(accounts_url, cookies=cookies)
    response.raise_for_status()
    return [
        AmexAccount(account["account_token"], account["account_key"])
        for account in response.json()["accounts"]
    ]


def parse_date(date_str: Optional[str]) -> Optional[date]:
    if date_str is None:
        return None
    return date.fromisoformat(date_str)


async def get_amex_transactions(
    cookies: Dict[str, str], account: AmexAccount, status: str, limit: int = 100
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                transactions_url,
                cookies=cookies,
                headers={
                    "account_token": account.account_token,
                },
                params={
                    "status": status,
                    "limit": limit,
                },
            )
            response.raise_for_status()
            transactions = response.json()["transactions"]
            return [
                AmexTransaction(
                    transaction["reference_id"],
                    transaction["extended_details"]["merchant"]["name"],
                    transaction["amount"],
                    transaction["type"],
                    parse_date(transaction.get("post_date")),
                    parse_date(transaction["charge_date"]),
                    status,
                    AmexForeignDetails(
                        transaction["foreign_details"]["amount"],
                        transaction["foreign_details"]["iso_alpha_currency_code"],
                        transaction["foreign_details"]["exchange_rate"],
                    )
                    if transaction.get("foreign_details")
                    else None,
                )
                for transaction in transactions
            ]
    except Exception as e:
        print(f"Error: {e}")
        return []


def convert_to_big_brother_transaction(transaction: AmexTransaction) -> Transaction:
    return Transaction(
        date=transaction.charge_date,
        amount=-1 * transaction.amount,
        payee=transaction.merchant_name,
        memo=f"{transaction.foreign_details.iso_alpha_currency_code} {transaction.foreign_details.amount}"
        if transaction.foreign_details
        else None,
        account="American Express",
        # this will ensure transactions get matched when posted transactions are eventually created
        import_id=f"bb-v2-{transaction.reference_id}"
        if transaction.status == "posted"
        else None,
        status="uncleared" if transaction.status == "pending" else "cleared",
    )


async def get_account_and_cookies() -> tuple[AmexAccount, Dict[str, str]]:
    cookies = get_amex_cookies()
    accounts = get_amex_accounts(cookies)
    if len(accounts) == 0:
        raise ValueError("No accounts found")
    return accounts[0], cookies


async def update_posted_transactions(account: AmexAccount, cookies: Dict[str, str]):
    posted = [
        convert_to_big_brother_transaction(transaction)
        for transaction in await get_amex_transactions(cookies, account, "posted")
    ]
    min_date = min(transaction.date for transaction in posted)
    ynab_transactions_import_ids = {
        transaction.import_id
        for transaction in get_ynab_transactions(min_date)
        if transaction.cleared == "cleared"
    }
    to_be_created_transactions = [
        transaction
        for transaction in posted
        if transaction.import_id not in ynab_transactions_import_ids
    ]
    print(f"Creating {len(to_be_created_transactions)} posted transactions in ynab")
    create_transactions(to_be_created_transactions)


async def update_pending_transactions(account: AmexAccount, cookies: Dict[str, str]):
    pending = [
        convert_to_big_brother_transaction(transaction)
        for transaction in await get_amex_transactions(cookies, account, "pending")
    ]
    min_date = min(transaction.date for transaction in pending)
    ynab_uncleared_transactions = [
        transaction
        for transaction in get_ynab_transactions(min_date)
        if transaction.cleared == "uncleared"
    ]
    frequency_of_transactions = collections.Counter(
        (transaction.account_id, transaction.var_date, transaction.amount)
        for transaction in ynab_uncleared_transactions
    )
    to_be_created_transactions = []
    # this ensures that we don't create duplicate transactions every hour
    for transaction in pending:
        unique_identifier = (
            find_account_id(transaction.account),
            transaction.date,
            convert_to_ynab_amount(transaction),
        )
        if frequency_of_transactions[unique_identifier] > 0:
            frequency_of_transactions[unique_identifier] -= 1
        else:
            to_be_created_transactions.append(transaction)
    print(f"Creating {len(to_be_created_transactions)} pending transactions in ynab")
    create_transactions(to_be_created_transactions)


async def monitor_amex():
    while True:
        try:
            print("Checking for AMEX transactions...")
            account, cookies = await get_account_and_cookies()
            await update_posted_transactions(account, cookies)
            await update_pending_transactions(account, cookies)
        except Exception as e:
            print(f"Error: {e}")
        # Check every hour
        await asyncio.sleep(1 * 60 * 60)


if __name__ == "__main__":
    asyncio.run(monitor_amex())
