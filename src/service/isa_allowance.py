from abc import ABC, abstractmethod
from typing import List, Dict
from decimal import Decimal
from datetime import date

from ..schema.isa_allowance import (
    Account, AccountType, IsaAllowance, NegativeBalanceError, Transaction
)

IsaLimitMapping = Dict[AccountType, Decimal]

def calculate_isa_allowance_for_account(
    client_id: int, # TODO - enable multiple accounts or change and have client id
    transactions: List[Transaction],
    tax_year: int = 2024,
) -> IsaAllowance:
    """
    Main entrypoint for calculating the ISA allowance for a given account.
    """

    isa_limits: IsaLimitMapping = get_isa_limits_for_tax_year(tax_year)

    TY_START_DATE: date = date(tax_year, 4, 6)
    TY_END_DATE: date = date(tax_year + 1, 4, 5)

    annual_isa_allowance: Decimal = isa_limits.get(AccountType.ISA)
    # annual_lifetime_isa_allowance - will come at Step 4
    
    # TODO - extract filtering to function
    client_transactions = [
        txn for txn in transactions
        if (TY_START_DATE < txn.transaction_date < TY_END_DATE 
            and txn.account.client_id == client_id)
    ]
    client_transactions.sort(key=lambda t: t.transaction_date)

    balance: Decimal = 0
    total_contributions: Decimal = 0

    for transaction in client_transactions:
        invested_amount: Decimal = transaction.amount

        if (balance + invested_amount  < 0):
            raise NegativeBalanceError(balance + invested_amount)
        
        ##### Calculating Remaining Allowance #####
        account_type: AccountType = transaction.account.account_type
        calculator: BaseIsaCalculator = get_isa_account_calculator(account_type)
        total_contributions = calculator.update_total_contributions(total_contributions, transaction)
        balance += invested_amount

    return IsaAllowance(
        annual_allowance=annual_isa_allowance,
        remaining_allowance=max(0, annual_isa_allowance - total_contributions)
    )


def get_isa_limits_for_tax_year(tax_year: int) -> IsaLimitMapping:
    """
    Get the ISA limits for different account types in a specific tax year.
    """

    # TODO: make this extendible (HashMap -> dict in python) + write tests
    if tax_year == 2024:
        return {
            AccountType.Flexible_ISA: Decimal("20_000.00"),
            AccountType.ISA: Decimal("20_000.00"),
            AccountType.Flexible_Lifetime_ISA: Decimal("4_000.00")
        }
    else:
        raise NotImplementedError(f"ISA limits not defined for the tax year: {tax_year}")
    
class BaseIsaCalculator(ABC):
    @abstractmethod
    def update_total_contributions(self, total_contributions, transaction):
        pass

class NonFlexibleIsaCalculator(BaseIsaCalculator):
    def update_total_contributions(self, total_contributions, transaction):
        # Only positive amounts count towards the allowance for non-flexible
        if transaction.amount > 0:
            return total_contributions + transaction.amount
        return total_contributions

class FlexibleIsaCalculator(BaseIsaCalculator):
    def update_total_contributions(self, total_contributions, transaction):
        # All amounts (positive or negative) affect the allowance for flexible
        return total_contributions + transaction.amount

class FlexibleLifetimeIsaCalculator(BaseIsaCalculator):
    def update_total_contributions(self, total_contributions, transaction):
        raise NotImplementedError("Flexible Lifetime ISA behavior not implemented yet.")

# Dispatcher is easily extendible with new account types and corresponding IsaCalculators
ISA_CALCULATOR_DISPATCHER = {
    AccountType.ISA: NonFlexibleIsaCalculator,
    AccountType.Flexible_ISA: FlexibleIsaCalculator,
    AccountType.Flexible_Lifetime_ISA: FlexibleLifetimeIsaCalculator,
}

# TODO - write test for NotImplementedError
# TODO - monitor test coverage
def get_isa_account_calculator(account_type: AccountType) -> BaseIsaCalculator:
    calculator_cls = ISA_CALCULATOR_DISPATCHER.get(account_type)
    if calculator_cls is None:
        raise NotImplementedError(f"No calculator implemented for account type: {account_type}")
    return calculator_cls()
