from decimal import Decimal
from unittest import TestCase
import datetime as dt
import pytest

from src.schema.isa_allowance import Account, AccountType, NegativeBalanceError, Transaction
from src.service.isa_allowance import calculate_isa_allowance_for_account

class TestIsaAllowanceCalculator(TestCase):
    def setUp(self):
        self.client_id = 1
        self.implemented_account = Account(id=self.client_id, client_id=1, account_type=AccountType.Flexible_ISA)
        self.unimplemented_account = Account(id=self.client_id, client_id=1, account_type=AccountType.Not_Implemented_ISA)
    
    def test_simple_lifetime_isa_allowance_calculator_with_unordered_transactions(self):
        transactions = [
            Transaction(account=self.unimplemented_account, amount=Decimal(2_000), transaction_date=dt.date(2024, 5, 5)),
        ]
        with pytest.raises(NotImplementedError):
            calculate_isa_allowance_for_account(client_id=1, transactions=transactions, tax_year=2024)


    def test_withdrawals_creating_negative_account_balance(self):
        transactions = [
            Transaction(account=self.implemented_account, amount=Decimal(5_000), transaction_date=dt.date(2024, 5, 10)),
            Transaction(account=self.implemented_account, amount=Decimal(-10_000), transaction_date=dt.date(2024, 5, 10)),
        ]
        with pytest.raises(NegativeBalanceError):
            calculate_isa_allowance_for_account(client_id=1, transactions=transactions, tax_year=2024)

    def test_year_other_than_2024(self):
        with pytest.raises(NotImplementedError):
            calculate_isa_allowance_for_account(client_id=1, transactions=[], tax_year=2020)

    # TODO - zero transactions inputted