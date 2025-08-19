from abc import ABC, abstractmethod
from typing import List, Dict
from decimal import Decimal
from datetime import date

from ..schema.isa_allowance import (
    AccountType, IsaAllowance, NegativeBalanceError, Transaction
)

IsaLimitMapping = Dict[AccountType, Decimal]

def calculate_isa_allowance_for_account(
    client_id: int,
    transactions: List[Transaction],
    tax_year: int = 2024,
) -> IsaAllowance:
    """
    Main entrypoint for calculating the ISA allowance for a given account.
    """

    TAX_YEAR_START_DATE: date = date(tax_year, 4, 6)
    TAX_YEAR_END_DATE: date = date(tax_year + 1, 4, 5)

    isa_limits: IsaLimitMapping = get_isa_limits_for_tax_year(tax_year)
    annual_isa_allowance: Decimal = isa_limits.get(AccountType.ISA)
    # annual_flexible_isa_allowance: Decimal = isa_limits.get(AccountType.Flexible_Lifetime_ISA) 
    # remaining_lifetime_isa_allowance: Decimal = annual_flexible_isa_allowance
    
    client_transactions = filter_transactions_by_tax_year_and_client_id(client_id, transactions, TAX_YEAR_START_DATE, TAX_YEAR_END_DATE)
    client_transactions.sort(key=lambda t: t.transaction_date)

    calculators: Dict[AccountType, IsaAllowanceCalculator] = {}

    for transaction in client_transactions:

        account_type = transaction.account.account_type
        if account_type not in calculators:
            calculator_clazz = ISA_CALCULATOR_DISPATCHER.get(account_type)
            if calculator_clazz is None:
                raise NotImplementedError(f"No calculator implemented for account type: {account_type}")
            calculators[account_type] = calculator_clazz(isa_limits)
        
        calculators[account_type].process_transaction(transaction)
    
    total_contributions = sum(calc.total_contributions for calc in calculators.values())
    print("Total contributions: ", total_contributions)

    return IsaAllowance(
        annual_allowance=annual_isa_allowance,
        remaining_allowance=max(Decimal(0), annual_isa_allowance - total_contributions)
    )

class IsaAllowanceCalculator(ABC):
    def __init__(self, isa_limit_mappings: IsaLimitMapping):
        self.total_contributions = Decimal(0)
        self.flexible_contributions = Decimal(0)
        self.annual_isa_allowance = isa_limit_mappings.get(AccountType.ISA)
        self.INITIAL_LIFETIME_ALLOWANCE = isa_limit_mappings.get(AccountType.Flexible_Lifetime_ISA)
        self.remaining_lifetime_isa_allowance = self.INITIAL_LIFETIME_ALLOWANCE
        self.balance = Decimal(0)

    def process_transaction(self, transaction: Transaction):
        invested_amount = transaction.amount
        if self.balance + invested_amount < 0:
            raise NegativeBalanceError(self.balance + invested_amount)
        
        self.update_contributions(transaction)
        self.balance += invested_amount
        print(f"Calc's balance: {self.balance}\n")

    @abstractmethod
    def update_contributions(self, transaction: Transaction):
        pass

    def get_allowance(self) -> IsaAllowance:
        remaining = max(Decimal(0), self.annual_isa_allowance - self.total_contributions)
        return IsaAllowance(
            annual_allowance=self.annual_isa_allowance,
            remaining_allowance=remaining
        )
    
class NonFlexibleIsaCalculator(IsaAllowanceCalculator):
    def update_contributions(self, transaction: Transaction):
        if transaction.amount > 0:
            self.total_contributions += transaction.amount
        print(f"NON FLEXIBLE ISA. Total con: {self.total_contributions}, flexible con: {self.flexible_contributions}, remaining lisa: {self.remaining_lifetime_isa_allowance}")

class FlexibleIsaCalculator(IsaAllowanceCalculator):
    def update_contributions(self, transaction: Transaction):
        self.total_contributions += transaction.amount
        if transaction.amount > 0:
            self.flexible_contributions += transaction.amount
        print(f"FLEXIBLE ISA. Total con: {self.total_contributions}, flexible con: {self.flexible_contributions}, remaining lisa: {self.remaining_lifetime_isa_allowance}")

