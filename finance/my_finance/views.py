import json

from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import CategoryForm, LoginForm, BudgetForm, BillForm, TransactionForm, GoalForm, AccountForm, MortgageForm
from .models import Category, Budget, Bill, Transaction, Goal, Account
from .mortgage import calculator


def home(request):
    return render(request, 'dashboard.html')


class CategoryList(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'category_list.html'


class CategoryDetail(DetailView):
    model = Category
    template_name = 'category_detail.html'


class CategoryAdd(CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'category_add.html'


class CategoryUpdate(UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'category_update.html'


class CategoryDelete(DeleteView):
    model = Category
    form_class = CategoryForm
    template_name = 'category_delete.html'

    def get_success_url(self):
        return reverse('category_list')


def user_login(request):
    next = request.GET.get('next')
    form = LoginForm(request.POST or None)
    if form.is_valid():
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)
        print(user)
        if user:
            login(request, user)
            if next:
                return redirect(next)
            else:
                return redirect("/list")

    context = {'form': form}
    template = 'login.html'
    return render(request, template, context)


def user_logout(request):
    auth.logout(request)
    return redirect('/login')


class BudgetList(LoginRequiredMixin, ListView):
    model = Budget
    template_name = 'budget_list.html'


class BudgetDetail(LoginRequiredMixin, DetailView):
    model = Budget
    template_name = 'budget_detail.html'


class BudgetAdd(LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budget_add.html'


class BudgetUpdate(LoginRequiredMixin, UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budget_update.html'


class BudgetDelete(LoginRequiredMixin, DeleteView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budget_delete.html'

    def get_success_url(self):
        return reverse('budget_list')


class BillList(LoginRequiredMixin, ListView):
    model = Bill
    template_name = 'bill_list.html'


class BillDetail(LoginRequiredMixin, DetailView):
    model = Bill
    template_name = 'bill_detail.html'


class BillAdd(LoginRequiredMixin, CreateView):
    model = Bill
    form_class = BillForm
    template_name = 'bill_add.html'


class BillUpdate(LoginRequiredMixin, UpdateView):
    model = Bill
    form_class = BillForm
    template_name = 'bill_update.html'


class BillDelete(LoginRequiredMixin, DeleteView):
    model = Bill
    form_class = BillForm
    template_name = 'bill_delete.html'


class TransactionList(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transaction_list.html'


class TransactionDetail(LoginRequiredMixin, DetailView):
    model = Transaction
    template_name = 'transaction_detail.html'


class TransactionAdd(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transaction_add.html'


class TransactionUpdate(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transaction_update.html'


class TransactionDelete(LoginRequiredMixin, DeleteView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transaction_delete.html'


class GoalList(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'goal_list.html'


class GoalDetail(LoginRequiredMixin, DetailView):
    model = Goal
    template_name = 'goal_detail.html'


class GoalAdd(LoginRequiredMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'goal_add.html'


class GoalUpdate(LoginRequiredMixin, UpdateView):
    model = Goal
    form_class = GoalForm
    template_name = 'goal_update.html'


class GoalDelete(LoginRequiredMixin, DeleteView):
    model = Goal
    form_class = GoalForm
    template_name = 'goal_delete.html'


class AccountList(LoginRequiredMixin, ListView):
    model = Account
    template_name = 'account_list.html'


class AccountDetail(LoginRequiredMixin, DetailView):
    model = Account
    template_name = 'account_detail.html'


class AccountAdd(LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'account_add.html'


class AccountUpdate(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'account_update.html'


class AccountDelete(LoginRequiredMixin, DeleteView):
    model = Account
    form_class = AccountForm
    template_name = 'account_delete.html'


def mortgagecalculator(request):
    form = MortgageForm(request.POST or None)
    if form.is_valid():
        amount = form.cleaned_data.get('amount')
        interest = form.cleaned_data.get('interest')
        tenure = form.cleaned_data.get('tenure')
        table = calculator(amount, interest, tenure)

        json_records = table.reset_index().to_json(orient='records')
        data = json.loads(json_records)
        context = {
            'form': form,
            'data': data,
        }
        return render(request, 'mortgagecalculator_add.html', context)

    context = {
        'form': form
    }
    return render(request, 'mortgagecalculator_add.html', context)
