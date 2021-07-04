import ast
import csv
import json
import calendar
import pandas as pd
import datetime
from io import BytesIO
from collections import OrderedDict
from django.contrib.auth.decorators import login_required
import requests
from django.contrib.auth.hashers import identify_hasher
from django.views.decorators.csrf import csrf_exempt
from dateutil.relativedelta import relativedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from .forms import CategoryForm, LoginForm, BudgetForm, BillForm, TransactionForm, GoalForm, AccountForm, \
    MortgageForm, LiabilityForm, PropertyForm
from .models import Category, Budget, Bill, Transaction, Goal, Account, SuggestiveCategory, Property, Revenues, Expenses
from .mortgage import calculator
from reportlab.lib.colors import PCMYKColor
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib.validators import Auto


def transaction_summary(transaction_data, select_filter):
    tags_data = ['All']
    credit_date_dict = {}
    debit_date_dict = {}
    credit_date_list = []
    debit_date_list = []
    date_list = []
    for transaction_name in transaction_data:
        if transaction_name.cleared:
            transaction_date = str(transaction_name.transaction_date)
            transaction_amount = transaction_name.amount
            if transaction_name.out_flow:
                if transaction_date in debit_date_dict:
                    debit_date_dict[transaction_date] += float(transaction_amount)
                else:
                    debit_date_dict[transaction_date] = float(transaction_amount)

            else:
                if transaction_date in debit_date_dict:
                    credit_date_dict[transaction_date] += float(transaction_amount)
                else:
                    credit_date_dict[transaction_date] = float(transaction_amount)
            date_list.append(str(transaction_date))
        if transaction_name.tags:
            tags_data.append(transaction_name.tags)

    tags_data = list(dict.fromkeys(tags_data))
    date_list = list(dict.fromkeys(date_list))

    for value in date_list:
        if value in debit_date_dict:
            debit_date_list.append(debit_date_dict[value])
            if value not in credit_date_dict:
                credit_date_list.append(0)
        if value in credit_date_dict:
            credit_date_list.append(credit_date_dict[value])
            if value not in debit_date_dict:
                debit_date_list.append(0)

    transaction_key = ['S.No.', 'Date', 'Amount', 'Payee', 'Account', 'Categories', 'Bill', 'Budget', 'Cleared']
    context = {
        'transaction_key': transaction_key,
        'transaction_key_dumbs': json.dumps(transaction_key),
        'transaction_data': transaction_data,
        'tags_data': tags_data,
        'select_filter': select_filter,
        'debit_graph_data': debit_date_list,
        'credit_graph_data': credit_date_list,
        'transaction_date_data': date_list,
        'transaction_date_data_dumbs': json.dumps(date_list),
    }
    return context


def transaction_checks(username, transaction_amount, account, bill_name, budget_name, cleared_amount, out_flow):
    if cleared_amount == "True":
        print("account", account)
        account_obj = Account.objects.get(user=username, name=account)
        print(account_obj)
        if bill_name:
            bill_name = bill_name.label
            bill_obj = Bill.objects.filter(user=username, label=bill_name)[0]
        else:
            bill_obj = False

        if budget_name:
            budget_name = budget_name.name
            budget_obj = Budget.objects.filter(user=username, name=budget_name)[0]
        else:
            budget_obj = False

        if out_flow == "True":
            account_obj.available_balance = round(float(account_obj.available_balance) - transaction_amount, 2)
        else:
            account_obj.available_balance = round(float(account_obj.available_balance) + transaction_amount, 2)

        if bill_obj:
            bill_amount = round(float(bill_obj.remaining_amount), 2)
            if transaction_amount == bill_amount:
                bill_obj.status = "paid"
                bill_obj.remaining_amount = bill_amount - transaction_amount
            else:
                bill_obj.status = "unpaid"
                bill_obj.amount = bill_amount - transaction_amount
            bill_obj.save()

        if budget_obj:
            if out_flow == "True":
                budget_obj.budget_spent = round(float(budget_obj.budget_spent) + transaction_amount, 2)
            else:
                budget_obj.amount = round(float(budget_obj.amount) + transaction_amount, 2)

            budget_obj.save()
        account_obj.transaction_count += 1
        account_obj.save()
        return account_obj


def category_spent_amount(category_data, user_name, categories_name, categories_value):
    for category_name in category_data:
        spent_value = 0
        category_transaction_data = Transaction.objects.filter(user=user_name, categories=category_name)
        for transaction_data in category_transaction_data:
            spent_value += float(transaction_data.amount)
        if spent_value != 0:
            categories_name.append(category_name.name)
            categories_value.append(spent_value)


def multi_acc_chart(acc_transaction_data, amount_date_dict, acc_current_balance, account_date_list, acc_create_date,
                    account_transaction_value, acc_available_balance):
    for data in acc_transaction_data:
        if data.cleared:
            acc_date = str(data.transaction_date)
            acc_transaction_amount = data.amount
            if acc_date in amount_date_dict:
                if data.out_flow:
                    acc_current_balance += float("-" + acc_transaction_amount)
                else:
                    acc_current_balance += float(acc_transaction_amount)

                amount_date_dict[acc_date] = float(acc_current_balance)
            else:
                if data.out_flow:
                    acc_current_balance += float("-" + acc_transaction_amount)
                else:
                    acc_current_balance += float(acc_transaction_amount)
                amount_date_dict[acc_date] = float(acc_current_balance)

    for date_value in account_date_list:
        check_date = datetime.datetime.strptime(date_value, '%Y-%m-%d').date()
        if acc_create_date >= check_date:
            if date_value in amount_date_dict:
                account_transaction_value.append(amount_date_dict[date_value])
                amount_constant = amount_date_dict[date_value]
            else:
                amount_constant = acc_available_balance
                account_transaction_value.append(amount_constant)
        if acc_create_date < check_date:
            if date_value in amount_date_dict:
                account_transaction_value.append(amount_date_dict[date_value])
                amount_constant = amount_date_dict[date_value]
            else:
                account_transaction_value.append(amount_constant)


def net_worth_cal(account_data, property_data, date_range_list, fun_name=None):
    liability_data = []
    assets_data = []
    total_asset_amount_dict = {}
    total_liability_dict = {}
    total_property_dict = {}
    currency_count_list = []
    net_worth_dict = {}
    asset_currency_balance = []
    liability_currency_balance = []
    property_currency_balance = []
    # base = max(date_compare)
    # min_date = min(date_compare)
    # num_days = base - min_date
    # num_days = num_days.days
    # date_range_list = [str(base - datetime.timedelta(days=x)) for x in range(num_days)]
    # date_range_list.append(str(min_date))

    for data in account_data:
        if data.include_net_worth:
            transaction_data = Transaction.objects.filter(account__pk=data.pk).order_by(
                'transaction_date')[::-1]
            current_balance = float(data.available_balance)
            balance_graph_dict = {}
            balance_graph_data = []
            date_list = []
            if data.liability_type != "Debt" and data.liability_type != "Loan" and data.liability_type != "Mortgage":
                if fun_name != "dash_board":
                    overtime_account_data(transaction_data, current_balance, balance_graph_dict, date_list,
                                          balance_graph_data,
                                          date_range_list)
                    asset_currency_balance.append({data.currency: balance_graph_data[::-1]})
                assets_data.append([data.name, data.currency + data.available_balance, data.created_at])
                if data.currency in total_asset_amount_dict:
                    total_asset_amount_dict[data.currency] = round(total_asset_amount_dict[data.currency] +
                                                                   float(data.available_balance), 2)
                else:
                    currency_count_list.append(data.currency)
                    total_asset_amount_dict[data.currency] = round(float(data.available_balance), 2)
            else:
                liability_data.append([data.name, data.currency + data.available_balance, data.liability_type,
                                       data.created_at])
                if data.currency in total_liability_dict:
                    total_liability_dict[data.currency] = round(total_liability_dict[data.currency] +
                                                                float(data.available_balance), 2)
                else:
                    currency_count_list.append(data.currency)
                    total_liability_dict[data.currency] = round(float(data.available_balance), 2)
                if fun_name != "dash_board":
                    overtime_account_data(transaction_data, current_balance, balance_graph_dict, date_list,
                                          balance_graph_data,
                                          date_range_list)
                    liability_currency_balance.append({data.currency: balance_graph_data[::-1]})

    for data in property_data:
        if data.include_net_worth:
            if data.currency in total_property_dict:
                total_property_dict[data.currency] = round(total_property_dict[data.currency] +
                                                           float(data.value), 2)
            else:
                currency_count_list.append(data.currency)
                total_property_dict[data.currency] = round(float(data.value), 2)

            property_currency_balance.append({data.currency: data.value})

    total_currency_list = list(dict.fromkeys(currency_count_list))

    for name in total_currency_list:
        if name in total_liability_dict:
            total_liability = total_liability_dict[name]
        else:
            total_liability = 0
        if name in total_asset_amount_dict:
            total_assets = total_asset_amount_dict[name]
        else:
            total_assets = 0
        if name in total_property_dict:
            total_property = total_property_dict[name]
        else:
            total_property = 0

        net_worth_dict[name] = total_assets + total_property - total_liability

    if fun_name == "dash_board":
        return net_worth_dict
    else:
        return net_worth_dict, assets_data, liability_data, total_asset_amount_dict, total_liability_dict, \
               total_property_dict, asset_currency_balance, liability_currency_balance, property_currency_balance, \
               total_currency_list, date_range_list


