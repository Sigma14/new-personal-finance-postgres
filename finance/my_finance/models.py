# from django.db import models
from ast import mod
import datetime
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from djongo import models
from django.utils.timezone import now

from .constants import (
    BUDGET_ACCOUNT_TYPES,
    BUDGET_PERIODS,
    CURRENCIES,
    INTEREST_PERIODS,
    MAINTENANCE_CATEGORY,
    MAINTENANCE_STATUS,
    MORTGAGE_TYPES,
    PROPERTY_TYPE,
)

# Create your models here.


class UserBudgets(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return str(self.name)


# Create a default budget for new user


@receiver(post_save, sender=User)
def add_user_budget(sender, instance, created, **kwargs):
    if created:
        UserBudgets.objects.create(name="Default Budget", user=instance)


class Property(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="property_user"
    )
    property_name = models.CharField(max_length=255, blank=True, null=True)
    property_image = models.ImageField(upload_to="property_pics", blank=True, null=True)
    property_type = models.CharField(
        max_length=10, choices=PROPERTY_TYPE, blank=True, null=True
    )
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    post_code = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    unit_details = models.CharField(max_length=100**6, blank=True, null=True)
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    value = models.CharField(max_length=255, blank=True, null=True)
    include_net_worth = models.BooleanField(default=False, blank=True, null=True)
    units_no = models.CharField(max_length=255, blank=True, null=True)
    total_monthly_rent = models.CharField(max_length=255, blank=True, null=True)
    total_tenants = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.property_name)


class PropertyRentalInfo(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="property_rental_user"
    )
    property_address = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="property_address"
    )
    unit_name = models.CharField(max_length=255, blank=True, null=True)
    rental_term = models.CharField(max_length=255, blank=True, null=True)
    rental_start_date = models.DateField(blank=True, null=True)
    rental_end_date = models.DateField(blank=True, null=True)
    deposit_amount = models.CharField(max_length=255, blank=True, null=True)
    deposit_due_date = models.DateField(blank=True, null=True)
    deposit_check = models.CharField(max_length=255, blank=True, null=True)
    rent_amount = models.CharField(max_length=255, blank=True, null=True)
    rent_due_every_month = models.CharField(max_length=255, blank=True, null=True)
    rent_due_date = models.DateField(blank=True, null=True)
    rental_summary = models.CharField(max_length=100**100, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    mobile_number = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return str(
            self.first_name
            + " "
            + self.property_address.property_name
            + " "
            + self.unit_name
        )


class PropertyInvoice(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="property_invoice_user"
    )
    property_details = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="property_details"
    )
    tenant_name = models.CharField(max_length=255, blank=True, null=True)
    unit_name = models.CharField(max_length=255, blank=True, null=True)
    item_type = models.CharField(max_length=255, blank=True, null=True)
    item_description = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.CharField(max_length=255, blank=True, null=True)
    item_amount = models.CharField(max_length=255, blank=True, null=True)
    already_paid = models.CharField(max_length=255, blank=True, null=True)
    balance_due = models.CharField(max_length=255, blank=True, null=True)
    invoice_due_date = models.DateField(blank=True, null=True)
    invoice_paid_date = models.DateField(blank=True, null=True)
    invoice_status = models.CharField(max_length=255, blank=True, null=True)
    record_payment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return str(
            self.tenant_name
            + " "
            + self.property_details.property_name
            + " "
            + self.unit_name
            + str(self.id)
        )


class PropertyMaintenance(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="property_maintenance_user"
    )
    property_details = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="property_maintenance_details"
    )
    unit_name = models.CharField(max_length=255, blank=True, null=True)
    tenant_name = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(
        max_length=10, choices=MAINTENANCE_CATEGORY, blank=True, null=True
    )
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=10, choices=MAINTENANCE_STATUS, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return str(
            self.name + " " + self.property_details.property_name + " " + self.unit_name
        )

    def get_absolute_url(self):
        return reverse("property_maintenance_list")


