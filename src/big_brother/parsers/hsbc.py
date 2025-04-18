from big_brother.parsers.common import Transaction
from big_brother.services.mail import EmailMessage
from datetime import datetime


def parse_hsbc_email(email: EmailMessage) -> Transaction:
    credit_card_number = None
    merchant = None
    # 18 Apr
    date = None
    amount = None
    for line in email.body_lines:
        if line.startswith("Credit card number"):
            credit_card_number = line.replace("Credit card number", "").strip()
        elif line.startswith("Merchant"):
            merchant = line.replace("Merchant", "").strip()
        elif line.startswith("Date"):
            date = line.replace("Date", "").strip()
            date = datetime.strptime(date, "%d %b").date()
        elif line.startswith("Amount") and "HKD" in line:
            amount = line.replace("Amount", "").strip()
            amount = amount.replace("HKD", "").strip()
            amount = amount.replace(",", "").strip()
            amount = -1 * float(amount)

    if credit_card_number and merchant and amount:
        return Transaction(
            account="Visa Signature",
            payee=merchant,
            date=email.date.date(),
            amount=amount,
        )
    raise ValueError("Missing required fields in email")