class FlexibleLifetimeIsaCalculator(IsaAllowanceCalculator):
    def update_contributions(self, transaction: Transaction):
        amount = transaction.amount

        self.flexible_contributions += amount
        
        if amount > 0:
            # Investment
            allowed = min(transaction.amount, self.remaining_lifetime_isa_allowance)
            self.remaining_lifetime_isa_allowance -= allowed
            self.total_contributions += allowed
        else:
            # Withdrawal
            non_tax_free_amount: Decimal = max(0, self.balance - self.INITIAL_LIFETIME_ALLOWANCE)
            restored = min(abs(amount), self.INITIAL_LIFETIME_ALLOWANCE - self.remaining_lifetime_isa_allowance) - non_tax_free_amount

            self.remaining_lifetime_isa_allowance += restored
            self.total_contributions -= restored

        print(f"LIFETIME ISA. Total con: {self.total_contributions}, flexible con: {self.flexible_contributions}, remaining lisa: {self.remaining_lifetime_isa_allowance}")

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
    
def filter_transactions_by_tax_year_and_client_id(client_id, transactions, TY_START_DATE, TY_END_DATE):
    client_transactions = [
        txn for txn in transactions
        if (TY_START_DATE < txn.transaction_date < TY_END_DATE 
            and txn.account.client_id == client_id)
    ]
    return client_transactions

# Dispatcher is easily extendible with new account types and corresponding IsaCalculators
ISA_CALCULATOR_DISPATCHER = {
    AccountType.ISA: NonFlexibleIsaCalculator,
    AccountType.Flexible_ISA: FlexibleIsaCalculator,
    AccountType.Flexible_Lifetime_ISA: FlexibleLifetimeIsaCalculator,
}

    # balance: Decimal = 0
    # total_contributions: Decimal = 0
    # flexible_contributions: Decimal = 0

    #     invested_amount: Decimal = transaction.amount # Can be negative -> withdrawal

    #     if (balance + invested_amount  < 0):
    #         raise NegativeBalanceError(balance + invested_amount)
        
    #     ##### Calculating Remaining Allowance #####
    #     account_type: AccountType = transaction.account.account_type
    #     calculator: BaseIsaCalculator = get_isa_account_calculator(account_type)
    #     # TODO - variables are passed down too many times, refactor as a Calculator object
    #     total_contributions, flexible_contributions, remaining_lifetime_isa_allowance = calculator.update_total_contributions(total_contributions, flexible_contributions, transaction, remaining_lifetime_isa_allowance)
    #     balance += invested_amount

    # return IsaAllowance(
    #     annual_allowance=annual_isa_allowance,
    #     remaining_allowance=max(0, annual_isa_allowance - total_contributions)
    # )

# TODO - write test for NotImplementedError
# def get_isa_account_calculator(account_type: AccountType) -> BaseIsaCalculator:
#     calculator_cls = ISA_CALCULATOR_DISPATCHER.get(account_type)
#     if calculator_cls is None:
#         raise NotImplementedError(f"No calculator implemented for account type: {account_type}")
#     return calculator_cls()
    
# class BaseIsaCalculator(ABC):
#     @abstractmethod
#     def update_total_contributions(
#         self, total_contributions: Decimal, flexible_contributions: Decimal, transaction: Transaction, remaining_lifetime_isa_allowance: Decimal
#     ):
#         pass

# class NonFlexibleIsaCalculator(BaseIsaCalculator):
#     def update_total_contributions(
#         self, total_contributions: Decimal, flexible_contributions: Decimal, transaction: Transaction, remaining_lifetime_isa_allowance: Decimal
#     ):
#         # Only positive amounts count towards the allowance for non-flexible
#         if transaction.amount > 0:
#             total_contributions += transaction.amount
#         return total_contributions, flexible_contributions, remaining_lifetime_isa_allowance

# class FlexibleIsaCalculator(BaseIsaCalculator):
#     def update_total_contributions(
#         self, total_contributions: Decimal, flexible_contributions: Decimal, transaction: Transaction, remaining_lifetime_isa_allowance: Decimal
#     ):
#         total_contributions += transaction.amount
#         # Both contributions and withdrawals affect total contributions
#         if transaction.amount > 0:
#             flexible_contributions += transaction.amount
#         return total_contributions, flexible_contributions, remaining_lifetime_isa_allowance

# class FlexibleLifetimeIsaCalculator(BaseIsaCalculator):
#     def update_total_contributions(
#         self, total_contributions: Decimal, flexible_contributions: Decimal, transaction: Transaction, remaining_lifetime_isa_allowance: Decimal
#     ):
#         # Calculate capped contribution
#         allowed = min(transaction.amount, remaining_lifetime_isa_allowance)
#         remaining_lifetime_isa_allowance -= allowed

#         total_contributions += transaction.amount
#          # Both contributions and withdrawals affect total contributions
#         if allowed > 0:
#             flexible_contributions += transaction.amount
#         # print("Amount vs remaining lifetime vs total contrib:\t", transaction.amount, remaining_lifetime_isa_allowance, total_contributions+allowed)
#         return total_contributions, flexible_contributions, remaining_lifetime_isa_allowance