class PropertyExpense(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="property_expense_user"
    )
    property_details = models.ForeignKey(
        Property, on_delete=models.CASCADE, related_name="property_info"
    )
    payee_name = models.CharField(max_length=255, blank=True, null=True)
    expense_date = models.DateField(blank=True, null=True)
    unit_name = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    amount = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return str(
            self.payee_name
            + " "
            + self.property_details.property_name
            + " "
            + self.unit_name
            + str(self.id)
        )

    def get_absolute_url(self):
        return reverse("property_expense_list")


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse("category_list")


class SubCategory(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{str(self.category.name)}: {str(self.name)}"

    def get_absolute_url(self):
        return reverse("category_list")


class SuggestiveCategory(models.Model):
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)


class TemplateBudget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, null=True, blank=True
    )
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    initial_amount = models.CharField(max_length=15, blank=True, null=True)
    amount = models.CharField(max_length=15, default=0, blank=True, null=True)
    budget_spent = models.CharField(max_length=15, default=0, blank=True, null=True)
    budget_left = models.CharField(max_length=15, default=0, blank=True, null=True)
    auto_budget = models.BooleanField(default=True, blank=True, null=True)
    auto_pay = models.BooleanField(default=True, blank=True, null=True)
    budget_period = models.CharField(
        max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
    )
    budget_status = models.BooleanField(default=False, blank=True, null=True)
    budget_start_date = models.DateField(blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    ended_at = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.name}{self.id}{self.currency}"

    def get_absolute_url(self):
        return reverse("template_budget_list")


class PlaidItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=255)
    item_id = models.CharField(max_length=255)


class Account(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="account_user"
    )
    name = models.CharField(max_length=50, null=True)
    account_type = models.CharField(
        max_length=50, choices=BUDGET_ACCOUNT_TYPES, blank=True, null=True
    )
    balance = models.CharField(max_length=10, blank=True, null=True)
    available_balance = models.CharField(max_length=10, blank=True, null=True)
    lock_amount = models.CharField(max_length=10, blank=True, null=True)
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    interest_rate = models.FloatField(verbose_name="Interest rate", default=0.00)
    include_net_worth = models.BooleanField(default=True, blank=True, null=True)
    liability_type = models.CharField(
        max_length=10, choices=MORTGAGE_TYPES, blank=True, null=True
    )
    interest_period = models.CharField(
        max_length=10, choices=INTEREST_PERIODS, blank=True, null=True
    )
    mortgage_date = models.DateField(blank=True, null=True)
    mortgage_monthly_payment = models.CharField(max_length=10, blank=True, null=True)
    mortgage_year = models.CharField(max_length=10, blank=True, null=True)
    transaction_count = models.IntegerField(default=0, blank=True, null=True)
    plaid_account_id = models.CharField(max_length=200, blank=True, null=True)
    mask = models.CharField(max_length=200, blank=True, null=True)
    subtype = models.CharField(max_length=200, blank=True, null=True)
    item = models.ForeignKey(PlaidItem, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name + "(" + self.currency + ")")

    def get_absolute_url(self):
        return reverse("account_box")


class BillDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    user_budget = models.ForeignKey(UserBudgets, on_delete=models.CASCADE, null=True)
    label = models.CharField(max_length=50)
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="bill_details_account",
        blank=True,
        null=True,
    )
    amount = models.CharField(max_length=50)
    date = models.DateField()
    frequency = models.CharField(
        max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
    )
    auto_bill = models.BooleanField(default=False, blank=True, null=True)
    auto_pay = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.label + self.user.username)


