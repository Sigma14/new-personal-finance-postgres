# from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from djongo import models

# Create your models here.

TYPES = (
    ("Debt", 'Debt'),
    ("Loan", 'Loan'),
    ("Mortgage", 'Mortgage'),
)

PERIODS = (
    ("Per day", 'Per day'),
    ("Per month", 'Per month'),
    ("Per year", 'Per year'),
)

CURRENCIES = (
    ("$", 'US Dollar ($)'),
    ("€", 'Euro (€)'),
    ("₹", 'Indian rupee (₹)'),
    ("£", 'British Pound (£)'),
)

BUDGET_PERIODS = (
    ("Daily", 'Daily'),
    ("Weekly", 'Weekly'),
    ("Monthly", 'Monthly'),
    ("Quarterly", 'Quarterly'),
    ("Yearly", 'Yearly'),
)


class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse('category_list')


class SuggestiveCategory(models.Model):
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    currency = models.CharField(max_length=10, choices=CURRENCIES, blank=True, null=True)
    amount = models.CharField(max_length=10, default=0)
    budget_spent = models.CharField(max_length=10, default=0)
    auto_budget = models.BooleanField(default=True, blank=True, null=True)
    budget_period = models.CharField(max_length=10, choices=BUDGET_PERIODS, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name + "(" + self.currency + ")")

    def get_absolute_url(self):
        return reverse('budget_list')


class Bill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    label = models.CharField(max_length=50)
    currency = models.CharField(max_length=10, choices=CURRENCIES, blank=True, null=True)
    amount = models.CharField(max_length=50)
    remaining_amount = models.CharField(max_length=50)
    date = models.DateField()
    status = models.CharField(max_length=50, default="unpaid", blank=True, null=True)
    frequency = models.CharField(max_length=10, choices=BUDGET_PERIODS, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.label + "(" + self.currency + ")")

    def get_absolute_url(self):
        return reverse('bill_list')


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_user')
    name = models.CharField(max_length=50, null=True)
    balance = models.CharField(max_length=10, blank=True, null=True)
    available_balance = models.CharField(max_length=10, blank=True, null=True)
    lock_amount = models.CharField(max_length=10, blank=True, null=True)
    currency = models.CharField(max_length=10, choices=CURRENCIES, blank=True, null=True)
    interest_rate = models.FloatField(verbose_name='Interest rate', default=0.00)
    include_net_worth = models.BooleanField(default=True, blank=True, null=True)
    liability_type = models.CharField(max_length=10, choices=TYPES, blank=True, null=True)
    interest_period = models.CharField(max_length=10, choices=PERIODS, blank=True, null=True)
    transaction_count = models.IntegerField(default=0, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name + "(" + self.currency + ")")

    def get_absolute_url(self):
        return reverse('account_list')


class AvailableFunds(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fund_user')
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='fund_account')
    total_fund = models.CharField(max_length=20)
    lock_fund = models.CharField(max_length=20)
    created_at = models.DateField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.account)


class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goal_user')
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    goal_date = models.DateField(blank=True, null=True)
    currency = models.CharField(max_length=10, choices=CURRENCIES, blank=True, null=True)
    label = models.CharField(max_length=40)
    goal_amount = models.FloatField()
    allocate_amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.label)


class Property(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='property_user')
    name = models.CharField(max_length=30)
    currency = models.CharField(max_length=10, choices=CURRENCIES, blank=True, null=True)
    value = models.CharField(max_length=12)
    include_net_worth = models.BooleanField(default=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse('property_list')


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transaction_user')
    amount = models.CharField(max_length=5)
    remaining_amount = models.CharField(max_length=10)
    transaction_date = models.DateField(blank=True, null=True)
    categories = models.ForeignKey(Category, on_delete=models.CASCADE)
    budgets = models.ForeignKey(Budget, on_delete=models.CASCADE)
    payee = models.CharField(max_length=25)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE)
    tags = models.CharField(max_length=225, blank=True, null=True)
    in_flow = models.BooleanField(default=False)
    out_flow = models.BooleanField(default=True)
    cleared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.payee)

    def get_absolute_url(self):
        return reverse('transaction_list')


class MortgageCalculator(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mortgagecalculator_user')
    label = models.CharField(max_length=30)
    currency = models.CharField(max_length=10, choices=CURRENCIES, blank=True, null=True)
    amount = models.IntegerField(default=0)
    years = models.CharField(max_length=10)
    interest = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.label)

    def get_absolute_url(self):
        return reverse('mortgagecalculator_list')


class Revenues(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='revenue_user')
    name = models.CharField(max_length=255)
    month = models.DateField(blank=True, null=True)
    end_month = models.DateField(blank=True, null=True)
    currency = models.CharField(max_length=10, choices=CURRENCIES, blank=True, null=True)
    amount = models.CharField(max_length=20)
    primary = models.BooleanField(default=False, blank=True, null=True)
    non_primary = models.BooleanField(default=False, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.month)


class Expenses(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses_user')
    categories = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    month = models.DateField(blank=True, null=True)
    currency = models.CharField(max_length=10, choices=CURRENCIES, blank=True, null=True)
    amount = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.month)
