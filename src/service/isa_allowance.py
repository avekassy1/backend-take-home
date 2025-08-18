from typing import List, Dict
from decimal import Decimal
from datetime import date

from ..schema.isa_allowance import (
    Account, IsaAllowance, Transaction, AccountType
)

IsaLimitMapping = Dict[AccountType, Decimal]

def calculate_isa_allowance_for_account(
    account: Account,
    transactions: List[Transaction],
    tax_year: int = 2024,
) -> IsaAllowance:
    """
    Main entrypoint for calculating the ISA allowance for a given account.
    """

    limits: IsaLimitMapping = get_isa_limits_for_tax_year(tax_year)

    # Step 1: Simple ISA (non-flexible)
    # Filter transactions by tax_year, sum up, return max(0, limits[account.account_type])
    # Withdrawal doesn't reset allowance

    start_date: date = date(tax_year, 4, 6)
    end_date: date = date(tax_year+1, 4, 5)

    remaining_allowance: Decimal = 0
    # Qs: Is for loop the most efficient way here?
    for transaction in transactions:
        ##### Generic Filtering #####
        if not (start_date < transaction.transaction_date < end_date):
            continue
        amount: Decimal = transaction.amount
        if (amount < 0):
            continue
            
        ##### Calculating Remaining Allowance #####
        # TODO: replace calculation with factory pattern - what if new AccountType is added
        match account.account_type:
            case AccountType.ISA:
                if (transaction.account != account):
                    continue
                remaining_allowance += amount
            case AccountType.Flexible_ISA:
                raise NotImplementedError
            case AccountType.Flexible_Lifetime_ISA:
                raise NotImplementedError

    annual_allowance: Decimal = limits.get(account.account_type)

    return IsaAllowance(
        annual_allowance=annual_allowance,
        remaining_allowance=max(0, annual_allowance - remaining_allowance)
    )


def get_isa_limits_for_tax_year(tax_year: int) -> IsaLimitMapping:
    """
    Get the ISA limits for different account types in a specific tax year.
    """

    if tax_year == 2024:
        return {
            AccountType.Flexible_ISA: Decimal("20_000.00"),
            AccountType.ISA: Decimal("20_000.00"),
            AccountType.Flexible_Lifetime_ISA: Decimal("4_000.00")
        }
    else:
        raise NotImplementedError(f"ISA limits not defined for the tax year: {tax_year}")
