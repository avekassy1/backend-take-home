from typing import List, Dict
from decimal import Decimal
from datetime import date

from ..schema.isa_allowance import (
    Account, AccountType, IsaAllowance, NegativeBalanceError, Transaction
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

    isa_limits: IsaLimitMapping = get_isa_limits_for_tax_year(tax_year)

    TY_START_DATE: date = date(tax_year, 4, 6)
    TY_END_DATE: date = date(tax_year + 1, 4, 5)

    annual_allowance: Decimal = isa_limits.get(account.account_type)
    total_amount_invested: Decimal = 0 # This looks logically bad

    # Qs: Is for loop the most efficient way here?
    for transaction in transactions:
        ##### Generic Filtering #####
        if not (TY_START_DATE < transaction.transaction_date < TY_END_DATE):
            continue
        if (transaction.account != account):
            continue
        invested_amount: Decimal = transaction.amount
        if (total_amount_invested + invested_amount  < 0):
            raise NegativeBalanceError(total_amount_invested + invested_amount)
            
        ##### Calculating Remaining Allowance #####
        # TODO: replace if-else cavalcade with factory pattern - what if new AccountType is added
        match account.account_type:
            case AccountType.ISA:
                if (invested_amount > 0):
                    total_amount_invested += invested_amount
            case AccountType.Flexible_ISA:
                total_amount_invested += invested_amount
            case AccountType.Flexible_Lifetime_ISA:
                raise NotImplementedError


    return IsaAllowance(
        annual_allowance=annual_allowance,
        remaining_allowance=max(0, annual_allowance - total_amount_invested)
    )


def get_isa_limits_for_tax_year(tax_year: int) -> IsaLimitMapping:
    """
    Get the ISA limits for different account types in a specific tax year.
    """

    # TODO: make this extendible + write tests
    if tax_year == 2024:
        return {
            AccountType.Flexible_ISA: Decimal("20_000.00"),
            AccountType.ISA: Decimal("20_000.00"),
            AccountType.Flexible_Lifetime_ISA: Decimal("4_000.00")
        }
    else:
        raise NotImplementedError(f"ISA limits not defined for the tax year: {tax_year}")