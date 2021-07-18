from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import Category, Budget, Bill, Transaction, Goal, Account, MortgageCalculator, Property, AvailableFunds

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

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        exclude = ('user',)


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


class BudgetForm(forms.ModelForm):
    currency = forms.CharField(widget=forms.Select(choices=CURRENCIES, attrs={'class': 'form-control'}))
    auto_budget = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}))
    budget_period = forms.CharField(widget=forms.Select(choices=BUDGET_PERIODS, attrs={'class': 'form-control'}))

    class Meta:
        model = Budget
        exclude = ('user', 'created_at', 'budget_spent', 'updated_at')


class BillForm(forms.ModelForm):
    currency = forms.CharField(widget=forms.Select(choices=CURRENCIES, attrs={'class': 'form-control'}))
    frequency = forms.CharField(widget=forms.Select(choices=BUDGET_PERIODS, attrs={'class': 'form-control'}))

    class Meta:
        model = Bill
        exclude = ('user', 'status', 'created_at', 'remaining_amount', 'updated_at')


class TransactionForm(forms.ModelForm):
    transaction_date = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control flatpickr-basic',
                                                                     'placeholder': "YYYY-MM-DD", }),
                                                                     required=True)
    in_flow = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}))
    out_flow = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}))
    cleared = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}))

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        user_name = self.request.user
        super(TransactionForm, self).__init__(*args, **kwargs)
        self.fields['categories'] = forms.ModelChoiceField(queryset=Category.objects.filter(user=user_name),
                                                           empty_label="Select Category",
                                                           widget=forms.Select(attrs={'class': 'form-control'}))
        self.fields['bill'] = forms.ModelChoiceField(queryset=Bill.objects.filter(user=user_name),
                                                     empty_label="Select Bill",
                                                     widget=forms.Select(attrs={'class': 'form-control'}), required=False)
        self.fields['budgets'] = forms.ModelChoiceField(queryset=Budget.objects.filter(user=user_name),
                                                     empty_label="Select Budget",
                                                     widget=forms.Select(attrs={'class': 'form-control'}),
                                                     required=False)
        self.fields['account'] = forms.ModelChoiceField(queryset=Account.objects.filter(user=user_name),
                                                        empty_label="Select Account",
                                                        widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Transaction
        exclude = ('user', 'remaining_amount', 'created_at')


class AccountForm(forms.ModelForm):
    include_net_worth = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}))
    interest_rate = forms.FloatField(required=False)
    balance = forms.FloatField(required=True)
    lock_amount = forms.FloatField(required=True)
    currency = forms.CharField(widget=forms.Select(choices=CURRENCIES, attrs={'class': 'form-control'}))
    lock_check = forms.CharField(widget=forms.CheckboxInput(attrs={'class': 'info'}), required=False)

    class Meta:
        model = Account
        exclude = ('user', 'available_balance', 'liability_type', 'interest_period', 'transaction_count', 'created_at', 'updated_at')


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
        exclude = ('user', 'balance', 'lock_amount', 'transaction_count', 'created_at', 'updated_at')


class MortgageCalculatorForm(forms.ModelForm):
    class Meta:
        model = MortgageCalculator
        exclude = ('user', 'created_at', 'updated_at')


class MortgageForm(forms.Form):
    currency = forms.CharField(widget=forms.Select(choices=CURRENCIES, attrs={'class': 'form-control'}))
    amount = forms.IntegerField()
    interest = forms.FloatField()
    tenure = forms.IntegerField()


class PropertyForm(forms.ModelForm):
    currency = forms.CharField(widget=forms.Select(choices=CURRENCIES, attrs={'class': 'form-control'}))
    class Meta:
        model = Property
        exclude = ('user', 'created_at', 'updated_at')
