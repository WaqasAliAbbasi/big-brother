import re
from big_brother.parsers.common import (
    Transaction,
    convert_currency_to_hkd,
    currency_regex,
)
from big_brother.services.mail import EmailMessage


def get_account_name(account: str) -> str:
    card_name = account.replace("Card", "").strip()
    if "American Express" in card_name:
        return "American Express"
    return card_name


def parse_ios_wallet_email(email: EmailMessage) -> Transaction:
    regex = f".*You spent ({currency_regex})(.*) at (.*) using (.*) card.*"
    match = re.match(regex, email.body, re.DOTALL)
    if not match:
        raise ValueError("Couldn't extract a transaction")
    currency, amount, payee, account = match.groups()
    amount = float("-" + amount.replace(",", ""))
    converted = convert_currency_to_hkd(currency, amount)
    return Transaction(
        date=email.date.date(),
        payee=payee,
        account=get_account_name(account),
        amount=converted,
        memo=f"Original: {currency} {amount}" if converted != amount else None,
        mark_as_import=False,
    )