class Bill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_budget = models.ForeignKey(UserBudgets, on_delete=models.CASCADE, null=True)
    label = models.CharField(max_length=50)
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="bill_account",
        blank=True,
        null=True,
    )
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    amount = models.CharField(max_length=50)
    remaining_amount = models.CharField(max_length=50)
    date = models.DateField()
    bill_details = models.ForeignKey(
        BillDetail,
        on_delete=models.CASCADE,
        related_name="bill_details",
        blank=True,
        null=True,
    )
    status = models.CharField(max_length=50, default="unpaid", blank=True, null=True)
    frequency = models.CharField(
        max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
    )
    auto_bill = models.BooleanField(default=False, blank=True, null=True)
    auto_pay = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.label + "(" + self.currency + ")")

    def get_absolute_url(self):
        return reverse("bill_list")


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    user_budget = models.ForeignKey(UserBudgets, on_delete=models.CASCADE, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, null=True, blank=True
    )
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="budget_account",
        blank=True,
        null=True,
    )
    initial_amount = models.CharField(max_length=15, blank=True, null=True)
    amount = models.CharField(max_length=15, default=0, blank=True, null=True)
    budget_spent = models.CharField(max_length=15, default=0, blank=True, null=True)
    budget_left = models.CharField(max_length=15, default=0, blank=True, null=True)
    auto_budget = models.BooleanField(default=True, blank=True, null=True)
    auto_pay = models.BooleanField(default=True, blank=True, null=True)
    budget_period = models.CharField(
        max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
    )
    budget_status = models.BooleanField(default=False, blank=True, null=True)
    budget_start_date = models.DateField(blank=True, null=True)
    created_at = models.DateField(blank=True, null=True)
    ended_at = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.name}{self.id}{self.currency}"

    def get_absolute_url(self):
        return reverse("current-budgets")


class AvailableFunds(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="fund_user")
    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="fund_account"
    )
    total_fund = models.CharField(max_length=20)
    lock_fund = models.CharField(max_length=20)
    created_at = models.DateField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.account)


class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="goal_user")
    user_budget = models.ForeignKey(UserBudgets, on_delete=models.CASCADE, null=True)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    goal_date = models.DateField(blank=True, null=True)
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    label = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, null=True, blank=True
    )
    goal_amount = models.FloatField()
    allocate_amount = models.FloatField()
    fund_amount = models.FloatField(default=0)
    budget_amount = models.FloatField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.label)


class PropertyPurchaseDetails(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="property_purchase_user"
    )
    best_case_price = models.CharField(max_length=30)
    likely_case_price = models.CharField(max_length=30)
    worst_case_price = models.CharField(max_length=30)
    selected_case = models.CharField(max_length=30)
    selected_price = models.CharField(max_length=30, blank=True, null=True)
    down_payment = models.CharField(max_length=30)


class MortgageDetails(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="mortgage_user"
    )
    start_date = models.DateField(blank=True, null=True)
    interest_rate = models.CharField(max_length=30)
    amortization_year = models.CharField(max_length=30)


class ClosingCostDetails(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="closing_cost_user"
    )
    transfer_tax = models.CharField(max_length=30)
    legal_fee = models.CharField(max_length=30)
    title_insurance = models.CharField(max_length=30)
    inspection = models.CharField(max_length=30)
    appraisal_fee = models.CharField(max_length=30)
    appliances = models.CharField(max_length=30)
    renovation_cost = models.CharField(max_length=30)
    others_cost = models.CharField(max_length=10000000)
    total_investment = models.CharField(max_length=30, blank=True, null=True)


class RevenuesDetails(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="rev_user")
    unit_1 = models.CharField(max_length=30)
    others_revenue_cost = models.CharField(max_length=1000000000)
    total_revenue = models.CharField(max_length=30)
    rent_increase_assumption = models.CharField(max_length=30)


