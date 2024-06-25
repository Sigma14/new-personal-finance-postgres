import ast
import csv
import json
import calendar
import time
import pandas as pd
import datetime

import pytz
from dateutil import relativedelta
from io import BytesIO
import base64
from collections import OrderedDict
from django.contrib.auth.decorators import login_required
import requests
from django.db.models import Sum
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from dateutil.relativedelta import relativedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.widgets.markers import makeMarker
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A0, letter
from reportlab.lib.colors import PCMYKColor
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib.units import inch
from reportlab.platypus.flowables import Spacer
from reportlab.lib.validators import Auto
from reportlab.lib.enums import TA_CENTER
from finance.settings import stock_app_url
from .forms import CategoryForm, LoginForm, BudgetForm, BillForm, TransactionForm, AccountForm, TemplateBudgetForm, \
    MortgageForm, LiabilityForm, MaintenanceForm, ExpenseForm
from .helper import create_categories, check_subcategory_exists, save_fund_obj, create_category_group, \
    sub_category_suggested_list, create_bill_request, check_bill_is_due, save_transaction, save_income, \
    save_income_details, create_income_request, get_period_date, start_end_date, save_budgets, create_budget_request, \
    dict_value_to_list, get_template_budget, get_cmp_data, get_cmp_diff_data
from .models import Category, Budget, Bill, Transaction, Goal, Account, SuggestiveCategory, Property, Revenues, \
    Expenses, AvailableFunds, TemplateBudget, RentalPropertyModel, PropertyPurchaseDetails, MortgageDetails, \
    ClosingCostDetails, RevenuesDetails, ExpensesDetails, CapexBudgetDetails, PropertyRentalInfo, PropertyInvoice, \
    PropertyMaintenance, PropertyExpense, PlaidItem, SubCategory, BillDetail, Income, IncomeDetail, StockHoldings, Tag
from .mortgage import calculator, calculate_tenure
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

wordpress_api_key = "YWxoyNoKNBmPmXy413m3jxYhTZ"
currency_dict = {'$': "US Dollar ($)", '€': 'Euro (€)', '₹': 'Indian rupee (₹)', '£': 'British Pound (£)'}
scenario_dict = {'best_case': "Best Case Scenario Purchase Price", 'likely_case': 'Likely Case Scenario Purchase Price',
                 'worst_case': 'Worst Case Scenario Purchase Price'}
property_type_list = ['Apartment', 'Commercial', 'Condo', 'Duplex', 'House', 'Mixed-Use', 'Other']
month_date_dict = {'1': '1st ', '2': '2nd ', '3': '3rd ', '4': '4th ', '5': '5th ', '6': '6th ', '7': '7th ',
                   '8': '8th ', '9': '9th ', '10': '10th', '11': '11th', '12': '12th', '13': '13th', '14': '14th',
                   '15': '15th', '16': '16th', '17': '17th', '18': '18th', '19': '19th', '20': '20th', '21': '21st',
                   '22': '22nd', '23': '23rd', '24': '24th', '25': '25th', '26': '26th', '27': '27th', '28': '28th',
                   '29': '29th', '30': '30th'}
today_date = datetime.date.today()

# plaid Intergration
import plaid
from plaid import ApiClient
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode

configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': "628518dd9002d30018305066",
        'secret': "e14271c91cbc26e38782ed74bfa0cf",
    }
)
api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

from django.utils.translation import gettext as _

wordpress_domain = "https://simplefinancial.org"
wordpress_api_key = "F4ARzxSFjQpZxqjt5jiJn7HlXqMu23Y"


@ensure_csrf_cookie
def create_link_token(request):
    user = request.user
    client_user_id = user.id
    if user.is_authenticated:
        # Create a link_token for the given user
        request = LinkTokenCreateRequest(
            products=[Products("transactions")],
            client_name="Personal Finance App",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(
                client_user_id=str(client_user_id)
            )
        )
        response = client.link_token_create(request)
        response = response.to_dict()
        print("response==========>", response)
        link_token = response['link_token']
        print("link_token====>", link_token)
        return JsonResponse({'link_token': link_token})
    else:
        return HttpResponseRedirect('/login')


def get_access_token(request):
    global access_token
    user = request.user

    if user.is_authenticated:
        body_data = json.loads(request.body.decode())
        public_token = body_data["public_token"]
        accounts = body_data["accounts"]
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(request)
        access_token = exchange_response['access_token']
        item_id = exchange_response['item_id']
        plaid_item = None

        try:
            plaid_item = user.plaiditem_set.get(item_id=item_id)
        except:
            new_plaid_item = PlaidItem(user=user, access_token=access_token, item_id=item_id)
            new_plaid_item.save()
            plaid_item = user.plaiditem_set.get(item_id=item_id)

        print('accounts=============>', accounts)
        for account in accounts:
            try:
                existing_acct = user.account_set.get(plaid_account_id=account['account_id'])
                continue
            except:
                new_acct = Account()
                new_acct.plaid_account_id = account['id']
                new_acct.balance = account['balances']['current']
                new_acct.available_balance = account['balances']['available']
                new_acct.mask = account['mask']
                new_acct.name = account['name']
                new_acct.subtype = account['subtype']
                new_acct.account_type = account['type']
                new_acct.user = user
                new_acct.item = plaid_item
                new_acct.save()

        # Pretty printing in development
        json.dumps(exchange_response, sort_keys=True, indent=4)
        print(exchange_response)

    return redirect('/login')


def get_transactions(request):
    user = request.user
    if user.is_authenticated:
        transactions = []
        plaid_items = user.plaiditem_set.all()
        if request.method == 'POST':
            start_date = request.POST['start_date']
            end_date = request.POST['end_date']
        else:
            timespan_weeks = 4 * 24  # Plaid only goes back 24 months
            start_date = '{:%Y-%m-%d}'.format(datetime.now() + datetime.timedelta(weeks=(-timespan_weeks)))
            end_date = '{:%Y-%m-%d}'.format(datetime.now())
        for item in plaid_items:
            try:
                access_token = item.access_token
                request = TransactionsGetRequest(
                    access_token=access_token,
                    start_date=start_date,
                    end_date=end_date,
                    options=TransactionsGetRequestOptions()
                )
                response = client.transactions_get(request)

                transactions = response['transactions']
                accounts = response['accounts']
                error = None

                for account in accounts:
                    try:
                        existing_acct = user.account_set.get(plaid_account_id=account['account_id'])
                        continue
                    except:
                        new_acct = Account()
                        new_acct.plaid_account_id = account['id']
                        new_acct.balance = account['balances']['current']
                        new_acct.available_balance = account['balances']['available']
                        new_acct.mask = account['mask']
                        new_acct.name = account['name']
                        new_acct.subtype = account['subtype']
                        new_acct.account_type = account['type']
                        new_acct.user = user
                        new_acct.item = item
                        new_acct.save()

                while len(transactions) < response['total_transactions']:
                    request = TransactionsGetRequest(
                        access_token=access_token,
                        start_date=start_date,
                        end_date=end_date,
                        options=TransactionsGetRequestOptions(
                            offset=len(transactions)
                        )
                    )
                    response = client.transactions_get(request)
                    transactions.extend(response['transactions'])

                for transaction in transactions:
                    try:
                        existing_trans = user.transaction_set.get(plaid_transaction_id=transaction['transaction_id'])
                        print("Transaction already exist")
                        continue
                    except Transaction.DoesNotExist:
                        category_name = transaction['category']
                        if category_name:
                            try:
                                category_obj = Category.objects.get(user=user, name=category_name[-1])
                            except:
                                category_obj = Category()
                                category_obj.user = user
                                category_obj.name = category_name[-1]
                                category_obj.save()
                        else:
                            category_obj = Category()
                            category_obj.user = user
                            category_obj.name = 'Account Summary'
                            category_obj.save()

                        transaction_obj = Transaction()
                        transaction_obj.user = user
                        transaction_obj.amount = transaction['amount']
                        transaction_obj.transaction_date = transaction['date']
                        transaction_obj.categories = category_obj
                        transaction_obj.account = user.account_set.get(plaid_account_id=transaction['account_id'])
                        transaction_obj.payee = transaction.get('name', '')
                        transaction_obj.tags = 'Account Summary'
                        transaction_obj.cleared = True

                        transaction_obj.save()
            except Exception as e:
                print(e)
            # error = {'display_message': 'You need to link your account.' }
        json.dumps(transactions, sort_keys=True, indent=4)
        return HttpResponseRedirect('/', {'error': error, 'transactions': transactions})
    else:
        return redirect('/login')


def check_zero_division(first_val, second_val):
    try:
        return first_val / second_val
    except:
        return 0


def save_rental_property(request, rental_obj, property_purchase_obj, mortgage_obj, closing_cost_obj, revenue_obj,
                         expense_obj, capex_budget_obj, property_name, currency_name, user_name, property_image):
    # Investor Details
    investor_detail = others_costs_data(request.POST.getlist('investor_detail'))

    # Budget Details
    roof = request.POST.getlist('roof')
    water_heater = request.POST.getlist('water_heater')
    all_appliances = request.POST.getlist('all_appliances')
    bathroom = request.POST.getlist('bathroom')
    drive_way = request.POST.getlist('drive_way')
    furnace = request.POST.getlist('furnace')
    air_conditioner = request.POST.getlist('air_conditioner')
    flooring = request.POST.getlist('flooring')
    plumbing = request.POST.getlist('plumbing')
    electrical = request.POST.getlist('electrical')
    windows = request.POST.getlist('windows')
    paint = request.POST.getlist('paint')
    kitchen = request.POST.getlist('kitchen')
    structure = request.POST.getlist('structure')
    component = request.POST.getlist('component')
    landscaping = request.POST.getlist('landscaping')
    others_budgets = request.POST.getlist('other_budget')
    total_budget_cost = request.POST['total_budget_cost']
    others_budgets_len = len(others_budgets)
    avg = 3
    others_budgets_list = []
    last = 0

    while last < others_budgets_len:
        others_budgets_list.append(others_budgets[int(last):int(last + avg)])
        last += avg

    others_budgets_dict = {}
    for val in others_budgets_list:
        others_budgets_dict[val[0]] = [float(val[1]), float(val[2])]

    # Property Purchase Details
    best_case = check_float(request.POST['best_case'])
    likely_case = check_float(request.POST['likely_case'])
    worst_case = check_float(request.POST['worst_case'])
    select_case = request.POST['select_case']
    select_price = float(request.POST['select_price'])
    down_payment = check_float(request.POST['down_payment'])

    property_purchase_obj.user = user_name
    property_purchase_obj.best_case_price = best_case
    property_purchase_obj.likely_case_price = likely_case
    property_purchase_obj.worst_case_price = worst_case
    property_purchase_obj.selected_case = select_case
    property_purchase_obj.selected_price = select_price
    property_purchase_obj.down_payment = down_payment
    property_purchase_obj.save()

    # Mortgage Details
    interest_rate = check_float(request.POST['interest_rate'])
    amortization_year = int(check_float(request.POST['amortization_year']))
    mortgage_start_date = request.POST['mortgage_start_date']
    mortgage_obj.user = user_name
    mortgage_obj.interest_rate = interest_rate
    mortgage_obj.amortization_year = amortization_year
    mortgage_obj.start_date = mortgage_start_date
    mortgage_obj.save()

    # Closing Costs / Renovations Costs Details
    transfer_tax = check_float(request.POST['transfer_tax'])
    legal_fee = check_float(request.POST['legal_fee'])
    title_insurance = check_float(request.POST['title_insurance'])
    inspection = check_float(request.POST['inspection'])
    appraisal_fee = check_float(request.POST['appraisal_fee'])
    appliances = check_float(request.POST['appliances'])
    renovation_cost = check_float(request.POST['renovation_cost'])
    others_cost = others_costs_data(request.POST.getlist('other_cost'))
    down_payment_value = round(select_price * down_payment / 100, 2)
    total_investment = down_payment_value + transfer_tax + legal_fee + title_insurance + inspection + appraisal_fee + appliances + renovation_cost
    for key in others_cost:
        total_investment += others_cost[key]

    closing_cost_obj.user = user_name
    closing_cost_obj.transfer_tax = transfer_tax
    closing_cost_obj.legal_fee = legal_fee
    closing_cost_obj.title_insurance = title_insurance
    closing_cost_obj.inspection = inspection
    closing_cost_obj.appraisal_fee = appraisal_fee
    closing_cost_obj.appliances = appliances
    closing_cost_obj.renovation_cost = renovation_cost
    closing_cost_obj.others_cost = str([others_cost])
    closing_cost_obj.total_investment = total_investment
    closing_cost_obj.save()

    # Monthly Revenue Details
    unit_1 = check_float(request.POST['unit_1'])
    others_revenue_cost = request.POST.getlist('others_revenue_cost')
    rent_increase_assumption = request.POST['rent_increase_assumption']
    others_revenue_cost_dict = {}
    revenue_index = 2
    for data in others_revenue_cost:
        name = f"Unit {revenue_index}"
        others_revenue_cost_dict[name] = check_float(data)
        revenue_index += 1

    total_revenue = float(unit_1)
    for key in others_revenue_cost_dict:
        total_revenue += float(others_revenue_cost_dict[key])

    revenue_obj.user = user_name
    revenue_obj.unit_1 = unit_1
    revenue_obj.total_revenue = total_revenue
    revenue_obj.others_revenue_cost = str([others_revenue_cost_dict])
    revenue_obj.rent_increase_assumption = rent_increase_assumption
    revenue_obj.save()

    # Monthly Expenses Details
    property_tax = check_float(request.POST['property_tax'])
    insurance = check_float(request.POST['insurance'])
    maintenance = check_float(request.POST['maintenance'])
    water = check_float(request.POST['water'])
    gas = check_float(request.POST['gas'])
    electricity = check_float(request.POST['electricity'])
    water_heater_rental = check_float(request.POST['water_heater_rental'])
    other_utilities = others_costs_data(request.POST.getlist('other_utilities'))
    management_fee = check_float(request.POST['management_fee'])
    vacancy = check_float(request.POST['vacancy'])
    capital_expenditure = check_float(request.POST['capital_expenditure'])
    other_expenses = others_costs_data(request.POST.getlist('other_expenses'))
    inflation_assumption = check_float(request.POST['inflation_assumption'])
    appreciation_assumption = check_float(request.POST['appreciation_assumption'])
    total_expenses = property_tax + insurance + maintenance + water + gas + electricity + water_heater_rental + \
                     management_fee + vacancy + capital_expenditure

    for key in other_utilities:
        total_expenses += other_utilities[key]

    for key in other_expenses:
        total_expenses += other_expenses[key]

    expense_obj.user = user_name
    expense_obj.property_tax = property_tax
    expense_obj.insurance = insurance
    expense_obj.maintenance = maintenance
    expense_obj.water = water
    expense_obj.gas = gas
    expense_obj.electricity = electricity
    expense_obj.water_heater_rental = water_heater_rental
    expense_obj.other_utilities = str([other_utilities])
    expense_obj.management_fee = management_fee
    expense_obj.vacancy = vacancy
    expense_obj.capital_expenditure = capital_expenditure
    expense_obj.other_expenses = str([other_expenses])
    expense_obj.total_expenses = total_expenses
    expense_obj.inflation_assumption = inflation_assumption
    expense_obj.appreciation_assumption = appreciation_assumption
    expense_obj.save()

    # Rental Property Model

    rental_obj.user = user_name
    rental_obj.name = property_name
    rental_obj.property_image = property_image
    rental_obj.currency = currency_name
    rental_obj.purchase_price_detail = property_purchase_obj
    rental_obj.mortgage_detail = mortgage_obj
    rental_obj.closing_cost_detail = closing_cost_obj
    rental_obj.monthly_revenue = revenue_obj
    rental_obj.monthly_expenses = expense_obj
    if investor_detail:
        rental_obj.investor_details = [investor_detail]

    # Budget Save

    capex_budget_obj.user = user_name
    capex_budget_obj.roof = roof
    capex_budget_obj.water_heater = water_heater
    capex_budget_obj.all_appliances = all_appliances
    capex_budget_obj.bathroom_fixtures = bathroom
    capex_budget_obj.drive_way = drive_way
    capex_budget_obj.furnance = furnace
    capex_budget_obj.air_conditioner = air_conditioner
    capex_budget_obj.flooring = flooring
    capex_budget_obj.plumbing = plumbing
    capex_budget_obj.electrical = electrical
    capex_budget_obj.windows = windows
    capex_budget_obj.paint = paint
    capex_budget_obj.kitchen = kitchen
    capex_budget_obj.structure = structure
    capex_budget_obj.components = component
    capex_budget_obj.landscaping = landscaping
    capex_budget_obj.other_budgets = [others_budgets_dict]
    capex_budget_obj.total_budget_cost = total_budget_cost
    capex_budget_obj.save()

    rental_obj.capex_budget_details = capex_budget_obj
    rental_obj.save()


def check_float(data_var):
    if data_var:
        try:
            data_var = round(float(data_var), 2)
        except:
            data_var = 0.0
    else:
        data_var = 0.0
    return data_var


def make_capex_budget(result_list):
    try:
        cost_per_year = float(result_list[0]) / float(result_list[1])
    except:
        cost_per_year = 0.0

    cost_per_month = cost_per_year / 12
    result_list.append(round(cost_per_year, 2))
    result_list.append(round(cost_per_month, 2))
    return result_list


def make_others_dict(other_unit_dict):
    for key, units in other_unit_dict.items():
        other_unit_dict[key] = [float(units) * 12]
    return other_unit_dict


def make_other_data(other_unit_dict, year, mortgage_year, rent_increase_assumption):
    for key, unit_value in other_unit_dict.items():
        current_unit = unit_value[-1]
        other_unit_value_increase = round((current_unit * rent_increase_assumption / 100) + current_unit, 2)
        if year != int(mortgage_year):
            unit_value.append(other_unit_value_increase)
            other_unit_dict[key] = unit_value
    return other_unit_dict


def update_budget_items(user_name, budget_obj, transaction_amount, transaction_out_flow, transaction_date,
                        update_transaction_amount=None):
    amount_budget = float(budget_obj.amount)
    spent_budget = round(float(budget_obj.budget_spent) - transaction_amount, 2)
    if update_transaction_amount:
        spent_budget += update_transaction_amount
    period_budget = budget_obj.budget_period
    if budget_obj.category.category.name == "Income":
        transaction_out_flow = True
    if transaction_out_flow:
        budget_obj.budget_spent = spent_budget
        if period_budget == 'Yearly' or period_budget == 'Quarterly':
            budget_left = float(budget_obj.budget_left) + transaction_amount
            budget_obj.budget_left = budget_left - update_transaction_amount
            print("budget_obj.budget_left", budget_obj.budget_left)
            data_budget = Budget.objects.filter(user=user_name, name=budget_obj.name,
                                                created_at=budget_obj.created_at,
                                                ended_at=budget_obj.ended_at)
            for budget_value in data_budget:
                if budget_value.start_date != budget_obj.start_date:
                    budget_value.budget_left = budget_obj.budget_left
                    budget_value.save()
        if period_budget == 'Daily' or period_budget == 'Weekly':
            try:
                budget_obj = Budget.objects.get(user=user_name, name=budget_obj.name, created_at__lte=transaction_date,
                                                ended_at__gte=transaction_date)
                amount_budget = float(budget_obj.amount)
                spent_budget = round(float(budget_obj.budget_spent) - transaction_amount, 2)
                if update_transaction_amount:
                    spent_budget += update_transaction_amount
                budget_obj.budget_spent = spent_budget
            except Exception as e:
                print("Exception=========>", e)
        if period_budget != 'Yearly' and period_budget != 'Quarterly':
            budget_obj.budget_left = round(amount_budget - spent_budget, 2)
    else:
        budget_obj.amount = round(amount_budget - transaction_amount, 2)
        budget_obj.budget_left = round(float(budget_obj.budget_left) - transaction_amount, 2)

        if period_budget == 'Yearly' or period_budget == 'Quarterly':
            data_budget = Budget.objects.filter(user=user_name, name=budget_obj.name,
                                                created_at=budget_obj.created_at, ended_at=budget_obj.ended_at)
            for budget_value in data_budget:
                if budget_value.start_date != budget_obj.start_date:
                    budget_value.amount = budget_obj.amount
                    budget_value.budget_left = budget_obj.budget_left
                    budget_value.save()

    return budget_obj


def add_new_budget_items(user_name, budget_obj, transaction_amount, out_flow, transaction_date=None):
    amount_budget = float(budget_obj.amount)
    spent_budget = round(float(budget_obj.budget_spent) + transaction_amount, 2)
    period_budget = budget_obj.budget_period
    if budget_obj.category.category.name == "Income":
        out_flow = "True"

    if out_flow == "True":
        budget_obj.budget_spent = spent_budget
        if period_budget == 'Yearly' or period_budget == 'Quarterly':
            data_budget = Budget.objects.filter(user=user_name, name=budget_obj.name,
                                                created_at=budget_obj.created_at, ended_at=budget_obj.ended_at)
            for budget_value in data_budget:
                if budget_value.start_date != budget_obj.start_date:
                    spent_budget += float(budget_value.budget_spent)

            for budget_value in data_budget:
                if budget_value.start_date != budget_obj.start_date:
                    budget_value.budget_left = round(amount_budget - spent_budget, 2)
                    budget_value.save()
        if period_budget == 'Daily' or period_budget == 'Weekly':
            try:
                budget_obj = Budget.objects.get(user=user_name, name=budget_obj.name, created_at__lte=transaction_date,
                                                ended_at__gte=transaction_date)
                amount_budget = float(budget_obj.amount)
                spent_budget = round(float(budget_obj.budget_spent) + transaction_amount, 2)
                budget_obj.budget_spent = spent_budget
            except Exception as e:
                print("Exception=========>", e)
        budget_obj.budget_left = round(amount_budget - spent_budget, 2)
    else:
        budget_obj.amount = round(amount_budget + transaction_amount, 2)
        budget_obj.budget_left = round(float(budget_obj.budget_left) + transaction_amount, 2)

        if period_budget == 'Yearly' or period_budget == 'Quarterly':
            data_budget = Budget.objects.filter(user=user_name, name=budget_obj.name,
                                                created_at=budget_obj.created_at, ended_at=budget_obj.ended_at)
            for budget_value in data_budget:
                if budget_value.start_date != budget_obj.start_date:
                    budget_value.amount = budget_obj.amount
                    budget_value.budget_left = budget_obj.budget_left
                    budget_value.save()

    return budget_obj


def add_remains_budget(user_name):
    minimum_budget_date = Budget.objects.filter(user=user_name).order_by('start_date')
    if minimum_budget_date:
        if minimum_budget_date[0].start_date:
            min_date = minimum_budget_date[0].start_date
            max_date = minimum_budget_date[len(minimum_budget_date) - 1].start_date
            budget_date_list = list(OrderedDict(((min_date + datetime.timedelta(_)).replace(day=1), None) for _ in
                                                range((max_date - min_date).days + 1)).keys())
            budget_date_list = list(dict.fromkeys(budget_date_list))
            budgets_names = get_budgets(user_name)
            for date_val in budget_date_list:
                date_end = date_val.replace(day=calendar.monthrange(date_val.year, date_val.month)[1])
                for name in budgets_names:
                    budgets_data = Budget.objects.filter(user=user_name, name=name, start_date=date_val,
                                                         end_date=date_end)
                    check_budget_data = Budget.objects.filter(user=user_name, name=name)[0]
                    check_currency = check_budget_data.currency
                    check_period = check_budget_data.budget_period
                    check_auto = check_budget_data.auto_budget
                    if not budgets_data:
                        save_budgets(user_name, date_val, date_end, name, check_period, check_currency, 0, check_auto,
                                     None, None, 0)


def get_budgets(user_name):
    budget_data = Budget.objects.filter(user=user_name)
    budget_names = []
    for value in budget_data:
        budget_names.append(value.name)

    return list(dict.fromkeys(budget_names))


def compare_budgets(user_name, start, end, budget_names_list):
    total_budget_amount = 0
    total_budget_spent = 0
    month_cmp_start, month_end = start_end_date(start, "Monthly")
    month_cmp_end, month_end = start_end_date(end, "Monthly")
    list_of_cmp_months = []
    yearly_check_list = []
    quarterly_check_list = []
    cmp_total_budget_amount_dict = {}
    cmp_total_budget_spent_dict = {}
    cmp_budgets_dict = {}
    cmp_transaction_budgets = []
    for budget_name in budget_names_list:
        transaction_budget = Transaction.objects.filter(user=user_name, budgets__name=budget_name,
                                                        transaction_date__range=(start, end)).order_by(
            'transaction_date')
        cmp_transaction_budgets.append(transaction_budget)
        cmp_total_budget_amount_dict[budget_name] = 0
        cmp_total_budget_spent_dict[budget_name] = 0
        cmp_budgets_dict[budget_name] = []

    while month_cmp_start <= month_cmp_end:
        list_of_cmp_months.append(month_cmp_start)
        month_cmp_start += relativedelta(months=1)

    for cmp_month in list_of_cmp_months:
        budget_data = Budget.objects.filter(user=user_name, start_date=cmp_month)
        for data in budget_data:
            if data.name not in cmp_budgets_dict:
                cmp_budgets_dict[data.name] = []
                cmp_total_budget_amount_dict[data.name] = 0
                cmp_total_budget_spent_dict[data.name] = 0

            amount_budget = round(float(data.amount), 2)
            amount_budget_left = round(float(data.budget_left), 2)
            amount_budget_spent = round(float(data.budget_spent), 2)
            if data.budget_period != "Quarterly" and data.budget_period != "Yearly":
                if data.budget_status:
                    if amount_budget_spent != 0.0:
                        total_budget_amount += amount_budget_spent
                        cmp_total_budget_amount_dict[data.name] += amount_budget_spent
                else:
                    total_budget_amount += amount_budget
                    cmp_total_budget_amount_dict[data.name] += amount_budget

            else:
                check_end_date = data.ended_at
                if data.budget_period == "Quarterly":
                    if check_end_date not in quarterly_check_list:
                        if data.budget_status:
                            if amount_budget_spent != 0.0:
                                if amount_budget_left < 0:
                                    total_budget_amount += amount_budget
                                    cmp_total_budget_amount_dict[data.name] += amount_budget_spent
                                else:
                                    diff_budget = amount_budget - amount_budget_left
                                    total_budget_amount += diff_budget
                                    cmp_total_budget_amount_dict[data.name] += diff_budget
                        else:
                            total_budget_amount += amount_budget
                            cmp_total_budget_amount_dict[data.name] += amount_budget
                        quarterly_check_list.append(data.ended_at)

                else:
                    if check_end_date not in yearly_check_list:
                        if data.budget_status:
                            if amount_budget_spent != 0.0:
                                if amount_budget_left < 0:
                                    total_budget_amount += amount_budget
                                    cmp_total_budget_amount_dict[data.name] += amount_budget
                                else:
                                    diff_budget = amount_budget - amount_budget_left
                                    total_budget_amount += diff_budget
                                    cmp_total_budget_amount_dict[data.name] += diff_budget
                        else:
                            total_budget_amount += amount_budget
                            cmp_total_budget_amount_dict[data.name] += amount_budget
                        yearly_check_list.append(check_end_date)

    print("total_budget_amount=======>", total_budget_amount)
    transaction_budget = Transaction.objects.filter(user=user_name, budgets__id__isnull=False,
                                                    transaction_date__range=(start, end)).order_by('transaction_date')

    if transaction_budget:
        for trans_data in transaction_budget:
            total_budget_spent += float(trans_data.amount)
            cmp_total_budget_spent_dict[trans_data.budgets.name] += float(trans_data.amount)

    for key in cmp_budgets_dict:
        cmp_total_budget_left = cmp_total_budget_amount_dict[key] - cmp_total_budget_spent_dict[key]
        cmp_budgets_dict[key].append(cmp_total_budget_spent_dict[key])
        cmp_budgets_dict[key].append(cmp_total_budget_left)

    total_budget_left = total_budget_amount - total_budget_spent

    return transaction_budget, [total_budget_spent, total_budget_left], cmp_budgets_dict, cmp_transaction_budgets


def transaction_summary(transaction_data, select_filter, user_name):
    credit_date_dict = {}
    debit_date_dict = {}
    credit_date_list = []
    debit_date_list = []
    date_list = []
    tags_data = []
    start_date = ""
    end_date = ""
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
                if transaction_date in credit_date_dict:
                    credit_date_dict[transaction_date] += float(transaction_amount)
                else:
                    credit_date_dict[transaction_date] = float(transaction_amount)
            date_list.append(str(transaction_date))

    date_list = list(dict.fromkeys(date_list))
    if transaction_data:
        start_date = date_list[-1]
        end_date = date_list[0]
    tags_data = list(Tag.objects.filter(user=user_name).values_list('name', flat=True))
    tags_data.insert(0, 'All')
    for value in date_list:
        if value in debit_date_dict:
            debit_date_list.append(debit_date_dict[value])
            if value not in credit_date_dict:
                credit_date_list.append(0)
        if value in credit_date_dict:
            credit_date_list.append(credit_date_dict[value])
            if value not in debit_date_dict:
                debit_date_list.append(0)

    transaction_key = ['S.No.', 'Date', 'Amount', 'Payee', 'Account', 'Categories', 'Bill', 'Budget']
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
        'debit_graph_data_dumbs': json.dumps(debit_date_list),
        'credit_graph_data_dumbs': json.dumps(credit_date_list),
        'start_date': start_date,
        'end_date': end_date,
    }

    return context


def transaction_checks(username, transaction_amount, account, bill_name, budget_name, cleared_amount, out_flow,
                       transaction_date):
    if cleared_amount == "True":
        account_obj = Account.objects.get(user=username, name=account)

        if bill_name:
            bill_obj = bill_name
        else:
            bill_obj = False

        if budget_name and budget_name != "None":
            date_check = datetime.datetime.strptime(transaction_date, "%Y-%m-%d").date()
            start_month_date, end_month_date = start_end_date(date_check, "Monthly")
            budget_obj = Budget.objects.filter(user=username, name=budget_name, start_date=start_month_date,
                                               end_date=end_month_date)
            if budget_obj:
                budget_obj = budget_obj[0]
            else:
                budget_obj = False
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
                bill_obj.remaining_amount = bill_amount - transaction_amount
            bill_obj.save()

        if budget_obj:
            budget_obj = add_new_budget_items(username, budget_obj, transaction_amount, out_flow, date_check)
            budget_obj.save()
        account_obj.transaction_count += 1
        account_obj.save()
        return account_obj, budget_obj


def category_spent_amount(category_data, user_name, categories_name, categories_value, total_spent_amount):
    for category_name in category_data:
        spent_value = 0
        category_transaction_data = Transaction.objects.filter(user=user_name, categories__category=category_name,
                                                               out_flow=True)
        for transaction_data in category_transaction_data:
            spent_value += float(transaction_data.amount)
            if transaction_data.account.currency in total_spent_amount:
                total_spent_amount[transaction_data.account.currency] += float(transaction_data.amount)
            else:
                total_spent_amount[transaction_data.account.currency] = float(transaction_data.amount)
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

    print("amount_date_ditvc=====>", amount_date_dict)
    print("account_date_list=======>", account_date_list)
    amount_constant = acc_available_balance
    for date_value in account_date_list:
        check_date = datetime.datetime.strptime(date_value, '%Y-%m-%d').date()
        if date_value in amount_date_dict:
            account_transaction_value.append(amount_date_dict[date_value])
            amount_constant = amount_date_dict[date_value]
        else:
            account_transaction_value.append(amount_constant)


def net_worth_cal(account_data, property_data, date_range_list, stock_portfolio_data, fun_name=None):
    liability_data = []
    assets_data = []
    total_asset_amount_dict = {}
    total_liability_dict = {}
    total_property_dict = {}
    total_portfolio_dict = {}
    currency_count_list = []
    net_worth_dict = {}
    asset_currency_balance = []
    liability_currency_balance = []
    property_currency_balance = []
    portfolio_currency_balance = []
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
            if data.account_type != "Mortgage" and data.account_type != "Loan" and data.account_type != "Student Loan" and data.account_type != "Personal Loan" and data.account_type != "Medical Debt" and data.account_type != "Other Loan" and data.account_type != "Other Debt":
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
                liability_data.append([data.name, data.currency + data.available_balance, data.account_type,
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

    start_date = datetime.datetime.today()
    utc_tz = pytz.UTC
    start_date = utc_tz.localize(start_date)
    for data in stock_portfolio_data:
        print("data.end_at=====>", data.end_at)
        print("start_date=====>", start_date)
        print(data.end_at < start_date)
        if data.end_at < start_date:
            print("Inn holdings==")
            data.end_at = start_date + datetime.timedelta(hours=2)
            my_portfolio_url = f"{stock_app_url}/api/portfolio_values/"
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0'}
            print("my_portfolio_url===>", my_portfolio_url)
            url_response = requests.post(my_portfolio_url, headers=headers,
                                         data={'user_name': data.user.username, 'port_id': data.port_id},
                                         timeout=500)
            print("url_response=====>", url_response)
            my_portfolio_context = url_response.json()
            print("my_portfolio_context=====>", my_portfolio_context)
            data.name = my_portfolio_context['name']
            data.value = my_portfolio_context['value']
            data.save()
        if data.currency in total_portfolio_dict:
            total_portfolio_dict[data.currency] = round(total_portfolio_dict[data.currency] +
                                                        float(data.value), 2)
        else:
            currency_count_list.append(data.currency)
            total_portfolio_dict[data.currency] = round(float(data.value), 2)
        portfolio_currency_balance.append({data.currency: data.value})

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
        if name in total_portfolio_dict:
            total_portfolio = total_portfolio_dict[name]
        else:
            total_portfolio = 0
        net_worth_dict[name] = total_assets + total_property + total_portfolio - total_liability

    print("total_assets=============>", total_assets)
    print("total_liability=============>", total_liability)
    print("total_portfolio=============>", total_portfolio)
    print("net_worth_dict=============>", net_worth_dict)
    if fun_name == "dash_board":
        return net_worth_dict
    else:
        return net_worth_dict, assets_data, liability_data, total_asset_amount_dict, total_liability_dict, \
            total_property_dict, asset_currency_balance, liability_currency_balance, property_currency_balance, \
            total_currency_list, date_range_list, portfolio_currency_balance, total_portfolio_dict


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


# from django.utils.translation import get_language, activate, gettext


# Personal Finance Home Page
def home(request):
    # trans = translate(language='fr')
    context = {"page": "home"}
    return render(request, "home.html", context)


# def translate(language):
#     cur_language = get_language()
#     try:
#         activate(language)
#         text = gettext('hello')
#     finally:
#         activate(cur_language)
#     return text 


# Real Estate Home Page
def real_estate_home(request):
    print("real_estate")
    context = {"page": "real_estate_home"}
    return render(request, "real_estate_home.html", context)


@login_required(login_url="/login")
def dash_board(request):
    user_name = request.user
    if not request.user.is_anonymous:
        categories = Category.objects.filter(user=user_name)
        all_transaction_data = Transaction.objects.filter(user=user_name).order_by('transaction_date')
        current_date = datetime.datetime.today().date()
        month_start, month_end = start_end_date(current_date, "Monthly")
        accounts_data = Account.objects.filter(user=user_name, account_type__in=['Checking', 'Savings', 'Cash',
                                                                                 'Credit Card', 'Line of Credit'])
        property_data = Property.objects.filter(user=user_name)
        stock_portfolio_data = StockHoldings.objects.filter(user=user_name)
        budget_data = Budget.objects.filter(user=user_name)
        bills_data = Bill.objects.filter(user=user_name)
        # income_data = Income.objects.filter(user=user_name)
        budget_label = []
        budget_values = []
        budget_percentage = []
        total_budget = 0
        total_account_balance = {}
        total_spent_amount = {}
        categories_name = []
        categories_value = []
        acc_graph_data = []
        acc_min_max_value_list = []
        asset_currency_balance = []
        liability_currency_balance = []
        property_currency_balance = []
        income_label = []
        income_values = []
        bill_graph_dict = {}
        bill_label = []
        bill_values = []
        budget_spent_dict = {}
        income_spent_dict = {}

        for bill in bills_data:
            bill_name = bill.bill_details.label
            if bill_name not in bill_graph_dict:
                bill_graph_dict[bill_name] = 0
                bill_transactions = all_transaction_data.filter(categories__category__name='Bills & Subscriptions',
                                                                categories__name=bill_name, out_flow=True)
                if bill_transactions:
                    bills_amount = 0
                    for bill_t in bill_transactions:
                        bill_graph_dict[bill_name] += float(bill_t.amount)

        for key, value in bill_graph_dict.items():
            bill_label.append(key)
            bill_values.append(value)

        if accounts_data and all_transaction_data:
            account_min_date = accounts_data[0].created_at.date()
            transaction_min_date = all_transaction_data[0].transaction_date
            if transaction_min_date < account_min_date:
                min_date = transaction_min_date
            else:
                min_date = account_min_date
            max_date = datetime.datetime.today().date()
            day_diff = (max_date - min_date).days
            account_date_list = [str(max_date - datetime.timedelta(days=x)) for x in range(day_diff)]
            account_date_list.append(str(min_date))
            account_date_list = account_date_list[::-1]
            for acc_obj in accounts_data:
                if acc_obj.currency in total_account_balance:
                    total_account_balance[acc_obj.currency] = total_account_balance[acc_obj.currency] + float(
                        acc_obj.available_balance)
                else:
                    total_account_balance[acc_obj.currency] = float(acc_obj.available_balance)
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

        else:
            if accounts_data:
                for acc_obj in accounts_data:
                    if acc_obj.currency in total_account_balance:
                        total_account_balance[acc_obj.currency] = total_account_balance[acc_obj.currency] + float(
                            acc_obj.available_balance)
                    else:
                        total_account_balance[acc_obj.currency] = float(acc_obj.available_balance)
            account_date_list = []

        for data in property_data:
            property_currency_balance.append({data.currency: data.value})

        category_spent_amount(categories, user_name, categories_name, categories_value, total_spent_amount)
        budget_currency = '$'

        # for income in income_data:
        #     income_transactions = all_transaction_data.filter(categories__category__name='Income',
        #                                                       categories=income.sub_category, out_flow=False)
        #     if income_transactions:
        #         income_amount = 0
        #         for income_t in income_transactions:
        #             income_amount += float(income_t.amount)
        #         income_label.append(income.sub_category.name)
        #         income_values.append(income_amount)

        for data in budget_data:
            budget_currency = data.currency
            category_group_name = data.category.category.name
            if category_group_name == 'Income':
                if data.name in income_spent_dict:
                    income_spent_dict[data.name] += float(data.budget_spent)
                else:
                    income_spent_dict[data.name] = float(data.budget_spent)
            else:
                if data.name in budget_spent_dict:
                    budget_spent_dict[data.name] += float(data.budget_spent)
                else:
                    budget_spent_dict[data.name] = float(data.budget_spent)

        for key, value in budget_spent_dict.items():
            budget_label.append(key)
            budget_values.append(round(value, 2))

        for key, value in income_spent_dict.items():
            income_label.append(key)
            income_values.append(round(value, 2))

        budget_label += bill_label
        budget_values += bill_values

        all_account_data = Account.objects.filter(user=user_name)
        net_worth_dict = net_worth_cal(all_account_data, property_data, account_date_list, stock_portfolio_data,
                                       fun_name="dash_board")
        if acc_min_max_value_list:
            acc_max_value = max(acc_min_max_value_list)
            acc_min_value = min(acc_min_max_value_list)
        else:
            acc_max_value = 0
            acc_min_value = 0

        context = {
            "categories_name": categories_name,
            "categories_series": [{'name': 'Spend', 'data': categories_value}],
            "categories_value": categories_value,
            "account_graph_data": acc_graph_data,
            "date_range_list": account_date_list,
            "graph_label": budget_label,
            "graph_value": budget_values,
            "graph_currency": budget_currency,
            "graph_id": "#budget-chart",
            "bill_label": bill_label,
            "bill_value": bill_values,
            "bill_currency": budget_currency,
            "bill_id": "#bill-chart",
            "income_label": income_label,
            "income_value": income_values,
            "income_currency": budget_currency,
            "income_id": "#income-chart",
            "net_worth_dict": net_worth_dict,
            "max_value": acc_max_value,
            "min_value": acc_min_value,
            "total_account_balance": total_account_balance,
            "total_spent_amount": total_spent_amount
        }
        return render(request, "dashboard.html", context=context)
    else:
        next = None
        return render(request, "login_page.html", context={'next': next})


@login_required(login_url="/login")
def net_worth(request):
    user_name = request.user
    account_data = Account.objects.filter(user=user_name)
    property_data = Property.objects.filter(user=user_name)
    all_transaction_data = Transaction.objects.filter(user=user_name)
    stock_portfolio_data = StockHoldings.objects.filter(user=user_name)

    if account_data:
        min_date = account_data[0].created_at.date()
        max_date = datetime.datetime.today().date()
        day_diff = (max_date - min_date).days
        account_date_list = [str(max_date - datetime.timedelta(days=x)) for x in range(day_diff)]
        account_date_list.append(str(min_date))
        account_date_list = account_date_list
    else:
        account_date_list = []

    net_worth_dict, assets_data, liability_data, total_asset_amount_dict, total_liability_dict, \
        total_property_dict, asset_currency_balance, liability_currency_balance, property_currency_balance, \
        total_currency_list, date_range_list, portfolio_currency_balance, total_portfolio_dict = net_worth_cal(
        account_data, property_data, account_date_list, stock_portfolio_data)

    asset_total_dict = {}
    liability_total_dict = {}
    net_worth_graph_list = []
    min_max_value_list = []

    if asset_currency_balance:
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

    if liability_currency_balance:
        for currency_index in range(len(liability_currency_balance)):
            liability_currency_name = list(liability_currency_balance[currency_index])[0]
            liability_balance_data = liability_currency_balance[currency_index][liability_currency_name]
            if liability_currency_name in total_currency_list:
                if liability_currency_name in liability_total_dict:
                    sum_liab_data = [x + y for (x, y) in
                                     zip(liability_total_dict[liability_currency_name], liability_balance_data)]
                    liability_total_dict[liability_currency_name] = sum_liab_data
                else:
                    liability_total_dict[liability_currency_name] = liability_balance_data
    for name in total_currency_list:
        net_worth_list = []
        for net_worth_index in range(len(date_range_list)):
            overtime_net_worth = 0
            if name in asset_total_dict:
                overtime_net_worth += asset_total_dict[name][net_worth_index]
            if name in total_property_dict:
                overtime_net_worth += total_property_dict[name]
            if name in total_portfolio_dict:
                overtime_net_worth += total_portfolio_dict[name]
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
        "portfolio_data": stock_portfolio_data,
        "assets_data": assets_data,
        "liability_data": liability_data,
        "total_asset_amount_dict": total_asset_amount_dict,
        "total_liability_dict": total_liability_dict,
        "total_property_dict": total_property_dict,
        "total_portfolio_dict": total_portfolio_dict,
        "net_worth_dict": net_worth_dict,
        "currency_dict": currency_dict,
        "account_graph_data": net_worth_graph_list,
        "date_range_list": date_range_list[::-1],
        "max_value": max_value,
        "min_value": min_value

    }
    return render(request, "net_worth.html", context=context)


# # Property Views
#
# class PropertyAdd(LoginRequiredMixin, CreateView):
#     model = Property
#     form_class = PropertyForm
#     template_name = 'properties/add_property.html'
#
#     def form_valid(self, form):
#         name = form.cleaned_data.get('name').title()
#         obj = form.save(commit=False)
#         obj.user = self.request.user
#         obj.name = name
#         obj.save()
#         return super().form_valid(form)
#
#
# class PropertyList(LoginRequiredMixin, ListView):
#     model = Property
#     template_name = 'properties/list_property.html'
#
#     def get_context_data(self, **kwargs):
#         # self.request = kwargs.pop('request')
#         data = super(PropertyList, self).get_context_data(**kwargs)
#         user_name = self.request.user
#         property_data = Property.objects.filter(user=user_name)
#         property_key = ['S.No.', 'Name', 'Value', 'Last Activity']
#         property_name = []
#         property_value = []
#
#         for obj in property_data:
#             property_name.append(obj.name)
#             property_value.append(obj.value)
#
#         data['property_data'] = property_data
#         data['property_key'] = property_key
#         data['categories_name'] = property_name
#         data['categories_name_dumbs'] = json.dumps(property_name)
#         data['category_key_dumbs'] = json.dumps(property_key)
#         data['categories_value'] = property_value
#         data['categories_series'] = [{'name': 'Value', 'data': property_value}]
#
#         return data
#
#
# class PropertyUpdate(LoginRequiredMixin, UpdateView):
#     model = Property
#     form_class = PropertyForm
#     template_name = 'properties/property_update.html'
#
#
# class PropertyDelete(LoginRequiredMixin, DeleteView):
#     def post(self, request, *args, **kwargs):
#         property_obj = Property.objects.get(pk=self.kwargs['pk'])
#         property_obj.delete()
#         return JsonResponse({"status": "Successfully", "path": "None"})

# Icons for Categoris page
category_icons = {
        "Rent/Mortgage": "app-assets/images/categories/Rent.png",
        "Electricity": 'app-assets/images/categories/Electricity.png',
        "Water": "app-assets/images/categories/Water-Bill.png",
        "Internet": "app-assets/images/categories/Internet.png",
        "New Car": "app-assets/images/categories/Car.png",
        "Insurance": "app-assets/images/categories/Insurance.png",
        "Cellphone": "app-assets/images/categories/Phone.png",
        "Netflix Subscription": "app-assets/images/categories/Netflix.png",
        "Amazon Prime Subscription": "app-assets/images/categories/Amazon.png",
        "Gym Membership": "app-assets/images/categories/Gym.png",
        "Groceries": "app-assets/images/categories/Shoping.png",
        "Eating Out": "app-assets/images/categories/dinner.png",
        "Gas / Transportation": "app-assets/images/categories/transport.png",
        "Entertainment": "app-assets/images/categories/entertainment.png",
        "Pets": "app-assets/images/categories/pet.png",
        "Kids/Children": "app-assets/images/categories/children.png",
        "Taxes": "app-assets/images/categories/taxes.png",
        "Car Maintenance": "app-assets/images/categories/car-maintenance.png",
        "Medical Expenses": "app-assets/images/categories/medical.png",
        "Gifts": "app-assets/images/categories/gift-box.png",
        "Holidays": "app-assets/images/categories/holiday.png",
        "Emergency Fund": "app-assets/images/categories/emergency-fund.png",
        "Phone": "app-assets/images/categories/Phone.png",
        "Retirement": "app-assets/images/categories/retirement.png",
        "Eating Out": "app-assets/images/categories/dinner.png",
        "New House": "app-assets/images/categories/Rent.png",
        "New Phone": "app-assets/images/categories/new-phone.png",
        "Education": "app-assets/images/categories/college-fee.png",
        "Netflix Spotify Subscription":"app-assets/images/categories/Netflix.png",
        "Amazon Prime Spotify Subscription":"app-assets/images/categories/Amazon.png",
        "Hair": "app-assets/images/categories/salon.png",
        "Job": "app-assets/images/categories/job.png",
        "Business": "app-assets/images/categories/business.png",
        "Vacation": "app-assets/images/categories/vacation.png",
        "Electronic Items": "app-assets/images/categories/electronics.png",
        "Electronics": "app-assets/images/categories/electronics.png",
        "Public Transportation": "app-assets/images/categories/transport.png",
        "Retirement": "app-assets/images/categories/retirement.png",
        "Spotify Subscription": "app-assets/images/categories/spotify.png",
        "Bonus": "app-assets/images/categories/bonus.png",
        "Beauty": "app-assets/images/categories/beauty.png",
        "Clothes": "app-assets/images/categories/clothes-hanger.png",
        "Movies": "app-assets/images/categories/entertainment.png"
        
    }

class CategoryList(LoginRequiredMixin, ListView):
    model = SubCategory
    template_name = 'category/category_list.html'

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            self.object_list = self.get_queryset()
            return self.render_to_response(self.get_context_data())
        else:
            return HttpResponseNotAllowed(['POST'])

    def get_context_data(self, **kwargs):
        
        # Start and End date calculation - Month-wise
        if self.request.method == 'POST':
            month_name = "01-" + self.request.POST['select_period']
            date_value = datetime.datetime.strptime(month_name, "%d-%b-%Y").date()
            current_month = datetime.datetime.strftime(date_value, "%b-%Y")
            start_date, end_date = start_end_date(date_value, "Monthly")
        else:
            date_value = datetime.datetime.today().date()
            current_month = datetime.datetime.strftime(date_value, "%b-%Y")
            start_date, end_date = start_end_date(date_value, "Monthly")
        
        data = super(CategoryList, self).get_context_data(**kwargs)
        user_name = self.request.user
        budget_form = BudgetForm(request=self.request)
        transaction_form = TransactionForm(request=self.request)
        category_list = Category.objects.filter(user=user_name)
        tags = Tag.objects.filter(user=user_name)
        sub_category_data = SubCategory.objects.filter(category__user=user_name)
        sub_category_dict = {}
        categories_name = []
        categories_value = []
        date_value = datetime.datetime.today().date()
        
        accounts_qs = Account.objects.filter(user=user_name,
                                         account_type__in=['Savings', 'Checking', 'Cash', 'Credit Card',
                                                           'Line of Credit'])
        bank_accounts_dict = {}
        for account_data in accounts_qs:
            bank_accounts_dict[account_data.id] = account_data.name

        # List of months for which the budgets exists 
        earliest = Budget.objects.filter(user=user_name, start_date__isnull=False).order_by('start_date')
        start, end = earliest[0].start_date, earliest[len(earliest) - 1].start_date
        list_of_months = list(OrderedDict(
            ((start + datetime.timedelta(_)).strftime("%b-%Y"), None) for _ in range((end - start).days + 1)).keys())
        
        for val in sub_category_data:
            if val.category.name != 'Funds': # Excluding Category - Funds
                
                transaction_amount = 0
                budgeted_amount = 0
                transaction_date = 'No transactions' 
                transaction_list = []
                id='false'
                # Filter transactions category and month-wise
                category_transaction_data = Transaction.objects.filter(user=user_name, categories__id=val.id,transaction_date__range=(start_date,end_date))
                
                for transaction_data in category_transaction_data:
                    transaction_list.append(transaction_data)
                    transaction_date = transaction_data.transaction_date
                    transaction_amount += float(transaction_data.amount)
                                            
                # Fetch Bill amount
                if val.category.name == 'Bills & Subscriptions':
                    bill_obj = Bill.objects.filter(label=val.name,user=user_name,date__range=(start_date, end_date))
                    
                    for i in bill_obj:
                        id = i.id
                        budgeted_amount = float(i.amount)
                        
                if val.category.name not in ['Bills & Subscriptions','Funds']:
                    budget_obj = Budget.objects.filter(user=user_name,name=val.name,start_date__range=(start_date,end_date))
                    for i in budget_obj:
                        id = i.id         
                        budgeted_amount = float(i.initial_amount)
                        
                # Percentage amount for Category progress bar
                if budgeted_amount <= 0:
                    percentage = 0
                else:
                    percentage = round((transaction_amount/budgeted_amount)*100,2)
                
                remaining_balance = budgeted_amount - transaction_amount       # Remaining balance amount
                
                category_key = val.category.name
                if category_key in sub_category_dict:
                    sub_category_dict[category_key][3].append([val.name, budgeted_amount, transaction_amount, val.id, percentage,remaining_balance,transaction_date,transaction_list,id])
                else:
                    sub_category_dict[category_key] = [0, 0, val.category.id, [[val.name, budgeted_amount, transaction_amount, val.id, percentage,remaining_balance,transaction_date,transaction_list,id]]]

        for cat_data in category_list:
            if cat_data.name != 'Funds':
                if cat_data.name not in sub_category_dict:
                    sub_category_dict[cat_data.name] = [0, 0, cat_data.id, []]
                else:
                    total_cat_spend = 0
                    total_cat_income = 0
                    for sub_cat in sub_category_dict[cat_data.name][3]:
                        total_cat_spend += sub_cat[1]
                        total_cat_income += sub_cat[2]
                    sub_category_dict[cat_data.name][0] = total_cat_spend
                    sub_category_dict[cat_data.name][1] = total_cat_income
                    if total_cat_spend != 0:
                        categories_name.append(cat_data.name)
                        categories_value.append(total_cat_spend)

        transaction_key =  ['S.No.', 'Date', 'Amount', 'Payee', 'Account', 'Categories', 'Bill', 'Budget'] 
        data['sub_category_data'] = sub_category_dict
        data['categories_name'] = categories_name
        data['categories_series'] = [{'name': 'Spent', 'data': categories_value}]
        data['category_icons'] = category_icons
        data['page'] = "category_list"
        data['transaction_key'] = transaction_key
        data['transaction_data']= category_transaction_data
        data['budget_form'] = budget_form
        data["bank_accounts"] = bank_accounts_dict
        data['form'] = transaction_form
        data['tags'] = tags
        data['list_of_months'] = list_of_months
        data['current_month'] = current_month
        
        return data

    # def get_context_data(self, **kwargs):
    #     # self.request = kwargs.pop('request')
    #     data = super(CategoryList, self).get_context_data(**kwargs)
    #     user_name = self.request.user
    #     category_list = Category.objects.filter(user=user_name)
    #     sub_category_data = SubCategory.objects.filter(category__user=user_name)
    #     sub_category_dict = {}
    #     categories_name = []
    #     categories_value = []

    #     for val in sub_category_data:
    #         print('sub-cat data====>',val)
    #         spent_value = 0
    #         income_value = 0
    #         category_transaction_data = Transaction.objects.filter(user=user_name, categories__id=val.id)
    #         for transaction_data in category_transaction_data:
    #             if transaction_data.out_flow:
    #                 spent_value += float(transaction_data.amount)
    #             else:
    #                 income_value += float(transaction_data.amount)
    #         if val.category.name == "Goals":
    #             goal_obj = Goal.objects.filter(label=val)
    #             if goal_obj:
    #                 spent_value = goal_obj[0].allocate_amount
    #         if val.category.name in sub_category_dict:
    #             sub_category_dict[val.category.name][3].append([val.name, spent_value, income_value, val.id])
    #         else:
    #             sub_category_dict[val.category.name] = [0, 0, val.category.id,
    #                                                     [[val.name, spent_value, income_value, val.id]]]

    #     for cat_data in category_list:
    #         if cat_data.name not in sub_category_dict:
    #             sub_category_dict[cat_data.name] = [0, 0, cat_data.id, []]
    #         else:
    #             total_cat_spend = 0
    #             total_cat_income = 0
    #             for sub_cat in sub_category_dict[cat_data.name][3]:
    #                 total_cat_spend += sub_cat[1]
    #                 total_cat_income += sub_cat[2]
    #             sub_category_dict[cat_data.name][0] = total_cat_spend
    #             sub_category_dict[cat_data.name][1] = total_cat_income
    #             if total_cat_spend != 0:
    #                 categories_name.append(cat_data.name)
    #                 categories_value.append(total_cat_spend)

    #     print(sub_category_dict)
    #     sub_category_key = ['Category', 'Budgetted Amount', 'Monthly Transactions','Remaining Balance', 'Actions']
    #     # sub_category_key = ['Category', 'Total Expenses','Total Income', 'Actions']
    #     data['sub_category_data'] = sub_category_dict
    #     data['categories_name'] = categories_name
    #     data['categories_series'] = [{'name': 'Spent', 'data': categories_value}]
    #     data['category_key'] = sub_category_key
    #     data['page'] = "category_list"
    #     return data


class CategoryDetail(LoginRequiredMixin, DetailView):
    model = Category
    template_name = 'category/category_detail.html'

    def get_context_data(self, **kwargs):
        data = super(CategoryDetail, self).get_context_data(**kwargs)
        data['page'] = "category_list"
        return data


class CategoryAdd(LoginRequiredMixin, CreateView):
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
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.name = self.request.POST.get('name').title().strip()
        obj.save()
        return super().form_valid(form)

    def get_success_url(self):
        """Detect the submit button used and act accordingly"""
        if 'add_other' in self.request.POST:
            url = reverse_lazy('category_add')
        else:
            url = reverse_lazy('category_list')
        return url


class CategoryUpdate(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'category/category_update.html'


class CategoryDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        category_obj = Category.objects.get(pk=self.kwargs['pk'])
        user_name = self.request.user
        transaction_details = Transaction.objects.filter(user=user_name, categories__category=category_obj)
        for data in transaction_details:
            delete_transaction_details(data.pk, user_name)
        category_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


def category_group_add(request):
    if request.method == 'POST' and request.is_ajax():
        user_name = request.user
        category_name = request.POST['category_name'].title()
        category_obj = Category.objects.filter(user=user_name, name=category_name)
        if category_obj:
            return JsonResponse({'status': "error"})
        else:
            Category.objects.create(user=user_name, name=category_name)
            return JsonResponse({'status': "success"})


# Subcategory views

def subcategory_suggestion(request):
    category_pk = int(request.POST['category_pk'])
    category_obj = Category.objects.get(pk=category_pk)
    suggestion_list = sub_category_suggested_list[category_obj.name]
    for name in suggestion_list:
        sub_obj = SubCategory.objects.filter(name=name, category=category_obj)
        if sub_obj:
            suggestion_list.remove(name)
    context = {'subcategory_suggestions': suggestion_list, 'category_pk': category_pk}
    return JsonResponse(context)


def subcategory_add(request, category_pk):
    category_obj = Category.objects.get(pk=category_pk)
    suggestion_list = sub_category_suggested_list[category_obj.name]
    for name in suggestion_list:
        sub_obj = SubCategory.objects.filter(name=name, category=category_obj)
        if sub_obj:
            suggestion_list.remove(name)
    context = {'subcategory_suggestions': suggestion_list, 'category_pk': category_pk}
    if request.method == 'POST':
        name = request.POST.get('name').title()
        try:
            SubCategory.objects.get(category__user=request.user, name=name)
            context['error'] = 'Subcategory already exists'
            return render(request, "subcategory/add.html", context=context)
        except:
            SubCategory.objects.create(name=name, category=category_obj)
            return redirect("/category_list")
    return render(request, "subcategory/add.html", context=context)


def subcategory_update(request, pk):
    user = request.user
    category_list = Category.objects.filter(user=user)
    subcategory_obj = SubCategory.objects.get(pk=pk)
    context = {'category_list': category_list,
               'subcategory_obj': subcategory_obj}

    if request.method == 'POST':
        category_obj = Category.objects.get(user=user, name=request.POST.get('category'))
        name = request.POST.get('name').title()
        old_name = subcategory_obj.name
        sub_category_exist = check_subcategory_exists(subcategory_obj, name, category_obj)
        if sub_category_exist:
            context['error'] = 'Subcategory already exists'
            return render(request, "subcategory/update.html", context=context)
        subcategory_obj.name = name
        subcategory_obj.category = category_obj
        subcategory_obj.save()
        if subcategory_obj.category.name == "Bills & Subscriptions":
            bill_obj = BillDetail.objects.get(user=user, label=old_name)
            bill_obj.label = name
            bill_obj.save()
        return redirect("/category_list")

    return render(request, "subcategory/update.html", context=context)


def subcategory_delete(request, pk):
    subcategory_obj = SubCategory.objects.get(pk=pk)
    user = request.user
    transaction_details = Transaction.objects.filter(user=user, categories=subcategory_obj)
    for data in transaction_details:
        delete_transaction_details(data.pk, user)
    subcategory_obj.delete()
    return JsonResponse({"status": "Successfully", "path": "None"})


def subcategory_list(request):
    if request.method == "POST" and request.is_ajax():
        user = request.user
        category_group = request.POST.get('category_group')
        print("caategoty_group=====>", category_group)
        try:
            category = Category.objects.get(user=user, pk=category_group)
        except:
            category = Category.objects.get(user=user, name=category_group)

        subcategories = SubCategory.objects.filter(category=category)
        subcategories = list(subcategories.values_list('name', flat=True))
        print("subcat======>", subcategories)
        return JsonResponse({"subcategories": subcategories})
    return redirect("/category_list")


def subcategory_budget(request):
    user_name = request.user
    category = int(request.POST.get('category'))
    sub_category_name = request.POST.get('name')
    subcategory_obj = SubCategory.objects.get(category__pk=category, name=sub_category_name)
    try:
        budget = Budget.objects.filter(user=user_name, category=subcategory_obj)
        budget_name = budget[0].name
    except:
        budget_name = False

    return JsonResponse({"budget_name": budget_name})


# def user_login(request):
#     # if request.method == 'POST':
#     #     try:
#     #         next = request.POST['next']
#     #     except:
#     #         next = None
#     #     username = request.POST['register-username']
#     #     password = request.POST['register-password']
#     #     user = authenticate(username=username, password=password)
#     #     if user is None:
#     #         context = {'login_error': 'Username and Password Incorrect'}
#     #         return render(request, "login_page.html", context)
#     #     elif not user.is_active:
#     #         context = {'login_error': 'User is not active'}
#     #         return render(request, "login_page.html", context)
#     #     else:
#     #         login(request, user)
#     #         template_budget_data = TemplateBudget.objects.filter(user=user)
#     #         if template_budget_data:
#     #             budget_obj = TemplateBudget.objects.filter(user=user)
#     #             budget_obj.delete()
#     #         period_list = {'Daily': 'Going out', 'Weekly': 'Groceries', 'Monthly': 'Bills'}
#     #         date_value = datetime.datetime.today().date()
#     #         start_month_date, end_month_date = start_end_date(date_value, "Monthly")
#     #         for key, value in period_list.items():
#     #             template_obj = TemplateBudget()
#     #             template_obj.user = user
#     #             budget_name = value
#     #             template_obj.name = budget_name
#     #             template_obj.currency = "$"
#     #             template_obj.auto_budget = True
#     #             template_obj.budget_period = key
#     #
#     #             if key == 'Monthly':
#     #                 template_obj.start_date = start_month_date
#     #                 template_obj.end_date = end_month_date
#     #                 template_obj.initial_amount = 1500
#     #                 template_obj.amount = 1500
#     #                 template_obj.budget_spent = 1000
#     #                 template_obj.budget_left = 500
#     #                 template_obj.created_at = start_month_date
#     #                 template_obj.ended_at = end_month_date
#     #                 template_obj.save()
#     #
#     #             if key == 'Weekly':
#     #                 start_week_date, end_week_date = start_end_date(date_value, key)
#     #                 template_obj.start_date = start_month_date
#     #                 template_obj.end_date = end_month_date
#     #                 template_obj.initial_amount = 200
#     #                 template_obj.amount = 200
#     #                 template_obj.budget_spent = 150
#     #                 template_obj.budget_left = 50
#     #                 template_obj.created_at = start_week_date
#     #                 template_obj.ended_at = end_week_date
#     #                 template_obj.save()
#     #
#     #             if key == 'Daily':
#     #                 template_obj.start_date = start_month_date
#     #                 template_obj.end_date = end_month_date
#     #                 template_obj.initial_amount = 100
#     #                 template_obj.amount = 100
#     #                 template_obj.budget_spent = 120
#     #                 template_obj.budget_left = -20
#     #                 template_obj.created_at = date_value
#     #                 template_obj.ended_at = date_value
#     #                 template_obj.save()
#     #
#     #         if next:
#     #             return redirect(next)
#     #         else:
#     #             return redirect('/')
#     # else:
#     #     try:
#     #         next = request.GET['next']
#     #     except:
#     #         next = None
#     #     return render(request, "login_page.html", context={'next': next})
#     context = {}
#     if request.method == "POST":
#         username = request.POST['register-username']
#         user_password = request.POST['register-password']
#         search_api_url = f"https://tradingtech.org/wp-content/plugins/indeed-membership-pro/apigate.php?ihch={wordpress_api_key}&action=search_users&term_name=user_login&term_value={username}"
#         try:
#             api_response = requests.get(search_api_url)
#             search_api_data = api_response.json()
#         except:
#             context['login_error'] = 'User data not accessed. Something Went Wrong!!'
#             return render(request, "login_page.html", context=context)
#
#         user_details = ""
#         user = authenticate(username=username, password=user_password)
#         if user:
#             if user.is_superuser:
#                 login(request, user)
#                 try:
#                     redirect_url = request.POST['redirect_url']
#                     return redirect(redirect_url)
#                 except:
#                     return redirect("/")
#
#         for data in search_api_data['response']:
#             user_api_url = f"https://tradingtech.org/wp-content/plugins/indeed-membership-pro/apigate.php?ihch={wordpress_api_key}&action=user_get_details&uid={data['ID']}"
#             print(user_api_url)
#             user_api_response = requests.get(user_api_url)
#             user_data = user_api_response.json()['response']
#             print(user_password)
#             print(user_data['user_pass'])
#             print(username)
#
#             if user_data['user_login'] == username and user_data['user_pass'] == user_password:
#                 if user:
#                     login(request, user)
#                 else:
#                     try:
#                         user = User.objects.get(username=username)
#                         user.set_password(user_password)
#                         user.first_name = user_data['user_nicename']
#                         user.email = user_data['user_email']
#                         user.save()
#                     except:
#                         user = User.objects.create_user(username, user_data['user_email'], user_password)
#                         user.first_name = user_data['user_nicename']
#                         user.save()
#                     login(request, user)
#                 try:
#                     redirect_url = request.POST['redirect_url']
#                     return redirect(redirect_url)
#                 except:
#                     return redirect("/")
#             else:
#                 user_details = "False"
#         if user_details == "False":
#             context['login_error'] = 'Username and Password Incorrect'
#             return render(request, "login_page.html", context=context)
#     else:
#         try:
#             context['redirect_url'] = request.GET['next']
#         except:
#             pass
#
#         return render(request, "login_page.html", context=context)


def user_login(request):
    context = {'page': 'login_page'}
    if request.method == "POST":
        username = request.POST['register-username']
        user_password = request.POST['register-password']
        check_jwt_authentication = False
        check_user_membership = False
        try:
            user = authenticate(username=username, password=user_password)
            if user.is_superuser:
                login(request, user)
                try:
                    redirect_url = request.POST['redirect_url']
                    return redirect(redirect_url)
                except:
                    return render(request, "home.html", context=context)

        except Exception as e:
            print("admin check===>", e)
            pass

        # Create User JWT Token
        token_url = f"{wordpress_domain}/wp-json/api/v1/token"
        token_data = {"username": username, "password": user_password}
        token_response = requests.post(token_url, json=token_data)
        if token_response.status_code == 200:
            token_response = token_response.json()
            if 'jwt_token' in token_response:
                jwt_token = token_response['jwt_token']
                check_jwt_authentication = True

        if check_jwt_authentication:
            try:
                # Get user info
                user_info_url = f"{wordpress_domain}/wp-json/wp/v2/users/me"
                headers = {"Authorization": f"Bearer {jwt_token}"}
                user_info_response = requests.get(user_info_url, headers=headers)
                user_info = user_info_response.json()
                user_id = user_info['id']
                print("user_info===============>", user_info)

                # get user plan
                plan_url = f"{wordpress_domain}/?ihc_action=api-gate&ihch={wordpress_api_key}&action=get_user_levels&uid={user_id}"
                plan_response = requests.get(plan_url).json()['response']
                user_plan_id = list(plan_response.keys())[0]
                print("user_plan_id=========>", user_plan_id)

                # Verify User Membership
                verify_user_url = f"{wordpress_domain}/?ihc_action=api-gate&ihch={wordpress_api_key}&action=verify_user_level&uid={user_id}&lid={user_plan_id}"
                verify_user_response = requests.get(verify_user_url)
                if verify_user_response.status_code == 200:
                    verify_user_data = verify_user_response.json()
                    if verify_user_data['response'] == 1:
                        check_user_membership = True
            except Exception as e:
                print("user membership exception===========>", e)
                check_user_membership = False

        if not check_user_membership:
            context['login_error'] = "you don't have membership subscription"
            return render(request, "login_page.html", context=context)

        if check_jwt_authentication and check_user_membership:
            try:
                user = User.objects.get(id=user_id)
                user.set_password(user_password)
                user.save()
            except:
                user = User()
                user.id = user_id
                user.username = username
                user.email = ''
                user.first_name = user_info['name']
                user.is_active = True
                user.set_password(user_password)
                user.save()

            user = authenticate(username=username, password=user_password)
            if user:
                login(request, user)
                try:
                    redirect_url = request.POST['redirect_url']
                    return redirect(redirect_url)
                except:
                    return render(request, "home.html", context=context)

        context['login_error'] = 'Username and Password Incorrect'
        return render(request, "login_page.html", context=context)

    else:
        try:
            context['redirect_url'] = request.GET['next']
        except Exception as e:
            print("Error: ", e)
            pass

        return render(request, "login_page.html")


@login_required(login_url="/login")
def user_logout(request):
    logout(request)
    return redirect('/login')


def make_budgets_values(user_name, budget_data, page_method):
    print("budget data==",budget_data)
    total_budget = 0
    total_spent = 0
    total_left = 0
    spent_data = {}
    left_data = {}
    over_spent_data = {}
    budget_names_list = []
    budgets_dict = {}
    income_bdgt_dict = {}
    income_daily_bdgt_dict = {}
    income_daily_total_dict = {}
    daily_bdgt_dict = {}
    daily_total_dict = {}
    total_bgt_income = 0
    all_budgets = []
    if budget_data:
        for data in budget_data:
            budget_create_date = data.created_at
            budget_end_date = data.ended_at
            budget_names_list.append(data.name)
            budget_amount = float(data.amount)
            left_amount = float(data.budget_left)
            budget_pre = data.budget_period
            spent_amount = float(data.budget_spent)
            total_spent_amount = spent_amount
            if budget_create_date:
                budget_start_date = datetime.datetime.strftime(budget_create_date, "%b %d, %Y")
                budget_end_date = datetime.datetime.strftime(budget_end_date, "%b %d, %Y")
            else:
                budget_start_date = False
                budget_end_date = False

            if budget_pre == 'Quarterly' or budget_pre == 'Yearly':
                all_bdgt_spent = Budget.objects.filter(user=user_name, name=data.name, created_at=budget_create_date,
                                                       ended_at=data.ended_at)
                total_spent_amount = sum(float(obj.budget_spent) for obj in all_bdgt_spent)

            budget_currency = data.currency
            category_group_name = data.category.category.name
            print("Category group",category_group_name)
            budget_value = [data.name, budget_amount, spent_amount, left_amount, data.id, budget_pre,
                            budget_start_date, budget_end_date, budget_currency, total_spent_amount]

            if category_group_name == "Income":
                if budget_pre != "Daily" and budget_pre != "Weekly":
                    if category_group_name in income_bdgt_dict:
                        income_bdgt_dict[category_group_name].append(budget_value)
                        total_bgt_income += spent_amount
                    else:
                        income_bdgt_dict[category_group_name] = [budget_value]
                        total_bgt_income += spent_amount
                else:
                    if category_group_name in income_daily_bdgt_dict:
                        if data.name in income_daily_bdgt_dict[category_group_name]:
                            income_daily_bdgt_dict[category_group_name][data.name].append(budget_value)
                            total_bgt_income += spent_amount
                            income_daily_total_dict[category_group_name][data.name][0] += budget_amount
                            income_daily_total_dict[category_group_name][data.name][1] += spent_amount
                            income_daily_total_dict[category_group_name][data.name][2] += left_amount
                        else:
                            income_daily_bdgt_dict[category_group_name] = {data.name: [budget_value]}
                            income_daily_total_dict[category_group_name] = {
                                data.name: [budget_amount, spent_amount, left_amount]}
                            total_bgt_income += spent_amount
                    else:
                        income_daily_bdgt_dict[category_group_name] = {data.name: [budget_value]}
                        income_daily_total_dict[category_group_name] = {
                            data.name: [budget_amount, spent_amount, left_amount]}
                        total_bgt_income += spent_amount
            else:
                if spent_amount > budget_amount:
                    if data.name not in over_spent_data:
                        over_spent_data[data.name] = spent_amount - budget_amount
                    else:
                        over_spent_data[data.name] += spent_amount - budget_amount

                    if data.name not in left_data:
                        left_data[data.name] = 0
                    else:
                        left_data[data.name] += 0

                    if data.name not in spent_data:
                        spent_data[data.name] = budget_amount
                    else:
                        spent_data[data.name] += budget_amount

                else:
                    if data.name not in over_spent_data:
                        over_spent_data[data.name] = 0
                    else:
                        over_spent_data[data.name] += 0

                    if data.name not in left_data:
                        left_data[data.name] = left_amount
                    else:
                        left_data[data.name] += left_amount

                    if data.name not in spent_data:
                        spent_data[data.name] = spent_amount
                    else:
                        spent_data[data.name] += spent_amount

                all_budgets.append(budget_value)

                if budget_pre != "Daily" and budget_pre != "Weekly":
                    if category_group_name in budgets_dict:
                        budgets_dict[category_group_name].append(budget_value)
                    else:
                        budgets_dict[category_group_name] = [budget_value]
                else:
                    if category_group_name in daily_bdgt_dict:
                        if data.name in daily_bdgt_dict[category_group_name]:
                            daily_bdgt_dict[category_group_name][data.name].append(budget_value)
                            daily_total_dict[category_group_name][data.name][0] += budget_amount
                            daily_total_dict[category_group_name][data.name][1] += spent_amount
                            daily_total_dict[category_group_name][data.name][2] += left_amount
                        else:
                            daily_bdgt_dict[category_group_name] = {data.name: [budget_value]}
                            daily_total_dict[category_group_name] = {
                                data.name: [budget_amount, spent_amount, left_amount]}
                    else:
                        daily_bdgt_dict[category_group_name] = {data.name: [budget_value]}
                        daily_total_dict[category_group_name] = {data.name: [budget_amount, spent_amount, left_amount]}

            total_budget += budget_amount
            total_spent += spent_amount
            total_left += left_amount

        if page_method == "budget_page":
            earliest = Budget.objects.filter(user=user_name, start_date__isnull=False).order_by('start_date')
            for key, value in daily_total_dict.items():
                for k, v in value.items():
                    bgt_val = daily_bdgt_dict[key][k][0]
                    daily_bdgt_dict[key][k].insert(0, [bgt_val[0], v[0], v[1], v[2], bgt_val[4], bgt_val[5],
                                                       bgt_val[6], bgt_val[7], bgt_val[8], v[1]])

            for key, value in income_daily_total_dict.items():
                for k, v in value.items():
                    bgt_val = income_daily_bdgt_dict[key][k][0]
                    income_daily_bdgt_dict[key][k].insert(0, [bgt_val[0], v[0], v[1], v[2], bgt_val[4], bgt_val[5],
                                                              bgt_val[6], bgt_val[7], bgt_val[8], v[1]])
        else:
            earliest = TemplateBudget.objects.filter(start_date__isnull=False).order_by('start_date')

        start, end = earliest[0].start_date, earliest[len(earliest) - 1].start_date
        list_of_months = list(OrderedDict(
            ((start + datetime.timedelta(_)).strftime("%b-%Y"), None) for _ in range((end - start).days + 1)).keys())
        budget_values = [total_spent, total_left]
    else:
        earliest = Budget.objects.filter(user=user_name, start_date__isnull=False).order_by('start_date')
        if earliest:
            start = earliest[0].start_date
        else:
            start = datetime.datetime.today().date()
        end = datetime.datetime.today().date()
        list_of_months = list(OrderedDict(
            ((start + datetime.timedelta(_)).strftime("%b-%Y"), None) for _ in range((end - start).days + 1)).keys())
        budget_values = [0, 0]
        budget_currency = ""

    budget_names_list = list(spent_data.keys())
    spent_data = dict_value_to_list(spent_data)
    left_data = dict_value_to_list(left_data)
    over_spent_data = dict_value_to_list(over_spent_data)
    budget_graph_data = [{'name': 'Spent', 'data': spent_data},
                         {'name': 'Left', 'data': left_data},
                         {'name': 'OverSpent', 'data': over_spent_data}]

    for key, value in daily_bdgt_dict.items():
        for k, v in value.items():
            if key in budgets_dict:
                budgets_dict[key].append([k, 0, 0, 0, 0, v[0][5], v])
            else:
                budgets_dict[key] = [[k, 0, 0, 0, 0, v[0][5], v]]

    for key, value in income_daily_bdgt_dict.items():
        for k, v in value.items():
            if key in income_bdgt_dict:
                income_bdgt_dict[key].append([k, 0, 0, 0, 0, v[0][5], v])
            else:
                income_bdgt_dict[key] = [[k, 0, 0, 0, 0, v[0][5], v]]

    return all_budgets, budget_graph_data, budget_values, budget_currency, list_of_months, budget_names_list, \
        budgets_dict, income_bdgt_dict, total_bgt_income


def budgets_page_data(request, budget_page, template_page):
    user_name = request.user
    transaction_key = ['S.No.', 'Date', 'Amount', 'Payee', 'Account', 'Categories', 'Bill', 'Budget', 'Cleared']
    if request.method == 'POST':
        month_name = "01-" + request.POST['select_period']
        date_value = datetime.datetime.strptime(month_name, "%d-%b-%Y").date()
        current_month = datetime.datetime.strftime(date_value, "%b-%Y")
        start_date, end_date = start_end_date(date_value, "Monthly")
    else:
        date_value = datetime.datetime.today().date()
        current_month = datetime.datetime.strftime(date_value, "%b-%Y")
        start_date, end_date = start_end_date(date_value, "Monthly")

    budget_data = Budget.objects.filter(user=user_name, start_date=start_date, end_date=end_date).order_by(
        '-created_at')
    template_budget_data = TemplateBudget.objects.filter(start_date=start_date, end_date=end_date).order_by(
        '-created_at')
    budget_key = ['Name', 'budgeted', 'Spent', 'Left']
    budget_label = ['Total Spent', 'Total Left']
    all_budgets, budget_graph_data, budget_values, budget_currency, list_of_months, current_budget_names_list, \
        budgets_dict, income_bdgt_dict, total_bgt_income = make_budgets_values(user_name, budget_data, "budget_page")
    template_all_budgets, template_budget_graph_data, template_budget_values, template_budget_currency, \
        template_list_of_months, template_budget_names_list, tem_budgets_dict, template_income_bdgt_dict, template_total_bgt_income = make_budgets_values(
        user_name,
        template_budget_data,
        "template_page")

    # COMPARE BUDGETS :-

    current_date = datetime.datetime.today().date()
    week_start, week_end = start_end_date(current_date, "Weekly")
    month_start, month_end = start_end_date(current_date, "Monthly")
    quart_end, quart_start = start_end_date(current_date, "Quarterly")
    yearly_start, yearly_end = start_end_date(current_date, "Yearly")
    monthly_budget_transaction_data, cmp_month_list, monthly_cmp_budgets_dict, monthly_cmp_transaction_budgets = compare_budgets(
        user_name, month_start, month_end, current_budget_names_list)
    week_budget_transaction_data, cmp_week_list, week_cmp_budgets_dict, week_cmp_transaction_budgets = compare_budgets(
        user_name, week_start, week_end, current_budget_names_list)
    quart_budget_transaction_data, cmp_quart_list, quart_cmp_budgets_dict, quart_cmp_transaction_budgets = compare_budgets(
        user_name, quart_start, quart_end, current_budget_names_list)
    yearly_budget_transaction_data, cmp_yearly_list, yearly_cmp_budgets_dict, yearly_cmp_transaction_budgets = compare_budgets(
        user_name, yearly_start, yearly_end, current_budget_names_list)

    if not current_budget_names_list:
        budget_page = ""
        template_page = "active"

    weekly_daily_budget = {'weekly': {}, 'daily': {}}
    total_budget = {'weekly': {}, 'daily': {}}
    total_spent = {'weekly': {}, 'daily': {}}
    total_left = {'weekly': {}, 'daily': {}}

    for bdgt_list in all_budgets:
        if bdgt_list[5] == 'Daily':
            if bdgt_list[0] not in weekly_daily_budget['daily']:
                weekly_daily_budget['daily'][bdgt_list[0]] = [bdgt_list]
            else:
                weekly_daily_budget['daily'][bdgt_list[0]].append(bdgt_list)
            if bdgt_list[0] not in total_budget['daily']:
                total_budget['daily'][bdgt_list[0]] = bdgt_list[1]
            else:
                total_budget['daily'][bdgt_list[0]] += bdgt_list[1]
            if bdgt_list[0] not in total_spent['daily']:
                total_spent['daily'][bdgt_list[0]] = bdgt_list[2]
            else:
                total_spent['daily'][bdgt_list[0]] += bdgt_list[2]
            if bdgt_list[0] not in total_left['daily']:
                total_left['daily'][bdgt_list[0]] = bdgt_list[3]
            else:
                total_left['daily'][bdgt_list[0]] += bdgt_list[3]

        if bdgt_list[5] == 'Weekly':
            if bdgt_list[0] not in weekly_daily_budget['weekly']:
                weekly_daily_budget['weekly'][bdgt_list[0]] = [bdgt_list]
            else:
                weekly_daily_budget['weekly'][bdgt_list[0]].append(bdgt_list)
            if bdgt_list[0] not in total_budget['weekly']:
                total_budget['weekly'][bdgt_list[0]] = bdgt_list[1]
            else:
                total_budget['weekly'][bdgt_list[0]] += bdgt_list[1]
            if bdgt_list[0] not in total_spent['weekly']:
                total_spent['weekly'][bdgt_list[0]] = bdgt_list[2]
            else:
                total_spent['weekly'][bdgt_list[0]] += bdgt_list[2]
            if bdgt_list[0] not in total_left['weekly']:
                total_left['weekly'][bdgt_list[0]] = bdgt_list[3]
            else:
                total_left['weekly'][bdgt_list[0]] += bdgt_list[3]

    for key, value in weekly_daily_budget.items():
        if key == 'daily':
            if value:
                for k, v in value.items():
                    v.insert(0, [v[0][0], total_budget[key][k], total_spent[key][k], total_left[key][k], v[0][4]])
        if key == 'weekly':
            if value:
                for k, v in value.items():
                    v.insert(0, [v[0][0], total_budget[key][k], total_spent[key][k], total_left[key][k], v[0][4]])

    template_budget_data, template_values, template_name_list, template_graph_data = get_template_budget()
    total_expense_list = budget_graph_data[0]['data']
    left_over_cash = round(total_bgt_income - sum(total_expense_list), 2)
    print("expenses dict===>",budgets_dict)
    context = {'left_over_cash': left_over_cash, 'total_income': total_bgt_income, 'income_bdgt_dict': income_bdgt_dict,
               'expenses_dict': budgets_dict,
               'all_budgets': all_budgets, 'budget_graph_data': budget_graph_data,
               'cash_flow_names': ['Earned', 'Spent'],
               'cash_flow_data': [{'name': 'Amount', 'data': [total_bgt_income, budget_values[0]]}],
               'budget_names': current_budget_names_list,
               'list_of_months': list_of_months, 'total_expense': sum(total_expense_list),
               "budget_graph_currency": budget_currency, "budget_bar_id": "#budgets-bar",
               "template_budget_bar_id": "#template-budgets-bar", "template_budget_graph_id": "#template_total_budget",
               'template_all_budgets': template_all_budgets, 'template_budget_graph_data': template_graph_data,
               'template_budget_names': template_name_list, 'template_list_of_months': template_list_of_months,
               "template_budget_graph_value": template_values,
               "template_budget_graph_currency": '$', 'budget_key': budget_key,
               'budget_key_dumbs': json.dumps(budget_key),
               "current_month": current_month,
               "budget_graph_value": total_expense_list, "budget_graph_label": budget_label,
               "budget_graph_id": "#total_budget", "monthly_budget_transaction_data": monthly_budget_transaction_data,
               "week_budget_transaction_data": week_budget_transaction_data,
               "quart_budget_transaction_data": quart_budget_transaction_data,
               "yearly_budget_transaction_data": yearly_budget_transaction_data, "week_start": week_start,
               "week_end": week_end, "quart_start": quart_start, "quart_end": quart_end, "yearly_start": yearly_start,
               "yearly_end": yearly_end, "transaction_key": transaction_key, "month_start": month_start,
               "month_end": month_end, "cmp_budget_value": cmp_month_list, "week_pie_chart": week_cmp_budgets_dict,
               "monthly_pie_chart": monthly_cmp_budgets_dict, "quart_pie_chart": quart_cmp_budgets_dict,
               "yearly_pie_chart": yearly_cmp_budgets_dict,
               "monthly_cmp_transaction_budgets": monthly_cmp_transaction_budgets,
               "week_cmp_transaction_budgets": week_cmp_transaction_budgets,
               "quart_cmp_transaction_budgets": quart_cmp_transaction_budgets,
               "yearly_cmp_transaction_budgets": yearly_cmp_transaction_budgets,
               "cmp_month_graph_id": "#cmp_month_budget", "cmp_week_list": cmp_week_list,
               "cmp_week_list_id": "#cmp_week_list", "cmp_quart_list": cmp_quart_list,
               "cmp_quart_list_id": "#cmp_quart_list", "cmp_yearly_list": cmp_yearly_list,
               "cmp_yearly_list_id": "#cmp_yearly_list", "budget_page": budget_page,
               "template_page": template_page, "weekly_daily_budget": weekly_daily_budget,
               "template_budget_data": template_budget_data
               }

    return context


@login_required(login_url="/login")
def budget_list(request):
    time.sleep(3)
    context = budgets_page_data(request, "active", "")
    return render(request, 'budget/budget_list.html', context=context)


@login_required(login_url="/login")
def budgets_box(request):
    budgets_qs = Budget.objects.filter(user=request.user)
    budgets = list(budgets_qs.values_list('name', flat=True).distinct())
    print("budgets====>", budgets)
    context = {"page": "budgets", "budgets_list": budgets}
    return render(request, 'budget/budget_box.html', context)


@login_required(login_url="/login")
@login_required(login_url="/login")
def budgets_walk_through(request):
    user_name = request.user
    print("username",request.user)
    print("budget request data=====>",request.POST)
    if request.method == "POST":
        category_group = request.POST['category_group']
        print("category gorup=====>",category_group)
        category_name = request.POST['category_name']
        category_obj = Category.objects.get(user=user_name, name=category_group)
        try:
            subcategory_obj = SubCategory.objects.get(name=category_name, category=category_obj)
        except:
            subcategory_obj = SubCategory.objects.create(name=category_name, category=category_obj)
        budget_amount = request.POST['amount']
        budget_currency = request.POST['currency']
        budget_start_date = request.POST['budget_date']
        budget_period = request.POST['budget_period']
        budget_auto = request.POST['auto_budget']
        if budget_auto == 'on':
            budget_auto = True
        budget_name = category_name
        budget_check = Budget.objects.filter(user=user_name, name=budget_name)
        if budget_check:
            return redirect("/budgets/current")

        budget_start_date = datetime.datetime.strptime(budget_start_date, '%Y-%m-%d')
        start_month_date, end_month_date = start_end_date(budget_start_date.date(), "Monthly")
        budget_end_date = get_period_date(budget_start_date, budget_period) - relativedelta(days=1)
        budget_obj = Budget()
        budget_obj.user = user_name
        budget_obj.category = subcategory_obj
        budget_obj.name = budget_name
        budget_obj.start_date = start_month_date
        budget_obj.end_date = end_month_date
        budget_obj.initial_amount = budget_amount
        budget_obj.amount = budget_amount
        budget_obj.budget_left = budget_amount
        budget_obj.created_at = budget_start_date
        budget_obj.currency = budget_currency
        budget_obj.auto_budget = budget_auto
        budget_obj.ended_at = budget_end_date
        budget_obj.budget_start_date = budget_start_date
        budget_obj.save()
        if budget_period == 'Quarterly':
            for month_value in range(2):
                start_month_date = start_month_date + relativedelta(months=1)
                start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")
                save_budgets(user_name, start_month_date, end_month_date, budget_name, budget_period, budget_currency,
                             budget_amount, budget_auto, budget_start_date, budget_end_date, budget_amount,
                             budget_start_date, subcategory_obj, None, budget_status=True)
        if budget_period == 'Yearly':
            for month_value in range(11):
                start_month_date = start_month_date + relativedelta(months=1)
                start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")
                save_budgets(user_name, start_month_date, end_month_date, budget_name, budget_period, budget_currency,
                             budget_amount, budget_auto, budget_start_date, budget_end_date, budget_amount,
                             budget_start_date, subcategory_obj, None, budget_status=True)
        create_budget_request()
        return redirect("/budgets/current")
    date_value = datetime.datetime.today().date()
    current_month = datetime.datetime.strftime(date_value, "%b-%Y")
    start_date, end_date = start_end_date(date_value, "Monthly")
    budget_data = Budget.objects.filter(user=user_name, start_date=start_date, end_date=end_date).order_by(
        '-created_at')

    income_categories = []
    bill_categories = []
    expense_categories = {}
    non_monthly_expense_categories = []
    goals_categories = []
    bills_dict = {'Bills': []}
    category_qs = SubCategory.objects.filter(category__user=user_name)
    for sub_data in category_qs:
        if sub_data.category.name == "Income":
            income_categories.append(sub_data.name)
        if sub_data.category.name == "Bills & Subscriptions":
            bill_categories.append(sub_data.name)
        if sub_data.category.name == "Non-Monthly":
            non_monthly_expense_categories.append(sub_data.name)
        if sub_data.category.name == "Goals":
            goals_categories.append(sub_data.name)
        if sub_data.category.name != "Income" and sub_data.category.name != "Bills & Subscriptions" and sub_data.category.name != "Goals" and sub_data.category.name != "Funds" and sub_data.category.name != "Non-Monthly":
            if sub_data.category.name in expense_categories:
                expense_categories[sub_data.category.name].append(
                    [sub_data.name, 0.0, 0.0, 0.0, "false", str(start_date), str(end_date), '$', 0.0])
            else:
                expense_categories[sub_data.category.name] = [
                    [sub_data.name, 0.0, 0.0, 0.0, "false", str(start_date), str(end_date), '$', 0.0]]

    all_budgets, budget_graph_data, budget_values, budget_currency, list_of_months, current_budget_names_list, \
        budgets_dict, income_bdgt_dict, total_bgt_income = make_budgets_values(user_name, budget_data, "budget_page")

    bills_qs = Bill.objects.filter(user=user_name, date__range=(start_date, end_date)).order_by('-created_at')
    total_expected_bill = 0
    total_actual_bill = 0

    for bill_data in bills_qs:
        bill = bill_data.bill_details
        bill_name = bill.label
        bill_amount = float(bill_data.amount)
        total_expected_bill += bill_amount
        bill_left_amount = float(bill_data.remaining_amount)
        bill_spent_amount = round(bill_amount - bill_left_amount, 2)
        total_actual_bill += bill_spent_amount
        bill_start_date = datetime.datetime.strftime(bill_data.date, "%b %d, %Y")
        transaction_qs = Transaction.objects.filter(user=user_name, bill=bill_data,
                                                    transaction_date__range=(start_date, end_date)).order_by(
            'transaction_date')
        current_spent_amount = 0
        for trans_data in transaction_qs:
            current_spent_amount += float(trans_data.amount)
        bill_bgt_list = [bill_name, bill_amount, current_spent_amount, bill_left_amount, bill_data.id, bill.frequency,
                         bill_start_date, bill_start_date, bill_data.currency, bill_spent_amount]

        bills_dict['Bills'].append(bill_bgt_list)
        if bill_name in bill_categories:
            bill_categories.remove(bill_name)

    total_income_expected = 0
    total_actual_income = 0

    if 'Income' in income_bdgt_dict:
        for inc_data in income_bdgt_dict['Income']:
            total_income_expected += float(inc_data[1])
            total_actual_income += float(inc_data[2])
            if inc_data[0] in income_categories:
                income_categories.remove(inc_data[0])
    else:
        income_bdgt_dict['Income'] = []
    for name in income_categories:
        income_bdgt_dict['Income'].insert(0, [name, 0.0, 0.0, 0.0, "false", str(start_date), str(end_date), '$', 0.0])

    for name in bill_categories:
        bills_dict['Bills'].insert(0, [name, 0.0, 0.0, 0.0, "false", str(start_date), str(end_date), '$', 0.0])

    accounts_qs = Account.objects.filter(user=request.user,
                                         account_type__in=['Savings', 'Checking', 'Cash', 'Credit Card',
                                                           'Line of Credit'])
    bank_accounts_dict = {}
    for account_data in accounts_qs:
        bank_accounts_dict[account_data.id] = account_data.name

    total_expected_expenses = 0
    total_actual_expenses = 0
    for key in budgets_dict:
        if key in expense_categories:
            expense_categories[key] = budgets_dict[key]
            for exp_data in budgets_dict[key]:
                total_expected_expenses += float(exp_data[1])
                total_actual_expenses += float(exp_data[2])

    total_non_monthly_expected_expenses = 0
    total_non_monthly_actual_expenses = 0
    non_monthly_expenses_dict = {}
    if "Non-Monthly" in budgets_dict:
        for exp in budgets_dict['Non-Monthly']:
            non_monthly_expenses_dict.update({exp[0]:exp})
            total_non_monthly_expected_expenses += float(exp[1])
            total_non_monthly_actual_expenses += float(exp[2])

    total_goals_expected = 0
    total_goals_actual = 0
    goals_dict = {}
    if "Goals" in budgets_dict:
        for i in budgets_dict['Goals']:
            goals_dict.update({i[0]:i})
            total_goals_expected += float(i[1])
            total_goals_actual += float(i[2])
    
    index_counter = 1
    for category, expenses in expense_categories.items():
        for expense_data in expenses:
            expense_data.append(index_counter)  # Insert index at the beginning
            index_counter += 1
    
    context = {"income_bdgt_dict": income_bdgt_dict, "total_actual_income": total_actual_income,
               "total_income_expected": total_income_expected,
               "bills_dict": bills_dict, "total_actual_bill": total_actual_bill,
               "total_expected_bill": total_expected_bill,
               "expenses_dict": expense_categories,"non_monthly_expenses_dict": non_monthly_expenses_dict, "total_expected_expenses": total_expected_expenses,
               "total_actual_expenses": total_actual_expenses,
               "bank_accounts": bank_accounts_dict,"total_non_monthly_expected_expenses":total_non_monthly_expected_expenses,
               "total_non_monthly_actual_expenses":total_non_monthly_actual_expenses,"goals_dict":goals_dict,"total_goals_expected":total_goals_expected,
               "total_goals_actual":total_goals_actual,'index_counter':index_counter,
               "today_date": str(today_date), "page": "budgets"}

    return render(request, 'budget/budget_walk_through.html', context=context)


@login_required(login_url="/login")
def budgets_income_walk_through(request):
    user_name = request.user
    print("Income request data====>",request.POST)
    if request.method == 'POST' and request.is_ajax():
        budget_name = request.POST['name']
        budget_exp_amount = float(request.POST['exp_amount'])
        budget_act_amount = float(request.POST['actual_amount'])
        budget_id = request.POST['id']
        income_account_id = request.POST['income_account_id']
        budget_left_amount = round(budget_exp_amount - budget_act_amount, 2)
        account_obj = Account.objects.get(id=int(income_account_id))
        # check subcategory exist or not
        try:
            sub_cat_obj = SubCategory.objects.get(category__user=user_name, category__name="Income", name=budget_name)
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()
        except:
            sub_cat_obj = SubCategory()
            sub_cat_obj.category = Category.objects.get(user=user_name, name="Income")
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()

        if budget_id == "false":
            budget_start_date = datetime.datetime.today().date()
            start_month_date, end_month_date = start_end_date(budget_start_date, "Monthly")
            budget_end_date = get_period_date(budget_start_date, "Monthly") - relativedelta(days=1)
            try:
                budget_obj = Budget.objects.filter(user=user_name,name=budget_name, budget_start_date__range=(start_month_date,end_month_date))
                if budget_obj:
                    print("Budget already exists")
                    return JsonResponse({'status': 'false','message':"Budget Already Exists"})
                else:
                    budget_obj = Budget()
            except:
                budget_obj = Budget()
            budget_obj.user = user_name
            budget_obj.start_date = start_month_date
            budget_obj.end_date = end_month_date
            budget_obj.name = budget_name
            budget_obj.category = sub_cat_obj
            budget_obj.currency = '$'
            budget_obj.auto_pay = False
            budget_obj.auto_budget = False
            budget_obj.budget_period = "Monthly"
            budget_obj.account = account_obj
            budget_obj.initial_amount = budget_exp_amount
            budget_obj.amount = budget_exp_amount
            budget_obj.budget_spent = budget_act_amount
            budget_obj.budget_left = budget_left_amount
            budget_obj.created_at = budget_start_date
            budget_obj.ended_at = budget_end_date
            budget_obj.budget_start_date = budget_start_date
            budget_obj.save()
        else:
            budget_obj = Budget.objects.get(id=int(budget_id))
            old_spend_amount = float(budget_obj.budget_spent)
            budget_obj.name = budget_name
            budget_obj.initial_amount = budget_exp_amount
            budget_obj.amount = budget_exp_amount
            budget_obj.budget_spent = budget_act_amount
            budget_obj.budget_left = budget_left_amount
            if income_account_id:
                budget_obj.account = account_obj
            budget_obj.save()
            if budget_act_amount > old_spend_amount:
                budget_act_amount = round(budget_act_amount - old_spend_amount, 2)

        if budget_act_amount > 0:
            account_obj = Account.objects.get(id=int(income_account_id))
            remaining_amount = round(float(account_obj.available_balance) + budget_act_amount, 2)
            tag_obj, tag_created = Tag.objects.get_or_create(user=user_name, name="Incomes")
            transaction_date = datetime.datetime.today().date()
            save_transaction(user_name, sub_cat_obj.name, budget_act_amount, remaining_amount, transaction_date,
                             sub_cat_obj,
                             account_obj,
                             tag_obj, False, True, None, budget_obj)
            account_obj.available_balance = remaining_amount
            account_obj.transaction_count += 1
            account_obj.save()

        return JsonResponse({'status': 'true'})

    income_category = SubCategory.objects.filter(category__user=user_name, category__name='Income')
    context = {"category_groups": "Income", "income_category": income_category, "today_date": str(today_date)}
    context.update({"page": "budgets"})
    return render(request, 'income/income_walk_through.html', context=context)


@login_required(login_url="/login")
def budgets_expenses_walk_through(request):
    user_name = request.user
    if request.method == 'POST' and request.is_ajax():
        budget_name = request.POST['name']
        category_name = request.POST['cat_name']
        budget_exp_amount = float(request.POST['exp_amount'])
        budget_act_amount = float(request.POST['actual_amount'])
        budget_id = request.POST['id']
        expense_account_id = request.POST['expenses_account_id']
        budget_left_amount = round(budget_exp_amount - budget_act_amount, 2)
        budget_start_date = request.POST['budget_date']
        budget_period = request.POST['budget_period']
        account_obj = Account.objects.get(id=int(expense_account_id))
        # check subcategory exist or not
        try:
            sub_cat_obj = SubCategory.objects.get(category__user=user_name, category__name=category_name, name=budget_name)
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()
        except:
            try:
                category_obj = Category.objects.get(user=user_name, name=category_name)
            except:
                category_obj = Category.objects.create(user=user_name, name=category_name)

            sub_cat_obj = SubCategory()
            sub_cat_obj.category = Category.objects.get(user=user_name, name=category_name)
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()

        if budget_id == "false":
            if budget_start_date:
                budget_start_date = datetime.datetime.strptime(budget_start_date, '%Y-%m-%d')
            else:
                budget_start_date = datetime.datetime.today().date()
            start_month_date, end_month_date = start_end_date(budget_start_date, "Monthly")
            budget_end_date = get_period_date(budget_start_date, budget_period) - relativedelta(days=1)
            try:
                budget_obj = Budget.objects.filter(user=user_name,name=budget_name, budget_start_date__range=(start_month_date,end_month_date))
                if budget_obj:
                    print("Budget already exists")
                    return JsonResponse({'status': 'false','message':"Budget Already Exists"})
                else:
                    budget_obj = Budget()
            except:
                budget_obj = Budget()
            budget_obj.user = user_name
            budget_obj.start_date = start_month_date
            budget_obj.end_date = end_month_date
            budget_obj.name = budget_name
            budget_obj.category = sub_cat_obj
            budget_obj.currency = '$'
            budget_obj.auto_pay = False
            budget_obj.auto_budget = False
            budget_obj.account = account_obj
            budget_obj.budget_period = budget_period
            budget_obj.initial_amount = budget_exp_amount
            budget_obj.amount = budget_exp_amount
            budget_obj.budget_spent = budget_act_amount
            budget_obj.budget_left = budget_left_amount
            budget_obj.created_at = budget_start_date
            budget_obj.ended_at = get_period_date(budget_start_date, budget_period) - relativedelta(days=1)
            budget_obj.budget_start_date = budget_start_date
            budget_obj.save()
            if budget_period == 'Yearly':
                budget_amount = budget_exp_amount
                budget_currency = "$"
                budget_auto= False
                subcategory_obj = sub_cat_obj
                for month_value in range(11):
                    start_month_date = start_month_date + relativedelta(months=1)
                    start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")
                    save_budgets(user_name, start_month_date, end_month_date, budget_name, budget_period, budget_currency,
                                budget_amount, budget_auto, budget_start_date, budget_end_date, budget_amount,
                                budget_start_date, subcategory_obj, None, budget_status=True)
        else:
            budget_obj = Budget.objects.get(id=int(budget_id))
            old_spend_amount = float(budget_obj.budget_spent)
            budget_obj.name = budget_name
            budget_obj.initial_amount = budget_exp_amount
            budget_obj.amount = budget_exp_amount
            budget_obj.budget_spent = budget_act_amount
            budget_obj.budget_left = budget_left_amount
            budget_obj.budget_period = budget_period
            budget_obj.account = account_obj
            budget_obj.save()
            if budget_act_amount > old_spend_amount:
                budget_act_amount = round(budget_act_amount - old_spend_amount, 2)
            if budget_period == 'Yearly':
                budget_amount = budget_exp_amount
                budget_currency = "$"
                budget_auto= False
                subcategory_obj = sub_cat_obj
                if budget_start_date:
                    budget_start_date = datetime.datetime.strptime(budget_start_date, '%Y-%m-%d')
                else:
                    budget_start_date = budget_obj.start_date
                start_month_date, end_month_date = start_end_date(budget_start_date, "Monthly")
                budget_end_date = get_period_date(budget_start_date, budget_period) - relativedelta(days=1)
                for month_value in range(11):
                    start_month_date = start_month_date + relativedelta(months=1)
                    start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")
                    save_budgets(user_name, start_month_date, end_month_date, budget_name, budget_period, budget_currency,
                                budget_amount, budget_auto, budget_start_date, budget_end_date, budget_amount,
                                budget_start_date, subcategory_obj, None, budget_status=True)
            
        if budget_act_amount > 0:
            account_obj = Account.objects.get(id=int(expense_account_id))
            remaining_amount = round(float(account_obj.available_balance) - budget_act_amount, 2)
            tag_obj, tag_created = Tag.objects.get_or_create(user=user_name, name=category_name)
            transaction_date = datetime.datetime.today().date()
            save_transaction(user_name, sub_cat_obj.name, budget_act_amount, remaining_amount, transaction_date,
                             sub_cat_obj,
                             account_obj,
                             tag_obj, True, True, None, budget_obj)
            account_obj.available_balance = remaining_amount
            account_obj.transaction_count += 1
            account_obj.save()

        return JsonResponse({'status': 'true'})

    context = {"page": "budgets"}
    return render(request, 'expenses/expense_walk_through.html', context=context)

@login_required(login_url="/login")
def budgets_non_monthly_expenses_walk_through(request):
    user_name = request.user
    print("request data======>",request.POST)
    if request.method == 'POST' and request.is_ajax():
        budget_name = request.POST['name']
        category_name = 'Non-Monthly' #request.POST['cat_name']
        budget_exp_amount = float(request.POST['exp_amount'])
        budget_act_amount = float(request.POST['actual_amount'])
        budget_id = request.POST['id']
        expense_account_id = request.POST['non_monthly_expenses_account_id']
        budget_period = request.POST['budget_period']
        budget_start_date = request.POST['budget_date']
        # print("budget_date",budget_date)
        account_obj = Account.objects.get(id=int(expense_account_id))
        budget_left_amount = round(budget_exp_amount - budget_act_amount, 2)
        # check subcategory exist or not
        try:
            sub_cat_obj = SubCategory.objects.get(category__user=user_name, category__name=category_name, name=budget_name)
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()
        except:
            try:
                category_obj = Category.objects.get(user=user_name, name=category_name)
            except:
                category_obj = Category.objects.create(user=user_name, name=category_name)

            sub_cat_obj = SubCategory()
            sub_cat_obj.category = Category.objects.get(user=user_name, name=category_name)
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()

        if budget_id == "false":
            if budget_start_date:
                budget_start_date = datetime.datetime.strptime(budget_start_date, '%Y-%m-%d')
            else:
                budget_start_date = datetime.datetime.today().date()
            start_month_date, end_month_date = start_end_date(budget_start_date, "Monthly")
            budget_end_date = get_period_date(budget_start_date, budget_period) - relativedelta(days=1)
            try:
                budget_obj = Budget.objects.filter(user=user_name,name=budget_name, budget_start_date__range=(start_month_date,end_month_date))
                if budget_obj:
                    print("Budget already exists")
                    return JsonResponse({'status': 'false','message':"Budget Already Exists"})
                else:
                    budget_obj = Budget()    
            except:
                budget_obj = Budget()
            budget_obj.user = user_name
            budget_obj.start_date = start_month_date
            budget_obj.end_date = end_month_date
            budget_obj.name = budget_name
            budget_obj.category = sub_cat_obj
            budget_obj.currency = '$'
            budget_obj.auto_pay = False
            budget_obj.auto_budget = False
            budget_obj.budget_period = budget_period
            budget_obj.initial_amount = budget_exp_amount
            budget_obj.amount = budget_exp_amount
            budget_obj.account = account_obj
            budget_obj.budget_spent = budget_act_amount
            budget_obj.budget_left = budget_left_amount
            budget_obj.created_at = budget_start_date
            budget_obj.ended_at = get_period_date(budget_start_date, budget_period) - relativedelta(days=1)
            budget_obj.budget_start_date = budget_start_date
            budget_obj.save()
            if budget_period == 'Yearly':
                budget_amount = budget_exp_amount
                budget_currency = "$"
                budget_auto= False
                subcategory_obj = sub_cat_obj
                for month_value in range(11):
                    start_month_date = start_month_date + relativedelta(months=1)
                    start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")
                    save_budgets(user_name, start_month_date, end_month_date, budget_name, budget_period, budget_currency,
                                budget_amount, budget_auto, budget_start_date, budget_end_date, budget_amount,
                                budget_start_date, subcategory_obj, None, budget_status=True)
        else:
            budget_obj = Budget.objects.get(id=int(budget_id))
            old_spend_amount = float(budget_obj.budget_spent)
            budget_obj.name = budget_name
            budget_obj.initial_amount = budget_exp_amount
            budget_obj.amount = budget_exp_amount
            budget_obj.budget_spent = budget_act_amount
            budget_obj.budget_left = budget_left_amount
            budget_obj.budget_period = budget_period
            budget_obj.account = account_obj
            budget_obj.save()
            if budget_act_amount > old_spend_amount:
                budget_act_amount = round(budget_act_amount - old_spend_amount, 2)

            if budget_period == 'Yearly':
                budget_amount = budget_exp_amount
                budget_currency = "$"
                budget_auto= False
                subcategory_obj = sub_cat_obj
                if budget_start_date:
                    budget_start_date = datetime.datetime.strptime(budget_start_date, '%Y-%m-%d')
                else:
                    budget_start_date = budget_obj.start_date
                start_month_date, end_month_date = start_end_date(budget_start_date, "Monthly")
                budget_end_date = get_period_date(budget_start_date, budget_period) - relativedelta(days=1)
                for month_value in range(11):
                    start_month_date = start_month_date + relativedelta(months=1)
                    start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")
                    save_budgets(user_name, start_month_date, end_month_date, budget_name, budget_period, budget_currency,
                                budget_amount, budget_auto, budget_start_date, budget_end_date, budget_amount,
                                budget_start_date, subcategory_obj, None, budget_status=True)
                    
        if budget_act_amount > 0:
            account_obj = Account.objects.get(id=int(expense_account_id))
            remaining_amount = round(float(account_obj.available_balance) - budget_act_amount, 2)
            tag_obj, tag_created = Tag.objects.get_or_create(user=user_name, name=category_name)
            transaction_date = datetime.datetime.today().date()
            save_transaction(user_name, sub_cat_obj.name, budget_act_amount, remaining_amount, transaction_date,
                             sub_cat_obj,
                             account_obj,
                             tag_obj, True, True, None, budget_obj)
            account_obj.available_balance = remaining_amount
            account_obj.transaction_count += 1
            account_obj.save()

        return JsonResponse({'status': 'true'})
    non_monthly_expenses_category = SubCategory.objects.filter(category__user=user_name, category__name='Non-Monthly')
    context = {"category_groups": "Non-Monthly", "non_monthly_expenses_category": non_monthly_expenses_category, "today_date": str(today_date)}
    context.update({"page": "budgets"})
    return render(request, 'non_monthly_expenses/non_monthly_expense_walk_through.html',context=context)

@login_required(login_url="/login")
def budgets_goals_walk_through(request):
    user_name = request.user
    print("request data======>",request.POST)
    if request.method == 'POST' and request.is_ajax():
        budget_name = request.POST['name']
        category_name = 'Goals' #request.POST['cat_name']
        budget_exp_amount = float(request.POST['goal_amount'])
        budget_act_amount = float(request.POST['actual_amount'])
        budget_id = request.POST['id']
        goal_account_id = request.POST['goals_account_id']
        budget_left_amount = round(budget_exp_amount - budget_act_amount, 2)
        account_obj = Account.objects.get(id=int(goal_account_id))
        account_name = account_obj.name
        goal_date = request.POST['goal_date']
        if goal_date == '': goal_date = None
        
        # check subcategory exist or not
        try:
            sub_cat_obj = SubCategory.objects.get(category__user=user_name, category__name=category_name, name=budget_name)
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()
        except:
            try:
                category_obj = Category.objects.get(user=user_name, name=category_name)
            except:
                category_obj = Category.objects.create(user=user_name, name=category_name)

            sub_cat_obj = SubCategory()
            sub_cat_obj.category = Category.objects.get(user=user_name, name=category_name)
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()

        if budget_id == "false":
            budget_start_date = datetime.datetime.today().date()
            start_month_date, end_month_date = start_end_date(budget_start_date, "Monthly")
            budget_end_date = get_period_date(budget_start_date, "Monthly") - relativedelta(days=1)
            try:
                budget_obj = Budget.objects.filter(user=user_name,name=budget_name, budget_start_date__range=(start_month_date,end_month_date))
                if budget_obj:
                    print("Budget already exists")
                    return JsonResponse({'status': 'false','message':"Budget Already Exists"})
                else:
                    budget_obj = Budget()    
            except:
                budget_obj = Budget()
            budget_obj.user = user_name
            budget_obj.start_date = start_month_date
            budget_obj.end_date = end_month_date
            budget_obj.name = budget_name
            budget_obj.category = sub_cat_obj
            budget_obj.currency = '$'
            budget_obj.auto_pay = False
            budget_obj.auto_budget = False
            budget_obj.budget_period = "Monthly"
            budget_obj.initial_amount = budget_exp_amount
            budget_obj.account = account_obj
            budget_obj.amount = budget_exp_amount
            budget_obj.budget_spent = budget_act_amount
            budget_obj.budget_left = budget_left_amount
            budget_obj.created_at = budget_start_date
            budget_obj.ended_at = budget_end_date
            budget_obj.budget_start_date = budget_start_date
            try:
                goal_obj = Goal.objects.get(user=user_name, label=sub_cat_obj)
                # If goal already exists, it'll allocate the budget actual amount to goals
                if goal_obj:
                        budget_obj.save()
                        goal_obj.allocate_amount += budget_act_amount
                        goal_obj.budget_amount += budget_act_amount
                        goal_obj.save()
                        message = "Goal already exists, Budget created!!"
            except:
                # If goal doesn't exists, creates a new one
                goal_obj = Goal()
                goal_obj.user = user_name
                goal_obj.account = account_obj
                goal_obj.goal_amount = budget_exp_amount
                goal_obj.currency = account_obj.currency
                goal_obj.goal_date = goal_date
                goal_obj.label = sub_cat_obj
                goal_obj.allocate_amount = budget_act_amount
                goal_obj.budget_amount += budget_act_amount
                goal_obj.save()
                budget_obj.save()
                message =''
        else:
            budget_obj = Budget.objects.get(id=int(budget_id))
            

            old_spend_amount = float(budget_obj.budget_spent)
            budget_obj.name = budget_name
            budget_obj.initial_amount = budget_exp_amount
            budget_obj.amount = budget_exp_amount
            budget_obj.budget_spent = budget_act_amount
            budget_obj.budget_left = budget_left_amount
            budget_obj.account = account_obj
            try:
                goal_obj = Goal.objects.get(user=user_name,label=budget_obj.category)
                if goal_date != None:
                    goal_obj.goal_date = goal_date
                goal_obj.allocate_amount += round(budget_act_amount - old_spend_amount, 2)
                goal_obj.budget_amount += round(budget_act_amount - old_spend_amount, 2)
                goal_obj.save()
                message ='' 
            except:
                # If budget exists, but the Goal doesn't , It will create a goal with Expected amount as goal amount and transacation amount as budget_amount and allocate amount
                goal_obj = Goal()
                goal_obj.user = user_name
                goal_obj.account = account_obj
                goal_obj.goal_amount = budget_exp_amount
                goal_obj.currency = account_obj.currency
                goal_obj.goal_date = goal_date
                goal_obj.label = sub_cat_obj
                goal_obj.allocate_amount = round(budget_act_amount - old_spend_amount, 2)
                goal_obj.budget_amount += round(budget_act_amount - old_spend_amount, 2)
                goal_obj.save()
                message = "Goal created successfully!!"
            budget_obj.save()
 
            if budget_act_amount > old_spend_amount:
                budget_act_amount = round(budget_act_amount - old_spend_amount, 2)

        if budget_act_amount > 0:
            account_obj = Account.objects.get(id=int(goal_account_id))
            remaining_amount = round(float(account_obj.available_balance) - budget_act_amount, 2)
            tag_obj, tag_created = Tag.objects.get_or_create(user=user_name, name=category_name)
            transaction_date = datetime.datetime.today().date()
            save_transaction(user_name, sub_cat_obj.name, budget_act_amount, remaining_amount, transaction_date,
                             sub_cat_obj,
                             account_obj,
                             tag_obj, True, True, None, budget_obj)
            account_obj.available_balance = remaining_amount
            account_obj.transaction_count += 1
            account_obj.save()

        return JsonResponse({'status': 'true','message':message})
    goals_category = SubCategory.objects.filter(category__user=user_name, category__name='Goals')
    context = {"category_groups": "Goals", "goals_category": goals_category, "today_date": str(today_date),"error":error}
    context.update({"page": "budgets"})
    return render(request, 'goal/goals_walk_through.html')

@login_required(login_url="/login")
def current_budget_box(request):
    user_name = request.user
    print("usernmame",user_name,"request data====>",request.GET)
    if request.method == 'POST':
        month_name = "01-" + request.POST['select_period']
        date_value = datetime.datetime.strptime(month_name, "%d-%b-%Y").date()
        current_month = datetime.datetime.strftime(date_value, "%b-%Y")
        start_date, end_date = start_end_date(date_value, "Monthly")
    else:
        date_value = datetime.datetime.today().date()
        current_month = datetime.datetime.strftime(date_value, "%b-%Y")
        start_date, end_date = start_end_date(date_value, "Monthly")

    budget_data = Budget.objects.filter(user=user_name, start_date=start_date, end_date=end_date).order_by(
        '-created_at')
    print("bugdet data=====>",budget_data)
    all_budgets, budget_graph_data, budget_values, budget_currency, list_of_months, current_budget_names_list, \
        budgets_dict, income_bdgt_dict, total_bgt_income = make_budgets_values(user_name, budget_data, "budget_page")

    bills_qs = Bill.objects.filter(user=user_name, date__range=(start_date, end_date)).order_by('-created_at')
    week_daily_dict = {}
    for bill_data in bills_qs:
        bill = bill_data.bill_details
        bill_name = bill.label
        bill_amount = float(bill_data.amount)
        bill_left_amount = float(bill_data.remaining_amount)
        bill_spent_amount = round(bill_amount - bill_left_amount, 2)
        bill_start_date = datetime.datetime.strftime(bill_data.date, "%b %d, %Y")
        transaction_qs = Transaction.objects.filter(user=user_name, bill=bill_data,
                                                    transaction_date__range=(start_date, end_date)).order_by(
            'transaction_date')
        current_spent_amount = 0
        for trans_data in transaction_qs:
            current_spent_amount += float(trans_data.amount)

        if budget_values:
            budget_values[0] += current_spent_amount
            budget_graph_data[0]['data'].append(current_spent_amount)
            budget_graph_data[1]['data'].append(bill_left_amount)
            budget_graph_data[2]['data'].append(0)
        current_budget_names_list.append(bill_name)
        bill_bgt_list = [bill_name, bill_amount, current_spent_amount, bill_left_amount, bill.id, bill.frequency,
                         bill_start_date, bill_start_date, bill_data.currency, bill_spent_amount]

        if bill.frequency != "Daily" and bill.frequency != "Weekly":
            if 'Bills & Subscriptions' in budgets_dict:
                budgets_dict['Bills & Subscriptions'].append(bill_bgt_list)
            else:
                budgets_dict['Bills & Subscriptions'] = [bill_bgt_list]
        else:
            if bill_name in week_daily_dict:
                week_daily_dict[bill_name][0] += bill_amount
                week_daily_dict[bill_name][1] += current_spent_amount
                week_daily_dict[bill_name][2] += bill_left_amount
                week_daily_dict[bill_name][3].append(bill_bgt_list)
            else:
                week_daily_dict[bill_name] = [bill_amount, current_spent_amount, bill_left_amount, [bill_bgt_list]]

    total_expense_list = budget_graph_data[0]['data']
    if 'Bills & Subscriptions' in budgets_dict:
        for key, value in week_daily_dict.items():
            value[3].insert(0, [key, value[0], value[1], value[2], value[3][0][4], value[3][0][5], value[3][0][6],
                                value[3][0][6], value[3][0][8], value[1]])
            budgets_dict['Bills & Subscriptions'].append([key, 0, 0, 0, 0, value[3][0][5], value[3]])
            week_bgt_len = len(value[3]) - 1
            for week_index in range(week_bgt_len):
                current_index = current_budget_names_list.index(key)
                if week_index == week_bgt_len - 1:
                    total_expense_list[current_index] = value[1]
                else:
                    total_expense_list.pop(current_index)
                    current_budget_names_list.pop(current_index)

    left_over_cash = round(total_bgt_income - sum(total_expense_list), 2)
    transaction_key = ['S.No.', 'Date', 'Amount', 'Payee', 'Account', 'Categories', 'Bill', 'Budget']
    transaction_data = Transaction.objects.filter(user=user_name, budgets__isnull=False,
                                                  transaction_date__range=(start_date, end_date)).order_by(
        'transaction_date')
    context = {"list_of_months": list_of_months, "current_month": current_month,
               "budget_graph_currency": budget_currency, 'total_income': total_bgt_income,
               'income_bdgt_dict': income_bdgt_dict, 'left_over_cash': left_over_cash,
               'total_expense': sum(total_expense_list), 'expenses_dict': budgets_dict,
               'all_budgets': all_budgets, 'budget_graph_data': budget_graph_data,
               'cash_flow_names': ['Earned', 'Spent'],
               'cash_flow_data': [{'name': 'Amount', 'data': [total_bgt_income, sum(total_expense_list)]}],
               "budget_bar_id": "#budgets-bar",
               'budget_names': current_budget_names_list,
               "budget_graph_value": total_expense_list,
               "budget_graph_id": "#total_budget",
               "transaction_key": transaction_key,
               "transaction_data": transaction_data,
               "page": "budgets"
               }
    print("context===>",context)
    return render(request, 'budget/current_budget_box.html', context=context)


@login_required(login_url="/login")
def compare_boxes(request):
    user_name = request.user
    return render(request, "budget/compare_boxes.html")


@login_required(login_url="/login")
def compare_different_budget_box(request):
    user_name = request.user
    budget_graph_currency = "$"
    budget_type = "Expenses"
    budgets_qs = Budget.objects.filter(user=user_name).exclude(
        category__category__name__in=["Bills", "Goals", "Funds"])
    bill_qs = Bill.objects.filter(user=user_name)
    if budgets_qs:
        budget_graph_currency = budgets_qs[0].currency
    if bill_qs:
        budget_graph_currency = bill_qs[0].currency
    budgets = list(budgets_qs.values_list('name', flat=True).distinct())
    bill_budgets = list(bill_qs.values_list('label', flat=True).distinct())
    budgets += bill_budgets
    total_budget_count = len(budgets)
    budget1_names = []
    budget2_names = []
    spending_amount_bgt1 = 0
    spending_amount_bgt2 = 0
    earned_amount_bgt1 = 0
    earned_amount_bgt2 = 0
    if budgets:
        earliest = Budget.objects.filter(user=user_name, start_date__isnull=False).order_by('start_date')
        no_budgets = not bool(earliest)
        if no_budgets == False:
            start, end = earliest[0].start_date, earliest[len(earliest) - 1].start_date
            list_of_months = list(OrderedDict(
                ((start + datetime.timedelta(_)).strftime("%b-%Y"), None) for _ in range((end - start).days + 1)).keys())
            split_budgets_count = int(total_budget_count / 2)
            budget1_names = budgets[0:split_budgets_count]
            budget2_names = budgets[split_budgets_count:total_budget_count]
        else:
            list_of_months=[]
    if request.method == 'POST':
        month_name = "01-" + request.POST['select_period']
        budget1_names = request.POST.getlist('budget1_name')
        budget2_names = request.POST.getlist('budget2_name')
        date_value = datetime.datetime.strptime(month_name, "%d-%b-%Y").date()
        current_month = datetime.datetime.strftime(date_value, "%b-%Y")
        start_date, end_date = start_end_date(date_value, "Monthly")
    else:
        date_value = datetime.datetime.today().date()
        current_month = datetime.datetime.strftime(date_value, "%b-%Y")
        start_date, end_date = start_end_date(date_value, "Monthly")

    transaction_data_dict1 = {}
    transaction_data_dict2 = {}
    budget1_graph_value = []
    budget1_bar_value = [{'name': 'Spent', 'data': []}]
    budget2_graph_value = []
    budget2_bar_value = [{'name': 'Spent', 'data': []}]
    budget1_income_graph_value = []
    budget1_income_bar_value = [{'name': 'Earned', 'data': []}]
    budget2_income_graph_value = []
    budget2_income_bar_value = [{'name': 'Earned', 'data': []}]
    income_bgt1_names = []
    income_bgt2_names = []
    expense_bgt1_names = []
    expense_bgt2_names = []

    budget1_bar_value, budget1_graph_value, budget1_income_graph_value, budget1_income_bar_value, expense_bgt1_names, income_bgt1_names, transaction_data_dict1, spending_amount_bgt1, earned_amount_bgt1 = get_cmp_diff_data(
        budget1_names, user_name, start_date, end_date, budget1_bar_value, budget1_graph_value, transaction_data_dict1,
        budget1_income_graph_value, budget1_income_bar_value, expense_bgt1_names, income_bgt1_names,
        spending_amount_bgt1, earned_amount_bgt1)

    budget2_bar_value, budget2_graph_value, budget2_income_graph_value, budget2_income_bar_value, expense_bgt2_names, income_bgt2_names, transaction_data_dict2, spending_amount_bgt2, earned_amount_bgt2 = get_cmp_diff_data(
        budget2_names, user_name, start_date, end_date, budget2_bar_value, budget2_graph_value, transaction_data_dict2,
        budget2_income_graph_value, budget2_income_bar_value, expense_bgt2_names, income_bgt2_names,
        spending_amount_bgt2, earned_amount_bgt2)
    
    # Fetch all bills and budgets
    budget_details = Budget.objects.filter(user=user_name, start_date=start_date, end_date=end_date)
    bill_details = Bill.objects.filter(user=user_name,date__range=(start_date, end_date))
    budget_dict = {}

    # Update Bill and Budget Budgetted amount and Spent amount to budget_dict
    for i in bill_details:
        if i.label in budget1_names:
            budget_dict.update({i.label:[float(i.amount), float(i.amount)- float(i.remaining_amount),i.remaining_amount]})
        if i.label in budget2_names:
            budget_dict.update({i.label:[float(i.amount), float(i.amount)- float(i.remaining_amount),i.remaining_amount]})
    
    for i in budget_details:
        if i.name in budget1_names:
            budget_dict.update({i.name:[float(i.initial_amount),i.budget_spent, float(i.initial_amount) - float(i.budget_spent)]})
        if i.name in budget2_names:
            budget_dict.update({i.name:[float(i.initial_amount),i.budget_spent, float(i.initial_amount) - float(i.budget_spent)]})
    
    context = {"budgets": budgets, "list_of_months": list_of_months,
               "budget1_names": budget1_names,
               "budget2_names": budget2_names,
               'budget_dict': budget_dict,
               "current_month": current_month,
               "total_spent_amount_bgt1": spending_amount_bgt1,
               "total_spent_amount_bgt2": spending_amount_bgt2,
               "total_earn_amount_bgt1": earned_amount_bgt1,
               "total_earn_amount_bgt2": earned_amount_bgt2,
               "transaction_data1": transaction_data_dict1,
               "transaction_data2": transaction_data_dict2,
               "budget_graph_currency": budget_graph_currency,
               'budget_names': expense_bgt1_names,
               "budget_graph_value": budget1_graph_value,
               "budget_graph_data": budget1_bar_value,
               "budget_graph_id": "#total_budget",
               "budget_bar_id": "#budgets-bar",
               'budget_names2': expense_bgt2_names,
               "budget_graph_value2": budget2_graph_value,
               "budget_graph_data2": budget2_bar_value,
               "budget_graph_id2": "#total_budget2",
               "budget_bar_id2": "#budgets-bar2",
               'budget_income_names': income_bgt1_names,
               "budget_income_graph_value": budget1_income_graph_value,
               "budget_income_graph_data": budget1_income_bar_value,
               "budget_income_graph_id": "#total_income_budget",
               "budget_income_bar_id": "#income-budgets-bar",
               'budget_income_names2': income_bgt2_names,
               "budget_income_graph_value2": budget2_income_graph_value,
               "budget_income_graph_data2": budget2_income_bar_value,
               "budget_income_graph_id2": "#total_income_budget2",
               "budget_income_bar_id2": "#income-budgets-bar2",
               "budget_type": budget_type,
               "page": "budgets",
               'no_budgets':no_budgets
               }
    return render(request, 'budget/compare_diff_bgt_box.html', context=context)



@login_required(login_url="/login")
def compare_target_budget_box(request):
    user_name = request.user
    budget_graph_currency = "$"
    budget_type = "Expenses"
    budgets_qs = Budget.objects.filter(user=user_name).exclude(
        category__category__name__in=["Bills", "Goals", "Funds"])
    bill_qs = Bill.objects.filter(user=user_name)
    if budgets_qs:
        budget_graph_currency = budgets_qs[0].currency
    if bill_qs:
        budget_graph_currency = bill_qs[0].currency
    budgets = list(budgets_qs.values_list('name', flat=True).distinct())
    bill_budgets = list(bill_qs.values_list('label', flat=True).distinct())
    budgets += bill_budgets
    total_budget_count = len(budgets)
    budget1_names = []
    spending_amount_bgt1 = 0
    earned_amount_bgt1 = 0
    if budgets:
        earliest = Budget.objects.filter(user=user_name, start_date__isnull=False).order_by('start_date')
        start, end = earliest[0].start_date, earliest[len(earliest) - 1].start_date
        list_of_months = list(OrderedDict(
            ((start + datetime.timedelta(_)).strftime("%b-%Y"), None) for _ in range((end - start).days + 1)).keys())
        split_budgets_count = int(total_budget_count / 2)
        budget1_names = budgets[0:split_budgets_count]
    if request.method == 'POST':
        month_name = "01-" + request.POST['select_period']
        budget1_names = request.POST.getlist('budget1_name')
        date_value = datetime.datetime.strptime(month_name, "%d-%b-%Y").date()
        current_month = datetime.datetime.strftime(date_value, "%b-%Y")
        start_date, end_date = start_end_date(date_value, "Monthly")
    else:
        date_value = datetime.datetime.today().date()
        current_month = datetime.datetime.strftime(date_value, "%b-%Y")
        start_date, end_date = start_end_date(date_value, "Monthly")

    transaction_data_dict1 = {}
    budget1_graph_value = []
    budget1_bar_value = [{'name': 'Spent', 'data': []}]
    budget1_income_graph_value = []
    budget1_income_bar_value = [{'name': 'Earned', 'data': []}]
    income_bgt1_names = []
    expense_bgt1_names = []

    budget1_bar_value, budget1_graph_value, budget1_income_graph_value, budget1_income_bar_value, expense_bgt1_names, income_bgt1_names, transaction_data_dict1, spending_amount_bgt1, earned_amount_bgt1 = get_cmp_diff_data(
        budget1_names, user_name, start_date, end_date, budget1_bar_value, budget1_graph_value, transaction_data_dict1,
        budget1_income_graph_value, budget1_income_bar_value, expense_bgt1_names, income_bgt1_names,
        spending_amount_bgt1, earned_amount_bgt1)

    context = {"budgets": budgets, "list_of_months": list_of_months,
               "budget1_names": budget1_names,
               "current_month": current_month,
               "total_spent_amount_bgt1": spending_amount_bgt1,
               "total_earn_amount_bgt1": earned_amount_bgt1,
               "transaction_data1": transaction_data_dict1,
               "budget_graph_currency": budget_graph_currency,
               'budget_names': expense_bgt1_names,
               "budget_graph_value": budget1_graph_value,
               "budget_graph_data": budget1_bar_value,
               "budget_graph_id": "#total_budget",
               "budget_bar_id": "#budgets-bar",
               'budget_income_names': income_bgt1_names,
               "budget_income_graph_value": budget1_income_graph_value,
               "budget_income_graph_data": budget1_income_bar_value,
               "budget_income_graph_id": "#total_income_budget",
               "budget_income_bar_id": "#income-budgets-bar",
               "budget_type": budget_type,
               "page": "budgets"
               }
    return render(request, 'budget/compare_target_box.html', context=context)


@login_required(login_url="/login")
def sample_budget_box(request):
    date_value = datetime.datetime.today().date()
    start_date, end_date = start_end_date(date_value, "Monthly")
    print(start_date, end_date)
    cash_flow_names = ['Earned', 'Spent']
    cash_flow_data = [{'name': 'Amount', 'data': [1000, 300]}]
    budget_names = ['Hobbies', 'Clothes', 'Gas&Fuel', 'Restaurants', 'Groceries']
    budget_graph_value = [50.0, 70.0, 40.0, 100.0, 40.0]
    budget_graph_data = [{'name': 'Spent', 'data': budget_graph_value},
                         {'name': 'Left', 'data': [50.0, 30.0, 160.0, 50.0, 160.0]},
                         {'name': 'OverSpent', 'data': [0, 0, 0, 0, 0]}]
    translated_data = {
        'earned': _('Earned'),
        'spending': _('Spending')
    }
    context = {"month_start": start_date, "month_end": end_date, "cash_flow_names": cash_flow_names,
               "cash_flow_data": cash_flow_data, "budget_bar_id": "#budgets-bar",
               "budget_graph_data": budget_graph_data, "budget_names": budget_names, "budget_graph_id": "#total_budget",
               "budget_graph_value": budget_graph_value, "budget_graph_currency": "$",
               'translated_data': json.dumps(translated_data),
               "page": "budgets"
               }
    return render(request, 'budget/sample_budget_box.html', context=context)


@login_required(login_url="/login")
def budget_details(request, pk):
    user_name = request.user
    budget_obj = Budget.objects.get(pk=pk)
    transaction_key = ['S.No.', 'Date', 'Amount', 'Payee', 'Account', 'Categories', 'Bill', 'Budget', 'Cleared']
    if request.method == "POST":
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        transaction_data = Transaction.objects.filter(user=user_name, categories=budget_obj.category,
                                                      transaction_date__range=(start_date, end_date)).order_by(
            'transaction_date')
    else:
        start_date = False
        end_date = False
        transaction_data = Transaction.objects.filter(user=user_name, categories=budget_obj.category).order_by(
            'transaction_date')
    context = {
        'budget_obj': budget_obj, 'budget_transaction_data': transaction_data,
        'transaction_key': transaction_key, 'transaction_key_dumbs': json.dumps(transaction_key),
        'start_date': start_date, 'end_date': end_date, "page": "budgets"
    }
    return render(request, "budget/budget_detail.html", context=context)


def make_month_obj(obj, user_name, quarter_list, quarter_value, upcoming_quarter_date, budget_name, budget_period,
                   budget_currency,
                   budget_amount, budget_auto):
    quarter_index = 0
    for month_date in quarter_list:
        if quarter_index == 0:
            obj.start_date = month_date
            obj.end_date = month_date.replace(day=calendar.monthrange(month_date.year, month_date.month)[1])
            obj.initial_amount = budget_amount
            obj.created_at = quarter_value
            obj.ended_at = upcoming_quarter_date
            obj.save()
        else:
            start_date = month_date
            end_date = month_date.replace(day=calendar.monthrange(month_date.year, month_date.month)[1])
            save_budgets(user_name, start_date, end_date, budget_name, budget_period, budget_currency, budget_amount,
                         budget_auto, quarter_value, upcoming_quarter_date, budget_amount)

        quarter_index += 1


class BudgetAdd(LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budget/budget_add.html'

    def get_form_kwargs(self):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""

        kwargs = super(BudgetAdd, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        user_name = self.request.user
        data = super(BudgetAdd, self).get_context_data(**kwargs)
        category_groups = Category.objects.filter(user=user_name)
        categories_list = list(category_groups.values_list('name', flat=True))
        category_suggestions = SuggestiveCategory.objects.all().values_list('name', flat=True)
        suggestion_list = []
        for name in category_suggestions:
            if name not in categories_list:
                suggestion_list.append(name)
        data['category_suggestions'] = suggestion_list
        data['category_groups'] = category_groups
        return data

    def form_valid(self, form):
        obj = form.save(commit=False)
        user_name = self.request.user
        obj.user = user_name
        category_name = form.cleaned_data.get('categories')
        name = self.request.POST['subcategory'].title()
        
        category_obj = Category.objects.get(user=user_name, name=category_name)
        subcategory_obj = SubCategory.objects.get( name=name, category=category_obj)
        obj.category = subcategory_obj
        budget_period = form.cleaned_data['budget_period']
        budget_name = name
        obj.name = budget_name
        budget_check = Budget.objects.filter(user=user_name, name=budget_name)
        if budget_check:
            form.add_error('name', 'Budget already exist')
            return self.form_invalid(form)
        budget_amount = form.cleaned_data['amount']
        budget_currency = form.cleaned_data['currency']
        budget_auto = form.cleaned_data['auto_budget']
        budget_start_date = self.request.POST['budget_date']
        budget_start_date = datetime.datetime.strptime(budget_start_date, '%Y-%m-%d')
        start_month_date, end_month_date = start_end_date(budget_start_date.date(), "Monthly")
        budget_end_date = get_period_date(budget_start_date, budget_period) - relativedelta(days=1)
        obj.start_date = start_month_date
        obj.end_date = end_month_date
        obj.initial_amount = budget_amount
        obj.budget_left = budget_amount
        obj.created_at = budget_start_date
        obj.ended_at = budget_end_date
        obj.budget_start_date = budget_start_date
        obj.save()
        if budget_period == 'Quarterly':
            for month_value in range(2):
                start_month_date = start_month_date + relativedelta(months=1)
                start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")
                save_budgets(user_name, start_month_date, end_month_date, budget_name, budget_period, budget_currency,
                             budget_amount, budget_auto, budget_start_date, budget_end_date, budget_amount,
                             budget_start_date, subcategory_obj, None, budget_status=True)
        if budget_period == 'Yearly':
            for month_value in range(11):
                start_month_date = start_month_date + relativedelta(months=1)
                start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")
                save_budgets(user_name, start_month_date, end_month_date, budget_name, budget_period, budget_currency,
                             budget_amount, budget_auto, budget_start_date, budget_end_date, budget_amount,
                             budget_start_date, subcategory_obj, None, budget_status=True)
        create_budget_request()
        return super().form_valid(form)


def budget_update(request, pk):
    error = False
    budget_obj = Budget.objects.get(pk=pk)
    budget_obj = Budget.objects.get(user=request.user, category=budget_obj.category, name=budget_obj.name,
                                    budget_status=False)
    user_name = request.user
    if request.method == 'POST':
        category_id = int(request.POST['categories'])
        subcategory = request.POST['subcategory']
        currency = request.POST['currency']
        amount = float(request.POST['amount'])
        auto_budget = request.POST.get('auto_budget', False)
        old_budget_period = budget_obj.budget_period
        old_budget_create_date = budget_obj.created_at
        try:
            budget_period = request.POST['budget_period']
            budget_date = request.POST['budget_date']
            budget_date = datetime.datetime.strptime(budget_date, '%Y-%m-%d').date()
        except:
            budget_period = old_budget_period
            budget_date = old_budget_create_date

        budget_already_exist = False
        if subcategory != budget_obj.name:
            budget_check = Budget.objects.filter(user=user_name, name=subcategory)
            if budget_check:
                budget_already_exist = True
        if budget_already_exist:
            error = 'Budget name already exist'
        else:
            category_obj = Category.objects.get(id=category_id)
            subcategory_obj = SubCategory.objects.get(name=subcategory, category=category_obj)
            if auto_budget:
                auto_budget = True
            old_budget_end_date = budget_obj.ended_at
            start_month_date, end_month_date = start_end_date(budget_date, "Monthly")
            budget_end_date = get_period_date(budget_date, budget_period) - relativedelta(days=1)
            if budget_period == old_budget_period:
                if old_budget_create_date == budget_date:
                    try:
                        budget_end_date = get_period_date(budget_date, budget_period) - relativedelta(days=1)
                        current_budget_date = request.POST['current_budget_date']
                        current_budget_amount = float(request.POST['current_amount'])
                        budget_left = round(current_budget_amount - float(budget_obj.budget_spent), 2)
                        Budget.objects.filter(user=user_name, name=budget_obj.name,
                                              created_at=budget_obj.created_at,
                                              ended_at=budget_obj.ended_at).update(name=subcategory,
                                                                                   category=subcategory_obj,
                                                                                   auto_budget=auto_budget,
                                                                                   currency=currency,
                                                                                   amount=current_budget_amount,
                                                                                   initial_amount=amount,
                                                                                   budget_left=budget_left,
                                                                                   created_at=current_budget_date,
                                                                                   ended_at=budget_end_date
                                                                                   )

                    except Exception as e:
                        print("Exception_==========>", e)
                        budget_qs = Budget.objects.filter(user=user_name, name=subcategory).delete()
                        if budget_period == 'Quarterly':
                            for month_value in range(3):
                                if month_value == 2:
                                    budget_status = False
                                else:
                                    budget_status = True
                                save_budgets(user_name, start_month_date, end_month_date, subcategory, budget_period,
                                             currency, amount, auto_budget, budget_date, budget_end_date, amount,
                                             budget_date, subcategory_obj, None, budget_status)
                                start_month_date = start_month_date + relativedelta(months=1)
                                start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")

                        if budget_period == 'Yearly':
                            for month_value in range(12):
                                if month_value == 11:
                                    budget_status = False
                                else:
                                    budget_status = True
                                save_budgets(user_name, start_month_date, end_month_date, subcategory, budget_period,
                                             currency, amount, auto_budget, budget_date, budget_end_date, amount,
                                             budget_date, subcategory_obj, None, budget_status)
                                start_month_date = start_month_date + relativedelta(months=1)
                                start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")

                        if budget_period == 'Daily' or budget_period == 'Weekly' or budget_period == 'Monthly':
                            save_budgets(user_name, start_month_date, end_month_date, subcategory, budget_period,
                                         currency, amount, auto_budget, budget_date, budget_end_date, amount,
                                         budget_date, subcategory_obj)
                else:
                    transaction_qs = Transaction.objects.filter(user=user_name, categories=budget_obj.category)
                    if not transaction_qs:
                        budget_qs = Budget.objects.filter(user=user_name, name=subcategory).delete()
                        if budget_period == 'Quarterly':
                            for month_value in range(3):
                                if month_value == 2:
                                    budget_status = False
                                else:
                                    budget_status = True
                                save_budgets(user_name, start_month_date, end_month_date, subcategory, budget_period,
                                             currency, amount, auto_budget, budget_date, budget_end_date, amount,
                                             budget_date, subcategory_obj, None, budget_status)
                                start_month_date = start_month_date + relativedelta(months=1)
                                start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")

                        if budget_period == 'Yearly':
                            for month_value in range(12):
                                if month_value == 11:
                                    budget_status = False
                                else:
                                    budget_status = True
                                save_budgets(user_name, start_month_date, end_month_date, subcategory, budget_period,
                                             currency, amount, auto_budget, budget_date, budget_end_date, amount,
                                             budget_date, subcategory_obj, None, budget_status)
                                start_month_date = start_month_date + relativedelta(months=1)
                                start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")

                        if budget_period == 'Daily' or budget_period == 'Weekly' or budget_period == 'Monthly':
                            save_budgets(user_name, start_month_date, end_month_date, subcategory, budget_period,
                                         currency, amount, auto_budget, budget_date, budget_end_date, amount,
                                         budget_date, subcategory_obj)

            else:
                # new_budget_qs = Budget.objects.filter(user=user_name, name=subcategory, created_at=budget_date,
                #                                       ended_at=budget_end_date)
                # if new_budget_qs:
                #     error = 'Budget already exists for this period!'
                # else:
                budget_qs = Budget.objects.filter(user=user_name, name=subcategory).delete()
                if budget_period == 'Quarterly':
                    for month_value in range(3):
                        if month_value == 2:
                            budget_status = False
                        else:
                            budget_status = True
                        save_budgets(user_name, start_month_date, end_month_date, subcategory, budget_period,
                                     currency, amount, auto_budget, budget_date, budget_end_date, amount,
                                     budget_date, subcategory_obj, None, budget_status)
                        start_month_date = start_month_date + relativedelta(months=1)
                        start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")

                if budget_period == 'Yearly':
                    for month_value in range(12):
                        if month_value == 11:
                            budget_status = False
                        else:
                            budget_status = True
                        save_budgets(user_name, start_month_date, end_month_date, subcategory, budget_period,
                                     currency, amount, auto_budget, budget_date, budget_end_date, amount,
                                     budget_date, subcategory_obj, None, budget_status)
                        start_month_date = start_month_date + relativedelta(months=1)
                        start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")

                if budget_period == 'Daily' or budget_period == 'Weekly' or budget_period == 'Monthly':
                    save_budgets(user_name, start_month_date, end_month_date, subcategory, budget_period,
                                 currency, amount, auto_budget, budget_date, budget_end_date, amount,
                                 budget_date, subcategory_obj)

        if not error:
            return redirect('/budgets/current')

    categories = Category.objects.filter(user=request.user)
    sub_categories = SubCategory.objects.filter(category__pk=budget_obj.category.category.id)
    budget_periods = ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly']
    transaction_qs = Transaction.objects.filter(user=user_name, categories=budget_obj.category)
    if transaction_qs:
        budget_update_period = True
    else:
        budget_update_period = False

    context = {'budget_data': budget_obj, 'categories': categories, 'sub_categories': sub_categories,
               'currency_dict': currency_dict, 'budget_period': budget_periods,
               'current_budget_date': str(budget_obj.created_at),
               'budget_date': str(budget_obj.budget_start_date), 'errors': error,
               'budget_update_period': budget_update_period,
               "page": "budgets"}
    return render(request, 'budget/budget_update.html', context=context)


class BudgetDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        budget_obj = Budget.objects.get(pk=self.kwargs['pk'])
        budget_name = budget_obj.name
        user_name = self.request.user
        transaction_details = Transaction.objects.filter(user=user_name, budgets__name=budget_name)
        for data in transaction_details:
            delete_transaction_details(data.pk, user_name)

        Budget.objects.filter(user=user_name, name=budget_name).delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


@login_required(login_url="/login")
def template_budget_list(request):
    context = budgets_page_data(request, "", "active")
    context.update({"page": "budgets"})
    return render(request, 'budget/budget_list.html', context=context)


class TemplateAdd(LoginRequiredMixin, CreateView):
    model = TemplateBudget
    form_class = TemplateBudgetForm
    template_name = 'budget/budget_add.html'

    def form_valid(self, form):
        obj = form.save(commit=False)
        user_name = self.request.user
        obj.user = user_name
        budget_period = form.cleaned_data['budget_period']
        date_value = datetime.datetime.today().date()
        budget_name = form.cleaned_data['name']
        budget_amount = form.cleaned_data['amount']
        budget_currency = form.cleaned_data['currency']
        budget_auto = form.cleaned_data['auto_budget']
        start_month_date, end_month_date = start_end_date(date_value, "Monthly")

        obj.start_date = start_month_date
        obj.end_date = end_month_date
        obj.initial_amount = budget_amount
        obj.budget_left = budget_amount

        if budget_period == 'Weekly':
            start_week_date, end_week_date = start_end_date(date_value, budget_period)
            obj.created_at = start_week_date
            obj.ended_at = end_week_date
            obj.save()

        if budget_period == 'Daily':
            obj.created_at = date_value
            obj.ended_at = date_value
            obj.save()

        if budget_period == 'Yearly':
            start_year_date, end_year_date = start_end_date(date_value, budget_period)
            obj.created_at = start_year_date
            obj.ended_at = end_year_date
            obj.save()

        if budget_period == 'Quarterly':
            upcoming_quarter_date, quarter_value = start_end_date(date_value, budget_period)
            obj.created_at = quarter_value
            obj.ended_at = upcoming_quarter_date
            obj.save()

        return super().form_valid(form)


class TemplateUpdate(LoginRequiredMixin, UpdateView):
    model = TemplateBudget
    form_class = TemplateBudgetForm
    template_name = 'budget/budget_update.html'

    def form_valid(self, form):
        user_name = self.request.user
        budget_obj = TemplateBudget.objects.get(user=user_name, pk=self.kwargs['pk'])
        old_amount = float(budget_obj.amount)
        update_amount = float(form.cleaned_data['amount'])
        update_period = form.cleaned_data['budget_period']
        auto_budget = form.cleaned_data['auto_budget']
        if auto_budget == "True":
            is_auto = True
        else:
            is_auto = False
        extra_amount = update_amount - old_amount
        obj = form.save(commit=False)
        obj.start_date = budget_obj.start_date
        obj.end_date = budget_obj.end_date
        obj.amount = update_amount
        obj.budget_left = float(budget_obj.budget_left) + extra_amount
        obj.budget_period = update_period
        obj.auto_budget = is_auto
        obj.created_at = budget_obj.created_at
        obj.ended_at = budget_obj.ended_at
        obj.save()
        return super().form_valid(form)


class TemplateDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        budget_obj = TemplateBudget.objects.get(pk=self.kwargs['pk'])
        budget_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


# @login_required(login_url="/login")
# def template_budget_details(request, pk):
#     user_name = request.user
#     budget_obj = TemplateBudget.objects.get(pk=pk)
#     transaction_key = ['S.No.', 'Date', 'Amount', 'Payee', 'Account', 'Categories', 'Bill', 'Budget', 'Cleared']
#
#     start_date = budget_obj.start_date
#     end_date = budget_obj.end_date
#     going_out_list = [[1, start_date, 100, "gaming", "", ]]
#     transaction_dict = {'Going out': [], 'Groceries': [], 'Bills': []}
#     context = {
#         'budget_obj': budget_obj, 'budget_transaction_data': transaction_data,
#         'transaction_key': transaction_key, 'transaction_key_dumbs': json.dumps(transaction_key),
#         'start_date': start_date, 'end_date': end_date
#     }
#     return render(request, "budget/budget_detail.html", context=context)

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

# Tag Views

def tag_add(request):
    name = request.POST['name'].title()
    user_name = request.user
    tag_obj = Tag.objects.filter(user=user_name, name=name)
    if tag_obj:
        return JsonResponse({"status": "Already Exist"})
    else:
        Tag.objects.create(user=user_name, name=name)
        return JsonResponse({"status": "success", "name": name})


@login_required(login_url="/login")
def transaction_split(request):
    user_name = request.user
    print(request.POST)
    method_name = request.POST['method_name']
    transaction_id = request.POST['transaction_id']
    category_list = ast.literal_eval(request.POST['category_list'])
    amount_list = ast.literal_eval(request.POST['amount_list'])
    original_amount = request.POST['original_amount']
    transaction_obj = Transaction.objects.get(user=user_name, pk=transaction_id)
    transaction_account = transaction_obj.account.name
    try:
        transaction_tags = transaction_obj.tags
    except:
        transaction_tags = None
    transaction_notes = transaction_obj.notes
    transaction_out_flow = transaction_obj.out_flow
    transaction_date = transaction_obj.transaction_date
    transaction_description = transaction_obj.payee
    cleared_amount = "True"
    split_trans_obj_list = []
    split_amount_dict = {}
    list_length = len(category_list)
    for list_index in range(list_length):
        split_amount = round(float(amount_list[list_index]), 2)
        if split_amount == 0.0:
            del amount_list[list_index]
            del category_list[list_index]

    if len(category_list) <= 1:
        return JsonResponse({"status": "error", "message": "Please add more than one category with amount"})
    else:
        print("mehtod_name========>", method_name)
        if method_name == "update_split":
            print("update=============>")
            split_dict = ast.literal_eval(transaction_obj.split_transactions)
            update_cat_list = []
            for key, val in split_dict.items():
                old_category_name = val[0]
                trans_obj = Transaction.objects.get(pk=int(key))
                print("old_category_name", old_category_name)
                print(category_list)
                if old_category_name in category_list:
                    old_amount = round(float(val[1]), 2)
                    split_index = category_list.index(old_category_name)
                    new_amount = round(float(amount_list[split_index]), 2)
                    update_cat_list.append(old_category_name)
                    split_amount_dict[trans_obj.id] = [old_category_name, new_amount]
                    split_trans_obj_list.append(trans_obj)
                    if new_amount != old_amount:
                        print("amount-different")
                        trans_obj.amount = new_amount
                        trans_obj.save()
                else:
                    print("Delete---------->", old_category_name)
                    update_cat_list.append(old_category_name)
                    trans_obj.delete()
            print("update_cat_list====>", update_cat_list)
            print("category_list====>", category_list)
            for i in range(len(category_list)):
                if category_list[i] not in update_cat_list:
                    print("NewCategory======>", category_list[i])
                    split_obj = Transaction()
                    subcategory_obj = SubCategory.objects.get(name=category_list[i], category__user=user_name)
                    transaction_amount = float(amount_list[i])
                    bill_name = ""
                    budget_name = ""
                    out_flow = "False"
                    if subcategory_obj.category.name == "Bills & Subscriptions":
                        bill_name = subcategory_obj.name
                    budget_qs = Budget.objects.filter(user=user_name, category=subcategory_obj)
                    if budget_qs:
                        budget_name = subcategory_obj.name
                    if transaction_out_flow:
                        out_flow = "True"

                    account_obj, budget_obj = transaction_checks(user_name, transaction_amount, transaction_account,
                                                                 bill_name,
                                                                 budget_name, cleared_amount, out_flow,
                                                                 str(transaction_date))
                    split_obj.user = user_name
                    split_obj.categories = subcategory_obj
                    split_obj.amount = round(transaction_amount, 2)
                    split_obj.remaining_amount = account_obj.available_balance
                    split_obj.account = account_obj
                    if transaction_tags:
                        split_obj.tags = transaction_tags
                    split_obj.notes = transaction_notes
                    split_obj.transaction_date = transaction_date
                    split_obj.original_amount = original_amount
                    split_obj.payee = transaction_description
                    split_obj.out_flow = transaction_out_flow
                    if budget_obj:
                        split_obj.budgets = budget_obj
                    if bill_name:
                        split_obj.bill = Bill.objects.get(user=user_name, name=bill_name)
                    split_obj.cleared = True
                    split_obj.save()
                    split_trans_obj_list.append(split_obj)
                    split_amount_dict[split_obj.id] = [category_list[i], split_obj.amount]
        else:
            transaction_obj.original_amount = original_amount
            transaction_obj.amount = amount_list[0]
            split_trans_obj_list.append(transaction_obj)
            split_amount_dict[transaction_obj.id] = [category_list[0], round(float(amount_list[0]), 2)]
            print(split_amount_dict)
            for i in range(1, len(category_list)):
                split_obj = Transaction()
                subcategory_obj = SubCategory.objects.get(name=category_list[i], category__user=user_name)
                transaction_amount = float(amount_list[i])
                bill_name = ""
                budget_name = ""
                out_flow = "False"
                if subcategory_obj.category.name == "Bills & Subscriptions":
                    bill_name = subcategory_obj.name
                budget_qs = Budget.objects.filter(user=user_name, category=subcategory_obj)
                if budget_qs:
                    budget_name = subcategory_obj.name
                if transaction_out_flow:
                    out_flow = "True"

                account_obj, budget_obj = transaction_checks(user_name, transaction_amount, transaction_account,
                                                             bill_name,
                                                             budget_name, cleared_amount, out_flow,
                                                             str(transaction_date))
                split_obj.user = user_name
                split_obj.categories = subcategory_obj
                split_obj.amount = round(transaction_amount, 2)
                split_obj.remaining_amount = account_obj.available_balance
                split_obj.account = account_obj
                if transaction_tags:
                    split_obj.tags = transaction_tags
                split_obj.notes = transaction_notes
                split_obj.transaction_date = transaction_date
                split_obj.original_amount = original_amount
                split_obj.payee = transaction_description
                split_obj.out_flow = transaction_out_flow
                if budget_obj:
                    split_obj.budgets = budget_obj
                if bill_name:
                    split_obj.bill = Bill.objects.get(user=user_name, name=bill_name)
                split_obj.cleared = True
                split_obj.save()
                split_trans_obj_list.append(split_obj)
                split_amount_dict[split_obj.id] = [category_list[i], split_obj.amount]

        print(split_amount_dict)
        print(split_trans_obj_list)
        for obj in split_trans_obj_list:
            obj.split_transactions = split_amount_dict
            obj.tags = obj.tags
            obj.save()

        return JsonResponse({"status": "success"})


@login_required(login_url="/login")
def transaction_list(request):
    user_name = request.user
    if request.method == "POST":
        tag_name = request.POST['tag_name']
        tags_data = request.POST['tags_data']
        if tag_name != 'All':
            transaction_data = Transaction.objects.filter(user=user_name, tags__name=tag_name).order_by(
                '-transaction_date')
        else:
            transaction_data = Transaction.objects.filter(user=user_name).order_by('-transaction_date')
        select_filter = tag_name
    else:
        transaction_data = Transaction.objects.filter(user=user_name).order_by('-transaction_date')
        select_filter = 'All'

    context = transaction_summary(transaction_data, select_filter, user_name)
    context.update({"page": "transaction_list"})
    return render(request, 'transaction/transaction_list.html', context=context)


@login_required(login_url="/login")
def transaction_report(request):
    user_name = request.user
    if request.method == "POST":
        tag_name = request.POST['tag_name']
        tags_data = request.POST['tags_data']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        tags_data = ast.literal_eval(tags_data)
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
        if tag_name != 'All':
            transaction_data = Transaction.objects.filter(user=user_name,
                                                          transaction_date__range=(start_date, end_date),
                                                          tags__name=tag_name).order_by('transaction_date')
        else:
            transaction_data = Transaction.objects.filter(user=user_name,
                                                          transaction_date__range=(start_date, end_date)).order_by(
                'transaction_date')
        select_filter = tag_name
    else:
        start_date = request.GET['start_date']
        end_date = request.GET['end_date']
        if start_date != "" and end_date != "":
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            transaction_data = Transaction.objects.filter(user=user_name,
                                                          transaction_date__range=(start_date, end_date)).order_by(
                'transaction_date')
            select_filter = 'All'
        else:
            return redirect("/transaction_list/")

    context = transaction_summary(transaction_data, select_filter, user_name)
    context['start_date'] = str(start_date)
    context['end_date'] = str(end_date)
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

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        user_name = self.request.user
        tags = Tag.objects.filter(user=user_name)
        data = super(TransactionAdd, self).get_context_data(**kwargs)
        data['tags'] = tags
        return data

    def get_success_url(self):
        """Detect the submit button used and act accordingly"""
        if 'add_other' in self.request.POST:
            url = reverse_lazy('transaction_add')
        elif 'category_page' in self.request.POST:
            url = reverse_lazy('category_list')
        else:
            url = reverse_lazy('transaction_list')
        return url

    def form_valid(self, form):
        obj = form.save(commit=False)
        category_name = form.cleaned_data.get('category')
        name = self.request.POST['subcategory'].title()
        user_name = self.request.user
        category_obj = Category.objects.get(user=user_name, name=category_name)
        subcategory_obj = SubCategory.objects.get(name=name, category=category_obj)
        user_name = self.request.user
        obj.user = user_name
        obj.categories = subcategory_obj
        account = form.cleaned_data.get('account')
        transaction_amount = round(float(form.cleaned_data.get('amount')), 2)
        tags = form.cleaned_data.get('tag_name')
        notes = form.cleaned_data.get('notes')
        print("tags=====>", tags)
        print("notes=====>", notes)
        if tags:
            obj.tags = Tag.objects.get(name=tags, user=user_name)
        if notes:
            obj.notes = notes
        out_flow = form.cleaned_data.get('out_flow')
        cleared_amount = "True"
        bill_name = form.cleaned_data.get('bill')
        # if category_name.name == 'Income':
        #     due_income_id = int(self.request.POST['due_income'])
        #     income_obj = IncomeDetail.objects.get(pk=due_income_id)
        #     income_obj.credited = True
        #     income_obj.save()

        if category_name.name == 'Bills & Subscriptions' or category_name.name == 'Bills':
            due_bill_id = int(self.request.POST['due_bill'])
            bill_name = Bill.objects.get(pk=due_bill_id)
            obj.bill = bill_name
        budget_name = self.request.POST['budget_name']
        transaction_date = form.cleaned_data.get('transaction_date')
        account = account.name
        account_obj, budget_obj = transaction_checks(user_name, transaction_amount, account, bill_name,
                                                     budget_name, cleared_amount, out_flow, transaction_date)
        # For Goals , Add transaction and add the amount to goal allocated amount
        if category_name.name == "Goals":
            goal_obj = Goal.objects.get(user=user_name,label=budget_obj.category)
            if goal_obj:
                goal_obj.allocate_amount += transaction_amount
                goal_obj.budget_amount += transaction_amount
                goal_obj.save()
            
        obj.remaining_amount = account_obj.available_balance
        if budget_obj:
            obj.budgets = budget_obj
        obj.cleared = True
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

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        user_name = self.request.user
        transaction_obj = Transaction.objects.get(pk=self.kwargs['pk'])
        data = super(TransactionUpdate, self).get_context_data(**kwargs)
        categories_data = Category.objects.filter(user=user_name)
        subcategories_data = SubCategory.objects.filter(category__user=user_name)
        select_subcategory = transaction_obj.categories
        subcategory_data = SubCategory.objects.filter(category=select_subcategory.category)
        select_category_id = select_subcategory.category.id
        select_subcategory_id = select_subcategory.id
        select_subcategory_name = select_subcategory.name
        original_amount = transaction_obj.original_amount
        try:
            select_budget_name = transaction_obj.budgets
        except:
            select_budget_name = None
        try:
            tag_name = transaction_obj.tags.name
        except:
            tag_name = None

        split_category = transaction_obj.split_transactions
        if split_category:
            split_category = ast.literal_eval(split_category)
            amount_list = []
            split_cat = []
            for key, value in split_category.items():
                split_cat.append(value[0])
                amount_list.append(value[1])
            data['split_category'] = split_category
            data['split_cat'] = json.dumps(split_cat)
            data['amount_list'] = json.dumps(amount_list)
        data['tags'] = Tag.objects.filter(user=user_name)
        data['select_budget_name'] = select_budget_name
        data['select_category_id'] = select_category_id
        data['select_subcategory_id'] = select_subcategory_id
        data['categories'] = categories_data
        data['subcategories'] = subcategory_data
        data['tag_name'] = tag_name
        data['original_amount'] = original_amount
        data['select_subcategory_name'] = select_subcategory_name
        data['subcategories_data'] = subcategories_data
        data['transaction_id'] = self.kwargs['pk']
        return data

    def form_valid(self, form):
        user_name = self.request.user
        transaction_obj = Transaction.objects.get(pk=self.kwargs['pk'])
        obj = form.save(commit=False)
        account = transaction_obj.account.name.title()
        user_name = self.request.user
        category_name = form.cleaned_data.get('category')
        name = self.request.POST['subcategory'].title()
        category_obj = Category.objects.get(name=category_name,user=user_name)
        subcategory_obj = SubCategory.objects.get(name=name, category=category_obj)
        obj.user = user_name
        obj.categories = subcategory_obj
        transaction_amount = round(float(transaction_obj.amount), 2)
        transaction_out_flow = transaction_obj.out_flow
        update_account = form.cleaned_data.get('account').name.title()
        update_transaction_amount = round(float(form.cleaned_data.get('amount')), 2)
        out_flow = form.cleaned_data.get('out_flow')
        if out_flow == "True":
            out_flow = True
        else:
            out_flow = False

        cleared_amount = "True"
        if category_name.name == 'Income':
            due_income_id = int(self.request.POST['due_income'])
            income_obj = IncomeDetail.objects.get(pk=due_income_id)
            income_obj.credited = True
            income_obj.save()

        if transaction_obj.categories.category.name == 'Income' != category_name.name:
            income_obj = IncomeDetail.objects.get(income__user=user_name, income__account=transaction_obj.account,
                                                  income__sub_category__id=transaction_obj.categories.id,
                                                  income_date=transaction_obj.transaction_date)
            income_obj.credited = False
            income_obj.save()

        if transaction_obj.categories.category.name == 'Bills & Subscriptions' == category_name.name:
            bill_obj = transaction_obj.bill
            bill_amount = float(bill_obj.remaining_amount)
            if transaction_amount != update_transaction_amount:
                bill_amount = bill_amount + transaction_amount
                bill_amount = bill_amount - update_transaction_amount

            if bill_amount == 0.0:
                bill_obj.status = "paid"
                bill_obj.remaining_amount == 0.0
            else:
                bill_obj.status = "unpaid"
                bill_obj.remaining_amount = bill_amount
            bill_obj.save()

        if transaction_obj.categories.category.name == 'Bills & Subscriptions' != category_name.name:
            bill_obj = transaction_obj.bill
            bill_amount = float(bill_obj.remaining_amount)
            bill_obj.status = "unpaid"
            bill_obj.remaining_amount = bill_amount + transaction_amount
            bill_obj.save()
            obj.bill = None
        if transaction_obj.categories.category.name != 'Bills & Subscriptions' == category_name.name:
            due_bill_id = int(self.request.POST['due_bill'])
            bill_obj = Bill.objects.get(pk=due_bill_id)
            bill_amount = float(bill_obj.remaining_amount) - update_transaction_amount
            if bill_amount == 0.0:
                bill_obj.status = "paid"
                bill_obj.remaining_amount == 0.0
            else:
                bill_obj.status = "unpaid"
                bill_obj.remaining_amount = bill_amount
            bill_obj.save()
            obj.bill = bill_obj

        budget_name = self.request.POST['budget_name']
        transaction_date = form.cleaned_data.get('transaction_date')

        if cleared_amount == "True":
            old_account_obj = Account.objects.get(user=user_name, name=account)
            if account == update_account:
                account_obj = Account.objects.get(user=user_name, name=account)
                if transaction_amount != update_transaction_amount:
                    if category_name.name == "Funds":
                        new_fund_obj = AvailableFunds.objects.get(user=user_name, account=account_obj)
                        if transaction_out_flow:
                            fund_total = round(float(new_fund_obj.total_fund) - transaction_amount, 2)
                            fund_total = fund_total + update_transaction_amount
                            new_fund_obj.total_fund = fund_total
                            new_fund_obj.save()
                        else:
                            fund_total = round(float(new_fund_obj.total_fund) + transaction_amount, 2)
                            fund_total = fund_total - update_transaction_amount

                        new_fund_obj.total_fund = fund_total
                        new_fund_obj.save()
                    else:
                        if transaction_obj.categories.category.name == "Funds":
                            old_fund_obj = AvailableFunds.objects.get(user=user_name, account=account_obj)
                            if transaction_out_flow:
                                fund_total = round(float(old_fund_obj.total_fund) - transaction_amount, 2)
                                old_fund_obj.total_fund = fund_total
                                total_fund = old_fund_obj.total_fund
                                total_lock_fund = 0.0
                                goal_qs = Goal.objects.filter(user=user_name, account=old_account_obj)
                                for goal_data in goal_qs:
                                    if total_fund == 0.0:
                                        goal_data.allocate_amount = 0.0
                                        goal_data.save()
                                    else:
                                        if goal_data.allocate_amount > total_fund:
                                            goal_data.allocate_amount = total_fund
                                            total_lock_fund += total_fund
                                            goal_data.save()
                                            total_fund == 0.0
                                        else:
                                            total_fund -= goal_data.allocate_amount
                                            total_lock_fund += goal_data.allocate_amount

                                old_fund_obj.lock_fund = total_lock_fund
                                old_fund_obj.save()
                            else:
                                fund_total = round(float(old_fund_obj.total_fund) + transaction_amount, 2)
                                old_fund_obj.total_fund = fund_total
                                old_fund_obj.save()

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
                account_obj = Account.objects.get(user=user_name, name=update_account)
                if category_name.name == "Funds" or transaction_obj.categories.category.name == "Funds":
                    old_fund_obj = AvailableFunds.objects.get(user=user_name, account=old_account_obj)
                    new_fund_obj = AvailableFunds.objects.get(user=user_name, account=account_obj)
                    if transaction_obj.categories.category.name == "Funds":
                        if transaction_out_flow:
                            old_fund_obj.total_fund = float(old_fund_obj.total_fund) - transaction_amount
                            total_fund = old_fund_obj.total_fund
                            total_lock_fund = 0.0
                            goal_qs = Goal.objects.filter(user=user_name, account=old_account_obj)
                            for goal_data in goal_qs:
                                if total_fund == 0.0:
                                    goal_data.allocate_amount = 0.0
                                    goal_data.save()
                                else:
                                    if goal_data.allocate_amount > total_fund:
                                        goal_data.allocate_amount = total_fund
                                        total_lock_fund += total_fund
                                        goal_data.save()
                                        total_fund == 0.0
                                    else:
                                        total_fund -= goal_data.allocate_amount
                                        total_lock_fund += goal_data.allocate_amount

                            old_fund_obj.lock_fund = total_lock_fund
                            old_fund_obj.save()
                        else:
                            old_fund_obj.total_fund = float(old_fund_obj.total_fund) + transaction_amount
                            old_fund_obj.save()

                    if category_name.name == "Funds":
                        if transaction_out_flow:
                            new_fund_obj.total_fund = float(new_fund_obj.total_fund) + transaction_amount
                            new_fund_obj.save()
                        else:
                            new_fund_obj.total_fund = float(new_fund_obj.total_fund) - transaction_amount
                            new_fund_obj.save()

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

            obj.remaining_amount = account_obj.available_balance
            account_obj.save()

            if budget_name:
                print("yes budget name")
                date_check = datetime.datetime.strptime(transaction_date, "%Y-%m-%d").date()
                start_month_date, end_month_date = start_end_date(date_check, "Monthly")
                budget_obj = Budget.objects.filter(user=user_name, name=budget_name, start_date=start_month_date,
                                                   end_date=end_month_date)[0]
            else:
                date_check = datetime.datetime.strptime(transaction_date, "%Y-%m-%d").date()
                try:
                    transaction_budget_name = transaction_obj.budgets.name
                    transaction_start_date, transaction_end_date = start_end_date(transaction_obj.transaction_date,
                                                                                  "Monthly")

                    budget_obj = Budget.objects.filter(user=user_name, name=transaction_budget_name,
                                                       start_date=transaction_start_date,
                                                       end_date=transaction_end_date)[0]

                    budget_obj = update_budget_items(user_name, budget_obj, transaction_amount, transaction_out_flow,
                                                     date_check)
                    budget_obj.save()

                    budget_obj = None
                except:
                    budget_obj = None

            if budget_obj:
                print("Yes Budget Obj")
                try:
                    transaction_budget_name = transaction_obj.budgets.name
                    transaction_start_date, transaction_end_date = start_end_date(transaction_obj.transaction_date,
                                                                                  "Monthly")
                    if transaction_budget_name == budget_name:
                        print("transaction_out_flow", transaction_out_flow)
                        print("out_flow", out_flow)
                        print(type(transaction_out_flow))
                        print(type(out_flow))
                        if out_flow != transaction_out_flow:
                            budget_obj = update_budget_items(user_name, budget_obj, transaction_amount,
                                                             transaction_out_flow, date_check)
                            budget_obj = add_new_budget_items(user_name, budget_obj, update_transaction_amount,
                                                              out_flow, date_check)
                        if transaction_amount != update_transaction_amount:
                            print("yes amount is not equal to update amount")
                            budget_obj = update_budget_items(user_name, budget_obj, transaction_amount,
                                                             transaction_out_flow, date_check,
                                                             update_transaction_amount)
                    else:
                        old_budget_obj = Budget.objects.get(user=user_name, name=transaction_budget_name,
                                                            start_date=transaction_start_date,
                                                            end_date=transaction_end_date)
                        old_budget_obj = update_budget_items(user_name, old_budget_obj, transaction_amount,
                                                             transaction_out_flow, date_check)
                        old_budget_obj.save()
                        budget_obj = add_new_budget_items(user_name, budget_obj, update_transaction_amount, out_flow,
                                                          date_check)
                except Exception as e:
                    print("exception ========>", e)
                    budget_obj = add_new_budget_items(user_name, budget_obj, update_transaction_amount, out_flow,
                                                      date_check)
                budget_obj.save()

            obj.budgets = budget_obj
        obj.cleared = True
        obj.save()
        return super().form_valid(form)


def delete_transaction_details(pk, user_name, method=None):
    transaction_obj = Transaction.objects.get(pk=pk)
    out_flow = transaction_obj.out_flow
    cleared_amount = transaction_obj.cleared
    account = transaction_obj.account
    sub_category = transaction_obj.categories
    try:
        bill_name = transaction_obj.bill
    except:
        bill_name = False
    try:
        budget_name = transaction_obj.budgets
    except:
        budget_name = False

    transaction_amount = float(transaction_obj.amount)
    if cleared_amount:
        account_obj = Account.objects.get(user=user_name, name=account.name)

        # check category name is funds
        if sub_category.category.name == "Funds":
            fund_obj = AvailableFunds.objects.get(user=user_name, account=account_obj)
            if out_flow:
                fund_obj.total_fund = float(fund_obj.total_fund) - transaction_amount
                total_fund = fund_obj.total_fund
                total_lock_fund = 0.0
                goal_qs = Goal.objects.filter(user=user_name, account=account_obj)
                for goal_data in goal_qs:
                    if total_fund == 0.0:
                        goal_data.allocate_amount = 0.0
                        goal_data.save()
                    else:
                        if goal_data.allocate_amount > total_fund:
                            goal_data.allocate_amount = total_fund
                            total_lock_fund += total_fund
                            goal_data.save()
                            total_fund == 0.0
                        else:
                            total_fund -= goal_data.allocate_amount
                            total_lock_fund += goal_data.allocate_amount

                fund_obj.lock_fund = total_lock_fund
                fund_obj.save()
            else:
                fund_obj.total_fund = float(fund_obj.total_fund) + transaction_amount
                fund_obj.save()

        # if sub_category.category.name == "Income":
        #     income_obj = IncomeDetail.objects.get(income__user=user_name, income__account=account_obj,
        #                                           income__sub_category__id=sub_category.id,
        #                                           income_date=transaction_obj.transaction_date)
        #     income_obj.credited = False
        #     income_obj.save()

        if bill_name and method is None:
            if out_flow:
                bill_name.remaining_amount = round(float(bill_name.remaining_amount) + transaction_amount, 2)
                bill_name.status = "unpaid"
            else:
                bill_name.remaining_amount = round(float(bill_name.remaining_amount) - transaction_amount, 2)
                bill_name.status = "unpaid"

            bill_name.remaining_amount = bill_name.remaining_amount
            bill_name.save()

        if budget_name:
            budget_obj = update_budget_items(user_name, budget_name, transaction_amount, out_flow,
                                             transaction_obj.transaction_date)
            budget_obj.save()

        if out_flow:
            account_obj.available_balance = round(float(account_obj.available_balance) + transaction_amount, 2)
        else:
            account_obj.available_balance = round(float(account_obj.available_balance) - transaction_amount, 2)

        account_obj.transaction_count -= 1
        account_obj.save()

    transaction_obj.delete()


class TransactionDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        user_name = self.request.user
        pk = self.kwargs['pk']
        delete_transaction_details(pk, user_name)
        return JsonResponse({"status": "Successfully", "path": "None"})


def calculate_available_lock_amount(user_name, account_obj):
    fund_data = AvailableFunds.objects.filter(user=user_name, account=account_obj).order_by('created_at')[::-1]
    if fund_data:
        lock_amount = fund_data[0].lock_fund
    goal_data = Goal.objects.filter(user=user_name, account=account_obj)
    total_allocate_amount = 0
    for data in goal_data:
        total_allocate_amount += float(data.allocate_amount)
    if lock_amount:
        available_lock_amount = float(lock_amount) - total_allocate_amount
    else:
        available_lock_amount = total_allocate_amount
    return available_lock_amount


@login_required(login_url="/login")
def goal_obj_save(request, goal_obj, user_name, fun_name=None):
    return_data = {}
    user = request.user
    category_name = request.POST['category']
    sub_category_name = request.POST['sub_category_name']
    goal_amount = request.POST['goal_amount'] 
    goal_date = request.POST['goal_date']
    if goal_date == '': goal_date = None
    account_name = request.POST['account_name']
    
    if 'allocate_amount' in request.POST :
        allocate_amount = float(request.POST['allocate_amount'])
    else:
        allocate_amount  = 0
    
    account_obj = Account.objects.get(user=user,name=account_name)
    fund_amount = 0
    if fun_name:
        # Fetches old goal amount and add the transaction amount to fund amount 
        old_goal_amount = goal_obj.allocate_amount
        if old_goal_amount <= allocate_amount:
            fund_amount = allocate_amount - old_goal_amount  
        
        goal_obj.fund_amount += fund_amount

        # Checks continues for fund
        try:
            fund_obj = AvailableFunds.objects.get(user=user_name, account=account_obj)
            if float(fund_obj.total_fund) < float(allocate_amount):
                return_data['error'] = f"Goal allocate amount is greater than {account_obj.name} account total fund." \
                                       f" please add more fund."
                return return_data
        except:
            return_data[
                'error'] = f"Please add lock fund to {account_obj.name} account first then allocate amount to goal"
            return return_data
        if account_obj != goal_obj.account:
            goal_obj.account = account_obj
            goal_obj.save()
            old_fund_obj = AvailableFunds.objects.get(user=user_name, account=goal_obj.account)
            old_fund_obj.lock_fund = round(float(old_fund_obj.lock_fund) - float(goal_obj.allocate_amount), 2)
            old_fund_obj.save()
            

            if float(allocate_amount) > float(fund_obj.total_fund):
                return_data['error'] = f"Goal allocate amount is greater than {account_obj.name} account lock fund." \
                                       f" please add more lock fund."
                return return_data
            lock_funds = round(float(fund_obj.lock_fund) + float(allocate_amount), 2)
            fund_obj.lock_fund = lock_funds
        else:
            if goal_obj.allocate_amount != float(allocate_amount):
                lock_funds = round(float(fund_obj.lock_fund) + float(allocate_amount), 2)
                fund_obj.lock_fund = lock_funds
                fund_obj.lock_fund = round(float(fund_obj.lock_fund) - float(goal_obj.allocate_amount), 2)
        category_obj = Category.objects.get(user=user, name=category_name)
        if sub_category_name != goal_obj.label.name:
            sub_category = SubCategory.objects.filter(category__user=user, name=sub_category_name)
            if not sub_category:
                sub_category = SubCategory.objects.create(category=category_obj, name=sub_category_name)
            else:
                goal = Goal.objects.filter(user=user, label=sub_category[0])
                if goal:
                    return_data['error'] = "Name is already exist"
                    return return_data
                sub_category = sub_category[0]
        else:
            sub_category = goal_obj.label
        
    else:
        try:
            fund_obj = AvailableFunds.objects.get(user=user_name, account=account_obj)
        except:
            return_data[
                'error'] = f"Please add lock fund to {account_obj.name} account first then allocate amount to goal"
            return return_data
        lock_funds = round(float(fund_obj.lock_fund) + float(allocate_amount), 2)
        fund_obj.lock_fund = lock_funds
        fund_amount = allocate_amount
        
        goal_obj.fund_amount = fund_amount
        if float(allocate_amount) > float(fund_obj.total_fund):
            return_data['error'] = f"Goal allocate amount is greater than {account_obj.name} account lock fund." \
                                   f" please add more lock fund."
            return return_data

        category = Category.objects.filter(user=user, name=category_name)
        if not category:
            category_obj = Category.objects.create(name=category_name, user=user)
        else:
            category_obj = category[0]

        sub_category = SubCategory.objects.filter(category=category_obj, name=sub_category_name)
        if not sub_category:
            sub_category = SubCategory.objects.create(category=category_obj, name=sub_category_name)
        else:
            goal = Goal.objects.filter(user=user, label=sub_category[0])
            if goal:
                return_data['error'] = "Name is already exist"
                return return_data
            sub_category = sub_category[0]

    goal_obj.user = user_name
    goal_obj.account = account_obj
    goal_obj.goal_amount = goal_amount
    goal_obj.currency = account_obj.currency
    goal_obj.goal_date = goal_date
    goal_obj.label = sub_category
    goal_obj.allocate_amount = allocate_amount
    goal_obj.save()
    fund_obj.save()
    return return_data


class GoalList(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'goal/goal_list.html'

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        data = super(GoalList, self).get_context_data(**kwargs)
        user_name = self.request.user
        goal_data = Goal.objects.filter(user=user_name)
        fund_value = show_current_funds(user_name, fun_name='goal_funds')
        fund_key = ['S.No.', 'See Overtime Graph', 'Account Name', 'Current Balance', 'Freeze Amount', 'Used Lock Fund',
                    'Available Fund', 'Action']
        data['fund_key'] = fund_key
        data['fund_value'] = fund_value
        data['goal_data'] = goal_data
        return data


class GoalDetail(LoginRequiredMixin, DetailView):
    model = Goal
    template_name = 'goal/goal_detail.html'


# class GoalAdd(LoginRequiredMixin, CreateView):
#     model = Goal
#     form_class = GoalForm
#     template_name = 'goal/goal_add.html'
#
#     def form_valid(self, form):
#         obj = form.save(commit=False)
#         obj.user = self.request.user
#         obj.save()
#         return super().form_valid(form)


# class GoalUpdate(LoginRequiredMixin, UpdateView):
#     model = Goal
#     form_class = GoalForm
#     template_name = 'goal/goal_update.html'


@login_required(login_url="/login")
def goal_add(request):
    user_name = request.user
    error = False
    print(request.POST)
    if request.method == 'POST':
        goal_obj = Goal()
        goal_data = goal_obj_save(request, goal_obj, user_name)
        if 'error' in goal_data:
            error = goal_data['error']
        else:
            return redirect('/goal_list')

    account_data = Account.objects.filter(user=user_name,
                                          account_type__in=['Checking', 'Savings', 'Cash', 'Credit Card',
                                                            'Line of Credit'])
    category_obj = Category.objects.get(name="Goals", user=user_name)
    sub_obj = SubCategory.objects.filter(category__user=user_name,category__name="Goals")
    context = {'account_data': account_data, 'goal_category': sub_obj,
               "page": "goal_add", "category_icons":category_icons}

    if error:
        context['error'] = error
    return render(request, 'goal/goal_add.html', context=context)


@login_required(login_url="/login")
def goal_update(request, pk):
    user_name = request.user
    error = False
    goal_data = Goal.objects.get(pk=pk)
    if request.method == 'POST':
        goal_result = goal_obj_save(request, goal_data, user_name, fun_name='goal_update')
        if 'error' in goal_result:
            error = goal_result['error']
        else:
            return redirect('/goal_list')

    account_data = Account.objects.filter(user=user_name,
                                          account_type__in=['Checking', 'Savings', 'Cash', 'Credit Card',
                                                            'Line of Credit'])

    category_obj = Category.objects.get(name="Goals", user=user_name)
    context = {'account_data': account_data, 'goal_data': goal_data,
               'goal_category': SubCategory.objects.filter(category=category_obj)}
    if error:
        context['error'] = error
    return render(request, 'goal/goal_update.html', context=context)


class GoalDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        user = request.user
        goal_obj = Goal.objects.get(pk=self.kwargs['pk'])
        fund_obj = AvailableFunds.objects.get(user=user, account=goal_obj.account)
        fund_obj.lock_fund = round(float(fund_obj.lock_fund) - float(goal_obj.fund_amount), 2)
        fund_obj.save()
        goal_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


def account_box(request):
    context = {"page": "account_box"}
    return render(request, 'account/account_box.html', context)


def account_list(request, name):
    account_qs = Account.objects.filter(user=request.user, account_type__in=[name])
    context = {'account_qs': account_qs, 'name': name}
    return render(request, 'account/account_list.html', context=context)


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
        account_name = form.cleaned_data.get('name').title()
        account_type = form.cleaned_data.get('account_type')
        balance = float(form.cleaned_data.get('balance'))
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.name = account_name
        obj.available_balance = balance
        obj.account_type = account_type
        obj.save()

        return super().form_valid(form)


class AccountUpdate(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = AccountForm
    template_name = 'account/account_update.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account_pk = self.kwargs['pk']
        account_obj = Account.objects.get(pk=account_pk)
        context['account_type'] = account_obj.account_type
        context['balance'] = account_obj.available_balance
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        account_type = form.cleaned_data.get('account_type')
        account_name = form.cleaned_data.get('name').title()
        balance = float(form.cleaned_data.get('balance'))
        obj.user = self.request.user
        obj.name = account_name
        obj.account_type = account_type
        obj.balance = balance
        obj.available_balance = balance
        obj.save()
        return super().form_valid(form)


class AccountDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        account_obj = Account.objects.get(pk=self.kwargs['pk'])
        account_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "/account_list/"})


# LOAN VIEW

def loan_accounts_box(request):
    return render(request, 'loan/loan_box.html')


def loan_add(request):
    loan_error = False
    user = request.user
    if request.method == "POST":
        category_name = request.POST['category'].title()
        loan_type = request.POST['loan_type']
        sub_category_name = request.POST['sub_category_name'].title()
        currency = request.POST['currency']
        amount = request.POST['amount']
        interest_rate = request.POST['interest_rate']
        monthly_payment = request.POST['monthly_payment']
        include_net_worth = request.POST['include_net_worth']
        mortgage_date = request.POST['mortgage_date']
        if include_net_worth == "on":
            include_net_worth = True
        else:
            include_net_worth = False

        category = Category.objects.filter(name=category_name)
        if not category:
            category_obj = Category.objects.create(name=category_name, user=user)
        else:
            category_obj = category[0]

        sub_category = SubCategory.objects.filter(category__user=user, name=sub_category_name)
        if not sub_category:
            SubCategory.objects.create(category=category_obj, name=sub_category_name)
            mortgage_year = calculate_tenure(float(amount), float(monthly_payment), float(interest_rate))
            if mortgage_year:
                print(mortgage_year)
                Account.objects.create(name=sub_category_name, user=user, account_type=loan_type, currency=currency,
                                       balance=amount, available_balance=amount, interest_rate=interest_rate,
                                       mortgage_monthly_payment=monthly_payment, mortgage_date=mortgage_date,
                                       mortgage_year=mortgage_year,
                                       include_net_worth=include_net_worth)
                return redirect("/mortgages-loans-accounts/")
            loan_error = "The monthly payment is not sufficient to cover the interest and principal."
        else:
            loan_error = "Name is already exist"

    category = Category.objects.filter(user=user)
    category_list = []
    for data in category:
        if "Mortgage" in data.name or "Loan" in data.name or "Mortgages" in data.name or "Loans" in data.name or "Mortgages and Loans" in data.name or "Mortgages & Loans" in data.name:
            category_list.append(data.name)

    loan_type = ['Mortgage', 'Loan', 'Student Loan', 'Personal Loan', 'Medical Debt', 'Other Debt']
    context = {'category_list': category_list, 'today_date': str(today_date), 'currency_dict': currency_dict,
               'loan_type': loan_type}
    if loan_error:
        context['loan_error'] = loan_error
    return render(request, 'loan/loan_add.html', context=context)


def loan_list(request, name):
    account = Account.objects.filter(user=request.user, account_type__in=[name])
    loan_accounts = []
    for data in account:
        transaction_data = Transaction.objects.filter(user=request.user, categories__name=data.name)
        loan_accounts.append({'id': data.id, 'name': data.name, 'account_type': data.account_type,
                              'available_balance': data.available_balance, 'currency': data.currency,
                              'interest_rate': data.interest_rate, 'updated_at': data.updated_at,
                              'transaction_count': len(transaction_data)})

    return render(request, 'loan/loan_list.html', context={'account': loan_accounts, 'name': name})


def loan_update(request, pk):
    user = request.user
    account = Account.objects.get(pk=pk)
    loan_error = False
    if request.method == "POST":
        category_name = request.POST['category'].title()
        loan_type = request.POST['loan_type']
        sub_category_name = request.POST['sub_category_name'].title()
        currency = request.POST['currency']
        amount = request.POST['amount']
        interest_rate = request.POST['interest_rate']
        monthly_payment = request.POST['monthly_payment']
        include_net_worth = request.POST['include_net_worth']
        mortgage_date = request.POST['mortgage_date']
        if include_net_worth == "on":
            include_net_worth = True
        else:
            include_net_worth = False
        account.name = sub_category_name
        account.account_type = loan_type
        account.currency = currency
        account.balance = amount
        account.available_balance = amount
        account.interest_rate = interest_rate
        account.mortgage_monthly_payment = monthly_payment
        account.mortgage_date = mortgage_date
        account.include_net_worth = include_net_worth

        if account.name != sub_category_name:
            category_obj = Category.objects.get(name=category_name)
            sub_category = SubCategory.objects.filter(category__user=user, name=sub_category_name)
            if not sub_category:
                SubCategory.objects.create(category=category_obj, name=sub_category_name)
                mortgage_year = calculate_tenure(float(amount), float(monthly_payment), float(interest_rate))
                if mortgage_year:
                    account.mortgage_year = mortgage_year
                    account.save()
                    return redirect(f"/mortgages-loans-accounts/{loan_type}")
                loan_error = "The monthly payment is not sufficient to cover the interest and principal."
            else:
                loan_error = "Name is already exist"
        else:
            mortgage_year = calculate_tenure(float(amount), float(monthly_payment), float(interest_rate))
            if mortgage_year:
                account.mortgage_year = mortgage_year
                account.save()
                return redirect(f"/mortgages-loans-accounts/{loan_type}")
            loan_error = "The monthly payment is not sufficient to cover the interest and principal."

    category = Category.objects.filter(user=user)
    category_list = []
    for data in category:
        if "Mortgage" in data.name or "Loan" in data.name or "Mortgages" in data.name or "Loans" in data.name or "Mortgages and Loans" in data.name or "Mortgages & Loans" in data.name:
            category_list.append(data.name)

    loan_type = ['Mortgage', 'Loan', 'Student Loan', 'Personal Loan', 'Medical Debt', 'Other Debt']
    context = {'category_list': category_list, 'today_date': str(today_date), 'currency_dict': currency_dict,
               'loan_type': loan_type, 'account': account}
    if loan_error:
        context['loan_error'] = loan_error
    return render(request, 'loan/loan_update.html', context=context)


def loan_delete(request, pk):
    user = request.user
    account = Account.objects.get(pk=pk)
    account_type = account.account_type
    sub_category = SubCategory.objects.get(category__user=user, name=account.name)
    user = request.user
    transaction_details = Transaction.objects.filter(user=user, categories=sub_category)
    for data in transaction_details:
        delete_transaction_details(data.pk, user)
    sub_category.delete()
    account.delete()
    return JsonResponse({"status": "Successfully", "path": f"/mortgages-loans-accounts/{account_type}"})


def loan_details(request, pk):
    account = Account.objects.get(pk=pk)
    amount = float(account.balance)
    interest = float(account.interest_rate)
    tenure_months = int(account.mortgage_year)
    mortgage_date = account.mortgage_date
    monthly_payment = account.mortgage_monthly_payment
    table = calculator(amount, interest, tenure_months, tenure_months)
    total_payment = abs(table['principle'].sum() + table['interest'].sum())
    json_records = table.reset_index().to_json(orient='records')
    data = json.loads(json_records)
    mortgage_key, mortgage_graph_data, last_month, mortgage_date_data = make_mortgage_data(data, tenure_months,
                                                                                           mortgage_date)
    transaction_key = ['S.No.', 'Date', 'Amount', 'Payee', 'Account', 'Categories', 'Bill', 'Budget', 'Cleared']
    categories = SubCategory.objects.get(name=account.name)
    transaction_data = Transaction.objects.filter(user=request.user, categories=categories, out_flow=True)
    total_pay_amount = list(transaction_data.values_list('amount', flat=True))
    total_pay_amount = [float(x) for x in total_pay_amount]
    print(sum(total_pay_amount))
    remaining_amount = float(total_payment) - float(sum(total_pay_amount))

    context = {
        'data': data,
        'monthly_payment': monthly_payment,
        'remaining_amount': remaining_amount,
        'last_month': last_month,
        'days': tenure_months,
        'total_payment': total_payment,
        'mortgage_key': mortgage_key,
        'mortgage_key_dumbs': json.dumps(mortgage_key),
        'mortgage_graph_data': mortgage_graph_data,
        'mortgage_date_data': mortgage_date_data,
        'account': account,
        'transaction_key': transaction_key,
        'transaction_data': transaction_data,

    }

    return render(request, 'loan/loan_detail.html', context=context)


class LiabilityAdd(LoginRequiredMixin, CreateView):
    # model = Account
    form_class = LiabilityForm
    template_name = 'liability/liability_add.html'

    def post(self, request, *args, **kwargs):
        name = request.POST['name']
        currency = request.POST['currency']
        liability_type = request.POST['liability_type']
        balance = float(request.POST['balance'])
        interest_rate = float(request.POST['interest_rate'])
        interest_period = request.POST['interest_period']
        mortgage_year = int(request.POST['mortgage_year'])
        try:
            include_net_worth = request.POST['include_net_worth']
            include_net_worth = True
        except:
            include_net_worth = False

        table = calculator(balance, interest_rate, mortgage_year)

        total_payment = abs(table['principle'].sum() + table['interest'].sum())
        liability_obj = Account()
        liability_obj.user = request.user
        liability_obj.name = name
        liability_obj.currency = currency
        liability_obj.liability_type = liability_type
        liability_obj.balance = round(balance, 2)
        liability_obj.available_balance = round(total_payment, 2)
        liability_obj.interest_rate = interest_rate
        liability_obj.interest_period = interest_period
        liability_obj.include_net_worth = include_net_worth
        liability_obj.mortgage_year = mortgage_year
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
        balance = float(request.POST['balance'])
        interest_rate = float(request.POST['interest_rate'])
        interest_period = request.POST['interest_period']
        mortgage_year = int(request.POST['mortgage_year'])
        try:
            include_net_worth = request.POST['include_net_worth']
            include_net_worth = True
        except:
            include_net_worth = False

        table = calculator(balance, interest_rate, mortgage_year)

        total_payment = abs(table['principle'].sum() + table['interest'].sum())
        liability_obj = Account.objects.get(pk=self.kwargs['pk'])
        liability_obj.user = request.user
        liability_obj.name = name
        liability_obj.currency = currency
        liability_obj.liability_type = liability_type
        liability_obj.balance = round(balance, 2)
        liability_obj.available_balance = round(total_payment, 2)
        liability_obj.interest_rate = interest_rate
        liability_obj.interest_period = interest_period
        liability_obj.include_net_worth = include_net_worth
        liability_obj.mortgage_year = mortgage_year
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


# FUNDS VIEWS


def show_current_funds(user_name, fun_name=None):
    account_data = Account.objects.all()
    fund_value = []
    for obj in account_data:
        fund_data = AvailableFunds.objects.filter(user=user_name, account=obj).order_by('created_at')[::-1]
        if fund_data:
            fund_obj = fund_data[0]
            transaction_data = Transaction.objects.filter(user=user_name, account=obj)
            spend_amount = 0
            for transaction in transaction_data:
                if transaction.cleared:
                    if transaction.out_flow:
                        spend_amount += float(transaction.amount)
                    else:
                        if spend_amount != 0:
                            spend_amount -= float(transaction.amount)

            if fun_name:
                available_lock_amount = calculate_available_lock_amount(user_name, obj)
                available_lock_amount = round(float(fund_obj.total_fund) - float(fund_obj.lock_fund), 2)
                fund_value.append(
                    [fund_obj.account.name, fund_obj.account.available_balance, fund_obj.total_fund,
                     fund_obj.lock_fund, available_lock_amount, fund_obj.id])
            else:
                fund_value.append([fund_obj.account.name, fund_obj.account.available_balance, fund_obj.total_fund,
                                   fund_obj.lock_fund, available_lock_amount, fund_obj.id])

    return fund_value


class FundList(LoginRequiredMixin, ListView):
    model = AvailableFunds
    template_name = 'funds/funds_list.html'

    def get_context_data(self, **kwargs):
        data = super(FundList, self).get_context_data(**kwargs)
        user_name = self.request.user
        fund_value = show_current_funds(user_name, fun_name='goal_funds')
        fund_key = ['S.No.', 'See Overtime Graph', 'Account Name', 'Current Balance', 'Freeze Amount', 'Used Lock Fund',
                    'Available Fund', 'Action']
        data['fund_key'] = fund_key
        data['fund_value'] = fund_value
        return data


@login_required(login_url="/login")
def fund_overtime(request):
    if request.method == 'POST' and request.is_ajax():
        user_name = request.user
        account_name = request.POST['account_name']
        transaction_qs = Transaction.objects.filter(user=user_name, account__name=account_name,
                                                    categories__category__name='Funds').order_by('transaction_date')
        if transaction_qs:
            min_date = transaction_qs[0].transaction_date
            max_date = datetime.datetime.today().date()
            day_diff = (max_date - min_date).days
            freeze_funds = []
            account_date_list = []
            fund_graph_data = []
            outflow_count = 0
            for transaction_data in transaction_qs:
                account_date_list.append(str(transaction_data.transaction_date))
                if transaction_data.out_flow:
                    outflow_count += 1
                    freeze_funds.append(float(transaction_data.amount))

                else:
                    if outflow_count >= 1:
                        freeze_total = sum(freeze_funds)
                        freeze_funds.append(freeze_total - float(transaction_data.amount))

            fund_graph_data.append({'label_name': 'Freeze Amount', 'data_value': freeze_funds})
            max_value = max(freeze_funds)
            min_value = min(freeze_funds)
            if min_value == max_value:
                min_value = 0

        # account_data = Account.objects.get(user=user_name, name=account_name)
        # transaction_data = Transaction.objects.filter(user=user_name, account=account_data)
        # account_min_date = account_data.created_at.date()
        # print(transaction_data)
        # if transaction_data:
        #     transaction_min_date = transaction_data[0].transaction_date
        #     if transaction_min_date <= account_min_date:
        #         min_date = transaction_min_date
        #     else:
        #         min_date = account_min_date
        # else:
        #     min_date = account_min_date
        # max_date = datetime.datetime.today().date()
        # day_diff = (max_date - min_date).days
        # account_date_list = [str(max_date - datetime.timedelta(days=x)) for x in range(day_diff)]
        # account_date_list.append(str(min_date))
        # account_date_list = account_date_list[::-1]
        # print("account_date_list=======>", account_date_list)
        # total_fund_data = []
        # lock_fund_data = []
        # fund_graph_data = []
        # initial_fund = AvailableFunds.objects.filter(user=user_name, account=account_data)[0]
        # total_fund = float(initial_fund.total_fund)
        # lock_fund = float(initial_fund.lock_fund)
        # account_transaction_value = []
        # acc_create_date = account_data.created_at.date()
        # amount_date_dict = {}
        # if account_data.lock_amount:
        #     acc_current_balance = float(account_data.balance) - float(account_data.lock_amount)
        # else:
        #     acc_current_balance = float(account_data.balance)
        #
        # acc_available_balance = float(acc_current_balance)
        # acc_transaction_data = Transaction.objects.filter(user=user_name, account=account_data).order_by(
        #     'transaction_date')
        # multi_acc_chart(acc_transaction_data, amount_date_dict, acc_current_balance, account_date_list,
        #                 acc_create_date, account_transaction_value, acc_available_balance)
        # print("account_transaction_value", account_transaction_value)
        # for name in account_date_list:
        #     check_date = datetime.datetime.strptime(name, '%Y-%m-%d').date()
        #     fund_data = AvailableFunds.objects.filter(user=user_name, account=account_data, created_at=check_date)
        #     print(fund_data)
        #     if fund_data:
        #         for fund_value in fund_data:
        #             total_fund = float(fund_value.total_fund)
        #             lock_fund = float(fund_value.lock_fund)
        #         total_fund_data.append(round(total_fund, 2))
        #         lock_fund_data.append(round(lock_fund, 2))
        #
        #     else:
        #         total_fund_data.append(total_fund)
        #         lock_fund_data.append(lock_fund)
        #
        # result_list = total_fund_data + lock_fund_data + account_transaction_value
        # max_value = max(result_list)
        # min_value = min(result_list)
        # fund_graph_data.append({'label_name': 'Total Fund', 'data_value': total_fund_data})
        # fund_graph_data.append({'label_name': 'Lock Fund', 'data_value': lock_fund_data})
        # fund_graph_data.append({'label_name': 'Available Fund', 'data_value': account_transaction_value})
        print("fund_graph_data", fund_graph_data)
    return JsonResponse({'fund_data': fund_graph_data, 'date_range_list': account_date_list,
                         'max_value': max_value, 'min_value': min_value})


@login_required(login_url="/login")
def fund_accounts(request):
    context = {}
    return render(request, 'funds/fund_account_box.html', context=context)


@login_required(login_url="/login")
def fund_add(request, name):
    user_name = request.user
    error = False
    
    if request.method == 'POST':
        fund_data = save_fund_obj(request, user_name)

        if 'error' in fund_data:
            error = fund_data['error']
        else:
            return redirect('/goal_list')

    account_data = Account.objects.filter(user=user_name, account_type=name)
    context = {'account_data': account_data, 'name': name}
    if error:
        context['error'] = error
    return render(request, 'funds/funds_add.html', context=context)


@login_required(login_url="/login")
def fund_update(request, pk):
    fund_data = AvailableFunds.objects.get(pk=pk)
    if request.method == 'POST':
        freeze_amount = round(float(request.POST['freeze_amount']), 2)
        old_total_fund = float(fund_data.total_fund)
        if old_total_fund != freeze_amount:
            account_obj = fund_data.account
            account_balance = float(account_obj.available_balance)
            sub_category = SubCategory.objects.get(category__user=fund_data.user, name=account_obj.name)
            transaction_obj = Transaction()
            if freeze_amount > old_total_fund:
                add_amount = freeze_amount - old_total_fund
                remaining_amount = account_balance - add_amount
                transaction_obj.out_flow = True
            else:
                add_amount = old_total_fund - freeze_amount
                if freeze_amount < float(fund_data.lock_fund):
                    context = {'fund_data': fund_data,
                               'error': 'This freeze amount already locked for goals. please add more amount to freeze.'}
                    return render(request, 'funds/funds_update.html', context=context)
                remaining_amount = account_balance + add_amount
                transaction_obj.out_flow = False
                transaction_obj.in_flow = True

            transaction_obj.user = fund_data.user
            transaction_obj.payee = "Self"
            transaction_obj.amount = add_amount
            transaction_obj.remaining_amount = remaining_amount
            transaction_obj.transaction_date = datetime.datetime.today().date()
            transaction_obj.categories = sub_category
            transaction_obj.account = account_obj
            tag_obj, tag_created = Tag.objects.get_or_create(user=fund_data.user, name="Adding Funds")
            if tag_created:
                transaction_obj.tags = tag_obj
            else:
                transaction_obj.tags = tag_obj
            transaction_obj.cleared = True
            account_obj.available_balance = remaining_amount
            account_obj.transaction_count += 1
            account_obj.save()
            transaction_obj.save()
        fund_data.total_fund = freeze_amount
        fund_data.save()
        return redirect('/goal_list')
    context = {'fund_data': fund_data}

    return render(request, 'funds/funds_update.html', context=context)


def fund_delete(request, pk):
    fund_data = AvailableFunds.objects.get(pk=pk)
    account_obj = fund_data.account
    sub_category = SubCategory.objects.get(category__user=fund_data.user, name=account_obj.name)
    goal_qs = Goal.objects.filter(user=fund_data.user, account=account_obj)
    transaction_qs = Transaction.objects.filter(user=fund_data.user, categories=sub_category)
    account_balance = float(account_obj.available_balance)
    remaining_amount = account_balance + float(fund_data.total_fund)
    account_obj.available_balance = remaining_amount
    account_obj.transaction_count -= len(transaction_qs)
    account_obj.save()
    transaction_qs.delete()
    fund_data.delete()
    goal_qs.delete()
    return JsonResponse({"status": "Successfully", "path": "None"})


# class FundUpdate(UpdateView):
#     model = AvailableFunds
#     form_class = FundForm
#     template_name = 'funds/funds_update.html'


# BILL VIEWS

@login_required(login_url="/login")
def bill_details(request, pk):
    user = request.user
    bill_qs = Bill.objects.filter(user=user, bill_details__pk=pk).order_by('date')
    bill_obj = bill_qs[0].bill_details
    bill_dict = {'id': bill_qs[0].bill_details.id, 'label': bill_obj.label, 'account': bill_obj.account,
                 'due_date': bill_obj.date,
                 'amount': bill_obj.amount, 'frequency': bill_obj.frequency,
                 'auto_pay': bill_obj.auto_pay, 'auto_bill': bill_obj.auto_bill, 'due_bills': [],
                 'paid_bills': []}
    for bill in bill_qs:
        if bill.status == "unpaid":
            bill_dict['due_bills'].append(bill)
        else:
            bill_dict['paid_bills'].append(bill)

    transaction_data = Transaction.objects.filter(user=user, bill__bill_details=bill_obj).order_by('-transaction_date')
    context = {"bill_data": bill_dict, 'transaction_data': transaction_data}
    return render(request, "bill/bill_detail.html", context=context)


@login_required(login_url="/login")
def bill_edit(request, pk):
    bill_obj = BillDetail.objects.get(pk=pk)
    form = BillForm(request.POST or None)
    error = ''
    user = request.user
    if form.is_valid():
        label = form.cleaned_data.get('label').title()
        amount = form.cleaned_data.get('amount')
        bill_date = form.cleaned_data.get('date')
        frequency = form.cleaned_data.get('frequency')
        account_name = request.POST['account_name']
        account_obj = Account.objects.get(user=user, name=account_name)
        bill_obj.label = label
        bill_obj.account = account_obj
        bill_obj.amount = amount
        bill_obj.date = bill_date
        try:
            auto_bill = request.POST['auto_bill']
            bill_obj.frequency = frequency
            bill_obj.auto_bill = True
        except:
            bill_obj.auto_bill = False

        try:
            auto_pay = request.POST['auto_pay']
            bill_obj.auto_pay = True
        except:
            bill_obj.auto_pay = False

        try:
            unpaid_apply = request.POST['unpaid_apply']
        except:
            unpaid_apply = 'off'

        if unpaid_apply == 'on':
            bill_obj.auto_pay = True
            bill_qs = Bill.objects.filter(user=request.user, label=label, account=account_obj, status='unpaid')
            for bill in bill_qs:
                remaining_amount = float(bill.remaining_amount)
                paid_amount = float(bill.amount)
                if remaining_amount < paid_amount:
                    continue
                else:
                    bill.label = label
                    bill.account = account_obj
                    bill.currency = account_obj.currency
                    bill.amount = amount
                    bill.date = bill_date
                    bill.bill_details = bill_obj
                    bill.frequency = bill_obj.frequency
                    bill.auto_bill = bill_obj.auto_bill
                    bill.auto_pay = bill_obj.auto_pay
                    bill.save()

        if label != bill_obj.label:
            check_bill_obj = Bill.objects.filter(user=request.user, label=label, account=account_obj)
            if check_bill_obj:
                error = 'Bill Already Exit!!'
            else:
                bill_obj.save()
                return redirect(f"/bill_details/{pk}")
        else:
            bill_obj.save()
            return redirect(f"/bill_details/{pk}")

    bill_category = SubCategory.objects.filter(category__name="Bills & Subscriptions", category__user=user)
    account_qs = Account.objects.filter(user=user, account_type__in=['Checking', 'Savings', 'Cash', 'Credit Card',
                                                                     'Line of Credit'])
    bill_frequency = ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly']
    context = {
        'form': form,
        'error': error,
        'bill_data': bill_obj,
        'currency_dict': currency_dict,
        'bill_category': bill_category,
        'account_qs': account_qs,
        'bill_frequency': bill_frequency
    }
    return render(request, "bill/bill_edit.html", context=context)


@login_required(login_url="/login")
def bill_pay(request, pk):
    bill_obj = Bill.objects.get(pk=pk)
    bill_amount = float(bill_obj.amount)
    account_obj = bill_obj.account
    account_balance = float(account_obj.available_balance)
    if account_balance < bill_amount:
        return JsonResponse({"status": "false"})
    remaining_amount = round(account_balance - bill_amount, 2)
    label = bill_obj.label
    user = bill_obj.user
    categories = SubCategory.objects.get(name=label, category__name='Bills & Subscriptions', category__user=user)
    tag_obj, tag_created = Tag.objects.get_or_create(user=user, name="Bills")
    save_transaction(user, label, bill_amount, remaining_amount, today_date, categories, account_obj,
                     tag_obj, True, True, bill_obj)
    account_obj.available_balance = remaining_amount
    account_obj.transaction_count += 1
    account_obj.save()
    bill_obj.remaining_amount = 0.0
    bill_obj.status = "paid"
    bill_obj.save()
    return JsonResponse({"status": "true"})


@login_required(login_url="/login")
def bill_list(request):
    bill_list_data = BillDetail.objects.filter(user=request.user).order_by('date')
    bill_list = bill_list_data
    bill_data = Bill.objects.filter(user=request.user)
    # If specific dataa requried from dropdown, it will update the bill list
    if 'selected_bill' in request.POST:
        bill_label = request.POST['selected_bill']
        if bill_label != 'all':
            bill_list_data = BillDetail.objects.filter(user=request.user,label=bill_label).order_by('date')
            bill_data = Bill.objects.filter(user=request.user,label=bill_label)
            
    else:
        bill_label = None

    

    calendar_bill_data = []

    for data in bill_data:
        data_dict = {'label': data.label,
                     'date': str(data.date),
                     'label_id': data.bill_details.id
                     }
        if data.status == "unpaid":
            data_dict['calendar_type'] = 'Personal'
        else:
            data_dict['calendar_type'] = 'Holiday'

        calendar_bill_data.append(data_dict)
    context = {"calendar_bill_data": calendar_bill_data, 'bill_list': bill_list ,'bill_data': bill_list_data, 'today_date': today_date,
               'bill_label': bill_label, 'page': 'bill_list'}
    return render(request, "bill/bill_list.html", context=context)


@login_required(login_url="/login")
def bill_detail(request, pk):
    bill_obj = Bill.objects.get(pk=pk)
    transaction_data = Transaction.objects.filter(bill=bill_obj)
    context = {"bill_data": bill_obj, 'transaction_data': transaction_data}
    return render(request, "bill/bill_detail.html", context)


def bill_adding_fun(request, method_name=None):
    form = BillForm(request.POST or None)
    error = ''
    user = request.user
    if form.is_valid():
        label = form.cleaned_data.get('label').title()
        amount = form.cleaned_data.get('amount')
        bill_date = form.cleaned_data.get('date')
        frequency = form.cleaned_data.get('frequency')
        account_name = request.POST['account_name']
        account_obj = Account.objects.get(user=user, name=account_name)
        currency = account_obj.currency
        check_bill_obj = Bill.objects.filter(user=request.user, label=label, account=account_obj)
        if check_bill_obj:
            if method_name:
                return "Bill_list"
            else:
                error = 'Bill Already Exit!!'
        else:
            bill_obj = Bill()
            bill_obj.user = request.user
            bill_obj.label = label
            bill_obj.account = account_obj
            bill_obj.amount = amount
            bill_obj.date = bill_date
            bill_obj.currency = currency
            bill_obj.remaining_amount = amount

            try:
                auto_bill = request.POST['auto_bill']
                bill_obj.frequency = frequency
                bill_obj.auto_bill = True
            except:
                bill_obj.auto_bill = False

            try:
                auto_pay = request.POST['auto_pay']
                bill_obj.auto_pay = True
            except:
                bill_obj.auto_pay = False

            bill_details_obj = BillDetail.objects.create(user=user, label=label, account=account_obj, amount=amount,
                                                         date=bill_date, frequency=bill_obj.frequency,
                                                         auto_bill=bill_obj.auto_bill, auto_pay=bill_obj.auto_pay)
            bill_obj.bill_details = bill_details_obj
            bill_obj.save()
            if bill_date <= today_date:
                check_bill_is_due()
            else:
                create_bill_request()
            return "Bill_list"

    bill_category = SubCategory.objects.filter(category__name="Bills & Subscriptions", category__user=user)
    bill_obj = Category.objects.get(user=user, name="Bills & Subscriptions")
    account_qs = Account.objects.filter(user=user, account_type__in=['Checking', 'Savings', 'Cash', 'Credit Card',
                                                                     'Line of Credit'])
    context = {
        'form': form,
        'error': error,
        'account_qs': account_qs,
        'bill_category': bill_category,
        'bill_id': bill_obj.id
    }
    return context


@login_required(login_url="/login")
def bill_walk_through(request):
    if request.method == 'POST' and request.is_ajax():
        user_name = request.user
        bill_name = request.POST['name']
        bill_exp_amount = float(request.POST['exp_amount'])
        bill_act_amount = float(request.POST['actual_amount'])
        bill_id = request.POST['id']
        bill_account_id = request.POST['bill_account_id']
        bill_left_amount = round(bill_exp_amount - bill_act_amount, 2)
        account_obj = Account.objects.get(id=int(bill_account_id))
        budget_period = request.POST['budget_period']
        bill_date = request.POST['budget_date']
        # check subcategory exist or not
        try:
            sub_cat_obj = SubCategory.objects.get(category__user=user_name, category__name="Bills & Subscriptions",
                                                  name=bill_name)
            sub_cat_obj.name = bill_name
            sub_cat_obj.save()
        except:
            sub_cat_obj = SubCategory()
            sub_cat_obj.category = Category.objects.get(user=user_name, name="Bills & Subscriptions")
            sub_cat_obj.name = bill_name
            sub_cat_obj.save()

        if bill_id == "false":
            if bill_date:
                bill_date = datetime.datetime.strptime(bill_date, '%Y-%m-%d')
            else:
                bill_date = datetime.datetime.today().date()
            bill_date, end_month_date = start_end_date(bill_date, "Monthly")
            bill_obj = Bill()
            bill_obj.user = request.user
            bill_obj.label = bill_name
            bill_obj.account = account_obj
            bill_obj.amount = bill_exp_amount
            bill_obj.date = bill_date
            bill_obj.currency = '$'
            bill_obj.remaining_amount = bill_left_amount
            bill_obj.frequency = budget_period
            bill_obj.auto_bill = False 
            bill_obj.auto_pay = False
            bill_details_obj = BillDetail.objects.create(user=user_name, label=bill_name, account=account_obj,
                                                         amount=bill_exp_amount,
                                                         date=bill_date, frequency=bill_obj.frequency,
                                                         auto_bill=bill_obj.auto_bill, auto_pay=bill_obj.auto_pay)
            bill_obj.bill_details = bill_details_obj
            bill_obj.save()
        else:
            bill_obj = Bill.objects.get(id=int(bill_id))
            old_spend_amount = round(float(bill_obj.amount) - float(bill_obj.remaining_amount), 2)
            bill_obj.name = bill_name
            bill_obj.amount = bill_exp_amount
            bill_obj.remaining_amount = bill_left_amount
            bill_details_obj = bill_obj.bill_details
            bill_details_obj.name = bill_name
            bill_details_obj.amount = bill_exp_amount
            bill_details_obj.save()
            bill_obj.save()

            if bill_act_amount > old_spend_amount:
                bill_act_amount = round(bill_act_amount - old_spend_amount, 2)

        if bill_act_amount > 0:
            account_obj = Account.objects.get(id=int(bill_account_id))
            remaining_amount = round(float(account_obj.available_balance) - bill_act_amount, 2)
            tag_obj, tag_created = Tag.objects.get_or_create(user=user_name, name="Incomes")
            transaction_date = datetime.datetime.today().date()
            save_transaction(user_name, sub_cat_obj.name, bill_act_amount, remaining_amount, transaction_date,
                             sub_cat_obj,
                             account_obj,
                             tag_obj, True, True, bill_obj)
            account_obj.available_balance = remaining_amount
            account_obj.transaction_count += 1
            account_obj.save()
        return JsonResponse({'status': 'true'})
    return render(request, "bill/bill_walk_through.html", context={})


@login_required(login_url="/login")
def bill_add(request):
    context = bill_adding_fun(request, "bill_walk_through")
    if context == "Bill_list":
        return redirect("/bill_list")
    return render(request, "bill/bill_add.html", context=context)


@login_required(login_url="/login")
def bill_update(request, pk):
    bill_obj = Bill.objects.get(pk=pk)
    form = BillForm(request.POST or None)
    error = ''
    user = request.user
    if form.is_valid():
        label = form.cleaned_data.get('label').title()
        amount = form.cleaned_data.get('amount')
        bill_date = form.cleaned_data.get('date')
        frequency = form.cleaned_data.get('frequency')
        account_name = request.POST['account_name']
        account_obj = Account.objects.get(user=user, name=account_name)
        currency = account_obj.currency
        bill_obj.user = request.user
        bill_obj.label = label
        bill_obj.account = account_obj
        bill_obj.amount = amount
        bill_obj.date = bill_date
        bill_obj.currency = currency
        bill_obj.remaining_amount = amount
        try:
            auto_bill = request.POST['auto_bill']
            bill_obj.frequency = frequency
            bill_obj.auto_bill = True
        except:
            bill_obj.auto_bill = False

        try:
            auto_pay = request.POST['auto_pay']
            bill_obj.auto_pay = True
        except:
            bill_obj.auto_pay = False

        if label != bill_obj.label:
            check_bill_obj = Bill.objects.filter(user=request.user, label=label, account=account_obj)
            if check_bill_obj:
                error = 'Bill Already Exit!!'
            else:
                bill_obj.save()
                return redirect(f"/bill_detail/{pk}")
        else:
            bill_date = datetime.datetime.strptime(str(bill_date), '%Y-%m-%d').date()
            if bill_date != bill_obj.date:
                check_bill_obj = Bill.objects.filter(user=request.user, label=label, account=account_obj,
                                                     date=bill_date)
                if check_bill_obj:
                    error = 'Bill Already Exit!!'
                else:
                    bill_obj.save()
                    return redirect(f"/bill_detail/{pk}")
            else:
                bill_obj.save()
                return redirect(f"/bill_detail/{pk}")

    bill_category = SubCategory.objects.filter(category__name="Bills & Subscriptions", category__user=user)
    account_qs = Account.objects.filter(user=user, account_type__in=['Checking', 'Savings', 'Cash', 'Credit Card',
                                                                     'Line of Credit'])
    bill_frequency = ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly']
    context = {
        'form': form,
        'error': error,
        'bill_data': bill_obj,
        'currency_dict': currency_dict,
        'bill_category': bill_category,
        'account_qs': account_qs,
        'bill_frequency': bill_frequency
    }
    return render(request, "bill/bill_update.html", context=context)


@login_required(login_url="/login")
def bill_delete(request, pk):
    bill_obj = BillDetail.objects.get(pk=pk)
    user_name = request.user
    transaction_details = Transaction.objects.filter(user=user_name, bill__bill_details=bill_obj)
    for data in transaction_details:
        delete_transaction_details(data.pk, user_name, "bill_delete")

    bill_obj.delete()
    return JsonResponse({"status": "Successfully", "path": "/bill_list/"})


@login_required(login_url="/login")
def bill_automatic_amount(request):
    bill_id = request.POST['bill_id']
    bill_obj = Bill.objects.get(pk=bill_id)
    return JsonResponse({'bill_amount': bill_obj.remaining_amount})


@login_required(login_url="/login")
def unpaid_bills(request):
    user = request.user
    category_id = int(request.POST['category_id'])
    category_obj = Category.objects.get(user=user,pk=category_id)
    if category_obj.name != "Bills & Subscriptions":
        return JsonResponse({"status": "error"}) 
    subcategory_name = request.POST['sub_category'].strip()
    bill_qs = Bill.objects.filter(user=user, label=subcategory_name, status="unpaid")
    unpaid_bill_dict = {}
    amount_dict = {}
    for data in bill_qs:
        unpaid_bill_dict[data.pk] = data.date
        amount_dict[data.pk] = data.remaining_amount
    return JsonResponse(
        {"status": "true", "unpaid_bill_dict": unpaid_bill_dict, "amount_dict": json.dumps(amount_dict)})


def make_mortgage_data(data, total_month, mortgage_date):
    last_date = mortgage_date + relativedelta(months=+total_month)
    last_month = f'{calendar.month_name[last_date.month]} {last_date.year}'
    balance_data = []
    principle_data = []
    interest_data = []
    mortgage_date_data = [str(mortgage_date + relativedelta(months=+x)) for x in range(total_month)]

    for value in data:
        balance_data.append(value['initial_balance'])
        principle_data.append(abs(value['principle']))
        interest_data.append(abs(value['interest']))

    mortgage_graph_data = [{'name': 'Balance', 'data': balance_data}, {'name': 'Principle', 'data': principle_data},
                           {'name': 'Interest', 'data': interest_data}]

    mortgage_key = ['Month', 'Initial Balance', 'Payment', 'Interest', 'Principle', 'Ending Balance']
    return mortgage_key, mortgage_graph_data, last_month, mortgage_date_data


@login_required(login_url="/login")
def mortgagecalculator(request):
    form = MortgageForm(request.POST or None)
    if form.is_valid():
        initial_amount = form.cleaned_data.get('amount')
        down_payment = form.cleaned_data.get('down_payment')
        amount = float(initial_amount) - float(down_payment)
        interest = form.cleaned_data.get('interest')
        tenure = form.cleaned_data.get('tenure')
        mortgage_date = form.cleaned_data.get('mortgage_date')
        table = calculator(amount, interest, tenure)
        total_payment = abs(table['principle'].sum() + table['interest'].sum())
        total_month = tenure * 12
        json_records = table.reset_index().to_json(orient='records')
        data = json.loads(json_records)
        print(data[0]['initial_balance'])
        monthly_payment = abs(data[0]['principle'] + data[0]['interest'])
        mortgage_key, mortgage_graph_data, last_month, mortgage_date_data = make_mortgage_data(data, total_month,
                                                                                               mortgage_date)
        context = {
            'form': form,
            'data': data,
            'monthly_payment': monthly_payment,
            'last_month': last_month,
            'days': total_month,
            'total_payment': total_payment,
            'mortgage_key': mortgage_key,
            'initial_amount': initial_amount,
            'mortgage_key_dumbs': json.dumps(mortgage_key),
            'mortgage_graph_data': mortgage_graph_data,
            'mortgage_date_data': mortgage_date_data,
            "page": "mortgagecalculator_list"
        }
        return render(request, 'mortgagecalculator_add.html', context)

    context = {
        'form': form,
        "page": "mortgagecalculator_list"
    }
    return render(request, 'mortgagecalculator_add.html', context)


# FUTURE NET WORTH CALCULATOR

@login_required(login_url="/login")
def future_net_worth_calculator(request):
    if request.method == "POST":
        home_value = check_float(request.POST['home_value'])
        vehicle_value = check_float(request.POST['vehicle_value'])
        cash_savings = check_float(request.POST['cash_savings'])
        open_taxable_savings = check_float(request.POST['open_taxable_savings'])
        non_taxable_savings = check_float(request.POST['non_taxable_savings'])
        tax_deferred_savings = check_float(request.POST['tax_deferred_savings'])
        other_asset_value = check_float(request.POST['other_asset_value'])
        home_mortgage_owing = check_float(request.POST['home_mortgage_owing'])
        vehicle_loan_owing = check_float(request.POST['vehicle_loan_owing'])
        s_i_loan_owing = check_float(request.POST['s_i_loan_owing'])
        credit_card_owing = check_float(request.POST['credit_card_owing'])
        student_loan_owing = check_float(request.POST['student_loan_owing'])
        other_loan_owing = check_float(request.POST['other_loan_owing'])
        asset_rate = check_float(request.POST['asset_rate'])
        income = check_float(request.POST['taxable_income'])
        age = int(request.POST['age'])
        currency = request.POST['currency']
        other_liab = others_costs_data(request.POST.getlist('other_liab'))
        other_cost = others_costs_data(request.POST.getlist('other_cost'))

    else:
        home_value = 1000000
        vehicle_value = 25000
        cash_savings = 3000
        open_taxable_savings = 4000
        non_taxable_savings = 1000
        tax_deferred_savings = 2000
        other_asset_value = 10000
        home_mortgage_owing = 750000
        vehicle_loan_owing = 15000
        s_i_loan_owing = 0
        credit_card_owing = 2000
        student_loan_owing = 3000
        other_loan_owing = 0
        other_cost = {}
        other_liab = {}
        asset_rate = 3
        age = 24
        income = 50000
        currency = '$'

    future_list = []
    total_worth = age * income / 10
    total_asset = home_value + vehicle_value + cash_savings + open_taxable_savings + non_taxable_savings + tax_deferred_savings + other_asset_value
    total_debt = home_mortgage_owing + vehicle_loan_owing + s_i_loan_owing + credit_card_owing + student_loan_owing + other_loan_owing
    current_net_worth = total_asset - total_debt

    for key, value in other_cost.items():
        total_asset += value

    for key, value in other_liab.items():
        total_debt += value

    for i in [5, 10, 25]:
        r = asset_rate / 100
        interest_rate = (1 + r) ** i
        fv = round(current_net_worth * interest_rate, 0)
        future_list.append(fv)

    categories_name = ['5 Year', '10 Year', '25 Year']
    categories_series = [{'name': 'Net Worth', 'data': future_list}]
    context = {
        'current_net_worth': current_net_worth,
        'total_asset': total_asset,
        'total_debt': total_debt,
        'age': age,
        'income': income,
        'total_worth': total_worth,
        'currency_dict': currency_dict,
        'currency': currency,
        'home_value': home_value,
        'vehicle_value': vehicle_value,
        'cash_savings': cash_savings,
        'open_taxable_savings': open_taxable_savings,
        'non_taxable_savings': non_taxable_savings,
        'tax_deferred_savings': tax_deferred_savings,
        'other_asset_value': other_asset_value,
        'home_mortgage_owing': home_mortgage_owing,
        'vehicle_loan_owing': vehicle_loan_owing,
        's_i_loan_owing': s_i_loan_owing,
        'credit_card_owing': credit_card_owing,
        'student_loan_owing': student_loan_owing,
        'other_loan_owing': other_loan_owing,
        'other_asset': other_cost,
        'other_liability': other_liab,
        'age': age,
        'taxable_income': income,
        'asset_rate': asset_rate,
        'categories_name': categories_name,
        'categories_series': categories_series
    }

    return render(request, "future_net_worth.html", context=context)


# Rental Property Model Views


class RentalPropertyList(LoginRequiredMixin, ListView):
    model = RentalPropertyModel
    template_name = 'properties/list_property.html'

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        data = super(RentalPropertyList, self).get_context_data(**kwargs)
        user_name = self.request.user
        rental_property_data = RentalPropertyModel.objects.filter(user=user_name)
        property_data = Property.objects.filter(user=user_name)
        account_obj = Account.objects.filter(user=user_name, liability_type='Mortgage')
        property_dict = {}
        liability_dict = {}
        for obj in property_data:
            property_dict[obj.property_name] = obj.id

        for obj in account_obj:
            liability_dict[obj.name] = obj.id

        data['property_data'] = property_dict
        data['liability_data'] = liability_dict
        data['rental_property_data'] = rental_property_data
        return data


@login_required(login_url="/login")
def rental_property_details(request, pk):
    try:
        user_name = request.user
        property_obj = RentalPropertyModel.objects.get(user=user_name, pk=pk)
        down_payment_value = (float(property_obj.purchase_price_detail.selected_price) * float(
            property_obj.purchase_price_detail.down_payment)) / 100
        selected_price = float(property_obj.purchase_price_detail.selected_price)
        amount = float(property_obj.purchase_price_detail.selected_price) - down_payment_value
        interest = float(property_obj.mortgage_detail.interest_rate)
        currency_name = property_obj.currency
        mortgage_year = float(property_obj.mortgage_detail.amortization_year)
        other_cost_dict = ast.literal_eval(property_obj.closing_cost_detail.others_cost)[0]
        total_investement = float(property_obj.closing_cost_detail.total_investment)
        table = calculator(amount, interest, mortgage_year)
        total_payment = abs(table['principle'].sum() + table['interest'].sum())
        total_month = int(mortgage_year * 12)
        json_records = table.reset_index().to_json(orient='records')
        data = json.loads(json_records)
        mortgage_date = property_obj.mortgage_detail.start_date
        mortgage_key, mortgage_graph_data, last_month, mortgage_date_data = make_mortgage_data(data, total_month,
                                                                                               mortgage_date)
        monthly_payment = round(data[0]['principle'] + data[0]['interest'], 2)
        for key in other_cost_dict:
            other_cost_dict[key] = f"{currency_name}{other_cost_dict[key]}"
        other_cost_dict["Total Investment Required"] = f"{currency_name}{total_investement}"
        other_cost_dict["Interest Rate Financed at"] = f"{interest}%"
        other_cost_dict["Monthly Mortgage Payment (Principle & Interest)"] = f"{currency_name}{monthly_payment}"

        investment_data = {'Property Address': property_obj.name,
                           'Property Purchase Price': f"{currency_name}{selected_price}",
                           'Down Payment': f"{currency_name}{down_payment_value}",
                           'Land Transfer Tax': f"{currency_name}{property_obj.closing_cost_detail.transfer_tax}",
                           'Legal Fees': f"{currency_name}{property_obj.closing_cost_detail.legal_fee}",
                           'Title Insurance': f"{currency_name}{property_obj.closing_cost_detail.title_insurance}",
                           'Home Inspection ': f"{currency_name}{property_obj.closing_cost_detail.inspection}",
                           'Appraisal Fee': f"{currency_name}{property_obj.closing_cost_detail.appraisal_fee}",
                           'Purchase of Appliances': f"{currency_name}{property_obj.closing_cost_detail.appliances}",
                           'Renovation Cost': f"{currency_name}{property_obj.closing_cost_detail.renovation_cost}",
                           }

        investment_data.update(other_cost_dict)

        projection_key = []
        total_revenue_list = []
        annual_cash_flow_list = []
        operating_expenses_list = []
        cash_return_list = []
        operating_expenses_ratio_list = []
        net_operating_income_list = []
        debt_cov_ratio_list = []
        net_income_list = []
        appreciation_assumption_list = []
        roi_list = []
        roi_p_list = []
        roi_with_appreciation_list = []
        roi_p_with_appreciation_list = []
        cap_rate_list = []
        cap_rate_include_closing_cost_list = []
        revenue_unit_1_list = []
        mortgage_principle_list = []
        mortgage_interest_list = []
        property_tax_list = []
        insurance_list = []
        maintenance_list = []
        water_list = []
        gas_list = []
        electricity_list = []
        water_heater_rental_list = []
        management_fee_list = []
        vacancy_list = []
        capital_expenditure_list = []
        annual_cash_flow_dict_investors = {}
        net_operating_income_dict_investors = {}
        roi_dict_investors = {}
        roi_with_appreciation_dict_investors = {}
        total_year_return_dict_investors = {}

        total_revenue = float(property_obj.monthly_revenue.total_revenue) * 12
        rent_increase_assumption = float(property_obj.monthly_revenue.rent_increase_assumption)
        interest_appreciation_assumption = float(property_obj.monthly_expenses.appreciation_assumption)
        appreciation_assumption_value = (selected_price * interest_appreciation_assumption) / 100
        all_investment = total_investement + (selected_price - down_payment_value)
        unit_1_value = float(property_obj.monthly_revenue.unit_1) * 12
        property_tax = float(property_obj.monthly_expenses.property_tax) * 12
        insurance = float(property_obj.monthly_expenses.insurance) * 12
        maintenance = float(property_obj.monthly_expenses.maintenance) * 12
        water = float(property_obj.monthly_expenses.water) * 12
        gas = float(property_obj.monthly_expenses.gas) * 12
        electricity = float(property_obj.monthly_expenses.electricity) * 12
        water_heater_rental = float(property_obj.monthly_expenses.water_heater_rental) * 12
        management_fee = float(property_obj.monthly_expenses.management_fee) * 12
        vacancy = float(property_obj.monthly_expenses.vacancy) * 12
        capital_expenditure = float(property_obj.monthly_expenses.capital_expenditure) * 12
        total_expense = float(property_obj.monthly_expenses.total_expenses) * 12
        inflation_assumption = float(property_obj.monthly_expenses.inflation_assumption)

        other_unit_dict = make_others_dict(ast.literal_eval(property_obj.monthly_revenue.others_revenue_cost)[0])
        other_utility_dict = make_others_dict(ast.literal_eval(property_obj.monthly_expenses.other_utilities)[0])
        other_expense_dict = make_others_dict(ast.literal_eval(property_obj.monthly_expenses.other_expenses)[0])
        investors_dict = ast.literal_eval(property_obj.investor_details)[0]
        total_investor_contributions = sum(investors_dict.values())
        excess_short_fall = total_investor_contributions - total_investement
        debt_financing = amount
        total_financing = total_investor_contributions + amount

        for key, units in investors_dict.items():
            investor_contribution = check_zero_division(float(units), total_investor_contributions)
            investor_contribution = round(investor_contribution * 100, 2)
            annual_cash_flow_dict_investors[key] = [investor_contribution]
            net_operating_income_dict_investors[key] = [investor_contribution]
            roi_dict_investors[key] = [investor_contribution]
            roi_with_appreciation_dict_investors[key] = [investor_contribution]
            investors_dict[key] = [f"{currency_name}{units}", f"{investor_contribution}%"]

        start_index = 0
        end_index = 12

        for year in range(1, int(mortgage_year) + 1):
            projection_key.append(f"Year {year}")
            revenue_increase_assumption = total_revenue * rent_increase_assumption / 100
            expense_increase_assumption = total_expense * inflation_assumption / 100
            property_tax_increase = property_tax * inflation_assumption / 100
            insurance_increase = insurance * inflation_assumption / 100
            maintenance_increase = maintenance * inflation_assumption / 100
            water_increase = water * inflation_assumption / 100
            gas_increase = gas * inflation_assumption / 100
            electricity_increase = electricity * inflation_assumption / 100
            water_heater_rental_increase = water_heater_rental * inflation_assumption / 100
            management_fee_increase = management_fee * inflation_assumption / 100
            vacancy_increase = vacancy * inflation_assumption / 100
            capital_expenditure_increase = capital_expenditure * inflation_assumption / 100

            appreciation_assumption_increase = (appreciation_assumption_value * interest_appreciation_assumption) / 100
            unit_1_value_increase = unit_1_value * rent_increase_assumption / 100
            mortgage_principle = 0
            mortgage_interest = 0
            for payment in data[start_index:end_index]:
                mortgage_principle += abs(payment['principle'])
                mortgage_interest += abs(payment['interest'])

            other_units_dict = make_other_data(other_unit_dict, year, mortgage_year, rent_increase_assumption)
            other_utilities_dict = make_other_data(other_utility_dict, year, mortgage_year, rent_increase_assumption)
            other_expenses_dict = make_other_data(other_expense_dict, year, mortgage_year, rent_increase_assumption)

            expenses_ratio = check_zero_division(total_expense, total_revenue)
            expenses_ratio = round(expenses_ratio * 100, 2)
            cash_flow_value = total_revenue - total_expense - (monthly_payment * 12)
            cash_return_value = check_zero_division(cash_flow_value, total_investement)
            cash_return_value = cash_return_value * 100
            income_value = round(total_revenue - total_expense, 2)
            debt_value = check_zero_division(income_value, monthly_payment)
            debt_value = round((debt_value * 12), 2)
            net_income_value = round(income_value - mortgage_interest, 2)
            roi_value = round(cash_flow_value + mortgage_principle, 2)
            roi_p_value = check_zero_division(roi_value, total_investement)
            roi_p_value = round(roi_p_value * 100, 2)
            roi_with_appreciation_value = round(roi_value + appreciation_assumption_value, 2)
            roi_p_with_appreciation_value = check_zero_division(roi_with_appreciation_value, total_investement)
            roi_p_with_appreciation_value = round(roi_p_with_appreciation_value * 100, 2)
            cap_rate_value = check_zero_division(income_value, selected_price)
            cap_rate_value = round(cap_rate_value * 100, 2)
            cap_rate_include_closing_cost_value = check_zero_division(income_value, all_investment)
            cap_rate_include_closing_cost_value = round(cap_rate_include_closing_cost_value * 100, 2)

            for key, value in annual_cash_flow_dict_investors.items():
                investor_value = round(cash_flow_value * value[0] / 100, 2)
                value.append(f"{currency_name}{investor_value}")

            for key, value in net_operating_income_dict_investors.items():
                investor_value = round(income_value * value[0] / 100, 2)
                value.append(f"{currency_name}{investor_value}")

            for key, value in roi_dict_investors.items():
                investor_value = round(roi_value * value[0] / 100, 2)
                value.append(f"{currency_name}{investor_value}")

            for key, value in roi_with_appreciation_dict_investors.items():
                investor_value = round(roi_with_appreciation_value * value[0] / 100, 2)
                value.append(f"{currency_name}{investor_value}")

            total_revenue_list.append(f"{currency_name}{round(total_revenue, 2)}")
            operating_expenses_list.append(f"{currency_name}{round(total_expense, 2)}")
            cash_return_list.append(f"{round(cash_return_value, 2)}%")
            operating_expenses_ratio_list.append(f"{expenses_ratio}%")
            annual_cash_flow_list.append(f"{currency_name}{round(cash_flow_value, 2)}")
            net_operating_income_list.append(f"{currency_name}{income_value}")
            debt_cov_ratio_list.append(debt_value)
            appreciation_assumption_list.append(f"{currency_name}{round(appreciation_assumption_value, 2)}")
            net_income_list.append(f"{currency_name}{net_income_value}")
            roi_list.append(f"{currency_name}{roi_value}")
            roi_p_list.append(f"{roi_p_value}%")
            roi_with_appreciation_list.append(f"{currency_name}{roi_with_appreciation_value}")
            roi_p_with_appreciation_list.append(f"{roi_p_with_appreciation_value}%")
            cap_rate_list.append(f"{cap_rate_value}%")
            cap_rate_include_closing_cost_list.append(f"{cap_rate_include_closing_cost_value}%")
            revenue_unit_1_list.append(f"{round(unit_1_value, 2)}")
            mortgage_principle_list.append(f"{round(mortgage_principle, 2)}")
            mortgage_interest_list.append(f"{round(mortgage_interest, 2)}")
            property_tax_list.append(f"{round(property_tax, 2)}")
            insurance_list.append(f"{round(insurance, 2)}")
            maintenance_list.append(f"{round(maintenance, 2)}")
            water_list.append(f"{round(water, 2)}")
            gas_list.append(f"{round(gas, 2)}")
            electricity_list.append(f"{round(electricity, 2)}")
            water_heater_rental_list.append(f"{round(water_heater_rental, 2)}")
            management_fee_list.append(f"{round(management_fee, 2)}")
            vacancy_list.append(f"{round(vacancy, 2)}")
            capital_expenditure_list.append(f"{round(capital_expenditure, 2)}")

            total_revenue += revenue_increase_assumption
            total_expense += expense_increase_assumption
            unit_1_value += unit_1_value_increase
            appreciation_assumption_value += appreciation_assumption_increase
            property_tax += property_tax_increase
            insurance += insurance_increase
            maintenance += maintenance_increase
            water += water_increase
            gas += gas_increase
            electricity += electricity_increase
            water_heater_rental += water_heater_rental_increase
            management_fee += management_fee_increase
            vacancy += vacancy_increase
            capital_expenditure += capital_expenditure_increase
            start_index = end_index
            end_index += 12

        # Capex Budget data

        capex_budget_obj = property_obj.capex_budget_details
        roof_list = make_capex_budget(ast.literal_eval(capex_budget_obj.roof))
        water_heater_list = make_capex_budget(ast.literal_eval(capex_budget_obj.water_heater))
        all_appliances_list = make_capex_budget(ast.literal_eval(capex_budget_obj.all_appliances))
        bathroom_fixtures_list = make_capex_budget(ast.literal_eval(capex_budget_obj.bathroom_fixtures))
        drive_way_list = make_capex_budget(ast.literal_eval(capex_budget_obj.drive_way))
        furnance_list = make_capex_budget(ast.literal_eval(capex_budget_obj.furnance))
        air_conditioner_list = make_capex_budget(ast.literal_eval(capex_budget_obj.air_conditioner))
        flooring_list = make_capex_budget(ast.literal_eval(capex_budget_obj.flooring))
        plumbing_list = make_capex_budget(ast.literal_eval(capex_budget_obj.plumbing))
        electrical_list = make_capex_budget(ast.literal_eval(capex_budget_obj.electrical))
        windows_list = make_capex_budget(ast.literal_eval(capex_budget_obj.windows))
        paint_list = make_capex_budget(ast.literal_eval(capex_budget_obj.paint))
        kitchen_list = make_capex_budget(ast.literal_eval(capex_budget_obj.kitchen))
        structure_list = make_capex_budget(ast.literal_eval(capex_budget_obj.structure))
        components_list = make_capex_budget(ast.literal_eval(capex_budget_obj.components))
        landscaping_list = make_capex_budget(ast.literal_eval(capex_budget_obj.landscaping))
        others_budgets_dict = ast.literal_eval(capex_budget_obj.other_budgets)[0]
        total_replacement_costs = capex_budget_obj.total_budget_cost
        for key, value in others_budgets_dict.items():
            make_capex_budget(value)

        capex_budget_value = {
            'Roof': roof_list,
            'Water Heater': water_heater_list,
            'All Appliances': all_appliances_list,
            'Bathroom Fixtures (Showers, Vanities, Toilets etc.)': bathroom_fixtures_list,
            'Driveway/Parking Lot': drive_way_list,
            'Furnace': furnance_list,
            'Air Conditioner ': air_conditioner_list,
            'Flooring': flooring_list,
            'Plumbing': plumbing_list,
            'Electrical': electrical_list,
            'Windows': windows_list,
            'Paint': paint_list,
            'Kitchen Cabinets/Counters': kitchen_list,
            'Structure (foundation, framing)': structure_list,
            'Components (garage door, etc.)': components_list,
            'Landscaping': landscaping_list,
        }
        if others_budgets_dict:
            capex_budget_value.update(others_budgets_dict)
        # Yearly projection
        projection_value = {'Total Revenue': total_revenue_list,
                            'Annual Cashflow': annual_cash_flow_list,
                            'Cash on Cash Return (%)': cash_return_list,
                            'Operating Expenses': operating_expenses_list,
                            'Operating Expenses Ratio': operating_expenses_ratio_list,
                            'Net Operating Income (NOI)': net_operating_income_list,
                            'Debt Service Coverage Ratio': debt_cov_ratio_list,
                            'Net Income (Rental Revenue Less Operating Expenses and Interest Expenses)': net_income_list,
                            'Property Appreciation Assumption': appreciation_assumption_list,
                            'Return On Investment % (ROI) (Assuming No Appreciation)': roi_p_list,
                            'Return On Investment (ROI) (Assuming No Appreciation)': roi_list,
                            'Return On Investment % (ROI) (With Appreciation Assumption)': roi_p_with_appreciation_list,
                            'Return On Investment (ROI) (With Appreciation Assumption)': roi_with_appreciation_list,
                            'Capitalization Rate (Cap Rate)': cap_rate_list,
                            'Capitalization Rate (Including all closing costs)': cap_rate_include_closing_cost_list,
                            }

        # yearly Revenues

        revenue_yearly_data = {'Unit 1': revenue_unit_1_list}
        other_unit_dict['Total Revenue'] = total_revenue_list
        revenue_yearly_data.update(other_units_dict)

        # Yearly Expenses
        expenses_yearly_data1 = {'Mortgage Principle': mortgage_principle_list,
                                 'Mortgage Interest': mortgage_interest_list,
                                 'Property Taxes': property_tax_list,
                                 'Insurance': insurance_list,
                                 'Regular Maintenance': maintenance_list,
                                 'Water': water_list,
                                 'Gas': gas_list,
                                 'Electricity': electricity_list,
                                 'Water Heater Rental': water_heater_rental_list,
                                 }
        expenses_yearly_data2 = {'Annual Cashflow': annual_cash_flow_list,
                                 'Cash on Cash Return (%)': cash_return_list,
                                 'Operating Expenses': operating_expenses_list,
                                 'Operating Expenses Ratio': operating_expenses_ratio_list,
                                 'Net Operating Income (NOI)': net_operating_income_list,
                                 'Debt Service Coverage Ratio': debt_cov_ratio_list,
                                 'Net Income (Rental Revenue Less Operating Expenses and Interest Expenses)': net_income_list
                                 }
        expenses_yearly_data1.update(other_utilities_dict)
        expenses_yearly_data1.update({"Capital Expenditure": capital_expenditure_list,
                                      "Property Management Fees": management_fee_list, "Vacancy": vacancy_list})
        expenses_yearly_data1.update(other_expenses_dict)

        # Yearly Return On Investment
        yearly_return_data = {
            'Property Appreciation Assumption': appreciation_assumption_list,
            'Return On Investment % (ROI) (Assuming No Appreciation)': roi_p_list,
            'Return On Investment (ROI) (Assuming No Appreciation)': roi_list,
            'Return On Investment % (ROI) (With Appreciation Assumption)': roi_p_with_appreciation_list,
            'Return On Investment (ROI) (With Appreciation Assumption)': roi_with_appreciation_list,
            'Capitalization Rate (Cap Rate)': cap_rate_list,
            'Capitalization Rate (Including all closing costs)': cap_rate_include_closing_cost_list,
        }

        # Stats and Graphs Data :-

        cash_on_cash_return_data = [{'name': 'Cash on Cash Return(%)', 'data': cash_return_list}]
        return_on_investment_data = [
            {'name': 'Return On Investment % (ROI) (Assuming No Appreciation)', 'data': roi_p_list},
            {'name': 'Return On Investment % (ROI) (With Appreciation Assumption)',
             'data': roi_p_with_appreciation_list}]

        change_annual_cash_flow_list = [float(x[1:]) for x in annual_cash_flow_list]
        change_appreciation_assumption_list = [float(x[1:]) for x in appreciation_assumption_list]
        change_mortgage_principle_list = [float(x) for x in mortgage_principle_list]

        debt_cov_ratio_data = [{'name': 'Debt Service Coverage Ratio (%)', 'data': debt_cov_ratio_list}]
        return_investment_data = [{'name': 'Annual Cashflow', 'data': change_annual_cash_flow_list},
                                  {'name': 'Net Operating Income(NOI)',
                                   'data': [x[1:] for x in net_operating_income_list]},
                                  {'name': 'Return On Investment (ROI) (Assuming No Appreciation)',
                                   'data': [x[1:] for x in roi_list]},
                                  {'name': 'Return On Investment (ROI) (With Appreciation Assumption)',
                                   'data': [x[1:] for x in roi_with_appreciation_list]
                                   }]
        property_expense_data = [{'name': 'Operating Expenses', 'data': [x[1:] for x in operating_expenses_list]}]

        stats_graph_dict = {'cash_on_cash_return_data': cash_on_cash_return_data,
                            'return_on_investment_data': return_on_investment_data,
                            'debt_cov_ratio_data': debt_cov_ratio_data,
                            'return_investment_data': return_investment_data,
                            'property_expense_data': property_expense_data}

        total_year_return = sum(change_annual_cash_flow_list) + sum(change_appreciation_assumption_list) + \
                            sum(change_mortgage_principle_list)

        for key, value in investors_dict.items():
            update_value = float(value[1].replace("%", ""))
            total_year_return_dict_investors[key] = [value[1],
                                                     f"{currency_name}{round(update_value * total_year_return, 2)}"]

        expenses_yearly_data_dumbs = {}
        expenses_yearly_data_dumbs.update(expenses_yearly_data1)
        expenses_yearly_data_dumbs.update(expenses_yearly_data2)

        context = {
            'primary_key': pk,
            'investment_data': investment_data, 'property_obj': property_obj, 'projection_key': projection_key,
            'projection_value': projection_value, "revenue_yearly_data": revenue_yearly_data,
            "expenses_yearly_data1": expenses_yearly_data1, "expenses_yearly_data2": expenses_yearly_data2,
            "yearly_return_data": yearly_return_data, 'data': data, 'monthly_payment': monthly_payment,
            'last_month': last_month, 'days': total_month, 'total_payment': total_payment, 'mortgage_key': mortgage_key,
            'mortgage_key_dumbs': json.dumps(mortgage_key), 'mortgage_graph_data': mortgage_graph_data,
            'mortgage_date_data': mortgage_date_data, "total_year_return": round(total_year_return, 2),
            "annual_cash_flow_dict_investors": annual_cash_flow_dict_investors,
            "net_operating_income_dict_investors": net_operating_income_dict_investors,
            "roi_dict_investors": roi_dict_investors,
            "roi_with_appreciation_dict_investors": roi_with_appreciation_dict_investors,
            "investors_dict": investors_dict, "total_investor_contributions": total_investor_contributions,
            "excess_short_fall": excess_short_fall, "debt_financing": debt_financing,
            "total_financing": total_financing, "capex_budget_value": capex_budget_value,
            "total_replacement_costs": total_replacement_costs,
            "total_return_investor_dict": total_year_return_dict_investors,
            'investment_data_dumbs': json.dumps(investment_data),
            "projection_value_dumbs": json.dumps(projection_value),
            "annual_cash_flow_dict_investors_dumbs": json.dumps(annual_cash_flow_dict_investors),
            "net_operating_income_dict_investors_dumbs": json.dumps(net_operating_income_dict_investors),
            "total_return_investor_dict_dumbs": json.dumps(total_year_return_dict_investors),
            "roi_dict_investors_dumbs": json.dumps(roi_dict_investors),
            "roi_with_appreciation_dict_investors_dumbs": json.dumps(roi_with_appreciation_dict_investors),
            "cash_on_cash_return_data_dumbs": json.dumps(stats_graph_dict['cash_on_cash_return_data'][0]['data']),
            "return_on_investment_data_dumbs": json.dumps(return_on_investment_data),
            "debt_cov_ratio_data_dumbs": json.dumps(stats_graph_dict['debt_cov_ratio_data'][0]['data']),
            "return_investment_data_dumbs": json.dumps(stats_graph_dict['return_investment_data']),
            "property_expense_data_dumbs": json.dumps(stats_graph_dict['property_expense_data'][0]['data']),
            "revenue_yearly_data_dumbs": json.dumps(revenue_yearly_data),
            "expenses_yearly_data_dumbs": json.dumps(expenses_yearly_data_dumbs),
            "yearly_return_data_dumbs": json.dumps(yearly_return_data)

        }
        context.update(stats_graph_dict)

        return render(request, "properties/property_detail.html", context=context)
    except Exception as err:
        return render(request, "error.html", context={'error': 'Something Went Wrong'})


def others_costs_data(other_closing_cost):
    cost_dict = dict.fromkeys(other_closing_cost[::2], 0)
    cost_index = 1
    for key in cost_dict:
        cost_dict[key] = check_float(other_closing_cost[cost_index])
        cost_index += 2

    return cost_dict


@login_required(login_url="/login")
def rental_property_add(request):
    if request.method == 'POST':
        print("method called")
        try:
            property_image = request.FILES['file']
        except:
            property_image = ""
        print(request.POST)
        property_name = request.POST['name_address'].title()
        currency_name = request.POST['currency_name']
        user_name = request.user
        property_obj = RentalPropertyModel.objects.filter(user=user_name, name=property_name)
        if property_obj:
            context = {'currency_dict': currency_dict, 'error': 'Property Already Exits'}
            return render(request, "properties/add_property.html", context=context)

        rental_obj = RentalPropertyModel()
        property_purchase_obj = PropertyPurchaseDetails()
        mortgage_obj = MortgageDetails()
        closing_cost_obj = ClosingCostDetails()
        revenue_obj = RevenuesDetails()
        expense_obj = ExpensesDetails()
        capex_budget_obj = CapexBudgetDetails()
        save_rental_property(request, rental_obj, property_purchase_obj, mortgage_obj, closing_cost_obj, revenue_obj,
                             expense_obj, capex_budget_obj, property_name, currency_name, user_name, property_image)
        return redirect("/rental_property_list/")

    else:
        upcoming_date = today_date + relativedelta(months=1, day=1)
        property_obj = {'mortgage_detail': {'start_date': str(upcoming_date), 'amortization_year': 25}}
        context = {
            'currency_dict': currency_dict,
            'scenario_dict': scenario_dict,
            'action_url': "/rental_property_add/",
            'heading_name': "Add Rental Property",
            'heading_url': "Add Property",
            'property_url': "/rental_property_list/",
            'property_obj': property_obj

        }
        return render(request, "properties/add_property.html", context=context)


@login_required(login_url="/login")
def rental_property_update(request, pk):
    user_name = request.user
    if request.method == "POST":
        rental_obj = RentalPropertyModel.objects.get(pk=pk)
        property_purchase_obj = rental_obj.purchase_price_detail
        mortgage_obj = rental_obj.mortgage_detail
        closing_cost_obj = rental_obj.closing_cost_detail
        revenue_obj = rental_obj.monthly_revenue
        expense_obj = rental_obj.monthly_expenses
        capex_budget_obj = rental_obj.capex_budget_details
        property_image = request.FILES['property_image']
        property_name = request.POST['name_address'].title()
        currency_name = request.POST['currency_name']
        user_name = request.user
        if rental_obj.name != property_name:
            property_obj = RentalPropertyModel.objects.filter(user=user_name, name=property_name)
            if property_obj:
                context = {'currency_dict': currency_dict, 'error': 'Property Already Exits'}
                return render(request, "properties/add_property.html", context=context)

        save_rental_property(request, rental_obj, property_purchase_obj, mortgage_obj, closing_cost_obj, revenue_obj,
                             expense_obj, capex_budget_obj, property_name, currency_name, user_name, property_image)
        return redirect(f"rental_property_detail/{pk}")

    else:
        property_obj = RentalPropertyModel.objects.get(pk=pk)
        roof_obj = ast.literal_eval(property_obj.capex_budget_details.roof)
        water_heater = ast.literal_eval(property_obj.capex_budget_details.water_heater)
        all_appliances = ast.literal_eval(property_obj.capex_budget_details.all_appliances)
        bathroom_fixtures = ast.literal_eval(property_obj.capex_budget_details.bathroom_fixtures)
        drive_way = ast.literal_eval(property_obj.capex_budget_details.drive_way)
        furnance = ast.literal_eval(property_obj.capex_budget_details.furnance)
        air_conditioner = ast.literal_eval(property_obj.capex_budget_details.air_conditioner)
        flooring = ast.literal_eval(property_obj.capex_budget_details.flooring)
        plumbing = ast.literal_eval(property_obj.capex_budget_details.plumbing)
        electrical = ast.literal_eval(property_obj.capex_budget_details.electrical)
        windows = ast.literal_eval(property_obj.capex_budget_details.windows)
        paint = ast.literal_eval(property_obj.capex_budget_details.paint)
        kitchen = ast.literal_eval(property_obj.capex_budget_details.kitchen)
        structure = ast.literal_eval(property_obj.capex_budget_details.structure)
        components = ast.literal_eval(property_obj.capex_budget_details.components)
        landscaping = ast.literal_eval(property_obj.capex_budget_details.landscaping)
        others_cost = ast.literal_eval(property_obj.closing_cost_detail.others_cost)[0]
        others_revenue_cost = ast.literal_eval(property_obj.monthly_revenue.others_revenue_cost)[0]
        other_utilities = ast.literal_eval(property_obj.monthly_expenses.other_utilities)[0]
        other_expenses = ast.literal_eval(property_obj.monthly_expenses.other_expenses)[0]
        investor_details = ast.literal_eval(property_obj.investor_details)[0]

        context = {'currency_dict': currency_dict, 'scenario_dict': scenario_dict, 'property_obj': property_obj,
                   'roof_obj': roof_obj, 'water_heater': water_heater, 'all_appliances': all_appliances,
                   'bathroom_fixtures': bathroom_fixtures, 'drive_way': drive_way, 'furnance': furnance,
                   'air_conditioner': air_conditioner, 'flooring': flooring, 'plumbing': plumbing,
                   'electrical': electrical, 'windows': windows, 'paint': paint, 'kitchen': kitchen,
                   'structure': structure, 'components': components, 'landscaping': landscaping,
                   "others_cost": others_cost, "others_cost_len": len(others_cost),
                   "others_revenue_cost": others_revenue_cost, "others_revenue_cost_len": len(others_revenue_cost),
                   "other_utilities": other_utilities, "other_utilities_len": len(other_utilities),
                   "other_expenses": other_expenses, "other_expenses_len": len(other_expenses),
                   "investor_details": investor_details, "investor_details_len": len(investor_details),
                   'action_url': f"/rental_property_update/{pk}",
                   'heading_name': "Update Rental Property",
                   'heading_url': "Update Property",
                   'property_url': f"/rental_property_detail/{pk}",
                   }

        return render(request, "properties/add_property.html", context=context)


@login_required(login_url="/login")
def rental_property_delete(request, pk):
    property_obj = RentalPropertyModel.objects.get(pk=pk)
    purchase_price_obj = property_obj.purchase_price_detail
    mortgage_detail_obj = property_obj.mortgage_detail
    closing_cost_obj = property_obj.closing_cost_detail
    monthly_revenue_obj = property_obj.monthly_revenue
    monthly_expenses_obj = property_obj.monthly_expenses
    capex_budget_details_obj = property_obj.capex_budget_details
    purchase_price_obj.delete()
    mortgage_detail_obj.delete()
    closing_cost_obj.delete()
    monthly_revenue_obj.delete()
    monthly_expenses_obj.delete()
    capex_budget_details_obj.delete()

    return JsonResponse({"status": "Successfully", "path": "/rental_property_list/"})


class RentalPdf:
    def __init__(self, buffer, pageSize):
        self.buffer = buffer
        # default format is A4
        if pageSize == 'A4':
            self.pageSize = A0
        elif pageSize == 'Letter':
            self.pageSize = letter
        self.width, self.height = self.pageSize

    def report(self, pdf_data_value, title, property_address, property_image, d=None):
        doc = SimpleDocTemplate(self.buffer, pagesize=self.pageSize)
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        title_style.alignment = TA_CENTER
        title_style.fontSize = 50
        if property_image == "None":
            data = [Spacer(50, 50), Paragraph(f"RENTAL PROPERTY INVESTMENT PROPOSAL", title_style), Spacer(100, 100),
                    Paragraph(f"Address {property_address}", title_style), Spacer(300, 300)]
        else:
            data = [Spacer(50, 50), Paragraph(f"RENTAL PROPERTY INVESTMENT PROPOSAL", title_style), Spacer(100, 100),
                    Paragraph(f"Address {property_address}", title_style), Spacer(100, 100),
                    Image(property_image, 25 * inch, 15 * inch), Spacer(200, 200)]
        for key, values in pdf_data_value.items():
            t = Table(values)
            t.setStyle(TableStyle(
                [('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
                 ('BOX', (0, 0), (-1, -1), 0.5, colors.black),
                 ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                 ('BACKGROUND', (0, 0), (-1, 0), colors.powderblue), ('FONTSIZE', (0, 0), (-1, -1), title)]))
            # create other flowables
            p = Paragraph(key, styles['Title'])
            data.append(p)
            data.append(t)
            data.append(Spacer(150, 150))
        if d:
            data.append(Paragraph(f"INVESTMENT SUMMARY GRAPHS AND STATISTICS", title_style))
            for bar_key, bar_d in d.items():
                data.append(Spacer(150, 150))
                # if bar_key == "Cash on Cash Return (%)" or bar_key == "Investment Returns":
                #     data.append(Spacer(200, 200))
                data.append(Paragraph(bar_key, styles['Title']))
                data.append(Spacer(50, 50))

                data.append(bar_d)

        doc.build(data)
        pdf = self.buffer.getvalue()
        self.buffer.close()
        return pdf


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
             ('BACKGROUND', (0, 0), (-1, 0), colors.powderblue)]))
        # create other flowables

        data.append(t)
        # d.save(formats=['pdf'], outDir='.', fnRoot='test')
        if d:
            data.append(d)
        doc.build(data)
        pdf = self.buffer.getvalue()
        self.buffer.close()
        return pdf


def draw_bar_chart(bar_data, data_label, graph_type, bar_legends=None):
    d = Drawing(400, 500)
    bar = VerticalBarChart()
    bar.width = 400
    bar.height = 400
    bar.data = bar_data
    bar.valueAxis.valueMin = 0
    bar.barSpacing = 0.5
    bar.categoryAxis.labels.dx = 8
    bar.categoryAxis.labels.dy = -2
    bar.categoryAxis.categoryNames = data_label
    bar.barLabels.nudge = 7
    bar.valueAxis.labels.fontName = 'Helvetica'
    bar.valueAxis.labels.fontSize = 10
    bar.valueAxis.forceZero = 1
    bar.valueAxis.rangeRound = 'both'
    bar.valueAxis.valueMax = None  # 10#
    bar.categoryAxis.visible = 1
    bar.categoryAxis.visibleTicks = 0
    bar.barLabels.fontSize = 10
    bar.valueAxis.labels.fontSize = 10
    bar.strokeWidth = 0.1
    bar.bars.strokeWidth = 0.5

    if graph_type == "bar":
        bar.bars[0].fillColor = PCMYKColor(46, 51, 0, 4)
        bar.bars[1].fillColor = colors.red
        bar.bars[2].fillColor = colors.darkgreen
        bar.bars[3].fillColor = colors.yellow

        d.add(bar)
    else:
        legend = Legend()
        legend.columnMaximum = 10
        legend.fontName = 'Helvetica'
        legend.fontSize = 14
        legend.boxAnchor = 'w'
        legend.x = 200
        legend.y = 600
        legend.dx = 16
        legend.dy = 16
        legend.alignment = 'left'
        print("bar_legends===>", bar_legends)
        legend.colorNamePairs = bar_legends
        bar.bars[0].fillColor = colors.red
        bar.bars[1].fillColor = colors.darkgreen
        d.add(bar)
        d.add(legend)

    return d


def make_return_data(result_dict, result_value):
    for key, val in result_dict.items():
        result_list = [key]
        for value in val[:5]:
            result_list.append(value)
        result_value.append(result_list)
    return result_value


@login_required(login_url="/login")
@csrf_exempt
def download_rental_pdf(request):
    property_address = request.POST['property_name']
    property_image = request.POST['property_image']
    scheme = request.scheme
    if property_image != "None":
        property_image = f"{scheme}://{request.META['HTTP_HOST']}{property_image}"
    invest_summary_data = request.POST['invest_summary_data']
    yearly_projection_data = request.POST['yearly_projection_data']
    annual_cashflow_data = request.POST['annual_cashflow_data']
    roi_with_appreciation_dict_investors_data = request.POST['roi_with_appreciation_dict_investors_data']
    roi_dict_investors_data = request.POST['roi_dict_investors_data']
    total_return_investor_data = request.POST['total_return_investor_data']
    net_operating_income_data = request.POST['net_operating_income_data']
    cash_on_cash_return_data = request.POST['cash_on_cash_return_data']
    return_on_investment_data = request.POST['return_on_investment_data']
    debt_cov_ratio_data = request.POST['debt_cov_ratio_data']
    property_expense_data = request.POST['property_expense_data']
    return_investment_data = request.POST['return_investment_data']
    revenue_yearly_data = request.POST['revenue_yearly_data']
    expenses_yearly_data = request.POST['expenses_yearly_data']
    yearly_return_data = request.POST['yearly_return_data']

    invest_summary_data = json.loads(invest_summary_data)
    yearly_projection_data = json.loads(yearly_projection_data)
    annual_cashflow_data = json.loads(annual_cashflow_data)
    roi_with_appreciation_dict_investors_data = json.loads(roi_with_appreciation_dict_investors_data)
    roi_dict_investors_data = json.loads(roi_dict_investors_data)
    total_return_investor_data = json.loads(total_return_investor_data)
    net_operating_income_data = json.loads(net_operating_income_data)
    cash_on_cash_return_data = json.loads(cash_on_cash_return_data)
    return_on_investment_data = json.loads(return_on_investment_data)
    debt_cov_ratio_data = json.loads(debt_cov_ratio_data)
    property_expense_data = json.loads(property_expense_data)
    return_investment_data = json.loads(return_investment_data)
    revenue_yearly_data = json.loads(revenue_yearly_data)
    expenses_yearly_data = json.loads(expenses_yearly_data)
    yearly_return_data = json.loads(yearly_return_data)
    property_expense_data = [float(i) for i in property_expense_data]
    file_name = f"{property_address}_Rental_Property.pdf"
    investment_data_values = []
    yearly_projection_data_values = []
    annual_cashflow_data_values = []
    cash_on_cash_return_data_values = []
    revenue_yearly_data_values = []
    expenses_yearly_data_values = []
    yearly_return_data_values = []
    yearly_keys = []
    return_on_investment_data_list1 = []
    return_on_investment_data_list2 = []
    return_investment_data_list = return_investment_data[0]['data']
    return_investment_data_list1 = []
    return_investment_data_list2 = []
    return_investment_data_list3 = []

    year_index = 1
    for key, val in invest_summary_data.items():
        investment_data_values.append([key, val])

    for key, val in revenue_yearly_data.items():
        result_list = [key]
        for value in val:
            result_list.append(value)
        revenue_yearly_data_values.append(result_list)

    for key, val in expenses_yearly_data.items():
        result_list = [key]
        for value in val:
            result_list.append(value)
        expenses_yearly_data_values.append(result_list)

    for key, val in yearly_return_data.items():
        result_list = [key]
        for value in val:
            result_list.append(value)
        yearly_return_data_values.append(result_list)

    for key, val in yearly_projection_data.items():
        result_list = [key]
        for value in val:
            result_list.append(value)
            if year_index == 1:
                yearly_keys.append(f"Year {len(yearly_keys) + 1}")

        year_index = 2
        yearly_projection_data_values.append(result_list)

    return_dict = {"Annual Cashflow ": annual_cashflow_data, "Net Operating Income (NOI)": net_operating_income_data,
                   "Return on Investment (ROI) ($) (Assuming NO Appreciation)": roi_dict_investors_data,
                   "Return on Investment(ROI) ($) (WITH appreciation assumption)": roi_with_appreciation_dict_investors_data,
                   f"Total {len(yearly_keys)} Year Return with Appreciation Assumption": total_return_investor_data}

    for k, v in return_dict.items():
        annual_cashflow_data_values.append([k])
        if k == f"Total {len(yearly_keys)} Year Return with Appreciation Assumption":
            for key, val in v.items():
                result_list = [key]
                for i in range(len(yearly_keys)):
                    if i == 0:
                        result_list.append(val[i].replace("%", ""))

                    elif i == len(yearly_keys) - 1:
                        result_list.append("")
                        result_list.append(val[-1])
                    else:
                        result_list.append("")
                annual_cashflow_data_values.append(result_list)
        else:
            for key, val in v.items():
                result_list = [key]
                for value in val:
                    result_list.append(value)
                annual_cashflow_data_values.append(result_list)

    for name in cash_on_cash_return_data:
        cash_on_cash_return_data_values.append(float(name.replace("%", "")))

    for name in return_on_investment_data[0]['data']:
        return_on_investment_data_list1.append(float(name.replace("%", "")))

    for name in return_on_investment_data[1]['data']:
        return_on_investment_data_list2.append(float(name.replace("%", "")))

    for name in return_investment_data[1]['data']:
        return_investment_data_list1.append(float(name.replace("%", "")))

    for name in return_investment_data[2]['data']:
        return_investment_data_list2.append(float(name.replace("%", "")))

    for name in return_investment_data[3]['data']:
        return_investment_data_list3.append(float(name.replace("%", "")))

    bar_label = yearly_keys.copy()
    cash_flow_keys = yearly_keys.copy()
    cash_flow_keys.insert(0, "INVESTOR OWNERSHIP %")
    cash_flow_keys.insert(0, "RETURN METRIC/INVESTOR")
    annual_cashflow_data_values.insert(0, cash_flow_keys)
    yearly_keys.insert(0, " ")
    yearly_projection_data_values.insert(0, yearly_keys)
    revenue_yearly_data_values.insert(0, yearly_keys)
    expenses_yearly_data_values.insert(0, yearly_keys)
    yearly_return_data_values.insert(0, yearly_keys)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename={file_name}'
    buffer = BytesIO()
    reporti = RentalPdf(buffer, 'A4')
    bar_legends = [(PCMYKColor(46, 51, 0, 4), return_on_investment_data[0]['name']),
                   (colors.red, return_on_investment_data[1]['name'])]
    return_bar_legends = [(PCMYKColor(46, 51, 0, 4), return_investment_data[0]['name']),
                          (colors.red, return_investment_data[1]['name']),
                          (colors.darkgreen, return_investment_data[2]['name']),
                          (colors.yellow, return_investment_data[3]['name']),
                          ]
    cash_on_cash_bar_chart = draw_bar_chart([cash_on_cash_return_data_values], bar_label, "bar")
    debt_cov_ratio_bar_chart = draw_bar_chart([debt_cov_ratio_data], bar_label, "bar")
    property_expense_data_bar_chart = draw_bar_chart([property_expense_data], bar_label, "bar")
    return_on_investment_chart = draw_bar_chart([return_on_investment_data_list1, return_on_investment_data_list2],
                                                bar_label, "return-bar", bar_legends)
    return_investment_chart = draw_bar_chart([return_investment_data_list, return_investment_data_list1,
                                              return_investment_data_list2, return_investment_data_list3],
                                             bar_label, "return-bar", return_bar_legends)

    d = {'Cash on Cash Return (%)': cash_on_cash_bar_chart, 'Return on Investment': return_on_investment_chart,
         'Debt Service Coverage Ratio': debt_cov_ratio_bar_chart, 'Investment Returns': return_investment_chart,
         'Property Operating Expenses': property_expense_data_bar_chart}

    pdf_title = 14

    if len(yearly_keys) > 45:
        pdf_title = 6
    else:
        if len(yearly_keys) >= 35:
            pdf_title = 7
        if len(yearly_keys) >= 25:
            pdf_title = 10

    pdf = reporti.report({'INVESTMENT SUMMARY': investment_data_values,
                          'YEARLY PROJECTION': yearly_projection_data_values,
                          'INVESTOR RETURNS SUMMARY': annual_cashflow_data_values,
                          'REVENUE': revenue_yearly_data_values, 'PROPERTY EXPENSES': expenses_yearly_data_values,
                          'INVESTMENT METRICS': yearly_return_data_values}, pdf_title, property_address,
                         property_image, d)
    response.write(pdf)
    return response


@login_required(login_url="/login")
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
        print("pdf_data_value--------->", pdf_data_value)
        try:
            graph_type = request.POST['graph_type']
            print("graph_type=======>", graph_type)
            data_label = request.POST['data_label']
            data_value = request.POST['data_value']
            data_label = json.loads(data_label)
            data_value = json.loads(data_value)
            print("graph_data_labels====>", data_label)
            print("graph_data_values====>", data_value)

            if graph_type == 'transaction-bar':
                credit_value = request.POST['credit_value']
                debit_value = data_value
                credit_value = json.loads(credit_value)
                bar_data = [debit_value, credit_value]
                print("colors.red========>", colors.red)
                print("colors.green========>", colors.green)

                bar_legends = [(colors.red, "Debit"), (colors.green, "Credit")]
                d = draw_bar_chart(bar_data, data_label, graph_type, bar_legends)

            if graph_type == 'bar':
                print("barr")
                bar_data = [data_value]
                d = draw_bar_chart(bar_data, data_label, graph_type)
                print(d)
            if graph_type == 'line':
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

            if graph_type == 'pie':
                d = Drawing(400, 500)
                pie = Pie()
                pie.x = 200
                pie.y = 65
                pie.width = 200
                pie.height = 300
                pie.data = data_value
                pie.labels = data_label
                pie.slices.strokeWidth = 0.5
                pie.slices[0].fillColor = colors.yellow
                pie.slices[1].fillColor = colors.red
                pie.slices[2].fillColor = PCMYKColor(46, 51, 0, 4)
                pie.slices[3].fillColor = colors.darkgreen
                d.add(pie)

            pdf = reporti.report(pdf_data_value, pdf_title, d)
        except:
            pdf = reporti.report(pdf_data_value, pdf_title)

        response.write(pdf)
        return response
    return render(request, "test.html")


# Download CSV file

@login_required(login_url="/login")
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


@login_required(login_url="/login")
def transaction_upload(request):
    if request.method == "POST" and request.is_ajax:
        try:
            test_file = request.FILES['csv_file']
            df = pd.read_csv(test_file)
            for index, row in df.iterrows():
                my_transaction = Transaction()
                user_name = request.user
                my_transaction.user = user_name
                category_name = row['Categories']
                if type(category_name) == float:
                    return JsonResponse({'status': 'Category is mandatory field'})
                category_obj = Category.objects.filter(user=user_name, name=category_name)
                if not category_obj:
                    category_obj = Category()
                    category_obj.user = user_name
                    category_obj.name = category_name
                    category_obj.save()
                else:
                    category_obj = category_obj[0]
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
                    try:
                        account_obj = Account.objects.get(user=user_name, name=account)
                    except:
                        return JsonResponse({'status': account + ' Account not Found!!'})
                    if type(bill_name) != float:
                        bill_obj = Bill.objects.filter(user=user_name, label=bill_name)
                        if not bill_obj:
                            return JsonResponse({'status': bill_name + ' Bill Not Found!!'})
                        else:
                            bill_obj = bill_obj[0]
                    else:
                        bill_obj = False

                    if type(budget_name) != float:
                        budget_obj = Budget.objects.filter(user=user_name, name=budget_name)
                        if not budget_obj:
                            return JsonResponse({'status': budget_name + ' Budget Not Found!!'})
                        else:
                            budget_obj = budget_obj[0]
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
                            bill_obj.remaining_amount = bill_amount - transaction_amount
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
    url = f"{stock_app_url}/api/portfolio/list/"
    portfolio_response = requests.get(url, data={'user_name': request.user.username}, timeout=500)
    portfolio_list = portfolio_response.json()

    if request.method == 'POST':
        p_name = request.POST['p_name']
    else:
        p_name = portfolio_list[0]

    my_portfolio_url = f"{stock_app_url}/api/my_portfolio/list/"
    url_response = requests.post(my_portfolio_url, data={'user_name': request.user.username, 'p_name': p_name},
                                 timeout=500)
    my_portfolio_context = url_response.json()
    my_portfolio_context['portfolio_list'] = portfolio_list
    return render(request, 'stock_analysis.html', context=my_portfolio_context)


@login_required(login_url="/login")
def stock_holdings(request):
    url = f"{stock_app_url}/api/portfolio/list/"
    print("url========>", url)
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0'}
    portfolio_response = requests.get(url, headers=headers, data={'user_name': request.user.username}, timeout=500)
    portfolio_dict = portfolio_response.json()
    if request.method == 'POST':
        my_portfolio_name = request.POST['portfolio_name']
    else:
        my_portfolio_name = portfolio_dict['portfolio_list'][0]
    my_portfolio_url = f"{stock_app_url}/api/my_portfolio/list/"
    print("url========>", my_portfolio_url)
    url_response = requests.post(my_portfolio_url, headers=headers,
                                 data={'user_name': request.user.username, 'p_name': my_portfolio_name},
                                 timeout=500)
    my_portfolio_context = url_response.json()
    portfolio_dict.update({"my_portfolio_name": my_portfolio_name})
    portfolio_dict.update(my_portfolio_context)
    check_networth = StockHoldings.objects.filter(user=request.user, port_id=portfolio_dict['portfolio_id'])
    portfolio_dict.update({'check_networth': check_networth})
    print(portfolio_dict)
    return render(request, 'stock_analysis.html', context=portfolio_dict)


@login_required(login_url="/login")
def add_port_in_networth(request):
    try:
        if request.method == 'POST' and request.is_ajax():
            portfolio_id = int(request.POST['portfolio_id'])
            portfolio_name = request.POST['portfolio_name']
            portfolio_value = request.POST['portfolio_value']
            portfolio_currency = request.POST['portfolio_currency']
            method_name = request.POST['method_name']
            portfolio_curr = {'USD': "$", 'EUR': '€', 'INR': '₹', 'GBP': '£'}
            if method_name == "delete_port":
                StockHoldings.objects.get(user=request.user, port_id=portfolio_id).delete()
                return JsonResponse({'status': 'delete'})
            else:
                end_date = today_date + datetime.timedelta(hours=2)
                StockHoldings.objects.create(user=request.user, port_id=portfolio_id, name=portfolio_name,
                                             value=portfolio_value, end_at=end_date,
                                             currency=portfolio_curr[portfolio_currency])
                return JsonResponse({'status': 'true'})
    except:
        return JsonResponse({'status': 'false'})


# Income views
@login_required(login_url="/login")
def income_add(request):
    error = False
    user = request.user
    if request.method == 'POST':
        sub_category_name = request.POST['sub_category_name'].title()
        account_name = request.POST['account_name']
        income_amount = request.POST['amount']
        income_date = request.POST['income_date']
        frequency = request.POST['frequency']
        auto_income = request.POST.get('auto_income', False)
        auto_credit = request.POST.get('auto_credit', False)
        if auto_income:
            auto_income = True
        if auto_credit:
            auto_credit = True

        subcategory_qs = SubCategory.objects.filter(category__user=user, category__name='Income',
                                                    name=sub_category_name)
        if not subcategory_qs:
            sub_category = SubCategory.objects.create(category=Category.objects.get(user=user, name='Income'),
                                                      name=sub_category_name)
        else:
            sub_category = subcategory_qs[0]

        income_qs = Income.objects.filter(user=user, sub_category=sub_category)
        if income_qs:
            if income_qs[0].auto_bill:
                error = 'Income Already Exit!!'
            else:
                pass
        else:
            account = Account.objects.get(user=user, name=account_name)
            created_date = datetime.datetime.strptime(income_date, '%Y-%m-%d')
            save_income(user, sub_category, account, income_amount, income_date, auto_income, frequency, auto_credit,
                        created_date, "True")
            if not auto_income:
                income = Income.objects.get(user=user, sub_category=sub_category)
                income_detail_obj = save_income_details(account, income_amount, income, False, income_date)
                if auto_credit:
                    account_balance = float(account.available_balance)
                    remaining_amount = round(account_balance + income_amount, 2)
                    tag_obj, tag_created = Tag.objects.get_or_create(user=income.user, name="Incomes")
                    save_transaction(income.user, sub_category.name, income_amount, remaining_amount, income_date,
                                     sub_category,
                                     account,
                                     tag_obj, False, True)
                    account.available_balance = remaining_amount
                    account.transaction_count += 1
                    account.save()
                    income_detail_obj.credited = True
                    income_detail_obj.save()
            create_income_request()
            return redirect('/income_list/')
    income_category = SubCategory.objects.filter(category__name="Income", category__user=user)
    account_qs = Account.objects.filter(user=user, account_type__in=['Checking', 'Savings', 'Cash', 'Credit Card',
                                                                     'Line of Credit'])
    frequency = ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly']
    context = {
        'error': error,
        'account_qs': account_qs,
        'income_category': income_category,
        'frequency': frequency
    }
    return render(request, "income/income_add.html", context=context)


@login_required(login_url="/login")
def income_update(request, pk):
    error = False
    user = request.user
    income_obj = Income.objects.get(pk=pk)
    if request.method == 'POST':
        sub_category_name = request.POST['sub_category_name'].title()
        account_name = request.POST['account_name']
        income_amount = request.POST['amount']
        income_date = request.POST['income_date']
        frequency = request.POST['frequency']
        auto_income = request.POST.get('auto_income', False)
        auto_credit = request.POST.get('auto_credit', False)
        if auto_income:
            auto_income = True
        if auto_credit:
            auto_credit = True
        account = Account.objects.get(user=user, name=account_name)
        income_obj.account = account
        income_obj.income_amount = income_amount
        income_obj.income_date = income_date
        income_obj.auto_income = auto_income
        income_obj.frequency = frequency
        income_obj.auto_credit = auto_credit

        if income_obj.sub_category.name != sub_category_name:
            subcategory_qs = SubCategory.objects.filter(category__user=user, category__name='Income',
                                                        name=sub_category_name)
            if not subcategory_qs:
                sub_category = SubCategory.objects.create(category=Category.objects.get(user=user, name='Income'),
                                                          name=sub_category_name)
            else:
                sub_category = subcategory_qs[0]
            income_qs = Income.objects.filter(user=user, sub_category=sub_category)
            if income_qs:
                error = 'Income Already Exit!!'
            else:
                Transaction.objects.filter(user=request.user, categories=income_obj.sub_category).update(
                    categories=sub_category)
                income_obj.sub_category = sub_category
                income_obj.save()
                return redirect(f"/income_details/{pk}")
        else:
            income_obj.save()
            return redirect(f"/income_details/{pk}")

    income_category = SubCategory.objects.filter(category__name="Income", category__user=user)
    account_qs = Account.objects.filter(user=user, account_type__in=['Checking', 'Savings', 'Cash', 'Credit Card',
                                                                     'Line of Credit'])
    frequency = ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly']
    context = {
        'error': error,
        'account_qs': account_qs,
        'income_category': income_category,
        'frequency': frequency,
        'income_data': income_obj,
        'income_date': income_obj.income_date.strftime('%Y-%m-%d'),
    }
    return render(request, "income/income_update.html", context=context)


@login_required(login_url="/login")
def income_list(request):
    income_data = Income.objects.filter(user=request.user)
    context = {'income_data': income_data}
    return render(request, "income/income_list.html", context=context)


def income_details(request, pk):
    income_obj = Income.objects.get(pk=pk)
    income_qs = IncomeDetail.objects.filter(income=income_obj).order_by('-income_date')
    transaction_data = Transaction.objects.filter(user=request.user, categories=income_obj.sub_category).order_by(
        '-transaction_date')
    context = {'income_data': income_obj, 'income_list': income_qs, 'transaction_data': transaction_data}
    return render(request, "income/income_details.html", context=context)


@login_required(login_url="/login")
def income_delete(request, pk):
    income_obj = Income.objects.get(pk=pk)
    user_name = request.user
    transaction_details = Transaction.objects.filter(user=user_name, categories=income_obj.sub_category)
    for data in transaction_details:
        delete_transaction_details(data.pk, user_name)
    income_obj.delete()
    return JsonResponse({"status": "Successfully", "path": "/income_list/"})


def income_edit(request, pk):
    income_obj = IncomeDetail.objects.get(pk=pk)
    if request.method == 'POST':
        new_amount = round(float(request.POST['amount']), 2)
        income_date = request.POST['income_date']
        credited = request.POST.get('credited', False)
        old_amount = float(income_obj.income_amount)
        account = income_obj.income.account
        if credited:
            credited = True
        income_obj.income_date = income_date
        if income_obj.credited is True and credited is True:
            if old_amount > new_amount:
                remaining_amount = old_amount - new_amount
                account.available_balance = round(float(account.available_balance) - remaining_amount, 2)
            if old_amount < new_amount:
                remaining_amount = new_amount - old_amount
                account.available_balance = round(float(account.available_balance) + remaining_amount, 2)
            Transaction.objects.filter(user=income_obj.income.user, transaction_date=income_obj.income_date,
                                       categories=income_obj.income.sub_category).update(amount=new_amount,
                                                                                         transaction_date=income_date)
            account.save()

        if income_obj.credited is True and credited is False:
            account.available_balance = round(float(account.available_balance) - old_amount, 2)
            account.save()
            Transaction.objects.filter(user=income_obj.income.user, transaction_date=income_obj.income_date,
                                       categories=income_obj.income.sub_category).delete()
            account.transaction_count -= 1

        if income_obj.credited is False and credited is True:
            account.available_balance = round(float(account.available_balance) + new_amount, 2)
            tag_obj, tag_created = Tag.objects.get_or_create(user=income_obj.income.user, name="Incomes")
            save_transaction(income_obj.income.user, income_obj.income.sub_category.name, new_amount,
                             account.available_balance,
                             income_date, income_obj.income.sub_category, account, tag_obj, False, True)
            account.transaction_count += 1
            account.save()
        income_obj.income_amount = new_amount
        income_obj.credited = credited
        income_obj.save()

        return redirect(f"/income_details/{income_obj.income.id}")

    return render(request, "income/income_edit.html",
                  {'income_data': income_obj, 'income_date': income_obj.income_date.strftime('%Y-%m-%d')})


@login_required(login_url="/login")
def income_date_delete(request, pk):
    income_obj = IncomeDetail.objects.get(pk=pk)
    user_name = income_obj.income.user
    if income_obj.credited is True:
        transaction_details = Transaction.objects.filter(user=user_name, transaction_date=income_obj.income_date,
                                                         categories=income_obj.income.sub_category)
        for data in transaction_details:
            delete_transaction_details(data.pk, user_name)
    income_obj.delete()
    return JsonResponse({"status": "Successfully", "path": f"/income_details/{income_obj.income.id}"})


@login_required(login_url="/login")
def income_uncredited_list(request):
    print(request.POST)
    category_id = int(request.POST['category_id'])
    category_obj = Category.objects.get(pk=category_id)
    subcategory_name = request.POST['sub_category'].strip()
    user = request.user
    income_qs = IncomeDetail.objects.filter(income__user=user, income__sub_category__name=subcategory_name,
                                            credited=False)
    uncredited_income_dict = {}
    amount_dict = {}
    for data in income_qs:
        uncredited_income_dict[data.pk] = data.income_date
        amount_dict[data.pk] = data.income_amount

    return JsonResponse(
        {"status": "true", "income_dict": uncredited_income_dict, "amount_dict": json.dumps(amount_dict)})


# EXPENSES ADD
def expense_save(request, user_name, expenses_obj):
    category = request.POST['category']
    name = request.POST['name']
    amount = request.POST['amount']
    month = request.POST['start_month']
    currency = request.POST['currency']
    category_data = Category.objects.get(user=user_name, name=category)
    month = datetime.datetime.strptime(month, '%Y-%m').date()
    if not expenses_obj:
        expenses_obj = Expenses()
    expenses_obj.user = user_name
    expenses_obj.name = name
    expenses_obj.currency = currency
    expenses_obj.categories = category_data
    expenses_obj.amount = amount
    expenses_obj.month = month
    expenses_obj.save()


@login_required(login_url="/login")
def expenses_add(request):
    user_name = request.user
    if request.method == 'POST':
        expense_save(request, user_name, None)
        if 'add_other' in request.POST:
            return redirect("/expenses_add/")
        else:
            return redirect("/budget_list/")
    else:
        category_data = Category.objects.filter(user=user_name)
        current = datetime.datetime.today()
        current_month = datetime.datetime.strftime(current, '%Y-%m')
        context = {'current_month': current_month, 'category_data': category_data}
    return render(request, "expenses/expenses_add.html", context=context)


# EXPENSES UPDATE

@login_required(login_url="/login")
def expenses_update(request, pk):
    user_name = request.user
    expense_obj = Expenses.objects.get(pk=pk)
    print()
    if request.method == 'POST':
        expense_save(request, user_name, expense_obj)
        return redirect("/budget_list/")
    else:
        category_data = Category.objects.filter(user=user_name)
        current_month = datetime.datetime.strftime(expense_obj.month, '%Y-%m')
        context = {'expense_obj': expense_obj, 'category_data': category_data, 'current_month': current_month,
                   'currency_data': currency_dict}
        return render(request, "expenses/expenses_update.html", context=context)


# EXPENSES DELETE

@login_required(login_url="/login")
def expenses_delete(request, pk):
    expense_obj = Expenses.objects.get(pk=pk)
    expense_obj.delete()
    return JsonResponse({"status": "Successfully", "path": "None"})


def add_checkbox_value(result_check, result_dict, result_type, result_name):
    if result_check:
        electric_value = result_check[0]
    else:
        electric_value = 'off'

    result_dict[result_type][result_name] = electric_value


def process_image(request):
    if request.method == 'POST':
        # -------------- Property Details ---------------------- #
        try:
            property_image = request.FILES['property_image']
        except:
            property_image = ""

        property_name = request.POST['property_name']
        address_line1 = request.POST['address_line1']
        address_line2 = request.POST['address_line2']
        postcode = request.POST['postcode']
        city = request.POST['city']
        state = request.POST['state']
        country = request.POST['country']
        property_type = request.POST['property_type']
        unit_name = request.POST.getlist('unit_name')
        bed_room_quantity = request.POST.getlist('bed_room_quantity')
        bath_room_quantity = request.POST.getlist('bath_room_quantity')
        square_feet = request.POST.getlist('square_feet')

        unit_details = []
        for i in range(len(unit_name)):
            unit_dict = {'name': unit_name[i],
                         'details': {'bed_room': bed_room_quantity[i], 'bath_room': bath_room_quantity[i],
                                     'square_feet': square_feet[i], 'rent_includes': {},
                                     'Amenities': {}}}
            electricity_check = request.POST.getlist(f'electricity_check{i}', [])
            gas_check = request.POST.getlist(f'gas_check{i}', [])
            water_check = request.POST.getlist(f'water_check{i}', [])
            int_cable_check = request.POST.getlist(f'int_cable_check{i}', [])
            ac_check = request.POST.getlist(f'ac_check{i}', [])
            pool_check = request.POST.getlist(f'pool_check{i}', [])
            pets_check = request.POST.getlist(f'pets_check{i}', [])
            furnished_check = request.POST.getlist(f'furnished_check{i}', [])
            balcony_check = request.POST.getlist(f'balcony_check{i}', [])
            hardwood_check = request.POST.getlist(f'hardwood_check{i}', [])
            wheel_check = request.POST.getlist(f'wheel_check{i}', [])
            parking_check = request.POST.getlist(f'parking_check{i}', [])

            add_checkbox_value(electricity_check, unit_dict['details'], 'rent_includes', 'electricity_check')
            add_checkbox_value(gas_check, unit_dict['details'], 'rent_includes', 'gas_check')
            add_checkbox_value(water_check, unit_dict['details'], 'rent_includes', 'water_check')
            add_checkbox_value(int_cable_check, unit_dict['details'], 'rent_includes', 'int_cable_check')
            add_checkbox_value(ac_check, unit_dict['details'], 'Amenities', 'ac_check')
            add_checkbox_value(pool_check, unit_dict['details'], 'Amenities', 'pool_check')
            add_checkbox_value(pets_check, unit_dict['details'], 'Amenities', 'pets_check')
            add_checkbox_value(furnished_check, unit_dict['details'], 'Amenities', 'furnished_check')
            add_checkbox_value(balcony_check, unit_dict['details'], 'Amenities', 'balcony_check')
            add_checkbox_value(hardwood_check, unit_dict['details'], 'Amenities', 'hardwood_check')
            add_checkbox_value(wheel_check, unit_dict['details'], 'Amenities', 'wheel_check')
            add_checkbox_value(parking_check, unit_dict['details'], 'Amenities', 'parking_check')
            unit_details.append(unit_dict)

        property_obj = Property()

        # -------------- Rental Details ---------------------- #
        select_unit = request.POST['select_unit']
        term_name = request.POST['term_name']
        lease_start_date = request.POST['lease_start_date']
        lease_end_date = request.POST['lease_end_date']
        deposit = request.POST['deposit']
        due_on = request.POST['due_on']
        already_deposit = request.POST.getlist('already_deposit', [])
        rent = request.POST['rent']
        select_due_date = request.POST['select_due_date']
        select_due_date = request.POST['select_due_date']
        first_rental_due_date = request.POST['first_rental_due_date']
        invoice_date_list = request.POST['invoice_date_list']
        invoice_amount_list = request.POST['invoice_amount_list']

        if already_deposit:
            deposit_check = already_deposit[0]
        else:
            deposit_check = 'off'

        # -------------- Tenants Details ---------------------- #
        tenant_f_name = request.POST['tenant_f_name']
        tenant_l_name = request.POST['tenant_l_name']
        tenant_email = request.POST['tenant_email']
        tenant_mobile_number = request.POST['tenant_mobile_number']

    p = pd.Period(str(today_date))
    if p.is_leap_year:
        one_year_date = today_date + datetime.timedelta(days=366)
    else:
        one_year_date = today_date + datetime.timedelta(days=365)

    currency_symbol = "$"
    return render(request, "test.html", context={'today_date': today_date, 'one_year_date': one_year_date,
                                                 'today_date_str': str(today_date),
                                                 'one_year_date_str': str(one_year_date),
                                                 "currency_symbol": currency_symbol})


def property_save_fun(request, property_obj, user_name, rent, total_tenants):
    # -------------- Property Details ---------------------- #
    try:
        property_image = request.FILES['property_image']
    except:
        property_image = ""

    try:
        net_worth_check = request.POST['net_worth_check']
    except:
        net_worth_check = False

    property_name = request.POST['property_name']
    address_line1 = request.POST['address_line1']
    address_line2 = request.POST['address_line2']
    postcode = request.POST['postcode']
    city = request.POST['city']
    state = request.POST['state']
    country = request.POST['country']
    currency_name = request.POST['currency_name']
    property_amount = request.POST['property_amount']
    property_type = request.POST['property_type']
    unit_name = request.POST.getlist('unit_name')
    bed_room_quantity = request.POST.getlist('bed_room_quantity')
    bath_room_quantity = request.POST.getlist('bath_room_quantity')
    square_feet = request.POST.getlist('square_feet')
    unit_details = []

    if net_worth_check:
        net_worth_check = True
    else:
        net_worth_check = False

    for i in range(len(unit_name)):
        unit_dict = {'name': unit_name[i],
                     'details': {'bed_room': bed_room_quantity[i], 'bath_room': bath_room_quantity[i],
                                 'square_feet': square_feet[i], 'rent_includes': {},
                                 'Amenities': {}}}
        electricity_check = request.POST.getlist(f'electricity_check{i}', [])
        gas_check = request.POST.getlist(f'gas_check{i}', [])
        water_check = request.POST.getlist(f'water_check{i}', [])
        int_cable_check = request.POST.getlist(f'int_cable_check{i}', [])
        ac_check = request.POST.getlist(f'ac_check{i}', [])
        pool_check = request.POST.getlist(f'pool_check{i}', [])
        pets_check = request.POST.getlist(f'pets_check{i}', [])
        furnished_check = request.POST.getlist(f'furnished_check{i}', [])
        balcony_check = request.POST.getlist(f'balcony_check{i}', [])
        hardwood_check = request.POST.getlist(f'hardwood_check{i}', [])
        wheel_check = request.POST.getlist(f'wheel_check{i}', [])
        parking_check = request.POST.getlist(f'parking_check{i}', [])

        add_checkbox_value(electricity_check, unit_dict['details'], 'rent_includes', 'electricity_check')
        add_checkbox_value(gas_check, unit_dict['details'], 'rent_includes', 'gas_check')
        add_checkbox_value(water_check, unit_dict['details'], 'rent_includes', 'water_check')
        add_checkbox_value(int_cable_check, unit_dict['details'], 'rent_includes', 'int_cable_check')
        add_checkbox_value(ac_check, unit_dict['details'], 'Amenities', 'ac_check')
        add_checkbox_value(pool_check, unit_dict['details'], 'Amenities', 'pool_check')
        add_checkbox_value(pets_check, unit_dict['details'], 'Amenities', 'pets_check')
        add_checkbox_value(furnished_check, unit_dict['details'], 'Amenities', 'furnished_check')
        add_checkbox_value(balcony_check, unit_dict['details'], 'Amenities', 'balcony_check')
        add_checkbox_value(hardwood_check, unit_dict['details'], 'Amenities', 'hardwood_check')
        add_checkbox_value(wheel_check, unit_dict['details'], 'Amenities', 'wheel_check')
        add_checkbox_value(parking_check, unit_dict['details'], 'Amenities', 'parking_check')
        unit_details.append(unit_dict)

    property_obj.user = user_name
    property_obj.property_image = property_image
    property_obj.property_name = property_name
    property_obj.property_type = property_type
    property_obj.address_line1 = address_line1
    property_obj.address_line2 = address_line2
    property_obj.post_code = postcode
    property_obj.city = city
    property_obj.state = state
    property_obj.country = country
    property_obj.unit_details = unit_details
    property_obj.value = property_amount
    property_obj.currency = currency_name
    property_obj.include_net_worth = net_worth_check
    property_obj.units_no = len(unit_name)
    property_obj.total_monthly_rent = rent
    property_obj.total_tenants = total_tenants
    property_obj.save()


def rental_info_save(request, user_name, rental_obj, property_obj, invoice_data, rent, method_name):
    # -------------- Rental Details ---------------------- #
    select_unit = request.POST['select_unit']
    term_name = request.POST['term_name']
    lease_start_date = request.POST['lease_start_date']
    lease_end_date = request.POST['lease_end_date']
    deposit = request.POST['deposit']
    due_on = request.POST['due_on']
    already_deposit = request.POST.getlist('already_deposit', [])
    select_due_date = request.POST['select_due_date']
    first_rental_due_date = request.POST['first_rental_due_date']
    invoice_date_list = ast.literal_eval(request.POST['invoice_date_list'])
    invoice_amount_list = ast.literal_eval(request.POST['invoice_amount_list'])
    first_rental_due_date = str(datetime.datetime.strptime(first_rental_due_date, "%B %d, %Y").date())

    # -------------- Tenants Details ---------------------- #
    tenant_f_name = request.POST['tenant_f_name']
    tenant_l_name = request.POST['tenant_l_name']
    tenant_email = request.POST['tenant_email']
    tenant_mobile_number = request.POST['tenant_mobile_number']

    if already_deposit:

        deposit_check = already_deposit[0]
    else:
        deposit_check = 'off'

    if float(deposit) > 0:
        if method_name == "update":
            if float(rental_obj.deposit_amount) > 0:
                invoice_obj = invoice_data[0]
            else:
                invoice_obj = PropertyInvoice()
        else:
            invoice_obj = invoice_data

        invoice_obj.user = user_name
        invoice_obj.property_details = property_obj
        invoice_obj.tenant_name = tenant_f_name + " " + tenant_l_name
        invoice_obj.unit_name = select_unit
        invoice_obj.item_type = "Rent"
        invoice_obj.item_description = f"Rent Deposit Due on"
        invoice_obj.quantity = 1
        invoice_obj.item_amount = deposit
        invoice_obj.invoice_due_date = due_on
        invoice_obj.record_payment = []
        if deposit_check == 'off':
            invoice_obj.invoice_status = "Unpaid"
            invoice_obj.already_paid = 0
            invoice_obj.balance_due = deposit
        else:
            invoice_obj.invoice_status = "Fully Paid"
            invoice_obj.already_paid = deposit
            invoice_obj.balance_due = 0
            invoice_obj.invoice_paid_date = today_date
            deposit_date = datetime.datetime.strftime(today_date, "%B %d, %Y")
            invoice_obj.record_payment = [[0, invoice_obj.tenant_name, deposit_date, 'Cash', deposit]]
        invoice_obj.save()

    rental_summary = []
    date_list_len = len(invoice_date_list)
    if method_name == "update":
        invoice_update_len = len(invoice_data)

    print("invoice_date_list======>", invoice_date_list)
    for i in range(date_list_len):
        if invoice_date_list[i] != "None":
            date_value = datetime.datetime.strptime(invoice_date_list[i], "%B %d, %Y").date()
            total_amount = float(invoice_amount_list[i])
            if method_name == "update":
                if date_list_len == invoice_update_len:
                    invoice_obj = invoice_data[i]
                elif date_list_len < invoice_update_len:
                    invoice_obj = invoice_data[i]
                    diff_len = invoice_update_len - date_list_len
                    for obj_index in range(diff_len):
                        invoice_update_len -= 1
                        invoice_data[invoice_update_len].delete()
                else:
                    if i + 1 > invoice_update_len:
                        invoice_obj = PropertyInvoice()
                    else:
                        invoice_obj = invoice_data[i]

            else:
                invoice_obj = PropertyInvoice()

            if first_rental_due_date == str(rental_obj.rent_due_date):
                paid_already = float(invoice_obj.already_paid)
                quantity = int(invoice_obj.quantity)
                total_due = total_amount * quantity
                tenant_name = invoice_obj.tenant_name
                item_type = invoice_obj.item_type
                item_description = f"Rent Due on {invoice_date_list[i]}"
                invoice_status = invoice_obj.invoice_status
                record_payment_list = ""
                already_paid = 0
                if invoice_obj.record_payment:
                    if paid_already <= total_due:
                        already_paid = paid_already
                        record_payment_list = ast.literal_eval(invoice_obj.record_payment)
                balance_due = total_due - already_paid
            else:
                already_paid = 0
                quantity = "1"
                tenant_name = tenant_f_name + " " + tenant_l_name
                item_type = "Rent"
                item_description = f"Rent Due on {invoice_date_list[i]}"
                invoice_status = "Unpaid"
                balance_due = total_amount
                record_payment_list = ""

            invoice_obj.user = user_name
            invoice_obj.property_details = property_obj
            invoice_obj.tenant_name = tenant_name
            invoice_obj.unit_name = select_unit
            invoice_obj.item_type = item_type
            invoice_obj.item_description = item_description
            invoice_obj.quantity = quantity
            invoice_obj.item_amount = total_amount
            invoice_obj.already_paid = already_paid
            invoice_obj.balance_due = balance_due
            invoice_obj.invoice_due_date = date_value
            invoice_obj.invoice_status = invoice_status
            invoice_obj.record_payment = record_payment_list
            invoice_obj.save()
            rental_summary.append({'due': invoice_date_list[i], 'amount': total_amount})

    print("rent--------->", rent)
    rental_obj.user = user_name
    rental_obj.property_address = property_obj
    rental_obj.unit_name = select_unit
    rental_obj.rental_term = term_name
    rental_obj.rental_start_date = lease_start_date
    rental_obj.rental_end_date = lease_end_date
    rental_obj.deposit_amount = deposit
    rental_obj.deposit_due_date = due_on
    rental_obj.deposit_check = deposit_check
    rental_obj.rent_amount = rent
    rental_obj.rent_due_every_month = select_due_date
    rental_obj.rent_due_date = first_rental_due_date
    rental_obj.rental_summary = rental_summary
    rental_obj.first_name = tenant_f_name
    rental_obj.last_name = tenant_l_name
    rental_obj.email = tenant_email
    rental_obj.mobile_number = tenant_mobile_number
    rental_obj.save()


def add_property(request):
    context = {}
    if request.method == 'POST':
        user_name = request.user
        property_obj = Property()
        rental_obj = PropertyRentalInfo()
        invoice_obj = PropertyInvoice()
        rent = request.POST['rent']
        total_tenants = 1
        property_save_fun(request, property_obj, user_name, rent, total_tenants)
        rental_info_save(request, user_name, rental_obj, property_obj, invoice_obj, rent, 'add')
        return redirect("/property_list/")
    else:
        try:
            file_name = request.GET['file_name']
            name = request.GET['name']
            currency = request.GET['currency']
            value = request.GET['value']
            context = {
                'file_name': file_name,
                'name': name,
                'currency': currency,
                'value': value,
            }

        except:
            context = {'file_name': 'False', 'currency_symbol': '$'}

    p = pd.Period(str(today_date))
    if p.is_leap_year:
        one_year_date = today_date + datetime.timedelta(days=366)
    else:
        one_year_date = today_date + datetime.timedelta(days=365)

    context.update({'today_date': today_date, 'one_year_date': one_year_date,
                    'today_date_str': str(today_date),
                    'one_year_date_str': str(one_year_date),
                    'month_date_dict': month_date_dict,
                    'currency_dict': currency_dict
                    })
    return render(request, "property/property_add.html", context=context)


def update_property(request, pk, method_name):
    user_name = request.user
    context = {'method_type': method_name,
               'currency_dict': currency_dict, 'property_type_list': property_type_list,
               'month_date_dict': month_date_dict, 'url_type': "Update"
               }
    if method_name == "property":
        result_obj = Property.objects.get(user=user_name, pk=pk)
        if request.method == 'POST':
            property_save_fun(request, result_obj, user_name, result_obj.total_monthly_rent, result_obj.total_tenants)
            return redirect(f"/property_details/{result_obj.id}")
        unit_details = ast.literal_eval(result_obj.unit_details)
        context['unit_details'] = unit_details
    else:
        result_obj = PropertyRentalInfo.objects.get(user=user_name, pk=pk)
        invoice_obj = PropertyInvoice.objects.filter(user=user_name, property_details=result_obj.property_address,
                                                     unit_name=result_obj.unit_name)
        if request.method == 'POST':
            rent = request.POST['rent']
            rental_info_save(request, user_name, result_obj, result_obj.property_address, invoice_obj,
                             rent, 'update')
            return redirect(f"/property_details/{result_obj.property_address.id}")

        invoice_date_list = []
        invoice_amount_list = []
        rent_invoice_list = []
        for invoice_detail in invoice_obj:
            due_date = datetime.datetime.strftime(invoice_detail.invoice_due_date, "%B %d, %Y")
            item_amount = float(invoice_detail.item_amount)
            rent_invoice_list.append({'due': due_date, 'amount': item_amount})
            invoice_date_list.append(due_date)
            invoice_amount_list.append(item_amount)

        print(invoice_date_list)
        context['invoice_date_list'] = json.dumps(invoice_date_list)
        context['invoice_amount_list'] = json.dumps(invoice_amount_list)
        context['total_invoice_amount'] = sum(invoice_amount_list)
        context['rent_invoice_list'] = rent_invoice_list

    context['result_obj'] = result_obj
    return render(request, "property/property_update.html", context=context)


@login_required(login_url="/login")
def list_property(request):
    property_obj = Property.objects.filter(user=request.user)
    maintenance_dict = {}
    for data in property_obj:
        maintenance_obj = PropertyMaintenance.objects.filter(property_details__property_name=data.property_name,
                                                             status='Unresolved')
        maintenance_dict[data.property_name] = len(maintenance_obj)

    property_key = ['Properties', 'Address', 'Property Value', 'Total Monthly Rent', 'Tenants/Owners',
                    'Open Maintenance']

    context = {'property_obj': property_obj, 'maintenance_dict': maintenance_dict,
               'property_key': property_key, 'property_key_dumps': json.dumps(property_key)}
    return render(request, "property/property_list.html", context=context)


@login_required(login_url="/login")
def property_details(request, pk):
    property_obj = Property.objects.get(user=request.user, pk=pk)
    unit_list = ast.literal_eval(property_obj.unit_details)
    maintenance_obj = PropertyMaintenance.objects.filter(property_details=property_obj)
    unit_details = PropertyRentalInfo.objects.filter(user=request.user, property_address=property_obj)
    remaining_unit_list = [i['name'] for i in unit_list]
    total_rent_amount_collected = 0
    other_amount_collected = 0
    collection_list = {}
    maintenance_dict = {}

    for data in unit_details:
        name_unit = data.unit_name
        remaining_unit_list.remove(name_unit)
        invoice_obj = PropertyInvoice.objects.filter(user=request.user, property_details=property_obj,
                                                     unit_name=data.unit_name)
        for maintenance_data in maintenance_obj:
            if maintenance_data.unit_name == name_unit:
                if name_unit in maintenance_dict:
                    maintenance_dict[name_unit].append(maintenance_data)
                else:
                    maintenance_dict[name_unit] = [maintenance_data]
        overdue_list = []
        for data_obj in invoice_obj:
            paid_amount = float(data_obj.already_paid)
            invoice_status = data_obj.invoice_status
            due_date = data_obj.invoice_due_date
            days_diff = due_date - today_date
            if days_diff.days <= 30:
                day_diff = data_obj.id
            else:
                day_diff = invoice_obj[0].id
            if invoice_status == "Overdue":
                overdue_list.append(data_obj.id)
            if data_obj.item_type == "Rent":
                total_rent_amount_collected += paid_amount
            else:
                other_amount_collected += paid_amount

        total_amount = total_rent_amount_collected + other_amount_collected
        collection_list[data.unit_name] = [total_rent_amount_collected, other_amount_collected, total_amount,
                                           day_diff, overdue_list]

    currency_symbol = property_obj.currency
    context = {'property_obj': property_obj,
               'unit_details': unit_details,
               'currency_symbol': currency_symbol,
               'collection_list': collection_list,
               'today_date': today_date,
               'unit_list': unit_list,
               'remaining_unit_list': remaining_unit_list,
               'maintenance_dict': maintenance_dict
               }
    return render(request, "property/property_detail.html", context=context)


@login_required(login_url="/login")
def add_lease(request, pk, unit_name):
    username = request.user
    result_obj = Property.objects.get(user=username, pk=pk)

    if request.method == 'POST':
        rental_obj = PropertyRentalInfo()
        invoice_obj = PropertyInvoice()
        rent = request.POST['rent']
        rental_info_save(request, username, rental_obj, result_obj, invoice_obj, rent, 'add')
        total_amount = float(result_obj.total_monthly_rent) + float(rent)
        result_obj.total_monthly_rent = total_amount
        tenants_no = int(result_obj.total_tenants) + 1
        result_obj.total_tenants = tenants_no
        result_obj.save()

        return redirect("/property_list/")

    else:

        p = pd.Period(str(today_date))
        if p.is_leap_year:
            one_year_date = today_date + datetime.timedelta(days=366)
        else:
            one_year_date = today_date + datetime.timedelta(days=365)

        context = {'today_date': today_date, 'one_year_date': one_year_date,
                   'today_date_str': str(today_date),
                   'one_year_date_str': str(one_year_date),
                   'method_type': 'Rental Lease',
                   'url_type': "Add",
                   'result_obj': result_obj,
                   'currency_dict': currency_dict,
                   'property_type_list': property_type_list,
                   'month_date_dict': month_date_dict,
                   'unit_name': unit_name
                   }
        unit_details = ast.literal_eval(result_obj.unit_details)
        context['unit_details'] = unit_details

        return render(request, "property/property_update.html", context=context)


@login_required(login_url="/login")
def delete_property(request, pk):
    property_obj = Property.objects.get(pk=pk)
    property_obj.delete()
    return JsonResponse({"status": "Successfully", "path": "/property_list/"})


# Property Maintenance

class MaintenanceList(LoginRequiredMixin, ListView):
    model = PropertyMaintenance
    template_name = 'maintenance/maintenance_list.html'

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        data = super(MaintenanceList, self).get_context_data(**kwargs)
        user_name = self.request.user
        property_data = PropertyMaintenance.objects.filter(user=user_name)
        maintenance_key = ['Properties', 'Address', 'Request', 'Category', 'Status']
        data['maintenance_key'] = maintenance_key
        data['maintenance_key_dumps'] = json.dumps(maintenance_key)
        data['maintenance_obj'] = property_data
        return data


class MaintenanceDetail(LoginRequiredMixin, DetailView):
    model = PropertyMaintenance
    template_name = 'maintenance/maintenance_detail.html'


class MaintenanceAdd(LoginRequiredMixin, CreateView):
    model = PropertyMaintenance
    form_class = MaintenanceForm
    template_name = 'maintenance/maintenance_add.html'

    def get_form_kwargs(self):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""

        kwargs = super(MaintenanceAdd, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(MaintenanceAdd, self).get_context_data(**kwargs)
        data['page'] = 'Add'
        return data

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return super().form_valid(form)


class MaintenanceUpdate(LoginRequiredMixin, UpdateView):
    model = PropertyMaintenance
    form_class = MaintenanceForm
    template_name = 'maintenance/maintenance_add.html'

    def get_form_kwargs(self):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""
        kwargs = super(MaintenanceUpdate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(MaintenanceUpdate, self).get_context_data(**kwargs)
        property_id = data['propertymaintenance'].property_details.pk
        user_name = self.request.user
        unit_list, tenant_dict, currency = get_units(user_name, property_id)
        data['unit_list'] = unit_list
        data['page'] = 'Update'
        data['maintenance_id'] = self.kwargs['pk']
        return data


def delete_maintenance(request, pk):
    maintenance_obj = PropertyMaintenance.objects.get(pk=pk)
    maintenance_obj.delete()
    return JsonResponse({"status": "Successfully", "path": "/property/maintenance/list/"})


# Property Expenses Views
class ExpenseAdd(LoginRequiredMixin, CreateView):
    model = PropertyExpense
    form_class = ExpenseForm
    template_name = 'property/expense_add.html'

    def get_form_kwargs(self):
        """ Passes the request object to the form class.
         This is necessary to only display members that belong to a given user"""

        kwargs = super(ExpenseAdd, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(ExpenseAdd, self).get_context_data(**kwargs)
        data['page'] = 'Add'
        return data

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return super().form_valid(form)


class ExpenseList(LoginRequiredMixin, ListView):
    model = PropertyExpense
    template_name = 'property/expense_list.html'

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        data = super(ExpenseList, self).get_context_data(**kwargs)
        user_name = self.request.user
        property_data = PropertyExpense.objects.filter(user=user_name)
        expense_key = ['Properties', 'Category', 'Date', 'Request', 'Amount']
        data['expense_key'] = expense_key
        data['expense_key_dumps'] = json.dumps(expense_key)
        data['expense_obj'] = property_data
        return data


class ExpenseUpdate(LoginRequiredMixin, UpdateView):
    model = PropertyExpense
    form_class = ExpenseForm
    template_name = 'property/expense_add.html'

    def get_form_kwargs(self):
        kwargs = super(ExpenseUpdate, self).get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(ExpenseUpdate, self).get_context_data(**kwargs)
        property_id = data['propertyexpense'].property_details.pk
        user_name = self.request.user
        unit_list, tenant_dict, currency = get_units(user_name, property_id)
        data['unit_list'] = unit_list
        data['page'] = 'Update'
        data['expense_id'] = self.kwargs['pk']
        return data


@login_required(login_url="/login")
def delete_expense(request, pk):
    expense_obj = PropertyExpense.objects.get(pk=pk)
    expense_obj.delete()
    return JsonResponse({"status": "Successfully", "path": "/property/expense/list/"})


# Income & Invoices

@login_required(login_url="/login")
def property_income_list(request):
    user_name = request.user
    unit_obj = PropertyRentalInfo.objects.filter(user=user_name)
    income_list = []
    income_label = ['Total Open Invoices', 'Overdue', 'Partially Paid', 'Fully Paid']
    total_open_invoice = 0
    total_overdue = 0
    total_partially_paid = 0
    total_fully_paid = 0
    graph_currency = '$'

    for data in unit_obj:
        invoice_obj = PropertyInvoice.objects.filter(user=user_name, property_details=data.property_address,
                                                     unit_name=data.unit_name)
        data_list = [data.property_address.currency, data.property_address.property_name, data.unit_name]
        graph_currency = data.property_address.currency
        total_amount = 0
        total_paid = 0

        for item in invoice_obj:
            item_amount = float(item.item_amount) * float(item.quantity)
            item_paid = float(item.already_paid)
            total_amount += item_amount
            total_paid += item_paid
            if item.invoice_status == 'Unpaid':
                total_open_invoice += item_amount
            if item.invoice_status == 'Partially Paid':
                total_partially_paid += item_paid
                total_open_invoice += float(item.balance_due)
            if item.invoice_status == 'Fully Paid':
                total_fully_paid += item_amount
            if item.invoice_status == 'Overdue':
                over_due_amount = float(item.balance_due)
                total_overdue += over_due_amount

        total_balance = total_amount - total_paid
        data_list += [total_amount, total_paid, total_balance]
        income_list.append(data_list)

    income_values = [total_open_invoice, total_overdue, total_partially_paid, total_fully_paid]
    income_key = ['Property', 'Unit', 'Amount', 'Paid', 'Balance']

    context = {'income_obj': income_list,
               "graph_label": income_label,
               "graph_value": income_values,
               "graph_currency": graph_currency,
               'graph_id': '#income_pie_chart',
               'income_key': income_key,
               'income_key_dumps': json.dumps(income_key),
               "graph_label_dumps": json.dumps(income_label),
               "graph_value_dumps": json.dumps(income_values),

               }
    return render(request, "property_invoice/property_income_list.html", context=context)


@login_required(login_url="/login")
def property_invoice_add(request):
    user_name = request.user
    if request.method == 'POST':
        property_name = request.POST['property_name']
        invoice_due_date = request.POST['invoice_due_date']
        unit_name = request.POST['unit_name']
        tenant_name = request.POST['tenant_name']
        item_type = request.POST['item_type']
        item_description = request.POST['item_description']
        quantity = request.POST['quantity']
        item_amount = request.POST['item_amount']
        already_paid = float(request.POST['already_paid'])
        total_paid = int(quantity) * float(item_amount)
        balance_due = total_paid - already_paid

        due_date = datetime.datetime.strptime(invoice_due_date, "%Y-%m-%d").date()
        property_obj = Property.objects.get(user=user_name, pk=property_name)
        try:
            invoice_id = request.POST['invoice_id']
            invoice_obj = PropertyInvoice.objects.get(user=user_name, pk=invoice_id)
            record_payment_list = ast.literal_eval(invoice_obj.record_payment)
            redirect_url = f'/property/invoice/details/{invoice_id}'
        except:
            invoice_obj = PropertyInvoice()
            redirect_url = f"/property/invoice/list/{property_obj.property_name}/{unit_name}"
            record_payment_list = ""

        invoice_obj.user = user_name
        invoice_obj.property_details = property_obj
        invoice_obj.tenant_name = tenant_name
        invoice_obj.unit_name = unit_name
        invoice_obj.item_type = item_type
        invoice_obj.item_description = item_description
        invoice_obj.quantity = quantity
        invoice_obj.item_amount = item_amount
        invoice_obj.invoice_due_date = invoice_due_date
        invoice_obj.already_paid = already_paid
        invoice_obj.balance_due = balance_due
        invoice_obj.record_payment = []

        if already_paid > 0:
            invoice_obj.invoice_status = 'Partially Paid'
            deposit_date = datetime.datetime.strftime(today_date, "%B %d, %Y")
            invoice_obj.invoice_paid_date = today_date
            if record_payment_list:
                pass
            else:
                record_payment_list.append([0, tenant_name, deposit_date, 'Cash', already_paid])
            invoice_obj.record_payment = record_payment_list

        elif already_paid == total_paid:
            invoice_obj.invoice_status = 'Fully Paid'

        else:
            invoice_obj.invoice_status = 'Unpaid'

        if due_date < today_date:
            invoice_obj.invoice_status = 'Overdue'

        invoice_obj.save()
        return redirect(redirect_url)
    else:
        property_list = Property.objects.filter(user=user_name)
        context = {'property_list': property_list}

    return render(request, "property_invoice/property_invoice_add.html", context=context)


@login_required(login_url="/login")
def property_invoice_list(request, property_name, unit_name):
    user_name = request.user
    invoice_details = PropertyInvoice.objects.filter(user=user_name, property_details__property_name=property_name,
                                                     unit_name=unit_name).order_by('invoice_due_date')

    invoice_key = ['Invoice Id', 'Due on', 'Paid on', 'Amount', 'Paid', 'Balance', 'Status']
    context = {'invoice_details': invoice_details, 'property_name': property_name, 'unit_name': unit_name,
               'invoice_key': invoice_key, 'invoice_key_dumps': json.dumps(invoice_key)
               }
    return render(request, "property_invoice/property_invoice_list.html", context=context)


@login_required(login_url="/login")
def property_invoice_detail(request, pk):
    user_name = request.user
    invoice_obj = PropertyInvoice.objects.get(user=user_name, pk=pk)
    if invoice_obj.record_payment:
        record_payment_detail = ast.literal_eval(invoice_obj.record_payment)
    else:
        record_payment_detail = []

    days_diff = (today_date - invoice_obj.invoice_due_date).days
    if days_diff < 0:
        text_message = f"Payment expected in about {abs(days_diff)} days"
        text_class = 'text-success'

    if days_diff > 0:
        text_message = f"Payment late {abs(days_diff)} days"
        text_class = 'text-danger'
    if days_diff == 0:
        text_message = f"Payment expected at today"
        text_class = 'text-warning'

    if invoice_obj.invoice_status == 'Fully Paid':
        text_message = ""

    context = {'invoice_obj': invoice_obj, 'record_payment_detail': record_payment_detail,
               'today_date': str(today_date), 'text_message': text_message, 'text_class': text_class}
    return render(request, "property_invoice/property_invoice_detail.html", context=context)


@login_required(login_url="/login")
def property_invoice_update(request, pk):
    user_name = request.user
    invoice_obj = PropertyInvoice.objects.get(user=user_name, pk=pk)
    context = {'invoice_obj': invoice_obj}
    return render(request, "property_invoice/property_invoice_update.html", context=context)


@login_required(login_url="/login")
def record_payment_save(request, pk, method_type, paid_amount, payment_index=None):
    user_name = request.user
    invoice_obj = PropertyInvoice.objects.get(user=user_name, pk=pk)
    if invoice_obj.record_payment:
        record_payments = ast.literal_eval(invoice_obj.record_payment)
    else:
        record_payments = []
    balance_due = float(invoice_obj.balance_due)
    redirect_url = f'/property/invoice/details/{invoice_obj.id}'
    if method_type == "delete_payment":
        record_payments.remove(record_payments[payment_index - 1])
        invoice_obj.already_paid = float(invoice_obj.already_paid) - paid_amount
        invoice_obj.balance_due = float(invoice_obj.balance_due) + paid_amount
        if invoice_obj.already_paid == 0:
            invoice_obj.invoice_status = 'Unpaid'
        else:
            invoice_obj.invoice_status = 'Partially Paid'
    else:
        payment_no = len(record_payments)
        payer_name = request.POST['payer_name']
        payment_method = request.POST['payment_method']
        deposit_date = request.POST['deposit_date']
        invoice_obj.invoice_paid_date = deposit_date
        deposit_date = datetime.datetime.strptime(deposit_date, "%Y-%m-%d").date()
        deposit_date = datetime.datetime.strftime(deposit_date, "%B %d, %Y")
        record_payments.append([payment_no, payer_name, deposit_date, payment_method, paid_amount])
        invoice_obj.already_paid = float(invoice_obj.already_paid) + paid_amount
        invoice_obj.balance_due = balance_due - paid_amount

        if paid_amount > 0:
            invoice_obj.invoice_status = 'Partially Paid'

        if paid_amount == balance_due:
            invoice_obj.invoice_status = 'Fully Paid'

    invoice_obj.record_payment = record_payments
    if invoice_obj.invoice_due_date < today_date:
        invoice_obj.invoice_status = 'Overdue'

    invoice_obj.save()
    return redirect_url


@login_required(login_url="/login")
def delete_invoice_payment(request, pk, payment_index, paid_amount):
    paid_amount = float(paid_amount)
    redirect_url = record_payment_save(request, pk, 'delete_payment', paid_amount, payment_index)
    return redirect(redirect_url)


@login_required(login_url="/login")
def property_invoice_payment(request, pk):
    paid_amount = float(request.POST['paid_amount'])
    redirect_url = record_payment_save(request, pk, 'record_payment', paid_amount)
    return redirect(redirect_url)


@login_required(login_url="/login")
def property_invoice_delete(request, pk):
    user_name = request.user
    invoice_obj = PropertyInvoice.objects.get(user=user_name, pk=pk)
    redirect_url = f"/property/invoice/list/{invoice_obj.property_details.property_name}/{invoice_obj.unit_name}"
    invoice_obj.delete()
    return JsonResponse({"status": "Successfully", "path": redirect_url})


def get_units(user_name, property_name):
    property_info = Property.objects.get(user=user_name, pk=property_name)
    rental_info = PropertyRentalInfo.objects.filter(user=user_name, property_address=property_info)
    tenant_dict = {}
    for data in rental_info:
        tenant_dict[data.unit_name] = data.first_name + " " + data.last_name

    unit_list = ast.literal_eval(property_info.unit_details)
    return unit_list, tenant_dict, property_info.currency


@login_required(login_url="/login")
def property_info(request):
    if request.method == 'POST' and request.is_ajax():
        property_name = request.POST['property_name']
        user_name = request.user
        unit_list, tenant_dict, currency_symbol = get_units(user_name, property_name)
        return JsonResponse({'unit_list': unit_list, 'tenant_dict': tenant_dict, 'currency_symbol': currency_symbol})


# Sample Pages

def property_sample_page(request):
    graph_label = ['Total Open Invoices', 'Overdue', 'Partially Paid', 'Fully Paid']
    graph_value = [11500.0, 0, 0, 600.0]
    graph_currency = "$"
    context = {'graph_label': json.dumps(graph_label),
               'graph_value': graph_value,
               'graph_currency': graph_currency,
               'graph_id': "#income_pie_chart"
               }
    return render(request, 'property_sample_page.html', context=context)


def rental_property_sample_page(request):
    projection_key = ['Year 1', 'Year 2', 'Year 3', 'Year 4', 'Year 5', 'Year 6', 'Year 7', 'Year 8', 'Year 9',
                      'Year 10', 'Year 11', 'Year 12', 'Year 13', 'Year 14', 'Year 15', 'Year 16', 'Year 17', 'Year 18',
                      'Year 19', 'Year 20', 'Year 21', 'Year 22', 'Year 23', 'Year 24', 'Year 25', 'Year 26', 'Year 27',
                      'Year 28', 'Year 29', 'Year 30']

    cash_on_cash_return_data = [{'name': 'Cash on Cash Return(%)',
                                 'data': ['9.21%', '9.76%', '10.33%', '10.91%', '11.5%', '12.11%', '12.72%', '13.35%',
                                          '13.99%', '14.65%', '15.31%', '15.99%', '16.69%', '17.39%', '18.12%',
                                          '18.85%', '19.6%', '20.37%', '21.15%', '21.95%', '22.76%', '23.59%', '24.43%',
                                          '25.3%', '26.18%', '27.07%', '27.99%', '28.92%', '29.87%', '30.85%']}]

    return_on_investment_data = [{'name': 'Return On Investment % (ROI) (Assuming No Appreciation)',
                                  'data': ['16.92%', '17.71%', '18.52%', '19.35%', '20.2%', '21.07%', '21.95%',
                                           '22.86%', '23.79%', '24.74%', '25.72%', '26.72%', '27.73%', '28.78%',
                                           '29.85%', '30.94%', '32.06%', '33.2%', '34.37%', '35.57%', '36.8%',
                                           '38.06%', '39.34%', '40.66%', '42.0%', '43.38%', '44.79%', '46.24%',
                                           '47.72%', '49.23%']},
                                 {'name': 'Return On Investment % (ROI) (With Appreciation Assumption)',
                                  'data': ['30.77%', '31.98%', '33.21%', '34.48%', '35.79%', '37.12%', '38.49%',
                                           '39.9%', '41.34%', '42.82%', '44.33%', '45.89%', '47.48%', '49.12%',
                                           '50.8%', '52.52%', '54.28%', '56.09%', '57.95%', '59.86%', '61.81%',
                                           '63.82%', '65.88%', '67.99%', '70.16%', '72.38%', '74.66%', '77.0%',
                                           '79.41%', '81.87%']}]
    debt_cov_ratio_data = [{'name': 'Debt Service Coverage Ratio (%)', 'data': [1.49, 1.52, 1.55, 1.58, 1.62, 1.65,
                                                                                1.68, 1.71, 1.75, 1.78, 1.82, 1.86,
                                                                                1.89, 1.93, 1.97, 2.01, 2.05, 2.09,
                                                                                2.13, 2.17, 2.22, 2.26, 2.31, 2.35, 2.4,
                                                                                2.45, 2.5, 2.55, 2.6, 2.65]}]
    return_investment_data = [{'name': 'Annual Cashflow', 'data': [9969.6, 10573.73, 11189.95, 11818.49, 12459.6,
                                                                   13113.53, 13780.54, 14460.89, 15154.85, 15862.69,
                                                                   16584.69, 17321.12, 18072.28, 18838.47, 19619.98,
                                                                   20417.12, 21230.2, 22059.55, 22905.48, 23768.33,
                                                                   24648.44, 25546.15, 26461.81, 27395.79, 28348.44,
                                                                   29320.15, 30311.3, 31322.27, 32353.45, 33405.26]},
                              {'name': 'Net Operating Income(NOI)', 'data': ['30206.64', '30810.77', '31426.99',
                                                                             '32055.53', '32696.64', '33350.57',
                                                                             '34017.58', '34697.93', '35391.89',
                                                                             '36099.73', '36821.73', '37558.16',
                                                                             '38309.32', '39075.51', '39857.02',
                                                                             '40654.16', '41467.24', '42296.59',
                                                                             '43142.52', '44005.37', '44885.48',
                                                                             '45783.19', '46698.85', '47632.83',
                                                                             '48585.48', '49557.19', '50548.34',
                                                                             '51559.31', '52590.49', '53642.3']},
                              {'name': 'Return On Investment (ROI) (Assuming No Appreciation)',
                               'data': ['18320.82', '19178.94', '20056.9', '20955.13', '21874.14', '22814.43',
                                        '23776.5', '24760.87', '25768.12', '26798.8', '27853.42', '28932.62',
                                        '30036.92', '31167.03', '32323.52', '33507.06', '34718.29', '35957.89',
                                        '37226.54', '38524.99', '39853.93', '41214.15', '42606.36', '44031.4',
                                        '45490.01', '46983.1', '48511.49', '50076.03', '51677.63', '53317.21']},
                              {'name': 'Return On Investment (ROI) (With Appreciation Assumption)',
                               'data': ['33320.82', '34628.94', '35970.4', '37346.04', '38756.77', '40203.54',
                                        '41687.28', '43208.98', '44769.67', '46370.4', '48012.17', '49696.13',
                                        '51423.33', '53195.04', '55012.37', '56876.57', '58788.89', '60750.6',
                                        '62763.04', '64827.58', '66945.6', '69118.57', '71347.91', '73635.2',
                                        '75981.92', '78389.77', '80860.36', '83395.37', '85996.55', '88665.69']}]

    property_expense_data = [{'name': 'Operating Expenses', 'data': ['11793.36', '12029.23', '12269.81', '12515.21',
                                                                     '12765.51', '13020.82', '13281.24', '13546.86',
                                                                     '13817.8', '14094.16', '14376.04', '14663.56',
                                                                     '14956.83', '15255.97', '15561.09', '15872.31',
                                                                     '16189.76', '16513.55', '16843.82', '17180.7',
                                                                     '17524.31', '17874.8', '18232.29', '18596.94',
                                                                     '18968.88', '19348.26', '19735.22', '20129.93',
                                                                     '20532.53', '20943.18']}]
    mortgage_graph_data = [{'name': 'Balance',
                            'data': [400000.0, 399313.58, 398625.45, 397935.6, 397244.02, 396550.72, 395855.68,
                                     395158.9, 394460.38,
                                     393760.12, 393058.1, 392354.33, 391648.8, 390941.5, 390232.44, 389521.61,
                                     388808.99, 388094.6, 387378.42,
                                     386660.45, 385940.69, 385219.12, 384495.75, 383770.58, 383043.59, 382314.78,
                                     381584.15, 380851.7,
                                     380117.41, 379381.29, 378643.32, 377903.51, 377161.86, 376418.35, 375672.98,
                                     374925.74, 374176.64,
                                     373425.67, 372672.81, 371918.08, 371161.46, 370402.95, 369642.54, 368880.23,
                                     368116.01, 367349.89,
                                     366581.84, 365811.88, 365040.0, 364266.18, 363490.43, 362712.74, 361933.11,
                                     361151.52, 360367.98,
                                     359582.49, 358795.03, 358005.6, 357214.2, 356420.82, 355625.45, 354828.1,
                                     354028.76, 353227.41,
                                     352424.06, 351618.71, 350811.34, 350001.95, 349190.54, 348377.1, 347561.63,
                                     346744.11, 345924.56,
                                     345102.95, 344279.29, 343453.58, 342625.79, 341795.94, 340964.02, 340130.01,
                                     339293.92, 338455.74,
                                     337615.46, 336773.08, 335928.6, 335082.01, 334233.29, 333382.46, 332529.5,
                                     331674.41, 330817.18,
                                     329957.81, 329096.28, 328232.61, 327366.77, 326498.77, 325628.61, 324756.26,
                                     323881.74, 323005.02,
                                     322126.12, 321245.02, 320361.72, 319476.2, 318588.48, 317698.53, 316806.36,
                                     315911.96, 315015.33,
                                     314116.45, 313215.32, 312311.95, 311406.31, 310498.41, 309588.24, 308675.79,
                                     307761.07, 306844.05,
                                     305924.75, 305003.14, 304079.24, 303153.02, 302224.48, 301293.63, 300360.45,
                                     299424.93, 298487.08,
                                     297546.88, 296604.33, 295659.43, 294712.16, 293762.52, 292810.51, 291856.12,
                                     290899.35, 289940.18,
                                     288978.61, 288014.64, 287048.26, 286079.47, 285108.25, 284134.61, 283158.53,
                                     282180.01, 281199.04,
                                     280215.62, 279229.74, 278241.4, 277250.59, 276257.3, 275261.53, 274263.26,
                                     273262.51, 272259.25,
                                     271253.48, 270245.2, 269234.39, 268221.06, 267205.2, 266186.8, 265165.85,
                                     264142.35, 263116.29,
                                     262087.66, 261056.46, 260022.69, 258986.33, 257947.38, 256905.83, 255861.68,
                                     254814.92, 253765.54,
                                     252713.54, 251658.9, 250601.64, 249541.72, 248479.16, 247413.94, 246346.06,
                                     245275.51, 244202.28,
                                     243126.37, 242047.77, 240966.48, 239882.48, 238795.77, 237706.34, 236614.19,
                                     235519.31, 234421.69,
                                     233321.33, 232218.22, 231112.35, 230003.71, 228892.3, 227778.12, 226661.15,
                                     225541.38, 224418.82,
                                     223293.45, 222165.27, 221034.27, 219900.44, 218763.77, 217624.26, 216481.91,
                                     215336.7, 214188.62,
                                     213037.68, 211883.86, 210727.15, 209567.55, 208405.05, 207239.65, 206071.33,
                                     204900.1, 203725.93,
                                     202548.83, 201368.79, 200185.79, 198999.84, 197810.92, 196619.03, 195424.17,
                                     194226.31, 193025.46,
                                     191821.61, 190614.74, 189404.87, 188191.96, 186976.03, 185757.05, 184535.03,
                                     183309.95, 182081.81,
                                     180850.59, 179616.3, 178378.93, 177138.46, 175894.89, 174648.21, 173398.42,
                                     172145.5, 170889.44,
                                     169630.25, 168367.91, 167102.41, 165833.75, 164561.92, 163286.91, 162008.71,
                                     160727.32, 159442.72,
                                     158154.91, 156863.88, 155569.63, 154272.13, 152971.4, 151667.41, 150360.16,
                                     149049.65, 147735.85,
                                     146418.78, 145098.41, 143774.74, 142447.76, 141117.46, 139783.84, 138446.88,
                                     137106.58, 135762.93,
                                     134415.93, 133065.55, 131711.8, 130354.66, 128994.13, 127630.2, 126262.86,
                                     124892.1, 123517.91,
                                     122140.29, 120759.23, 119374.71, 117986.73, 116595.28, 115200.35, 113801.94,
                                     112400.03, 110994.61,
                                     109585.68, 108173.23, 106757.25, 105337.72, 103914.65, 102488.02, 101057.83,
                                     99624.05, 98186.7, 96745.75,
                                     95301.2, 93853.03, 92401.25, 90945.84, 89486.79, 88024.09, 86557.73, 85087.71,
                                     83614.01, 82136.63,
                                     80655.56, 79170.78, 77682.29, 76190.08, 74694.14, 73194.46, 71691.03, 70183.84,
                                     68672.88, 67158.15,
                                     65639.63, 64117.31, 62591.19, 61061.25, 59527.49, 57989.89, 56448.45, 54903.15,
                                     53353.99, 51800.96,
                                     50244.05, 48683.24, 47118.54, 45549.92, 43977.37, 42400.9, 40820.49, 39236.12,
                                     37647.8, 36055.5,
                                     34459.22, 32858.96, 31254.69, 29646.41, 28034.11, 26417.78, 24797.4, 23172.98,
                                     21544.5, 19911.94,
                                     18275.31, 16634.58, 14989.75, 13340.81, 11687.74, 10030.55, 8369.21, 6703.71,
                                     5034.06, 3360.23,
                                     1682.21]}, {'name': 'Principle',
                                                 'data': [686.42, 688.13, 689.85, 691.58, 693.31, 695.04, 696.78,
                                                          698.52, 700.27, 702.02,
                                                          703.77, 705.53, 707.29, 709.06, 710.84, 712.61, 714.39,
                                                          716.18, 717.97, 719.77,
                                                          721.56, 723.37, 725.18, 726.99, 728.81, 730.63, 732.46,
                                                          734.29, 736.12, 737.96,
                                                          739.81, 741.66, 743.51, 745.37, 747.23, 749.1, 750.97, 752.85,
                                                          754.73, 756.62,
                                                          758.51, 760.41, 762.31, 764.22, 766.13, 768.04, 769.96,
                                                          771.89, 773.82, 775.75,
                                                          777.69, 779.63, 781.58, 783.54, 785.5, 787.46, 789.43, 791.4,
                                                          793.38, 795.36,
                                                          797.35, 799.35, 801.34, 803.35, 805.36, 807.37, 809.39,
                                                          811.41, 813.44, 815.47,
                                                          817.51, 819.56, 821.6, 823.66, 825.72, 827.78, 829.85, 831.93,
                                                          834.01, 836.09,
                                                          838.18, 840.28, 842.38, 844.48, 846.59, 848.71, 850.83,
                                                          852.96, 855.09, 857.23,
                                                          859.37, 861.52, 863.68, 865.83, 868.0, 870.17, 872.34, 874.53,
                                                          876.71, 878.9, 881.1,
                                                          883.3, 885.51, 887.73, 889.94, 892.17, 894.4, 896.64, 898.88,
                                                          901.13, 903.38,
                                                          905.64, 907.9, 910.17, 912.45, 914.73, 917.01, 919.31, 921.6,
                                                          923.91, 926.22,
                                                          928.53, 930.85, 933.18, 935.52, 937.85, 940.2, 942.55, 944.91,
                                                          947.27, 949.64,
                                                          952.01, 954.39, 956.78, 959.17, 961.57, 963.97, 966.38, 968.8,
                                                          971.22, 973.65,
                                                          976.08, 978.52, 980.97, 983.42, 985.88, 988.34, 990.81,
                                                          993.29, 995.77, 998.26,
                                                          1000.76, 1003.26, 1005.77, 1008.28, 1010.8, 1013.33, 1015.86,
                                                          1018.4, 1020.95,
                                                          1023.5, 1026.06, 1028.63, 1031.2, 1033.77, 1036.36, 1038.95,
                                                          1041.55, 1044.15,
                                                          1046.76, 1049.38, 1052.0, 1054.63, 1057.27, 1059.91, 1062.56,
                                                          1065.22, 1067.88,
                                                          1070.55, 1073.23, 1075.91, 1078.6, 1081.3, 1084.0, 1086.71,
                                                          1089.43, 1092.15,
                                                          1094.88, 1097.62, 1100.36, 1103.11, 1105.87, 1108.64, 1111.41,
                                                          1114.19, 1116.97,
                                                          1119.76, 1122.56, 1125.37, 1128.18, 1131.0, 1133.83, 1136.67,
                                                          1139.51, 1142.36,
                                                          1145.21, 1148.07, 1150.94, 1153.82, 1156.71, 1159.6, 1162.5,
                                                          1165.4, 1168.32,
                                                          1171.24, 1174.17, 1177.1, 1180.04, 1182.99, 1185.95, 1188.92,
                                                          1191.89, 1194.87,
                                                          1197.86, 1200.85, 1203.85, 1206.86, 1209.88, 1212.9, 1215.94,
                                                          1218.98, 1222.02,
                                                          1225.08, 1228.14, 1231.21, 1234.29, 1237.38, 1240.47, 1243.57,
                                                          1246.68, 1249.8,
                                                          1252.92, 1256.05, 1259.19, 1262.34, 1265.5, 1268.66, 1271.83,
                                                          1275.01, 1278.2,
                                                          1281.39, 1284.6, 1287.81, 1291.03, 1294.26, 1297.49, 1300.74,
                                                          1303.99, 1307.25,
                                                          1310.52, 1313.79, 1317.08, 1320.37, 1323.67, 1326.98, 1330.3,
                                                          1333.62, 1336.96,
                                                          1340.3, 1343.65, 1347.01, 1350.38, 1353.75, 1357.14, 1360.53,
                                                          1363.93, 1367.34,
                                                          1370.76, 1374.19, 1377.62, 1381.07, 1384.52, 1387.98, 1391.45,
                                                          1394.93, 1398.42,
                                                          1401.91, 1405.42, 1408.93, 1412.45, 1415.98, 1419.52, 1423.07,
                                                          1426.63, 1430.2,
                                                          1433.77, 1437.36, 1440.95, 1444.55, 1448.16, 1451.78, 1455.41,
                                                          1459.05, 1462.7,
                                                          1466.36, 1470.02, 1473.7, 1477.38, 1481.07, 1484.78, 1488.49,
                                                          1492.21, 1495.94,
                                                          1499.68, 1503.43, 1507.19, 1510.96, 1514.73, 1518.52, 1522.32,
                                                          1526.12, 1529.94,
                                                          1533.76, 1537.6, 1541.44, 1545.3, 1549.16, 1553.03, 1556.91,
                                                          1560.81, 1564.71,
                                                          1568.62, 1572.54, 1576.47, 1580.41, 1584.36, 1588.33, 1592.3,
                                                          1596.28, 1600.27,
                                                          1604.27, 1608.28, 1612.3, 1616.33, 1620.37, 1624.42, 1628.48,
                                                          1632.55, 1636.64,
                                                          1640.73, 1644.83, 1648.94, 1653.06, 1657.2, 1661.34, 1665.49,
                                                          1669.66, 1673.83,
                                                          1678.02, 1682.21]}, {'name': 'Interest',
                                                                               'data': [1000.0, 998.28, 996.56, 994.84,
                                                                                        993.11, 991.38,
                                                                                        989.64, 987.9, 986.15, 984.4,
                                                                                        982.65, 980.89, 979.12,
                                                                                        977.35, 975.58, 973.8, 972.02,
                                                                                        970.24, 968.45, 966.65,
                                                                                        964.85, 963.05, 961.24, 959.43,
                                                                                        957.61, 955.79,
                                                                                        953.96, 952.13, 950.29, 948.45,
                                                                                        946.61, 944.76, 942.9,
                                                                                        941.05, 939.18, 937.31, 935.44,
                                                                                        933.56, 931.68, 929.8,
                                                                                        927.9, 926.01, 924.11, 922.2,
                                                                                        920.29, 918.37, 916.45,
                                                                                        914.53, 912.6, 910.67, 908.73,
                                                                                        906.78, 904.83, 902.88,
                                                                                        900.92, 898.96, 896.99, 895.01,
                                                                                        893.04, 891.05,
                                                                                        889.06, 887.07, 885.07, 883.07,
                                                                                        881.06, 879.05,
                                                                                        877.03, 875.0, 872.98, 870.94,
                                                                                        868.9, 866.86, 864.81,
                                                                                        862.76, 860.7, 858.63, 856.56,
                                                                                        854.49, 852.41, 850.33,
                                                                                        848.23, 846.14, 844.04, 841.93,
                                                                                        839.82, 837.71,
                                                                                        835.58, 833.46, 831.32, 829.19,
                                                                                        827.04, 824.89,
                                                                                        822.74, 820.58, 818.42, 816.25,
                                                                                        814.07, 811.89, 809.7,
                                                                                        807.51, 805.32, 803.11, 800.9,
                                                                                        798.69, 796.47, 794.25,
                                                                                        792.02, 789.78, 787.54, 785.29,
                                                                                        783.04, 780.78,
                                                                                        778.52, 776.25, 773.97, 771.69,
                                                                                        769.4, 767.11, 764.81,
                                                                                        762.51, 760.2, 757.88, 755.56,
                                                                                        753.23, 750.9, 748.56,
                                                                                        746.22, 743.87, 741.51, 739.15,
                                                                                        736.78, 734.41,
                                                                                        732.03, 729.64, 727.25, 724.85,
                                                                                        722.45, 720.04,
                                                                                        717.62, 715.2, 712.77, 710.34,
                                                                                        707.9, 705.45, 703.0,
                                                                                        700.54, 698.07, 695.6, 693.13,
                                                                                        690.64, 688.15, 685.66,
                                                                                        683.16, 680.65, 678.13, 675.61,
                                                                                        673.09, 670.55,
                                                                                        668.01, 665.47, 662.91, 660.36,
                                                                                        657.79, 655.22,
                                                                                        652.64, 650.06, 647.47, 644.87,
                                                                                        642.26, 639.65,
                                                                                        637.04, 634.41, 631.78, 629.15,
                                                                                        626.5, 623.85, 621.2,
                                                                                        618.53, 615.87, 613.19, 610.51,
                                                                                        607.82, 605.12,
                                                                                        602.42, 599.71, 596.99, 594.27,
                                                                                        591.54, 588.8, 586.05,
                                                                                        583.3, 580.55, 577.78, 575.01,
                                                                                        572.23, 569.45, 566.65,
                                                                                        563.85, 561.05, 558.23, 555.41,
                                                                                        552.59, 549.75,
                                                                                        546.91, 544.06, 541.2, 538.34,
                                                                                        535.47, 532.59, 529.71,
                                                                                        526.82, 523.92, 521.01, 518.1,
                                                                                        515.18, 512.25, 509.31,
                                                                                        506.37, 503.42, 500.46, 497.5,
                                                                                        494.53, 491.55, 488.56,
                                                                                        485.57, 482.56, 479.55, 476.54,
                                                                                        473.51, 470.48,
                                                                                        467.44, 464.39, 461.34, 458.27,
                                                                                        455.2, 452.13, 449.04,
                                                                                        445.95, 442.85, 439.74, 436.62,
                                                                                        433.5, 430.36, 427.22,
                                                                                        424.08, 420.92, 417.76, 414.58,
                                                                                        411.4, 408.22, 405.02,
                                                                                        401.82, 398.61, 395.39, 392.16,
                                                                                        388.92, 385.68,
                                                                                        382.43, 379.17, 375.9, 372.62,
                                                                                        369.34, 366.05, 362.75,
                                                                                        359.44, 356.12, 352.79, 349.46,
                                                                                        346.12, 342.77,
                                                                                        339.41, 336.04, 332.66, 329.28,
                                                                                        325.89, 322.49,
                                                                                        319.08, 315.66, 312.23, 308.79,
                                                                                        305.35, 301.9, 298.44,
                                                                                        294.97, 291.49, 288.0, 284.5,
                                                                                        281.0, 277.49, 273.96,
                                                                                        270.43, 266.89, 263.34, 259.79,
                                                                                        256.22, 252.64,
                                                                                        249.06, 245.47, 241.86, 238.25,
                                                                                        234.63, 231.0, 227.36,
                                                                                        223.72, 220.06, 216.39, 212.72,
                                                                                        209.04, 205.34,
                                                                                        201.64, 197.93, 194.21, 190.48,
                                                                                        186.74, 182.99,
                                                                                        179.23, 175.46, 171.68, 167.9,
                                                                                        164.1, 160.29, 156.48,
                                                                                        152.65, 148.82, 144.97, 141.12,
                                                                                        137.26, 133.38, 129.5,
                                                                                        125.61, 121.71, 117.8, 113.87,
                                                                                        109.94, 106.0, 102.05,
                                                                                        98.09, 94.12, 90.14, 86.15,
                                                                                        82.15, 78.14, 74.12,
                                                                                        70.09, 66.04, 61.99, 57.93,
                                                                                        53.86, 49.78, 45.69,
                                                                                        41.59, 37.47, 33.35, 29.22,
                                                                                        25.08, 20.92, 16.76,
                                                                                        12.59, 8.4, 4.21]}]
    mortgage_date_data = ['2022-10-01', '2022-11-01', '2022-12-01', '2023-01-01', '2023-02-01', '2023-03-01',
                          '2023-04-01', '2023-05-01', '2023-06-01', '2023-07-01', '2023-08-01', '2023-09-01',
                          '2023-10-01', '2023-11-01', '2023-12-01', '2024-01-01', '2024-02-01', '2024-03-01',
                          '2024-04-01', '2024-05-01', '2024-06-01', '2024-07-01', '2024-08-01', '2024-09-01',
                          '2024-10-01', '2024-11-01', '2024-12-01', '2025-01-01', '2025-02-01', '2025-03-01',
                          '2025-04-01', '2025-05-01', '2025-06-01', '2025-07-01', '2025-08-01', '2025-09-01',
                          '2025-10-01', '2025-11-01', '2025-12-01', '2026-01-01', '2026-02-01', '2026-03-01',
                          '2026-04-01', '2026-05-01', '2026-06-01', '2026-07-01', '2026-08-01', '2026-09-01',
                          '2026-10-01', '2026-11-01', '2026-12-01', '2027-01-01', '2027-02-01', '2027-03-01',
                          '2027-04-01', '2027-05-01', '2027-06-01', '2027-07-01', '2027-08-01', '2027-09-01',
                          '2027-10-01', '2027-11-01', '2027-12-01', '2028-01-01', '2028-02-01', '2028-03-01',
                          '2028-04-01', '2028-05-01', '2028-06-01', '2028-07-01', '2028-08-01', '2028-09-01',
                          '2028-10-01', '2028-11-01', '2028-12-01', '2029-01-01', '2029-02-01', '2029-03-01',
                          '2029-04-01', '2029-05-01', '2029-06-01', '2029-07-01', '2029-08-01', '2029-09-01',
                          '2029-10-01', '2029-11-01', '2029-12-01', '2030-01-01', '2030-02-01', '2030-03-01',
                          '2030-04-01', '2030-05-01', '2030-06-01', '2030-07-01', '2030-08-01', '2030-09-01',
                          '2030-10-01', '2030-11-01', '2030-12-01', '2031-01-01', '2031-02-01', '2031-03-01',
                          '2031-04-01', '2031-05-01', '2031-06-01', '2031-07-01', '2031-08-01', '2031-09-01',
                          '2031-10-01', '2031-11-01', '2031-12-01', '2032-01-01', '2032-02-01', '2032-03-01',
                          '2032-04-01', '2032-05-01', '2032-06-01', '2032-07-01', '2032-08-01', '2032-09-01',
                          '2032-10-01', '2032-11-01', '2032-12-01', '2033-01-01', '2033-02-01', '2033-03-01',
                          '2033-04-01', '2033-05-01', '2033-06-01', '2033-07-01', '2033-08-01', '2033-09-01',
                          '2033-10-01', '2033-11-01', '2033-12-01', '2034-01-01', '2034-02-01', '2034-03-01',
                          '2034-04-01', '2034-05-01', '2034-06-01', '2034-07-01', '2034-08-01', '2034-09-01',
                          '2034-10-01', '2034-11-01', '2034-12-01', '2035-01-01', '2035-02-01', '2035-03-01',
                          '2035-04-01', '2035-05-01', '2035-06-01', '2035-07-01', '2035-08-01', '2035-09-01',
                          '2035-10-01', '2035-11-01', '2035-12-01', '2036-01-01', '2036-02-01', '2036-03-01',
                          '2036-04-01', '2036-05-01', '2036-06-01', '2036-07-01', '2036-08-01', '2036-09-01',
                          '2036-10-01', '2036-11-01', '2036-12-01', '2037-01-01', '2037-02-01', '2037-03-01',
                          '2037-04-01', '2037-05-01', '2037-06-01', '2037-07-01', '2037-08-01', '2037-09-01',
                          '2037-10-01', '2037-11-01', '2037-12-01', '2038-01-01', '2038-02-01', '2038-03-01',
                          '2038-04-01', '2038-05-01', '2038-06-01', '2038-07-01', '2038-08-01', '2038-09-01',
                          '2038-10-01', '2038-11-01', '2038-12-01', '2039-01-01', '2039-02-01', '2039-03-01',
                          '2039-04-01', '2039-05-01', '2039-06-01', '2039-07-01', '2039-08-01', '2039-09-01',
                          '2039-10-01', '2039-11-01', '2039-12-01', '2040-01-01', '2040-02-01', '2040-03-01',
                          '2040-04-01', '2040-05-01', '2040-06-01', '2040-07-01', '2040-08-01', '2040-09-01',
                          '2040-10-01', '2040-11-01', '2040-12-01', '2041-01-01', '2041-02-01', '2041-03-01',
                          '2041-04-01', '2041-05-01', '2041-06-01', '2041-07-01', '2041-08-01', '2041-09-01',
                          '2041-10-01', '2041-11-01', '2041-12-01', '2042-01-01', '2042-02-01', '2042-03-01',
                          '2042-04-01', '2042-05-01', '2042-06-01', '2042-07-01', '2042-08-01', '2042-09-01',
                          '2042-10-01', '2042-11-01', '2042-12-01', '2043-01-01', '2043-02-01', '2043-03-01',
                          '2043-04-01', '2043-05-01', '2043-06-01', '2043-07-01', '2043-08-01', '2043-09-01',
                          '2043-10-01', '2043-11-01', '2043-12-01', '2044-01-01', '2044-02-01', '2044-03-01',
                          '2044-04-01', '2044-05-01', '2044-06-01', '2044-07-01', '2044-08-01', '2044-09-01',
                          '2044-10-01', '2044-11-01', '2044-12-01', '2045-01-01', '2045-02-01', '2045-03-01',
                          '2045-04-01', '2045-05-01', '2045-06-01', '2045-07-01', '2045-08-01', '2045-09-01',
                          '2045-10-01', '2045-11-01', '2045-12-01', '2046-01-01', '2046-02-01', '2046-03-01',
                          '2046-04-01', '2046-05-01', '2046-06-01', '2046-07-01', '2046-08-01', '2046-09-01',
                          '2046-10-01', '2046-11-01', '2046-12-01', '2047-01-01', '2047-02-01', '2047-03-01',
                          '2047-04-01', '2047-05-01', '2047-06-01', '2047-07-01', '2047-08-01', '2047-09-01',
                          '2047-10-01', '2047-11-01', '2047-12-01', '2048-01-01', '2048-02-01', '2048-03-01',
                          '2048-04-01', '2048-05-01', '2048-06-01', '2048-07-01', '2048-08-01', '2048-09-01',
                          '2048-10-01', '2048-11-01', '2048-12-01', '2049-01-01', '2049-02-01', '2049-03-01',
                          '2049-04-01', '2049-05-01', '2049-06-01', '2049-07-01', '2049-08-01', '2049-09-01',
                          '2049-10-01', '2049-11-01', '2049-12-01', '2050-01-01', '2050-02-01', '2050-03-01',
                          '2050-04-01', '2050-05-01', '2050-06-01', '2050-07-01', '2050-08-01', '2050-09-01',
                          '2050-10-01', '2050-11-01', '2050-12-01', '2051-01-01', '2051-02-01', '2051-03-01',
                          '2051-04-01', '2051-05-01', '2051-06-01', '2051-07-01', '2051-08-01', '2051-09-01',
                          '2051-10-01', '2051-11-01', '2051-12-01', '2052-01-01', '2052-02-01', '2052-03-01',
                          '2052-04-01', '2052-05-01', '2052-06-01', '2052-07-01', '2052-08-01', '2052-09-01']
    context = {
        'cash_on_cash_return_data': cash_on_cash_return_data,
        'projection_key': projection_key,
        'return_on_investment_data': return_on_investment_data,
        'debt_cov_ratio_data': debt_cov_ratio_data,
        'return_investment_data': return_investment_data,
        'property_expense_data': property_expense_data,
        'mortgage_date_data': mortgage_date_data,
        'mortgage_graph_data': mortgage_graph_data}

    return render(request, 'rental_prop_sample_page.html', context=context)


# Page Errors

def error_404(request, exception):
    data = {'error': 'Page Not Found!'}
    return render(request, 'error.html', data)


def error_500(request):
    data = {'error': 'Internal Server Error!'}
    return render(request, 'error.html', data)


def error_403(request, exception):
    data = {'error': 'Access Denied.!'}
    return render(request, 'error.html', data)


def error_400(request, exception):
    data = {'error': 'Bad Request!'}
    return render(request, 'error.html', data)
