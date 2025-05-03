import re
import uuid
from big_brother.parsers.common import (
    Transaction,
    currency_regex,
    convert_currency_to_hkd,
)
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
        elif line.startswith("Amount"):
            amount = line.replace("Amount", "").strip()
            regex = f"({currency_regex})(.*)"
            currency, amount = re.match(regex, amount).groups()
            amount = float("-" + amount.replace(",", "").strip())

    if credit_card_number and merchant and amount:
        converted = convert_currency_to_hkd(currency, amount)
        return Transaction(
            account="Visa Signature",
            payee=merchant,
            date=email.date.date(),
            amount=converted,
            memo=f"Original: {currency} {amount}" if converted != amount else None,
            import_id=str(uuid.uuid4()),
        )
    raise ValueError("Missing required fields in email")
