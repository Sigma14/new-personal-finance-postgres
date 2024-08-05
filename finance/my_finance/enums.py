from enum import Enum


class BudgetPeriods(Enum):
    """
        Enum representing different budget periods.

        Attributes:
            DAILY (str): Represents daily budget period.
            WEEKLY (str): Represents weekly budget period.
            MONTHLY (str): Represents monthly budget period.
            QUARTERLY (str): Represents quarterly budget period.
            YEARLY (str): Represents yearly budget period.
    """
    DAILY = 'Daily'
    WEEKLY = 'Weekly'
    MONTHLY = 'Monthly'
    QUARTERLY = 'Quarterly'
    YEARLY = 'Yearly'


class CategoryTypes(Enum):
    """
        Enum representing different category types for budgets.

        Attributes:
            BILLS_AND_SUBSCRIPTIONS (str): Represents bills and subscriptions category.
            FUNDS (str): Represents funds category.
            GOALS (str): Represents goals category.
            INCOME (str): Represents income category.
            NON_MONTHLY (str): Represents non-monthly expenses category.
    """
    BILLS_AND_SUBSCRIPTIONS = 'Bills & Subscriptions'
    FUNDS = 'Funds'
    GOALS = 'Goals'
    INCOME = 'Income'
    NON_MONTHLY = 'Non-Monthly'


class AccountTypes(Enum):
    """
        Enum representing different account types.

        Attributes:
            SAVINGS (str): Represents savings account type.
            CASH (str): Represents cash account type.
            CHECKING (str): Represents checking account type.
            LOC (str): Represents line of credit account type.
            EF (str): Represents emergency fund account type.
            CREDIT (str): Represents credit card account type.
    """
    SAVINGS = 'Savings'
    CASH = 'Cash'
    CHECKING = 'Checking'
    LOC = 'Line of Credit'
    EF = 'Emergency Fund'
    CREDIT = 'Credit Card'
