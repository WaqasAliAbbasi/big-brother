from dataclasses import dataclass
from datetime import date


@dataclass
class Transaction:
    date: date
    payee: str
    account: str
    amount: float


currency_regex = "HKD|HK\$|USD|\$|JPY|¥|GBP|£"

currency_rates = {
    "HKD": 1,
    "HK$": 1,
    "USD": 7.78,
    "$": 7.78,
    "JPY": 0.055,
    "¥": 0.055,
    "GBP": 10,
    "£": 10,
}


def convert_currency_to_hkd(currency: str, amount: float) -> float:
    if currency not in currency_rates:
        raise ValueError("Unsupported currency")
    return round(amount * currency_rates[currency], 2)
