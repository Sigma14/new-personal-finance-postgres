from datetime import datetime
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import Category, Budget, Bill, Transaction, Goal, Account, MortgageCalculator, Property, AvailableFunds, \
    TemplateBudget, PropertyMaintenance, PropertyExpense, SubCategory, UserBudgets

CURRENCIES = (
    ("$", 'US Dollar ($)'),
    ("€", 'Euro (€)'),
    ("₹", 'Indian rupee (₹)'),
    ("£", 'British Pound (£)'),
    ("CAD", 'Canadian Dollar ($)'),
)

BUDGET_PERIODS = (
    ("Daily", 'Daily'),
    ("Weekly", 'Weekly'),
    ("Monthly", 'Monthly'),
    ("Quarterly", 'Quarterly'),
    ("Yearly", 'Yearly'),
)

MAINTENANCE_CATEGORY = (
    ("A/C", 'A/C'),
    ("Appliance ", 'Appliance '),
    ("Electrical", 'Electrical'),
    ("Heat", 'Heat'),
    ("Kitchen", 'Kitchen'),
    ("Plumbing", 'Plumbing'),
    ("Other", 'Other'),
)

MAINTENANCE_STATUS = (
    ("Unresolved", 'Unresolved'),
    ("Resolved", 'Resolved'),)

class UserBudgetsForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)

    class Meta:
        model = UserBudgets
        exclude = ('user', 'created_at', 'updated_at')

    

class CategoryForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)

    class Meta:
        model = Category
        exclude = ('user', 'created_at', 'updated_at')

    def clean(self):
        name = self.cleaned_data.get('name').title()
        qs = Category.objects.filter(name=name)
        if qs.exists():
            raise forms.ValidationError('Category is already exists.')
        return super(CategoryForm, self).clean()


class RegisterForm(forms.ModelForm):
    email = forms.EmailField(label='Email Address')
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password'
        ]

    def clean(self):
        email = self.cleaned_data.get('email')
        qs = User.objects.filter(email=email)
        if qs.exists():
            raise forms.ValidationError('Email is already exists,'
                                        'Please use another email address to register')
        return super(RegisterForm, self).clean()


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        if user is None:
            raise forms.ValidationError('user does not exist please register first')
        if not user.check_password(password):
            raise forms.ValidationError('Incorrect password')
        elif not user.is_active:
            raise forms.ValidationError('User is not active')
        return super(LoginForm, self).clean()


class MaintenanceForm(forms.ModelForm):
    category = forms.CharField(widget=forms.Select(choices=MAINTENANCE_CATEGORY, attrs={'class': 'form-control'}),
                               required=True)
    unit_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    tenant_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    description = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}), required=True)
    status = forms.CharField(widget=forms.Select(choices=MAINTENANCE_STATUS, attrs={'class': 'form-control'}),
                             required=True)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        user_name = self.request.user
        super(MaintenanceForm, self).__init__(*args, **kwargs)
        self.fields['property_details'] = forms.ModelChoiceField(queryset=Property.objects.filter(user=user_name),
                                                                 empty_label="Select Property",
                                                                 widget=forms.Select(
                                                                     attrs={'class': 'form-control select_property'}),
                                                                 required=True)

    class Meta:
        model = PropertyMaintenance
        exclude = ('user', 'created_at', 'updated_at')


class ExpenseForm(forms.ModelForm):
    unit_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    payee_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    description = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    amount = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    expense_date = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control flatpickr-basic',
                                                                 'placeholder': 'YYYY-MM-DD'}), required=True)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        user_name = self.request.user
        super(ExpenseForm, self).__init__(*args, **kwargs)
        self.fields['property_details'] = forms.ModelChoiceField(queryset=Property.objects.filter(user=user_name),
                                                                 empty_label="Select Property",
                                                                 widget=forms.Select(
                                                                     attrs={'class': 'form-control select_property'}),
                                                                 required=True)

    class Meta:
        model = PropertyExpense
        exclude = ('user', 'created_at', 'updated_at')


class BudgetForm(forms.ModelForm):
    currency = forms.CharField(widget=forms.Select(choices=CURRENCIES, attrs={'class': 'form-control'}))
    auto_budget = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}))
    budget_period = forms.CharField(initial='Monthly', widget=forms.Select(choices=BUDGET_PERIODS, attrs={'class': 'form-control'},))
    categories = forms.ModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        try:
            self.request = kwargs.pop('request')
            user_name = self.request.user
            super(BudgetForm, self).__init__(*args, **kwargs)
            self.fields['categories'] = forms.ModelChoiceField(
                queryset=Category.objects.filter(user=user_name)
                .exclude(name__in=["Goals", "Funds"]),
                empty_label="Select Category Group",
                widget=forms.Select(
                attrs={'class': 'form-control pick_category',
                'method_name': 'add_budget'}))
        except Exception as msg:
            print(msg)

    class Meta:
        model = Budget
        exclude = ('user', 'created_at', 'budget_spent', 'budget_left', 'updated_at', 'initial_amount', 'budget_status')