class ExpensesDetails(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="expense_user"
    )
    property_tax = models.CharField(max_length=30)
    insurance = models.CharField(max_length=30)
    maintenance = models.CharField(max_length=30)
    water = models.CharField(max_length=30)
    gas = models.CharField(max_length=30)
    electricity = models.CharField(max_length=30)
    water_heater_rental = models.CharField(max_length=30)
    other_utilities = models.CharField(max_length=1000000000)
    management_fee = models.CharField(max_length=30)
    vacancy = models.CharField(max_length=30)
    capital_expenditure = models.CharField(max_length=30)
    other_expenses = models.CharField(max_length=1000000000)
    total_expenses = models.CharField(max_length=30)
    inflation_assumption = models.CharField(max_length=30)
    appreciation_assumption = models.CharField(max_length=30)


class CapexBudgetDetails(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="capex_budget_user"
    )
    roof = models.CharField(max_length=1000000000, blank=True, null=True)
    water_heater = models.CharField(max_length=1000000000, blank=True, null=True)
    all_appliances = models.CharField(max_length=1000000000, blank=True, null=True)
    bathroom_fixtures = models.CharField(max_length=1000000000, blank=True, null=True)
    drive_way = models.CharField(max_length=1000000000, blank=True, null=True)
    furnance = models.CharField(max_length=1000000000, blank=True, null=True)
    air_conditioner = models.CharField(max_length=1000000000, blank=True, null=True)
    flooring = models.CharField(max_length=1000000000, blank=True, null=True)
    plumbing = models.CharField(max_length=1000000000, blank=True, null=True)
    electrical = models.CharField(max_length=1000000000, blank=True, null=True)
    windows = models.CharField(max_length=1000000000, blank=True, null=True)
    paint = models.CharField(max_length=1000000000, blank=True, null=True)
    kitchen = models.CharField(max_length=1000000000, blank=True, null=True)
    structure = models.CharField(max_length=1000000000, blank=True, null=True)
    components = models.CharField(max_length=1000000000, blank=True, null=True)
    landscaping = models.CharField(max_length=1000000000, blank=True, null=True)
    other_budgets = models.CharField(
        max_length=10000000000000000, blank=True, null=True
    )
    total_budget_cost = models.CharField(max_length=30, blank=True, null=True)


class RentalPropertyModel(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="property_rental"
    )
    property_image = models.ImageField(upload_to="property_pics", blank=True, null=True)
    name = models.CharField(max_length=30)
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    purchase_price_detail = models.ForeignKey(
        PropertyPurchaseDetails,
        on_delete=models.CASCADE,
        related_name="property_purchase_user",
    )
    mortgage_detail = models.ForeignKey(
        MortgageDetails, on_delete=models.CASCADE, related_name="mortgage_user"
    )
    closing_cost_detail = models.ForeignKey(
        ClosingCostDetails, on_delete=models.CASCADE, related_name="closing_cost_user"
    )
    monthly_revenue = models.ForeignKey(
        RevenuesDetails, on_delete=models.CASCADE, related_name="rev_user"
    )
    monthly_expenses = models.ForeignKey(
        ExpensesDetails, on_delete=models.CASCADE, related_name="expense_user"
    )
    capex_budget_details = models.ForeignKey(
        CapexBudgetDetails, on_delete=models.CASCADE, related_name="capex_budget"
    )
    investor_details = models.CharField(max_length=1000000000, blank=True, null=True)
    include_net_worth = models.BooleanField(default=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)


class Tag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tag_user")
    name = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


class Transaction(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="transaction_user"
    )
    amount = models.CharField(max_length=255)
    remaining_amount = models.CharField(max_length=10)
    transaction_date = models.DateField(blank=True, null=True)
    categories = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, null=True, blank=True
    )
    split_transactions = models.CharField(max_length=255, blank=True, null=True)
    original_amount = models.CharField(max_length=255, blank=True, null=True)
    budgets = models.ForeignKey(Budget, on_delete=models.CASCADE)
    payee = models.CharField(max_length=25)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    tags = models.ForeignKey(Tag, on_delete=models.CASCADE, null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True, null=True)
    in_flow = models.BooleanField(default=False)
    out_flow = models.BooleanField(default=True)
    plaid_account_id = models.CharField(max_length=255, blank=True, null=True)
    plaid_transaction_id = models.CharField(max_length=255, blank=True, null=True)
    cleared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.payee)

    def get_absolute_url(self):
        return reverse("transaction_list")


