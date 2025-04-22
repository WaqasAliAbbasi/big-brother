import re
from big_brother.services.mail import EmailMessage

from big_brother.parsers.common import (
    Transaction,
    convert_currency_to_hkd,
    currency_regex,
)

transaction_patterns = [
    (
        f".*You spent ({currency_regex})(.*) at (.*), earning.*",
        lambda m: (m.group(1), "-" + m.group(2), m.group(3)),
    ),
    (
        f".*You spent ({currency_regex})(.*) at (.*)\. Any doubt.*",
        lambda m: (m.group(1), "-" + m.group(2), m.group(3)),
    ),
    (
        f".*You transferred ({currency_regex})(.*) to (.*) on .*",
        lambda m: (m.group(1), "-" + m.group(2), m.group(3)),
    ),
    (
        f".*You've sent ({currency_regex})(.*) to (.*) successfully.*",
        lambda m: (m.group(1), "-" + m.group(2), m.group(3)),
    ),
    (
        f".*direct payment of ({currency_regex})(.*) to (.*) successfully",
        lambda m: (m.group(1), "-" + m.group(2), m.group(3)),
    ),
    (
        f".*({currency_regex})(.*) merchant payment to (.*) on .*",
        lambda m: (m.group(1), "-" + m.group(2), m.group(3)),
    ),
    (
        f".*❤️ (.*) sent ({currency_regex})(.*) to you.*",
        lambda m: (m.group(2), m.group(3), m.group(1)),
    ),
]


def parse_mox_email(email: EmailMessage) -> Transaction:
    for pattern, processor in transaction_patterns:
        match = re.match(pattern, email.body, re.DOTALL)
        if match:
            currency, amount, payee = processor(match)
            amount = float(amount.replace(",", ""))
            return Transaction(
                date=email.date.date(),
                payee=payee,
                account="Mox",
                amount=convert_currency_to_hkd(currency, amount),
            )
    raise ValueError("Couldn't extract a transaction")