def overtime_account_data(transaction_data, current_balance, balance_graph_dict, date_list, balance_graph_data,
                          date_range_list):
    account_index = 1
    for data in transaction_data:
        if account_index == 1:
            balance_graph_dict[str(data.transaction_date)] = round(current_balance, 2)
            print(balance_graph_dict)
            if data.out_flow:
                amount_list = [float("-" + data.amount)]
                current_balance += float(data.amount)
            else:
                amount_list = [float(data.amount)]
                current_balance -= float(data.amount)
            date_list.append(str(data.transaction_date))

        else:
            if str(data.transaction_date) in date_list:
                date_index = date_list.index(str(data.transaction_date))
                if data.out_flow:
                    amount_list.append(float("-" + data.amount))
                    current_balance += float(data.amount)
                else:
                    amount_list.append(float(data.amount))
                    current_balance -= float(data.amount)

                if sum(amount_list) < 0:
                    result_value = current_balance + sum(amount_list)
                else:
                    result_value = current_balance - sum(amount_list)
                balance_graph_dict[str(data.transaction_date)] = round(result_value, 2)
            else:
                balance_graph_dict[str(data.transaction_date)] = round(current_balance, 2)
                date_list.append(str(data.transaction_date))

                if data.out_flow:
                    amount_list = [float("-" + data.amount)]
                    current_balance += float(data.amount)
                else:
                    amount_list = [float(data.amount)]
                    current_balance -= float(data.amount)
        account_index += 1
    date_range_index = 1

    if balance_graph_dict:
        balance_key = list(balance_graph_dict.keys())[-1]
        if sum(amount_list) < 0:
            starting_balance = balance_graph_dict[balance_key] - sum(amount_list)
        else:
            starting_balance = balance_graph_dict[balance_key] + sum(amount_list)

        for date_value in date_range_list:
            if date_value in balance_graph_dict:
                graph_value = balance_graph_dict[date_value]
                balance_graph_data.append(graph_value)
            else:
                if date_range_index == len(date_range_list):
                    print("Latest DAe--------------->", date_value)
                    balance_graph_data.append(current_balance)
                else:
                    try:
                        balance_graph_data.append(graph_value)
                    except:
                        balance_graph_data.append(balance_graph_dict[balance_key])
            date_range_index += 1
    else:
        for date_value in date_range_list:
            balance_graph_data.append(round(current_balance, 2))


def home(request):
    user_name = request.user
    if not request.user.is_anonymous:
        categories = Category.objects.filter(user=user_name)
        all_transaction_data = Transaction.objects.filter(user=user_name)
        accounts_data = Account.objects.filter(user=user_name)
        property_data = Property.objects.filter(user=user_name)
        budget_data = Budget.objects.filter(user=user_name)
        budget_label = []
        budget_values = []
        budget_percentage = []
        total_budget = 0
        categories_name = []
        categories_value = []
        acc_graph_data = []
        acc_min_max_value_list = []
        asset_currency_balance = []
        liability_currency_balance = []
        property_currency_balance = []

        if accounts_data:
            min_date = accounts_data[0].created_at.date()
            max_date = datetime.datetime.today().date()
            day_diff = (max_date - min_date).days
            account_date_list = [str(max_date - datetime.timedelta(days=x)) for x in range(day_diff)]
            account_date_list.append(str(min_date))
            account_date_list = account_date_list[::-1]
        else:
            account_date_list = []
        for acc_obj in accounts_data:
            account_transaction_value = []
            acc_create_date = acc_obj.created_at.date()
            amount_date_dict = {}
            if acc_obj.lock_amount:
                acc_current_balance = float(acc_obj.balance) - float(acc_obj.lock_amount)
            else:
                acc_current_balance = float(acc_obj.balance)

            acc_available_balance = float(acc_current_balance)
            acc_transaction_data = Transaction.objects.filter(user=user_name, account__pk=acc_obj.pk).order_by(
                'transaction_date')
            multi_acc_chart(acc_transaction_data, amount_date_dict, acc_current_balance, account_date_list,
                            acc_create_date, account_transaction_value, acc_available_balance)
            graph_dict = {'label_name': acc_obj.name, 'data_value': account_transaction_value}
            acc_graph_data.append(graph_dict)
            acc_min_max_value_list.append(min(account_transaction_value))
            acc_min_max_value_list.append(max(account_transaction_value))

        for data in property_data:
            property_currency_balance.append({data.currency: data.value})

        category_spent_amount(categories, user_name, categories_name, categories_value)

        for data in budget_data:
            total_budget += float(data.amount)
            budget_label.append(data.name)
            budget_values.append(float(data.amount))

        for value in budget_values:
            result = round((value / total_budget) * 100, 2)
            budget_percentage.append(result)

        net_worth_dict = net_worth_cal(accounts_data, property_data, account_date_list, fun_name="dash_board")
        print(net_worth_dict)
        if acc_min_max_value_list:
            acc_max_value = max(acc_min_max_value_list)
            acc_min_value = min(acc_min_max_value_list)
        else:
            acc_max_value = 0
            acc_min_value = 0

        print("Assets_currency_data", asset_currency_balance)
        print("Liabiliy_currency_data", liability_currency_balance)
        print("Property_currency_data", property_currency_balance)

        context = {
            "categories_name": categories_name,
            "categories_value": categories_value,
            "account_graph_data": acc_graph_data,
            "date_range_list": account_date_list,
            "graph_label": budget_label,
            "graph_value": budget_percentage,
            "net_worth_dict": net_worth_dict,
            "max_value": acc_max_value,
            "min_value": acc_min_value
        }
    else:
        context = {}
    return render(request, 'dashboard.html', context=context)