class MortgageCalculator(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="mortgagecalculator_user"
    )
    label = models.CharField(max_length=30)
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    amount = models.IntegerField(default=0)
    years = models.CharField(max_length=10)
    interest = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.label)

    def get_absolute_url(self):
        return reverse("mortgagecalculator_list")


class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    sub_category = models.ForeignKey(
        SubCategory, on_delete=models.CASCADE, null=True, blank=True
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="income_account",
        blank=True,
        null=True,
    )
    income_amount = models.CharField(max_length=50)
    income_date = models.DateField()
    auto_income = models.BooleanField(default=False, blank=True, null=True)
    frequency = models.CharField(
        max_length=10, choices=BUDGET_PERIODS, blank=True, null=True
    )
    auto_credit = models.BooleanField(default=False, blank=True, null=True)
    primary = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{str(self.sub_category.name)}"


class IncomeDetail(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="income_detail_account",
        blank=True,
        null=True,
    )
    income_amount = models.CharField(max_length=50)
    income_date = models.DateField(blank=True, null=True)
    income = models.ForeignKey(Income, on_delete=models.CASCADE)
    credited = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{str(self.income.sub_category.name)}"


class Revenues(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="revenue_user"
    )
    name = models.CharField(max_length=255)
    month = models.DateField(blank=True, null=True)
    end_month = models.DateField(blank=True, null=True)
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    amount = models.CharField(max_length=20)
    primary = models.BooleanField(default=False, blank=True, null=True)
    non_primary = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.month)


class Expenses(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="expenses_user"
    )
    categories = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    month = models.DateField(blank=True, null=True)
    currency = models.CharField(
        max_length=10, choices=CURRENCIES, blank=True, null=True
    )
    amount = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.month)


class StockHoldings(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="stockholdings_user"
    )
    port_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    currency = models.CharField(max_length=10, blank=True, null=True)
    value = models.CharField(max_length=255)
    end_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)


class MyNotes(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    notes = models.TextField()
    added_on = models.DateField(default=datetime.date.today)

    def __str__(self):
        return str(self.title + " " + self.user.username)


# Chat Model for chatting with chatgpt
class AIChat(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="aichat_user")
    message = models.TextField()
    ai_response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.message}"

    class Meta:
        ordering = ["-created_at"]


# Feedback model
class Feedback(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="feedback_user"
    )
    feature = models.CharField(max_length=255)
    issue = models.CharField(max_length=255)
    screenshot = models.ImageField(
        upload_to="feedback_screenshots/", null=True, blank=True
    )
    description = models.TextField()
    suggestion = models.TextField()
    importance = models.CharField(max_length=255)
    is_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.issue}"

    class Meta:
        ordering = ["-created_at"]



class AppErrorLog(models.Model):
    class StatusChoices(models.TextChoices):
        RESOLVED = "resolved", "Resolved"
        OPEN = "open", "Open"
        SKIP = "skip", "Skip"
    users = models.ManyToManyField(User, blank=True, related_name="error_logs")
    timestamp = models.DateTimeField(default=now, db_index=True)
    exception_type = models.CharField(max_length=255, db_index=True)
    error_message = models.TextField()
    traceback = models.TextField()
    request_path = models.CharField(max_length=255, blank=True, null=True)
    count = models.PositiveIntegerField(default=1)
    code = models.IntegerField(null=True, blank=True, db_index=True)
    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.OPEN,
        db_index=True,
    )

    class Meta:
        verbose_name = "Error Log"
        verbose_name_plural = "Error Logs"
        ordering = ["-timestamp"]
    
    def __str__(self):
        return f"[{self.count}] {self.exception_type} ({self.code}): {self.error_message[:50]}"