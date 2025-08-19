from decimal import Decimal
from unittest import TestCase

import datetime as dt

from src.schema.isa_allowance import Account, AccountType, Transaction
from src.service.isa_allowance import calculate_isa_allowance_for_account

class TestIsaAllowanceCalculator(TestCase):
    """Key Rules:
    - Lifetime ISA contributions count towards the overall £20,000 ISA allowance
    - Client has separate £4,000 Lifetime ISA allowance AND reduced regular ISA allowance
    - If £4,000 contributed to Lifetime ISA, only £16,000 remains for regular ISAs
    - Design considerations for cross-account allowance calculations
    """
    def setUp(self):
        self.client_id = 1
        self.nonflex_account = Account(id=1, client_id=self.client_id, account_type=AccountType.ISA)
        self.flex_account = Account(id=2, client_id=self.client_id, account_type=AccountType.Flexible_ISA)
        self.lifetime_account = Account(id=3, client_id=self.client_id, account_type=AccountType.Flexible_Lifetime_ISA)

    def test_combination_of_flexible_nonflexible_and_lifetime_isa(self):
        transactions = [
            Transaction(account=self.flex_account, amount=Decimal(5_000), transaction_date=dt.date(2024, 4, 26)),
            Transaction(account=self.nonflex_account, amount=Decimal(1_000), transaction_date=dt.date(2024, 4, 27)),
            Transaction(account=self.lifetime_account, amount=Decimal(5_000), transaction_date=dt.date(2024, 4, 28)), # Exhausting 4k allowance
            Transaction(account=self.lifetime_account, amount=Decimal(-3_000), transaction_date=dt.date(2024, 4, 29)),
            Transaction(account=self.nonflex_account, amount=Decimal(-1_000), transaction_date=dt.date(2024, 4, 30)), # Does not affect remaining allowance
            Transaction(account=self.flex_account, amount=Decimal(-2_000), transaction_date=dt.date(2024, 5, 5)), # Restores allowance
        ]
        allowance = calculate_isa_allowance_for_account(client_id=self.client_id, transactions=transactions, tax_year=2024)
        assert allowance.annual_allowance == Decimal(20_000)
        assert allowance.remaining_allowance == Decimal(14_000)

    