def net_worth(request):
    user_name = request.user
    account_data = Account.objects.filter(user=user_name)
    property_data = Property.objects.filter(user=user_name)
    all_transaction_data = Transaction.objects.filter(user=user_name)
    if account_data:
        min_date = account_data[0].created_at.date()
        max_date = datetime.datetime.today().date()
        day_diff = (max_date - min_date).days
        account_date_list = [str(max_date - datetime.timedelta(days=x)) for x in range(day_diff)]
        account_date_list.append(str(min_date))
        account_date_list = account_date_list

    currency_dict = {
        "$": 'US Dollar ($)',
        "€": 'Euro (€)',
        "₹": 'Indian rupee (₹)',
        "£": 'British Pound (£)',
    }
    net_worth_dict, assets_data, liability_data, total_asset_amount_dict, total_liability_dict, \
    total_property_dict, asset_currency_balance, liability_currency_balance, property_currency_balance, \
    total_currency_list, date_range_list = net_worth_cal(account_data, property_data, account_date_list)

    print("Assets_currency_data", asset_currency_balance)
    print("Liabiliy_currency_data", liability_currency_balance)
    print("Property_currency_data", property_currency_balance)
    print(total_currency_list)
    asset_total_dict = {}
    liability_total_dict = {}
    net_worth_graph_list = []
    min_max_value_list = []

    for currency_index in range(len(asset_currency_balance)):
        asset_currency_name = list(asset_currency_balance[currency_index])[0]
        balance_data = asset_currency_balance[currency_index][asset_currency_name]
        print("asset_currency_name", asset_currency_name)
        print("currency_name", currency_index)
        if asset_currency_name in total_currency_list:
            if asset_currency_name in asset_total_dict:
                sum_balance_data = [x + y for (x, y) in zip(asset_total_dict[asset_currency_name], balance_data)]
                asset_total_dict[asset_currency_name] = sum_balance_data
            else:
                asset_total_dict[asset_currency_name] = balance_data

    for currency_index in range(len(liability_currency_balance)):
        liability_currency_name = list(liability_currency_balance[currency_index])[0]
        liability_balance_data = liability_currency_balance[currency_index][liability_currency_name]
        if liability_currency_name in total_currency_list:
            if asset_currency_name in liability_total_dict:
                sum_liab_data = [x + y for (x, y) in
                                 zip(liability_total_dict[liability_currency_name], liability_balance_data)]
                liability_total_dict[liability_currency_name] = sum_liab_data
            else:
                liability_total_dict[liability_currency_name] = liability_balance_data

    print(asset_total_dict)
    print(liability_total_dict)
    print(total_property_dict)
    for name in total_currency_list:
        net_worth_list = []
        for net_worth_index in range(len(date_range_list)):
            overtime_net_worth = 0
            if name in asset_total_dict:
                overtime_net_worth += asset_total_dict[name][net_worth_index]
            if name in total_property_dict:
                overtime_net_worth += total_property_dict[name]
                print("overtime_net_worth=====>", overtime_net_worth)
            if name in liability_total_dict:
                overtime_net_worth -= liability_total_dict[name][net_worth_index]
            net_worth_list.append(overtime_net_worth)
            min_max_value_list.append(overtime_net_worth)
        net_worth_graph_dict = {'label_name': name, 'data_value': net_worth_list}
        net_worth_graph_list.append(net_worth_graph_dict)

    if min_max_value_list:
        max_value = max(min_max_value_list)
        min_value = min(min_max_value_list)
    else:
        max_value = 0
        min_value = 0

    context = {
        "property_data": property_data,
        "assets_data": assets_data,
        "liability_data": liability_data,
        "total_asset_amount_dict": total_asset_amount_dict,
        "total_liability_dict": total_liability_dict,
        "total_property_dict": total_property_dict,
        "net_worth_dict": net_worth_dict,
        "currency_dict": currency_dict,
        "account_graph_data": net_worth_graph_list,
        "date_range_list": date_range_list[::-1],
        "max_value": max_value,
        "min_value": min_value

    }
    return render(request, "net_worth.html", context=context)


