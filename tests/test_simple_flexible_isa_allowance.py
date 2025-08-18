from decimal import Decimal
from unittest import TestCase
import datetime as dt

from src.schema.isa_allowance import Account, AccountType, Transaction
from src.service.isa_allowance import calculate_isa_allowance_for_account

class TestIsaAllowanceCalculator(TestCase):
# TODO - separate test classes for Step 2 and beyond
    def test_simple_flexible_isa_allowance_calculator(self):
        account = Account(id=1, client_id=1, account_type=AccountType.Flexible_ISA)
        transactions = [
            Transaction(account=account, amount=Decimal(5_000), transaction_date=dt.date(2024, 5, 10)),
            Transaction(account=account, amount=Decimal(10_000), transaction_date=dt.date(2024, 5, 10)),
            Transaction(account=account, amount=Decimal(-10_000), transaction_date=dt.date(2024, 5, 10)),
        ]
        allowance = calculate_isa_allowance_for_account(account=account, transactions=transactions, tax_year=2024)
        assert allowance.annual_allowance == Decimal(20_000)
        assert allowance.remaining_allowance == Decimal(15_000)