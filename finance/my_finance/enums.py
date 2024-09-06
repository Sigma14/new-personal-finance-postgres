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

    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    QUARTERLY = "Quarterly"
    YEARLY = "Yearly"

    @classmethod
    def list(cls):
        """Class method to list all budget periods"""
        return list(map(lambda member: member.value, cls))


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

    BILLS_AND_SUBSCRIPTIONS = "Bills & Subscriptions"
    FUNDS = "Funds"
    GOALS = "Goals"
    INCOME = "Income"
    NON_MONTHLY = "Non-Monthly"

    @classmethod
    def list(cls):
        """Class method to list all categories"""
        return list(map(lambda member: member.value, cls))


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

    SAVINGS = "Savings"
    CASH = "Cash"
    CHECKING = "Checking"
    LOC = "Line of Credit"
    EF = "Emergency Fund"
    CREDIT = "Credit Card"

    @classmethod
    def list(cls):
        """Class method to list all account types"""
        return list(map(lambda member: member.value, cls))


# To-do Invoice status
class InvoiceStatuses(Enum):
    """
    Enumeration for various invoice statuses:

    - PARTIALLY: Indicates that the invoice is partially paid.
    - FULLY: Indicates that the invoice is fully paid.
    - UNPAID: Indicates that the invoice is not paid.
    - OVERDUE: Indicates that the invoice is overdue.
    """

    PARTIALLY = "Partially Paid"
    FULLY = "Fully Paid"
    UNPAID = "Unpaid"
    OVERDUE = "Overdue"


class DateFormats(Enum):
    """
    Enumeration for various date formats:

    - YYYY_MM_DD: Year-Month-Day format (e.g., 2024-08-06)
    - MONTH_DD_YYYY: Full month name, Day, Year format (e.g., August 06, 2024)
    - DD_MON_YYYY: Day-Short month name-Year format (e.g., 06-Aug-2024)
    - MON_YYYY: Short month name-Year format (e.g., Aug-2024)
    - MON_DD_YYYY: Short month name Day, Year format (e.g., Aug 06, 2024)
    - DD_MM_YYYY: Day-Month-Year format (e.g., 06-08-2024)
    - YYYY_MM: Year-Month format (e.g., 2024-08)
    """

    YYYY_MM_DD = "%Y-%m-%d"
    MONTH_DD_YYYY = "%B %d, %Y"
    DD_MON_YYYY = "%d-%b-%Y"
    MON_YYYY = "%b-%Y"
    MON_DD_YYYY = "%b %d, %Y"
    DD_MM_YYYY = "%d-%m-%Y"
    YYYY_MM = "%Y-%m"
