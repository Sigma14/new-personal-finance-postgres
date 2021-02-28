# from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from djongo import models

# Create your models here.
BUDGETS = (
    (0, 'No auto-budget'),
    (1, 'Set a fixed amount every period'),
    (2, 'Add an amount every period'),

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


class Budget(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    autobudget = models.CharField(max_length=33, choices=BUDGETS, blank=True, null=True)
    currency = models.CharField(max_length=5, blank=True, null=True)
    amount = models.CharField(max_length=10, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse('budget_list')


class Bill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    currency = models.CharField(max_length=5)
    minimumamount = models.CharField(max_length=10)
    maximumamount = models.CharField(max_length=12)
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse('bill_list')


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transaction_user')
    name = models.CharField(max_length=50)
    amount = models.CharField(max_length=5)
    categories = models.ForeignKey(Category, on_delete=models.CASCADE)
    payee = models.CharField(max_length=25)
    account = models.CharField(max_length=20)
    bill = models.ForeignKey(User, on_delete=models.CASCADE)
    cleared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.name)

    def get_absolute_url(self):
        return reverse('transaction_list')


class Goal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goal_user')
    label = models.CharField(max_length=40)
    goalamount = models.CharField(max_length=10)
    currentbalance = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.label)

    def get_absolute_url(self):
        return reverse('goal_list')


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='account_user')
    balance = models.CharField(max_length=10)
    interestrate = models.CharField(max_length=10,verbose_name='Interest rate')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.balance)

    def get_absolute_url(self):
        return reverse('account_list')


class MortgageCalculator(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mortgagecalculator_user')
    label = models.CharField(max_length=30)
    amount = models.IntegerField(default=0)
    years = models.CharField(max_length=10)
    interest = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.label)

    def get_absolute_url(self):
        return reverse('mortgagecalculator_list')