class TemplateBudgetForm(forms.ModelForm):
    currency = forms.CharField(widget=forms.Select(choices=CURRENCIES, attrs={'class': 'form-control'}))
    auto_budget = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}))
    budget_period = forms.CharField(widget=forms.Select(choices=BUDGET_PERIODS, attrs={'class': 'form-control'}))

    class Meta:
        model = TemplateBudget
        exclude = ('user', 'created_at', 'budget_spent', 'budget_left', 'updated_at', 'initial_amount', 'budget_status')


class BillForm(forms.ModelForm):
    frequency = forms.CharField(widget=forms.Select(choices=BUDGET_PERIODS, attrs={'class': 'form-control'}))

    class Meta:
        model = Bill
        exclude = ('user', 'currency', 'status', 'created_at', 'remaining_amount', 'updated_at')


class TransactionForm(forms.ModelForm):
    transaction_date = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control flatpickr-basic',
                                                                     'placeholder': "YYYY-MM-DD",
                                                                     'value': str(datetime.today().date())}),
                                       required=True)
    in_flow = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}))
    out_flow = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}))
    cleared = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}), required=False)
    amount = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    notes = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    tag_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=False)
    category = forms.ModelChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        user_name = self.request.user
        super(TransactionForm, self).__init__(*args, **kwargs)
        self.fields['category'] = forms.ModelChoiceField(queryset=Category.objects.filter(user=user_name),#.exclude(name__in=["Goals"]),
                                                           empty_label="Select Category Group",
                                                           widget=forms.Select(
                                                               attrs={'class': 'form-control pick_category'}))
        self.fields['bill'] = forms.ModelChoiceField(queryset=Bill.objects.filter(user=user_name),
                                                     empty_label="Select Bill",
                                                     widget=forms.Select(attrs={'class': 'form-control'}),
                                                     required=False)
        self.fields['account'] = forms.ModelChoiceField(queryset=Account.objects.filter(user=user_name,
                                                                                        account_type__in=['Checking',
                                                                                                          'Savings',
                                                                                                          'Cash',
                                                                                                          'Credit Card',
                                                                                                          'Line of Credit',
                                                                                                          'Emergency Fund']),
                                                        empty_label="Select Account",
                                                        widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Transaction
        exclude = ('user', 'split_transactions', 'original_amount', 'plaid_account_id', 'plaid_transaction_id', 'remaining_amount', 'created_at', 'budgets')


class AccountForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    include_net_worth = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}))
    balance = forms.FloatField(widget=forms.TextInput(attrs={'class': 'form-control'}), required=True)
    currency = forms.CharField(widget=forms.Select(choices=CURRENCIES, attrs={'class': 'form-control'}))
    account_type = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Account
        exclude = ('user', 'plaid_account_id', 'mask', 'sub_type', 'item', 'available_balance',
                   'liability_type', 'interest_rate', 'interest_period', 'transaction_count', 'mortgage_year', 'created_at',
                   'updated_at')


# class FundForm(forms.ModelForm):
#     total_fund = forms.FloatField(required=True)
#     lock_fund = forms.FloatField(required=True)
#
#     class Meta:
#         model = AvailableFunds
#         exclude = ('user', 'account', 'created_at', 'updated_at')


class LiabilityForm(forms.ModelForm):
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
    include_net_worth = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}))
    currency = forms.CharField(widget=forms.Select(choices=CURRENCIES, attrs={'class': 'form-control'}))
    liability_type = forms.CharField(widget=forms.Select(choices=TYPES, attrs={'class': 'form-control'}))
    interest_period = forms.CharField(widget=forms.Select(choices=PERIODS, attrs={'class': 'form-control'}))
    lock_check = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}))

    class Meta:
        model = Account
        exclude = (
        'user', 'plaid_account_id', 'mask', 'sub_type', 'account_type', 'item', 'available_balance', 'lock_amount',
        'transaction_count', 'created_at', 'updated_at')


class MortgageCalculatorForm(forms.ModelForm):
    class Meta:
        model = MortgageCalculator
        exclude = ('user', 'created_at', 'updated_at')


class MortgageForm(forms.Form):
    mortgage_date = forms.DateField(widget=forms.Select(choices=CURRENCIES, attrs={'class': 'form-control'}),
                                    required=True)
    amount = forms.IntegerField(required=True)
    down_payment = forms.IntegerField(required=True)
    interest = forms.FloatField(required=True)
    tenure = forms.IntegerField(required=True)

# class PropertyForm(forms.ModelForm):
#     include_net_worth = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}))
#     currency = forms.CharField(widget=forms.Select(choices=CURRENCIES, attrs={'class': 'form-control'}))
#     class Meta:
#         model = Property
#         exclude = ('user', 'created_at', 'updated_at')
