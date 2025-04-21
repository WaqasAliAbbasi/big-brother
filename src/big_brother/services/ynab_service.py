import os
import uuid
import ynab
import ynab.models
import ynab.models.account
import ynab.models.new_transaction
import ynab.models.post_transactions_wrapper
import ynab.models.transaction_detail

from big_brother.parsers.common import Transaction

access_token = os.environ.get("YNAB_API_KEY")
if not access_token:
    raise ValueError("Please set the YNAB_API_KEY environment variable.")

configuration = ynab.Configuration(access_token=access_token)


def get_accounts() -> list[ynab.models.account.Account]:
    with ynab.ApiClient(configuration) as api_client:
        accounts_api = ynab.AccountsApi(api_client)
        accounts_response = accounts_api.get_accounts(budget_id="last-used")
        return accounts_response.data.accounts


def find_account_id(transaction: Transaction) -> str:
    accounts = get_accounts()
    for account in accounts:
        if transaction.account.lower() in account.name.lower():
            return account.id
    raise ValueError(f"Account {transaction.account} not found in YNAB.")


def submit_transaction(
    transaction: Transaction,
) -> ynab.models.transaction_detail.TransactionDetail:
    with ynab.ApiClient(configuration) as api_client:
        transactions_api = ynab.TransactionsApi(api_client)
        transaction_response = transactions_api.create_transaction(
            budget_id="last-used",
            data=ynab.models.post_transactions_wrapper.PostTransactionsWrapper(
                transaction=ynab.models.new_transaction.NewTransaction(
                    account_id=find_account_id(transaction),
                    payee_name=transaction.payee,
                    amount=int(transaction.amount * 1000),
                    var_date=transaction.date,
                    cleared="uncleared",
                    approved=False,
                    # to make it look like a imported transaction
                    import_id=str(uuid.uuid4()),
                )
            ),
        )
        return transaction_response.data.transaction


if __name__ == "__main__":
    accounts = get_accounts()
    for account in accounts:
        print(f"Account ID: {account.id}, Name: {account.name}")
