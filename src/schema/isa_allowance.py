import enum
from decimal import Decimal

from pydantic import BaseModel
import datetime as dt

class AccountType(enum.Enum):
    ISA = enum.auto()  # non-flexible
    Flexible_ISA = enum.auto()
    Flexible_Lifetime_ISA = enum.auto()

class Account(BaseModel):
    id: int
    client_id: int
    account_type: AccountType

class Transaction(BaseModel):
    account: Account
    transaction_date: dt.date
    amount: Decimal

class TotalLimit(BaseModel):
    tax_year: str
    total_limit: Decimal

class IsaAllowance(BaseModel):
    annual_allowance: Decimal
    remaining_allowance: Decimal

class NegativeBalanceError(Exception):
    """Exception raised when an ISA account balance goes negative."""

    def __init__(self, balance, message="Account balance cannot go negative"):
        self.balance = balance
        self.message = message
        super().__init__(f"{message}: Balance is {balance}")
