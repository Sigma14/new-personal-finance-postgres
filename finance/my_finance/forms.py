from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import Category, Budget, Bill, Transaction, Goal, Account, MortgageCalculator


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
    class Meta:
        model = Budget
        exclude = ('user', 'autobudget', 'created_at', 'updated_at')


class BillForm(forms.ModelForm):
    class Meta:
        model = Bill
        exclude = ('user', 'created_at', 'updated_at')


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        exclude = ('user', 'created_at', 'updated_at')


class GoalForm(forms.ModelForm):
    class Meta:
        model = Goal
        exclude = ('user', 'created_at', 'updated_at')


class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        exclude = ('user', 'created_at', 'updated_at')


class MortgageCalculatorForm(forms.ModelForm):
    class Meta:
        model = MortgageCalculator
        exclude = ('user', 'created_at', 'updated_at')


class MortgageForm(forms.Form):
    amount = forms.IntegerField()
    interest = forms.FloatField()
    tenure = forms.IntegerField()
