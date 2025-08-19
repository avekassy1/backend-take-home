from decimal import Decimal
from unittest import TestCase
import datetime as dt

from src.schema.isa_allowance import Account, AccountType, Transaction
from src.service.isa_allowance import calculate_isa_allowance_for_account

class TestCustomIsaAllowanceCalculator(TestCase):
    """Key Rules:
    - Inherited ISAs may have different annual allowance rules
    - Custom limits should be configurable per account or client -> ye they shoud be
    - Consider how custom limits interact with standard limits
    - Design for extensibility to support various edge cases
    """
    def setUp(self):
        self.client_id = 1
        self.lifetime_account = Account(id=self.client_id, client_id=1, account_type=AccountType.Custom_ISA)

    