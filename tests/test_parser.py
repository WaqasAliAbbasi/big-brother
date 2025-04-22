import json
import pytest
from datetime import datetime
from big_brother.services.mail import EmailMessage
from big_brother.parsers.parse import parse_email

current_path = __file__.rsplit("/", 1)[0]
test_cases_path = f"{current_path}/parser_test_cases.json"
with open(test_cases_path, "r") as f:
    test_cases = json.load(f)


@pytest.mark.parametrize("test_case", test_cases)
def test_parser(test_case):
    email = EmailMessage(
        uid="0",
        subject=test_case["subject"],
        body=test_case["body"],
        date=datetime.fromisoformat(test_case["date"]),
        from_address=test_case["from_address"],
        body_lines=test_case["body"].splitlines(),
    )
    transaction = parse_email(email)
    assert transaction.payee == test_case["expected"]["payee"]
    assert transaction.amount == test_case["expected"]["amount"]
    assert transaction.account == test_case["expected"]["account"]
