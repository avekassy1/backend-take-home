from unittest import TestCase

from src.schema.isa_allowance import Account, AccountType


class TestCustomIsaAllowanceCalculator(TestCase):
    """Key Rules:
    - Inherited ISAs may have different annual allowance rules
    - Custom limits should be configurable per account or client -> ye they shoud be
    - Consider how custom limits interact with standard limits
    - Design for extensibility to support various edge cases
    """

    def setUp(self):
        self.client_id = 1
        self.lifetime_account = Account(
            id=self.client_id, client_id=1, account_type=AccountType.Custom_ISA
        )
