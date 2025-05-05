from typing import Optional
from big_brother.parsers.common import Transaction
from big_brother.parsers.hsbc import parse_hsbc_email, is_hsbc_email
from big_brother.parsers.mox import parse_mox_email, is_mox_email
from big_brother.parsers.ios_wallet import parse_ios_wallet_email, is_wallet_email


def parse_email(email) -> Optional[Transaction]:
    if is_hsbc_email(email):
        return parse_hsbc_email(email)
    elif is_mox_email(email):
        return parse_mox_email(email)
    elif is_wallet_email(email):
        return parse_ios_wallet_email(email)
    return None
