import os
import ynab
import ynab.api
import ynab.api.accounts_api
import ynab.api.transactions_api
import ynab.api.user_api
import ynab.models
import ynab.models.account
import ynab.models.new_transaction
import ynab.models.patch_transactions_wrapper
import ynab.models.post_transactions_wrapper
import ynab.models.save_transaction_with_id_or_import_id
import ynab.models.transaction_detail
from functools import cache
from big_brother.parsers.common import Transaction
from datetime import date
from typing import Optional

access_token = os.environ.get("YNAB_API_KEY")
if not access_token:
    raise ValueError("Please set the YNAB_API_KEY environment variable.")

configuration = ynab.Configuration(access_token=access_token)


def get_accounts() -> list[ynab.models.account.Account]:
    with ynab.ApiClient(configuration) as api_client:
        accounts_api = ynab.AccountsApi(api_client)
        accounts_response = accounts_api.get_accounts(budget_id="last-used")
        return accounts_response.data.accounts


def get_ynab_transactions(
    since_date: Optional[date] = None,
) -> list[ynab.models.transaction_detail.TransactionDetail]:
    with ynab.ApiClient(configuration) as api_client:
        transactions_api = ynab.api.transactions_api.TransactionsApi(api_client)
        transactions_response = transactions_api.get_transactions(
            budget_id="last-used", since_date=since_date
        )
        return transactions_response.data.transactions


@cache
def find_account_id(account_name: str) -> str:
    accounts = get_accounts()
    for account in accounts:
        if account_name.lower() in account.name.lower():
            return account.id
    raise ValueError(f"Account {account_name} not found in YNAB.")


def convert_to_ynab_amount(transaction: Transaction) -> int:
    return int(transaction.amount * 1000)


def create_transactions(
    transactions: list[Transaction],
) -> list[ynab.models.transaction_detail.TransactionDetail]:
    if not transactions:
        return []
    with ynab.ApiClient(configuration) as api_client:
        transactions_api = ynab.TransactionsApi(api_client)
        transaction_response = transactions_api.create_transaction(
            budget_id="last-used",
            data=ynab.models.post_transactions_wrapper.PostTransactionsWrapper(
                transactions=[
                    ynab.models.new_transaction.NewTransaction(
                        account_id=find_account_id(transaction.account),
                        payee_name=transaction.payee,
                        memo=transaction.memo,
                        amount=convert_to_ynab_amount(transaction),
                        var_date=transaction.date,
                        cleared=transaction.status,
                        import_id=transaction.import_id,
                    )
                    for transaction in transactions
                ],
            ),
        )
        return transaction_response.data.transactions


if __name__ == "__main__":
    accounts = get_accounts()
    for account in accounts:
        print(f"Account ID: {account.id}, Name: {account.name}")
