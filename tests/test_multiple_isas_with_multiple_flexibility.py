from decimal import Decimal
from unittest import TestCase
import datetime as dt

from src.schema.isa_allowance import Account, AccountType, Transaction
from src.service.isa_allowance import calculate_isa_allowance_for_account

class TestIsaAllowanceCalculator(TestCase):
    """ Key Rules:
    - Combined ISA limit of £20,000 applies across all ISA accounts
    - Flexible account withdrawals can restore allowance for either account
    - Non-flexible account withdrawals permanently reduce total allowance
    """
    def setUp(self):
        self.client_id = 1
        self.nonflex_account = Account(id=1, client_id=self.client_id, account_type=AccountType.ISA)
        self.flex_account = Account(id=2, client_id=self.client_id, account_type=AccountType.Flexible_ISA)

    def test_combining_flexible_and_nonflexible_isas(self):
        # TODO - add unordered transactions
        transactions = [
            Transaction(account=self.flex_account, amount=Decimal(10_000), transaction_date=dt.date(2024, 5, 10)),
            Transaction(account=self.nonflex_account, amount=Decimal(5_000), transaction_date=dt.date(2024, 4, 27)), # Transaction with unordered date
            Transaction(account=self.flex_account, amount=Decimal(-3_000), transaction_date=dt.date(2024, 4, 28)), # Restores allowance
            Transaction(account=self.flex_account, amount=Decimal(-4_000), transaction_date=dt.date(2024, 5, 10)), # Restores allowance
            Transaction(account=self.nonflex_account, amount=Decimal(-5_000), transaction_date=dt.date(2024, 5, 10)), # Does not affect allowance
        ]
        # Multiple accounts?
        allowance = calculate_isa_allowance_for_account(client_id=self.client_id, transactions=transactions, tax_year=2024)
        assert allowance.annual_allowance == Decimal(20_000)
        assert allowance.remaining_allowance == Decimal(12_000)
