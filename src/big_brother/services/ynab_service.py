import os
import ynab
import ynab.api
import ynab.api.transactions_api
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


def get_transactions(
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
                        amount=int(transaction.amount * 1000),
                        var_date=transaction.date,
                        cleared=transaction.status,
                        import_id=transaction.import_id,
                    )
                    for transaction in transactions
                ],
            ),
        )
        return transaction_response.data.transactions


def update_transactions(transactions: list[Transaction]):
    if not transactions:
        return []
    with ynab.ApiClient(configuration) as api_client:
        transactions_api = ynab.TransactionsApi(api_client)
        transactions_api.update_transactions(
            budget_id="last-used",
            data=ynab.models.patch_transactions_wrapper.PatchTransactionsWrapper(
                transactions=[
                    ynab.models.save_transaction_with_id_or_import_id.SaveTransactionWithIdOrImportId(
                        import_id=transaction.import_id,
                        account_id=find_account_id(transaction.account),
                        amount=int(transaction.amount * 1000),
                        cleared=transaction.status,
                    )
                    for transaction in transactions
                ]
            ),
        )


def upsert_transactions(transactions: list[Transaction]):
    earliest_date = min(transaction.date for transaction in transactions)
    ynab_transactions = get_transactions(earliest_date)
    ynab_transactions_by_import_id = {
        transaction.import_id: transaction for transaction in ynab_transactions
    }

    to_be_created_transactions = [
        transaction
        for transaction in transactions
        if transaction.import_id not in ynab_transactions_by_import_id
    ]
    if to_be_created_transactions:
        print(f"Creating {len(to_be_created_transactions)} new transactions...")
        create_transactions(to_be_created_transactions)

    to_be_updated_transactions = [
        transaction
        for transaction in transactions
        if transaction.import_id in ynab_transactions_by_import_id
    ]
    if to_be_updated_transactions:
        print(f"Updating {len(to_be_updated_transactions)} transactions...")
        update_transactions(to_be_updated_transactions)


if __name__ == "__main__":
    accounts = get_accounts()
    for account in accounts:
        print(f"Account ID: {account.id}, Name: {account.name}")
