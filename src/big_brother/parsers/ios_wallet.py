import re
from big_brother.parsers.common import Transaction
from big_brother.services.mail import EmailMessage


def parse_ios_wallet_email(email: EmailMessage) -> Transaction:
    email.body = email.body.replace("HK$", "HKD")
    regex = r"You spent (HKD|USD)(.*) at (.*) using (.*)"
    match = re.match(regex, email.body, re.DOTALL)
    if not match:
        raise ValueError("Couldn't extract a transaction")
    currency, amount, payee, account = match.groups()
    amount = "-" + amount.replace(",", "")
    amount = float(amount)
    if currency == "USD":
        amount *= 7.78
    return Transaction(
        date=email.date.date(),
        payee=payee,
        account=account.replace("Card", "").strip(),
        amount=amount,
    )
