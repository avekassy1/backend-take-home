from decimal import Decimal
from unittest import TestCase
import datetime as dt

from src.schema.isa_allowance import Account, AccountType, Transaction
from src.service.isa_allowance import calculate_isa_allowance_for_account

class TestIsaAllowanceCalculator(TestCase):
    """ Key Rules:
    - Annual limit: £4,000 (2024/25 tax year)
    - Separate allowance from regular ISA allowance
    - Withdrawals restore contribution allowance (flexible behavior)
    """

    def setUp(self):
        self.client_id = 1
        self.lifetime_account = Account(id=self.client_id, client_id=1, account_type=AccountType.Flexible_Lifetime_ISA)

    def test_simple_lifetime_isa_allowance_calculator_with_unordered_transactions(self):
        transactions = [
            Transaction(account=self.lifetime_account, amount=Decimal(2_000), transaction_date=dt.date(2024, 5, 5)),
            Transaction(account=self.lifetime_account, amount=Decimal(2_000), transaction_date=dt.date(2024, 4, 28)),
            Transaction(account=self.lifetime_account, amount=Decimal(-3_000), transaction_date=dt.date(2024, 5, 10)),
        ]
        allowance = calculate_isa_allowance_for_account(client_id=self.client_id, transactions=transactions, tax_year=2024)
        assert allowance.annual_allowance == Decimal(20_000)
        assert allowance.remaining_allowance == Decimal(19_000)

    def test_simple_lifetime_isa_allowance_exhausted_then_reduced_back_below_limit(self):
        transactions = [
            Transaction(account=self.lifetime_account, amount=Decimal(5_000), transaction_date=dt.date(2024, 5, 5)),
            Transaction(account=self.lifetime_account, amount=Decimal(-2_000), transaction_date=dt.date(2024, 5, 6)), 
            Transaction(account=self.lifetime_account, amount=Decimal(1_500), transaction_date=dt.date(2024, 5, 7)), 
            Transaction(account=self.lifetime_account, amount=Decimal(-1_500), transaction_date=dt.date(2024, 5, 8)), 
        ]
        allowance = calculate_isa_allowance_for_account(client_id=self.client_id, transactions=transactions, tax_year=2024)
        assert allowance.annual_allowance == Decimal(20_000)
        assert allowance.remaining_allowance == Decimal(17_000)