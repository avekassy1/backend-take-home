from decimal import Decimal
from unittest import TestCase
import datetime as dt
import pytest

from src.schema.isa_allowance import Account, AccountType, Transaction
from src.service.isa_allowance import calculate_isa_allowance_for_account

class TestIsaAllowanceCalculator(TestCase):
    """ Key Rules:
    - Annual limit: £20,000 (2024/25 tax year)
    - Withdrawals restore contribution allowance (can re-contribute withdrawn amounts)
    - Track net contributions vs. allowable contributions including restored amounts
    """

    def setUp(self):
        self.account = Account(id=1, client_id=1, account_type=AccountType.Flexible_ISA)

    def test_simple_flexible_isa_allowance_calculator_with_unordered_transactions(self):
        transactions = [
            Transaction(account=self.account, amount=Decimal(5_000), transaction_date=dt.date(2024, 5, 10)),
            Transaction(account=self.account, amount=Decimal(5_000), transaction_date=dt.date(2024, 4, 28)),
            Transaction(account=self.account, amount=Decimal(5_000), transaction_date=dt.date(2024, 5, 10)),
            Transaction(account=self.account, amount=Decimal(-10_000), transaction_date=dt.date(2024, 5, 10)),
        ]
        allowance = calculate_isa_allowance_for_account(client_id=1, transactions=transactions, tax_year=2024)
        assert allowance.annual_allowance == Decimal(20_000)
        assert allowance.remaining_allowance == Decimal(15_000)

    def test_withdrawal_restoring_allowance_from_zero(self):
        transactions = [
                Transaction(account=self.account, amount=Decimal(25_000), transaction_date=dt.date(2024, 5, 10)),
                Transaction(account=self.account, amount=Decimal(-10_000), transaction_date=dt.date(2024, 5, 10)),
            ]
        allowance = calculate_isa_allowance_for_account(client_id=1, transactions=transactions, tax_year=2024)
        assert allowance.annual_allowance == Decimal(20_000)
        assert allowance.remaining_allowance == Decimal(5_000)