class CategoryList(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'category/category_list.html'

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        data = super(CategoryList, self).get_context_data(**kwargs)
        user_name = self.request.user
        category_data = Category.objects.filter(user=self.request.user)
        categories_name = []
        categories_value = []

        for category_name in category_data:
            spent_value = 0
            category_transaction_data = Transaction.objects.filter(user=user_name, categories=category_name)
            for transaction_data in category_transaction_data:
                spent_value += float(transaction_data.amount)
            if spent_value != 0:
                categories_name.append(category_name.name)
                categories_value.append(spent_value)

        category_key = ['S.No.', 'Name', 'Last Activity']
        data['category_data'] = category_data
        data['categories_name'] = categories_name
        data['categories_name_dumbs'] = json.dumps(categories_name)
        data['category_key'] = category_key
        data['category_key_dumbs'] = json.dumps(category_key)
        data['categories_value'] = categories_value

        return data


class CategoryDetail(DetailView):
    model = Category
    template_name = 'category/category_detail.html'


class CategoryAdd(CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'category/category_add.html'

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        user_name = self.request.user
        data = super(CategoryAdd, self).get_context_data(**kwargs)
        categories_list = list(Category.objects.filter(user=user_name).values_list('name', flat=True))
        category_suggestions = SuggestiveCategory.objects.all().values_list('name', flat=True)
        suggestion_list = []
        for name in category_suggestions:
            if name not in categories_list:
                suggestion_list.append(name)
        data['category_suggestions'] = suggestion_list
        return data

    def form_valid(self, form):
        name = form.cleaned_data.get('name').title()
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.name = name
        obj.save()
        return super().form_valid(form)

    def get_success_url(self):
        """Detect the submit button used and act accordingly"""
        if 'add_other' in self.request.POST:
            url = reverse_lazy('category_add')
        else:
            url = reverse_lazy('category_list')
        return url


class CategoryUpdate(UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'category/category_update.html'


class CategoryDelete(DeleteView):
    def post(self, request, *args, **kwargs):
        category_obj = Category.objects.get(pk=self.kwargs['pk'])
        category_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


def user_login(request):
    if request.method == 'POST':
        next = request.POST['next']
        username = request.POST['register-username']
        password = request.POST['register-password']
        user = authenticate(username=username, password=password)
        if user is None:
            context = {'login_error': 'Username and Password Incorrect'}
            return render(request, "login_page.html", context)
        elif not user.is_active:
            context = {'login_error': 'User is not active'}
            return render(request, "login_page.html", context)
        else:
            login(request, user)
            if next:
                return redirect(next)
            else:
                return redirect('/')
    else:
        next = request.GET['next']
        return render(request, "login_page.html", context={'next': next})


def user_logout(request):
    logout(request)
    return redirect('/login')


class BudgetList(LoginRequiredMixin, ListView):
    model = Budget
    template_name = 'budget/budget_list.html'

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        data = super(BudgetList, self).get_context_data(**kwargs)
        user_name = self.request.user
        budget_data = Budget.objects.filter(user=user_name)

        budget_key = ['S.No.', 'Name', 'budget Amount', 'Spent Amount', 'Left Amount', 'Last Updated']
        revenue_values = []
        revenue_data = Revenues.objects.filter(user=user_name).order_by('month')
        revenue_month = []
        revenue_name = []
        for revenue_value in revenue_data:
            revenue_month.append(revenue_value.month)
            if revenue_value.primary:
                revenue_name.insert(1, revenue_value.name)
            else:
                revenue_name.append(revenue_value.name)

        revenue_month = list(dict.fromkeys(revenue_month))
        revenue_name = list(dict.fromkeys(revenue_name))
        print(revenue_name)
        for month in revenue_month:
            obj_data = {'month': datetime.datetime.strftime(month, "%B, %y")}
            for name in revenue_name:
                revenue_obj = Revenues.objects.filter(user=user_name, month=month, name=name)
                if revenue_obj:
                    currency_name = revenue_obj[0].currency
                    obj_data[revenue_obj[0].id] = revenue_obj[0].currency + revenue_obj[0].amount
                else:
                    new_revenue_obj = Revenues()
                    new_revenue_obj.non_primary = True
                    revenue_save(new_revenue_obj, user_name, name, "0", month, currency_name)
                    obj_data[new_revenue_obj.id] = currency_name + "0"
            revenue_values.append(obj_data)

        revenue_name.insert(0, 'Month')
        data['budget_data'] = budget_data
        data['budget_key'] = budget_key
        data['budget_key_dumbs'] = json.dumps(budget_key)
        data['revenue_keys'] = revenue_name
        data['revenue_values'] = revenue_values
        print('revenue_values', revenue_values)
        return data


class BudgetDetail(LoginRequiredMixin, DetailView):
    model = Budget
    template_name = 'budget/budget_detail.html'


class BudgetAdd(LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budget/budget_add.html'

    def get_context_data(self, **kwargs):
        data = super(BudgetAdd, self).get_context_data(**kwargs)
        category_suggestions = SuggestiveCategory.objects.all().values_list('name', flat=True)
        data['category_suggestions'] = category_suggestions
        return data

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return super().form_valid(form)


class BudgetUpdate(LoginRequiredMixin, UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budget/budget_update.html'


class BudgetDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        property_obj = Budget.objects.get(pk=self.kwargs['pk'])
        property_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


# class BillList(LoginRequiredMixin, ListView):
#     model = Bill
#     template_name = 'bill/bill_list.html'
#
#     def get_queryset(self):
#         return Bill.objects.filter(user=self.request.user)
#
#
# class BillDetail(LoginRequiredMixin, DetailView):
#     model = Bill
#     template_name = 'bill/bill_detail.html'
#
#
# class BillAdd(LoginRequiredMixin, CreateView):
#     model = Bill
#     form_class = BillForm
#     template_name = 'bill/bill_add.html'
#
#     def form_valid(self, form):
#         obj = form.save(commit=False)
#         obj.user = self.request.user
#         obj.save()
#         return super().form_valid(form)
#
#
# class BillUpdate(LoginRequiredMixin, UpdateView):
#     model = Bill
#     form_class = BillForm
#     template_name = 'bill/bill_update.html'
#
#
# class BillDelete(LoginRequiredMixin, DeleteView):
#     model = Bill
#     form_class = BillForm
#     template_name = 'bill/bill_delete.html'

@login_required(login_url="/login")
def transaction_list(request):
    user_name = request.user
    if request.method == "POST":
        tag_name = request.POST['tag_name']
        tags_data = request.POST['tags_data']
        print("tags_data", tags_data)
        if tag_name != 'All':
            transaction_data = Transaction.objects.filter(user=user_name, tags=tag_name)
        else:
            transaction_data = Transaction.objects.filter(user=user_name)
        select_filter = tag_name
    else:
        transaction_data = Transaction.objects.filter(user=user_name)
        select_filter = 'All'

    context = transaction_summary(transaction_data, select_filter)
    return render(request, 'transaction/transaction_list.html', context=context)


def transaction_report(request):
    user_name = request.user
    if request.method == "POST":
        tag_name = request.POST['tag_name']
        tags_data = request.POST['tags_data']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        tags_data = ast.literal_eval(tags_data)
        if tag_name != 'All':
            transaction_data = Transaction.objects.filter(user=user_name,
                                                          transaction_date__range=(start_date, end_date), tags=tag_name)
        else:
            transaction_data = Transaction.objects.filter(user=user_name,
                                                          transaction_date__range=(start_date, end_date))
        select_filter = tag_name
    else:
        start_date = request.GET['start_date']
        end_date = request.GET['end_date']
        transaction_data = Transaction.objects.filter(user=user_name, transaction_date__range=(start_date, end_date))
        select_filter = 'All'

    context = transaction_summary(transaction_data, select_filter)
    context['start_date'] = start_date
    context['end_date'] = end_date
    return render(request, 'transaction/transaction_list.html', context=context)


class TransactionDetail(LoginRequiredMixin, DetailView):
    model = Transaction
    template_name = 'transaction/transaction_detail.html'


class TransactionAdd(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transaction/transaction_add.html'

    def get_form_kwargs(self):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""

        kwargs = super(TransactionAdd, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_success_url(self):
        """Detect the submit button used and act accordingly"""
        if 'add_other' in self.request.POST:
            url = reverse_lazy('transaction_add')
        else:
            url = reverse_lazy('transaction_list')
        return url

    def form_valid(self, form):
        obj = form.save(commit=False)
        user_name = self.request.user
        obj.user = user_name
        account = form.cleaned_data.get('account')
        transaction_amount = round(float(form.cleaned_data.get('amount')), 2)
        tags = form.cleaned_data.get('tags')
        if tags:
            obj.tags = tags
        out_flow = form.cleaned_data.get('out_flow')
        cleared_amount = form.cleaned_data.get('cleared')
        bill_name = form.cleaned_data.get('bill')
        budget_name = form.cleaned_data.get('budgets')
        account = account.name
        account_obj = transaction_checks(user_name, transaction_amount, account, bill_name,
                                         budget_name, cleared_amount, out_flow)
        obj.remaining_amount = account_obj.available_balance
        obj.save()
        return super().form_valid(form)


class TransactionUpdate(LoginRequiredMixin, UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'transaction/transaction_update.html'

    def get_form_kwargs(self):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""

        kwargs = super(TransactionUpdate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        transaction_obj = Transaction.objects.get(pk=self.kwargs['pk'])
        account = transaction_obj.account.name.title()
        transaction_amount = round(float(transaction_obj.amount), 2)
        transaction_out_flow = transaction_obj.out_flow
        update_account = form.cleaned_data.get('account').name.title()
        update_transaction_amount = round(float(form.cleaned_data.get('amount')), 2)
        out_flow = form.cleaned_data.get('out_flow')
        cleared_amount = form.cleaned_data.get('cleared')
        bill_name = form.cleaned_data.get('bill')
        budget_name = form.cleaned_data.get('budgets')
        print(out_flow)
        print("out_flow======>", type(out_flow))

        if cleared_amount == "True":
            if account == update_account:
                account_obj = Account.objects.get(user=self.request.user, name=account)
                if transaction_amount != update_transaction_amount:
                    if transaction_out_flow:
                        account_obj.available_balance = round(float(account_obj.available_balance) + transaction_amount,
                                                              2)
                    else:
                        account_obj.available_balance = round(float(account_obj.available_balance) - transaction_amount,
                                                              2)

                    if out_flow:
                        account_obj.available_balance = round(
                            float(account_obj.available_balance) - update_transaction_amount, 2)
                    else:
                        account_obj.available_balance = round(
                            float(account_obj.available_balance) + update_transaction_amount, 2)


            else:
                old_account_obj = Account.objects.get(user=self.request.user, name=account)
                account_obj = Account.objects.get(user=self.request.user, name=update_account)

                if transaction_out_flow:
                    old_account_obj.available_balance = round(
                        float(old_account_obj.available_balance) + transaction_amount, 2)
                else:
                    old_account_obj.available_balance = round(
                        float(old_account_obj.available_balance) - transaction_amount, 2)

                if out_flow:
                    account_obj.available_balance = round(
                        float(account_obj.available_balance) - update_transaction_amount, 2)
                else:
                    account_obj.available_balance = round(
                        float(account_obj.available_balance) + update_transaction_amount, 2)

                account_obj.transaction_count += 1
                old_account_obj.transaction_count -= 1

                old_account_obj.save()

            transaction_obj.remaining_amount = account_obj.available_balance
            transaction_obj.save()
            account_obj.save()

            if bill_name:
                bill_name = bill_name.label
                bill_obj = Bill.objects.filter(user=self.request.user, label=bill_name)[0]
            else:
                bill_obj = False

            if bill_obj:
                transaction_bill_name = transaction_obj.bill
                bill_obj_amount = round(float(bill_obj.amount), 2)
                if transaction_bill_name == bill_name:
                    if transaction_amount != update_transaction_amount:
                        bill_obj_amount = bill_obj_amount + transaction_amount
                else:
                    old_bill_obj = Bill.objects.filter(user=self.request.user, label=transaction_bill_name)
                    if old_bill_obj:
                        old_bill_obj_amount = round(float(old_bill_obj.amount), 2)
                        old_bill_obj.amount = old_bill_obj_amount + transaction_amount
                        if old_bill_obj.amount > 0.0:
                            old_bill_obj.status = "unpaid"
                        else:
                            old_bill_obj.status = "paid"

                        old_bill_obj.save()

                if update_transaction_amount >= bill_obj_amount:
                    bill_obj.status = "paid"
                    bill_obj.amount = bill_obj_amount - update_transaction_amount
                else:
                    bill_obj.status = "unpaid"
                    bill_obj.amount = bill_obj_amount - update_transaction_amount
                bill_obj.save()

            if budget_name:
                budget_name = budget_name.name
                budget_obj = Budget.objects.filter(user=self.request.user, name=budget_name)[0]
            else:
                try:
                    transaction_budget_name = transaction_obj.budgets
                    budget_obj = Budget.objects.filter(user=self.request.user, name=transaction_budget_name)
                    if transaction_out_flow:
                        budget_obj.budget_spent = round(float(budget_obj.budget_spent) - transaction_amount, 2)
                    else:
                        budget_obj.amount = round(float(budget_obj.amount) - transaction_amount, 2)
                    budget_obj.save()
                    budget_obj = False
                except:
                    budget_obj = False

            if budget_obj:
                transaction_budget_name = transaction_obj.budgets.name
                if transaction_budget_name == budget_name:
                    if out_flow != transaction_out_flow or transaction_amount != update_transaction_amount:
                        if transaction_out_flow:
                            budget_obj.budget_spent = round(float(budget_obj.budget_spent) - transaction_amount, 2)
                        else:
                            budget_obj.amount = round(float(budget_obj.amount) - transaction_amount, 2)

                        if out_flow == "True":
                            budget_obj.budget_spent = round(float(budget_obj.budget_spent) + update_transaction_amount,
                                                            2)
                        else:
                            budget_obj.amount = round(float(budget_obj.amount) + update_transaction_amount, 2)
                else:
                    old_budget_obj = Budget.objects.filter(user=self.request.user, name=transaction_budget_name)[0]
                    if transaction_out_flow:
                        old_budget_obj.budget_spent = round(
                            float(transaction_obj.budgets.budget_spent) - transaction_amount, 2)
                    else:
                        old_budget_obj.amount = round(float(transaction_obj.budgets.amount) - transaction_amount, 2)

                    old_budget_obj.save()

                    if out_flow == "True":
                        budget_obj.budget_spent = round(float(budget_obj.budget_spent) + update_transaction_amount, 2)
                    else:
                        budget_obj.amount = round(float(budget_obj.amount) + update_transaction_amount, 2)

                budget_obj.save()

        return super().form_valid(form)


class TransactionDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        transaction_obj = Transaction.objects.get(pk=self.kwargs['pk'])
        out_flow = transaction_obj.out_flow
        cleared_amount = transaction_obj.cleared
        account = transaction_obj.account
        try:
            bill_name = transaction_obj.bill
        except:
            bill_name = False
        try:
            budget_name = transaction_obj.budgets
        except:
            budget_name = False

        transaction_amount = float(transaction_obj.amount)
        print("out_flow", type(out_flow))
        print("cleared_amount", type(cleared_amount))
        print("bill_name", bill_name)
        print("budget_name", budget_name)

        if cleared_amount:
            account_obj = Account.objects.get(user=self.request.user, name=account.name)

            if bill_name:
                bill_name = bill_name.label
                bill_obj = Bill.objects.filter(user=self.request.user, label=bill_name)[0]
                if out_flow:
                    bill_obj.amount = round(float(bill_obj.amount) + transaction_amount, 2)
                else:
                    bill_obj.amount = round(float(bill_obj.amount) - transaction_amount, 2)

                bill_obj.amount = bill_obj.amount
                bill_obj.save()

            if budget_name:
                budget_name = budget_name.name
                budget_obj = Budget.objects.filter(user=self.request.user, name=budget_name)[0]

                if out_flow:
                    budget_obj.budget_spent = round(float(budget_obj.budget_spent) - transaction_amount, 2)
                else:
                    budget_obj.amount = round(float(budget_obj.amount) - transaction_amount, 2)

                budget_obj.amount = budget_obj.amount
                budget_obj.save()

            if out_flow:
                account_obj.available_balance = round(float(account_obj.available_balance) + transaction_amount, 2)
            else:
                account_obj.available_balance = round(float(account_obj.available_balance) - transaction_amount, 2)

            account_obj.transaction_count -= 1
            account_obj.save()

        transaction_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


class GoalList(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'goal/goal_list.html'

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)


class GoalDetail(LoginRequiredMixin, DetailView):
    model = Goal
    template_name = 'goal/goal_detail.html'


class GoalAdd(LoginRequiredMixin, CreateView):
    model = Goal
    form_class = GoalForm
    template_name = 'goal/goal_add.html'

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return super().form_valid(form)


class GoalUpdate(LoginRequiredMixin, UpdateView):
    model = Goal
    form_class = GoalForm
    template_name = 'goal/goal_update.html'


class GoalDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        goal_obj = Goal.objects.get(pk=self.kwargs['pk'])
        goal_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


class AccountList(LoginRequiredMixin, ListView):
    model = Account
    template_name = 'account/account_list.html'

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)


class AccountDetail(LoginRequiredMixin, DetailView):
    model = Account
    template_name = 'account/account_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account_pk = self.kwargs['pk']
        account_obj = Account.objects.get(pk=account_pk)
        current_balance = float(account_obj.available_balance)
        initial_balance = current_balance
        transaction_data = Transaction.objects.filter(user=self.request.user, account__pk=account_pk).order_by(
            'transaction_date')[::-1]
        date_list = []
        balance_graph_data = []
        transaction_graph_value = []
        index = 1
        for data in transaction_data:
            if data.cleared:
                if index == 1:
                    graph_dict = {'x': str(data.transaction_date), 'y': round(initial_balance, 2)}
                    if data.out_flow:
                        amount_list = [float("-" + data.amount)]
                        current_balance += float(data.amount)
                    else:
                        amount_list = [float(data.amount)]
                        current_balance -= float(data.amount)
                    date_list.append(str(data.transaction_date))
                    balance_graph_data.append(graph_dict)
                else:
                    if str(data.transaction_date) in date_list:
                        date_index = date_list.index(str(data.transaction_date))
                        if data.out_flow:
                            amount_list.append(float("-" + data.amount))
                            current_balance += float(data.amount)
                        else:
                            amount_list.append(float(data.amount))
                            current_balance -= float(data.amount)

                        if sum(amount_list) < 0:
                            result_value = current_balance + sum(amount_list)
                        else:
                            result_value = current_balance - sum(amount_list)
                        balance_graph_data[date_index]['y'] = round(result_value, 2)
                    else:
                        graph_dict = {'x': str(data.transaction_date),
                                      'y': round(current_balance, 2)}
                        balance_graph_data.append(graph_dict)
                        date_list.append(str(data.transaction_date))

                        if data.out_flow:
                            amount_list = [float("-" + data.amount)]
                            current_balance += float(data.amount)
                        else:
                            amount_list = [float(data.amount)]
                            current_balance -= float(data.amount)
                index += 1

        if balance_graph_data:
            if sum(amount_list) < 0:
                starting_balance = balance_graph_data[-1]['y'] - sum(amount_list)
            else:
                starting_balance = balance_graph_data[-1]['y'] + sum(amount_list)

            amount_diff = initial_balance - starting_balance
            amount_inc_percentage = round(amount_diff / starting_balance * 100, 2)
            for data in balance_graph_data:
                transaction_graph_value.append(data['y'])
        else:
            amount_diff = 0
            amount_inc_percentage = 0

        print(balance_graph_data)
        transaction_key = ['S.No.', 'Date', 'Amount', 'Payee', 'Account', 'Categories', 'Bill', 'Budget', 'Cleared']
        context['balance_graph_data'] = balance_graph_data
        context['transaction_data'] = transaction_data
        context['transaction_date_dumbs'] = json.dumps(date_list)
        context['transaction_graph_value'] = transaction_graph_value
        context['transaction_key'] = transaction_key
        context['transaction_key_dumbs'] = json.dumps(transaction_key)
        context['amount_diff'] = amount_diff
        context['amount_inc_percentage'] = amount_inc_percentage

        return context


class AccountAdd(LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'account/account_add.html'

    def form_valid(self, form):
        total_balance = float(form.cleaned_data.get('balance'))
        lock_amount = form.cleaned_data.get('lock_amount')
        lock_check = form.cleaned_data.get('lock_check')
        print("lock_check=====>", lock_check)
        if lock_amount != "None" and lock_amount and lock_check == "True":
            available_balance = total_balance - float(lock_amount)
        else:
            available_balance = total_balance
            lock_amount = ""
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.lock_amount = lock_amount
        obj.available_balance = round(available_balance, 2)
        obj.save()
        return super().form_valid(form)


class AccountUpdate(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'account/account_update.html'

    def form_valid(self, form):
        total_balance = float(form.cleaned_data.get('balance'))
        lock_amount = form.cleaned_data.get('lock_amount')
        lock_check = form.cleaned_data.get('lock_check')
        print("lock_check=====>", lock_check)
        if lock_amount != "None" and lock_amount and lock_check == "True":
            available_balance = total_balance - float(lock_amount)
        else:
            available_balance = total_balance
            lock_amount = ""
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.lock_amount = lock_amount
        obj.available_balance = round(available_balance, 2)
        obj.save()
        return super().form_valid(form)


class AccountDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        account_obj = Account.objects.get(pk=self.kwargs['pk'])
        account_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "/account_list/"})


class LiabilityAdd(LoginRequiredMixin, CreateView):
    # model = Account
    form_class = LiabilityForm
    template_name = 'liability/liability_add.html'

    def post(self, request, *args, **kwargs):
        name = request.POST['name']
        currency = request.POST['currency']
        liability_type = request.POST['liability_type']
        balance = request.POST['available_balance']
        interest_rate = request.POST['interest_rate']
        interest_period = request.POST['interest_period']
        try:
            include_net_worth = request.POST['include_net_worth']
            include_net_worth = True
        except:
            include_net_worth = False
        liability_obj = Account()
        liability_obj.user = request.user
        liability_obj.name = name
        liability_obj.currency = currency
        liability_obj.liability_type = liability_type
        liability_obj.available_balance = balance
        liability_obj.interest_rate = interest_rate
        liability_obj.interest_rate = interest_rate
        liability_obj.interest_period = interest_period
        liability_obj.include_net_worth = include_net_worth
        liability_obj.save()
        return redirect('/liability_list/')


class LiabilityList(LoginRequiredMixin, ListView):
    model = Account
    template_name = 'liability/liability_list.html'

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)


class LiabilityUpdate(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = LiabilityForm
    template_name = 'liability/liability_update.html'

    def post(self, request, *args, **kwargs):
        name = request.POST['name']
        currency = request.POST['currency']
        liability_type = request.POST['liability_type']
        balance = request.POST['available_balance']
        interest_rate = request.POST['interest_rate']
        interest_period = request.POST['interest_period']
        try:
            include_net_worth = request.POST['include_net_worth']
            include_net_worth = True
        except:
            include_net_worth = False
        liability_obj = Account.objects.get(pk=self.kwargs['pk'])
        liability_obj.name = name
        liability_obj.currency = currency
        liability_obj.liability_type = liability_type
        liability_obj.available_balance = balance
        liability_obj.interest_rate = interest_rate
        liability_obj.interest_rate = interest_rate
        liability_obj.interest_period = interest_period
        liability_obj.include_net_worth = include_net_worth
        liability_obj.save()
        return redirect('/liability_list/')


class LiabilityDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        liability_obj = Account.objects.get(pk=self.kwargs['pk'])
        liability_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "/liability_list/"})


class LiabilityDetail(LoginRequiredMixin, DetailView):
    model = Account
    template_name = 'liability/liability_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account_pk = self.kwargs['pk']
        account_obj = Account.objects.get(pk=account_pk)
        current_balance = float(account_obj.available_balance)
        initial_balance = current_balance
        transaction_data = Transaction.objects.filter(user=self.request.user, account__pk=account_pk).order_by(
            'transaction_date')[::-1]
        date_list = []
        balance_graph_data = []
        index = 1
        for data in transaction_data:
            if index == 1:
                graph_dict = {'x': str(data.transaction_date), 'y': round(initial_balance, 2)}
                if data.out_flow:
                    amount_list = [float("-" + data.amount)]
                    current_balance += float(data.amount)
                else:
                    amount_list = [float(data.amount)]
                    current_balance -= float(data.amount)
                date_list.append(str(data.transaction_date))
                balance_graph_data.append(graph_dict)
            else:
                if str(data.transaction_date) in date_list:
                    date_index = date_list.index(str(data.transaction_date))
                    if data.out_flow:
                        amount_list.append(float("-" + data.amount))
                        current_balance += float(data.amount)
                    else:
                        amount_list.append(float(data.amount))
                        current_balance -= float(data.amount)

                    if sum(amount_list) < 0:
                        result_value = current_balance + sum(amount_list)
                    else:
                        result_value = current_balance - sum(amount_list)
                    balance_graph_data[date_index]['y'] = round(result_value, 2)
                else:
                    graph_dict = {'x': str(data.transaction_date),
                                  'y': round(current_balance, 2)}
                    balance_graph_data.append(graph_dict)
                    date_list.append(str(data.transaction_date))

                    if data.out_flow:
                        amount_list = [float("-" + data.amount)]
                        current_balance += float(data.amount)
                    else:
                        amount_list = [float(data.amount)]
                        current_balance -= float(data.amount)
            index += 1

        if balance_graph_data:
            if sum(amount_list) < 0:
                starting_balance = balance_graph_data[-1]['y'] - sum(amount_list)
            else:
                starting_balance = balance_graph_data[-1]['y'] + sum(amount_list)

            amount_diff = initial_balance - starting_balance
            amount_inc_percentage = round(amount_diff / starting_balance * 100, 2)
        else:
            amount_diff = 0
            amount_inc_percentage = 0

        transaction_key = ['S.No.', 'Date', 'Amount', 'Payee', 'Account', 'Categories', 'Bill', 'Budget', 'Cleared']
        context['balance_graph_data'] = balance_graph_data
        context['transaction_data'] = transaction_data
        context['transaction_key'] = transaction_key
        context['transaction_key_dumbs'] = json.dumps(transaction_key)
        context['amount_diff'] = amount_diff
        context['amount_inc_percentage'] = amount_inc_percentage
        return context


def bill_list(request):
    bill_data = Bill.objects.filter(user=request.user)

    calendar_bill_data = []

    for data in bill_data:
        data_dict = {'label': data.label,
                     'date': str(data.date),
                     'label_id': data.id
                     }
        if data.status == "unpaid":
            data_dict['calendar_type'] = 'Personal'
        else:
            data_dict['calendar_type'] = 'Holiday'

        calendar_bill_data.append(data_dict)

    context = {"calendar_bill_data": calendar_bill_data}
    return render(request, "bill/bill_list.html", context)


def bill_detail(request, pk):
    bill_obj = Bill.objects.get(pk=pk)
    transaction_data = Transaction.objects.filter(bill=bill_obj)
    context = {"bill_data": bill_obj, 'transaction_data': transaction_data}
    return render(request, "bill/bill_detail.html", context)


def bill_add(request):
    form = BillForm(request.POST or None)
    if form.is_valid():
        label = form.cleaned_data.get('label')
        amount = form.cleaned_data.get('amount')
        bill_date = form.cleaned_data.get('date')
        frequency = form.cleaned_data.get('frequency')
        currency = form.cleaned_data.get('currency')

        bill_obj = Bill()
        bill_obj.user = request.user
        bill_obj.label = label
        bill_obj.amount = amount
        bill_obj.date = bill_date
        bill_obj.currency = currency
        bill_obj.remaining_amount = amount
        bill_obj.frequency = frequency
        bill_obj.save()
        return redirect("/bill_list")

    context = {
        'form': form
    }
    return render(request, "bill/bill_add.html", context=context)


def bill_update(request, pk):
    bill_obj = Bill.objects.get(pk=pk)
    currency_dict = {
        "$": 'US Dollar ($)',
        "€": 'Euro (€)',
        "₹": 'Indian rupee (₹)',
        "£": 'British Pound (£)',
    }

    form = BillForm(request.POST or None)
    if form.is_valid():
        label = form.cleaned_data.get('label')
        amount = form.cleaned_data.get('amount')
        bill_date = form.cleaned_data.get('date')
        frequency = form.cleaned_data.get('frequency')
        currency = form.cleaned_data.get('currency')

        bill_obj.label = label
        bill_obj.amount = amount
        bill_obj.remaining_amount = amount
        bill_obj.date = bill_date
        bill_obj.currency = currency
        bill_obj.frequency = frequency
        bill_obj.save()
        return redirect(f"/bill_detail/{pk}")

    print("bill_date======>", bill_obj.date)
    print("bill_date======>", type(bill_obj.date))
    context = {
        'form': form,
        'bill_data': bill_obj,
        'currency_dict': currency_dict
    }
    return render(request, "bill/bill_update.html", context=context)


def bill_delete(request, pk):
    bill_obj = Bill.objects.get(pk=pk)
    bill_obj.delete()
    return JsonResponse({"status": "Successfully", "path": "/bill_list/"})


def bill_automatic_amount(request):
    bill_id = request.POST['bill_id']
    bill_obj = Bill.objects.get(pk=bill_id)
    return JsonResponse({'bill_amount': bill_obj.remaining_amount})


def mortgagecalculator(request):
    form = MortgageForm(request.POST or None)
    if form.is_valid():
        amount = form.cleaned_data.get('amount')
        interest = form.cleaned_data.get('interest')
        tenure = form.cleaned_data.get('tenure')
        table = calculator(amount, interest, tenure)
        total_payment = abs(table['principle'].sum() + table['interest'].sum())
        total_month = tenure * 12
        json_records = table.reset_index().to_json(orient='records')
        data = json.loads(json_records)
        monthly_payment = abs(data[0]['principle'] + data[0]['interest'])
        last_date = datetime.date.today() + relativedelta(months=+total_month)
        last_month = f'{calendar.month_name[last_date.month]} {last_date.year}'
        print("data======>", data)
        balance_data = []
        principle_data = []
        interest_data = []
        mortgage_date_data = [str(datetime.date.today() + relativedelta(months=+x)) for x in range(total_month)]

        for value in data:
            balance_data.append(value['initial_balance'])
            principle_data.append(abs(value['principle']))
            interest_data.append(abs(value['interest']))

        mortgage_graph_data = [{'name': 'Balance', 'data': balance_data}, {'name': 'Principle', 'data': principle_data},
                               {'name': 'Interest', 'data': interest_data}]

        mortgage_key = ['Month', 'Initial Balance', 'Principle', 'Interest', 'Ending Balance']
        context = {
            'form': form,
            'data': data,
            'monthly_payment': monthly_payment,
            'last_month': last_month,
            'days': total_month,
            'total_payment': total_payment,
            'mortgage_key': mortgage_key,
            'mortgage_key_dumbs': json.dumps(mortgage_key),
            'mortgage_graph_data': mortgage_graph_data,
            'mortgage_date_data': mortgage_date_data
        }
        return render(request, 'mortgagecalculator_add.html', context)

    context = {
        'form': form
    }
    return render(request, 'mortgagecalculator_add.html', context)


# Properties Views

class PropertyList(LoginRequiredMixin, ListView):
    model = Property
    template_name = 'property/property_list.html'

    def get_queryset(self):
        return Property.objects.filter(user=self.request.user)


class PropertyDetail(LoginRequiredMixin, DetailView):
    model = Property
    template_name = 'property/property_detail.html'


class PropertyAdd(LoginRequiredMixin, CreateView):
    model = Property
    form_class = PropertyForm
    template_name = 'property/property_add.html'

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return super().form_valid(form)


class PropertyUpdate(LoginRequiredMixin, UpdateView):
    model = Property
    form_class = PropertyForm
    template_name = 'property/property_update.html'


class PropertyDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        property_obj = Property.objects.get(pk=self.kwargs['pk'])
        property_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


def fund_list(request):
    user_name = request.user
    fund_data = Account.objects.filter(user=user_name, liability_type=None)
    fund_key = ['S.No.', 'Account Name', 'Total Fund', 'Available Fund', 'Lock Fund']
    context = {
        'fund_data': fund_data,
        'fund_key': fund_key,
        'fund_key_dumbs': json.dumps(fund_key),
    }
    return render(request, 'funds.html', context=context)


class PdfPrint:
    def __init__(self, buffer, pageSize):
        self.buffer = buffer
        # default format is A4
        if pageSize == 'A4':
            self.pageSize = A4
        elif pageSize == 'Letter':
            self.pageSize = letter
        self.width, self.height = self.pageSize

    def report(self, pdf_data_value, title, d=None):
        # set some characteristics for pdf document
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=self.pageSize)
        styles = getSampleStyleSheet()
        # create document
        data = [Paragraph(title, styles['Title'])]
        t = Table(pdf_data_value)
        t.setStyle(TableStyle(
            [('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
             ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
             ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
             ('BACKGROUND', (0, 0), (-1, 0), colors.gray)]))
        # create other flowables

        data.append(t)
        # d.save(formats=['pdf'], outDir='.', fnRoot='test')
        if d:
            data.append(d)
        doc.build(data)
        pdf = self.buffer.getvalue()
        self.buffer.close()
        return pdf


def draw_bar_chart(bar_data, data_label, graph_type):
    d = Drawing(200, 500)
    bar = VerticalBarChart()
    bar.x = 100
    bar.y = 85
    bar.width = 300
    bar.height = 300
    bar.data = bar_data
    bar.valueAxis.valueMin = 0
    bar.barSpacing = 0.5
    bar.categoryAxis.labels.dx = 8
    bar.categoryAxis.labels.dy = -2
    bar.categoryAxis.categoryNames = data_label
    bar.barLabels.nudge = 7
    bar.valueAxis.labels.fontName = 'Helvetica'
    bar.valueAxis.labels.fontSize = 8
    bar.valueAxis.forceZero = 1
    bar.valueAxis.rangeRound = 'both'
    bar.valueAxis.valueMax = None  # 10#
    bar.categoryAxis.visible = 1
    bar.categoryAxis.visibleTicks = 0
    bar.barLabels.fontSize = 6
    bar.valueAxis.labels.fontSize = 6
    bar.strokeWidth = 0.1
    bar.bars.strokeWidth = 0.5
    if graph_type == "bar":
        bar.bars[0].fillColor = PCMYKColor(46, 51, 0, 4)
        d.add(bar)
    else:
        legend = Legend()
        legend.columnMaximum = 10
        legend.fontName = 'Helvetica'
        legend.fontSize = 5.5
        legend.boxAnchor = 'w'
        legend.x = 400
        legend.y = 400
        legend.dx = 16
        legend.dy = 16
        legend.alignment = 'left'
        legend.colorNamePairs = [(colors.red, "Debit"), (colors.green, "Credit")]
        d.add(bar)
        d.add(legend)

    #
    # bar.bars[1].fillColor = PCMYKColor(23, 51, 0, 4, alpha=85)
    # bar.bars.fillColor = PCMYKColor(100, 0, 90, 50, alpha=85)
    return d


@csrf_exempt
def download_pdf(request):
    if request.method == 'POST':
        pdf_data_key = request.POST['csv_data_key']
        pdf_title = request.POST['pdf_title']
        pdf_data_value = request.POST['csv_data_value']
        file_name = request.POST['file_name']
        pdf_data_key = json.loads(pdf_data_key)
        pdf_data_value = json.loads(pdf_data_value)
        pdf_data_value.insert(0, pdf_data_key)
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename={file_name}'
        buffer = BytesIO()
        reporti = PdfPrint(buffer, 'A4')
        try:
            graph_type = request.POST['graph_type']
            print("graph_type=======>", graph_type)
            print(type(graph_type))
            data_label = request.POST['data_label']
            data_value = request.POST['data_value']
            data_label = json.loads(data_label)
            data_value = json.loads(data_value)
            if graph_type == 'transaction-bar':
                credit_value = request.POST['credit_value']
                debit_value = data_value
                credit_value = json.loads(credit_value)
                bar_data = [debit_value, credit_value]
                d = draw_bar_chart(bar_data, data_label, graph_type)

            if graph_type == 'bar':
                bar_data = [data_value]
                print(bar_data)
                d = draw_bar_chart(bar_data, data_label, graph_type)

            if graph_type == 'line':
                print("Line===", data_value)
                d = Drawing(200, 500)
                chart = HorizontalLineChart()
                chart.data = [tuple(data_value[::-1])]
                chart.x = 5
                chart.y = 5
                chart.width = 500
                chart.height = 300
                chart.valueAxis.valueMin = 0
                chart.lines[0].fillColor = colors.orange
                chart.categoryAxis.categoryNames = data_label[::-1]
                d.add(chart)
            pdf = reporti.report(pdf_data_value, pdf_title, d)
        except:
            pdf = reporti.report(pdf_data_value, pdf_title)

        response.write(pdf)
        return response
    return render(request, "test.html")


# Download CSV file

@csrf_exempt
def download_csv(request):
    """
    :param request: Request to Access this Function
    :return: Csv Download response
    """
    print("innnnnnn")

    if request.method == 'POST':
        csv_data_key = request.POST['csv_data_key']
        print("csv_data_key", csv_data_key)
        print("csv_data_key", type(csv_data_key))
        csv_data_value = request.POST['csv_data_value']
        print("csv_data_value", csv_data_value)
        file_name = request.POST['file_name']
        csv_data_key = json.loads(csv_data_key)
        csv_data_value = json.loads(csv_data_value)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={file_name}'
        writer = csv.writer(response)
        writer.writerow(csv_data_key)
        for data in csv_data_value:
            writer.writerow(data)
        return response


def transaction_upload(request):
    if request.method == "POST" and request.is_ajax:
        print("iIIIIIIINnn")
        try:
            test_file = request.FILES['csv_file']
            df = pd.read_csv(test_file)
            print(df)
            for index, row in df.iterrows():
                my_transaction = Transaction()
                user_name = request.user
                my_transaction.user = user_name
                category_name = row['Categories']
                category_obj = Category.objects.get(user=user_name, name=category_name)
                my_transaction.categories = category_obj
                account = row['Account']
                transaction_amount = row['Amount']
                out_flow = row['Type']
                if out_flow == "Debit":
                    out_flow = "True"
                    my_transaction.out_flow = True
                else:
                    my_transaction.out_flow = False

                cleared_amount = row['Cleared']
                if cleared_amount:
                    cleared_amount = "True"
                transaction_date = row['Date']
                transaction_date = datetime.datetime.strptime(transaction_date, "%d-%m-%Y")
                bill_name = row['Bill']
                budget_name = row['Budget']
                transaction_tags = row['Tags']
                if cleared_amount == "True":
                    account_obj = Account.objects.get(user=user_name, name=account)
                    if bill_name != "None":
                        bill_obj = Bill.objects.filter(user=user_name, label=bill_name)[0]
                    else:
                        bill_obj = False

                    if budget_name != "None":
                        budget_obj = Budget.objects.filter(user=user_name, name=budget_name)[0]
                        print("budget_obj", budget_obj)
                    else:
                        budget_obj = False

                    if out_flow == "True":
                        account_obj.available_balance = round(float(account_obj.available_balance) - transaction_amount,
                                                              2)
                    else:
                        account_obj.available_balance = round(float(account_obj.available_balance) + transaction_amount,
                                                              2)

                    if bill_obj:
                        bill_amount = round(float(bill_obj.remaining_amount), 2)
                        if transaction_amount == bill_amount:
                            bill_obj.status = "paid"
                            bill_obj.remaining_amount = bill_amount - transaction_amount
                        else:
                            bill_obj.status = "unpaid"
                            bill_obj.amount = bill_amount - transaction_amount
                        bill_obj.save()
                        my_transaction.bill = bill_obj
                    if budget_obj:
                        if out_flow == "True":
                            budget_obj.budget_spent = round(float(budget_obj.budget_spent) + transaction_amount, 2)
                        else:
                            budget_obj.amount = round(float(budget_obj.amount) + transaction_amount, 2)
                        budget_obj.save()
                        my_transaction.budgets = budget_obj
                    account_obj.transaction_count += 1
                    account_obj.save()
                    my_transaction.remaining_amount = account_obj.available_balance

                my_transaction.transaction_date = transaction_date
                my_transaction.payee = row['Payee']
                my_transaction.account = account_obj
                my_transaction.amount = row['Amount']
                my_transaction.tags = transaction_tags
                my_transaction.cleared = cleared_amount
                my_transaction.save()
            return JsonResponse({'status': 'File Uploaded'})
        except:
            return JsonResponse({'status': 'Uploading Failed!! Please Check File Format'})


@login_required(login_url="/login")
def stock_analysis(request):
    url = "http://vuexy.myds.me:8000/api/portfolio/list/"
    portfolio_response = requests.get(url, data={'user_name': request.user.username}, timeout=500)
    portfolio_list = portfolio_response.json()

    if request.method == 'POST':
        p_name = request.POST['p_name']
    else:
        p_name = portfolio_list[0]

    my_portfolio_url = "http://vuexy.myds.me:8000/api/my_portfolio/list/"
    url_response = requests.post(my_portfolio_url, data={'user_name': request.user.username, 'p_name': p_name}, timeout=500)
    my_portfolio_context = url_response.json()
    my_portfolio_context['portfolio_list'] = portfolio_list
    return render(request, 'stock_analysis.html', context=my_portfolio_context)


# REVENUE ADD

def revenue_save(revenue_object, user_name, name, amount, month_name, currency):
    revenue_object.user = user_name
    revenue_object.name = name
    revenue_object.amount = amount
    revenue_object.month = month_name
    revenue_object.currency = currency
    revenue_object.save()


def revenue_add(request):
    if request.method == 'POST':
        revenue_obj = Revenues()
        user_name = request.user
        name = request.POST['name']
        amount = request.POST['amount']
        month = request.POST['start_month']
        currency = request.POST['currency']
        primary = request.POST['revenue_type']
        month = datetime.datetime.strptime(month, '%Y-%m')
        if primary == "non-prime":
            revenue_obj.non_primary = True
            revenue_save(revenue_obj, user_name, name, amount, month, currency)
        else:
            end_month = request.POST['end_month']
            end_month = datetime.datetime.strptime(end_month, '%Y-%m')
            today_month = datetime.datetime.today().date().strftime('%Y-%m')
            today_month = datetime.datetime.strptime(today_month, '%Y-%m')
            if today_month > month:
                months_list = list(OrderedDict(((month + datetime.timedelta(_)).strftime(r"%b-%y"), None) for _ in range((today_month - month).days + 1)).keys())
                for month_name in months_list:
                    month_name = datetime.datetime.strptime(month_name, '%b-%y')
                    revenue_value = Revenues.objects.filter(user=user_name, month=month_name)
                    if revenue_value:
                        for data in revenue_value:
                            revenue_object = data
                    else:
                        revenue_object = Revenues()

                    revenue_object.end_month = end_month
                    revenue_object.primary = True
                    revenue_save(revenue_object, user_name, name, amount, month_name, currency)
            else:
                revenue_obj.end_month = end_month
                revenue_obj.primary = True
                revenue_save(revenue_obj, user_name, name, amount, month, currency)

        if 'add_other' in request.POST:
            return redirect("/revenue_add/")
        else:
            return redirect("/budget_list/")
    else:
        current = datetime.datetime.today()
        current_month = datetime.datetime.strftime(current, '%Y-%m')
        context = {'current_month': current_month}
        return render(request, "revenue/revenue_add.html", context=context)


# REVENUE UPDATE

def revenue_update(request, pk):

    revenue_obj = Revenues.objects.get(pk=int(pk))

    if request.method == 'POST':
        user_name = request.user
        name = request.POST['name']
        amount = request.POST['amount']
        month = request.POST['start_month']
        currency = request.POST['currency']
        primary = request.POST['revenue_type']
        month = datetime.datetime.strptime(month, '%Y-%m').date()
        obj_month = revenue_obj.month
        if month != obj_month:
            try:
                new_revenue_obj = Revenues.objects.get(user=user_name, month=month, name=name)
                revenue_save(new_revenue_obj, user_name, name, amount, month, currency)
            except:
                context = {
                    'name': revenue_obj.name,
                    'start_date': datetime.datetime.strftime(month, '%Y-%m'),
                    'amount': revenue_obj.amount,
                    'currency': revenue_obj.currency,
                    'primary': revenue_obj.primary,
                    'pk': pk,
                    'error': '*Month not present in your income!! Please Select Another or'
                }
                return render(request, "revenue/revenue_update.html", context=context)
            revenue_obj.amount = '0'
            revenue_obj.save()
        else:
            print("innnn")
            revenue_save(revenue_obj, user_name, name, amount, month, currency)
        return redirect("/budget_list/")
    else:
        start_date = datetime.datetime.strftime(revenue_obj.month, '%Y-%m')
        context = {
                    'name': revenue_obj.name,
                    'start_date': start_date,
                    'amount': revenue_obj.amount,
                    'currency': revenue_obj.currency,
                    'primary': revenue_obj.primary,
                    'pk': pk
                  }
        return render(request, "revenue/revenue_update.html", context=context)


# REVENUE DELETE

def revenue_delete(request):
    return render(request, "revenue/revenue_add.html")


def revenue_update_name(request, pk):
    if request.method == 'POST':
        name = request.POST['name']
        user_name = request.user
        if name != pk:
            revenue_obj = Revenues.objects.filter(user=user_name, name=pk)
            check_revenue = Revenues.objects.filter(user=user_name, name=name)
            if check_revenue:
                context = {
                    'name': pk,
                    'fun_name': 'only_name',
                    'error': 'Name already exists enter another name or'
                }
                return render(request, "revenue/revenue_update.html", context=context)
            else:
                for data in revenue_obj:
                    data.name = name
                    data.save()
        return redirect("/budget_list/")
    else:
        context = {
                   'name': pk,
                   'fun_name': 'only_name'
        }
    return render(request, "revenue/revenue_update.html", context=context)



# EXPENSES ADD

def expenses_add(request):
    if request.method == 'POST':
        user_name = request.user
        category = request.POST['category']
        name = request.POST['name']
        amount = request.POST['amount']
        month = request.POST['month']
        expenses_obj = Expenses()
        expenses_obj.user = user_name
        expenses_obj.name = name
        expenses_obj.amount = amount
        expenses_obj.month = month
        expenses_obj.save()
    else:
        current = datetime.datetime.today()
        current_month = datetime.datetime.strftime(current, '%y-%m')
        context = {'current_month': current_month}
    return render(request, "revenue/revenue_add.html", context=context)


# EXPENSES UPDATE

def expenses_update(request):
    return render(request, "revenue/revenue_update.html")


# EXPENSES DELETE

def expenses_delete(request):
    return render(request, "revenue/revenue_add.html")
