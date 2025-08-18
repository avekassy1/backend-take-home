from decimal import Decimal
from unittest import TestCase
import datetime as dt

from src.schema.isa_allowance import Account, AccountType, Transaction
from src.service.isa_allowance import calculate_isa_allowance_for_account

class TestIsaAllowanceCalculator(TestCase):

    def setUp(self):
        self.account = Account(id=1, client_id=1, account_type=AccountType.ISA)
        self.other_account = Account(id=2, client_id=2, account_type=AccountType.Flexible_ISA)

    def test_simple_non_flexible_isa_allowance_calculator(self):
        """ Test cases covered
        - Regular, in-year transactions
        - Negative transactions (withdrawals)
        - Transactions from another tax year
        - Transactions by another account
        """

        transactions = [
            Transaction(account=self.account, amount=Decimal(5_000), transaction_date=dt.date(2024, 5, 10)),
            Transaction(account=self.account, amount=Decimal(10_000), transaction_date=dt.date(2024, 5, 10)),
            Transaction(account=self.account, amount=Decimal(-10_000), transaction_date=dt.date(2024, 5, 10)), # should be ignored
            Transaction(account=self.account, amount=Decimal(9_250), transaction_date=dt.date(2021, 5, 10)), # should be ignored
            Transaction(account=self.other_account, amount=Decimal(9_250), transaction_date=dt.date(2024, 5, 10)), # should be ignored
            # What happened to type validation here?
            # Transaction(account=account, amount=int(8), transaction_date=dt.date(2021, 5, 10)),
        ]
        allowance = calculate_isa_allowance_for_account(account=self.account, transactions=transactions, tax_year=2024)
        assert allowance.annual_allowance == Decimal(20_000)
        assert allowance.remaining_allowance == Decimal(5_000)

    def test_simple_non_flexible_exhausting_allowance(self):
        transactions = [
            Transaction(account=self.account, amount=Decimal(21_000), transaction_date=dt.date(2024, 5, 10)),
        ]
        allowance = calculate_isa_allowance_for_account(account=self.account, transactions=transactions, tax_year=2024)
        assert allowance.annual_allowance == Decimal(20_000)
        assert allowance.remaining_allowance == Decimal(0)

    # TODO: Error cases for account creation?