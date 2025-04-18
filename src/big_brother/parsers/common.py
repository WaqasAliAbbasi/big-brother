from dataclasses import dataclass
from datetime import date


@dataclass
class Transaction:
    date: date
    payee: str
    account: str
    amount: float
