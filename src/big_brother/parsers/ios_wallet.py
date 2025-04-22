import re
from big_brother.parsers.common import (
    Transaction,
    convert_currency_to_hkd,
    currency_regex,
)
from big_brother.services.mail import EmailMessage


def parse_ios_wallet_email(email: EmailMessage) -> Transaction:
    regex = f"You spent ({currency_regex})(.*) at (.*) using (.*)"
    match = re.match(regex, email.body, re.DOTALL)
    if not match:
        raise ValueError("Couldn't extract a transaction")
    currency, amount, payee, account = match.groups()
    amount = float("-" + amount.replace(",", ""))
    return Transaction(
        date=email.date.date(),
        payee=payee,
        account=account.replace("Card", "").strip(),
        amount=convert_currency_to_hkd(currency, amount),
    )
