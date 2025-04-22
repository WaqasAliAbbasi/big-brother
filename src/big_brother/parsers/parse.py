from typing import Optional
from big_brother.parsers.common import Transaction
from big_brother.parsers.hsbc import parse_hsbc_email
from big_brother.parsers.mox import parse_mox_email
from big_brother.parsers.ios_wallet import parse_ios_wallet_email


def is_hsbc_email(email):
    return "HSBC Credit Card Transaction Notification" in email.subject


def is_mox_email(email):
    return "notify@mox.com" in email.body


def is_wallet_email(email):
    return "iOS Wallet" in email.subject


def parse_email(email) -> Optional[Transaction]:
    if is_hsbc_email(email):
        return parse_hsbc_email(email)
    elif is_mox_email(email):
        return parse_mox_email(email)
    elif is_wallet_email(email):
        return parse_ios_wallet_email(email)
    return None
