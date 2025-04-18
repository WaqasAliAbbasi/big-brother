import re
from big_brother.services.mail import EmailMessage

from big_brother.parsers.common import Transaction

transaction_patterns = [
    (
        r".*You spent (HKD|USD)(.*) at (.*), earning.*",
        lambda m: (m.group(1), "-" + m.group(2), m.group(3)),
    ),
    (
        r".*You spent (HKD|USD)(.*) at (.*)\. Any doubt.*",
        lambda m: (m.group(1), "-" + m.group(2), m.group(3)),
    ),
    (
        r".*You transferred (HKD|USD)(.*) to (.*) on .*",
        lambda m: (m.group(1), "-" + m.group(2), m.group(3)),
    ),
    (
        r".*You've sent (HKD|USD)(.*) to (.*) successfully.*",
        lambda m: (m.group(1), "-" + m.group(2), m.group(3)),
    ),
    (
        r".*direct payment of (HKD|USD)(.*) to (.*) successfully",
        lambda m: (m.group(1), "-" + m.group(2), m.group(3)),
    ),
    (
        r".*(HKD|USD)(.*) merchant payment to (.*) on .*",
        lambda m: (m.group(1), "-" + m.group(2), m.group(3)),
    ),
    (
        r".*❤️ (.*) sent (HKD|USD)(.*) to you.*",
        lambda m: (m.group(2), m.group(3), m.group(1)),
    ),
]


def parse_mox_email(email: EmailMessage) -> Transaction:
    for pattern, processor in transaction_patterns:
        match = re.match(pattern, email.body, re.DOTALL)
        if match:
            currency, amount, payee = processor(match)
            amount = amount.replace(",", "")
            amount = float(amount)
            if currency == "USD":
                amount *= 7.78
            return Transaction(
                date=email.date.date(),
                payee=payee,
                account="Mox",
                amount=float(amount),
            )
    raise ValueError("Couldn't extract a transaction")
