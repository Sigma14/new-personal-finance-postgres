import os
import ast
import calendar
import csv
import datetime
import json
import logging
import os
import time
from collections import OrderedDict
from io import BytesIO
from itertools import chain
from openai import OpenAI

import bleach
import pandas as pd
import plaid
import pytz
import requests
from axes.decorators import axes_dispatch
from axes.utils import reset_request
from dateutil import relativedelta
from dateutil.relativedelta import relativedelta
from decouple import config
from django.conf import settings
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.staticfiles import finders
from django.db.models import Q
from django.http import (
    FileResponse,
    HttpResponse,
    HttpResponseNotAllowed,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
    FileResponse,
    HttpResponseNotFound
)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.timezone import localtime
from django.utils.translation import gettext as _
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from openai import OpenAI
from plaid import ApiClient
from plaid.api import plaid_api
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import (
    ItemPublicTokenExchangeRequest,
)
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.colors import PCMYKColor
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A0, A4, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Table, TableStyle
from reportlab.platypus.flowables import Spacer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from finance.settings import stock_app_url

from .constants import (
    BUDGET_KEYS,
    BUDGET_LABELS,
    CATEGORY_ICONS,
    CURRENCY_DICT,
    EXCLUDED_SUB_CATEGORIES,
    FUND_KEYS,
    INCOME_KEYS,
    INCOME_LABELS,
    INVOICE_KEYS,
    LOAN_TYPES,
    MAINTENANCE_KEYS,
    MONTH_DATE_DICT,
    MORTGAGE_ACCOUNT_TYPES,
    MORTGAGE_KEYS,
    MORTGAGE_KEYWORDS,
    PORTFOLIO_CURRENCY,
    PROPERTY_EXPENSES_KEYS,
    PROPERTY_KEYS,
    PROPERTY_TYPE_LIST,
    SCENARIO_DICT,
    SUB_CATEGORY_KEYS,
    SUGGESTED_SUB_CATEGORIES,
    TRANSACTION_KEYS,
    YEAR_LABELS,
)
from .enums import (
    AccountTypes,
    BudgetPeriods,
    CategoryTypes,
    DateFormats,
    InvoiceStatuses,
)
from .forms import (
    AccountForm,
    BillForm,
    BudgetForm,
    CategoryForm,
    ExpenseForm,
    LiabilityForm,
    MaintenanceForm,
    MortgageForm,
    TemplateBudgetForm,
    TransactionForm,
    UserBudgetsForm,
)
from .helper import (
    check_bill_is_due,
    check_subcategory_exists,
    create_bill_request,
    create_budget_request,
    create_income_request,
    dict_value_to_list,
    get_cmp_diff_data,
    get_list_of_months,
    get_period_date,
    get_template_budget,
    save_budgets,
    save_fund_obj,
    save_income,
    save_income_details,
    save_transaction,
    start_end_date,
)
from .models import (
    Account,
    AIChat,
    AppErrorLog,
    AvailableFunds,
    Bill,
    BillDetail,
    Budget,
    CapexBudgetDetails,
    Category,
    ClosingCostDetails,
    Expenses,
    ExpensesDetails,
    Feedback,
    Goal,
    Income,
    IncomeDetail,
    MortgageDetails,
    MyNotes,
    MyNotes,
    PlaidItem,
    Property,
    PropertyExpense,
    PropertyInvoice,
    PropertyMaintenance,
    PropertyPurchaseDetails,
    PropertyRentalInfo,
    RentalPropertyModel,
    RevenuesDetails,
    StockHoldings,
    SubCategory,
    SuggestiveCategory,
    Tag,
    TemplateBudget,
    Transaction,
    UserBudgets,
)
from .mortgage import calculate_tenure, calculator
from .sample_constants import (
    BUDGET_GRAPH_DATA,
    BUDGET_GRAPH_VALUE,
    BUDGET_NAMES,
    CASH_FLOW_DATA,
    CASH_FLOW_NAMES,
    GRAPH_LABELS,
    GRAPH_VALUES,
    SAMPLE_CASH_ON_CASH_RETURN_DATA,
    SAMPLE_DEBT_COV_RATIO_DATA,
    SAMPLE_MORTGAGE_DATE_DATA,
    SAMPLE_MORTGAGE_GRAPH_DATA,
    SAMPLE_PROJECTION_KEY,
    SAMPLE_PROPERTY_EXPENSE_DATA,
    SAMPLE_RETURN_INVESTMENT_DATA,
    SAMPLE_RETURN_ON_INVESTMENT_DATA,
)

# Move these dictionaries and lists to constant.py
today_date = datetime.date.today()

# plaid Intergration

# To-Do - Remove api creds
PLAID_API_KEY = json.loads(config("PLAID_API_KEY"))
configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox, api_key=PLAID_API_KEY
)
api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# open ai
open_ai_api_key = config("OPEN_AI_KEY")
ai_client = OpenAI(api_key=open_ai_api_key)

# CSV File links
Tour_APIs = json.loads(config("TOUR_API"))

# open ai
open_ai_api_key = config("OPEN_AI_KEY")
ai_client = OpenAI(api_key=open_ai_api_key)

# CSV File links
Tour_APIs = json.loads(config("TOUR_API"))


wordpress_domain = config("WORDPRESS_DOMAIN")
wordpress_api_key = config("WORDPRESS_API_KEY")


@ensure_csrf_cookie
def create_link_token(request):
    user = request.user
    client_user_id = user.id
    if user.is_authenticated:
        # Create a link_token for the given user
        request = LinkTokenCreateRequest(
            products=[Products("transactions")],
            client_name="Personal Finance App",
            country_codes=[CountryCode("US")],
            language="en",
            user=LinkTokenCreateRequestUser(
                client_user_id=str(client_user_id)),
        )
        response = client.link_token_create(request)
        response = response.to_dict()
        print("response==========>", response)
        link_token = response["link_token"]
        print("link_token====>", link_token)
        return JsonResponse({"link_token": link_token})
    else:
        return HttpResponseRedirect("/login")


def get_access_token(request):
    """
    Handles the exchange of a public token for an access token and updates
    the user's accounts.

    Args:
        request (HttpRequest): The HTTP request containing the user and body
        data.

    Returns:
        HttpResponseRedirect: Redirects the user to the login page if not
        authenticated.
    """
    global access_token
    user = request.user

    if user.is_authenticated:
        body_data = json.loads(request.body.decode())
        public_token = body_data["public_token"]
        accounts = body_data["accounts"]
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(request)
        access_token = exchange_response["access_token"]
        item_id = exchange_response["item_id"]
        plaid_item = None

        try:
            plaid_item = user.plaiditem_set.get(item_id=item_id)
        except:
            new_plaid_item = PlaidItem(
                user=user, access_token=access_token, item_id=item_id
            )
            new_plaid_item.save()
            plaid_item = user.plaiditem_set.get(item_id=item_id)

        print("accounts=============>", accounts)
        for account in accounts:
            try:
                existing_acct = user.account_set.get(
                    plaid_account_id=account["account_id"]
                )
                continue
            # To-Do - Remove  bare-except
            except:
                new_acct = Account()
                new_acct.plaid_account_id = account["id"]
                new_acct.balance = account["balances"]["current"]
                new_acct.available_balance = account["balances"]["available"]
                new_acct.mask = account["mask"]
                new_acct.name = account["name"]
                new_acct.subtype = account["subtype"]
                new_acct.account_type = account["type"]
                new_acct.user = user
                new_acct.item = plaid_item
                new_acct.save()

        # Pretty printing in development
        json.dumps(exchange_response, sort_keys=True, indent=4)
        print(exchange_response)

    return redirect("/login")


def get_transactions(request):
    user = request.user
    if user.is_authenticated:
        transactions = []
        plaid_items = user.plaiditem_set.all()
        if request.method == "POST":
            start_date = request.POST["start_date"]
            end_date = request.POST["end_date"]
        else:
            timespan_weeks = 4 * 24  # Plaid only goes back 24 months
            start_date = "{:%Y-%m-%d}".format(
                datetime.now() + datetime.timedelta(weeks=(-timespan_weeks))
            )
            end_date = "{:%Y-%m-%d}".format(datetime.now())
        for item in plaid_items:
            try:
                access_token = item.access_token
                request = TransactionsGetRequest(
                    access_token=access_token,
                    start_date=start_date,
                    end_date=end_date,
                    options=TransactionsGetRequestOptions(),
                )
                response = client.transactions_get(request)

                transactions = response["transactions"]
                accounts = response["accounts"]
                error = None

                for account in accounts:
                    try:
                        existing_acct = user.account_set.get(
                            plaid_account_id=account["account_id"]
                        )
                        continue
                    # To-Do  Remove bare except /
                    except Exception as e:
                        new_acct = Account()
                        new_acct.plaid_account_id = account["id"]
                        new_acct.balance = account["balances"]["current"]
                        new_acct.available_balance = account["balances"]["available"]
                        new_acct.mask = account["mask"]
                        new_acct.name = account["name"]
                        new_acct.subtype = account["subtype"]
                        new_acct.account_type = account["type"]
                        new_acct.user = user
                        new_acct.item = item
                        new_acct.save()

                while len(transactions) < response["total_transactions"]:
                    request = TransactionsGetRequest(
                        access_token=access_token,
                        start_date=start_date,
                        end_date=end_date,
                        options=TransactionsGetRequestOptions(
                            offset=len(transactions)),
                    )
                    response = client.transactions_get(request)
                    transactions.extend(response["transactions"])

                for transaction in transactions:
                    try:
                        existing_trans = user.transaction_set.get(
                            plaid_transaction_id=transaction["transaction_id"]
                        )
                        print("Transaction already exist")
                        continue
                    except Transaction.DoesNotExist:
                        category_name = transaction["category"]
                        if category_name:
                            try:
                                category_obj = Category.objects.get(
                                    user=user, name=category_name[-1]
                                )
                            # To-Do  Remove bare except
                            except:
                                category_obj = Category()
                                category_obj.user = user
                                category_obj.name = category_name[-1]
                                category_obj.save()
                        else:
                            category_obj = Category()
                            category_obj.user = user
                            category_obj.name = "Account Summary"
                            category_obj.save()

                        transaction_obj = Transaction()
                        transaction_obj.user = user
                        transaction_obj.amount = transaction["amount"]
                        transaction_obj.transaction_date = transaction["date"]
                        transaction_obj.categories = category_obj
                        transaction_obj.account = user.account_set.get(
                            plaid_account_id=transaction["account_id"]
                        )
                        transaction_obj.payee = transaction.get("name", "")
                        transaction_obj.tags = "Account Summary"
                        transaction_obj.cleared = True

                        transaction_obj.save()
            except Exception as e:
                print(e)
            # error = {'display_message': 'You need to link your account.' }
        json.dumps(transactions, sort_keys=True, indent=4)
        return HttpResponseRedirect("/", {"error": error, "transactions": transactions})
    else:
        return redirect("/login")


def check_zero_division(first_val, second_val):
    """
    Divides first_val by second_val, returning 0 if division by zero occurs.

    Args:
        first_val (float): The numerator.
        second_val (float): The denominator.

    Returns:
        float: The result of the division, or 0 if division by zero occurs.
    """
    try:
        return first_val / second_val
    except ZeroDivisionError:
        return 0


def save_rental_property(
    request,
    rental_obj,
    property_purchase_obj,
    mortgage_obj,
    closing_cost_obj,
    revenue_obj,
    expense_obj,
    capex_budget_obj,
    property_name,
    currency_name,
    user_name,
    property_image,
):
    # Investor Details
    investor_detail = others_costs_data(
        request.POST.getlist("investor_detail"))

    # Budget Details
    roof = request.POST.getlist("roof")
    water_heater = request.POST.getlist("water_heater")
    all_appliances = request.POST.getlist("all_appliances")
    bathroom = request.POST.getlist("bathroom")
    drive_way = request.POST.getlist("drive_way")
    furnace = request.POST.getlist("furnace")
    air_conditioner = request.POST.getlist("air_conditioner")
    flooring = request.POST.getlist("flooring")
    plumbing = request.POST.getlist("plumbing")
    electrical = request.POST.getlist("electrical")
    windows = request.POST.getlist("windows")
    paint = request.POST.getlist("paint")
    kitchen = request.POST.getlist("kitchen")
    structure = request.POST.getlist("structure")
    component = request.POST.getlist("component")
    landscaping = request.POST.getlist("landscaping")
    others_budgets = request.POST.getlist("other_budget")
    total_budget_cost = request.POST["total_budget_cost"]
    others_budgets_len = len(others_budgets)
    avg = 3
    others_budgets_list = []
    last = 0

    while last < others_budgets_len:
        others_budgets_list.append(others_budgets[int(last): int(last + avg)])
        last += avg

    others_budgets_dict = {}
    for val in others_budgets_list:
        others_budgets_dict[val[0]] = [float(val[1]), float(val[2])]

    # Property Purchase Details
    best_case = check_float(request.POST["best_case"])
    likely_case = check_float(request.POST["likely_case"])
    worst_case = check_float(request.POST["worst_case"])
    select_case = request.POST["select_case"]
    select_price = float(request.POST["select_price"])
    down_payment = check_float(request.POST["down_payment"])

    property_purchase_obj.user = user_name
    property_purchase_obj.best_case_price = best_case
    property_purchase_obj.likely_case_price = likely_case
    property_purchase_obj.worst_case_price = worst_case
    property_purchase_obj.selected_case = select_case
    property_purchase_obj.selected_price = select_price
    property_purchase_obj.down_payment = down_payment
    property_purchase_obj.save()

    # Mortgage Details
    interest_rate = check_float(request.POST["interest_rate"])
    amortization_year = int(check_float(request.POST["amortization_year"]))
    mortgage_start_date = request.POST["mortgage_start_date"]
    mortgage_obj.user = user_name
    mortgage_obj.interest_rate = interest_rate
    mortgage_obj.amortization_year = amortization_year
    mortgage_obj.start_date = mortgage_start_date
    mortgage_obj.save()

    # Closing Costs / Renovations Costs Details
    transfer_tax = check_float(request.POST["transfer_tax"])
    legal_fee = check_float(request.POST["legal_fee"])
    title_insurance = check_float(request.POST["title_insurance"])
    inspection = check_float(request.POST["inspection"])
    appraisal_fee = check_float(request.POST["appraisal_fee"])
    appliances = check_float(request.POST["appliances"])
    renovation_cost = check_float(request.POST["renovation_cost"])
    others_cost = others_costs_data(request.POST.getlist("other_cost"))
    down_payment_value = round(select_price * down_payment / 100, 2)
    total_investment = (
        down_payment_value
        + transfer_tax
        + legal_fee
        + title_insurance
        + inspection
        + appraisal_fee
        + appliances
        + renovation_cost
    )
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
    unit_1 = check_float(request.POST["unit_1"])
    others_revenue_cost = request.POST.getlist("others_revenue_cost")
    rent_increase_assumption = request.POST["rent_increase_assumption"]
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
    property_tax = check_float(request.POST["property_tax"])
    insurance = check_float(request.POST["insurance"])
    maintenance = check_float(request.POST["maintenance"])
    water = check_float(request.POST["water"])
    gas = check_float(request.POST["gas"])
    electricity = check_float(request.POST["electricity"])
    water_heater_rental = check_float(request.POST["water_heater_rental"])
    other_utilities = others_costs_data(
        request.POST.getlist("other_utilities"))
    management_fee = check_float(request.POST["management_fee"])
    vacancy = check_float(request.POST["vacancy"])
    capital_expenditure = check_float(request.POST["capital_expenditure"])
    other_expenses = others_costs_data(request.POST.getlist("other_expenses"))
    inflation_assumption = check_float(request.POST["inflation_assumption"])
    appreciation_assumption = check_float(
        request.POST["appreciation_assumption"])
    total_expenses = (
        property_tax
        + insurance
        + maintenance
        + water
        + gas
        + electricity
        + water_heater_rental
        + management_fee
        + vacancy
        + capital_expenditure
    )

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
    """
    Checks & converts data_var to a float, rounds it to two decimal places,
    and handles invalid input by returning 0.0.

    Args:
        data_var: The variable to be converted to a float.

    Returns:
        float: The converted and rounded float value, or 0.0 if conversion fails.
    """
    if data_var:
        try:
            data_var = round(float(data_var), 2)
        except ValueError:
            data_var = 0.0
    else:
        data_var = 0.0
    return data_var


def make_capex_budget(result_list):
    """
    Calculate the yearly and monthly capital expenditure budget.

    The function takes a list containing the total cost and the number of years,
    calculates the cost per year and per month, and appends these values to the
    list.

    Args:
        result_list (list): A list containing two elements. The first element is
                            the total cost (a float or string that can be
                            converted to a float), and the second element is the
                            number of years (an integer or string that can be
                            converted to an integer).

    Returns:
        list: The original list with the added yearly and monthly budget
              calculations, rounded to two decimal places.
    """
    try:
        # Attempt to calculate the cost per year
        cost_per_year = float(result_list[0]) / float(result_list[1])
    except (ValueError, ZeroDivisionError):
        # Sets cost per year to 0.0 if exception occurs
        cost_per_year = 0.0

    # Calculate the cost per month
    cost_per_month = cost_per_year / 12

    # Append the calculated yearly and monthly costs to the result list
    result_list.append(round(cost_per_year, 2))
    result_list.append(round(cost_per_month, 2))
    return result_list


def make_others_dict(other_unit_dict):
    """
    Converts the unit values in the dictionary to annual units.

    This function takes a dictionary where the values are numeric values
    representing units, multiplies each unit by 12 to convert to annual units,
    and updates the dictionary in place.

    Args:
        other_unit_dict (dict): A dictionary where the keys are identifiers
                                and the values are numeric values representing units.

    Returns:
        dict: The updated dictionary with annual unit values.
    """
    for key, units in other_unit_dict.items():
        other_unit_dict[key] = [float(units) * 12]
    return other_unit_dict


def make_other_data(other_unit_dict, year, mortgage_year, rent_increase_assumption):
    """
    Updates unit values based on rent increase assumption.

    Args:
        other_unit_dict (dict): Dictionary with lists of unit values.
        year (int): Current year.
        mortgage_year (int): Year when mortgage ends.
        rent_increase_assumption (float): Annual rent increase percentage.

    Returns:
        dict: Updated dictionary with increased unit values.
    """
    for key, unit_value in other_unit_dict.items():
        current_unit = unit_value[-1]
        other_unit_value_increase = round(
            (current_unit * rent_increase_assumption / 100) + current_unit, 2
        )
        if year != int(mortgage_year):
            unit_value.append(other_unit_value_increase)
            other_unit_dict[key] = unit_value
    return other_unit_dict


def update_budget_items(
    user_name,
    budget_obj,
    transaction_amount,
    transaction_out_flow,
    transaction_date,
    update_transaction_amount=None,
):
    """
    Updates budget item based on transaction details.

    Args:
        user_name (str): The username of the budget owner.
        budget_obj (Budget): The budget object to update.
        transaction_amount (float): The amount of the transaction.
        transaction_out_flow (bool): Indicates if the transaction is an outflow.
        transaction_date (datetime): The date of the transaction.
        update_transaction_amount (float, optional): An additional amount to update.

    Returns:
        Budget: The updated budget object.
    """
    amount_budget = float(budget_obj.amount)
    spent_budget = round(float(budget_obj.budget_spent) -
                         transaction_amount, 2)
    if update_transaction_amount:
        spent_budget += update_transaction_amount

    period_budget = budget_obj.budget_period

    # Handle case where category is income and adjust transaction flow
    if budget_obj.category.category.name == CategoryTypes.INCOME.value:
        transaction_out_flow = True

    if transaction_out_flow:
        # Update spent budget for outflow transactions
        budget_obj.budget_spent = spent_budget

        # Handle yearly and quarterly budget periods
        if period_budget in (BudgetPeriods.YEARLY.value, BudgetPeriods.QUARTERLY.value):
            budget_left = float(budget_obj.budget_left) + transaction_amount
            budget_obj.budget_left = budget_left - update_transaction_amount
            print("budget_obj.budget_left", budget_obj.budget_left)
            data_budget = Budget.objects.filter(
                user=user_name,
                name=budget_obj.name,
                created_at=budget_obj.created_at,
                ended_at=budget_obj.ended_at,
            )
            for budget_value in data_budget:
                if budget_value.start_date != budget_obj.start_date:
                    budget_value.budget_left = budget_obj.budget_left
                    budget_value.save()

        # Handle daily and weekly budget periods
        if period_budget in (BudgetPeriods.DAILY.value, BudgetPeriods.WEEKLY.value):
            try:
                budget_obj = Budget.objects.get(
                    user=user_name,
                    name=budget_obj.name,
                    created_at__lte=transaction_date,
                    ended_at__gte=transaction_date,
                )
                amount_budget = float(budget_obj.amount)
                spent_budget = round(
                    float(budget_obj.budget_spent) - transaction_amount, 2
                )
                if update_transaction_amount:
                    spent_budget += update_transaction_amount
                budget_obj.budget_spent = spent_budget
            except Exception as e:
                print("Exception=========>", e)
        # Update budget left for non-yearly/quarterly periods
        if period_budget not in (
            BudgetPeriods.YEARLY.value,
            BudgetPeriods.QUARTERLY.value,
        ):
            budget_obj.budget_left = round(amount_budget - spent_budget, 2)
    else:
        # Handle inflow transactions and update amount and budget left
        budget_obj.amount = round(amount_budget - transaction_amount, 2)
        budget_obj.budget_left = round(
            float(budget_obj.budget_left) - transaction_amount, 2
        )

        if period_budget in (BudgetPeriods.YEARLY.value, BudgetPeriods.QUARTERLY.value):
            data_budget = Budget.objects.filter(
                user=user_name,
                name=budget_obj.name,
                created_at=budget_obj.created_at,
                ended_at=budget_obj.ended_at,
            )
            for budget_value in data_budget:
                if budget_value.start_date != budget_obj.start_date:
                    budget_value.amount = budget_obj.amount
                    budget_value.budget_left = budget_obj.budget_left
                    budget_value.save()

    return budget_obj


def add_new_budget_items(
    user_name, budget_obj, transaction_amount, out_flow, transaction_date=None
):
    """
    Adds new budget items based on transaction details.

    Args:
        user_name (str): The username of the budget owner.
        budget_obj (Budget): The budget object to be updated.
        transaction_amount (float): The amount of the transaction.
        out_flow (str): Indicates if the transaction is an outflow ("True") or not.
        transaction_date (datetime, optional): The date of the transaction.

    Returns:
        Budget: The updated budget object.
    """
    amount_budget = float(budget_obj.amount)
    spent_budget = round(float(budget_obj.budget_spent) +
                         transaction_amount, 2)
    period_budget = budget_obj.budget_period
    if budget_obj.category.category.name == CategoryTypes.INCOME.value:
        out_flow = "True"

    if out_flow == "True":
        # Update spent budget for outflow transactions
        budget_obj.budget_spent = spent_budget

        # Handle yearly and quarterly budget periods
        if period_budget in (BudgetPeriods.YEARLY.value, BudgetPeriods.QUARTERLY.value):
            data_budget = Budget.objects.filter(
                user=user_name,
                name=budget_obj.name,
                created_at=budget_obj.created_at,
                ended_at=budget_obj.ended_at,
            )
            for budget_value in data_budget:
                if budget_value.start_date != budget_obj.start_date:
                    spent_budget += float(budget_value.budget_spent)

            for budget_value in data_budget:
                if budget_value.start_date != budget_obj.start_date:
                    budget_value.budget_left = round(
                        amount_budget - spent_budget, 2)
                    budget_value.save()

        # Handle daily and weekly budget periods
        if period_budget in (BudgetPeriods.DAILY.value, BudgetPeriods.WEEKLY.value):
            try:
                budget_obj = Budget.objects.get(
                    user=user_name,
                    name=budget_obj.name,
                    created_at__lte=transaction_date,
                    ended_at__gte=transaction_date,
                )
                amount_budget = float(budget_obj.amount)
                spent_budget = round(
                    float(budget_obj.budget_spent) + transaction_amount, 2
                )
                budget_obj.budget_spent = spent_budget
            except Exception as e:
                print("Exception=========>", e)
        budget_obj.budget_left = round(amount_budget - spent_budget, 2)
    else:
        # Handle Inflow transactions
        budget_obj.amount = round(amount_budget + transaction_amount, 2)
        budget_obj.budget_left = round(
            float(budget_obj.budget_left) + transaction_amount, 2
        )

        if period_budget in (BudgetPeriods.YEARLY.value, BudgetPeriods.QUARTERLY.value):
            data_budget = Budget.objects.filter(
                user=user_name,
                name=budget_obj.name,
                created_at=budget_obj.created_at,
                ended_at=budget_obj.ended_at,
            )
            for budget_value in data_budget:
                if budget_value.start_date != budget_obj.start_date:
                    budget_value.amount = budget_obj.amount
                    budget_value.budget_left = budget_obj.budget_left
                    budget_value.save()

    return budget_obj


# Unused
# def add_remains_budget(user_name):
#     minimum_budget_date = Budget.objects.filter(user=user_name).order_by('start_date')
#     if minimum_budget_date:
#         if minimum_budget_date[0].start_date:
#             min_date = minimum_budget_date[0].start_date
#             max_date = minimum_budget_date[len(minimum_budget_date) - 1].start_date
#             budget_date_list = list(OrderedDict(((min_date + datetime.timedelta(_)).replace(day=1), None) for _ in
#                                                 range((max_date - min_date).days + 1)).keys())
#             budget_date_list = list(dict.fromkeys(budget_date_list))
#             budgets_names = get_budgets(user_name)
#             for date_val in budget_date_list:
#                 date_end = date_val.replace(day=calendar.monthrange(date_val.year, date_val.month)[1])
#                 for name in budgets_names:
#                     budgets_data = Budget.objects.filter(user=user_name, name=name, start_date=date_val,
#                                                          end_date=date_end)
#                     check_budget_data = Budget.objects.filter(user=user_name, name=name)[0]
#                     check_currency = check_budget_data.currency
#                     check_period = check_budget_data.budget_period
#                     check_auto = check_budget_data.auto_budget
#                     if not budgets_data:
#                         save_budgets(user_name, date_val, date_end, name, check_period, check_currency, 0, check_auto,
#                                      None, None, 0)


# def get_budgets(user_name):
#     budget_data = Budget.objects.filter(user=user_name)
#     budget_names = []
#     for value in budget_data:
#         budget_names.append(value.name)
#
#     return list(dict.fromkeys(budget_names))


def compare_budgets(user_name, start, end, budget_names_list):
    """
    Compares budgets and transactions over a specified period.

    Args:
        user_name (str): The username of the budget owner.
        start (datetime): Start date of the comparison period.
        end (datetime): End date of the comparison period.
        budget_names_list (list): List of budget names to compare.

    Returns:
        tuple:
            - transaction_budget (QuerySet): Transactions within the period.
            - total_budget_summary (list): Total spent and left budget.
            - cmp_budgets_dict (dict): Budget comparison details.
            - cmp_transaction_budgets (list): List of transactions per budget.
    """
    total_budget_amount = 0
    total_budget_spent = 0

    # Calculate comparison months
    month_cmp_start, month_end = start_end_date(
        start, BudgetPeriods.MONTHLY.value)
    month_cmp_end, month_end = start_end_date(end, BudgetPeriods.MONTHLY.value)
    list_of_cmp_months = []
    yearly_check_list = []
    quarterly_check_list = []
    cmp_total_budget_amount_dict = {}
    cmp_total_budget_spent_dict = {}
    cmp_budgets_dict = {}
    cmp_transaction_budgets = []

    # Initialize budget dictionaries
    for budget_name in budget_names_list:
        transaction_budget = Transaction.objects.filter(
            user=user_name,
            budgets__name=budget_name,
            transaction_date__range=(start, end),
        ).order_by("transaction_date")
        cmp_transaction_budgets.append(transaction_budget)
        cmp_total_budget_amount_dict[budget_name] = 0
        cmp_total_budget_spent_dict[budget_name] = 0
        cmp_budgets_dict[budget_name] = []

    # Generate list of comparison months
    while month_cmp_start <= month_cmp_end:
        list_of_cmp_months.append(month_cmp_start)
        month_cmp_start += relativedelta(months=1)

    # Compare budget data
    for cmp_month in list_of_cmp_months:
        budget_data = Budget.objects.filter(
            user=user_name, start_date=cmp_month)
        for data in budget_data:
            if data.name not in cmp_budgets_dict:
                cmp_budgets_dict[data.name] = []
                cmp_total_budget_amount_dict[data.name] = 0
                cmp_total_budget_spent_dict[data.name] = 0

            amount_budget = round(float(data.amount), 2)
            amount_budget_left = round(float(data.budget_left), 2)
            amount_budget_spent = round(float(data.budget_spent), 2)

            # Handle non-quarterly and non-yearly budgets
            if data.budget_period not in (
                BudgetPeriods.QUARTERLY.value,
                BudgetPeriods.YEARLY.value,
            ):
                if data.budget_status:
                    if amount_budget_spent != 0.0:
                        total_budget_amount += amount_budget_spent
                        cmp_total_budget_amount_dict[data.name] += amount_budget_spent
                else:
                    total_budget_amount += amount_budget
                    cmp_total_budget_amount_dict[data.name] += amount_budget

            else:
                check_end_date = data.ended_at
                # Handle quarterly budgets
                if data.budget_period == BudgetPeriods.QUARTERLY.value:
                    if check_end_date not in quarterly_check_list:
                        if data.budget_status:
                            if amount_budget_spent != 0.0:
                                if amount_budget_left < 0:
                                    total_budget_amount += amount_budget
                                    cmp_total_budget_amount_dict[
                                        data.name
                                    ] += amount_budget_spent
                                else:
                                    diff_budget = amount_budget - amount_budget_left
                                    total_budget_amount += diff_budget
                                    cmp_total_budget_amount_dict[
                                        data.name
                                    ] += diff_budget
                        else:
                            total_budget_amount += amount_budget
                            cmp_total_budget_amount_dict[data.name] += amount_budget
                        quarterly_check_list.append(data.ended_at)

                else:
                    # Handle yearly budgets
                    if check_end_date not in yearly_check_list:
                        if data.budget_status:
                            if amount_budget_spent != 0.0:
                                if amount_budget_left < 0:
                                    total_budget_amount += amount_budget
                                    cmp_total_budget_amount_dict[
                                        data.name
                                    ] += amount_budget
                                else:
                                    diff_budget = amount_budget - amount_budget_left
                                    total_budget_amount += diff_budget
                                    cmp_total_budget_amount_dict[
                                        data.name
                                    ] += diff_budget
                        else:
                            total_budget_amount += amount_budget
                            cmp_total_budget_amount_dict[data.name] += amount_budget
                        yearly_check_list.append(check_end_date)

    # Calculate total spent and left budget
    transaction_budget = Transaction.objects.filter(
        user=user_name, budgets__id__isnull=False, transaction_date__range=(start, end)
    ).order_by("transaction_date")

    if transaction_budget:
        for trans_data in transaction_budget:
            total_budget_spent += float(trans_data.amount)
            cmp_total_budget_spent_dict[trans_data.budgets.name] += float(
                trans_data.amount
            )

    for key in cmp_budgets_dict:
        cmp_total_budget_left = (
            cmp_total_budget_amount_dict[key] -
            cmp_total_budget_spent_dict[key]
        )
        cmp_budgets_dict[key].append(cmp_total_budget_spent_dict[key])
        cmp_budgets_dict[key].append(cmp_total_budget_left)

    total_budget_left = total_budget_amount - total_budget_spent

    return (
        transaction_budget,
        [total_budget_spent, total_budget_left],
        cmp_budgets_dict,
        cmp_transaction_budgets,
    )


def transaction_summary(transaction_data, select_filter, user_name):
    """
    Summarizes transaction data for generating graphs and reports.

    Args:
        transaction_data (QuerySet): List of transactions to summarize.
        select_filter (str): Filter criteria for selecting transactions.
        user_name (str): Username for fetching tags.

    Returns:
        dict: Context dictionary with summarized transaction data and tags.
    """
    credit_date_dict = {}
    debit_date_dict = {}
    credit_date_list = []
    debit_date_list = []
    date_list = []
    tags_data = []
    start_date = ""
    end_date = ""

    # Process each transaction and categorize by date and flow
    for transaction_name in transaction_data:
        if transaction_name.cleared:
            transaction_date = str(transaction_name.transaction_date)
            transaction_amount = transaction_name.amount
            if transaction_name.out_flow:
                if transaction_date in debit_date_dict:
                    debit_date_dict[transaction_date] += float(
                        transaction_amount)
                else:
                    debit_date_dict[transaction_date] = float(
                        transaction_amount)

            else:
                if transaction_date in credit_date_dict:
                    credit_date_dict[transaction_date] += float(
                        transaction_amount)
                else:
                    credit_date_dict[transaction_date] = float(
                        transaction_amount)
            date_list.append(str(transaction_date))

    date_list = list(dict.fromkeys(date_list))
    if transaction_data:
        start_date = date_list[-1]
        end_date = date_list[0]

    # Fetch tags for the user
    tags_data = list(Tag.objects.filter(
        user=user_name).values_list("name", flat=True))
    tags_data.insert(0, "All")
    for value in date_list:
        if value in debit_date_dict:
            debit_date_list.append(debit_date_dict[value])
            if value not in credit_date_dict:
                credit_date_list.append(0)
        if value in credit_date_dict:
            credit_date_list.append(credit_date_dict[value])
            if value not in debit_date_dict:
                debit_date_list.append(0)

    context = {
        "transaction_key": TRANSACTION_KEYS[:-1],
        "transaction_key_dumbs": json.dumps(TRANSACTION_KEYS[:-1]),
        "transaction_data": transaction_data,
        "tags_data": tags_data,
        "select_filter": select_filter,
        "debit_graph_data": debit_date_list,
        "credit_graph_data": credit_date_list,
        "transaction_date_data": date_list,
        "transaction_date_data_dumbs": json.dumps(date_list),
        "debit_graph_data_dumbs": json.dumps(debit_date_list),
        "credit_graph_data_dumbs": json.dumps(credit_date_list),
        "start_date": start_date,
        "end_date": end_date,
    }

    return context


def transaction_checks(
    username,
    transaction_amount,
    account,
    bill_name,
    budget_name,
    cleared_amount,
    out_flow,
    transaction_date,
    user_budget,
):
    """
    Processes a transaction by updating account, bill, and budget information.

    Args:
        username (str): The username of the user.
        transaction_amount (float): Amount of the transaction.
        account (str): Account name where the transaction occurred.
        bill_name (str): Optional bill associated with the transaction.
        budget_name (str): Optional budget for updating budget information.
        cleared_amount (str): Status of whether the amount is cleared ("True"/"False").
        out_flow (str): Indicator if the transaction is an outflow ("True"/"False").
        transaction_date (str): Date of the transaction in YYYY-MM-DD format.
        user_budget (int): ID of the user's budget.

    Returns:
        tuple: Updated account and budget objects.
    """
    if cleared_amount == "True":
        # Retrieve the account object
        account_obj = Account.objects.get(user=username, name=account)

        # Determine the bill object if passed
        if bill_name:
            bill_obj = bill_name
        else:
            bill_obj = False

        # Fetches user budget to filter the Budget Categories
        if budget_name and budget_name != "None":
            user_budget = UserBudgets.objects.get(
                user=username, pk=int(user_budget))
            date_check = datetime.datetime.strptime(
                transaction_date, DateFormats.YYYY_MM_DD.value
            ).date()
            start_month_date, end_month_date = start_end_date(
                date_check, BudgetPeriods.MONTHLY.value
            )
            budget_obj = Budget.objects.filter(
                user=username,
                user_budget=user_budget,
                name=budget_name,
                start_date=start_month_date,
                end_date=end_month_date,
            )
            if budget_obj:
                budget_obj = budget_obj[0]
            else:
                budget_obj = False
        else:
            budget_obj = False

        # Update account balance
        if out_flow == "True":
            account_obj.available_balance = round(
                float(account_obj.available_balance) - transaction_amount, 2
            )
        else:
            account_obj.available_balance = round(
                float(account_obj.available_balance) + transaction_amount, 2
            )

        # Update bill status and amount
        if bill_obj:
            bill_amount = round(float(bill_obj.remaining_amount), 2)
            if transaction_amount == bill_amount:
                bill_obj.status = "paid"
                bill_obj.remaining_amount = bill_amount - transaction_amount
            else:
                bill_obj.status = "unpaid"
                bill_obj.remaining_amount = bill_amount - transaction_amount
            bill_obj.save()

        # Update budget details
        if budget_obj:
            budget_obj = add_new_budget_items(
                username, budget_obj, transaction_amount, out_flow, date_check
            )
            budget_obj.save()

        # Update transaction count for the account
        account_obj.transaction_count += 1
        account_obj.save()
        return account_obj, budget_obj


def category_spent_amount(
    category_data, user_name, categories_name, categories_value, total_spent_amount
):
    """
    Calculates spent amounts for categories and updates lists and dicts.

    Args:
        category_data (QuerySet): Categories to calculate amounts for.
        user_name (str): Username for filtering transactions.
        categories_name (list): List to append category names.
        categories_value (list): List to append spent amounts for categories.
        total_spent_amount (dict): Dict to update total spent amounts by currency.

    Returns:
        None: Updates the provided lists and dictionary in place.
    """
    # Iterate through each category
    for category_name in category_data:
        spent_value = 0

        # Filter transactions for the current category
        category_transaction_data = Transaction.objects.filter(
            user=user_name, categories__category=category_name, out_flow=True
        )
        for transaction_data in category_transaction_data:
            spent_value += float(transaction_data.amount)
            # Sum up the spent amounts for the category
            if transaction_data.account.currency in total_spent_amount:
                total_spent_amount[transaction_data.account.currency] += float(
                    transaction_data.amount
                )
            else:
                total_spent_amount[transaction_data.account.currency] = float(
                    transaction_data.amount
                )

        # Append category name and spent amount if spent value is non-zero
        if spent_value != 0:
            categories_name.append(category_name.name)
            categories_value.append(spent_value)


def multi_acc_chart(
    acc_transaction_data,
    amount_date_dict,
    acc_current_balance,
    account_date_list,
    acc_create_date,
    account_transaction_value,
    acc_available_balance,
):
    """
    Updates account balance and transaction values for a chart.

    Args:
        acc_transaction_data (QuerySet): Transactions to process.
        amount_date_dict (dict): Dictionary mapping dates to account balances.
        acc_current_balance (float): Current balance of the account.
        account_date_list (list): List of dates for the chart.
        acc_create_date (str): Account creation date (not used in current code).
        account_transaction_value (list): List to append balance values.
        acc_available_balance (float): Initial available balance.

    Returns:
        None: Updates provided lists and dictionary in place.
    """
    # Process each transaction
    for data in acc_transaction_data:
        if data.cleared:
            acc_date = str(data.transaction_date)
            acc_transaction_amount = data.amount

            # Update current balance based on transaction type
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

    # Initialize balance for dates not in amount_date_dict
    amount_constant = acc_available_balance
    for date_value in account_date_list:
        check_date = datetime.datetime.strptime(
            date_value, DateFormats.YYYY_MM_DD.value
        ).date()
        check_date = datetime.datetime.strptime(
            date_value, DateFormats.YYYY_MM_DD.value
        ).date()
        if date_value in amount_date_dict:
            account_transaction_value.append(amount_date_dict[date_value])
            amount_constant = amount_date_dict[date_value]
        else:
            account_transaction_value.append(amount_constant)


def net_worth_cal(
    account_data, property_data, date_range_list, stock_portfolio_data, fun_name=None
):
    """
    Calculates net worth and associated financial data.

    Args:
        account_data (QuerySet): User account data.
        property_data (QuerySet): User property data.
        date_range_list (list): List of dates for the calculation period.
        stock_portfolio_data (QuerySet): User stock portfolio data.
        fun_name (str, optional): Function name to control the return value.

    Returns:
        dict or tuple: Net worth dictionary or a tuple of multiple financial data.
    """
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

    # Process account data for assets and liabilities
    for data in account_data:
        if data.include_net_worth:
            transaction_data = Transaction.objects.filter(account__pk=data.pk).order_by(
                "transaction_date"
            )[::-1]
            current_balance = float(data.available_balance)
            balance_graph_dict = {}
            balance_graph_data = []
            date_list = []

            # Handle non-mortgage accounts
            if data.account_type not in MORTGAGE_ACCOUNT_TYPES:
                if fun_name != "dash_board":
                    overtime_account_data(
                        transaction_data,
                        current_balance,
                        balance_graph_dict,
                        date_list,
                        balance_graph_data,
                        date_range_list,
                    )
                    asset_currency_balance.append(
                        {data.currency: balance_graph_data[::-1]}
                    )
                assets_data.append(
                    [data.name, data.currency +
                        data.available_balance, data.created_at]
                )
                if data.currency in total_asset_amount_dict:
                    total_asset_amount_dict[data.currency] = round(
                        total_asset_amount_dict[data.currency]
                        + float(data.available_balance),
                        2,
                    )
                else:
                    currency_count_list.append(data.currency)
                    total_asset_amount_dict[data.currency] = round(
                        float(data.available_balance), 2
                    )
            else:
                # Handle mortgage accounts
                liability_data.append(
                    [
                        data.name,
                        data.currency + data.available_balance,
                        data.account_type,
                        data.created_at,
                    ]
                )
                if data.currency in total_liability_dict:
                    total_liability_dict[data.currency] = round(
                        total_liability_dict[data.currency]
                        + float(data.available_balance),
                        2,
                    )
                else:
                    currency_count_list.append(data.currency)
                    total_liability_dict[data.currency] = round(
                        float(data.available_balance), 2
                    )
                if fun_name != "dash_board":
                    overtime_account_data(
                        transaction_data,
                        current_balance,
                        balance_graph_dict,
                        date_list,
                        balance_graph_data,
                        date_range_list,
                    )
                    liability_currency_balance.append(
                        {data.currency: balance_graph_data[::-1]}
                    )

    for data in property_data:
        if data.include_net_worth:
            if data.currency in total_property_dict:
                total_property_dict[data.currency] = round(
                    total_property_dict[data.currency] + float(data.value), 2
                )
            else:
                currency_count_list.append(data.currency)
                total_property_dict[data.currency] = round(
                    float(data.value), 2)

            property_currency_balance.append({data.currency: data.value})

    # Update stock portfolio values if outdated
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
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0"
            }
            print("my_portfolio_url===>", my_portfolio_url)
            url_response = requests.post(
                my_portfolio_url,
                headers=headers,
                data={"user_name": data.user.username, "port_id": data.port_id},
                timeout=500,
            )
            print("url_response=====>", url_response)
            my_portfolio_context = url_response.json()
            print("my_portfolio_context=====>", my_portfolio_context)
            data.name = my_portfolio_context["name"]
            data.value = my_portfolio_context["value"]
            data.save()
        if data.currency in total_portfolio_dict:
            total_portfolio_dict[data.currency] = round(
                total_portfolio_dict[data.currency] + float(data.value), 2
            )
        else:
            currency_count_list.append(data.currency)
            total_portfolio_dict[data.currency] = round(float(data.value), 2)
        portfolio_currency_balance.append({data.currency: data.value})

    # Calculate net worth per currency
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
        net_worth_dict[name] = (
            total_assets + total_property + total_portfolio - total_liability
        )

    print("total_assets=============>", total_assets)
    print("total_liability=============>", total_liability)
    print("total_portfolio=============>", total_portfolio)
    print("net_worth_dict=============>", net_worth_dict)
    if fun_name == "dash_board":
        return net_worth_dict
    else:
        return (
            net_worth_dict,
            assets_data,
            liability_data,
            total_asset_amount_dict,
            total_liability_dict,
            total_property_dict,
            asset_currency_balance,
            liability_currency_balance,
            property_currency_balance,
            total_currency_list,
            date_range_list,
            portfolio_currency_balance,
            total_portfolio_dict,
        )


def overtime_account_data(
    transaction_data,
    current_balance,
    balance_graph_dict,
    date_list,
    balance_graph_data,
    date_range_list,
):
    """
    Updates balance graph data over time based on transactions.

    Args:
        transaction_data (QuerySet): User's transaction data.
        current_balance (float): Current balance of the account.
        balance_graph_dict (dict): Dictionary to track balance over time.
        date_list (list): List of dates for transactions.
        balance_graph_data (list): List to store balance graph data.
        date_range_list (list): List of dates for the graph.
    """
    # Initialize index for the account's transactions
    account_index = 1
    for data in transaction_data:
        # Handle the first transaction separately
        if account_index == 1:
            balance_graph_dict[str(data.transaction_date)
                               ] = round(current_balance, 2)
            print(balance_graph_dict)
            if data.out_flow:
                amount_list = [float("-" + data.amount)]
                current_balance += float(data.amount)
            else:
                amount_list = [float(data.amount)]
                current_balance -= float(data.amount)
            date_list.append(str(data.transaction_date))

        else:
            # Update balance for existing dates
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
                balance_graph_dict[str(data.transaction_date)] = round(
                    result_value, 2)
            else:
                # Handle new dates
                balance_graph_dict[str(data.transaction_date)] = round(
                    current_balance, 2
                )
                date_list.append(str(data.transaction_date))

                if data.out_flow:
                    amount_list = [float("-" + data.amount)]
                    current_balance += float(data.amount)
                else:
                    amount_list = [float(data.amount)]
                    current_balance -= float(data.amount)
        account_index += 1  # Move to the next transaction
    date_range_index = 1  # Initialize index for the date range list

    if balance_graph_dict:
        # Update balance graph data for all dates in the date range
        balance_key = list(balance_graph_dict.keys())[-1]
        if sum(amount_list) < 0:
            starting_balance = balance_graph_dict[balance_key] - \
                sum(amount_list)
        else:
            starting_balance = balance_graph_dict[balance_key] + \
                sum(amount_list)

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
                    # To-Do  Remove bare except
                    except:
                        balance_graph_data.append(
                            balance_graph_dict[balance_key])
            date_range_index += 1
    else:
        for date_value in date_range_list:
            balance_graph_data.append(round(current_balance, 2))


# Personal Finance Home Page
@login_required(login_url="/login")
def home(request):
    """
    Renders the home page with context data.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML response for the home page.
    """
    # trans = translate(language='fr')
    context = {"page": "home",
               "tour_api": Tour_APIs["personal_finance_dashboard"]}
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
    """
    Renders the real estate home page with context data.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML response for the real estate home page.
    """
    context = {"page": "real_estate_home"}
    return render(request, "real_estate_home.html", context)


@login_required(login_url="/login")
def dash_board(request):
    """
    Renders the dashboard page with various financial summaries and charts.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML response for the dashboard page.
    """
    user_name = request.user

    # Check if the user is authenticated
    if not request.user.is_anonymous:
        # Retrieve various types of data for the dashboard
        categories = Category.objects.filter(user=user_name)
        all_transaction_data = Transaction.objects.filter(user=user_name).order_by(
            "transaction_date"
        )
        accounts_data = Account.objects.filter(
            user=user_name, account_type__in=AccountTypes.list()
        )
        property_data = Property.objects.filter(user=user_name)
        stock_portfolio_data = StockHoldings.objects.filter(user=user_name)
        budget_data = Budget.objects.filter(user=user_name)
        bills_data = Bill.objects.filter(user=user_name)
        # income_data = Income.objects.filter(user=user_name)

        # Initialize lists and dictionaries for dashboard data
        budget_label = []
        budget_values = []
        total_account_balance = {}
        total_spent_amount = {}
        categories_name = []
        categories_value = []
        acc_graph_data = []
        acc_min_max_value_list = []
        property_currency_balance = []
        income_label = []
        income_values = []
        bill_graph_dict = {}
        bill_label = []
        bill_values = []
        budget_spent_dict = {}
        income_spent_dict = {}

        # Calculate bill amounts and prepare graph data
        for bill in bills_data:
            bill_name = bill.bill_details.label
            if bill_name not in bill_graph_dict:
                bill_graph_dict[bill_name] = 0
                bill_transactions = all_transaction_data.filter(
                    categories__category__name=CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value,
                    categories__name=bill_name,
                    out_flow=True,
                )
                if bill_transactions:
                    for bill_t in bill_transactions:
                        bill_graph_dict[bill_name] += float(bill_t.amount)

        for key, value in bill_graph_dict.items():
            bill_label.append(key)
            bill_values.append(value)

        # Prepare account-related data for graph plotting
        if accounts_data and all_transaction_data:
            account_min_date = accounts_data[0].created_at.date()
            transaction_min_date = all_transaction_data[0].transaction_date
            if transaction_min_date < account_min_date:
                min_date = transaction_min_date
            else:
                min_date = account_min_date
            max_date = datetime.datetime.today().date()
            day_diff = (max_date - min_date).days
            account_date_list = [
                str(max_date - datetime.timedelta(days=x)) for x in range(day_diff)
            ]
            account_date_list.append(str(min_date))
            account_date_list = account_date_list[::-1]
            for acc_obj in accounts_data:
                if acc_obj.currency in total_account_balance:
                    total_account_balance[acc_obj.currency] = total_account_balance[
                        acc_obj.currency
                    ] + float(acc_obj.available_balance)
                else:
                    total_account_balance[acc_obj.currency] = float(
                        acc_obj.available_balance
                    )
                account_transaction_value = []
                acc_create_date = acc_obj.created_at.date()
                amount_date_dict = {}
                if acc_obj.lock_amount:
                    acc_current_balance = float(acc_obj.balance) - float(
                        acc_obj.lock_amount
                    )
                else:
                    acc_current_balance = float(acc_obj.balance)

                acc_available_balance = float(acc_current_balance)
                acc_transaction_data = Transaction.objects.filter(
                    user=user_name, account__pk=acc_obj.pk
                ).order_by("transaction_date")

                # Calculate balance over time for each account
                multi_acc_chart(
                    acc_transaction_data,
                    amount_date_dict,
                    acc_current_balance,
                    account_date_list,
                    acc_create_date,
                    account_transaction_value,
                    acc_available_balance,
                )
                graph_dict = {
                    "label_name": acc_obj.name,
                    "data_value": account_transaction_value,
                }
                acc_graph_data.append(graph_dict)
                acc_min_max_value_list.append(min(account_transaction_value))
                acc_min_max_value_list.append(max(account_transaction_value))

        else:
            if accounts_data:
                for acc_obj in accounts_data:
                    if acc_obj.currency in total_account_balance:
                        total_account_balance[acc_obj.currency] = total_account_balance[
                            acc_obj.currency
                        ] + float(acc_obj.available_balance)
                    else:
                        total_account_balance[acc_obj.currency] = float(
                            acc_obj.available_balance
                        )
            account_date_list = []

        # Process property data
        for data in property_data:
            property_currency_balance.append({data.currency: data.value})

        category_spent_amount(
            categories, user_name, categories_name, categories_value, total_spent_amount
        )
        budget_currency = "$"

        # for income in income_data:
        #     income_transactions = all_transaction_data.filter(categories__category__name='Income',
        #                                                       categories=income.sub_category, out_flow=False)
        #     if income_transactions:
        #         income_amount = 0
        #         for income_t in income_transactions:
        #             income_amount += float(income_t.amount)
        #         income_label.append(income.sub_category.name)
        #         income_values.append(income_amount)
        # Process budget data
        for data in budget_data:
            budget_currency = data.currency
            category_group_name = data.category.category.name
            if category_group_name == CategoryTypes.INCOME.value:
                if data.name in income_spent_dict:
                    income_spent_dict[data.name] += float(data.budget_spent)
                else:
                    income_spent_dict[data.name] = float(data.budget_spent)
            else:
                if data.name in budget_spent_dict:
                    budget_spent_dict[data.name] += float(data.budget_spent)
                else:
                    budget_spent_dict[data.name] = float(data.budget_spent)

        # Append budget and income data to labels and values
        for key, value in budget_spent_dict.items():
            budget_label.append(key)
            budget_values.append(round(value, 2))

        for key, value in income_spent_dict.items():
            income_label.append(key)
            income_values.append(round(value, 2))

        budget_label += bill_label
        budget_values += bill_values

        # Calculate net worth
        all_account_data = Account.objects.filter(user=user_name)
        net_worth_dict = net_worth_cal(
            all_account_data,
            property_data,
            account_date_list,
            stock_portfolio_data,
            fun_name="dash_board",
        )
        # Calculate min and max account values
        if acc_min_max_value_list:
            acc_max_value = max(acc_min_max_value_list)
            acc_min_value = min(acc_min_max_value_list)
        else:
            acc_max_value = 0
            acc_min_value = 0
        # Prepare context for rendering the dashboard template
        context = {
            "categories_name": categories_name,
            "categories_series": [{"name": "Spend", "data": categories_value}],
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
            "total_spent_amount": total_spent_amount,
        }
        return render(request, "dashboard.html", context=context)
    else:
        # Redirect to login page if user is not authenticated
        next = None
        return render(request, "login_page.html", context={"next": next})


@login_required(login_url="/login")
def net_worth(request):
    """
    Renders the net worth page with detailed breakdowns of assets,
    liabilities, and net worth over time.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: Rendered HTML response for the net worth page.
    """
    user_name = request.user
    # Fetch user-related financial data
    account_data = Account.objects.filter(user=user_name)
    property_data = Property.objects.filter(user=user_name)
    stock_portfolio_data = StockHoldings.objects.filter(user=user_name)

    # Generate the date range list for account data
    if account_data:
        min_date = account_data[0].created_at.date()
        max_date = datetime.datetime.today().date()
        day_diff = (max_date - min_date).days
        account_date_list = [
            str(max_date - datetime.timedelta(days=x)) for x in range(day_diff)
        ]
        account_date_list.append(str(min_date))
        account_date_list = account_date_list
    else:
        account_date_list = []

    # Calculate net worth and related financial data
    (
        net_worth_dict,
        assets_data,
        liability_data,
        total_asset_amount_dict,
        total_liability_dict,
        total_property_dict,
        asset_currency_balance,
        liability_currency_balance,
        _,
        total_currency_list,
        date_range_list,
        _,
        total_portfolio_dict,
    ) = net_worth_cal(
        account_data, property_data, account_date_list, stock_portfolio_data
    )

    asset_total_dict = {}
    liability_total_dict = {}
    net_worth_graph_list = []
    min_max_value_list = []

    # Aggregate asset balances by currency
    if asset_currency_balance:
        for currency_index in range(len(asset_currency_balance)):
            asset_currency_name = list(
                asset_currency_balance[currency_index])[0]
            balance_data = asset_currency_balance[currency_index][asset_currency_name]
            print("asset_currency_name", asset_currency_name)
            print("currency_name", currency_index)
            if asset_currency_name in total_currency_list:
                if asset_currency_name in asset_total_dict:
                    sum_balance_data = [
                        x + y
                        for (x, y) in zip(
                            asset_total_dict[asset_currency_name], balance_data
                        )
                    ]
                    asset_total_dict[asset_currency_name] = sum_balance_data
                else:
                    asset_total_dict[asset_currency_name] = balance_data

    # Aggregate liability balances by currency
    if liability_currency_balance:
        for currency_index in range(len(liability_currency_balance)):
            liability_currency_name = list(liability_currency_balance[currency_index])[
                0
            ]
            liability_balance_data = liability_currency_balance[currency_index][
                liability_currency_name
            ]
            if liability_currency_name in total_currency_list:
                if liability_currency_name in liability_total_dict:
                    sum_liab_data = [
                        x + y
                        for (x, y) in zip(
                            liability_total_dict[liability_currency_name],
                            liability_balance_data,
                        )
                    ]
                    liability_total_dict[liability_currency_name] = sum_liab_data
                else:
                    liability_total_dict[liability_currency_name] = (
                        liability_balance_data
                    )
    # Calculate net worth over time for each currency
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
        net_worth_graph_dict = {
            "label_name": name, "data_value": net_worth_list}
        net_worth_graph_list.append(net_worth_graph_dict)

    # Determine the min and max values for the net worth graph
    if min_max_value_list:
        max_value = max(min_max_value_list)
        min_value = min(min_max_value_list)
    else:
        max_value = 0
        min_value = 0
    # Prepare context for rendering the net worth template
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
        "currency_dict": CURRENCY_DICT,
        "account_graph_data": net_worth_graph_list,
        "date_range_list": date_range_list[::-1],
        "max_value": max_value,
        "min_value": min_value,
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


class CategoryList(LoginRequiredMixin, ListView):
    """
    View to display and manage the user's category list, including budget tracking
    and transaction summaries for each category.
    """

    model = SubCategory
    template_name = "category/category_list.html"

    def get(self, request, *args, **kwargs):
        """
        Handles GET request to retrieve and display category data
        of first budget of the user.
        """
        self.object_list = self.get_queryset()
        self.date_value = datetime.datetime.today().date()
        self.user_budget = UserBudgets.objects.filter(
            user=self.request.user).first()

        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        """
        Handles POST request to filter and update category data based on user input.
        """
        if request.method == "POST":
            self.object_list = self.get_queryset()
            select_period = self.request.POST.get("select_period")
            user_budget_id = self.request.POST.get("user_budget")
            self.date_value = datetime.datetime.today().date()

            # Fetch the selected user budget object
            if user_budget_id:
                self.user_budget = UserBudgets.objects.get(
                    user=self.request.user, pk=user_budget_id
                )

            # Prepare date value for the selected period
            if select_period:
                month_name = "01-" + select_period
                self.date_value = datetime.datetime.strptime(
                    month_name, DateFormats.DD_MON_YYYY.value
                ).date()

            return self.render_to_response(self.get_context_data())
        else:
            # Return 405 Method Not Allowed if the request method is not POST
            return HttpResponseNotAllowed(["POST"])

    def get_context_data(self, **kwargs):
        """
        Generates context data for rendering the category list page, including
        budgets, transactions, and category summaries.
        """
        user_name = self.request.user
        current_month = datetime.datetime.strftime(
            self.date_value, DateFormats.MON_YYYY.value
        )
        start_date, end_date = start_end_date(
            self.date_value, BudgetPeriods.MONTHLY.value
        )
        data = super(CategoryList, self).get_context_data(**kwargs)

        # Initialize forms for budgets and transactions
        budget_form = BudgetForm(request=self.request)
        transaction_form = TransactionForm(request=self.request)

        # Retrieve the user's budgets and categories
        user_budgets = UserBudgets.objects.filter(user=user_name)
        category_list = Category.objects.filter(user=user_name)
        tags = Tag.objects.filter(user=user_name)
        sub_category_data = SubCategory.objects.filter(
            category__user=user_name)

        # Initialize lists and dictionaries for category names and values
        categories_name, categories_value = [], []
        bank_accounts_dict, sub_category_dict = {}, {}

        # Fetch account data for the user's bank accounts
        accounts_qs = Account.objects.filter(
            user=user_name, account_type__in=AccountTypes.list()
        )
        for account_data in accounts_qs:
            bank_accounts_dict[account_data.id] = account_data.name

        # Get the list of months for the selected budget
        list_of_months = get_list_of_months(user_name, self.user_budget)

        # Process each subcategory to gather budget and transaction data
        for val in sub_category_data:
            if (
                val.category.name != CategoryTypes.FUNDS.value
            ):  # Excluding Category - Funds

                transaction_amount = 0
                budgeted_amount = 0
                transaction_date = "No transactions"
                transactions_list = []
                id = "false"

                # Process Bills and Subscriptions category
                if val.category.name == CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value:
                    # Fetches transaction data for Bills
                    category_transaction_data = Transaction.objects.filter(
                        user=user_name,
                        bill__user_budget=self.user_budget,
                        categories__id=val.id,
                        transaction_date__range=(start_date, end_date),
                    )
                    # Fetch the bill details within the selected date range
                    bill_obj = Bill.objects.filter(
                        label=val.name,
                        user_budget=self.user_budget,
                        user=user_name,
                        date__range=(start_date, end_date),
                    )

                    for i in bill_obj:
                        id = i.id
                        budgeted_amount = float(i.amount)

                # Process other budget categories
                if val.category.name not in (
                    CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value,
                    CategoryTypes.FUNDS.value,
                ):
                    # Fetches transaction data for Budgets
                    category_transaction_data = Transaction.objects.filter(
                        user=user_name,
                        budgets__user_budget=self.user_budget,
                        categories__id=val.id,
                        transaction_date__range=(start_date, end_date),
                    )
                    # Fetch the budget details within the selected date range
                    budget_obj = Budget.objects.filter(
                        user=user_name,
                        user_budget=self.user_budget,
                        name=val.name,
                        start_date__range=(start_date, end_date),
                    )

                    for i in budget_obj:
                        id = i.id
                        budgeted_amount = float(i.initial_amount)

                # Sum up transaction amounts for the subcategory
                for transaction_data in category_transaction_data:
                    transactions_list.append(transaction_data)
                    transaction_date = transaction_data.transaction_date
                    transaction_amount += float(transaction_data.amount)

                # Percentage amount for Category progress bar
                if budgeted_amount <= 0:
                    percentage = 0
                else:
                    percentage = round(
                        (transaction_amount / budgeted_amount) * 100, 2)

                remaining_balance = (
                    budgeted_amount - transaction_amount
                )  # Remaining balance amount
                # Populate the subcategory dictionary with the calculated data
                category_key = val.category.name
                if category_key in sub_category_dict:
                    sub_category_dict[category_key][3].append(
                        [
                            val.name,
                            budgeted_amount,
                            transaction_amount,
                            val.id,
                            percentage,
                            remaining_balance,
                            transaction_date,
                            transactions_list,
                            id,
                        ]
                    )
                else:
                    sub_category_dict[category_key] = [
                        0,
                        0,
                        val.category.id,
                        [
                            [
                                val.name,
                                budgeted_amount,
                                transaction_amount,
                                val.id,
                                percentage,
                                remaining_balance,
                                transaction_date,
                                transactions_list,
                                id,
                            ]
                        ],
                    ]

        # Prepares data for Category totals and graph
        for cat_data in category_list:
            if cat_data.name != CategoryTypes.FUNDS.value:
                if cat_data.name not in sub_category_dict:
                    sub_category_dict[cat_data.name] = [0, 0, cat_data.id, []]
                else:
                    total_cat_budget = 0
                    total_cat_spent = 0
                    for sub_cat in sub_category_dict[cat_data.name][3]:
                        total_cat_budget += sub_cat[1]
                        total_cat_spent += sub_cat[2]
                    sub_category_dict[cat_data.name][0] = total_cat_budget
                    sub_category_dict[cat_data.name][1] = total_cat_spent
                    if total_cat_spent != 0:
                        categories_name.append(cat_data.name)
                        categories_value.append(total_cat_spent)

        data["user_budgets"] = user_budgets
        data["sub_category_data"] = sub_category_dict
        data["categories_name"] = categories_name
        data["categories_series"] = [
            {"name": "Spent", "data": categories_value}]
        data["category_icons"] = CATEGORY_ICONS
        data["page"] = "category_list"
        data["transaction_key"] = TRANSACTION_KEYS[:-1]
        data["transaction_data"] = category_transaction_data
        data["budget_form"] = budget_form
        data["bank_accounts"] = bank_accounts_dict
        data["form"] = transaction_form
        data["tags"] = tags
        data["list_of_months"] = list_of_months
        data["current_month"] = current_month
        data["category_key_dumbs"] = json.dumps(SUB_CATEGORY_KEYS)
        data["categories_name_dumbs"] = json.dumps(TRANSACTION_KEYS[:-1])
        data["categories_value"] = categories_value
        data["selected_budget"] = self.user_budget
        data["tour_api"] = Tour_APIs["category_page"]
        data["tour_api"] = Tour_APIs["category_page"]

        return data


class CategoryDetail(LoginRequiredMixin, DetailView):
    """
    View to display detailed information about a specific category.
    """

    model = Category
    template_name = "category/category_detail.html"

    def get_context_data(self, **kwargs):
        data = super(CategoryDetail, self).get_context_data(**kwargs)
        data["page"] = "category_list"
        return data


class CategoryAdd(LoginRequiredMixin, CreateView):
    """
    View to handle the creation of a new category.
    """

    model = Category
    form_class = CategoryForm
    template_name = "category/category_add.html"

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        user_name = self.request.user
        data = super(CategoryAdd, self).get_context_data(**kwargs)

        # Get a list of existing categories for the current user
        categories_list = list(
            Category.objects.filter(
                user=user_name).values_list("name", flat=True)
        )

        # Get a list of all suggestive categories
        category_suggestions = SuggestiveCategory.objects.all().values_list(
            "name", flat=True
        )
        suggestion_list = []
        for name in category_suggestions:
            if name not in categories_list:
                suggestion_list.append(name)

        # Add the filtered suggestions to the context
        data["category_suggestions"] = suggestion_list
        return data

    def form_valid(self, form):
        """
        Sets the user and processes the form submission.
        """
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.name = self.request.POST.get("name").title().strip()
        obj.save()
        return super().form_valid(form)

    def get_success_url(self):
        """
        Detect the submit button used and act accordingly
        """
        if "add_other" in self.request.POST:
            url = reverse_lazy("category_add")
        else:
            url = reverse_lazy("category_list")
        return url


class CategoryUpdate(LoginRequiredMixin, UpdateView):
    """
    View to handle the updating of an existing category.
    """

    model = Category
    form_class = CategoryForm
    template_name = "category/category_update.html"


class CategoryDelete(LoginRequiredMixin, DeleteView):
    """
    View to handle the deletion of a category and its associated transactions.
    """

    def post(self, request, *args, **kwargs):
        """
        Handles POST request for deleting a category.
        - Retrieves the category object using the primary key (pk) from the URL.
        - Deletes all associated transaction details for the user.
        - Deletes the category object.
        - Returns a JSON response indicating success.
        """
        # Retrieve the category object to be deleted
        category_obj = Category.objects.get(pk=self.kwargs["pk"])
        user_name = self.request.user

        # Fetch all transactions associated with this category for the user
        transaction_details = Transaction.objects.filter(
            user=user_name, categories__category=category_obj
        )

        # Delete each associated transaction
        for data in transaction_details:
            delete_transaction_details(data.pk, user_name)
        category_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


def category_group_add(request):
    """
    Handles the addition of a new category group via an AJAX POST request.
    - Checks if the category already exists for the user.
    - If it exists, returns an error response.
    - If not, creates the new category and returns a success response.
    """
    if request.method == "POST" and request.is_ajax():
        user_name = request.user
        category_name = request.POST["category_name"].title()
        category_obj = Category.objects.filter(
            user=user_name, name=category_name)
        if category_obj:
            return JsonResponse({"status": "error"})
        else:
            Category.objects.create(user=user_name, name=category_name)
            return JsonResponse({"status": "success"})


# Subcategory views


def subcategory_suggestion(request):
    """
    Returns subcategory suggestions for a given category.

    Args:
        request (HttpRequest): The HTTP request object containing 'category_pk'.

    Returns:
        JsonResponse: JSON with subcategory suggestions and category_pk.
    """
    category_pk = int(request.POST["category_pk"])
    category_obj = Category.objects.get(pk=category_pk)
    suggestion_list = SUGGESTED_SUB_CATEGORIES[category_obj.name]
    for name in suggestion_list:
        sub_obj = SubCategory.objects.filter(name=name, category=category_obj)
        if sub_obj:
            suggestion_list.remove(name)
    context = {"subcategory_suggestions": suggestion_list,
               "category_pk": category_pk}
    return JsonResponse(context)


def subcategory_add(request, category_pk):
    """
    Handles adding a new subcategory to a specified category.

    Args:
        request (HttpRequest): The HTTP request object.
        category_pk (int): The primary key of the category to which the subcategory will be added.

    Returns:
        HttpResponse: Renders a page to add a subcategory or redirects after successful addition.
    """
    category_obj = Category.objects.get(pk=category_pk)
    try:
        # Get the list of suggested subcategories for the given category
        suggestion_list = SUGGESTED_SUB_CATEGORIES[category_obj.name]

        for name in suggestion_list:
            sub_obj = SubCategory.objects.filter(
                name=name, category=category_obj)

            if sub_obj:
                # Remove names from suggestions if they already exist
                suggestion_list.remove(name)

        context = {
            "subcategory_suggestions": suggestion_list,
            "category_pk": category_pk,
        }
    except:
        # Handle cases where category name is not found in suggestions
        context = {"category_pk": category_pk}

    if request.method == "POST":
        name = request.POST.get("name").title()
        try:
            # Check if the subcategory already exists
            SubCategory.objects.get(
                category__user=request.user, name=name, category__name=category_obj.name
            )
            context["error"] = "Subcategory already exists"
            return render(request, "subcategory/add.html", context=context)
        # To-Do  Remove bare except
        except:
            # Create the new subcategory
            SubCategory.objects.create(name=name, category=category_obj)
            return redirect("/category_list")
    return render(request, "subcategory/add.html", context=context)


def subcategory_update(request, pk):
    """
    Updates an existing subcategory and its associated data.

    Args:
        request (HttpRequest): The HTTP request object.
        pk (int): The primary key of the subcategory to update.

    Returns:
        HttpResponse: Renders the update form or redirects to the category list.
    """
    user = request.user
    category_list = Category.objects.filter(user=user)
    subcategory_obj = SubCategory.objects.get(pk=pk)
    context = {"category_list": category_list,
               "subcategory_obj": subcategory_obj}

    if request.method == "POST":
        # Get the new category and name from the form
        category_obj = Category.objects.get(
            user=user, name=request.POST.get("category")
        )
        name = request.POST.get("name").title()
        old_name = subcategory_obj.name

        # Check if the new subcategory name already exists
        sub_category_exist = check_subcategory_exists(
            subcategory_obj, name, category_obj
        )
        if sub_category_exist:
            context["error"] = "Subcategory already exists"
            return render(request, "subcategory/update.html", context=context)

        # Update the subcategory's name and category
        subcategory_obj.name = name
        subcategory_obj.category = category_obj
        subcategory_obj.save()

        # Update related BillDetail if the category is "Bills and Subscriptions"
        if subcategory_obj.category.name == CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value:
            bill_obj = BillDetail.objects.get(user=user, label=old_name)
            bill_obj.label = name
            bill_obj.save()
        return redirect("/category_list")

    return render(request, "subcategory/update.html", context=context)


def subcategory_delete(request, pk):
    """
    Deletes a subcategory and associated transactions.

    Args:
        request (HttpRequest): The HTTP request object.
        pk (int): The primary key of the subcategory to delete.

    Returns:
        JsonResponse: A JSON response indicating the success status.
    """
    user = request.user
    subcategory_obj = SubCategory.objects.get(pk=pk)

    # Fetch and delete transactions associated with the sub category
    transaction_details = Transaction.objects.filter(
        user=user, categories=subcategory_obj
    )
    for data in transaction_details:
        delete_transaction_details(data.pk, user)

    # Delete the subcategory
    subcategory_obj.delete()
    return JsonResponse({"status": "Successfully", "path": "None"})


def subcategory_list(request):
    """
    Retrieves a list of subcategories for a given category.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: A JSON response containing a list of subcategory names.
        Redirect: Redirects to category list if not a POST request or not AJAX.
    """
    if request.method == "POST" and request.is_ajax():
        user = request.user
        category_group = request.POST.get("category_group")
        try:
            category = Category.objects.get(user=user, pk=category_group)
        # To-Do  Remove bare except
        except:
            category = Category.objects.get(user=user, name=category_group)

        # Fetch subcategories for the specified category
        subcategories = SubCategory.objects.filter(category=category)
        subcategories = list(subcategories.values_list("name", flat=True))
        return JsonResponse({"subcategories": subcategories})

    # Redirect to category list if not an AJAX POST request
    return redirect("/category_list")


def subcategory_budget(request):
    """
    Retrieves the budget name associated with a specific subcategory
    and user budget.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        JsonResponse: A JSON response containing the budget name or
        False if not found.
    """
    user_name = request.user
    category = int(request.POST.get("category"))
    sub_category_name = request.POST.get("name")
    user_budget_id = request.POST.get("user_budget_id")
    # Fetch category from the selected user budget
    if user_budget_id:
        user_budget = UserBudgets.objects.get(
            user=user_name, pk=user_budget_id)

    # Get the subcategory object
    subcategory_obj = SubCategory.objects.get(
        category__pk=category, name=sub_category_name
    )
    try:
        # Fetch the budget associated with the subcategory and user budget
        budget = Budget.objects.filter(
            user=user_name, user_budget=user_budget, category=subcategory_obj
        )
        budget_name = budget[0].name
    # To-Do  Remove bare except
    except:
        # Handle case where no budget is found
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


# In an api_views.py file within your app
class ProtectedResourceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        An example view that requires JWT authentication.
        """
        return Response(
            {
                "message": "You have access to this protected resource",
                "user": request.user.username,
            }
        )


logger = logging.getLogger("my_finance")


@axes_dispatch
def user_login(request):
    """
    Handles user login, including authentication via Django and JWT from WordPress,
    along with generating JWT tokens for the session.
    """
    context = {"page": "login_page"}

    if request.method == "POST":
        username = request.POST.get("register-username")
        user_password = request.POST.get("register-password")

        # Get redirect URL from POST data, defaulting to 'home' if not provided
        redirect_url = request.POST.get("redirect_url", "")

        # If redirect_url is empty or invalid, use 'home' as a default
        if not redirect_url:
            redirect_url = "home"

        # Step 1: Try Django authentication first
        user = authenticate(
            request=request, username=username, password=user_password)

        # For superusers, proceed with standard Django login
        if user and user.is_superuser:
            login(request, user)
            reset_request(request)  # Reset Axes counters on successful login
            return redirect(redirect_url)

        # Step 2: If Django authentication fails for non-superusers, try WordPress JWT
        if not user:
            try:
                # Handle JWT authentication from WordPress
                token_url = f"{wordpress_domain}/wp-json/api/v1/token"
                token_data = {"username": username, "password": user_password}

                token_response = requests.post(
                    token_url, json=token_data, timeout=10)
                token_response.raise_for_status()
                token_data = token_response.json()

                if "jwt_token" not in token_data:
                    # Authentication failed - log this failure
                    context["login_error"] = "Invalid credentials"
                    return render(request, "login_page.html", context=context)

                jwt_token = token_data["jwt_token"]

                # Step 3: Membership verification
                user_info_url = f"{wordpress_domain}/wp-json/wp/v2/users/me"
                headers = {"Authorization": f"Bearer {jwt_token}"}
                user_info_response = requests.get(
                    user_info_url, headers=headers, timeout=10
                )
                user_info = user_info_response.json()

                if "id" not in user_info:
                    # Failed to get user info
                    context["login_error"] = "Failed to retrieve user information"
                    return render(request, "login_page.html", context=context)

                user_id = user_info["id"]

                # Check membership plan
                plan_url = f"{wordpress_domain}/?ihc_action=api-gate&ihch={wordpress_api_key}&action=get_user_levels&uid={user_id}"
                plan_response = requests.get(plan_url, timeout=10).json()

                if "response" not in plan_response or not plan_response["response"]:
                    context["login_error"] = "No membership plan found"
                    return render(request, "login_page.html", context=context)

                user_plan_id = list(plan_response["response"].keys())[0]

                # Verify membership level
                verify_user_url = f"{wordpress_domain}/?ihc_action=api-gate&ihch={wordpress_api_key}&action=verify_user_level&uid={user_id}&lid={user_plan_id}"
                verify_user_response = requests.get(
                    verify_user_url, timeout=10)
                verify_user_response.raise_for_status()

                verify_user_data = verify_user_response.json()
                if verify_user_data.get("response") != 1:
                    context["login_error"] = (
                        "You don't have a valid membership subscription"
                    )
                    return render(request, "login_page.html", context=context)

                # Create or update user in Django
                try:
                    django_user = User.objects.get(id=user_id)
                    # Update password if needed
                    django_user.set_password(user_password)
                    django_user.save()
                except User.DoesNotExist:
                    django_user = User(
                        id=user_id,
                        username=username,
                        email=user_info.get("email", ""),
                        first_name=user_info.get("name", ""),
                    )
                    django_user.set_password(user_password)
                    django_user.save()

                # If we get here, authentication was successful, so reset Axes counters
                reset_request(request)

                # Log the user in
                login(request, django_user)

                # Generate JWT tokens for the session
                refresh = RefreshToken.for_user(django_user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                # Store tokens in secure, HTTP-only cookies
                response = redirect(redirect_url)

                # Set access and refresh tokens as HTTP-only cookies
                response.set_cookie(
                    "access_token",
                    access_token,
                    max_age=15 * 60,  # 15 minutes in seconds
                    httponly=True,
                    secure=True,
                    samesite="Strict",
                )

                response.set_cookie(
                    "refresh_token",
                    refresh_token,
                    max_age=24 * 60 * 60,  # 1 day in seconds
                    httponly=True,
                    secure=True,
                    samesite="Strict",
                )

                # Redirect to the target URL
                return response

            except requests.exceptions.RequestException as e:
                logger.error(f"API request error during login: {str(e)}")
                context["login_error"] = f"Error during login: {str(e)}"
                return render(request, "login_page.html", context=context)
            except Exception as e:
                logger.error(f"Unexpected error during login: {str(e)}")
                context["login_error"] = f"An unexpected error occurred: {str(e)}"
                return render(request, "login_page.html", context=context)

        # If Django authentication was successful for non-superusers
        login(request, user)

        # Reset Axes counters
        reset_request(request)

        # Generate JWT tokens for the session
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Set cookies with the tokens
        response = redirect(redirect_url)
        response.set_cookie(
            "access_token",
            access_token,
            max_age=15 * 60,  # 15 minutes
            httponly=True,
            secure=True,
            samesite="Strict",
        )
        response.set_cookie(
            "refresh_token",
            refresh_token,
            max_age=24 * 60 * 60,  # 1 day
            httponly=True,
            secure=True,
            samesite="Strict",
        )

        # Redirect after successful login
        return response

    # GET request - just show the login form
    next_url = request.GET.get("next", "")
    context["redirect_url"] = next_url
    return render(request, "login_page.html", context=context)


# from axes.decorators import axes_dispatch
# from axes.utils import reset_request
# from django.contrib.auth import authenticate, login
# from django.contrib.auth.models import User
# from django.shortcuts import render, redirect
# from django.urls import reverse
# import requests
# import logging

# logger = logging.getLogger('my_finance')

# @axes_dispatch
# def user_login(request):
#     """
#     Handles user login, including authentication via Django and JWT,
#     as well as membership verification.
#     """
#     context = {"page": "login_page"}
#     if request.method == "POST":
#         username = request.POST.get("register-username")
#         user_password = request.POST.get("register-password")

#         # Get redirect URL from POST data, defaulting to 'home' if not provided
#         redirect_url = request.POST.get("redirect_url", "")

#         # If redirect_url is empty or invalid, use 'home' as a default
#         if not redirect_url:
#             redirect_url = "home"

#         # Step 1: First try Django authentication
#         user = authenticate(request=request, username=username, password=user_password)

#         # For superusers, proceed with standard Django login
#         if user and user.is_superuser:
#             login(request, user)
#             return redirect(redirect_url)

#         # If Django authentication fails for non-superusers, try WordPress JWT
#         if not user:
#             try:
#                 # Handle JWT authentication from WordPress
#                 token_url = f"{wordpress_domain}/wp-json/api/v1/token"
#                 token_data = {"username": username, "password": user_password}

#                 token_response = requests.post(token_url, json=token_data, timeout=10)
#                 token_response.raise_for_status()
#                 token_data = token_response.json()

#                 if "jwt_token" not in token_data:
#                     # Authentication failed - this will be logged by Axes
#                     context["login_error"] = "Invalid credentials"
#                     return render(request, "login_page.html", context=context)

#                 jwt_token = token_data["jwt_token"]

#                 # Membership verification
#                 user_info_url = f"{wordpress_domain}/wp-json/wp/v2/users/me"
#                 headers = {"Authorization": f"Bearer {jwt_token}"}
#                 user_info_response = requests.get(user_info_url, headers=headers, timeout=10)
#                 user_info = user_info_response.json()

#                 if 'id' not in user_info:
#                     # Failed to get user info
#                     context["login_error"] = "Failed to retrieve user information"
#                     return render(request, "login_page.html", context=context)

#                 user_id = user_info["id"]

#                 # Check membership plan
#                 plan_url = f"{wordpress_domain}/?ihc_action=api-gate&ihch={wordpress_api_key}&action=get_user_levels&uid={user_id}"
#                 plan_response = requests.get(plan_url, timeout=10).json()

#                 if "response" not in plan_response or not plan_response["response"]:
#                     context["login_error"] = "No membership plan found"
#                     return render(request, "login_page.html", context=context)

#                 user_plan_id = list(plan_response["response"].keys())[0]

#                 # Verify membership
#                 verify_user_url = f"{wordpress_domain}/?ihc_action=api-gate&ihch={wordpress_api_key}&action=verify_user_level&uid={user_id}&lid={user_plan_id}"
#                 verify_user_response = requests.get(verify_user_url, timeout=10)
#                 verify_user_response.raise_for_status()

#                 verify_user_data = verify_user_response.json()
#                 if verify_user_data.get("response") != 1:
#                     context["login_error"] = "You don't have a valid membership subscription"
#                     return render(request, "login_page.html", context=context)

#                 # Create or update user in Django
#                 try:
#                     django_user = User.objects.get(id=user_id)
#                     django_user.set_password(user_password)
#                     django_user.save()
#                 except User.DoesNotExist:
#                     django_user = User(
#                         id=user_id,
#                         username=username,
#                         email=user_info.get("email", ""),
#                         first_name=user_info.get("name", "")
#                     )
#                     django_user.set_password(user_password)
#                     django_user.save()

#                 # If we get here, authentication was successful, so reset Axes counters
#                 reset_request(request)

#                 # Log the user in
#                 login(request, django_user)

#                 # Use reverse to check URL validity before redirecting
#                 try:
#                     # Check if it's a named URL pattern
#                     reverse(redirect_url)
#                     return redirect(redirect_url)
#                 except:
#                     # If it's not a named URL pattern, check if it's a direct URL path
#                     if redirect_url.startswith('/'):
#                         return redirect(redirect_url)
#                     else:
#                         # Fall back to the home page
#                         return redirect('home')

#             except requests.exceptions.RequestException as e:
#                 logger.error(f"API request error during login: {str(e)}")
#                 context["login_error"] = f"Error during login: {str(e)}"
#                 return render(request, "login_page.html", context=context)
#             except Exception as e:
#                 logger.error(f"Unexpected error during login: {str(e)}")
#                 context["login_error"] = f"An unexpected error occurred: {str(e)}"
#                 return render(request, "login_page.html", context=context)

#         # If we get here, Django authentication was successful
#         login(request, user)

#         # Use reverse to check URL validity before redirecting
#         try:
#             # Check if it's a named URL pattern
#             reverse(redirect_url)
#             return redirect(redirect_url)
#         except:
#             # If it's not a named URL pattern, check if it's a direct URL path
#             if redirect_url.startswith('/'):
#                 return redirect(redirect_url)
#             else:
#                 # Fall back to the home page
#                 return redirect('home')

#     # GET request - just show the login form
#     next_url = request.GET.get("next", "")
#     context["redirect_url"] = next_url
#     return render(request, "login_page.html", context=context)


# from axes.decorators import axes_dispatch
# from axes.models import AccessAttempt
# from django.contrib.auth import authenticate, login
# from django.shortcuts import render, redirect
# import requests

# @axes_dispatch
# def user_login(request):
#     """
#     Handles user login, including authentication via Django and JWT,
#     as well as membership verification.
#     """
#     context = {"page": "login_page"}

#     if request.method == "POST":
#         username = request.POST.get("register-username")
#         user_password = request.POST.get("register-password")
#         check_jwt_authentication = False
#         check_user_membership = False

#         try:
#             # Authenticate the user and pass the request object to authenticate
#             user = authenticate(request=request, username=username, password=user_password)
#             if user:
#                 if user.is_superuser:
#                     login(request, user)
#                     redirect_url = request.POST.get("redirect_url")
#                     return redirect(redirect_url if redirect_url else "home")
#             else:
#                 context["login_error"] = "Invalid credentials"
#                 return render(request, "login_page.html", context=context)
#         except Exception as e:
#             context["login_error"] = f"Authentication error: {e}"
#             return render(request, "login_page.html", context=context)

#         # Handle JWT authentication from WordPress
#         token_url = f"{wordpress_domain}/wp-json/api/v1/token"
#         token_data = {"username": username, "password": user_password}
#         try:
#             token_response = requests.post(token_url, json=token_data)
#             token_response.raise_for_status()  # Raises HTTPError for bad responses
#             token_data = token_response.json()
#             if "jwt_token" in token_data:
#                 jwt_token = token_data["jwt_token"]
#                 check_jwt_authentication = True
#         except requests.exceptions.RequestException as e:
#             context["login_error"] = f"Error while fetching token: {e}"
#             return render(request, "login_page.html", context=context)

#         # Membership verification
#         if check_jwt_authentication:
#             try:
#                 user_info_url = f"{wordpress_domain}/wp-json/wp/v2/users/me"
#                 headers = {"Authorization": f"Bearer {jwt_token}"}
#                 user_info_response = requests.get(user_info_url, headers=headers)
#                 user_info = user_info_response.json()
#                 user_id = user_info["id"]

#                 plan_url = f"{wordpress_domain}/?ihc_action=api-gate&ihch={wordpress_api_key}&action=get_user_levels&uid={user_id}"
#                 plan_response = requests.get(plan_url).json()["response"]
#                 user_plan_id = list(plan_response.keys())[0]

#                 verify_user_url = f"{wordpress_domain}/?ihc_action=api-gate&ihch={wordpress_api_key}&action=verify_user_level&uid={user_id}&lid={user_plan_id}"
#                 verify_user_response = requests.get(verify_user_url)
#                 if verify_user_response.status_code == 200:
#                     verify_user_data = verify_user_response.json()
#                     if verify_user_data["response"] == 1:
#                         check_user_membership = True
#             except requests.exceptions.RequestException as e:
#                 context["login_error"] = f"Error during membership verification: {e}"
#                 return render(request, "login_page.html", context=context)

#         if not check_user_membership:
#             context["login_error"] = "You don't have a membership subscription."
#             return render(request, "login_page.html", context=context)

#         if check_jwt_authentication and check_user_membership:
#             try:
#                 user = User.objects.get(id=user_id)
#                 user.set_password(user_password)
#                 user.save()
#             except User.DoesNotExist:
#                 user = User(id=user_id, username=username, email="", first_name=user_info["name"])
#                 user.set_password(user_password)
#                 user.save()

#             login(request, user)
#             redirect_url = request.POST.get("redirect_url")
#             return redirect(redirect_url if redirect_url else "home")

#     else:
#         context["redirect_url"] = request.GET.get("next", "")
#         return render(request, "login_page.html", context=context)


@login_required(login_url="/login")
def user_logout(request):
    """
    Logs out the user and redirects to the login page.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponseRedirect: Redirects to the login page.
    """
    logout(request)
    return redirect("/login")


def make_budgets_values(user_name, budget_data, page_method):
    """
    Calculates and organizes budget data for the specified user.

    Args:
        user_name (User): The user for whom the budget data is being calculated.
        budget_data (QuerySet): The queryset of budget data.
        page_method (str): The type of page requesting the budget data.

    Returns:
        tuple: Contains all budgets, budget graph data, budget values, budget currency,
               list of months, budget names list, budgets dictionary, income budgets dictionary,
               and total budget income.
    """
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

            # Retrieve budget details
            budget_create_date = data.created_at
            budget_end_date = data.ended_at
            budget_names_list.append(data.name)
            budget_amount = float(data.amount)
            left_amount = float(data.budget_left)
            budget_pre = data.budget_period
            spent_amount = float(data.budget_spent)
            total_spent_amount = spent_amount
            if budget_create_date:
                budget_start_date = datetime.datetime.strftime(
                    budget_create_date, DateFormats.MON_DD_YYYY.value
                )
                budget_end_date = datetime.datetime.strftime(
                    budget_end_date, DateFormats.MON_DD_YYYY.value
                )
            else:
                budget_start_date = False
                budget_end_date = False

            # Handle quarterly and yearly budget periods
            if budget_pre in (
                BudgetPeriods.QUARTERLY.value,
                BudgetPeriods.YEARLY.value,
            ):
                all_bdgt_spent = Budget.objects.filter(
                    user=user_name,
                    name=data.name,
                    created_at=budget_create_date,
                    ended_at=data.ended_at,
                )
                total_spent_amount = sum(
                    float(obj.budget_spent) for obj in all_bdgt_spent
                )

            budget_currency = data.currency
            category_group_name = data.category.category.name

            # Store the retieved values in a list
            budget_value = [
                data.name,
                budget_amount,
                spent_amount,
                left_amount,
                data.id,
                budget_pre,
                budget_start_date,
                budget_end_date,
                budget_currency,
                total_spent_amount,
            ]

            # Handles Income data
            if category_group_name == CategoryTypes.INCOME.value:
                if budget_pre not in (
                    BudgetPeriods.DAILY.value,
                    BudgetPeriods.WEEKLY.value,
                ):
                    if category_group_name in income_bdgt_dict:
                        income_bdgt_dict[category_group_name].append(
                            budget_value)
                        total_bgt_income += spent_amount
                    else:
                        income_bdgt_dict[category_group_name] = [budget_value]
                        total_bgt_income += spent_amount
                else:
                    if category_group_name in income_daily_bdgt_dict:
                        if data.name in income_daily_bdgt_dict[category_group_name]:
                            income_daily_bdgt_dict[category_group_name][
                                data.name
                            ].append(budget_value)
                            total_bgt_income += spent_amount
                            income_daily_total_dict[category_group_name][data.name][
                                0
                            ] += budget_amount
                            income_daily_total_dict[category_group_name][data.name][
                                1
                            ] += spent_amount
                            income_daily_total_dict[category_group_name][data.name][
                                2
                            ] += left_amount
                        else:
                            income_daily_bdgt_dict[category_group_name] = {
                                data.name: [budget_value]
                            }
                            income_daily_total_dict[category_group_name] = {
                                data.name: [budget_amount,
                                            spent_amount, left_amount]
                            }
                            total_bgt_income += spent_amount
                    else:
                        income_daily_bdgt_dict[category_group_name] = {
                            data.name: [budget_value]
                        }
                        income_daily_total_dict[category_group_name] = {
                            data.name: [budget_amount,
                                        spent_amount, left_amount]
                        }
                        total_bgt_income += spent_amount
            else:
                if spent_amount > budget_amount:
                    if data.name not in over_spent_data:
                        over_spent_data[data.name] = spent_amount - \
                            budget_amount
                    else:
                        over_spent_data[data.name] += spent_amount - \
                            budget_amount

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

                # Handle daily and weekly budget periods
                if budget_pre not in (
                    BudgetPeriods.DAILY.value,
                    BudgetPeriods.WEEKLY.value,
                ):
                    if category_group_name in budgets_dict:
                        budgets_dict[category_group_name].append(budget_value)
                    else:
                        budgets_dict[category_group_name] = [budget_value]
                else:
                    if category_group_name in daily_bdgt_dict:
                        if data.name in daily_bdgt_dict[category_group_name]:
                            daily_bdgt_dict[category_group_name][data.name].append(
                                budget_value
                            )
                            daily_total_dict[category_group_name][data.name][
                                0
                            ] += budget_amount
                            daily_total_dict[category_group_name][data.name][
                                1
                            ] += spent_amount
                            daily_total_dict[category_group_name][data.name][
                                2
                            ] += left_amount
                        else:
                            daily_bdgt_dict[category_group_name] = {
                                data.name: [budget_value]
                            }
                            daily_total_dict[category_group_name] = {
                                data.name: [budget_amount,
                                            spent_amount, left_amount]
                            }
                    else:
                        daily_bdgt_dict[category_group_name] = {
                            data.name: [budget_value]
                        }
                        daily_total_dict[category_group_name] = {
                            data.name: [budget_amount,
                                        spent_amount, left_amount]
                        }

            total_budget += budget_amount
            total_spent += spent_amount
            total_left += left_amount

        # Process budget data for specific page types
        if page_method == "budget_page":
            earliest = Budget.objects.filter(
                user=user_name, start_date__isnull=False
            ).order_by("start_date")
            for key, value in daily_total_dict.items():
                for k, v in value.items():
                    bgt_val = daily_bdgt_dict[key][k][0]
                    daily_bdgt_dict[key][k].insert(
                        0,
                        [
                            bgt_val[0],
                            v[0],
                            v[1],
                            v[2],
                            bgt_val[4],
                            bgt_val[5],
                            bgt_val[6],
                            bgt_val[7],
                            bgt_val[8],
                            v[1],
                        ],
                    )

            for key, value in income_daily_total_dict.items():
                for k, v in value.items():
                    bgt_val = income_daily_bdgt_dict[key][k][0]
                    income_daily_bdgt_dict[key][k].insert(
                        0,
                        [
                            bgt_val[0],
                            v[0],
                            v[1],
                            v[2],
                            bgt_val[4],
                            bgt_val[5],
                            bgt_val[6],
                            bgt_val[7],
                            bgt_val[8],
                            v[1],
                        ],
                    )
        else:
            earliest = TemplateBudget.objects.filter(start_date__isnull=False).order_by(
                "start_date"
            )

        start, end = earliest[0].start_date, earliest[len(
            earliest) - 1].start_date
        list_of_months = list(
            OrderedDict(
                (
                    (start + datetime.timedelta(_)).strftime(
                        DateFormats.MON_YYYY.value
                    ),
                    None,
                )
                for _ in range((end - start).days + 1)
            ).keys()
        )
        budget_values = [total_spent, total_left]
    else:
        earliest = Budget.objects.filter(
            user=user_name, start_date__isnull=False
        ).order_by("start_date")
        if earliest:
            start = earliest[0].start_date
        else:
            start = datetime.datetime.today().date()
        end = datetime.datetime.today().date()
        list_of_months = list(
            OrderedDict(
                (
                    (start + datetime.timedelta(_)).strftime(
                        DateFormats.MON_YYYY.value
                    ),
                    None,
                )
                for _ in range((end - start).days + 1)
            ).keys()
        )
        budget_values = [0, 0]
        budget_currency = ""

    budget_names_list = list(spent_data.keys())
    spent_data = dict_value_to_list(spent_data)
    left_data = dict_value_to_list(left_data)
    over_spent_data = dict_value_to_list(over_spent_data)
    budget_graph_data = [
        {"name": "Spent", "data": spent_data},
        {"name": "Left", "data": left_data},
        {"name": "OverSpent", "data": over_spent_data},
    ]

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

    return (
        all_budgets,
        budget_graph_data,
        budget_values,
        budget_currency,
        list_of_months,
        budget_names_list,
        budgets_dict,
        income_bdgt_dict,
        total_bgt_income,
    )


def budgets_page_data(request, budget_page, template_page):
    """
    Generates context data for rendering budget pages, including user budgets,
    comparisons across different periods, and template budgets.

    Args:
        request (HttpRequest): The HTTP request object.
        budget_page (str): The identifier for the current budget page.
        template_page (str): The identifier for the template budget page.

    Returns:
        dict: The context data needed to render the budget page.
    """
    user_name = request.user

    # Determine the date range based on POST data or default to current date
    if request.method == "POST":
        month_name = "01-" + request.POST["select_period"]
        date_value = datetime.datetime.strptime(
            month_name, DateFormats.DD_MON_YYYY.value
        ).date()
        current_month = datetime.datetime.strftime(
            date_value, DateFormats.MON_YYYY.value
        )
        start_date, end_date = start_end_date(
            date_value, BudgetPeriods.MONTHLY.value)
    else:
        date_value = datetime.datetime.today().date()
        current_month = datetime.datetime.strftime(
            date_value, DateFormats.MON_YYYY.value
        )
        start_date, end_date = start_end_date(
            date_value, BudgetPeriods.MONTHLY.value)

    # Fetch user-specific budget data for the given period
    budget_data = Budget.objects.filter(
        user=user_name, start_date=start_date, end_date=end_date
    ).order_by("-created_at")

    # Fetch template budget data for the same period
    template_budget_data = TemplateBudget.objects.filter(
        start_date=start_date, end_date=end_date
    ).order_by("-created_at")

    # Generate budget values and graph data
    (
        all_budgets,
        budget_graph_data,
        budget_values,
        budget_currency,
        list_of_months,
        current_budget_names_list,
        budgets_dict,
        income_bdgt_dict,
        total_bgt_income,
    ) = make_budgets_values(user_name, budget_data, "budget_page")
    (
        template_all_budgets,
        _,
        _,
        _,
        template_list_of_months,
        _,
        _,
        template_income_bdgt_dict,
        template_total_bgt_income,
    ) = make_budgets_values(user_name, template_budget_data, "template_page")

    # COMPARE BUDGETS :-

    current_date = datetime.datetime.today().date()
    week_start, week_end = start_end_date(
        current_date, BudgetPeriods.WEEKLY.value)
    month_start, month_end = start_end_date(
        current_date, BudgetPeriods.MONTHLY.value)
    quart_end, quart_start = start_end_date(
        current_date, BudgetPeriods.QUARTERLY.value)
    yearly_start, yearly_end = start_end_date(
        current_date, BudgetPeriods.YEARLY.value)
    (
        monthly_budget_transaction_data,
        cmp_month_list,
        monthly_cmp_budgets_dict,
        monthly_cmp_transaction_budgets,
    ) = compare_budgets(user_name, month_start, month_end, current_budget_names_list)
    (
        week_budget_transaction_data,
        cmp_week_list,
        week_cmp_budgets_dict,
        week_cmp_transaction_budgets,
    ) = compare_budgets(user_name, week_start, week_end, current_budget_names_list)
    (
        quart_budget_transaction_data,
        cmp_quart_list,
        quart_cmp_budgets_dict,
        quart_cmp_transaction_budgets,
    ) = compare_budgets(user_name, quart_start, quart_end, current_budget_names_list)
    (
        yearly_budget_transaction_data,
        cmp_yearly_list,
        yearly_cmp_budgets_dict,
        yearly_cmp_transaction_budgets,
    ) = compare_budgets(user_name, yearly_start, yearly_end, current_budget_names_list)

    if not current_budget_names_list:
        budget_page = ""
        template_page = "active"

    weekly_daily_budget = {"weekly": {}, "daily": {}}
    total_budget = {"weekly": {}, "daily": {}}
    total_spent = {"weekly": {}, "daily": {}}
    total_left = {"weekly": {}, "daily": {}}

    # Populate the dictionaries with budget data
    for bdgt_list in all_budgets:
        if bdgt_list[5] == BudgetPeriods.DAILY.value:
            if bdgt_list[0] not in weekly_daily_budget["daily"]:
                weekly_daily_budget["daily"][bdgt_list[0]] = [bdgt_list]
            else:
                weekly_daily_budget["daily"][bdgt_list[0]].append(bdgt_list)
            if bdgt_list[0] not in total_budget["daily"]:
                total_budget["daily"][bdgt_list[0]] = bdgt_list[1]
            else:
                total_budget["daily"][bdgt_list[0]] += bdgt_list[1]
            if bdgt_list[0] not in total_spent["daily"]:
                total_spent["daily"][bdgt_list[0]] = bdgt_list[2]
            else:
                total_spent["daily"][bdgt_list[0]] += bdgt_list[2]
            if bdgt_list[0] not in total_left["daily"]:
                total_left["daily"][bdgt_list[0]] = bdgt_list[3]
            else:
                total_left["daily"][bdgt_list[0]] += bdgt_list[3]

        if bdgt_list[5] == BudgetPeriods.WEEKLY.value:
            if bdgt_list[0] not in weekly_daily_budget["weekly"]:
                weekly_daily_budget["weekly"][bdgt_list[0]] = [bdgt_list]
            else:
                weekly_daily_budget["weekly"][bdgt_list[0]].append(bdgt_list)
            if bdgt_list[0] not in total_budget["weekly"]:
                total_budget["weekly"][bdgt_list[0]] = bdgt_list[1]
            else:
                total_budget["weekly"][bdgt_list[0]] += bdgt_list[1]
            if bdgt_list[0] not in total_spent["weekly"]:
                total_spent["weekly"][bdgt_list[0]] = bdgt_list[2]
            else:
                total_spent["weekly"][bdgt_list[0]] += bdgt_list[2]
            if bdgt_list[0] not in total_left["weekly"]:
                total_left["weekly"][bdgt_list[0]] = bdgt_list[3]
            else:
                total_left["weekly"][bdgt_list[0]] += bdgt_list[3]

    for key, value in weekly_daily_budget.items():
        if key == "daily":
            if value:
                for k, v in value.items():
                    v.insert(
                        0,
                        [
                            v[0][0],
                            total_budget[key][k],
                            total_spent[key][k],
                            total_left[key][k],
                            v[0][4],
                        ],
                    )
        if key == "weekly":
            if value:
                for k, v in value.items():
                    v.insert(
                        0,
                        [
                            v[0][0],
                            total_budget[key][k],
                            total_spent[key][k],
                            total_left[key][k],
                            v[0][4],
                        ],
                    )

    # Fetch template budget data for rendering
    template_budget_data, template_values, template_name_list, template_graph_data = (
        get_template_budget()
    )

    # Calculate the left-over cash after expenses
    total_expense_list = budget_graph_data[0]["data"]
    left_over_cash = round(total_bgt_income - sum(total_expense_list), 2)
    context = {
        "left_over_cash": left_over_cash,
        "total_income": total_bgt_income,
        "income_bdgt_dict": income_bdgt_dict,
        "expenses_dict": budgets_dict,
        "all_budgets": all_budgets,
        "budget_graph_data": budget_graph_data,
        "cash_flow_names": ["Earned", "Spent"],
        "cash_flow_data": [
            {"name": "Amount", "data": [total_bgt_income, budget_values[0]]}
        ],
        "budget_names": current_budget_names_list,
        "list_of_months": list_of_months,
        "total_expense": sum(total_expense_list),
        "budget_graph_currency": budget_currency,
        "budget_bar_id": "#budgets-bar",
        "template_budget_bar_id": "#template-budgets-bar",
        "template_budget_graph_id": "#template_total_budget",
        "template_all_budgets": template_all_budgets,
        "template_budget_graph_data": template_graph_data,
        "template_budget_names": template_name_list,
        "template_list_of_months": template_list_of_months,
        "template_budget_graph_value": template_values,
        "template_budget_graph_currency": "$",
        "budget_key": BUDGET_KEYS,
        "budget_key_dumbs": json.dumps(BUDGET_KEYS),
        "current_month": current_month,
        "budget_graph_value": total_expense_list,
        "budget_graph_label": BUDGET_LABELS,
        "budget_graph_id": "#total_budget",
        "monthly_budget_transaction_data": monthly_budget_transaction_data,
        "week_budget_transaction_data": week_budget_transaction_data,
        "quart_budget_transaction_data": quart_budget_transaction_data,
        "yearly_budget_transaction_data": yearly_budget_transaction_data,
        "week_start": week_start,
        "week_end": week_end,
        "quart_start": quart_start,
        "quart_end": quart_end,
        "yearly_start": yearly_start,
        "yearly_end": yearly_end,
        "transaction_key": TRANSACTION_KEYS,
        "month_start": month_start,
        "month_end": month_end,
        "cmp_budget_value": cmp_month_list,
        "week_pie_chart": week_cmp_budgets_dict,
        "monthly_pie_chart": monthly_cmp_budgets_dict,
        "quart_pie_chart": quart_cmp_budgets_dict,
        "yearly_pie_chart": yearly_cmp_budgets_dict,
        "monthly_cmp_transaction_budgets": monthly_cmp_transaction_budgets,
        "week_cmp_transaction_budgets": week_cmp_transaction_budgets,
        "quart_cmp_transaction_budgets": quart_cmp_transaction_budgets,
        "yearly_cmp_transaction_budgets": yearly_cmp_transaction_budgets,
        "cmp_month_graph_id": "#cmp_month_budget",
        "cmp_week_list": cmp_week_list,
        "cmp_week_list_id": "#cmp_week_list",
        "cmp_quart_list": cmp_quart_list,
        "cmp_quart_list_id": "#cmp_quart_list",
        "cmp_yearly_list": cmp_yearly_list,
        "cmp_yearly_list_id": "#cmp_yearly_list",
        "budget_page": budget_page,
        "template_page": template_page,
        "weekly_daily_budget": weekly_daily_budget,
        "template_budget_data": template_budget_data,
    }

    return context


@login_required(login_url="/login")
def budget_list(request):
    """
    Renders the budget list page with translated labels and budget data.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered HTML page with budget data.
    """
    time.sleep(3)
    translated_data = {"earned": _("Earned"), "spending": _("Spending")}
    context = budgets_page_data(request, "active", "")
    context.update({"translated_data": json.dumps(translated_data)})
    return render(request, "budget/budget_list.html", context=context)


@login_required(login_url="/login")
def budgets_box(request):
    """
    Renders the budget box page with the user's budgets and a form for user budgets.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered HTML page with budgets and form data.
    """
    user_name = request.user

    selected_budget_id = request.session.get("default_budget_id", None)
    if selected_budget_id:
        selected_budget_id = int(selected_budget_id)

    selected_budget_id = request.session.get("default_budget_id", None)
    if selected_budget_id:
        selected_budget_id = int(selected_budget_id)

    # Fetch the existing user budgets
    user_budgets_qs = UserBudgets.objects.filter(user=user_name)
    budgets_qs = Budget.objects.filter(user=request.user)
    budgets = list(budgets_qs.values_list("name", flat=True).distinct())
    user_budgets = list(user_budgets_qs.values_list(
        "name", flat=True).distinct())

    # Form for creating new user budget
    form = UserBudgetsForm(request.POST or None)
    context = {
        "page": "budgets",
        "budgets_list": budgets,
        "user_budgets": user_budgets_qs,
        "user_budget_form": form,
        "selected_budget": selected_budget_id,
        "tour_api": Tour_APIs["budget_page"],
    }
    return render(request, "budget/budget_box.html", context)


@login_required(login_url="/login")
@login_required(login_url="/login")
def budgets_walk_through(request, pk):
    """
    Handle budget walk-through for a user. Process form submissions to create
    or update budgets, and prepare context data for rendering the budget
    walk-through page.

    Args:
        request: The HTTP request object.
        pk: The primary key of the user budget.

    Returns:
        HttpResponse: Rendered budget walk-through page with context data.
    """
    user_name = request.user
    if request.method == "POST":
        # Extract form data from the POST request
        category_group = request.POST["category_group"]
        category_name = request.POST["category_name"]
        category_obj = Category.objects.get(
            user=user_name, name=category_group)

        # Retrieve or create subcategory
        try:
            subcategory_obj = SubCategory.objects.get(
                name=category_name, category=category_obj
            )
        # To-Do  Remove bare except
        except:
            subcategory_obj = SubCategory.objects.create(
                name=category_name, category=category_obj
            )
        budget_amount = request.POST["amount"]
        budget_currency = request.POST["currency"]
        budget_start_date = request.POST["budget_date"]
        budget_period = request.POST["budget_period"]
        budget_auto = request.POST["auto_budget"]
        if budget_auto == "on":
            budget_auto = True
        budget_name = category_name
        budget_check = Budget.objects.filter(user=user_name, name=budget_name)
        if budget_check:
            return redirect("/budgets/current")

        # Process dates and budget period
        budget_start_date = datetime.datetime.strptime(
            budget_start_date, DateFormats.YYYY_MM_DD.value
        )
        budget_start_date = datetime.datetime.strptime(
            budget_start_date, DateFormats.YYYY_MM_DD.value
        )
        start_month_date, end_month_date = start_end_date(
            budget_start_date.date(), BudgetPeriods.MONTHLY.value
        )
        budget_end_date = get_period_date(
            budget_start_date, budget_period
        ) - relativedelta(days=1)

        # Create and save the budget object
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

        # If the budget period is quarterly, create budgets for the next 2 months
        if budget_period == BudgetPeriods.QUARTERLY.value:
            for _ in range(2):
                start_month_date = start_month_date + relativedelta(months=1)
                start_month_date, end_month_date = start_end_date(
                    start_month_date, BudgetPeriods.MONTHLY.value
                )
                save_budgets(
                    user_name,
                    start_month_date,
                    end_month_date,
                    budget_name,
                    budget_period,
                    budget_currency,
                    budget_amount,
                    budget_auto,
                    budget_start_date,
                    budget_end_date,
                    budget_amount,
                    budget_start_date,
                    subcategory_obj,
                    None,
                    budget_status=True,
                )
        # If the budget period is yearly, create budgets for the next 11 months
        if budget_period == BudgetPeriods.YEARLY.value:
            for _ in range(11):
                start_month_date = start_month_date + relativedelta(months=1)
                start_month_date, end_month_date = start_end_date(
                    start_month_date, BudgetPeriods.MONTHLY.value
                )
                save_budgets(
                    user_name,
                    start_month_date,
                    end_month_date,
                    budget_name,
                    budget_period,
                    budget_currency,
                    budget_amount,
                    budget_auto,
                    budget_start_date,
                    budget_end_date,
                    budget_amount,
                    budget_start_date,
                    subcategory_obj,
                    None,
                    budget_status=True,
                )
        create_budget_request()
        return redirect("/budgets/current")
    date_value = datetime.datetime.today().date()
    start_date, end_date = start_end_date(
        date_value, BudgetPeriods.MONTHLY.value)
    budget_data = Budget.objects.filter(
        user_budget=pk, user=user_name, start_date=start_date, end_date=end_date
    ).order_by("-created_at")
    user_budget_name = UserBudgets.objects.get(user=user_name, pk=pk).name
    income_categories = []
    bill_categories = []
    expense_categories = {}
    non_monthly_expense_categories = []
    goals_categories = []
    bills_dict = {"Bills": []}

    # Retrieve and categorize the user's subcategories
    category_qs = SubCategory.objects.filter(category__user=user_name)
    for sub_data in category_qs:
        if sub_data.category.name == CategoryTypes.INCOME.value:
            income_categories.append(sub_data.name)
        if sub_data.category.name == CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value:
            bill_categories.append(sub_data.name)
        if sub_data.category.name == CategoryTypes.NON_MONTHLY.value:
            non_monthly_expense_categories.append(sub_data.name)
        if sub_data.category.name == CategoryTypes.GOALS.value:
            goals_categories.append(sub_data.name)
        if sub_data.category.name not in (type.value for type in CategoryTypes):
            if sub_data.category.name in expense_categories:
                expense_categories[sub_data.category.name].append(
                    [
                        sub_data.name,
                        0.0,
                        0.0,
                        0.0,
                        "false",
                        str(start_date),
                        str(end_date),
                        "$",
                        0.0,
                    ]
                )
            else:
                expense_categories[sub_data.category.name] = [
                    [
                        sub_data.name,
                        0.0,
                        0.0,
                        0.0,
                        "false",
                        str(start_date),
                        str(end_date),
                        "$",
                        0.0,
                    ]
                ]

    # Generate budget values and update categories
    _, _, _, budget_currency, _, _, budgets_dict, income_bdgt_dict, _ = (
        make_budgets_values(user_name, budget_data, "budget_page")
    )

    # Retrieve and process bills associated with the user budget
    bills_qs = Bill.objects.filter(
        user=user_name, user_budget=pk, date__range=(start_date, end_date)
    ).order_by("-created_at")
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
        bill_start_date = datetime.datetime.strftime(
            bill_data.date, DateFormats.MON_DD_YYYY.value
        )

        # Retrieve and sum transactions related to the bill
        transaction_qs = Transaction.objects.filter(
            user=user_name,
            bill=bill_data,
            transaction_date__range=(start_date, end_date),
        ).order_by("transaction_date")
        current_spent_amount = 0
        for trans_data in transaction_qs:
            current_spent_amount += float(trans_data.amount)
        bill_bgt_list = [
            bill_name,
            bill_amount,
            current_spent_amount,
            bill_left_amount,
            bill_data.id,
            bill.frequency,
            bill_start_date,
            bill_start_date,
            bill_data.currency,
            bill_spent_amount,
        ]
        # Append bill data to the bills dictionary
        bills_dict["Bills"].append(bill_bgt_list)
        if bill_name in bill_categories:
            bill_categories.remove(bill_name)

    # Calculate the total expected and actual income
    total_income_expected = 0
    total_actual_income = 0

    if CategoryTypes.INCOME.value in income_bdgt_dict:
        for inc_data in income_bdgt_dict[CategoryTypes.INCOME.value]:
            total_income_expected += float(inc_data[1])
            total_actual_income += float(inc_data[2])
            if inc_data[0] in income_categories:
                income_categories.remove(inc_data[0])
    else:
        income_bdgt_dict[CategoryTypes.INCOME.value] = []
    for name in income_categories:
        income_bdgt_dict[CategoryTypes.INCOME.value].insert(
            0, [name, 0.0, 0.0, 0.0, "false", str(
                start_date), str(end_date), "$", 0.0]
        )

    # Insert uncategorized bills into the bills dictionary
    for name in bill_categories:
        bills_dict["Bills"].insert(
            0, [name, 0.0, 0.0, 0.0, "false", str(
                start_date), str(end_date), "$", 0.0]
        )

    # Retrieve the user's bank accounts and map them by account ID
    accounts_qs = Account.objects.filter(
        user=request.user, account_type__in=AccountTypes.list()
    )
    bank_accounts_dict = {}
    for account_data in accounts_qs:
        bank_accounts_dict[account_data.id] = account_data.name

    # Calculate the total expected and actual expenses
    total_expected_expenses = 0
    total_actual_expenses = 0
    for key in budgets_dict:
        if key in expense_categories:
            expense_categories[key] = budgets_dict[key]
            for exp_data in budgets_dict[key]:
                total_expected_expenses += float(exp_data[1])
                total_actual_expenses += float(exp_data[2])

    # Calculate the total expected and actual non-monthly expenses
    total_non_monthly_expected_expenses = 0
    total_non_monthly_actual_expenses = 0
    non_monthly_expenses_dict = {}
    if CategoryTypes.NON_MONTHLY.value in budgets_dict:
        for exp in budgets_dict[CategoryTypes.NON_MONTHLY.value]:
            non_monthly_expenses_dict.update({exp[0]: exp})
            total_non_monthly_expected_expenses += float(exp[1])
            total_non_monthly_actual_expenses += float(exp[2])

    # Calculate the total expected and actual goals expenses
    total_goals_expected = 0
    total_goals_actual = 0
    goals_dict = {}
    if CategoryTypes.GOALS.value in budgets_dict:
        for i in budgets_dict[CategoryTypes.GOALS.value]:
            goals_dict.update({i[0]: i})
            total_goals_expected += float(i[1])
            total_goals_actual += float(i[2])

    # Initialize index counter for displaying expenses
    index_counter = 1
    for _, expenses in expense_categories.items():
        for expense_data in expenses:
            expense_data.append(index_counter)  # Insert index at the beginning
            index_counter += 1

    context = {
        "user_budget_name": user_budget_name,
        "pk": pk,
        "income_bdgt_dict": income_bdgt_dict,
        "total_actual_income": total_actual_income,
        "total_income_expected": total_income_expected,
        "bills_dict": bills_dict,
        "total_actual_bill": total_actual_bill,
        "total_expected_bill": total_expected_bill,
        "expenses_dict": expense_categories,
        "non_monthly_expenses_dict": non_monthly_expenses_dict,
        "total_expected_expenses": total_expected_expenses,
        "total_actual_expenses": total_actual_expenses,
        "bank_accounts": bank_accounts_dict,
        "total_non_monthly_expected_expenses": total_non_monthly_expected_expenses,
        "total_non_monthly_actual_expenses": total_non_monthly_actual_expenses,
        "goals_dict": goals_dict,
        "total_goals_expected": total_goals_expected,
        "total_goals_actual": total_goals_actual,
        "index_counter": index_counter,
        "today_date": str(today_date),
        "page": "budgets",
        "category_icons": CATEGORY_ICONS,
        "subcategories": SUGGESTED_SUB_CATEGORIES,
        "excluded_subcategories": EXCLUDED_SUB_CATEGORIES,
    }

    return render(request, "budget/budget_walk_through.html", context=context)


@login_required(login_url="/login")
def budgets_income_walk_through(request):
    """
    Handles the income walk-through process for budgets. It allows users to
    create or update their income budgets and save transactions.

    Args:
        request: The HTTP request object.

    Returns:
        JsonResponse: A JSON response indicating success or failure.
        HttpResponse: The income walk-through page with relevant context.
    """
    user_name = request.user

    if request.method == "POST" and request.is_ajax():
        # Retrieve data from the POST request
        user_budget_id = request.POST.get("user_budget_id")
        budget_name = request.POST["name"]
        budget_exp_amount = float(request.POST["exp_amount"])
        budget_act_amount = float(request.POST["actual_amount"])
        budget_id = request.POST["id"]
        income_account_id = request.POST["income_account_id"]
        budget_left_amount = round(budget_exp_amount - budget_act_amount, 2)

        # Get the account and user budget objects
        account_obj = Account.objects.get(id=int(income_account_id))
        user_budget = UserBudgets.objects.get(pk=int(user_budget_id))

        # Check if the expected amount is greater than Zero to avoid ZeroDivisionError
        if budget_exp_amount == 0:
            return JsonResponse(
                {"status": "false", "message": "Budget amount cannot be 0"}
            )
            return JsonResponse(
                {"status": "false", "message": "Budget amount cannot be 0"}
            )

        # check subcategory exist or not
        try:
            sub_cat_obj = SubCategory.objects.get(
                category__user=user_name,
                category__name=CategoryTypes.INCOME.value,
                name=budget_name,
            )
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()
        # To-Do  Remove bare except
        except:
            sub_cat_obj = SubCategory()
            sub_cat_obj.category = Category.objects.get(
                user=user_name, name=CategoryTypes.INCOME.value
            )
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()

        if budget_id == "false":
            # If budget ID is "false", create a new budget
            budget_start_date = datetime.datetime.today().date()

            # Calculate the start and end dates for the budget period
            start_month_date, end_month_date = start_end_date(
                budget_start_date, BudgetPeriods.MONTHLY.value
            )
            budget_end_date = get_period_date(
                budget_start_date, BudgetPeriods.MONTHLY.value
            ) - relativedelta(days=1)

            # Check if a budget with the same name already exists
            try:
                budget_obj = Budget.objects.filter(
                    user=user_name,
                    user_budget=user_budget,
                    name=budget_name,
                    budget_start_date__range=(
                        start_month_date, end_month_date),
                )
                if budget_obj:
                    print("Budget already exists")
                    return JsonResponse(
                        {"status": "false", "message": "Budget Already Exists"}
                    )
                else:
                    budget_obj = Budget()
            # To-Do  Remove bare except
            except:
                budget_obj = Budget()

            # Set the budget properties and save it
            budget_obj.user_budget = user_budget
            budget_obj.user = user_name
            budget_obj.start_date = start_month_date
            budget_obj.end_date = end_month_date
            budget_obj.name = budget_name
            budget_obj.category = sub_cat_obj
            budget_obj.currency = "$"
            budget_obj.auto_pay = False
            budget_obj.auto_budget = False
            budget_obj.budget_period = BudgetPeriods.MONTHLY.value
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
            # If budget ID is not "false", update the existing budget
            budget_obj = Budget.objects.get(
                id=int(budget_id), user_budget=user_budget)
            # Checks if new values are added or not
            if (
                float(budget_obj.initial_amount) == budget_exp_amount
                and float(budget_obj.budget_spent) == budget_act_amount
            ):
                return JsonResponse({"status": "false", "message": "Values unchanged"})

            old_spend_amount = float(budget_obj.budget_spent)
            budget_obj.name = budget_name
            budget_obj.initial_amount = budget_exp_amount
            budget_obj.amount = budget_exp_amount
            budget_obj.budget_spent = budget_act_amount
            budget_obj.budget_left = budget_left_amount
            if income_account_id:
                budget_obj.account = account_obj
            budget_obj.save()
            if budget_act_amount >= old_spend_amount:
                budget_act_amount = round(
                    budget_act_amount - old_spend_amount, 2)

        if budget_act_amount > 0:
            # Update the account balance and save the transaction
            account_obj = Account.objects.get(id=int(income_account_id))
            remaining_amount = round(
                float(account_obj.available_balance) + budget_act_amount, 2
            )
            tag_obj, _ = Tag.objects.get_or_create(
                user=user_name, name="Incomes")
            transaction_date = datetime.datetime.today().date()
            save_transaction(
                user_name,
                sub_cat_obj.name,
                budget_act_amount,
                remaining_amount,
                transaction_date,
                sub_cat_obj,
                account_obj,
                tag_obj,
                False,
                True,
                None,
                budget_obj,
            )
            account_obj.available_balance = remaining_amount
            account_obj.transaction_count += 1
            account_obj.save()
        return JsonResponse({"status": "true"})

    income_category = SubCategory.objects.filter(
        category__user=user_name, category__name=CategoryTypes.INCOME.value
    )
    context = {
        "category_groups": CategoryTypes.INCOME.value,
        "income_category": income_category,
        "today_date": str(today_date),
    }
    context.update({"page": "budgets"})
    return render(request, "income/income_walk_through.html", context=context)


@login_required(login_url="/login")
def budgets_expenses_walk_through(request):
    """
    Handles the expenses walk-through process for budgets. It allows users to
    create, update, and manage their budget expenses based on categories and
    other inputs.

    Args:
        request: The HTTP request object.

    Returns:
        JsonResponse: A JSON response indicating success or failure.
        HttpResponse: The expenses walk-through page with the relevant context.
    """
    user_name = request.user
    if request.method == "POST" and request.is_ajax():
        # Retrieve data from the POST request
        user_budget_id = request.POST.get("user_budget_id")
        budget_name = request.POST["name"]
        category_name = request.POST["cat_name"]
        budget_exp_amount = float(request.POST["exp_amount"])
        budget_act_amount = float(request.POST["actual_amount"])
        budget_id = request.POST["id"]
        expense_account_id = request.POST["expenses_account_id"]
        budget_left_amount = round(budget_exp_amount - budget_act_amount, 2)
        budget_start_date = request.POST["budget_date"]
        budget_period = request.POST["budget_period"]

        # Get the account and user budget objects
        account_obj = Account.objects.get(id=int(expense_account_id))
        user_budget = UserBudgets.objects.get(pk=int(user_budget_id))

        # Check if the expected amount is greater than Zero to avoid ZeroDivisionError
        if budget_exp_amount == 0:
            return JsonResponse(
                {"status": "false", "message": "Budget amount cannot be 0"}
            )
            return JsonResponse(
                {"status": "false", "message": "Budget amount cannot be 0"}
            )

        # check subcategory exist or not
        try:
            sub_cat_obj = SubCategory.objects.get(
                category__user=user_name, category__name=category_name, name=budget_name
            )
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()
        # To-Do  Remove bare except / get or create
        except:
            try:
                category_obj = Category.objects.get(
                    user=user_name, name=category_name)
            except:
                category_obj = Category.objects.create(
                    user=user_name, name=category_name
                )

            sub_cat_obj = SubCategory()
            sub_cat_obj.category = Category.objects.get(
                user=user_name, name=category_name
            )
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()

        if budget_id == "false":
            # If budget ID is "false", create a new budget
            if budget_start_date:
                budget_start_date = datetime.datetime.strptime(
                    budget_start_date, DateFormats.YYYY_MM_DD.value
                )
            else:
                budget_start_date = datetime.datetime.today().date()

            # Calculate the start and end dates for the budget period
            start_month_date, end_month_date = start_end_date(
                budget_start_date, BudgetPeriods.MONTHLY.value
            )
            budget_end_date = get_period_date(
                budget_start_date, budget_period
            ) - relativedelta(days=1)

            # Check if a budget with the same name already exists
            try:
                budget_obj = Budget.objects.filter(
                    user=user_name,
                    user_budget=user_budget,
                    name=budget_name,
                    budget_start_date__range=(
                        start_month_date, end_month_date),
                )
                if budget_obj:
                    print("Budget already exists")
                    return JsonResponse(
                        {"status": "false", "message": "Budget Already Exists"}
                    )
                else:
                    budget_obj = Budget()
            # To-Do  Remove bare except
            except:
                budget_obj = Budget()

            # Set the budget properties and save it
            budget_obj.user_budget = user_budget
            budget_obj.user = user_name
            budget_obj.start_date = start_month_date
            budget_obj.end_date = end_month_date
            budget_obj.name = budget_name
            budget_obj.category = sub_cat_obj
            budget_obj.currency = "$"
            budget_obj.auto_pay = False
            budget_obj.auto_budget = False
            budget_obj.account = account_obj
            budget_obj.budget_period = budget_period
            budget_obj.initial_amount = budget_exp_amount
            budget_obj.amount = budget_exp_amount
            budget_obj.budget_spent = budget_act_amount
            budget_obj.budget_left = budget_left_amount
            budget_obj.created_at = budget_start_date
            budget_obj.ended_at = get_period_date(
                budget_start_date, budget_period
            ) - relativedelta(days=1)
            budget_obj.budget_start_date = budget_start_date
            budget_obj.save()

            # If the budget period is yearly, create budgets for the next 11 months
            if budget_period == BudgetPeriods.YEARLY.value:
                budget_amount = budget_exp_amount
                budget_currency = "$"
                budget_auto = False
                subcategory_obj = sub_cat_obj
                for month_value in range(11):
                    start_month_date = start_month_date + \
                        relativedelta(months=1)
                    start_month_date, end_month_date = start_end_date(
                        start_month_date, BudgetPeriods.MONTHLY.value
                    )
                    save_budgets(
                        user_name,
                        start_month_date,
                        end_month_date,
                        budget_name,
                        budget_period,
                        budget_currency,
                        budget_amount,
                        budget_auto,
                        budget_start_date,
                        budget_end_date,
                        budget_amount,
                        budget_start_date,
                        subcategory_obj,
                        None,
                        budget_status=True,
                    )
        else:
            # If budget ID is not "false", update the existing budget
            budget_obj = Budget.objects.get(
                id=int(budget_id), user_budget=user_budget)
            # Checks if new values are added or not
            if (
                float(budget_obj.initial_amount) == budget_exp_amount
                and float(budget_obj.budget_spent) == budget_act_amount
            ):
                return JsonResponse({"status": "false", "message": "Values unchanged"})

            old_spend_amount = float(budget_obj.budget_spent)
            budget_obj.name = budget_name
            budget_obj.initial_amount = budget_exp_amount
            budget_obj.amount = budget_exp_amount
            budget_obj.budget_spent = budget_act_amount
            budget_obj.budget_left = budget_left_amount
            budget_obj.budget_period = budget_period
            budget_obj.account = account_obj
            budget_obj.save()

            # Update budget amounts if actual amount has increased
            if budget_act_amount > old_spend_amount:
                budget_act_amount = round(
                    budget_act_amount - old_spend_amount, 2)
            if budget_period == BudgetPeriods.YEARLY.value:
                budget_amount = budget_exp_amount
                budget_currency = "$"
                budget_auto = False
                subcategory_obj = sub_cat_obj
                if budget_start_date:
                    budget_start_date = datetime.datetime.strptime(
                        budget_start_date, DateFormats.YYYY_MM_DD.value
                    )
                else:
                    budget_start_date = budget_obj.start_date
                start_month_date, end_month_date = start_end_date(
                    budget_start_date, BudgetPeriods.MONTHLY.value
                )
                budget_end_date = get_period_date(
                    budget_start_date, budget_period
                ) - relativedelta(days=1)
                for month_value in range(11):
                    start_month_date = start_month_date + \
                        relativedelta(months=1)
                    start_month_date, end_month_date = start_end_date(
                        start_month_date, BudgetPeriods.MONTHLY.value
                    )
                    save_budgets(
                        user_name,
                        start_month_date,
                        end_month_date,
                        budget_name,
                        budget_period,
                        budget_currency,
                        budget_amount,
                        budget_auto,
                        budget_start_date,
                        budget_end_date,
                        budget_amount,
                        budget_start_date,
                        subcategory_obj,
                        None,
                        budget_status=True,
                    )

        if budget_act_amount > 0:
            # Update the account balance and save the transaction
            account_obj = Account.objects.get(id=int(expense_account_id))
            remaining_amount = round(
                float(account_obj.available_balance) - budget_act_amount, 2
            )
            tag_obj, _ = Tag.objects.get_or_create(
                user=user_name, name=category_name)
            transaction_date = datetime.datetime.today().date()
            save_transaction(
                user_name,
                sub_cat_obj.name,
                budget_act_amount,
                remaining_amount,
                transaction_date,
                sub_cat_obj,
                account_obj,
                tag_obj,
                True,
                True,
                None,
                budget_obj,
            )
            account_obj.available_balance = remaining_amount
            account_obj.transaction_count += 1
            account_obj.save()

        return JsonResponse({"status": "true"})

    context = {"page": "budgets"}
    return render(request, "expenses/expense_walk_through.html", context=context)


@login_required(login_url="/login")
def budgets_non_monthly_expenses_walk_through(request):
    """
    Handles the non-monthly expenses walk-through process for budgets.
    It allows users to create, update, and manage their budget expenses
    based on categories and other inputs.

    Args:
        request: The HTTP request object.

    Returns:
        JsonResponse: A JSON response indicating success or failure.
        HttpResponse: The non-monthly expenses walk-through page with the
        relevant context.
    """
    user_name = request.user
    if request.method == "POST" and request.is_ajax():
        # Retrieve data from the POST request
        user_budget_id = request.POST.get("user_budget_id")
        budget_name = request.POST["name"]
        category_name = CategoryTypes.NON_MONTHLY.value
        budget_exp_amount = float(request.POST["exp_amount"])
        budget_act_amount = float(request.POST["actual_amount"])
        budget_id = request.POST["id"]
        expense_account_id = request.POST["non_monthly_expenses_account_id"]
        budget_period = request.POST["budget_period"]
        budget_start_date = request.POST["budget_date"]
        # print("budget_date",budget_date)

        # Get the account and user budget objects
        account_obj = Account.objects.get(id=int(expense_account_id))
        budget_left_amount = round(budget_exp_amount - budget_act_amount, 2)
        user_budget = UserBudgets.objects.get(pk=int(user_budget_id))

        # Check if the expected amount is greater than Zero to avoid ZeroDivisionError
        if budget_exp_amount == 0:
            return JsonResponse(
                {"status": "false", "message": "Budget amount cannot be 0"}
            )
            return JsonResponse(
                {"status": "false", "message": "Budget amount cannot be 0"}
            )

        # check subcategory exist or not
        try:
            sub_cat_obj = SubCategory.objects.get(
                category__user=user_name, category__name=category_name, name=budget_name
            )
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()
        # To-Do  Remove bare except
        except:
            try:
                category_obj = Category.objects.get(
                    user=user_name, name=category_name)
            except:
                category_obj = Category.objects.create(
                    user=user_name, name=category_name
                )

            sub_cat_obj = SubCategory()
            sub_cat_obj.category = Category.objects.get(
                user=user_name, name=category_name
            )
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()

        if budget_id == "false":
            # If budget ID is "false", create a new budget
            if budget_start_date:
                budget_start_date = datetime.datetime.strptime(
                    budget_start_date, DateFormats.YYYY_MM_DD.value
                )
            else:
                budget_start_date = datetime.datetime.today().date()

            # Calculate the start and end dates for the budget period
            start_month_date, end_month_date = start_end_date(
                budget_start_date, BudgetPeriods.MONTHLY.value
            )
            budget_end_date = get_period_date(
                budget_start_date, budget_period
            ) - relativedelta(days=1)

            # Check if a budget with the same name already exists
            try:
                budget_obj = Budget.objects.filter(
                    user=user_name,
                    user_budget=user_budget,
                    name=budget_name,
                    budget_start_date__range=(
                        start_month_date, end_month_date),
                )
                if budget_obj:
                    print("Budget already exists")
                    return JsonResponse(
                        {"status": "false", "message": "Budget Already Exists"}
                    )
                else:
                    budget_obj = Budget()
            # To-Do  Remove bare except
            except:
                budget_obj = Budget()

            # Set the budget properties and save it
            budget_obj.user_budget = user_budget
            budget_obj.user = user_name
            budget_obj.start_date = start_month_date
            budget_obj.end_date = end_month_date
            budget_obj.name = budget_name
            budget_obj.category = sub_cat_obj
            budget_obj.currency = "$"
            budget_obj.auto_pay = False
            budget_obj.auto_budget = False
            budget_obj.budget_period = budget_period
            budget_obj.initial_amount = budget_exp_amount
            budget_obj.amount = budget_exp_amount
            budget_obj.account = account_obj
            budget_obj.budget_spent = budget_act_amount
            budget_obj.budget_left = budget_left_amount
            budget_obj.created_at = budget_start_date
            budget_obj.ended_at = get_period_date(
                budget_start_date, budget_period
            ) - relativedelta(days=1)
            budget_obj.budget_start_date = budget_start_date
            budget_obj.save()
            if budget_period == BudgetPeriods.YEARLY.value:
                budget_amount = budget_exp_amount
                budget_currency = "$"
                budget_auto = False
                subcategory_obj = sub_cat_obj
                for month_value in range(11):
                    start_month_date = start_month_date + \
                        relativedelta(months=1)
                    start_month_date, end_month_date = start_end_date(
                        start_month_date, BudgetPeriods.MONTHLY.value
                    )
                    save_budgets(
                        user_name,
                        start_month_date,
                        end_month_date,
                        budget_name,
                        budget_period,
                        budget_currency,
                        budget_amount,
                        budget_auto,
                        budget_start_date,
                        budget_end_date,
                        budget_amount,
                        budget_start_date,
                        subcategory_obj,
                        None,
                        budget_status=True,
                    )
        else:
            # If budget ID is not "false", update the existing budget
            budget_obj = Budget.objects.get(
                id=int(budget_id), user_budget=user_budget)
            # Checks if new values are added or not
            if (
                float(budget_obj.initial_amount) == budget_exp_amount
                and float(budget_obj.budget_spent) == budget_act_amount
            ):
                return JsonResponse({"status": "false", "message": "Values unchanged"})

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
                budget_act_amount = round(
                    budget_act_amount - old_spend_amount, 2)

            if budget_period == BudgetPeriods.YEARLY.value:
                budget_amount = budget_exp_amount
                budget_currency = "$"
                budget_auto = False
                subcategory_obj = sub_cat_obj
                if budget_start_date:
                    budget_start_date = datetime.datetime.strptime(
                        budget_start_date, DateFormats.YYYY_MM_DD.value
                    )
                else:
                    budget_start_date = budget_obj.start_date
                start_month_date, end_month_date = start_end_date(
                    budget_start_date, BudgetPeriods.MONTHLY.value
                )
                budget_end_date = get_period_date(
                    budget_start_date, budget_period
                ) - relativedelta(days=1)
                for month_value in range(11):
                    start_month_date = start_month_date + \
                        relativedelta(months=1)
                    start_month_date, end_month_date = start_end_date(
                        start_month_date, BudgetPeriods.MONTHLY.value
                    )
                    save_budgets(
                        user_name,
                        start_month_date,
                        end_month_date,
                        budget_name,
                        budget_period,
                        budget_currency,
                        budget_amount,
                        budget_auto,
                        budget_start_date,
                        budget_end_date,
                        budget_amount,
                        budget_start_date,
                        subcategory_obj,
                        None,
                        budget_status=True,
                    )

        if budget_act_amount > 0:
            # Update the account balance and save the transaction
            account_obj = Account.objects.get(id=int(expense_account_id))
            remaining_amount = round(
                float(account_obj.available_balance) - budget_act_amount, 2
            )
            tag_obj, _ = Tag.objects.get_or_create(
                user=user_name, name=category_name)
            transaction_date = datetime.datetime.today().date()
            save_transaction(
                user_name,
                sub_cat_obj.name,
                budget_act_amount,
                remaining_amount,
                transaction_date,
                sub_cat_obj,
                account_obj,
                tag_obj,
                True,
                True,
                None,
                budget_obj,
            )
            account_obj.available_balance = remaining_amount
            account_obj.transaction_count += 1
            account_obj.save()

        return JsonResponse({"status": "true"})
    non_monthly_expenses_category = SubCategory.objects.filter(
        category__user=user_name, category__name=CategoryTypes.NON_MONTHLY.value
    )
    context = {
        "category_groups": CategoryTypes.NON_MONTHLY.value,
        "non_monthly_expenses_category": non_monthly_expenses_category,
        "today_date": str(today_date),
    }
    context.update({"page": "budgets"})
    return render(
        request,
        "non_monthly_expenses/non_monthly_expense_walk_through.html",
        context=context,
    )


@login_required(login_url="/login")
def budgets_goals_walk_through(request):
    """
    Handles the goals walk-through process for budgets. It allows users to
    create, update, and manage their budget goals based on categories and
    other inputs.

    Args:
        request: The HTTP request object.

    Returns:
        JsonResponse: A JSON response indicating success or failure.
        HttpResponse: The goals walk-through page with the relevant context.
    """
    user_name = request.user
    print("request data======>", request.POST)
    if request.method == "POST" and request.is_ajax():
        # Retrieve data from the POST request
        user_budget_id = request.POST.get("user_budget_id")
        budget_name = request.POST["name"]
        category_name = CategoryTypes.GOALS.value  # request.POST['cat_name']
        budget_exp_amount = float(request.POST["goal_amount"])
        budget_act_amount = float(request.POST["actual_amount"])
        budget_id = request.POST["id"]
        goal_account_id = request.POST["goals_account_id"]
        budget_left_amount = round(budget_exp_amount - budget_act_amount, 2)

        # Get the account and user budget objects
        account_obj = Account.objects.get(id=int(goal_account_id))
        account_name = account_obj.name
        goal_date = request.POST["goal_date"]
        if goal_date == "":
            goal_date = None
        user_budget = UserBudgets.objects.get(pk=int(user_budget_id))

        # Check if the expected amount is greater than Zero to avoid ZeroDivisionError
        if budget_exp_amount == 0:
            return JsonResponse(
                {"status": "false", "message": "Budget amount cannot be 0"}
            )
            return JsonResponse(
                {"status": "false", "message": "Budget amount cannot be 0"}
            )

        # check subcategory exist or not
        try:
            sub_cat_obj = SubCategory.objects.get(
                category__user=user_name, category__name=category_name, name=budget_name
            )
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()
        # To-Do  Remove bare except
        except:
            try:
                category_obj = Category.objects.get(
                    user=user_name, name=category_name)
            except:
                category_obj = Category.objects.create(
                    user=user_name, name=category_name
                )

            sub_cat_obj = SubCategory()
            sub_cat_obj.category = Category.objects.get(
                user=user_name, name=category_name
            )
            sub_cat_obj.name = budget_name
            sub_cat_obj.save()

        if budget_id == "false":
            # If budget ID is "false", create a new budget
            budget_start_date = datetime.datetime.today().date()
            start_month_date, end_month_date = start_end_date(
                budget_start_date, BudgetPeriods.MONTHLY.value
            )
            budget_end_date = get_period_date(
                budget_start_date, BudgetPeriods.MONTHLY.value
            ) - relativedelta(days=1)

            # Check if a budget with the same name already exists
            try:
                budget_obj = Budget.objects.filter(
                    user=user_name,
                    user_budget=user_budget,
                    name=budget_name,
                    budget_start_date__range=(
                        start_month_date, end_month_date),
                )
                if budget_obj:
                    print("Budget already exists")
                    return JsonResponse(
                        {"status": "false", "message": "Budget Already Exists"}
                    )
                else:
                    budget_obj = Budget()
            # To-Do  Remove bare except
            except:
                budget_obj = Budget()

            # Set the budget properties and save it
            budget_obj.user_budget = user_budget
            budget_obj.user = user_name
            budget_obj.start_date = start_month_date
            budget_obj.end_date = end_month_date
            budget_obj.name = budget_name
            budget_obj.category = sub_cat_obj
            budget_obj.currency = "$"
            budget_obj.auto_pay = False
            budget_obj.auto_budget = False
            budget_obj.budget_period = BudgetPeriods.MONTHLY.value
            budget_obj.initial_amount = budget_exp_amount
            budget_obj.account = account_obj
            budget_obj.amount = budget_exp_amount
            budget_obj.budget_spent = budget_act_amount
            budget_obj.budget_left = budget_left_amount
            budget_obj.created_at = budget_start_date
            budget_obj.ended_at = budget_end_date
            budget_obj.budget_start_date = budget_start_date
            try:
                goal_obj = Goal.objects.get(
                    user_budget=user_budget, label=sub_cat_obj)
                # If goal already exists, it'll allocate the budget actual amount to goals
                if goal_obj:
                    budget_obj.save()
                    goal_obj.allocate_amount += budget_act_amount
                    goal_obj.budget_amount += budget_act_amount
                    goal_obj.save()
                    message = "Goal already exists, Budget created!!"
            # To-Do  Remove bare except
            except:
                # If goal doesn't exist, creates a new one
                goal_obj = Goal()
                goal_obj.user = user_name
                goal_obj.user_budget = user_budget
                goal_obj.account = account_obj
                goal_obj.goal_amount = budget_exp_amount
                goal_obj.currency = account_obj.currency
                goal_obj.goal_date = goal_date
                goal_obj.label = sub_cat_obj
                goal_obj.allocate_amount = budget_act_amount
                goal_obj.budget_amount += budget_act_amount
                goal_obj.save()
                budget_obj.save()
                message = ""
        else:
            budget_obj = Budget.objects.get(
                id=int(budget_id), user_budget=user_budget)
            # Checks if new values are added or not
            if (
                float(budget_obj.initial_amount) == budget_exp_amount
                and float(budget_obj.budget_spent) == budget_act_amount
            ):
                return JsonResponse({"status": "true", "message": "Values unchanged"})

            old_spend_amount = float(budget_obj.budget_spent)
            budget_obj.name = budget_name
            budget_obj.initial_amount = budget_exp_amount
            budget_obj.amount = budget_exp_amount
            budget_obj.budget_spent = budget_act_amount
            budget_obj.budget_left = budget_left_amount
            budget_obj.account = account_obj
            try:
                goal_obj = Goal.objects.get(
                    user=user_name, label=budget_obj.category)
                if goal_date != None:
                    goal_obj.goal_date = goal_date
                goal_obj.allocate_amount += round(
                    budget_act_amount - old_spend_amount, 2
                )
                goal_obj.budget_amount += round(budget_act_amount -
                                                old_spend_amount, 2)
                goal_obj.save()
                message = ""
            # To-Do  Remove bare except
            except:
                # If budget exist, but the Goal doesn't , It will create a goal with
                # Expected amount as goal amount and transacation amount as budget_amount
                # and allocate amount
                goal_obj = Goal()
                goal_obj.user = user_name
                goal_obj.user_budget = user_budget
                goal_obj.account = account_obj
                goal_obj.goal_amount = budget_exp_amount
                goal_obj.currency = account_obj.currency
                goal_obj.goal_date = goal_date
                goal_obj.label = sub_cat_obj
                goal_obj.allocate_amount = round(
                    budget_act_amount - old_spend_amount, 2
                )
                goal_obj.budget_amount += round(budget_act_amount -
                                                old_spend_amount, 2)
                goal_obj.save()
                message = "Goal created successfully!!"
            budget_obj.save()
            if budget_act_amount > old_spend_amount:
                budget_act_amount = round(
                    budget_act_amount - old_spend_amount, 2)

        if budget_act_amount > 0:
            # Update the account balance and save the transaction
            account_obj = Account.objects.get(id=int(goal_account_id))
            remaining_amount = round(
                float(account_obj.available_balance) - budget_act_amount, 2
            )
            tag_obj, _ = Tag.objects.get_or_create(
                user=user_name, name=category_name)
            transaction_date = datetime.datetime.today().date()
            save_transaction(
                user_name,
                sub_cat_obj.name,
                budget_act_amount,
                remaining_amount,
                transaction_date,
                sub_cat_obj,
                account_obj,
                tag_obj,
                True,
                True,
                None,
                budget_obj,
            )
            account_obj.available_balance = remaining_amount
            account_obj.transaction_count += 1
            account_obj.save()

        return JsonResponse({"status": "true", "message": message})
    goals_category = SubCategory.objects.filter(
        category__user=user_name, category__name=CategoryTypes.GOALS.value
    )
    context = {
        "category_groups": CategoryTypes.GOALS.value,
        "goals_category": goals_category,
        "today_date": str(today_date),
    }
    context.update({"page": "budgets"})
    return render(request, "goal/goals_walk_through.html")


@login_required(login_url="/login")
def current_budget_box(request, pk):
    """
    Renders the current budget overview for a specified user budget. It calculates
    budget data, bills, and transactions within the selected or current month, and
    prepares this data for visualization.

    Args:
        request: The HTTP request object.
        pk: The primary key of the UserBudgets object.

    Returns:
        HttpResponse: The rendered current budget overview page with relevant context.
    """
    user_name = request.user
    user_budget = UserBudgets.objects.get(user=user_name, pk=pk)

    # Determine the date range based on user selection or current month
    if request.method == "POST":
        month_name = "01-" + request.POST["select_period"]
        date_value = datetime.datetime.strptime(
            month_name, DateFormats.DD_MON_YYYY.value
        ).date()
        current_month = datetime.datetime.strftime(
            date_value, DateFormats.MON_YYYY.value
        )
        start_date, end_date = start_end_date(
            date_value, BudgetPeriods.MONTHLY.value)
    else:
        date_value = datetime.datetime.today().date()
        current_month = datetime.datetime.strftime(
            date_value, DateFormats.MON_YYYY.value
        )
        start_date, end_date = start_end_date(
            date_value, BudgetPeriods.MONTHLY.value)

    # Fetch budget data for the current period
    budget_data = Budget.objects.filter(
        user=user_name,
        user_budget=user_budget,
        start_date=start_date,
        end_date=end_date,
    ).order_by("-created_at")

    # Calculate budget values and prepare data for budget graph
    (
        all_budgets,
        budget_graph_data,
        budget_values,
        budget_currency,
        list_of_months,
        current_budget_names_list,
        budgets_dict,
        income_bdgt_dict,
        total_bgt_income,
    ) = make_budgets_values(user_name, budget_data, "budget_page")

    # Fetch bills for the current period and calculate related expenses
    bills_qs = Bill.objects.filter(
        user=user_name, user_budget=user_budget, date__range=(
            start_date, end_date)
    ).order_by("-created_at")

    # Initialize a dictionary for weekly/daily bills
    week_daily_dict = {}
    for bill_data in bills_qs:
        bill = bill_data.bill_details
        bill_name = bill.label
        bill_amount = float(bill_data.amount)
        bill_left_amount = float(bill_data.remaining_amount)
        bill_spent_amount = round(bill_amount - bill_left_amount, 2)
        bill_start_date = datetime.datetime.strftime(
            bill_data.date, DateFormats.MON_DD_YYYY.value
        )

        # Fetch transactions related to the bill
        transaction_qs = Transaction.objects.filter(
            user=user_name,
            bill=bill_data,
            transaction_date__range=(start_date, end_date),
        ).order_by("transaction_date")
        current_spent_amount = 0
        for trans_data in transaction_qs:
            current_spent_amount += float(trans_data.amount)

        # Update budget graph data
        if budget_values:
            budget_values[0] += current_spent_amount
            budget_graph_data[0]["data"].append(current_spent_amount)
            budget_graph_data[1]["data"].append(bill_left_amount)
            budget_graph_data[2]["data"].append(0)

        # Add bill to the list of current budget names
        current_budget_names_list.append(bill_name)
        bill_bgt_list = [
            bill_name,
            bill_amount,
            current_spent_amount,
            bill_left_amount,
            bill.id,
            bill.frequency,
            bill_start_date,
            bill_start_date,
            bill_data.currency,
            bill_spent_amount,
        ]

        # Categorize the bill based on its frequency
        if bill.frequency not in (
            BudgetPeriods.DAILY.value,
            BudgetPeriods.WEEKLY.value,
        ):
            if CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value in budgets_dict:
                budgets_dict[CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value].append(
                    bill_bgt_list
                )
            else:
                budgets_dict[CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value] = [
                    bill_bgt_list
                ]
        else:
            if bill_name in week_daily_dict:
                week_daily_dict[bill_name][0] += bill_amount
                week_daily_dict[bill_name][1] += current_spent_amount
                week_daily_dict[bill_name][2] += bill_left_amount
                week_daily_dict[bill_name][3].append(bill_bgt_list)
            else:
                week_daily_dict[bill_name] = [
                    bill_amount,
                    current_spent_amount,
                    bill_left_amount,
                    [bill_bgt_list],
                ]
    # Adjust total expense list and budget names for weekly/daily bills
    total_expense_list = budget_graph_data[0]["data"]
    if CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value in budgets_dict:
        for key, value in week_daily_dict.items():
            value[3].insert(
                0,
                [
                    key,
                    value[0],
                    value[1],
                    value[2],
                    value[3][0][4],
                    value[3][0][5],
                    value[3][0][6],
                    value[3][0][6],
                    value[3][0][8],
                    value[1],
                ],
            )
            budgets_dict[CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value].append(
                [key, 0, 0, 0, 0, value[3][0][5], value[3]]
            )
            week_bgt_len = len(value[3]) - 1
            for week_index in range(week_bgt_len):
                current_index = current_budget_names_list.index(key)
                if week_index == week_bgt_len - 1:
                    total_expense_list[current_index] = value[1]
                else:
                    total_expense_list.pop(current_index)
                    current_budget_names_list.pop(current_index)

    # Calculate leftover cash
    left_over_cash = round(total_bgt_income - sum(total_expense_list), 2)

    # Fetch and combine Bills and Budgets related transaction from a user budget
    bgt_transaction_data = Transaction.objects.filter(
        user=user_name,
        budgets__isnull=False,
        budgets__user_budget=user_budget,
        transaction_date__range=(start_date, end_date),
    ).order_by("transaction_date")
    bill_transaction_data = Transaction.objects.filter(
        user=user_name,
        bill__isnull=False,
        bill__user_budget=user_budget,
        transaction_date__range=(start_date, end_date),
    ).order_by("transaction_date")
    transaction_data = list(chain(bgt_transaction_data, bill_transaction_data))

    # Prepare translation data and list of months
    translated_data = {"earned": _("Earned"), "spending": _("Spending")}
    list_of_months = get_list_of_months(user_name, pk)

    context = {
        "pk": pk,
        "list_of_months": list_of_months,
        "current_month": current_month,
        "budget_graph_currency": budget_currency,
        "total_income": total_bgt_income,
        "income_bdgt_dict": income_bdgt_dict,
        "left_over_cash": left_over_cash,
        "total_expense": sum(total_expense_list),
        "expenses_dict": budgets_dict,
        "all_budgets": all_budgets,
        "budget_graph_data": budget_graph_data,
        "cash_flow_names": ["Earned", "Spent"],
        "budget_bar_id": "#budgets-bar",
        "cash_flow_data": [
            {"name": "Amount", "data": [
                total_bgt_income, sum(total_expense_list)]}
        ],
        "budget_names": current_budget_names_list,
        "budget_graph_value": total_expense_list,
        "budget_graph_id": "#total_budget",
        "transaction_key": TRANSACTION_KEYS[:-1],
        "transaction_data": transaction_data,
        "translated_data": json.dumps(translated_data),
        "page": "budgets",
        "category_icons": CATEGORY_ICONS,
        "budget_name": user_budget.name,
    }
    return render(request, "budget/current_budget_box.html", context=context)


# @login_required(login_url="/login")
# def compare_boxes(request):
#     user_name = request.user
#     return render(request, "budget/compare_boxes.html")


@login_required(login_url="/login")
def compare_different_budget_box(request):
    user_name = request.user
    budget_graph_currency = "$"
    budget_type = "Expenses"
    no_budgets = True
    # Fetch all the user budgets
    user_budgets = UserBudgets.objects.filter(user=user_name)
    no_budgets = True
    # Fetch all the user budgets
    user_budgets = UserBudgets.objects.filter(user=user_name)
    budgets_qs = Budget.objects.filter(user=user_name).exclude(
        category__category__name__in=["Bills", CategoryTypes.FUNDS.value]
    )
    bill_qs = Bill.objects.filter(user=user_name)
    if budgets_qs:
        budget_graph_currency = budgets_qs[0].currency
    if bill_qs:
        budget_graph_currency = bill_qs[0].currency
    budgets = list(budgets_qs.values_list("name", flat=True).distinct())
    bill_budgets = list(bill_qs.values_list("label", flat=True).distinct())
    budgets += bill_budgets
    total_budget_count = len(budgets)
    budget1_names = []
    budget2_names = []
    list_of_months = []
    list_of_months = []
    spending_amount_bgt1 = 0
    spending_amount_bgt2 = 0
    earned_amount_bgt1 = 0
    earned_amount_bgt2 = 0
    if budgets:
        earliest = Budget.objects.filter(
            user=user_name, start_date__isnull=False
        ).order_by("start_date")
        no_budgets = not bool(earliest)
        if no_budgets == False:
            start, end = earliest[0].start_date, earliest[len(
                earliest) - 1].start_date
            list_of_months = list(
                OrderedDict(
                    (
                        (start + datetime.timedelta(_)).strftime(
                            DateFormats.MON_YYYY.value
                        ),
                        None,
                    )
                    for _ in range((end - start).days + 1)
                ).keys()
            )
            split_budgets_count = int(total_budget_count / 2)
            budget1_names = budgets[0:split_budgets_count]
            budget2_names = budgets[split_budgets_count:total_budget_count]
        else:
            list_of_months = []
    user_bgt1 = user_bgt2 = None

    user_bgt1 = user_bgt2 = None

    if request.method == "POST":
        month_name = "01-" + request.POST["select_period"]
        user_bgt1 = request.POST.get("user_budget1")
        user_bgt2 = request.POST.get("user_budget2")
        if user_bgt1 and user_bgt2:
            user_bgt1, user_bgt2 = int(user_bgt1), int(user_bgt2)
        user_bgt1 = request.POST.get("user_budget1")
        user_bgt2 = request.POST.get("user_budget2")
        if user_bgt1 and user_bgt2:
            user_bgt1, user_bgt2 = int(user_bgt1), int(user_bgt2)
        budget1_names = request.POST.getlist("budget1_name")
        budget2_names = request.POST.getlist("budget2_name")
        date_value = datetime.datetime.strptime(
            month_name, DateFormats.DD_MON_YYYY.value
        ).date()
        current_month = datetime.datetime.strftime(
            date_value, DateFormats.MON_YYYY.value
        )
        start_date, end_date = start_end_date(
            date_value, BudgetPeriods.MONTHLY.value)
        user_bgt_obj1 = UserBudgets.objects.get(pk=user_bgt1)
        user_bgt_obj2 = UserBudgets.objects.get(pk=user_bgt2)

    else:
        date_value = datetime.datetime.today().date()
        current_month = datetime.datetime.strftime(
            date_value, DateFormats.MON_YYYY.value
        )
        start_date, end_date = start_end_date(
            date_value, BudgetPeriods.MONTHLY.value)
        user_bgt_obj1 = user_bgt_obj2 = None

    transaction_data_dict1 = {}
    transaction_data_dict2 = {}
    budget1_graph_value = []
    budget1_bar_value = [{"name": "Spent", "data": []}]
    budget2_graph_value = []
    budget2_bar_value = [{"name": "Spent", "data": []}]
    budget1_income_graph_value = []
    budget1_income_bar_value = [{"name": "Earned", "data": []}]
    budget2_income_graph_value = []
    budget2_income_bar_value = [{"name": "Earned", "data": []}]
    income_bgt1_names = []
    income_bgt2_names = []
    expense_bgt1_names = []
    expense_bgt2_names = []

    if user_bgt_obj1 and user_bgt_obj2:
        (
            budget1_bar_value,
            budget1_graph_value,
            budget1_income_graph_value,
            budget1_income_bar_value,
            expense_bgt1_names,
            income_bgt1_names,
            transaction_data_dict1,
            spending_amount_bgt1,
            earned_amount_bgt1,
        ) = get_cmp_diff_data(
            budget2_names,
            user_name,
            start_date,
            end_date,
            budget1_bar_value,
            budget1_graph_value,
            transaction_data_dict1,
            budget1_income_graph_value,
            budget1_income_bar_value,
            expense_bgt1_names,
            income_bgt1_names,
            spending_amount_bgt1,
            earned_amount_bgt1,
            user_bgt_obj1,
        )
    if user_bgt_obj1 and user_bgt_obj2:
        (
            budget1_bar_value,
            budget1_graph_value,
            budget1_income_graph_value,
            budget1_income_bar_value,
            expense_bgt1_names,
            income_bgt1_names,
            transaction_data_dict1,
            spending_amount_bgt1,
            earned_amount_bgt1,
        ) = get_cmp_diff_data(
            budget2_names,
            user_name,
            start_date,
            end_date,
            budget1_bar_value,
            budget1_graph_value,
            transaction_data_dict1,
            budget1_income_graph_value,
            budget1_income_bar_value,
            expense_bgt1_names,
            income_bgt1_names,
            spending_amount_bgt1,
            earned_amount_bgt1,
            user_bgt_obj1,
        )

        (
            budget2_bar_value,
            budget2_graph_value,
            budget2_income_graph_value,
            budget2_income_bar_value,
            expense_bgt2_names,
            income_bgt2_names,
            transaction_data_dict2,
            spending_amount_bgt2,
            earned_amount_bgt2,
        ) = get_cmp_diff_data(
            budget2_names,
            user_name,
            start_date,
            end_date,
            budget2_bar_value,
            budget2_graph_value,
            transaction_data_dict2,
            budget2_income_graph_value,
            budget2_income_bar_value,
            expense_bgt2_names,
            income_bgt2_names,
            spending_amount_bgt2,
            earned_amount_bgt2,
            user_bgt_obj2,
        )

    else:
        (
            budget1_bar_value,
            budget1_graph_value,
            budget1_income_graph_value,
            budget1_income_bar_value,
            expense_bgt1_names,
            income_bgt1_names,
            transaction_data_dict1,
            spending_amount_bgt1,
            earned_amount_bgt1,
        ) = get_cmp_diff_data(
            budget2_names,
            user_name,
            start_date,
            end_date,
            budget1_bar_value,
            budget1_graph_value,
            transaction_data_dict1,
            budget1_income_graph_value,
            budget1_income_bar_value,
            expense_bgt1_names,
            income_bgt1_names,
            spending_amount_bgt1,
            earned_amount_bgt1,
        )

        (
            budget2_bar_value,
            budget2_graph_value,
            budget2_income_graph_value,
            budget2_income_bar_value,
            expense_bgt2_names,
            income_bgt2_names,
            transaction_data_dict2,
            spending_amount_bgt2,
            earned_amount_bgt2,
        ) = get_cmp_diff_data(
            budget2_names,
            user_name,
            start_date,
            end_date,
            budget2_bar_value,
            budget2_graph_value,
            transaction_data_dict2,
            budget2_income_graph_value,
            budget2_income_bar_value,
            expense_bgt2_names,
            income_bgt2_names,
            spending_amount_bgt2,
            earned_amount_bgt2,
        )

    # Initialize a dictionary to group by category
    grouped_data = {}

    # Process transaction_data1 and group by category
    for name, data in transaction_data_dict1.items():
        category = data[0][2]  # Get the category
        amount = data[0][1]  # Get the amount
        if category not in grouped_data:
            grouped_data[category] = {"items": [], "total1": 0, "total2": 0}
        grouped_data[category]["items"].append(
            {
                "name": name,
                "amount1": amount,
                "amount2": 0,  # Will fill this later with transaction_data2
            }
        )
        grouped_data[category]["total1"] += amount

    # Process transaction_data2 and update grouped data
    for name, data in transaction_data_dict2.items():
        category = data[0][2]
        amount = data[0][1]
        if category not in grouped_data:
            grouped_data[category] = {"items": [], "total1": 0, "total2": 0}
        # Check if the item already exists in transaction_data1
        existing_item = next(
            (item for item in grouped_data[category]
             ["items"] if item["name"] == name),
            None,
        )
        if existing_item:
            existing_item["amount2"] = amount
        else:
            grouped_data[category]["items"].append(
                {
                    "name": name,
                    "amount1": 0,  # Not in transaction_data1
                    "amount2": amount,
                }
            )
        grouped_data[category]["total2"] += amount
        grouped_data[category]["total2"] += amount
    context = {
        "user_budgets": user_budgets,
        "user_budgets": user_budgets,
        "budgets": budgets,
        "list_of_months": list_of_months,
        "budget1_names": budget1_names,
        "budget2_names": budget2_names,
        "current_month": current_month,
        "total_spent_amount_bgt1": spending_amount_bgt1,
        "total_spent_amount_bgt2": spending_amount_bgt2,
        "total_earn_amount_bgt1": earned_amount_bgt1,
        "total_earn_amount_bgt2": earned_amount_bgt2,
        "transaction_data1": transaction_data_dict1,
        "transaction_data2": transaction_data_dict2,
        "budget_graph_currency": budget_graph_currency,
        "budget_names": expense_bgt1_names,
        "budget_graph_value": budget1_graph_value,
        "budget_graph_data": budget1_bar_value,
        "budget_graph_id": "#total_budget",
        "budget_bar_id": "#budgets-bar",
        "budget_names2": expense_bgt2_names,
        "budget_graph_value2": budget2_graph_value,
        "budget_graph_data2": budget2_bar_value,
        "budget_graph_id2": "#total_budget2",
        "budget_bar_id2": "#budgets-bar2",
        "budget_income_names": income_bgt1_names,
        "budget_income_graph_value": budget1_income_graph_value,
        "budget_income_graph_data": budget1_income_bar_value,
        "budget_income_graph_id": "#total_income_budget",
        "budget_income_bar_id": "#income-budgets-bar",
        "budget_income_names2": income_bgt2_names,
        "budget_income_graph_value2": budget2_income_graph_value,
        "budget_income_graph_data2": budget2_income_bar_value,
        "budget_income_graph_id2": "#total_income_budget2",
        "budget_income_bar_id2": "#income-budgets-bar2",
        "budget_type": budget_type,
        "page": "budgets",
        "no_budgets": no_budgets,
        "user_budget_1": user_bgt1,
        "user_budget_2": user_bgt2,
        "grouped_data": grouped_data,
        "category_icons": CATEGORY_ICONS,
        "tour_api": Tour_APIs["compare_budget_page"],
    }
    return render(request, "budget/compare_diff_bgt_box.html", context=context)


# def compare_different_budget_box(request):
#     user_name = request.user
#     budget_graph_currency = "$"
#     budget_type = "Expenses"
#     budgets_qs = Budget.objects.filter(user=user_name).exclude(
#         category__category__name__in=["Bills", CategoryTypes.FUNDS.value]
#     )
#     bill_qs = Bill.objects.filter(user=user_name)
#     if budgets_qs:
#         budget_graph_currency = budgets_qs[0].currency
#     if bill_qs:
#         budget_graph_currency = bill_qs[0].currency
#     budgets = list(budgets_qs.values_list("name", flat=True).distinct())
#     bill_budgets = list(bill_qs.values_list("label", flat=True).distinct())
#     budgets += bill_budgets
#     total_budget_count = len(budgets)
#     budget1_names = []
#     budget2_names = []
#     spending_amount_bgt1 = 0
#     spending_amount_bgt2 = 0
#     earned_amount_bgt1 = 0
#     earned_amount_bgt2 = 0
#     if budgets:
#         earliest = Budget.objects.filter(
#             user=user_name, start_date__isnull=False
#         ).order_by("start_date")
#         no_budgets = not bool(earliest)
#         if no_budgets == False:
#             start, end = earliest[0].start_date, earliest[len(earliest) - 1].start_date
#             list_of_months = list(
#                 OrderedDict(
#                     (
#                         (start + datetime.timedelta(_)).strftime(
#                             DateFormats.MON_YYYY.value
#                         ),
#                         None,
#                     )
#                     for _ in range((end - start).days + 1)
#                 ).keys()
#             )
#             split_budgets_count = int(total_budget_count / 2)
#             budget1_names = budgets[0:split_budgets_count]
#             budget2_names = budgets[split_budgets_count:total_budget_count]
#         else:
#             list_of_months = []
#     if request.method == "POST":
#         month_name = "01-" + request.POST["select_period"]
#         budget1_names = request.POST.getlist("budget1_name")
#         budget2_names = request.POST.getlist("budget2_name")
#         date_value = datetime.datetime.strptime(
#             month_name, DateFormats.DD_MON_YYYY.value
#         ).date()
#         current_month = datetime.datetime.strftime(
#             date_value, DateFormats.MON_YYYY.value
#         )
#         start_date, end_date = start_end_date(date_value, BudgetPeriods.MONTHLY.value)
#     else:
#         date_value = datetime.datetime.today().date()
#         current_month = datetime.datetime.strftime(
#             date_value, DateFormats.MON_YYYY.value
#         )
#         start_date, end_date = start_end_date(date_value, BudgetPeriods.MONTHLY.value)
#
#     transaction_data_dict1 = {}
#     transaction_data_dict2 = {}
#     budget1_graph_value = []
#     budget1_bar_value = [{"name": "Spent", "data": []}]
#     budget2_graph_value = []
#     budget2_bar_value = [{"name": "Spent", "data": []}]
#     budget1_income_graph_value = []
#     budget1_income_bar_value = [{"name": "Earned", "data": []}]
#     budget2_income_graph_value = []
#     budget2_income_bar_value = [{"name": "Earned", "data": []}]
#     income_bgt1_names = []
#     income_bgt2_names = []
#     expense_bgt1_names = []
#     expense_bgt2_names = []
#
#     (
#         budget1_bar_value,
#         budget1_graph_value,
#         budget1_income_graph_value,
#         budget1_income_bar_value,
#         expense_bgt1_names,
#         income_bgt1_names,
#         transaction_data_dict1,
#         spending_amount_bgt1,
#         earned_amount_bgt1,
#     ) = get_cmp_diff_data(
#         budget1_names,
#         user_name,
#         start_date,
#         end_date,
#         budget1_bar_value,
#         budget1_graph_value,
#         transaction_data_dict1,
#         budget1_income_graph_value,
#         budget1_income_bar_value,
#         expense_bgt1_names,
#         income_bgt1_names,
#         spending_amount_bgt1,
#         earned_amount_bgt1,
#     )
#
#     (
#         budget2_bar_value,
#         budget2_graph_value,
#         budget2_income_graph_value,
#         budget2_income_bar_value,
#         expense_bgt2_names,
#         income_bgt2_names,
#         transaction_data_dict2,
#         spending_amount_bgt2,
#         earned_amount_bgt2,
#     ) = get_cmp_diff_data(
#         budget2_names,
#         user_name,
#         start_date,
#         end_date,
#         budget2_bar_value,
#         budget2_graph_value,
#         transaction_data_dict2,
#         budget2_income_graph_value,
#         budget2_income_bar_value,
#         expense_bgt2_names,
#         income_bgt2_names,
#         spending_amount_bgt2,
#         earned_amount_bgt2,
#     )
#
#     # Fetch all bills and budgets
#     budget_details = Budget.objects.filter(
#         user=user_name, start_date=start_date, end_date=end_date
#     )
#     bill_details = Bill.objects.filter(
#         user=user_name, date__range=(start_date, end_date)
#     )
#     budget_dict = {}
#
#     # Update Bill and Budget Budgetted amount and Spent amount to budget_dict
#     for i in bill_details:
#         if i.label in budget1_names:
#             budget_dict.update(
#                 {
#                     i.label: [
#                         float(i.amount),
#                         float(i.amount) - float(i.remaining_amount),
#                         i.remaining_amount,
#                     ]
#                 }
#             )
#         if i.label in budget2_names:
#             budget_dict.update(
#                 {
#                     i.label: [
#                         float(i.amount),
#                         float(i.amount) - float(i.remaining_amount),
#                         i.remaining_amount,
#                     ]
#                 }
#             )
#
#     for i in budget_details:
#         if i.name in budget1_names:
#             budget_dict.update(
#                 {
#                     i.name: [
#                         float(i.initial_amount),
#                         i.budget_spent,
#                         float(i.initial_amount) - float(i.budget_spent),
#                     ]
#                 }
#             )
#         if i.name in budget2_names:
#             budget_dict.update(
#                 {
#                     i.name: [
#                         float(i.initial_amount),
#                         i.budget_spent,
#                         float(i.initial_amount) - float(i.budget_spent),
#                     ]
#                 }
#             )
#
#     context = {
#         "budgets": budgets,
#         "list_of_months": list_of_months,
#         "budget1_names": budget1_names,
#         "budget2_names": budget2_names,
#         "budget_dict": budget_dict,
#         "current_month": current_month,
#         "total_spent_amount_bgt1": spending_amount_bgt1,
#         "total_spent_amount_bgt2": spending_amount_bgt2,
#         "total_earn_amount_bgt1": earned_amount_bgt1,
#         "total_earn_amount_bgt2": earned_amount_bgt2,
#         "transaction_data1": transaction_data_dict1,
#         "transaction_data2": transaction_data_dict2,
#         "budget_graph_currency": budget_graph_currency,
#         "budget_names": expense_bgt1_names,
#         "budget_graph_value": budget1_graph_value,
#         "budget_graph_data": budget1_bar_value,
#         "budget_graph_id": "#total_budget",
#         "budget_bar_id": "#budgets-bar",
#         "budget_names2": expense_bgt2_names,
#         "budget_graph_value2": budget2_graph_value,
#         "budget_graph_data2": budget2_bar_value,
#         "budget_graph_id2": "#total_budget2",
#         "budget_bar_id2": "#budgets-bar2",
#         "budget_income_names": income_bgt1_names,
#         "budget_income_graph_value": budget1_income_graph_value,
#         "budget_income_graph_data": budget1_income_bar_value,
#         "budget_income_graph_id": "#total_income_budget",
#         "budget_income_bar_id": "#income-budgets-bar",
#         "budget_income_names2": income_bgt2_names,
#         "budget_income_graph_value2": budget2_income_graph_value,
#         "budget_income_graph_data2": budget2_income_bar_value,
#         "budget_income_graph_id2": "#total_income_budget2",
#         "budget_income_bar_id2": "#income-budgets-bar2",
#         "budget_type": budget_type,
#         "page": "budgets",
#         "no_budgets": no_budgets,
#     }
#     return render(request, "budget/compare_diff_bgt_box.html", context=context)


# def compare_different_budget_box(request):
#     user_name = request.user
#     budget_graph_currency = "$"
#     budget_type = "Expenses"
#     budgets_qs = Budget.objects.filter(user=user_name).exclude(
#         category__category__name__in=["Bills", CategoryTypes.FUNDS.value]
#     )
#     bill_qs = Bill.objects.filter(user=user_name)
#     if budgets_qs:
#         budget_graph_currency = budgets_qs[0].currency
#     if bill_qs:
#         budget_graph_currency = bill_qs[0].currency
#     budgets = list(budgets_qs.values_list("name", flat=True).distinct())
#     bill_budgets = list(bill_qs.values_list("label", flat=True).distinct())
#     budgets += bill_budgets
#     total_budget_count = len(budgets)
#     budget1_names = []
#     budget2_names = []
#     spending_amount_bgt1 = 0
#     spending_amount_bgt2 = 0
#     earned_amount_bgt1 = 0
#     earned_amount_bgt2 = 0
#     if budgets:
#         earliest = Budget.objects.filter(
#             user=user_name, start_date__isnull=False
#         ).order_by("start_date")
#         no_budgets = not bool(earliest)
#         if no_budgets == False:
#             start, end = earliest[0].start_date, earliest[len(earliest) - 1].start_date
#             list_of_months = list(
#                 OrderedDict(
#                     (
#                         (start + datetime.timedelta(_)).strftime(
#                             DateFormats.MON_YYYY.value
#                         ),
#                         None,
#                     )
#                     for _ in range((end - start).days + 1)
#                 ).keys()
#             )
#             split_budgets_count = int(total_budget_count / 2)
#             budget1_names = budgets[0:split_budgets_count]
#             budget2_names = budgets[split_budgets_count:total_budget_count]
#         else:
#             list_of_months = []
#     if request.method == "POST":
#         month_name = "01-" + request.POST["select_period"]
#         budget1_names = request.POST.getlist("budget1_name")
#         budget2_names = request.POST.getlist("budget2_name")
#         date_value = datetime.datetime.strptime(
#             month_name, DateFormats.DD_MON_YYYY.value
#         ).date()
#         current_month = datetime.datetime.strftime(
#             date_value, DateFormats.MON_YYYY.value
#         )
#         start_date, end_date = start_end_date(date_value, BudgetPeriods.MONTHLY.value)
#     else:
#         date_value = datetime.datetime.today().date()
#         current_month = datetime.datetime.strftime(
#             date_value, DateFormats.MON_YYYY.value
#         )
#         start_date, end_date = start_end_date(date_value, BudgetPeriods.MONTHLY.value)
#
#     transaction_data_dict1 = {}
#     transaction_data_dict2 = {}
#     budget1_graph_value = []
#     budget1_bar_value = [{"name": "Spent", "data": []}]
#     budget2_graph_value = []
#     budget2_bar_value = [{"name": "Spent", "data": []}]
#     budget1_income_graph_value = []
#     budget1_income_bar_value = [{"name": "Earned", "data": []}]
#     budget2_income_graph_value = []
#     budget2_income_bar_value = [{"name": "Earned", "data": []}]
#     income_bgt1_names = []
#     income_bgt2_names = []
#     expense_bgt1_names = []
#     expense_bgt2_names = []
#
#     (
#         budget1_bar_value,
#         budget1_graph_value,
#         budget1_income_graph_value,
#         budget1_income_bar_value,
#         expense_bgt1_names,
#         income_bgt1_names,
#         transaction_data_dict1,
#         spending_amount_bgt1,
#         earned_amount_bgt1,
#     ) = get_cmp_diff_data(
#         budget1_names,
#         user_name,
#         start_date,
#         end_date,
#         budget1_bar_value,
#         budget1_graph_value,
#         transaction_data_dict1,
#         budget1_income_graph_value,
#         budget1_income_bar_value,
#         expense_bgt1_names,
#         income_bgt1_names,
#         spending_amount_bgt1,
#         earned_amount_bgt1,
#     )
#
#     (
#         budget2_bar_value,
#         budget2_graph_value,
#         budget2_income_graph_value,
#         budget2_income_bar_value,
#         expense_bgt2_names,
#         income_bgt2_names,
#         transaction_data_dict2,
#         spending_amount_bgt2,
#         earned_amount_bgt2,
#     ) = get_cmp_diff_data(
#         budget2_names,
#         user_name,
#         start_date,
#         end_date,
#         budget2_bar_value,
#         budget2_graph_value,
#         transaction_data_dict2,
#         budget2_income_graph_value,
#         budget2_income_bar_value,
#         expense_bgt2_names,
#         income_bgt2_names,
#         spending_amount_bgt2,
#         earned_amount_bgt2,
#     )
#
#     # Fetch all bills and budgets
#     budget_details = Budget.objects.filter(
#         user=user_name, start_date=start_date, end_date=end_date
#     )
#     bill_details = Bill.objects.filter(
#         user=user_name, date__range=(start_date, end_date)
#     )
#     budget_dict = {}
#
#     # Update Bill and Budget Budgetted amount and Spent amount to budget_dict
#     for i in bill_details:
#         if i.label in budget1_names:
#             budget_dict.update(
#                 {
#                     i.label: [
#                         float(i.amount),
#                         float(i.amount) - float(i.remaining_amount),
#                         i.remaining_amount,
#                     ]
#                 }
#             )
#         if i.label in budget2_names:
#             budget_dict.update(
#                 {
#                     i.label: [
#                         float(i.amount),
#                         float(i.amount) - float(i.remaining_amount),
#                         i.remaining_amount,
#                     ]
#                 }
#             )
#
#     for i in budget_details:
#         if i.name in budget1_names:
#             budget_dict.update(
#                 {
#                     i.name: [
#                         float(i.initial_amount),
#                         i.budget_spent,
#                         float(i.initial_amount) - float(i.budget_spent),
#                     ]
#                 }
#             )
#         if i.name in budget2_names:
#             budget_dict.update(
#                 {
#                     i.name: [
#                         float(i.initial_amount),
#                         i.budget_spent,
#                         float(i.initial_amount) - float(i.budget_spent),
#                     ]
#                 }
#             )
#
#     context = {
#         "budgets": budgets,
#         "list_of_months": list_of_months,
#         "budget1_names": budget1_names,
#         "budget2_names": budget2_names,
#         "budget_dict": budget_dict,
#         "current_month": current_month,
#         "total_spent_amount_bgt1": spending_amount_bgt1,
#         "total_spent_amount_bgt2": spending_amount_bgt2,
#         "total_earn_amount_bgt1": earned_amount_bgt1,
#         "total_earn_amount_bgt2": earned_amount_bgt2,
#         "transaction_data1": transaction_data_dict1,
#         "transaction_data2": transaction_data_dict2,
#         "budget_graph_currency": budget_graph_currency,
#         "budget_names": expense_bgt1_names,
#         "budget_graph_value": budget1_graph_value,
#         "budget_graph_data": budget1_bar_value,
#         "budget_graph_id": "#total_budget",
#         "budget_bar_id": "#budgets-bar",
#         "budget_names2": expense_bgt2_names,
#         "budget_graph_value2": budget2_graph_value,
#         "budget_graph_data2": budget2_bar_value,
#         "budget_graph_id2": "#total_budget2",
#         "budget_bar_id2": "#budgets-bar2",
#         "budget_income_names": income_bgt1_names,
#         "budget_income_graph_value": budget1_income_graph_value,
#         "budget_income_graph_data": budget1_income_bar_value,
#         "budget_income_graph_id": "#total_income_budget",
#         "budget_income_bar_id": "#income-budgets-bar",
#         "budget_income_names2": income_bgt2_names,
#         "budget_income_graph_value2": budget2_income_graph_value,
#         "budget_income_graph_data2": budget2_income_bar_value,
#         "budget_income_graph_id2": "#total_income_budget2",
#         "budget_income_bar_id2": "#income-budgets-bar2",
#         "budget_type": budget_type,
#         "page": "budgets",
#         "no_budgets": no_budgets,
#     }
#     return render(request, "budget/compare_diff_bgt_box.html", context=context)


@login_required(login_url="/login")
def compare_target_budget_box(request):
    user_name = request.user
    budget_graph_currency = "$"
    budget_type = "Expenses"
    list_of_months = []
    list_of_months = []
    budgets_qs = Budget.objects.filter(user=user_name).exclude(
        category__category__name__in=["Bills", CategoryTypes.FUNDS.value]
    )
    bill_qs = Bill.objects.filter(user=user_name)
    if budgets_qs:
        budget_graph_currency = budgets_qs[0].currency
    if bill_qs:
        budget_graph_currency = bill_qs[0].currency
    budgets = list(budgets_qs.values_list("name", flat=True).distinct())
    bill_budgets = list(bill_qs.values_list("label", flat=True).distinct())
    budgets += bill_budgets
    total_budget_count = len(budgets)
    budget1_names = []
    spending_amount_bgt1 = 0
    earned_amount_bgt1 = 0
    if budgets:
        earliest = Budget.objects.filter(
            user=user_name, start_date__isnull=False
        ).order_by("start_date")
        start, end = earliest[0].start_date, earliest[len(
            earliest) - 1].start_date
        list_of_months = list(
            OrderedDict(
                (
                    (start + datetime.timedelta(_)).strftime(
                        DateFormats.MON_YYYY.value
                    ),
                    None,
                )
                for _ in range((end - start).days + 1)
            ).keys()
        )
        split_budgets_count = int(total_budget_count / 2)
        budget1_names = budgets[0:split_budgets_count]
    if request.method == "POST":
        month_name = "01-" + request.POST["select_period"]
        budget1_names = request.POST.getlist("budget1_name")
        date_value = datetime.datetime.strptime(
            month_name, DateFormats.DD_MON_YYYY.value
        ).date()
        current_month = datetime.datetime.strftime(
            date_value, DateFormats.MON_YYYY.value
        )
        start_date, end_date = start_end_date(
            date_value, BudgetPeriods.MONTHLY.value)
    else:
        date_value = datetime.datetime.today().date()
        current_month = datetime.datetime.strftime(
            date_value, DateFormats.MON_YYYY.value
        )
        start_date, end_date = start_end_date(
            date_value, BudgetPeriods.MONTHLY.value)

    transaction_data_dict1 = {}
    budget1_graph_value = []
    budget1_bar_value = [{"name": "Spent", "data": []}]
    budget1_income_graph_value = []
    budget1_income_bar_value = [{"name": "Earned", "data": []}]
    income_bgt1_names = []
    expense_bgt1_names = []

    (
        budget1_bar_value,
        budget1_graph_value,
        budget1_income_graph_value,
        budget1_income_bar_value,
        expense_bgt1_names,
        income_bgt1_names,
        transaction_data_dict1,
        spending_amount_bgt1,
        earned_amount_bgt1,
    ) = get_cmp_diff_data(
        budget1_names,
        user_name,
        start_date,
        end_date,
        budget1_bar_value,
        budget1_graph_value,
        transaction_data_dict1,
        budget1_income_graph_value,
        budget1_income_bar_value,
        expense_bgt1_names,
        income_bgt1_names,
        spending_amount_bgt1,
        earned_amount_bgt1,
    )
    # Fetch all bills and budgets
    budget_details = Budget.objects.filter(
        user=user_name, start_date=start_date, end_date=end_date
    )
    bill_details = Bill.objects.filter(
        user=user_name, date__range=(start_date, end_date)
    )
    budget_dict = {}

    # Update Bill and Budget Budgetted amount to budget_dict
    for i in bill_details:
        if i.label in budget1_names:
            budget_dict.update({i.label: i.amount})

    for i in budget_details:
        if i.name in budget1_names:
            budget_dict.update({i.name: i.initial_amount})

    context = {
        "budgets": budgets,
        "list_of_months": list_of_months,
        "budget1_names": budget1_names,
        "current_month": current_month,
        "total_spent_amount_bgt1": spending_amount_bgt1,
        "total_earn_amount_bgt1": earned_amount_bgt1,
        "transaction_data1": transaction_data_dict1,
        "budget_graph_currency": budget_graph_currency,
        "budget_names": expense_bgt1_names,
        "budget_graph_value": budget1_graph_value,
        "budget_graph_data": budget1_bar_value,
        "budget_graph_id": "#total_budget",
        "budget_bar_id": "#budgets-bar",
        "budget_income_names": income_bgt1_names,
        "budget_income_graph_value": budget1_income_graph_value,
        "budget_income_graph_data": budget1_income_bar_value,
        "budget_income_graph_id": "#total_income_budget",
        "budget_income_bar_id": "#income-budgets-bar",
        "budget_type": budget_type,
        "page": "budgets",
        "budget_dict": budget_dict,
        "tour_api": Tour_APIs["compare_target_budget_page"],
    }
    return render(request, "budget/compare_target_box.html", context=context)


@login_required(login_url="/login")
def sample_budget_box(request):
    """
    Renders the sample budget box page with budget and cash flow data.

    Args:
        request (HttpRequest): The HTTP request object.

    Returns:
        HttpResponse: The rendered HTML page with budget and cash flow data.
    """
    date_value = datetime.datetime.today().date()
    start_date, end_date = start_end_date(
        date_value, BudgetPeriods.MONTHLY.value)
    translated_data = {"earned": _("Earned"), "spending": _("Spending")}
    context = {
        "month_start": start_date,
        "month_end": end_date,
        "cash_flow_names": CASH_FLOW_NAMES,
        "cash_flow_data": CASH_FLOW_DATA,
        "budget_bar_id": "#budgets-bar",
        "budget_graph_data": BUDGET_GRAPH_DATA,
        "budget_names": BUDGET_NAMES,
        "budget_graph_id": "#total_budget",
        "budget_graph_value": BUDGET_GRAPH_VALUE,
        "budget_graph_currency": "$",
        "translated_data": json.dumps(translated_data),
        "page": "budgets",
        "tour_api": Tour_APIs["sample_budgets_page"],
    }
    return render(request, "budget/sample_budget_box.html", context=context)


@login_required(login_url="/login")
def set_default_budget(request):
    """
    Sets the default budget in the session based on user selection in POST data.
    If 'user_budget' is 'No', the session budget is removed. Otherwise, the
    selected budget is stored.

    Args:
        request: HttpRequest object containing POST data.

    Returns:
        HttpResponse: Redirects to the 'budgets' view.
    """

    if request.POST:
        user_budget = request.POST.get("user_budget")
        if user_budget != "No":
            # Store the selected budget in the session
            request.session["default_budget_id"] = user_budget
        else:
            # Delete the session
            request.session.pop("default_budget_id", None)
        return redirect("budgets")


@login_required(login_url="/login")
def set_default_budget(request):
    """
    Sets the default budget in the session based on user selection in POST data.
    If 'user_budget' is 'No', the session budget is removed. Otherwise, the
    selected budget is stored.

    Args:
        request: HttpRequest object containing POST data.

    Returns:
        HttpResponse: Redirects to the 'budgets' view.
    """

    if request.POST:
        user_budget = request.POST.get("user_budget")
        if user_budget != "No":
            # Store the selected budget in the session
            request.session["default_budget_id"] = user_budget
        else:
            # Delete the session
            request.session.pop("default_budget_id", None)
        return redirect("budgets")


@login_required(login_url="/login")
def budget_details(request, pk):
    """
    Renders the details of a specific budget, including transactions associated
    with the budget. Allows filtering of transactions by a date range.

    Args:
        request: The HTTP request object.
        pk: The primary key of the Budget object.

    Returns:
        HttpResponse: The rendered budget detail page with relevant context.
    """
    user_name = request.user

    # Fetch the budget object using the primary key (pk)
    budget_obj = Budget.objects.get(pk=pk)

    # Handle POST request to filter transactions by date range
    if request.method == "POST":
        start_date = request.POST["start_date"]
        end_date = request.POST["end_date"]
        transaction_data = Transaction.objects.filter(
            user=user_name,
            budgets=budget_obj,
        transaction_data = Transaction.objects.filter(
            user=user_name,
            budgets=budget_obj,
            categories=budget_obj.category,
            transaction_date__range=(start_date, end_date),
        ).order_by("transaction_date")
    else:
        # Default to fetching all transactions associated with the budget
        start_date = False
        end_date = False
        transaction_data = Transaction.objects.filter(
            user=user_name, budgets=budget_obj, categories=budget_obj.category
        ).order_by("transaction_date")
    context = {
        "budget_obj": budget_obj,
        "budget_transaction_data": transaction_data,
        "transaction_key": TRANSACTION_KEYS,
        "transaction_key_dumbs": json.dumps(TRANSACTION_KEYS),
        "start_date": start_date,
        "end_date": end_date,
        "page": "budgets",
    }
    return render(request, "budget/budget_detail.html", context=context)


def make_month_obj(
    obj,
    user_name,
    quarter_list,
    quarter_value,
    upcoming_quarter_date,
    budget_name,
    budget_period,
    budget_currency,
    budget_amount,
    budget_auto,
):
    quarter_index = 0
    for month_date in quarter_list:
        if quarter_index == 0:
            obj.start_date = month_date
            obj.end_date = month_date.replace(
                day=calendar.monthrange(month_date.year, month_date.month)[1]
            )
            obj.initial_amount = budget_amount
            obj.created_at = quarter_value
            obj.ended_at = upcoming_quarter_date
            obj.save()
        else:
            start_date = month_date
            end_date = month_date.replace(
                day=calendar.monthrange(month_date.year, month_date.month)[1]
            )
            save_budgets(
                user_name,
                start_date,
                end_date,
                budget_name,
                budget_period,
                budget_currency,
                budget_amount,
                budget_auto,
                quarter_value,
                upcoming_quarter_date,
                budget_amount,
            )

        quarter_index += 1


class UserBudgetAdd(LoginRequiredMixin, CreateView):
    model = UserBudgets
    form_class = UserBudgetsForm

    def get_success_url(self):
        """
        Redirect the user to the Budget box page.
        """

        return reverse_lazy("budgets")

    def form_valid(self, form):
        """
        Validate the form and handle the creation of a new UserBudgets object.

        Args:
            form: The form instance with validated data.

        Returns:
            HttpResponseRedirect: Redirects to the success URL if form is valid.
        """
        user_name = self.request.user
        user_budget_name = form.cleaned_data.get("name").title()

        # Check if a budget with the same name already exists for the user
        budget_check = UserBudgets.objects.filter(
            user=user_name, name=user_budget_name)
        if budget_check:
            form.add_error("name", "User Budget already exist")
            return self.form_invalid(form)

        obj = form.save(commit=False)
        obj.user = user_name
        obj.name = user_budget_name
        obj.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle invalid form submissions.
        Redirect the user to the form page with error messages.
        """
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, error)
        return redirect(self.get_success_url())


def user_budget_update(request, pk):
    """
    Update the 'name' field of a UserBudget instance identified by pk.

    Args:
        request (HttpRequest): The request object with POST data.
        pk (int): Primary key of the UserBudget instance.

    Returns:
        JsonResponse: JSON response with the result of the update.
    """
    if request.method == "POST":
        # Get the new name from POST data
        name = request.POST.get("user_budget_name")

        # Get the UserBudget instance
        user_budget = UserBudgets.objects.get(pk=pk)

        # Check if the name is different from the current name
        if name != user_budget.name:

            # Check if the name is already used or not
            if UserBudgets.objects.filter(user=request.user, name=name).exists():
                return JsonResponse(
                    {"status": "false", "message": "Name already exist"}
                )
                return JsonResponse(
                    {"status": "false", "message": "Name already exist"}
                )

            user_budget.name = name
            user_budget.save()
            return JsonResponse({"status": "true", "message": "Updated successfully"})

        return JsonResponse({"status": "false", "message": "No changes detected"})


class BudgetAdd(LoginRequiredMixin, CreateView):
    model = Budget
    form_class = BudgetForm
    template_name = "budget/budget_add.html"

    def get_form_kwargs(self):
        """Passes the request object to the form class.
        This is necessary to only display members that belong to a given user"""

        kwargs = super(BudgetAdd, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        user_name = self.request.user
        data = super(BudgetAdd, self).get_context_data(**kwargs)
        category_groups = Category.objects.filter(user=user_name)
        categories_list = list(category_groups.values_list("name", flat=True))
        category_suggestions = SuggestiveCategory.objects.all().values_list(
            "name", flat=True
        )
        suggestion_list = []
        for name in category_suggestions:
            if name not in categories_list:
                suggestion_list.append(name)
        data["category_suggestions"] = suggestion_list
        data["category_groups"] = category_groups
        return data

    def form_valid(self, form):
        obj = form.save(commit=False)
        user_name = self.request.user
        obj.user = user_name
        category_name = form.cleaned_data.get("categories")
        name = self.request.POST["subcategory"].title()
        user_budget_id = self.request.POST.get("user_budget")
        user_budget = UserBudgets.objects.get(
            user=user_name, name=user_budget_id)
        category_obj = Category.objects.get(user=user_name, name=category_name)
        subcategory_obj = SubCategory.objects.get(
            name=name, category=category_obj)
        obj.category = subcategory_obj
        budget_period = form.cleaned_data["budget_period"]
        budget_name = name
        obj.name = budget_name
        budget_check = Budget.objects.filter(
            user=user_name, user_budget=user_budget, name=budget_name
        )
        if budget_check:
            form.add_error("name", "Budget already exist")
            return self.form_invalid(form)
        budget_amount = form.cleaned_data["amount"]
        budget_currency = form.cleaned_data["currency"]
        budget_auto = form.cleaned_data["auto_budget"]
        budget_start_date = self.request.POST["budget_date"]
        budget_start_date = datetime.datetime.strptime(
            budget_start_date, DateFormats.YYYY_MM_DD.value
        )
        budget_start_date = datetime.datetime.strptime(
            budget_start_date, DateFormats.YYYY_MM_DD.value
        )
        start_month_date, end_month_date = start_end_date(
            budget_start_date.date(), BudgetPeriods.MONTHLY.value
        )
        budget_end_date = get_period_date(
            budget_start_date, budget_period
        ) - relativedelta(days=1)
        obj.start_date = start_month_date
        obj.end_date = end_month_date
        obj.initial_amount = budget_amount
        obj.budget_left = budget_amount
        obj.created_at = budget_start_date
        obj.ended_at = budget_end_date
        obj.budget_start_date = budget_start_date
        obj.user_budget = user_budget
        obj.save()
        if budget_period == BudgetPeriods.QUARTERLY.value:
            for _ in range(2):
                start_month_date = start_month_date + relativedelta(months=1)
                start_month_date, end_month_date = start_end_date(
                    start_month_date, BudgetPeriods.MONTHLY.value
                )
                save_budgets(
                    user_name,
                    start_month_date,
                    end_month_date,
                    budget_name,
                    budget_period,
                    budget_currency,
                    budget_amount,
                    budget_auto,
                    budget_start_date,
                    budget_end_date,
                    budget_amount,
                    budget_start_date,
                    subcategory_obj,
                    None,
                    budget_status=True,
                )
        if budget_period == BudgetPeriods.YEARLY.value:
            for _ in range(11):
                start_month_date = start_month_date + relativedelta(months=1)
                start_month_date, end_month_date = start_end_date(
                    start_month_date, BudgetPeriods.MONTHLY.value
                )
                save_budgets(
                    user_name,
                    start_month_date,
                    end_month_date,
                    budget_name,
                    budget_period,
                    budget_currency,
                    budget_amount,
                    budget_auto,
                    budget_start_date,
                    budget_end_date,
                    budget_amount,
                    budget_start_date,
                    subcategory_obj,
                    None,
                    budget_status=True,
                )
        create_budget_request()
        return super().form_valid(form)


def budget_update(request, pk):
    error = False
    budget_obj = Budget.objects.get(user=request.user, pk=pk)
    user_name = request.user
    if request.method == "POST":
        category_id = int(request.POST["categories"])
        subcategory = request.POST["subcategory"]
        currency = request.POST["currency"]
        amount = float(request.POST["amount"])
        auto_budget = request.POST.get("auto_budget", False)
        old_budget_period = budget_obj.budget_period
        old_budget_create_date = budget_obj.created_at
        try:
            budget_period = request.POST["budget_period"]
            budget_date = request.POST["budget_date"]
            budget_date = datetime.datetime.strptime(
                budget_date, DateFormats.YYYY_MM_DD.value
            ).date()
            budget_date = datetime.datetime.strptime(
                budget_date, DateFormats.YYYY_MM_DD.value
            ).date()
        # To-Do  Remove bare except
        except:
            budget_period = old_budget_period
            budget_date = old_budget_create_date

        budget_already_exist = False
        if subcategory != budget_obj.name:
            budget_check = Budget.objects.filter(
                user=user_name, name=subcategory)
            if budget_check:
                budget_already_exist = True
        if budget_already_exist:
            error = "Budget name already exist"
        else:
            category_obj = Category.objects.get(id=category_id)
            subcategory_obj = SubCategory.objects.get(
                name=subcategory, category=category_obj
            )
            if auto_budget:
                auto_budget = True
            old_budget_end_date = budget_obj.ended_at
            start_month_date, end_month_date = start_end_date(
                budget_date, BudgetPeriods.MONTHLY.value
            )
            budget_end_date = get_period_date(
                budget_date, budget_period
            ) - relativedelta(days=1)
            if budget_period == old_budget_period:
                if old_budget_create_date == budget_date:
                    try:
                        budget_end_date = get_period_date(
                            budget_date, budget_period
                        ) - relativedelta(days=1)
                        current_budget_date = request.POST["current_budget_date"]
                        current_budget_amount = float(
                            request.POST["current_amount"])
                        budget_left = round(
                            current_budget_amount -
                            float(budget_obj.budget_spent), 2
                        )
                        Budget.objects.filter(
                            user=user_name,
                            name=budget_obj.name,
                            created_at=budget_obj.created_at,
                            ended_at=budget_obj.ended_at,
                        ).update(
                            name=subcategory,
                            category=subcategory_obj,
                            auto_budget=auto_budget,
                            currency=currency,
                            amount=current_budget_amount,
                            initial_amount=amount,
                            budget_left=budget_left,
                            created_at=current_budget_date,
                            ended_at=budget_end_date,
                        )

                    except Exception as e:
                        print("Exception_==========>", e)
                        budget_qs = Budget.objects.filter(
                            user=user_name, name=subcategory
                        ).delete()
                        if budget_period == BudgetPeriods.QUARTERLY.value:
                            for month_value in range(3):
                                if month_value == 2:
                                    budget_status = False
                                else:
                                    budget_status = True
                                save_budgets(
                                    user_name,
                                    start_month_date,
                                    end_month_date,
                                    subcategory,
                                    budget_period,
                                    currency,
                                    amount,
                                    auto_budget,
                                    budget_date,
                                    budget_end_date,
                                    amount,
                                    budget_date,
                                    subcategory_obj,
                                    None,
                                    budget_status,
                                )
                                start_month_date = start_month_date + relativedelta(
                                    months=1
                                )
                                start_month_date, end_month_date = start_end_date(
                                    start_month_date, BudgetPeriods.MONTHLY.value
                                )

                        if budget_period == BudgetPeriods.YEARLY.value:
                            for month_value in range(12):
                                if month_value == 11:
                                    budget_status = False
                                else:
                                    budget_status = True
                                save_budgets(
                                    user_name,
                                    start_month_date,
                                    end_month_date,
                                    subcategory,
                                    budget_period,
                                    currency,
                                    amount,
                                    auto_budget,
                                    budget_date,
                                    budget_end_date,
                                    amount,
                                    budget_date,
                                    subcategory_obj,
                                    None,
                                    budget_status,
                                )
                                start_month_date = start_month_date + relativedelta(
                                    months=1
                                )
                                start_month_date, end_month_date = start_end_date(
                                    start_month_date, BudgetPeriods.MONTHLY.value
                                )

                        if budget_period in (
                            BudgetPeriods.DAILY.value,
                            BudgetPeriods.WEEKLY.value,
                            BudgetPeriods.MONTHLY.value,
                        ):
                            save_budgets(
                                user_name,
                                start_month_date,
                                end_month_date,
                                subcategory,
                                budget_period,
                                currency,
                                amount,
                                auto_budget,
                                budget_date,
                                budget_end_date,
                                amount,
                                budget_date,
                                subcategory_obj,
                            )
                else:
                    transaction_qs = Transaction.objects.filter(
                        user=user_name, categories=budget_obj.category
                    )
                    if not transaction_qs:
                        budget_qs = Budget.objects.filter(
                            user=user_name, name=subcategory
                        ).delete()
                        if budget_period == BudgetPeriods.QUARTERLY.value:
                            for month_value in range(3):
                                if month_value == 2:
                                    budget_status = False
                                else:
                                    budget_status = True
                                save_budgets(
                                    user_name,
                                    start_month_date,
                                    end_month_date,
                                    subcategory,
                                    budget_period,
                                    currency,
                                    amount,
                                    auto_budget,
                                    budget_date,
                                    budget_end_date,
                                    amount,
                                    budget_date,
                                    subcategory_obj,
                                    None,
                                    budget_status,
                                )
                                start_month_date = start_month_date + relativedelta(
                                    months=1
                                )
                                start_month_date, end_month_date = start_end_date(
                                    start_month_date, BudgetPeriods.MONTHLY.value
                                )

                        if budget_period == BudgetPeriods.YEARLY.value:
                            for month_value in range(12):
                                if month_value == 11:
                                    budget_status = False
                                else:
                                    budget_status = True
                                save_budgets(
                                    user_name,
                                    start_month_date,
                                    end_month_date,
                                    subcategory,
                                    budget_period,
                                    currency,
                                    amount,
                                    auto_budget,
                                    budget_date,
                                    budget_end_date,
                                    amount,
                                    budget_date,
                                    subcategory_obj,
                                    None,
                                    budget_status,
                                )
                                start_month_date = start_month_date + relativedelta(
                                    months=1
                                )
                                start_month_date, end_month_date = start_end_date(
                                    start_month_date, BudgetPeriods.MONTHLY.value
                                )

                        if budget_period in (
                            BudgetPeriods.DAILY.value,
                            BudgetPeriods.WEEKLY.value,
                            BudgetPeriods.MONTHLY.value,
                        ):
                            save_budgets(
                                user_name,
                                start_month_date,
                                end_month_date,
                                subcategory,
                                budget_period,
                                currency,
                                amount,
                                auto_budget,
                                budget_date,
                                budget_end_date,
                                amount,
                                budget_date,
                                subcategory_obj,
                            )

            else:
                # new_budget_qs = Budget.objects.filter(user=user_name, name=subcategory, created_at=budget_date,
                #                                       ended_at=budget_end_date)
                # if new_budget_qs:
                #     error = 'Budget already exists for this period!'
                # else:
                budget_qs = Budget.objects.filter(
                    user=user_name, name=subcategory
                ).delete()
                if budget_period == BudgetPeriods.QUARTERLY.value:
                    for month_value in range(3):
                        if month_value == 2:
                            budget_status = False
                        else:
                            budget_status = True
                        save_budgets(
                            user_name,
                            start_month_date,
                            end_month_date,
                            subcategory,
                            budget_period,
                            currency,
                            amount,
                            auto_budget,
                            budget_date,
                            budget_end_date,
                            amount,
                            budget_date,
                            subcategory_obj,
                            None,
                            budget_status,
                        )
                        start_month_date = start_month_date + \
                            relativedelta(months=1)
                        start_month_date, end_month_date = start_end_date(
                            start_month_date, BudgetPeriods.MONTHLY.value
                        )

                if budget_period == BudgetPeriods.YEARLY.value:
                    for month_value in range(12):
                        if month_value == 11:
                            budget_status = False
                        else:
                            budget_status = True
                        save_budgets(
                            user_name,
                            start_month_date,
                            end_month_date,
                            subcategory,
                            budget_period,
                            currency,
                            amount,
                            auto_budget,
                            budget_date,
                            budget_end_date,
                            amount,
                            budget_date,
                            subcategory_obj,
                            None,
                            budget_status,
                        )
                        start_month_date = start_month_date + \
                            relativedelta(months=1)
                        start_month_date, end_month_date = start_end_date(
                            start_month_date, BudgetPeriods.MONTHLY.value
                        )

                if budget_period in (
                    BudgetPeriods.DAILY.value,
                    BudgetPeriods.WEEKLY.value,
                    BudgetPeriods.MONTHLY.value,
                ):
                    save_budgets(
                        user_name,
                        start_month_date,
                        end_month_date,
                        subcategory,
                        budget_period,
                        currency,
                        amount,
                        auto_budget,
                        budget_date,
                        budget_end_date,
                        amount,
                        budget_date,
                        subcategory_obj,
                    )

        if not error:
            return redirect("/budgets/current")

    categories = Category.objects.filter(user=request.user)
    sub_categories = SubCategory.objects.filter(
        category__pk=budget_obj.category.category.id
    )
    budget_periods = BudgetPeriods.list()
    transaction_qs = Transaction.objects.filter(
        user=user_name, categories=budget_obj.category
    )
    if transaction_qs:
        budget_update_period = True
    else:
        budget_update_period = False

    context = {
        "budget_data": budget_obj,
        "categories": categories,
        "sub_categories": sub_categories,
        "currency_dict": CURRENCY_DICT,
        "budget_period": budget_periods,
        "current_budget_date": str(budget_obj.created_at),
        "budget_date": str(budget_obj.budget_start_date),
        "errors": error,
        "budget_update_period": budget_update_period,
        "page": "budgets",
    }
    return render(request, "budget/budget_update.html", context=context)


class BudgetDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        budget_obj = Budget.objects.get(pk=self.kwargs["pk"])
        budget_name = budget_obj.name
        user_name = self.request.user
        transaction_details = Transaction.objects.filter(
            user=user_name, budgets__name=budget_name
        )
        for data in transaction_details:
            delete_transaction_details(data.pk, user_name)

        Budget.objects.filter(user=user_name, name=budget_name).delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


@login_required(login_url="/login")
def template_budget_list(request):
    context = budgets_page_data(request, "", "active")
    context.update({"page": "budgets"})
    return render(request, "budget/budget_list.html", context=context)


class TemplateAdd(LoginRequiredMixin, CreateView):
    model = TemplateBudget
    form_class = TemplateBudgetForm
    template_name = "budget/budget_add.html"

    def form_valid(self, form):
        obj = form.save(commit=False)
        user_name = self.request.user
        obj.user = user_name
        budget_period = form.cleaned_data["budget_period"]
        date_value = datetime.datetime.today().date()
        budget_amount = form.cleaned_data["amount"]
        start_month_date, end_month_date = start_end_date(
            date_value, BudgetPeriods.MONTHLY.value
        )

        obj.start_date = start_month_date
        obj.end_date = end_month_date
        obj.initial_amount = budget_amount
        obj.budget_left = budget_amount

        if budget_period == BudgetPeriods.WEEKLY.value:
            start_week_date, end_week_date = start_end_date(
                date_value, budget_period)
            obj.created_at = start_week_date
            obj.ended_at = end_week_date
            obj.save()

        if budget_period == BudgetPeriods.DAILY.value:
            obj.created_at = date_value
            obj.ended_at = date_value
            obj.save()

        if budget_period == BudgetPeriods.YEARLY.value:
            start_year_date, end_year_date = start_end_date(
                date_value, budget_period)
            obj.created_at = start_year_date
            obj.ended_at = end_year_date
            obj.save()

        if budget_period == BudgetPeriods.QUARTERLY.value:
            upcoming_quarter_date, quarter_value = start_end_date(
                date_value, budget_period
            )
            obj.created_at = quarter_value
            obj.ended_at = upcoming_quarter_date
            obj.save()

        return super().form_valid(form)


class TemplateUpdate(LoginRequiredMixin, UpdateView):
    model = TemplateBudget
    form_class = TemplateBudgetForm
    template_name = "budget/budget_update.html"

    def form_valid(self, form):
        user_name = self.request.user
        budget_obj = TemplateBudget.objects.get(
            user=user_name, pk=self.kwargs["pk"])
        old_amount = float(budget_obj.amount)
        update_amount = float(form.cleaned_data["amount"])
        update_period = form.cleaned_data["budget_period"]
        auto_budget = form.cleaned_data["auto_budget"]
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
        budget_obj = TemplateBudget.objects.get(pk=self.kwargs["pk"])
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
    name = request.POST["name"].title()
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
    method_name = request.POST["method_name"]
    transaction_id = request.POST["transaction_id"]
    category_list = ast.literal_eval(request.POST["category_list"])
    amount_list = ast.literal_eval(request.POST["amount_list"])
    original_amount = request.POST["original_amount"]
    transaction_obj = Transaction.objects.get(
        user=user_name, pk=transaction_id)
    transaction_account = transaction_obj.account.name
    try:
        transaction_tags = transaction_obj.tags
    # To-Do  Remove bare except
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
        return JsonResponse(
            {
                "status": "error",
                "message": "Please add more than one category with amount",
            }
        )
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
                    split_amount_dict[trans_obj.id] = [
                        old_category_name, new_amount]
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
                    subcategory_obj = SubCategory.objects.get(
                        name=category_list[i], category__user=user_name
                    )
                    transaction_amount = float(amount_list[i])
                    bill_name = ""
                    budget_name = ""
                    out_flow = "False"
                    if (
                        subcategory_obj.category.name
                        == CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value
                    ):
                        bill_name = subcategory_obj.name
                    budget_qs = Budget.objects.filter(
                        user=user_name, category=subcategory_obj
                    )
                    if budget_qs:
                        budget_name = subcategory_obj.name
                    if transaction_out_flow:
                        out_flow = "True"

                    account_obj, budget_obj = transaction_checks(
                        user_name,
                        transaction_amount,
                        transaction_account,
                        bill_name,
                        budget_name,
                        cleared_amount,
                        out_flow,
                        str(transaction_date),
                    )
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
                        split_obj.bill = Bill.objects.get(
                            user=user_name, name=bill_name
                        )
                    split_obj.cleared = True
                    split_obj.save()
                    split_trans_obj_list.append(split_obj)
                    split_amount_dict[split_obj.id] = [
                        category_list[i],
                        split_obj.amount,
                    ]
        else:
            transaction_obj.original_amount = original_amount
            transaction_obj.amount = amount_list[0]
            split_trans_obj_list.append(transaction_obj)
            split_amount_dict[transaction_obj.id] = [
                category_list[0],
                round(float(amount_list[0]), 2),
            ]
            print(split_amount_dict)
            for i in range(1, len(category_list)):
                split_obj = Transaction()
                subcategory_obj = SubCategory.objects.get(
                    name=category_list[i], category__user=user_name
                )
                transaction_amount = float(amount_list[i])
                bill_name = ""
                budget_name = ""
                out_flow = "False"
                if (
                    subcategory_obj.category.name
                    == CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value
                ):
                    bill_name = subcategory_obj.name
                budget_qs = Budget.objects.filter(
                    user=user_name, category=subcategory_obj
                )
                if budget_qs:
                    budget_name = subcategory_obj.name
                if transaction_out_flow:
                    out_flow = "True"

                account_obj, budget_obj = transaction_checks(
                    user_name,
                    transaction_amount,
                    transaction_account,
                    bill_name,
                    budget_name,
                    cleared_amount,
                    out_flow,
                    str(transaction_date),
                )
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
                    split_obj.bill = Bill.objects.get(
                        user=user_name, name=bill_name)
                split_obj.cleared = True
                split_obj.save()
                split_trans_obj_list.append(split_obj)
                split_amount_dict[split_obj.id] = [
                    category_list[i], split_obj.amount]

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
        tag_name = request.POST["tag_name"]
        if tag_name != "All":
            transaction_data = Transaction.objects.filter(
                user=user_name, tags__name=tag_name
            ).order_by("-transaction_date")
        else:
            transaction_data = Transaction.objects.filter(user=user_name).order_by(
                "-transaction_date"
            )
        select_filter = tag_name
    else:
        transaction_data = Transaction.objects.filter(user=user_name).order_by(
            "-transaction_date"
        )
        select_filter = "All"

    context = transaction_summary(transaction_data, select_filter, user_name)
    context.update({"page": "transaction_list",
                   "tour_api": Tour_APIs["transactions"]})
    return render(request, "transaction/transaction_list.html", context=context)


@login_required(login_url="/login")
def transaction_report(request):
    user_name = request.user
    if request.method == "POST":
        tag_name = request.POST["tag_name"]
        tags_data = request.POST["tags_data"]
        start_date = request.POST["start_date"]
        end_date = request.POST["end_date"]
        tags_data = ast.literal_eval(tags_data)
        start_date = datetime.datetime.strptime(
            start_date, DateFormats.YYYY_MM_DD.value
        ).date()
        end_date = datetime.datetime.strptime(
            end_date, DateFormats.YYYY_MM_DD.value
        ).date()
        start_date = datetime.datetime.strptime(
            start_date, DateFormats.YYYY_MM_DD.value
        ).date()
        end_date = datetime.datetime.strptime(
            end_date, DateFormats.YYYY_MM_DD.value
        ).date()
        if tag_name != "All":
            transaction_data = Transaction.objects.filter(
                user=user_name,
                transaction_date__range=(start_date, end_date),
                tags__name=tag_name,
            ).order_by("transaction_date")
        else:
            transaction_data = Transaction.objects.filter(
                user=user_name, transaction_date__range=(start_date, end_date)
            ).order_by("transaction_date")
        select_filter = tag_name
    else:
        start_date = request.GET["start_date"]
        end_date = request.GET["end_date"]
        if start_date != "" and end_date != "":
            start_date = datetime.datetime.strptime(
                start_date, DateFormats.YYYY_MM_DD.value
            ).date()
            end_date = datetime.datetime.strptime(
                end_date, DateFormats.YYYY_MM_DD.value
            ).date()
            start_date = datetime.datetime.strptime(
                start_date, DateFormats.YYYY_MM_DD.value
            ).date()
            end_date = datetime.datetime.strptime(
                end_date, DateFormats.YYYY_MM_DD.value
            ).date()
            transaction_data = Transaction.objects.filter(
                user=user_name, transaction_date__range=(start_date, end_date)
            ).order_by("transaction_date")
            select_filter = "All"
        else:
            return redirect("/transaction_list/")

    context = transaction_summary(transaction_data, select_filter, user_name)
    context["start_date"] = str(start_date)
    context["end_date"] = str(end_date)
    return render(request, "transaction/transaction_list.html", context=context)


class TransactionDetail(LoginRequiredMixin, DetailView):
    model = Transaction
    template_name = "transaction/transaction_detail.html"


class TransactionAdd(LoginRequiredMixin, CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = "transaction/transaction_add.html"

    def get_form_kwargs(self):
        """Passes the request object to the form class.
        This is necessary to only display members that belong to a given user"""

        kwargs = super(TransactionAdd, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        user_name = self.request.user
        tags = Tag.objects.filter(user=user_name)
        data = super(TransactionAdd, self).get_context_data(**kwargs)
        data["tags"] = tags
        return data

    def get_success_url(self):
        if "add_other" in self.request.POST:
            url = reverse_lazy("transaction_add")
        elif "category_page" in self.request.POST:
            url = reverse_lazy("category_list")
        else:
            url = reverse_lazy("transaction_list")
        return url

    def form_valid(self, form):
        obj = form.save(commit=False)
        category_name = form.cleaned_data.get("category")
        user_budget = self.request.POST.get("user_budget")
        name = self.request.POST["subcategory"].title()
        user_name = self.request.user
        category_obj = Category.objects.get(user=user_name, name=category_name)
        subcategory_obj = SubCategory.objects.get(
            name=name, category=category_obj)
        obj.user = user_name
        obj.categories = subcategory_obj
        account = form.cleaned_data.get("account")
        transaction_amount = round(float(form.cleaned_data.get("amount")), 2)
        tags = form.cleaned_data.get("tag_name")
        notes = form.cleaned_data.get("notes")
        print("tags=====>", tags)
        print("notes=====>", notes)
        if tags:
            obj.tags = Tag.objects.get(name=tags, user=user_name)
        if notes:
            obj.notes = notes
        out_flow = form.cleaned_data.get("out_flow")
        cleared_amount = "True"
        bill_name = form.cleaned_data.get("bill")
        # if category_name.name == 'Income':
        #     due_income_id = int(self.request.POST['due_income'])
        #     income_obj = IncomeDetail.objects.get(pk=due_income_id)
        #     income_obj.credited = True
        #     income_obj.save()

        if category_name.name in (CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value, "Bills"):
            due_bill_id = int(self.request.POST["due_bill"])
            bill_name = Bill.objects.get(
                pk=due_bill_id, user_budget=user_budget)
            obj.bill = bill_name
        budget_name = self.request.POST["budget_name"]
        transaction_date = form.cleaned_data.get("transaction_date")
        account = account.name
        account_obj, budget_obj = transaction_checks(
            user_name,
            transaction_amount,
            account,
            bill_name,
            budget_name,
            cleared_amount,
            out_flow,
            transaction_date,
            user_budget,
        )
        # For Goals , Add transaction and add the amount to goal allocated amount
        if category_name.name == CategoryTypes.GOALS.value:
            goal_obj = Goal.objects.get(
                user=user_name, label=budget_obj.category)
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
    template_name = "transaction/transaction_update.html"

    def get_form_kwargs(self):
        """Passes the request object to the form class.
        This is necessary to only display members that belong to a given user"""

        kwargs = super(TransactionUpdate, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        user_name = self.request.user
        transaction_obj = Transaction.objects.get(pk=self.kwargs["pk"])
        data = super(TransactionUpdate, self).get_context_data(**kwargs)
        categories_data = Category.objects.filter(user=user_name)
        subcategories_data = SubCategory.objects.filter(
            category__user=user_name)
        select_subcategory = transaction_obj.categories
        subcategory_data = SubCategory.objects.filter(
            category=select_subcategory.category
        )
        select_category_id = select_subcategory.category.id
        select_subcategory_id = select_subcategory.id
        select_subcategory_name = select_subcategory.name
        original_amount = transaction_obj.original_amount
        try:
            select_budget_name = transaction_obj.budgets
        # To-Do  Remove bare except
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
            data["split_category"] = split_category
            data["split_cat"] = json.dumps(split_cat)
            data["amount_list"] = json.dumps(amount_list)
        data["tags"] = Tag.objects.filter(user=user_name)
        data["select_budget_name"] = select_budget_name
        data["select_category_id"] = select_category_id
        data["select_subcategory_id"] = select_subcategory_id
        data["categories"] = categories_data
        data["subcategories"] = subcategory_data
        data["tag_name"] = tag_name
        data["original_amount"] = original_amount
        data["select_subcategory_name"] = select_subcategory_name
        data["subcategories_data"] = subcategories_data
        data["transaction_id"] = self.kwargs["pk"]
        return data

    def form_valid(self, form):
        user_name = self.request.user
        transaction_obj = Transaction.objects.get(pk=self.kwargs["pk"])
        obj = form.save(commit=False)
        account = transaction_obj.account.name.title()
        user_name = self.request.user
        category_name = form.cleaned_data.get("category")
        name = self.request.POST["subcategory"].title()
        category_obj = Category.objects.get(name=category_name, user=user_name)
        subcategory_obj = SubCategory.objects.get(
            name=name, category=category_obj)
        obj.user = user_name
        obj.categories = subcategory_obj
        transaction_amount = round(float(transaction_obj.amount), 2)
        transaction_out_flow = transaction_obj.out_flow
        update_account = form.cleaned_data.get("account").name.title()
        update_transaction_amount = round(
            float(form.cleaned_data.get("amount")), 2)
        out_flow = form.cleaned_data.get("out_flow")
        if out_flow == "True":
            out_flow = True
        else:
            out_flow = False

        cleared_amount = "True"
        # if category_name.name == CategoryTypes.INCOME.value:
        #     due_income_id = int(self.request.POST['due_income'])
        #     income_obj = IncomeDetail.objects.get(pk=due_income_id)
        #     income_obj.credited = True
        #     income_obj.save()
        #
        # if transaction_obj.categories.category.name == CategoryTypes.INCOME.value != category_name.name:
        #     income_obj = IncomeDetail.objects.get(income__user=user_name, income__account=transaction_obj.account,
        #                                           income__sub_category__id=transaction_obj.categories.id,
        #                                           income_date=transaction_obj.transaction_date)
        #     income_obj.credited = False
        #     income_obj.save()

        if (
            transaction_obj.categories.category.name
            == CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value
            == category_name.name
        ):
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

        if (
            transaction_obj.categories.category.name
            == CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value
            != category_name.name
        ):
            bill_obj = transaction_obj.bill
            bill_amount = float(bill_obj.remaining_amount)
            bill_obj.status = "unpaid"
            bill_obj.remaining_amount = bill_amount + transaction_amount
            bill_obj.save()
            obj.bill = None
        if (
            transaction_obj.categories.category.name
            != CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value
            == category_name.name
        ):
            due_bill_id = int(self.request.POST["due_bill"])
            bill_obj = Bill.objects.get(pk=due_bill_id)
            bill_amount = float(bill_obj.remaining_amount) - \
                update_transaction_amount
            if bill_amount == 0.0:
                bill_obj.status = "paid"
                bill_obj.remaining_amount == 0.0
            else:
                bill_obj.status = "unpaid"
                bill_obj.remaining_amount = bill_amount
            bill_obj.save()
            obj.bill = bill_obj

        budget_name = self.request.POST["budget_name"]
        transaction_date = form.cleaned_data.get("transaction_date")

        if cleared_amount == "True":
            old_account_obj = Account.objects.get(user=user_name, name=account)
            if account == update_account:
                account_obj = Account.objects.get(user=user_name, name=account)
                if transaction_amount != update_transaction_amount:
                    if category_name.name == CategoryTypes.FUNDS.value:
                        new_fund_obj = AvailableFunds.objects.get(
                            user=user_name, account=account_obj
                        )
                        if transaction_out_flow:
                            fund_total = round(
                                float(new_fund_obj.total_fund) -
                                transaction_amount, 2
                            )
                            fund_total = fund_total + update_transaction_amount
                            new_fund_obj.total_fund = fund_total
                            new_fund_obj.save()
                        else:
                            fund_total = round(
                                float(new_fund_obj.total_fund) +
                                transaction_amount, 2
                            )
                            fund_total = fund_total - update_transaction_amount

                        new_fund_obj.total_fund = fund_total
                        new_fund_obj.save()
                    else:
                        if (
                            transaction_obj.categories.category.name
                            == CategoryTypes.FUNDS.value
                        ):
                            old_fund_obj = AvailableFunds.objects.get(
                                user=user_name, account=account_obj
                            )
                            if transaction_out_flow:
                                fund_total = round(
                                    float(old_fund_obj.total_fund) -
                                    transaction_amount,
                                    2,
                                )
                                old_fund_obj.total_fund = fund_total
                                total_fund = old_fund_obj.total_fund
                                total_lock_fund = 0.0
                                goal_qs = Goal.objects.filter(
                                    user=user_name, account=old_account_obj
                                )
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
                                fund_total = round(
                                    float(old_fund_obj.total_fund) +
                                    transaction_amount,
                                    2,
                                )
                                old_fund_obj.total_fund = fund_total
                                old_fund_obj.save()

                    if transaction_out_flow:
                        account_obj.available_balance = round(
                            float(account_obj.available_balance) +
                            transaction_amount, 2
                        )
                    else:
                        account_obj.available_balance = round(
                            float(account_obj.available_balance) -
                            transaction_amount, 2
                        )

                    if out_flow:
                        account_obj.available_balance = round(
                            float(account_obj.available_balance)
                            - update_transaction_amount,
                            2,
                        )
                    else:
                        account_obj.available_balance = round(
                            float(account_obj.available_balance)
                            + update_transaction_amount,
                            2,
                        )

            else:
                account_obj = Account.objects.get(
                    user=user_name, name=update_account)
                if CategoryTypes.FUNDS.value in (
                    category_name.name,
                    transaction_obj.categories.category.name,
                ):
                    old_fund_obj = AvailableFunds.objects.get(
                        user=user_name, account=old_account_obj
                    )
                    new_fund_obj = AvailableFunds.objects.get(
                        user=user_name, account=account_obj
                    )
                    if (
                        transaction_obj.categories.category.name
                        == CategoryTypes.FUNDS.value
                    ):
                        if transaction_out_flow:
                            old_fund_obj.total_fund = (
                                float(old_fund_obj.total_fund) -
                                transaction_amount
                            )
                            total_fund = old_fund_obj.total_fund
                            total_lock_fund = 0.0
                            goal_qs = Goal.objects.filter(
                                user=user_name, account=old_account_obj
                            )
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
                            old_fund_obj.total_fund = (
                                float(old_fund_obj.total_fund) +
                                transaction_amount
                            )
                            old_fund_obj.save()

                    if category_name.name == CategoryTypes.FUNDS.value:
                        if transaction_out_flow:
                            new_fund_obj.total_fund = (
                                float(new_fund_obj.total_fund) +
                                transaction_amount
                            )
                            new_fund_obj.save()
                        else:
                            new_fund_obj.total_fund = (
                                float(new_fund_obj.total_fund) -
                                transaction_amount
                            )
                            new_fund_obj.save()

                if transaction_out_flow:
                    old_account_obj.available_balance = round(
                        float(old_account_obj.available_balance) +
                        transaction_amount, 2
                    )
                else:
                    old_account_obj.available_balance = round(
                        float(old_account_obj.available_balance) -
                        transaction_amount, 2
                    )

                if out_flow:
                    account_obj.available_balance = round(
                        float(account_obj.available_balance)
                        - update_transaction_amount,
                        2,
                    )
                else:
                    account_obj.available_balance = round(
                        float(account_obj.available_balance)
                        + update_transaction_amount,
                        2,
                    )

                account_obj.transaction_count += 1
                old_account_obj.transaction_count -= 1

                old_account_obj.save()

            obj.remaining_amount = account_obj.available_balance
            account_obj.save()

            if budget_name:
                print("yes budget name")
                date_check = datetime.datetime.strptime(
                    transaction_date, DateFormats.YYYY_MM_DD.value
                ).date()
                start_month_date, end_month_date = start_end_date(
                    date_check, BudgetPeriods.MONTHLY.value
                )
                budget_obj = Budget.objects.filter(
                    user=user_name,
                    name=budget_name,
                    start_date=start_month_date,
                    end_date=end_month_date,
                )[0]
            else:
                date_check = datetime.datetime.strptime(
                    transaction_date, DateFormats.YYYY_MM_DD.value
                ).date()
                try:
                    transaction_budget_name = transaction_obj.budgets.name
                    transaction_start_date, transaction_end_date = start_end_date(
                        transaction_obj.transaction_date, BudgetPeriods.MONTHLY.value
                    )

                    budget_obj = Budget.objects.filter(
                        user=user_name,
                        name=transaction_budget_name,
                        start_date=transaction_start_date,
                        end_date=transaction_end_date,
                    )[0]

                    budget_obj = update_budget_items(
                        user_name,
                        budget_obj,
                        transaction_amount,
                        transaction_out_flow,
                        date_check,
                    )
                    budget_obj.save()

                    budget_obj = None
                # To-Do  Remove bare except
                except:
                    budget_obj = None

            if budget_obj:
                print("Yes Budget Obj")
                try:
                    transaction_budget_name = transaction_obj.budgets.name
                    transaction_start_date, transaction_end_date = start_end_date(
                        transaction_obj.transaction_date, BudgetPeriods.MONTHLY.value
                    )
                    if transaction_budget_name == budget_name:
                        print("transaction_out_flow", transaction_out_flow)
                        print("out_flow", out_flow)
                        print(type(transaction_out_flow))
                        print(type(out_flow))
                        if out_flow != transaction_out_flow:
                            budget_obj = update_budget_items(
                                user_name,
                                budget_obj,
                                transaction_amount,
                                transaction_out_flow,
                                date_check,
                            )
                            budget_obj = add_new_budget_items(
                                user_name,
                                budget_obj,
                                update_transaction_amount,
                                out_flow,
                                date_check,
                            )
                        if transaction_amount != update_transaction_amount:
                            print("yes amount is not equal to update amount")
                            budget_obj = update_budget_items(
                                user_name,
                                budget_obj,
                                transaction_amount,
                                transaction_out_flow,
                                date_check,
                                update_transaction_amount,
                            )
                    else:
                        old_budget_obj = Budget.objects.get(
                            user=user_name,
                            name=transaction_budget_name,
                            start_date=transaction_start_date,
                            end_date=transaction_end_date,
                        )
                        old_budget_obj = update_budget_items(
                            user_name,
                            old_budget_obj,
                            transaction_amount,
                            transaction_out_flow,
                            date_check,
                        )
                        old_budget_obj.save()
                        budget_obj = add_new_budget_items(
                            user_name,
                            budget_obj,
                            update_transaction_amount,
                            out_flow,
                            date_check,
                        )
                except Exception as e:
                    print("exception ========>", e)
                    budget_obj = add_new_budget_items(
                        user_name,
                        budget_obj,
                        update_transaction_amount,
                        out_flow,
                        date_check,
                    )
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
    # To-Do  Remove bare except
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
        if sub_category.category.name == CategoryTypes.FUNDS.value:
            fund_obj = AvailableFunds.objects.get(
                user=user_name, account=account_obj)
            if out_flow:
                fund_obj.total_fund = float(
                    fund_obj.total_fund) - transaction_amount
                total_fund = fund_obj.total_fund
                total_lock_fund = 0.0
                goal_qs = Goal.objects.filter(
                    user=user_name, account=account_obj)
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
                fund_obj.total_fund = float(
                    fund_obj.total_fund) + transaction_amount
                fund_obj.save()

        # if sub_category.category.name == CategoryTypes.INCOME.value:
        #     income_obj = IncomeDetail.objects.get(income__user=user_name, income__account=account_obj,
        #                                           income__sub_category__id=sub_category.id,
        #                                           income_date=transaction_obj.transaction_date)
        #     income_obj.credited = False
        #     income_obj.save()

        if bill_name and method is None:
            if out_flow:
                bill_name.remaining_amount = round(
                    float(bill_name.remaining_amount) + transaction_amount, 2
                )
                bill_name.status = "unpaid"
            else:
                bill_name.remaining_amount = round(
                    float(bill_name.remaining_amount) - transaction_amount, 2
                )
                bill_name.status = "unpaid"

            bill_name.remaining_amount = bill_name.remaining_amount
            bill_name.save()

        if budget_name:
            budget_obj = update_budget_items(
                user_name,
                budget_name,
                transaction_amount,
                out_flow,
                transaction_obj.transaction_date,
            )
            budget_obj.save()

        if out_flow:
            account_obj.available_balance = round(
                float(account_obj.available_balance) + transaction_amount, 2
            )
        else:
            account_obj.available_balance = round(
                float(account_obj.available_balance) - transaction_amount, 2
            )

        account_obj.transaction_count -= 1
        account_obj.save()

    transaction_obj.delete()


class TransactionDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        user_name = self.request.user
        pk = self.kwargs["pk"]
        delete_transaction_details(pk, user_name)
        return JsonResponse({"status": "Successfully", "path": "None"})


def calculate_available_lock_amount(user_name, account_obj):
    fund_data = AvailableFunds.objects.filter(
        user=user_name, account=account_obj
    ).order_by("created_at")[::-1]
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
    category_name = request.POST["category"]
    sub_category_name = request.POST["sub_category_name"]
    goal_amount = request.POST["goal_amount"]
    goal_date = request.POST["goal_date"]
    user_budget_id = request.POST.get("user_budget", "")
    if goal_date == "":
        goal_date = None
    account_name = request.POST["account_name"]
    if "allocate_amount" in request.POST:
        allocate_amount = float(request.POST["allocate_amount"])
    else:
        allocate_amount = 0

    account_obj = Account.objects.get(user=user, name=account_name)
    if user_budget_id:
        user_budget = UserBudgets.objects.get(user=user, pk=user_budget_id)
    fund_amount = 0
    if fun_name:
        # Fetches old goal amount and add the transaction amount to fund amount
        old_goal_amount = goal_obj.allocate_amount
        if old_goal_amount <= allocate_amount:
            fund_amount = allocate_amount - old_goal_amount

        goal_obj.fund_amount += fund_amount

        # Checks continues for fund
        try:
            fund_obj = AvailableFunds.objects.get(
                user=user_name, account=account_obj)
            if float(fund_obj.total_fund) < float(allocate_amount):
                return_data["error"] = (
                    f"Goal allocate amount is greater than {account_obj.name} account total fund."
                    f" please add more fund."
                )
                return return_data
        # To-Do  Remove bare except
        except:
            return_data["error"] = (
                f"Please add lock fund to {account_obj.name} account first then allocate amount to goal"
            )
            return return_data
        if account_obj != goal_obj.account:
            goal_obj.account = account_obj
            goal_obj.save()
            old_fund_obj = AvailableFunds.objects.get(
                user=user_name, account=goal_obj.account
            )
            old_fund_obj.lock_fund = round(
                float(old_fund_obj.lock_fund) -
                float(goal_obj.allocate_amount), 2
            )
            old_fund_obj.save()

            if float(allocate_amount) > float(fund_obj.total_fund):
                return_data["error"] = (
                    f"Goal allocate amount is greater than {account_obj.name} account lock fund."
                    f" please add more lock fund."
                )
                return return_data
            lock_funds = round(float(fund_obj.lock_fund) +
                               float(allocate_amount), 2)
            fund_obj.lock_fund = lock_funds
        else:
            if goal_obj.allocate_amount != float(allocate_amount):
                lock_funds = round(
                    float(fund_obj.lock_fund) + float(allocate_amount), 2
                )
                fund_obj.lock_fund = lock_funds
                fund_obj.lock_fund = round(
                    float(fund_obj.lock_fund) -
                    float(goal_obj.allocate_amount), 2
                )
        category_obj = Category.objects.get(user=user, name=category_name)
        if sub_category_name != goal_obj.label.name:
            sub_category = SubCategory.objects.filter(
                category__user=user, name=sub_category_name
            )
            if not sub_category:
                sub_category = SubCategory.objects.create(
                    category=category_obj, name=sub_category_name
                )
            else:
                goal = Goal.objects.filter(
                    user_budget=user_budget, label=sub_category[0]
                )
                goal = Goal.objects.filter(
                    user_budget=user_budget, label=sub_category[0]
                )
                if goal:
                    return_data["error"] = "Name is already exist"
                    return return_data
                sub_category = sub_category[0]
        else:
            sub_category = goal_obj.label

    else:
        try:
            fund_obj = AvailableFunds.objects.get(
                user=user_name, account=account_obj)
        # To-Do  Remove bare except
        except:
            return_data["error"] = (
                f"Please add lock fund to {account_obj.name} account first then allocate amount to goal"
            )
            return return_data
        lock_funds = round(float(fund_obj.lock_fund) +
                           float(allocate_amount), 2)
        fund_obj.lock_fund = lock_funds
        fund_amount = allocate_amount

        goal_obj.fund_amount = fund_amount
        if float(allocate_amount) > float(fund_obj.total_fund):
            return_data["error"] = (
                f"Goal allocate amount is greater than {account_obj.name} account lock fund."
                f" please add more lock fund."
            )
            return return_data

        category = Category.objects.filter(user=user, name=category_name)
        if not category:
            category_obj = Category.objects.create(
                name=category_name, user=user)
        else:
            category_obj = category[0]

        sub_category = SubCategory.objects.filter(
            category=category_obj, name=sub_category_name
        )
        if not sub_category:
            sub_category = SubCategory.objects.create(
                category=category_obj, name=sub_category_name
            )
        else:
            goal = Goal.objects.filter(
                user_budget=user_budget, label=sub_category[0])
            if goal:
                return_data["error"] = "Name is already exist"
                return return_data
            sub_category = sub_category[0]

    goal_obj.user = user_name
    goal_obj.user_budget = user_budget
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
    template_name = "goal/goal_list.html"

    def post(self, request, *args, **kwargs):
        """
        Handles POST request
        """
        if request.method == "POST":
        if request.method == "POST":
            self.object_list = self.get_queryset()
            user_budget_id = self.request.POST.get("user_budget")
            user_budget_id = self.request.POST.get("user_budget")
            if user_budget_id:
                self.user_budget = UserBudgets.objects.get(
                    user=request.user, pk=user_budget_id
                )
                    user=request.user, pk=user_budget_id
                )

            return self.render_to_response(self.get_context_data())
        else:
            return HttpResponseNotAllowed(["POST"])
            return HttpResponseNotAllowed(["POST"])

    def get(self, request, *args, **kwargs):
        """
        Handles GET request
        """

        self.object_list = self.get_queryset()
        # self.date_value = datetime.datetime.today().date()

        # Fetch the Default budget id if available, if not fetch the \
        # first user budget
        selected_budget_id = request.session.get("default_budget_id")
        if selected_budget_id:
            try:
                self.user_budget = UserBudgets.objects.get(
                    user=request.user, pk=int(selected_budget_id)
                )
            except UserBudgets.DoesNotExist:
                self.user_budget = UserBudgets.objects.filter(
                    user=request.user).first()
        else:
            self.user_budget = UserBudgets.objects.filter(
                user=self.request.user
            ).first()

        return self.render_to_response(self.get_context_data())

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        data = super(GoalList, self).get_context_data(**kwargs)
        user_name = self.request.user
        user_budget_qs = UserBudgets.objects.filter(user=user_name)
        goal_data = Goal.objects.filter(user_budget=self.user_budget)
        fund_value = show_current_funds(user_name, fun_name="goal_funds")
        data["fund_key"] = FUND_KEYS
        data["fund_value"] = fund_value
        data["goal_data"] = goal_data
        data["user_budget_qs"] = user_budget_qs
        data["selected_budget"] = self.user_budget
        data["tour_api"] = Tour_APIs["goals_page"]
        data["user_budget_qs"] = user_budget_qs
        data["selected_budget"] = self.user_budget
        data["tour_api"] = Tour_APIs["goals_page"]
        return data


class GoalDetail(LoginRequiredMixin, DetailView):
    model = Goal
    template_name = "goal/goal_detail.html"


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
    budget_qs = UserBudgets.objects.filter(user=user_name)
    if request.method == "POST":
        goal_obj = Goal()
        goal_data = goal_obj_save(request, goal_obj, user_name)
        if "error" in goal_data:
            error = goal_data["error"]
        else:
            return redirect("/goal_list")

    account_data = Account.objects.filter(
        user=user_name, account_type__in=AccountTypes.list()
    )
    category_obj = Category.objects.get(
        name=CategoryTypes.GOALS.value, user=user_name)
    sub_obj = SubCategory.objects.filter(
        category__user=user_name, category__name=CategoryTypes.GOALS.value
    )
    context = {
        "account_data": account_data,
        "goal_category": sub_obj,
        "page": "goal_add",
        "category_icons": CATEGORY_ICONS,
        "budget_qs": budget_qs,
        "budget_qs": budget_qs,
    }

    if error:
        context["error"] = error
    return render(request, "goal/goal_add.html", context=context)


@login_required(login_url="/login")
def goal_update(request, pk):
    user_name = request.user
    error = False
    goal_data = Goal.objects.get(pk=pk)
    budget_qs = UserBudgets.objects.filter(user=user_name)
    if request.method == "POST":
        goal_result = goal_obj_save(
            request, goal_data, user_name, fun_name="goal_update"
        )
        if "error" in goal_result:
            error = goal_result["error"]
        else:
            return redirect("/goal_list")

    account_data = Account.objects.filter(
        user=user_name, account_type__in=AccountTypes.list()
    )

    category_obj = Category.objects.get(
        name=CategoryTypes.GOALS.value, user=user_name)
    context = {
        "account_data": account_data,
        "goal_data": goal_data,
        "goal_category": SubCategory.objects.filter(category=category_obj),
        "budget_qs": budget_qs,
        "budget_qs": budget_qs,
    }
    if error:
        context["error"] = error
    return render(request, "goal/goal_update.html", context=context)


class GoalDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        user = request.user
        goal_obj = Goal.objects.get(pk=self.kwargs["pk"])
        fund_obj = AvailableFunds.objects.get(
            user=user, account=goal_obj.account)
        fund_obj.lock_fund = round(
            float(fund_obj.lock_fund) - float(goal_obj.fund_amount), 2
        )
        fund_obj.save()
        goal_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


def account_box(request):
    context = {"page": "account_box", "tour_api": Tour_APIs["bank_ac_page"]}
    context = {"page": "account_box", "tour_api": Tour_APIs["bank_ac_page"]}
    return render(request, "account/account_box.html", context)


def account_list(request, name):
    account_qs = Account.objects.filter(
        user=request.user, account_type__in=[name])
    context = {"account_qs": account_qs, "name": name}
    return render(request, "account/account_list.html", context=context)


class AccountDetail(LoginRequiredMixin, DetailView):
    model = Account
    template_name = "account/account_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account_pk = self.kwargs["pk"]
        account_obj = Account.objects.get(pk=account_pk)
        current_balance = float(account_obj.available_balance)
        initial_balance = current_balance
        transaction_data = Transaction.objects.filter(
            user=self.request.user, account__pk=account_pk
        ).order_by("transaction_date")[::-1]
        date_list = []
        balance_graph_data = []
        transaction_graph_value = []
        index = 1
        for data in transaction_data:
            if data.cleared:
                if index == 1:
                    graph_dict = {
                        "x": str(data.transaction_date),
                        "y": round(initial_balance, 2),
                    }
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
                        date_index = date_list.index(
                            str(data.transaction_date))
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
                        balance_graph_data[date_index]["y"] = round(
                            result_value, 2)
                    else:
                        graph_dict = {
                            "x": str(data.transaction_date),
                            "y": round(current_balance, 2),
                        }
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
                starting_balance = balance_graph_data[-1]["y"] - \
                    sum(amount_list)
            else:
                starting_balance = balance_graph_data[-1]["y"] + \
                    sum(amount_list)

            amount_diff = initial_balance - starting_balance
            amount_inc_percentage = round(
                amount_diff / starting_balance * 100, 2)
            for data in balance_graph_data:
                transaction_graph_value.append(data["y"])
        else:
            amount_diff = 0
            amount_inc_percentage = 0

        print(balance_graph_data)
        context["balance_graph_data"] = balance_graph_data
        context["transaction_data"] = transaction_data
        context["transaction_date_dumbs"] = json.dumps(date_list)
        context["transaction_graph_value"] = transaction_graph_value
        context["transaction_key"] = TRANSACTION_KEYS
        context["transaction_key_dumbs"] = json.dumps(TRANSACTION_KEYS)
        context["amount_diff"] = amount_diff
        context["amount_inc_percentage"] = amount_inc_percentage

        return context


class AccountAdd(LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = "account/account_add.html"

    def get_success_url(self):
        """Detect the submit button used and act accordingly
        Redirect the user to the selected account list page.
        """

        if "account_type" in self.request.POST:
            name = self.request.POST.get("account_type")
            return reverse_lazy("account_list", kwargs={"name": name})
        else:
            return reverse_lazy("account_add")

    def form_valid(self, form):
        account_name = form.cleaned_data.get("name").title()
        account_type = form.cleaned_data.get("account_type")
        balance = float(form.cleaned_data.get("balance"))
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
    template_name = "account/account_update.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account_pk = self.kwargs["pk"]
        account_obj = Account.objects.get(pk=account_pk)
        context["account_type"] = account_obj.account_type
        context["balance"] = account_obj.available_balance
        return context

    def form_valid(self, form):
        obj = form.save(commit=False)
        account_type = form.cleaned_data.get("account_type")
        account_name = form.cleaned_data.get("name").title()
        balance = float(form.cleaned_data.get("balance"))
        obj.user = self.request.user
        obj.name = account_name
        obj.account_type = account_type
        obj.balance = balance
        obj.available_balance = balance
        obj.save()
        return super().form_valid(form)


class AccountDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        account_obj = Account.objects.get(pk=self.kwargs["pk"])
        account_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "/account_list/"})


# LOAN VIEW


def loan_accounts_box(request):
    return render(request, "loan/loan_box.html")


def loan_add(request):
    loan_error = False
    user = request.user
    if request.method == "POST":
        category_name = request.POST["category"].title()
        loan_type = request.POST["loan_type"]
        sub_category_name = request.POST["sub_category_name"].title()
        currency = request.POST["currency"]
        amount = request.POST["amount"]
        interest_rate = request.POST["interest_rate"]
        monthly_payment = request.POST["monthly_payment"]
        include_net_worth = request.POST["include_net_worth"]
        mortgage_date = request.POST["mortgage_date"]
        if include_net_worth == "on":
            include_net_worth = True
        else:
            include_net_worth = False

        category = Category.objects.filter(name=category_name)
        if not category:
            category_obj = Category.objects.create(
                name=category_name, user=user)
        else:
            category_obj = category[0]

        sub_category = SubCategory.objects.filter(
            category__user=user, name=sub_category_name
        )
        if not sub_category:
            SubCategory.objects.create(
                category=category_obj, name=sub_category_name)
            mortgage_year = calculate_tenure(
                float(amount), float(monthly_payment), float(interest_rate)
            )
            if mortgage_year:
                print(mortgage_year)
                Account.objects.create(
                    name=sub_category_name,
                    user=user,
                    account_type=loan_type,
                    currency=currency,
                    balance=amount,
                    available_balance=amount,
                    interest_rate=interest_rate,
                    mortgage_monthly_payment=monthly_payment,
                    mortgage_date=mortgage_date,
                    mortgage_year=mortgage_year,
                    include_net_worth=include_net_worth,
                )
                return redirect("/mortgages-loans-accounts/")
            loan_error = "The monthly payment is not sufficient to cover the interest and principal."
        else:
            loan_error = "Name is already exist"

    category = Category.objects.filter(user=user)
    category_list = []
    for data in category:
        if any(name in data.name for name in MORTGAGE_KEYWORDS):
            category_list.append(data.name)

    context = {
        "category_list": category_list,
        "today_date": str(today_date),
        "currency_dict": CURRENCY_DICT,
        "loan_type": LOAN_TYPES,
    }
    if loan_error:
        context["loan_error"] = loan_error
    return render(request, "loan/loan_add.html", context=context)


def loan_list(request, name):
    account = Account.objects.filter(
        user=request.user, account_type__in=[name])
    loan_accounts = []
    for data in account:
        transaction_data = Transaction.objects.filter(
            user=request.user, categories__name=data.name
        )
        loan_accounts.append(
            {
                "id": data.id,
                "name": data.name,
                "account_type": data.account_type,
                "available_balance": data.available_balance,
                "currency": data.currency,
                "interest_rate": data.interest_rate,
                "updated_at": data.updated_at,
                "transaction_count": len(transaction_data),
            }
        )

    return render(
        request, "loan/loan_list.html", context={"account": loan_accounts, "name": name}
    )


def loan_update(request, pk):
    user = request.user
    account = Account.objects.get(pk=pk)
    loan_error = False
    if request.method == "POST":
        category_name = request.POST["category"].title()
        loan_type = request.POST["loan_type"]
        sub_category_name = request.POST["sub_category_name"].title()
        currency = request.POST["currency"]
        amount = request.POST["amount"]
        interest_rate = request.POST["interest_rate"]
        monthly_payment = request.POST["monthly_payment"]
        include_net_worth = request.POST["include_net_worth"]
        mortgage_date = request.POST["mortgage_date"]
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
            sub_category = SubCategory.objects.filter(
                category__user=user, name=sub_category_name
            )
            if not sub_category:
                SubCategory.objects.create(
                    category=category_obj, name=sub_category_name
                )
                mortgage_year = calculate_tenure(
                    float(amount), float(monthly_payment), float(interest_rate)
                )
                if mortgage_year:
                    account.mortgage_year = mortgage_year
                    account.save()
                    return redirect(f"/mortgages-loans-accounts/{loan_type}")
                loan_error = "The monthly payment is not sufficient to cover the interest and principal."
            else:
                loan_error = "Name is already exist"
        else:
            mortgage_year = calculate_tenure(
                float(amount), float(monthly_payment), float(interest_rate)
            )
            if mortgage_year:
                account.mortgage_year = mortgage_year
                account.save()
                return redirect(f"/mortgages-loans-accounts/{loan_type}")
            loan_error = "The monthly payment is not sufficient to cover the interest and principal."

    category = Category.objects.filter(user=user)
    category_list = []
    for data in category:
        if any(name in data.name for name in MORTGAGE_KEYWORDS):
            category_list.append(data.name)

    context = {
        "category_list": category_list,
        "today_date": str(today_date),
        "currency_dict": CURRENCY_DICT,
        "loan_type": LOAN_TYPES,
        "account": account,
    }
    if loan_error:
        context["loan_error"] = loan_error
    return render(request, "loan/loan_update.html", context=context)


def loan_delete(request, pk):
    user = request.user
    account = Account.objects.get(pk=pk)
    account_type = account.account_type
    sub_category = SubCategory.objects.get(
        category__user=user, name=account.name)
    user = request.user
    transaction_details = Transaction.objects.filter(
        user=user, categories=sub_category)
    for data in transaction_details:
        delete_transaction_details(data.pk, user)
    sub_category.delete()
    account.delete()
    return JsonResponse(
        {"status": "Successfully", "path": f"/mortgages-loans-accounts/{account_type}"}
    )


def loan_details(request, pk):
    account = Account.objects.get(pk=pk)
    amount = float(account.balance)
    interest = float(account.interest_rate)
    tenure_months = int(account.mortgage_year)
    mortgage_date = account.mortgage_date
    monthly_payment = account.mortgage_monthly_payment
    table = calculator(amount, interest, tenure_months, tenure_months)
    total_payment = abs(table["principle"].sum() + table["interest"].sum())
    json_records = table.reset_index().to_json(orient="records")
    data = json.loads(json_records)
    mortgage_key, mortgage_graph_data, last_month, mortgage_date_data = (
        make_mortgage_data(data, tenure_months, mortgage_date)
    )
    categories = SubCategory.objects.get(name=account.name)
    transaction_data = Transaction.objects.filter(
        user=request.user, categories=categories, out_flow=True
    )
    total_pay_amount = list(transaction_data.values_list("amount", flat=True))
    total_pay_amount = [float(x) for x in total_pay_amount]
    print(sum(total_pay_amount))
    remaining_amount = float(total_payment) - float(sum(total_pay_amount))

    context = {
        "data": data,
        "monthly_payment": monthly_payment,
        "remaining_amount": remaining_amount,
        "last_month": last_month,
        "days": tenure_months,
        "total_payment": total_payment,
        "mortgage_key": mortgage_key,
        "mortgage_key_dumbs": json.dumps(mortgage_key),
        "mortgage_graph_data": mortgage_graph_data,
        "mortgage_date_data": mortgage_date_data,
        "account": account,
        "transaction_key": TRANSACTION_KEYS,
        "transaction_data": transaction_data,
    }

    return render(request, "loan/loan_detail.html", context=context)


class LiabilityAdd(LoginRequiredMixin, CreateView):
    # model = Account
    form_class = LiabilityForm
    template_name = "liability/liability_add.html"

    def post(self, request, *args, **kwargs):
        name = request.POST["name"]
        currency = request.POST["currency"]
        liability_type = request.POST["liability_type"]
        balance = float(request.POST["balance"])
        interest_rate = float(request.POST["interest_rate"])
        interest_period = request.POST["interest_period"]
        mortgage_year = int(request.POST["mortgage_year"])
        try:
            include_net_worth = request.POST["include_net_worth"]
            include_net_worth = True
        # To-Do  Remove bare except
        except:
            include_net_worth = False

        table = calculator(balance, interest_rate, mortgage_year)

        total_payment = abs(table["principle"].sum() + table["interest"].sum())
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
        return redirect("/liability_list/")


class LiabilityList(LoginRequiredMixin, ListView):
    model = Account
    template_name = "liability/liability_list.html"

    def get_queryset(self):
        return Account.objects.filter(user=self.request.user)


class LiabilityUpdate(LoginRequiredMixin, UpdateView):
    model = Account
    form_class = LiabilityForm
    template_name = "liability/liability_update.html"

    def post(self, request, *args, **kwargs):
        name = request.POST["name"]
        currency = request.POST["currency"]
        liability_type = request.POST["liability_type"]
        balance = float(request.POST["balance"])
        interest_rate = float(request.POST["interest_rate"])
        interest_period = request.POST["interest_period"]
        mortgage_year = int(request.POST["mortgage_year"])
        try:
            include_net_worth = request.POST["include_net_worth"]
            include_net_worth = True
        # To-Do  Remove bare except
        except:
            include_net_worth = False

        table = calculator(balance, interest_rate, mortgage_year)

        total_payment = abs(table["principle"].sum() + table["interest"].sum())
        liability_obj = Account.objects.get(pk=self.kwargs["pk"])
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
        return redirect("/liability_list/")


class LiabilityDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        liability_obj = Account.objects.get(pk=self.kwargs["pk"])
        liability_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "/liability_list/"})


class LiabilityDetail(LoginRequiredMixin, DetailView):
    model = Account
    template_name = "liability/liability_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        account_pk = self.kwargs["pk"]
        account_obj = Account.objects.get(pk=account_pk)
        current_balance = float(account_obj.available_balance)
        initial_balance = current_balance
        transaction_data = Transaction.objects.filter(
            user=self.request.user, account__pk=account_pk
        ).order_by("transaction_date")[::-1]
        date_list = []
        balance_graph_data = []
        index = 1
        for data in transaction_data:
            if index == 1:
                graph_dict = {
                    "x": str(data.transaction_date),
                    "y": round(initial_balance, 2),
                }
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
                    balance_graph_data[date_index]["y"] = round(
                        result_value, 2)
                else:
                    graph_dict = {
                        "x": str(data.transaction_date),
                        "y": round(current_balance, 2),
                    }
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
                starting_balance = balance_graph_data[-1]["y"] - \
                    sum(amount_list)
            else:
                starting_balance = balance_graph_data[-1]["y"] + \
                    sum(amount_list)

            amount_diff = initial_balance - starting_balance
            amount_inc_percentage = round(
                amount_diff / starting_balance * 100, 2)
        else:
            amount_diff = 0
            amount_inc_percentage = 0

        context["balance_graph_data"] = balance_graph_data
        context["transaction_data"] = transaction_data
        context["transaction_key"] = TRANSACTION_KEYS
        context["transaction_key_dumbs"] = json.dumps(TRANSACTION_KEYS)
        context["amount_diff"] = amount_diff
        context["amount_inc_percentage"] = amount_inc_percentage
        return context


# FUNDS VIEWS


def show_current_funds(user_name, fun_name=None):
    account_data = Account.objects.all()
    fund_value = []
    for obj in account_data:
        fund_data = AvailableFunds.objects.filter(user=user_name, account=obj).order_by(
            "created_at"
        )[::-1]
        if fund_data:
            fund_obj = fund_data[0]
            transaction_data = Transaction.objects.filter(
                user=user_name, account=obj)
            spend_amount = 0
            for transaction in transaction_data:
                if transaction.cleared:
                    if transaction.out_flow:
                        spend_amount += float(transaction.amount)
                    else:
                        if spend_amount != 0:
                            spend_amount -= float(transaction.amount)

            if fun_name:
                available_lock_amount = calculate_available_lock_amount(
                    user_name, obj)
                available_lock_amount = round(
                    float(fund_obj.total_fund) - float(fund_obj.lock_fund), 2
                )
                fund_value.append(
                    [
                        fund_obj.account.name,
                        fund_obj.account.available_balance,
                        fund_obj.total_fund,
                        fund_obj.lock_fund,
                        available_lock_amount,
                        fund_obj.id,
                    ]
                )
            else:
                fund_value.append(
                    [
                        fund_obj.account.name,
                        fund_obj.account.available_balance,
                        fund_obj.total_fund,
                        fund_obj.lock_fund,
                        available_lock_amount,
                        fund_obj.id,
                    ]
                )

    return fund_value


class FundList(LoginRequiredMixin, ListView):
    model = AvailableFunds
    template_name = "funds/funds_list.html"

    def get_context_data(self, **kwargs):
        data = super(FundList, self).get_context_data(**kwargs)
        user_name = self.request.user
        fund_value = show_current_funds(user_name, fun_name="goal_funds")
        data["fund_key"] = FUND_KEYS
        data["fund_value"] = fund_value
        return data


@login_required(login_url="/login")
def fund_overtime(request):
    if request.method == "POST" and request.is_ajax():
        user_name = request.user
        account_name = request.POST["account_name"]
        transaction_qs = Transaction.objects.filter(
            user=user_name,
            account__name=account_name,
            categories__category__name=CategoryTypes.FUNDS.value,
        ).order_by("transaction_date")
        if transaction_qs:
            min_date = transaction_qs[0].transaction_date
            max_date = datetime.datetime.today().date()
            day_diff = (max_date - min_date).days
            freeze_funds = []
            account_date_list = []
            fund_graph_data = []
            outflow_count = 0
            for transaction_data in transaction_qs:
                account_date_list.append(
                    str(transaction_data.transaction_date))
                if transaction_data.out_flow:
                    outflow_count += 1
                    freeze_funds.append(float(transaction_data.amount))

                else:
                    if outflow_count >= 1:
                        freeze_total = sum(freeze_funds)
                        freeze_funds.append(
                            freeze_total - float(transaction_data.amount)
                        )

            fund_graph_data.append(
                {"label_name": "Freeze Amount", "data_value": freeze_funds}
            )
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
    return JsonResponse(
        {
            "fund_data": fund_graph_data,
            "date_range_list": account_date_list,
            "max_value": max_value,
            "min_value": min_value,
        }
    )


@login_required(login_url="/login")
def fund_accounts(request):
    context = {}
    return render(request, "funds/fund_account_box.html", context=context)


@login_required(login_url="/login")
def fund_add(request, name):
    user_name = request.user
    error = False

    if request.method == "POST":
        fund_data = save_fund_obj(request, user_name)

        if "error" in fund_data:
            error = fund_data["error"]
        else:
            return redirect("/goal_list")

    account_data = Account.objects.filter(user=user_name, account_type=name)
    context = {"account_data": account_data, "name": name}
    if error:
        context["error"] = error
    return render(request, "funds/funds_add.html", context=context)


@login_required(login_url="/login")
def fund_update(request, pk):
    fund_data = AvailableFunds.objects.get(pk=pk)
    if request.method == "POST":
        freeze_amount = round(float(request.POST["freeze_amount"]), 2)
        old_total_fund = float(fund_data.total_fund)
        if old_total_fund != freeze_amount:
            account_obj = fund_data.account
            account_balance = float(account_obj.available_balance)
            sub_category = SubCategory.objects.get(
                category__user=fund_data.user, name=account_obj.name
            )
            transaction_obj = Transaction()
            if freeze_amount > old_total_fund:
                add_amount = freeze_amount - old_total_fund
                remaining_amount = account_balance - add_amount
                transaction_obj.out_flow = True
            else:
                add_amount = old_total_fund - freeze_amount
                if freeze_amount < float(fund_data.lock_fund):
                    context = {
                        "fund_data": fund_data,
                        "error": "This freeze amount already locked for goals. please add more amount to freeze.",
                    }
                    return render(request, "funds/funds_update.html", context=context)
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
            tag_obj, tag_created = Tag.objects.get_or_create(
                user=fund_data.user, name="Adding Funds"
            )
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
        return redirect("/goal_list")
    context = {"fund_data": fund_data}

    return render(request, "funds/funds_update.html", context=context)


def fund_delete(request, pk):
    fund_data = AvailableFunds.objects.get(pk=pk)
    account_obj = fund_data.account
    sub_category = SubCategory.objects.get(
        category__user=fund_data.user, name=account_obj.name
    )
    goal_qs = Goal.objects.filter(user=fund_data.user, account=account_obj)
    transaction_qs = Transaction.objects.filter(
        user=fund_data.user, categories=sub_category
    )
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
    bill_qs = Bill.objects.filter(
        user=user, bill_details__pk=pk).order_by("date")
    bill_obj = bill_qs[0].bill_details
    bill_dict = {
        "id": bill_qs[0].bill_details.id,
        "label": bill_obj.label,
        "account": bill_obj.account,
        "due_date": bill_obj.date,
        "amount": bill_obj.amount,
        "frequency": bill_obj.frequency,
        "auto_pay": bill_obj.auto_pay,
        "auto_bill": bill_obj.auto_bill,
        "due_bills": [],
        "paid_bills": [],
    }
    for bill in bill_qs:
        if bill.status == "unpaid":
            bill_dict["due_bills"].append(bill)
        else:
            bill_dict["paid_bills"].append(bill)

    transaction_data = Transaction.objects.filter(
        user=user, bill__bill_details=bill_obj
    ).order_by("-transaction_date")
    context = {"bill_data": bill_dict, "transaction_data": transaction_data}
    return render(request, "bill/bill_detail.html", context=context)


@login_required(login_url="/login")
def bill_edit(request, pk):
    bill_obj = BillDetail.objects.get(pk=pk)
    form = BillForm(request.POST or None, request=request)
    error = ""
    user = request.user
    if form.is_valid():
        label = form.cleaned_data.get("label").title()
        amount = form.cleaned_data.get("amount")
        bill_date = form.cleaned_data.get("date")
        frequency = form.cleaned_data.get("frequency")
        account_name = request.POST["account_name"]
        account_obj = Account.objects.get(user=user, name=account_name)
        bill_obj.label = label
        bill_obj.account = account_obj
        bill_obj.amount = amount
        bill_obj.date = bill_date
        try:
            auto_bill = request.POST["auto_bill"]
            bill_obj.frequency = frequency
            bill_obj.auto_bill = True
        # To-Do  Remove bare except
        except:
            bill_obj.auto_bill = False

        try:
            auto_pay = request.POST["auto_pay"]
            bill_obj.auto_pay = True
        except:
            bill_obj.auto_pay = False

        try:
            unpaid_apply = request.POST["unpaid_apply"]
        except:
            unpaid_apply = "off"

        if unpaid_apply == "on":
            bill_obj.auto_pay = True
            bill_qs = Bill.objects.filter(
                user=request.user, label=label, account=account_obj, status="unpaid"
            )
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
            check_bill_obj = Bill.objects.filter(
                user=request.user, label=label, account=account_obj
            )
            if check_bill_obj:
                error = "Bill Already Exit!!"
            else:
                bill_obj.save()
                return redirect(f"/bill_details/{pk}")
        else:
            bill_obj.save()
            return redirect(f"/bill_details/{pk}")

    bill_category = SubCategory.objects.filter(
        category__name=CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value, category__user=user
    )
    account_qs = Account.objects.filter(
        user=user, account_type__in=AccountTypes.list())
    bill_frequency = BudgetPeriods.list()
    context = {
        "form": form,
        "error": error,
        "bill_data": bill_obj,
        "currency_dict": CURRENCY_DICT,
        "bill_category": bill_category,
        "account_qs": account_qs,
        "bill_frequency": bill_frequency,
    }
    return render(request, "bill/bill_edit.html", context=context)


@login_required(login_url="/login")
def bill_pay(request, pk):
    bill_obj = Bill.objects.get(pk=pk)
    # Pay the remaining amount from the bill
    bill_amount = float(bill_obj.remaining_amount)
    account_obj = bill_obj.account
    account_balance = float(account_obj.available_balance)
    if account_balance < bill_amount:
        return JsonResponse({"status": "false"})
    remaining_amount = round(account_balance - bill_amount, 2)
    label = bill_obj.label
    user = bill_obj.user
    categories = SubCategory.objects.get(
        name=label,
        category__name=CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value,
        category__user=user,
    )
    tag_obj, _ = Tag.objects.get_or_create(user=user, name="Bills")
    save_transaction(
        user,
        label,
        bill_amount,
        remaining_amount,
        today_date,
        categories,
        account_obj,
        tag_obj,
        True,
        True,
        bill_obj,
    )
    account_obj.available_balance = remaining_amount
    account_obj.transaction_count += 1
    account_obj.save()
    bill_obj.remaining_amount = 0.0
    bill_obj.status = "paid"
    bill_obj.save()
    return JsonResponse({"status": "true"})


@login_required(login_url="/login")
def bill_list(request):
    user_name = request.user
    selected_budget_id = request.session.get("default_budget_id", None)

    selected_budget_id = request.session.get("default_budget_id", None)

    user_budget_qs = UserBudgets.objects.filter(user=request.user)
    user_budget = None

    # Fetch the user budget from POST request
    user_budget = None

    # Fetch the user budget from POST request
    if "user_budget" in request.POST:
        user_budget_id = request.POST.get("user_budget")
        user_budget = UserBudgets.objects.get(
            user=user_name, pk=int(user_budget_id))

    # If session data available, fetch the default budget object
    if user_budget is None and selected_budget_id:
        user_budget = UserBudgets.objects.get(
            user=user_name, pk=int(selected_budget_id)
        )

    # If neither session is availabe nor the POST data, fetch \
    # first budget object
    if user_budget is None:
        user_budget = UserBudgets.objects.filter(user=user_name).first()

    bill_list_data = BillDetail.objects.filter(
        user=request.user, user_budget=user_budget
    ).order_by("date")
    bills_list = bill_list_data
    bill_data = Bill.objects.filter(user=user_name, user_budget=user_budget)

    # If specific dataa requried from dropdown, it will update the bill list
    # if 'selected_bill' in request.POST:
    #     bill_label = request.POST['selected_bill']
    #     if bill_label != 'all':
    #         bill_list_data = BillDetail.objects.filter(user=request.user, user_budget=user_budget,
    #             label=bill_label).order_by('date')
    #         bill_data = Bill.objects.filter(user=user_name, user_budget=user_budget, label=bill_label)
    # else:
    #     bill_label = None

    calendar_bill_data = []

    for data in bill_data:
        data_dict = {
            "label": data.label,
            "date": str(data.date),
            "label_id": data.bill_details.id,
        }
        if data.status == "unpaid":
            data_dict["calendar_type"] = "Personal"
        else:
            data_dict["calendar_type"] = "Holiday"

        calendar_bill_data.append(data_dict)
    context = {
        "calendar_bill_data": calendar_bill_data,
        "user_budget_qs": user_budget_qs,
        "bill_list": bills_list,
        "bill_data": bill_list_data,
        "today_date": today_date,
        "page": "bill_list",
        "selected_budget": user_budget,
        "tour_api": Tour_APIs["bill_subs_page"],
        "tour_api": Tour_APIs["bill_subs_page"],
    }
    return render(request, "bill/bill_list.html", context=context)


@login_required(login_url="/login")
def bill_detail(request, pk):
    bill_obj = Bill.objects.get(pk=pk)
    transaction_data = Transaction.objects.filter(bill=bill_obj)
    context = {"bill_data": bill_obj, "transaction_data": transaction_data}
    return render(request, "bill/bill_detail.html", context)


def bill_adding_fun(request, method_name=None):
    form = BillForm(request.POST or None, request=request)
    error = ""
    user = request.user
    if form.is_valid():
        label = form.cleaned_data.get("label").title()
        amount = form.cleaned_data.get("amount")
        bill_date = form.cleaned_data.get("date")
        frequency = form.cleaned_data.get("frequency")
        account_name = request.POST["account_name"]
        account_obj = Account.objects.get(user=user, name=account_name)
        user_budget = form.cleaned_data.get("user_budget")
        currency = account_obj.currency
        user_budget = UserBudgets.objects.get(
            user=request.user, name=user_budget)
        check_bill_obj = Bill.objects.filter(
            user=request.user, user_budget=user_budget, label=label, account=account_obj
        )
        if check_bill_obj:
            if method_name:
                return "Bill_list"
            else:
                error = "Bill Already Exist!!"
        else:
            if float(amount) > 0:
                bill_obj = Bill()
                bill_obj.user = request.user
                bill_obj.label = label
                bill_obj.account = account_obj
                bill_obj.amount = amount
                bill_obj.date = bill_date
                bill_obj.currency = currency
                bill_obj.remaining_amount = amount
                bill_obj.user_budget = user_budget

                try:
                    auto_bill = request.POST["auto_bill"]
                    bill_obj.frequency = frequency
                    bill_obj.auto_bill = True
                # To-Do  Remove bare except
                except:
                    bill_obj.auto_bill = False

                try:
                    auto_pay = request.POST["auto_pay"]
                    bill_obj.auto_pay = True
                except:
                    bill_obj.auto_pay = False

                bill_details_obj = BillDetail.objects.create(
                    user=user,
                    label=label,
                    user_budget=user_budget,
                    account=account_obj,
                    amount=amount,
                    date=bill_date,
                    frequency=bill_obj.frequency,
                    auto_bill=bill_obj.auto_bill,
                    auto_pay=bill_obj.auto_pay,
                )
                bill_obj.bill_details = bill_details_obj
                bill_obj.save()
                # if bill_date <= today_date:
                #     check_bill_is_due()
                # else:
                create_bill_request()
                return "Bill_list"

            else:
                error = "Please enter Bill amount greater than 0."
    bill_category = SubCategory.objects.filter(
        category__name=CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value, category__user=user
    )
    bill_obj = Category.objects.get(
        user=user, name=CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value
    )
    account_qs = Account.objects.filter(
        user=user, account_type__in=AccountTypes.list())
    context = {
        "form": form,
        "error": error,
        "account_qs": account_qs,
        "bill_category": bill_category,
        "bill_id": bill_obj.id,
    }
    return context


@login_required(login_url="/login")
def bill_walk_through(request):
    if request.method == "POST" and request.is_ajax():
        user_budget_id = request.POST.get("user_budget_id")
        user_name = request.user
        bill_name = request.POST["name"]
        bill_exp_amount = float(request.POST["exp_amount"])
        bill_act_amount = float(request.POST["actual_amount"])
        bill_id = request.POST["id"]
        bill_account_id = request.POST["bill_account_id"]
        bill_left_amount = round(bill_exp_amount - bill_act_amount, 2)
        account_obj = Account.objects.get(id=int(bill_account_id))
        budget_period = request.POST["budget_period"]
        bill_date = request.POST["budget_date"]
        user_budget = UserBudgets.objects.get(
            user=user_name, pk=int(user_budget_id))

        # Check if the expected amount is greater than Zero to avoid ZeroDivisionError
        if bill_exp_amount == 0:
            return JsonResponse(
                {"status": "false", "message": "Bill amount cannot be 0"}
            )

            return JsonResponse(
                {"status": "false", "message": "Bill amount cannot be 0"}
            )

        # check subcategory exist or not
        try:
            sub_cat_obj = SubCategory.objects.get(
                category__user=user_name,
                category__name=CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value,
                name=bill_name,
            )
            sub_cat_obj.name = bill_name
            sub_cat_obj.save()
        # To-Do  Remove bare except
        except:
            sub_cat_obj = SubCategory()
            sub_cat_obj.category = Category.objects.get(
                user=user_name, name=CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value
            )
            sub_cat_obj.name = bill_name
            sub_cat_obj.save()

        if bill_id == "false":
            if bill_date:
                bill_date = datetime.datetime.strptime(
                    bill_date, DateFormats.YYYY_MM_DD.value
                )
                bill_date = datetime.datetime.strptime(
                    bill_date, DateFormats.YYYY_MM_DD.value
                )
            else:
                bill_date = datetime.datetime.today().date()
            bill_date, end_month_date = start_end_date(
                bill_date, BudgetPeriods.MONTHLY.value
            )
            try:
                bill_obj = Bill.objects.filter(
                    user=user_name,
                    user_budget=user_budget,
                    label=bill_name,
                    date__range=(bill_date, end_month_date),
                )
                if bill_obj:
                    return JsonResponse(
                        {"status": "false", "message": "Bill Already Exists"}
                    )
                else:
                    bill_obj = Bill()
            # To-Do  Remove bare except
            except:
                bill_obj = Bill()

            bill_obj.user = request.user
            bill_obj.user_budget = user_budget
            bill_obj.label = bill_name
            bill_obj.account = account_obj
            bill_obj.amount = bill_exp_amount
            bill_obj.date = bill_date
            bill_obj.currency = "$"
            bill_obj.remaining_amount = bill_left_amount
            bill_obj.frequency = budget_period
            bill_obj.auto_bill = False
            bill_obj.auto_pay = False
            # If full amount paid, change the status to 'paid'
            if bill_exp_amount == bill_act_amount:
                bill_obj.status = "paid"
            else:
                bill_obj.status = "unpaid"
            bill_details_obj = BillDetail.objects.create(
                user=user_name,
                user_budget=user_budget,
                label=bill_name,
                account=account_obj,
                amount=bill_exp_amount,
                date=bill_date,
                frequency=bill_obj.frequency,
                auto_bill=bill_obj.auto_bill,
                auto_pay=bill_obj.auto_pay,
            )
            bill_obj.bill_details = bill_details_obj
            bill_obj.save()
        else:
            bill_obj = Bill.objects.get(
                id=int(bill_id), user_budget=user_budget)
            old_spend_amount = round(
                float(bill_obj.amount) - float(bill_obj.remaining_amount), 2
            )
            bill_obj.name = bill_name
            bill_obj.amount = bill_exp_amount
            bill_obj.remaining_amount = bill_left_amount
            bill_details_obj = bill_obj.bill_details
            bill_details_obj.name = bill_name
            bill_details_obj.amount = bill_exp_amount
            bill_details_obj.save()
            # Change status to 'paid', if remaining amount becomes zero
            if bill_left_amount == 0.0:
                bill_obj.status = "paid"
            bill_obj.save()

            if bill_act_amount >= old_spend_amount:
                bill_act_amount = round(bill_act_amount - old_spend_amount, 2)

        if bill_act_amount > 0:
            account_obj = Account.objects.get(id=int(bill_account_id))
            remaining_amount = round(
                float(account_obj.available_balance) - bill_act_amount, 2
            )
            tag_obj, _ = Tag.objects.get_or_create(
                user=user_name, name="Incomes")
            transaction_date = datetime.datetime.today().date()
            save_transaction(
                user_name,
                sub_cat_obj.name,
                bill_act_amount,
                remaining_amount,
                transaction_date,
                sub_cat_obj,
                account_obj,
                tag_obj,
                True,
                True,
                bill_obj,
            )
            account_obj.available_balance = remaining_amount
            account_obj.transaction_count += 1
            account_obj.save()
        return JsonResponse({"status": "true"})
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
    error = ""
    user = request.user
    if form.is_valid():
        label = form.cleaned_data.get("label").title()
        amount = form.cleaned_data.get("amount")
        bill_date = form.cleaned_data.get("date")
        frequency = form.cleaned_data.get("frequency")
        account_name = request.POST["account_name"]
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
            auto_bill = request.POST["auto_bill"]
            bill_obj.frequency = frequency
            bill_obj.auto_bill = True
        # To-Do  Remove bare except
        except:
            bill_obj.auto_bill = False

        try:
            auto_pay = request.POST["auto_pay"]
            bill_obj.auto_pay = True
        except:
            bill_obj.auto_pay = False

        if label != bill_obj.label:
            check_bill_obj = Bill.objects.filter(
                user=request.user, label=label, account=account_obj
            )
            if check_bill_obj:
                error = "Bill Already Exit!!"
            else:
                bill_obj.save()
                return redirect(f"/bill_detail/{pk}")
        else:
            bill_date = datetime.datetime.strptime(
                str(bill_date), DateFormats.YYYY_MM_DD.value
            ).date()
            bill_date = datetime.datetime.strptime(
                str(bill_date), DateFormats.YYYY_MM_DD.value
            ).date()
            if bill_date != bill_obj.date:
                check_bill_obj = Bill.objects.filter(
                    user=request.user, label=label, account=account_obj, date=bill_date
                )
                if check_bill_obj:
                    error = "Bill Already Exit!!"
                else:
                    bill_obj.save()
                    return redirect(f"/bill_detail/{pk}")
            else:
                bill_obj.save()
                return redirect(f"/bill_detail/{pk}")

    bill_category = SubCategory.objects.filter(
        category__name=CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value, category__user=user
    )
    account_qs = Account.objects.filter(
        user=user, account_type__in=AccountTypes.list())
    bill_frequency = BudgetPeriods.list()
    context = {
        "form": form,
        "error": error,
        "bill_data": bill_obj,
        "currency_dict": CURRENCY_DICT,
        "bill_category": bill_category,
        "account_qs": account_qs,
        "bill_frequency": bill_frequency,
    }
    return render(request, "bill/bill_update.html", context=context)


@login_required(login_url="/login")
def bill_delete(request, pk):
    bill_obj = BillDetail.objects.get(pk=pk)
    user_name = request.user
    transaction_details = Transaction.objects.filter(
        user=user_name, bill__bill_details=bill_obj
    )
    for data in transaction_details:
        delete_transaction_details(data.pk, user_name, "bill_delete")

    bill_obj.delete()
    return JsonResponse({"status": "Successfully", "path": "/bill_list/"})


@login_required(login_url="/login")
def bill_automatic_amount(request):
    bill_id = request.POST["bill_id"]
    bill_obj = Bill.objects.get(pk=bill_id)
    return JsonResponse({"bill_amount": bill_obj.remaining_amount})


@login_required(login_url="/login")
def unpaid_bills(request):
    user = request.user
    category_id = int(request.POST["category_id"])
    category_obj = Category.objects.get(user=user, pk=category_id)
    if category_obj.name != CategoryTypes.BILLS_AND_SUBSCRIPTIONS.value:
        return JsonResponse({"status": "error"})
    subcategory_name = request.POST["sub_category"].strip()
    bill_qs = Bill.objects.filter(
        user=user, label=subcategory_name, status="unpaid")
    unpaid_bill_dict = {}
    amount_dict = {}
    for data in bill_qs:
        unpaid_bill_dict[data.pk] = data.date
        amount_dict[data.pk] = data.remaining_amount
    return JsonResponse(
        {
            "status": "true",
            "unpaid_bill_dict": unpaid_bill_dict,
            "amount_dict": json.dumps(amount_dict),
        }
    )


def make_mortgage_data(data, total_month, mortgage_date):
    last_date = mortgage_date + relativedelta(months=+total_month)
    last_month = f"{calendar.month_name[last_date.month]} {last_date.year}"
    balance_data = []
    principle_data = []
    interest_data = []
    mortgage_date_data = [
        str(mortgage_date + relativedelta(months=+x)) for x in range(total_month)
    ]

    for value in data:
        balance_data.append(value["initial_balance"])
        principle_data.append(abs(value["principle"]))
        interest_data.append(abs(value["interest"]))

    mortgage_graph_data = [
        {"name": "Balance", "data": balance_data},
        {"name": "Principle", "data": principle_data},
        {"name": "Interest", "data": interest_data},
    ]

    return MORTGAGE_KEYS, mortgage_graph_data, last_month, mortgage_date_data


@login_required(login_url="/login")
def mortgagecalculator(request):
    form = MortgageForm(request.POST or None)
    if form.is_valid():
        initial_amount = form.cleaned_data.get("amount")
        down_payment = form.cleaned_data.get("down_payment")
        amount = float(initial_amount) - float(down_payment)
        interest = form.cleaned_data.get("interest")
        tenure = form.cleaned_data.get("tenure")
        mortgage_date = form.cleaned_data.get("mortgage_date")
        table = calculator(amount, interest, tenure)
        total_payment = abs(table["principle"].sum() + table["interest"].sum())
        total_month = tenure * 12
        json_records = table.reset_index().to_json(orient="records")
        data = json.loads(json_records)
        print(data[0]["initial_balance"])
        monthly_payment = abs(data[0]["principle"] + data[0]["interest"])
        mortgage_key, mortgage_graph_data, last_month, mortgage_date_data = (
            make_mortgage_data(data, total_month, mortgage_date)
        )
        context = {
            "form": form,
            "data": data,
            "monthly_payment": monthly_payment,
            "last_month": last_month,
            "days": total_month,
            "total_payment": total_payment,
            "mortgage_key": mortgage_key,
            "initial_amount": initial_amount,
            "mortgage_key_dumbs": json.dumps(mortgage_key),
            "mortgage_graph_data": mortgage_graph_data,
            "mortgage_date_data": mortgage_date_data,
            "page": "mortgagecalculator_list",
            "tour_api": Tour_APIs["mortgage_calculator_page"],
            "tour_api": Tour_APIs["mortgage_calculator_page"],
        }
        return render(request, "mortgagecalculator_add.html", context)

    context = {
        "form": form,
        "page": "mortgagecalculator_list",
        "tour_api": Tour_APIs["mortgage_calculator_page"],
    }
    return render(request, "mortgagecalculator_add.html", context)


# FUTURE NET WORTH CALCULATOR


@login_required(login_url="/login")
def future_net_worth_calculator(request):
    if request.method == "POST":
        home_value = check_float(request.POST["home_value"])
        vehicle_value = check_float(request.POST["vehicle_value"])
        cash_savings = check_float(request.POST["cash_savings"])
        open_taxable_savings = check_float(
            request.POST["open_taxable_savings"])
        non_taxable_savings = check_float(request.POST["non_taxable_savings"])
        tax_deferred_savings = check_float(
            request.POST["tax_deferred_savings"])
        other_asset_value = check_float(request.POST["other_asset_value"])
        home_mortgage_owing = check_float(request.POST["home_mortgage_owing"])
        vehicle_loan_owing = check_float(request.POST["vehicle_loan_owing"])
        s_i_loan_owing = check_float(request.POST["s_i_loan_owing"])
        credit_card_owing = check_float(request.POST["credit_card_owing"])
        student_loan_owing = check_float(request.POST["student_loan_owing"])
        other_loan_owing = check_float(request.POST["other_loan_owing"])
        asset_rate = check_float(request.POST["asset_rate"])
        income = check_float(request.POST["taxable_income"])
        age = int(request.POST["age"])
        currency = request.POST["currency"]
        other_liab = others_costs_data(request.POST.getlist("other_liab"))
        other_cost = others_costs_data(request.POST.getlist("other_cost"))

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
        currency = "$"

    future_list = []
    total_worth = age * income / 10
    total_asset = (
        home_value
        + vehicle_value
        + cash_savings
        + open_taxable_savings
        + non_taxable_savings
        + tax_deferred_savings
        + other_asset_value
    )
    total_debt = (
        home_mortgage_owing
        + vehicle_loan_owing
        + s_i_loan_owing
        + credit_card_owing
        + student_loan_owing
        + other_loan_owing
    )
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

    categories_series = [{"name": "Net Worth", "data": future_list}]
    context = {
        "current_net_worth": current_net_worth,
        "total_asset": total_asset,
        "total_debt": total_debt,
        "age": age,
        "income": income,
        "total_worth": total_worth,
        "currency_dict": CURRENCY_DICT,
        "currency": currency,
        "home_value": home_value,
        "vehicle_value": vehicle_value,
        "cash_savings": cash_savings,
        "open_taxable_savings": open_taxable_savings,
        "non_taxable_savings": non_taxable_savings,
        "tax_deferred_savings": tax_deferred_savings,
        "other_asset_value": other_asset_value,
        "home_mortgage_owing": home_mortgage_owing,
        "vehicle_loan_owing": vehicle_loan_owing,
        "s_i_loan_owing": s_i_loan_owing,
        "credit_card_owing": credit_card_owing,
        "student_loan_owing": student_loan_owing,
        "other_loan_owing": other_loan_owing,
        "other_asset": other_cost,
        "other_liability": other_liab,
        "taxable_income": income,
        "asset_rate": asset_rate,
        "categories_name": YEAR_LABELS,
        "categories_series": categories_series,
    }

    return render(request, "future_net_worth.html", context=context)


# Rental Property Model Views


class RentalPropertyList(LoginRequiredMixin, ListView):
    model = RentalPropertyModel
    template_name = "properties/list_property.html"

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        data = super(RentalPropertyList, self).get_context_data(**kwargs)
        user_name = self.request.user
        rental_property_data = RentalPropertyModel.objects.filter(
            user=user_name)
        property_data = Property.objects.filter(user=user_name)
        account_obj = Account.objects.filter(
            user=user_name, liability_type="Mortgage")
        property_dict = {}
        liability_dict = {}
        for obj in property_data:
            property_dict[obj.property_name] = obj.id

        for obj in account_obj:
            liability_dict[obj.name] = obj.id

        data["property_data"] = property_dict
        data["liability_data"] = liability_dict
        data["rental_property_data"] = rental_property_data
        return data


@login_required(login_url="/login")
def rental_property_details(request, pk):
    try:
        user_name = request.user
        property_obj = RentalPropertyModel.objects.get(user=user_name, pk=pk)
        down_payment_value = (
            float(property_obj.purchase_price_detail.selected_price)
            * float(property_obj.purchase_price_detail.down_payment)
        ) / 100
        selected_price = float(
            property_obj.purchase_price_detail.selected_price)
        amount = (
            float(property_obj.purchase_price_detail.selected_price)
            - down_payment_value
        )
        interest = float(property_obj.mortgage_detail.interest_rate)
        currency_name = property_obj.currency
        mortgage_year = float(property_obj.mortgage_detail.amortization_year)
        other_cost_dict = ast.literal_eval(
            property_obj.closing_cost_detail.others_cost
        )[0]
        total_investement = float(
            property_obj.closing_cost_detail.total_investment)
        table = calculator(amount, interest, mortgage_year)
        total_payment = abs(table["principle"].sum() + table["interest"].sum())
        total_month = int(mortgage_year * 12)
        json_records = table.reset_index().to_json(orient="records")
        data = json.loads(json_records)
        mortgage_date = property_obj.mortgage_detail.start_date
        mortgage_key, mortgage_graph_data, last_month, mortgage_date_data = (
            make_mortgage_data(data, total_month, mortgage_date)
        )
        monthly_payment = round(data[0]["principle"] + data[0]["interest"], 2)
        for key in other_cost_dict:
            other_cost_dict[key] = f"{currency_name}{other_cost_dict[key]}"
        other_cost_dict["Total Investment Required"] = (
            f"{currency_name}{total_investement}"
        )
        other_cost_dict["Interest Rate Financed at"] = f"{interest}%"
        other_cost_dict["Monthly Mortgage Payment (Principle & Interest)"] = (
            f"{currency_name}{monthly_payment}"
        )

        investment_data = {
            "Property Address": property_obj.name,
            "Property Purchase Price": f"{currency_name}{selected_price}",
            "Down Payment": f"{currency_name}{down_payment_value}",
            "Land Transfer Tax": f"{currency_name}{property_obj.closing_cost_detail.transfer_tax}",
            "Legal Fees": f"{currency_name}{property_obj.closing_cost_detail.legal_fee}",
            "Title Insurance": f"{currency_name}{property_obj.closing_cost_detail.title_insurance}",
            "Home Inspection ": f"{currency_name}{property_obj.closing_cost_detail.inspection}",
            "Appraisal Fee": f"{currency_name}{property_obj.closing_cost_detail.appraisal_fee}",
            "Purchase of Appliances": f"{currency_name}{property_obj.closing_cost_detail.appliances}",
            "Renovation Cost": f"{currency_name}{property_obj.closing_cost_detail.renovation_cost}",
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
        rent_increase_assumption = float(
            property_obj.monthly_revenue.rent_increase_assumption
        )
        interest_appreciation_assumption = float(
            property_obj.monthly_expenses.appreciation_assumption
        )
        appreciation_assumption_value = (
            selected_price * interest_appreciation_assumption
        ) / 100
        all_investment = total_investement + \
            (selected_price - down_payment_value)
        unit_1_value = float(property_obj.monthly_revenue.unit_1) * 12
        property_tax = float(property_obj.monthly_expenses.property_tax) * 12
        insurance = float(property_obj.monthly_expenses.insurance) * 12
        maintenance = float(property_obj.monthly_expenses.maintenance) * 12
        water = float(property_obj.monthly_expenses.water) * 12
        gas = float(property_obj.monthly_expenses.gas) * 12
        electricity = float(property_obj.monthly_expenses.electricity) * 12
        water_heater_rental = (
            float(property_obj.monthly_expenses.water_heater_rental) * 12
        )
        management_fee = float(
            property_obj.monthly_expenses.management_fee) * 12
        vacancy = float(property_obj.monthly_expenses.vacancy) * 12
        capital_expenditure = (
            float(property_obj.monthly_expenses.capital_expenditure) * 12
        )
        total_expense = float(
            property_obj.monthly_expenses.total_expenses) * 12
        inflation_assumption = float(
            property_obj.monthly_expenses.inflation_assumption)

        other_unit_dict = make_others_dict(
            ast.literal_eval(
                property_obj.monthly_revenue.others_revenue_cost)[0]
        )
        other_utility_dict = make_others_dict(
            ast.literal_eval(property_obj.monthly_expenses.other_utilities)[0]
        )
        other_expense_dict = make_others_dict(
            ast.literal_eval(property_obj.monthly_expenses.other_expenses)[0]
        )
        investors_dict = ast.literal_eval(property_obj.investor_details)[0]
        total_investor_contributions = sum(investors_dict.values())
        excess_short_fall = total_investor_contributions - total_investement
        debt_financing = amount
        total_financing = total_investor_contributions + amount

        for key, units in investors_dict.items():
            investor_contribution = check_zero_division(
                float(units), total_investor_contributions
            )
            investor_contribution = round(investor_contribution * 100, 2)
            annual_cash_flow_dict_investors[key] = [investor_contribution]
            net_operating_income_dict_investors[key] = [investor_contribution]
            roi_dict_investors[key] = [investor_contribution]
            roi_with_appreciation_dict_investors[key] = [investor_contribution]
            investors_dict[key] = [
                f"{currency_name}{units}",
                f"{investor_contribution}%",
            ]

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
            water_heater_rental_increase = (
                water_heater_rental * inflation_assumption / 100
            )
            management_fee_increase = management_fee * inflation_assumption / 100
            vacancy_increase = vacancy * inflation_assumption / 100
            capital_expenditure_increase = (
                capital_expenditure * inflation_assumption / 100
            )

            appreciation_assumption_increase = (
                appreciation_assumption_value * interest_appreciation_assumption
            ) / 100
            unit_1_value_increase = unit_1_value * rent_increase_assumption / 100
            mortgage_principle = 0
            mortgage_interest = 0
            for payment in data[start_index:end_index]:
                mortgage_principle += abs(payment["principle"])
                mortgage_interest += abs(payment["interest"])

            other_units_dict = make_other_data(
                other_unit_dict, year, mortgage_year, rent_increase_assumption
            )
            other_utilities_dict = make_other_data(
                other_utility_dict, year, mortgage_year, rent_increase_assumption
            )
            other_expenses_dict = make_other_data(
                other_expense_dict, year, mortgage_year, rent_increase_assumption
            )

            expenses_ratio = check_zero_division(total_expense, total_revenue)
            expenses_ratio = round(expenses_ratio * 100, 2)
            cash_flow_value = total_revenue - \
                total_expense - (monthly_payment * 12)
            cash_return_value = check_zero_division(
                cash_flow_value, total_investement)
            cash_return_value = cash_return_value * 100
            income_value = round(total_revenue - total_expense, 2)
            debt_value = check_zero_division(income_value, monthly_payment)
            debt_value = round((debt_value * 12), 2)
            net_income_value = round(income_value - mortgage_interest, 2)
            roi_value = round(cash_flow_value + mortgage_principle, 2)
            roi_p_value = check_zero_division(roi_value, total_investement)
            roi_p_value = round(roi_p_value * 100, 2)
            roi_with_appreciation_value = round(
                roi_value + appreciation_assumption_value, 2
            )
            roi_p_with_appreciation_value = check_zero_division(
                roi_with_appreciation_value, total_investement
            )
            roi_p_with_appreciation_value = round(
                roi_p_with_appreciation_value * 100, 2
            )
            cap_rate_value = check_zero_division(income_value, selected_price)
            cap_rate_value = round(cap_rate_value * 100, 2)
            cap_rate_include_closing_cost_value = check_zero_division(
                income_value, all_investment
            )
            cap_rate_include_closing_cost_value = round(
                cap_rate_include_closing_cost_value * 100, 2
            )

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
                investor_value = round(
                    roi_with_appreciation_value * value[0] / 100, 2)
                value.append(f"{currency_name}{investor_value}")

            total_revenue_list.append(
                f"{currency_name}{round(total_revenue, 2)}")
            operating_expenses_list.append(
                f"{currency_name}{round(total_expense, 2)}")
            cash_return_list.append(f"{round(cash_return_value, 2)}%")
            operating_expenses_ratio_list.append(f"{expenses_ratio}%")
            annual_cash_flow_list.append(
                f"{currency_name}{round(cash_flow_value, 2)}")
            net_operating_income_list.append(f"{currency_name}{income_value}")
            debt_cov_ratio_list.append(debt_value)
            appreciation_assumption_list.append(
                f"{currency_name}{round(appreciation_assumption_value, 2)}"
            )
            net_income_list.append(f"{currency_name}{net_income_value}")
            roi_list.append(f"{currency_name}{roi_value}")
            roi_p_list.append(f"{roi_p_value}%")
            roi_with_appreciation_list.append(
                f"{currency_name}{roi_with_appreciation_value}"
            )
            roi_p_with_appreciation_list.append(
                f"{roi_p_with_appreciation_value}%")
            cap_rate_list.append(f"{cap_rate_value}%")
            cap_rate_include_closing_cost_list.append(
                f"{cap_rate_include_closing_cost_value}%"
            )
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
        water_heater_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.water_heater)
        )
        all_appliances_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.all_appliances)
        )
        bathroom_fixtures_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.bathroom_fixtures)
        )
        drive_way_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.drive_way))
        furnance_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.furnance))
        air_conditioner_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.air_conditioner)
        )
        flooring_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.flooring))
        plumbing_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.plumbing))
        electrical_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.electrical)
        )
        windows_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.windows))
        paint_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.paint))
        kitchen_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.kitchen))
        structure_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.structure))
        components_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.components)
        )
        landscaping_list = make_capex_budget(
            ast.literal_eval(capex_budget_obj.landscaping)
        )
        others_budgets_dict = ast.literal_eval(
            capex_budget_obj.other_budgets)[0]
        total_replacement_costs = capex_budget_obj.total_budget_cost
        for key, value in others_budgets_dict.items():
            make_capex_budget(value)

        capex_budget_value = {
            "Roof": roof_list,
            "Water Heater": water_heater_list,
            "All Appliances": all_appliances_list,
            "Bathroom Fixtures (Showers, Vanities, Toilets etc.)": bathroom_fixtures_list,
            "Driveway/Parking Lot": drive_way_list,
            "Furnace": furnance_list,
            "Air Conditioner ": air_conditioner_list,
            "Flooring": flooring_list,
            "Plumbing": plumbing_list,
            "Electrical": electrical_list,
            "Windows": windows_list,
            "Paint": paint_list,
            "Kitchen Cabinets/Counters": kitchen_list,
            "Structure (foundation, framing)": structure_list,
            "Components (garage door, etc.)": components_list,
            "Landscaping": landscaping_list,
        }
        if others_budgets_dict:
            capex_budget_value.update(others_budgets_dict)
        # Yearly projection
        projection_value = {
            "Total Revenue": total_revenue_list,
            "Annual Cashflow": annual_cash_flow_list,
            "Cash on Cash Return (%)": cash_return_list,
            "Operating Expenses": operating_expenses_list,
            "Operating Expenses Ratio": operating_expenses_ratio_list,
            "Net Operating Income (NOI)": net_operating_income_list,
            "Debt Service Coverage Ratio": debt_cov_ratio_list,
            "Net Income (Rental Revenue Less Operating Expenses and Interest Expenses)": net_income_list,
            "Property Appreciation Assumption": appreciation_assumption_list,
            "Return On Investment % (ROI) (Assuming No Appreciation)": roi_p_list,
            "Return On Investment (ROI) (Assuming No Appreciation)": roi_list,
            "Return On Investment % (ROI) (With Appreciation Assumption)": roi_p_with_appreciation_list,
            "Return On Investment (ROI) (With Appreciation Assumption)": roi_with_appreciation_list,
            "Capitalization Rate (Cap Rate)": cap_rate_list,
            "Capitalization Rate (Including all closing costs)": cap_rate_include_closing_cost_list,
        }

        # yearly Revenues

        revenue_yearly_data = {"Unit 1": revenue_unit_1_list}
        other_unit_dict["Total Revenue"] = total_revenue_list
        revenue_yearly_data.update(other_units_dict)

        # Yearly Expenses
        expenses_yearly_data1 = {
            "Mortgage Principle": mortgage_principle_list,
            "Mortgage Interest": mortgage_interest_list,
            "Property Taxes": property_tax_list,
            "Insurance": insurance_list,
            "Regular Maintenance": maintenance_list,
            "Water": water_list,
            "Gas": gas_list,
            "Electricity": electricity_list,
            "Water Heater Rental": water_heater_rental_list,
        }
        expenses_yearly_data2 = {
            "Annual Cashflow": annual_cash_flow_list,
            "Cash on Cash Return (%)": cash_return_list,
            "Operating Expenses": operating_expenses_list,
            "Operating Expenses Ratio": operating_expenses_ratio_list,
            "Net Operating Income (NOI)": net_operating_income_list,
            "Debt Service Coverage Ratio": debt_cov_ratio_list,
            "Net Income (Rental Revenue Less Operating Expenses and Interest Expenses)": net_income_list,
        }
        expenses_yearly_data1.update(other_utilities_dict)
        expenses_yearly_data1.update(
            {
                "Capital Expenditure": capital_expenditure_list,
                "Property Management Fees": management_fee_list,
                "Vacancy": vacancy_list,
            }
        )
        expenses_yearly_data1.update(other_expenses_dict)

        # Yearly Return On Investment
        yearly_return_data = {
            "Property Appreciation Assumption": appreciation_assumption_list,
            "Return On Investment % (ROI) (Assuming No Appreciation)": roi_p_list,
            "Return On Investment (ROI) (Assuming No Appreciation)": roi_list,
            "Return On Investment % (ROI) (With Appreciation Assumption)": roi_p_with_appreciation_list,
            "Return On Investment (ROI) (With Appreciation Assumption)": roi_with_appreciation_list,
            "Capitalization Rate (Cap Rate)": cap_rate_list,
            "Capitalization Rate (Including all closing costs)": cap_rate_include_closing_cost_list,
        }

        # Stats and Graphs Data :-

        cash_on_cash_return_data = [
            {"name": "Cash on Cash Return(%)", "data": cash_return_list}
        ]
        return_on_investment_data = [
            {
                "name": "Return On Investment % (ROI) (Assuming No Appreciation)",
                "data": roi_p_list,
            },
            {
                "name": "Return On Investment % (ROI) (With Appreciation Assumption)",
                "data": roi_p_with_appreciation_list,
            },
        ]

        change_annual_cash_flow_list = [
            float(x[1:]) for x in annual_cash_flow_list]
        change_appreciation_assumption_list = [
            float(x[1:]) for x in appreciation_assumption_list
        ]
        change_mortgage_principle_list = [
            float(x) for x in mortgage_principle_list]

        debt_cov_ratio_data = [
            {"name": "Debt Service Coverage Ratio (%)",
             "data": debt_cov_ratio_list}
        ]
        return_investment_data = [
            {"name": "Annual Cashflow", "data": change_annual_cash_flow_list},
            {
                "name": "Net Operating Income(NOI)",
                "data": [x[1:] for x in net_operating_income_list],
            },
            {
                "name": "Return On Investment (ROI) (Assuming No Appreciation)",
                "data": [x[1:] for x in roi_list],
            },
            {
                "name": "Return On Investment (ROI) (With Appreciation Assumption)",
                "data": [x[1:] for x in roi_with_appreciation_list],
            },
        ]
        property_expense_data = [
            {
                "name": "Operating Expenses",
                "data": [x[1:] for x in operating_expenses_list],
            }
        ]

        stats_graph_dict = {
            "cash_on_cash_return_data": cash_on_cash_return_data,
            "return_on_investment_data": return_on_investment_data,
            "debt_cov_ratio_data": debt_cov_ratio_data,
            "return_investment_data": return_investment_data,
            "property_expense_data": property_expense_data,
        }

        total_year_return = (
            sum(change_annual_cash_flow_list)
            + sum(change_appreciation_assumption_list)
            + sum(change_mortgage_principle_list)
        )

        for key, value in investors_dict.items():
            update_value = float(value[1].replace("%", ""))
            total_year_return_dict_investors[key] = [
                value[1],
                f"{currency_name}{round(update_value * total_year_return, 2)}",
            ]

        expenses_yearly_data_dumbs = {}
        expenses_yearly_data_dumbs.update(expenses_yearly_data1)
        expenses_yearly_data_dumbs.update(expenses_yearly_data2)

        context = {
            "primary_key": pk,
            "investment_data": investment_data,
            "property_obj": property_obj,
            "projection_key": projection_key,
            "projection_value": projection_value,
            "revenue_yearly_data": revenue_yearly_data,
            "expenses_yearly_data1": expenses_yearly_data1,
            "expenses_yearly_data2": expenses_yearly_data2,
            "yearly_return_data": yearly_return_data,
            "data": data,
            "monthly_payment": monthly_payment,
            "last_month": last_month,
            "days": total_month,
            "total_payment": total_payment,
            "mortgage_key": mortgage_key,
            "mortgage_key_dumbs": json.dumps(mortgage_key),
            "mortgage_graph_data": mortgage_graph_data,
            "mortgage_date_data": mortgage_date_data,
            "total_year_return": round(total_year_return, 2),
            "annual_cash_flow_dict_investors": annual_cash_flow_dict_investors,
            "net_operating_income_dict_investors": net_operating_income_dict_investors,
            "roi_dict_investors": roi_dict_investors,
            "roi_with_appreciation_dict_investors": roi_with_appreciation_dict_investors,
            "investors_dict": investors_dict,
            "total_investor_contributions": total_investor_contributions,
            "excess_short_fall": excess_short_fall,
            "debt_financing": debt_financing,
            "total_financing": total_financing,
            "capex_budget_value": capex_budget_value,
            "total_replacement_costs": total_replacement_costs,
            "total_return_investor_dict": total_year_return_dict_investors,
            "investment_data_dumbs": json.dumps(investment_data),
            "projection_value_dumbs": json.dumps(projection_value),
            "annual_cash_flow_dict_investors_dumbs": json.dumps(
                annual_cash_flow_dict_investors
            ),
            "net_operating_income_dict_investors_dumbs": json.dumps(
                net_operating_income_dict_investors
            ),
            "total_return_investor_dict_dumbs": json.dumps(
                total_year_return_dict_investors
            ),
            "roi_dict_investors_dumbs": json.dumps(roi_dict_investors),
            "roi_with_appreciation_dict_investors_dumbs": json.dumps(
                roi_with_appreciation_dict_investors
            ),
            "cash_on_cash_return_data_dumbs": json.dumps(
                stats_graph_dict["cash_on_cash_return_data"][0]["data"]
            ),
            "return_on_investment_data_dumbs": json.dumps(return_on_investment_data),
            "debt_cov_ratio_data_dumbs": json.dumps(
                stats_graph_dict["debt_cov_ratio_data"][0]["data"]
            ),
            "return_investment_data_dumbs": json.dumps(
                stats_graph_dict["return_investment_data"]
            ),
            "property_expense_data_dumbs": json.dumps(
                stats_graph_dict["property_expense_data"][0]["data"]
            ),
            "revenue_yearly_data_dumbs": json.dumps(revenue_yearly_data),
            "expenses_yearly_data_dumbs": json.dumps(expenses_yearly_data_dumbs),
            "yearly_return_data_dumbs": json.dumps(yearly_return_data),
        }
        context.update(stats_graph_dict)

        return render(request, "properties/property_detail.html", context=context)
    except Exception as err:
        return render(request, "error.html", context={"error": "Something Went Wrong"})


def others_costs_data(other_closing_cost):
    cost_dict = dict.fromkeys(other_closing_cost[::2], 0)
    cost_index = 1
    for key in cost_dict:
        cost_dict[key] = check_float(other_closing_cost[cost_index])
        cost_index += 2

    return cost_dict


@login_required(login_url="/login")
def rental_property_add(request):
    if request.method == "POST":
        print("method called")
        try:
            property_image = request.FILES["file"]
        # To-Do  Remove bare except
        except:
            property_image = ""
        print(request.POST)
        property_name = request.POST["name_address"].title()
        currency_name = request.POST["currency_name"]
        user_name = request.user
        property_obj = RentalPropertyModel.objects.filter(
            user=user_name, name=property_name
        )
        if property_obj:
            context = {
                "currency_dict": CURRENCY_DICT,
                "error": "Property Already Exits",
            }
            return render(request, "properties/add_property.html", context=context)

        rental_obj = RentalPropertyModel()
        property_purchase_obj = PropertyPurchaseDetails()
        mortgage_obj = MortgageDetails()
        closing_cost_obj = ClosingCostDetails()
        revenue_obj = RevenuesDetails()
        expense_obj = ExpensesDetails()
        capex_budget_obj = CapexBudgetDetails()
        save_rental_property(
            request,
            rental_obj,
            property_purchase_obj,
            mortgage_obj,
            closing_cost_obj,
            revenue_obj,
            expense_obj,
            capex_budget_obj,
            property_name,
            currency_name,
            user_name,
            property_image,
        )
        return redirect("/rental_property_list/")

    else:
        upcoming_date = today_date + relativedelta(months=1, day=1)
        property_obj = {
            "mortgage_detail": {
                "start_date": str(upcoming_date),
                "amortization_year": 25,
            }
        }
        context = {
            "currency_dict": CURRENCY_DICT,
            "scenario_dict": SCENARIO_DICT,
            # Fetch the url from the request
            "action_url": request.path,
            "heading_name": "Add Rental Property",
            "heading_url": "Add Property",
            "property_url": "/rental_property_list/",
            "property_obj": property_obj,
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
        property_image = request.FILES["property_image"]
        property_name = request.POST["name_address"].title()
        currency_name = request.POST["currency_name"]
        user_name = request.user
        if rental_obj.name != property_name:
            property_obj = RentalPropertyModel.objects.filter(
                user=user_name, name=property_name
            )
            if property_obj:
                context = {
                    "currency_dict": CURRENCY_DICT,
                    "error": "Property Already Exits",
                }
                return render(request, "properties/add_property.html", context=context)

        save_rental_property(
            request,
            rental_obj,
            property_purchase_obj,
            mortgage_obj,
            closing_cost_obj,
            revenue_obj,
            expense_obj,
            capex_budget_obj,
            property_name,
            currency_name,
            user_name,
            property_image,
        )
        return redirect(f"rental_property_detail/{pk}")

    else:
        property_obj = RentalPropertyModel.objects.get(pk=pk)
        roof_obj = ast.literal_eval(property_obj.capex_budget_details.roof)
        water_heater = ast.literal_eval(
            property_obj.capex_budget_details.water_heater)
        all_appliances = ast.literal_eval(
            property_obj.capex_budget_details.all_appliances
        )
        bathroom_fixtures = ast.literal_eval(
            property_obj.capex_budget_details.bathroom_fixtures
        )
        drive_way = ast.literal_eval(
            property_obj.capex_budget_details.drive_way)
        furnance = ast.literal_eval(property_obj.capex_budget_details.furnance)
        air_conditioner = ast.literal_eval(
            property_obj.capex_budget_details.air_conditioner
        )
        flooring = ast.literal_eval(property_obj.capex_budget_details.flooring)
        plumbing = ast.literal_eval(property_obj.capex_budget_details.plumbing)
        electrical = ast.literal_eval(
            property_obj.capex_budget_details.electrical)
        windows = ast.literal_eval(property_obj.capex_budget_details.windows)
        paint = ast.literal_eval(property_obj.capex_budget_details.paint)
        kitchen = ast.literal_eval(property_obj.capex_budget_details.kitchen)
        structure = ast.literal_eval(
            property_obj.capex_budget_details.structure)
        components = ast.literal_eval(
            property_obj.capex_budget_details.components)
        landscaping = ast.literal_eval(
            property_obj.capex_budget_details.landscaping)
        others_cost = ast.literal_eval(
            property_obj.closing_cost_detail.others_cost)[0]
        others_revenue_cost = ast.literal_eval(
            property_obj.monthly_revenue.others_revenue_cost
        )[0]
        other_utilities = ast.literal_eval(
            property_obj.monthly_expenses.other_utilities
        )[0]
        other_expenses = ast.literal_eval(property_obj.monthly_expenses.other_expenses)[
            0
        ]
        investor_details = ast.literal_eval(property_obj.investor_details)[0]

        context = {
            "currency_dict": CURRENCY_DICT,
            "scenario_dict": SCENARIO_DICT,
            "property_obj": property_obj,
            "roof_obj": roof_obj,
            "water_heater": water_heater,
            "all_appliances": all_appliances,
            "bathroom_fixtures": bathroom_fixtures,
            "drive_way": drive_way,
            "furnance": furnance,
            "air_conditioner": air_conditioner,
            "flooring": flooring,
            "plumbing": plumbing,
            "electrical": electrical,
            "windows": windows,
            "paint": paint,
            "kitchen": kitchen,
            "structure": structure,
            "components": components,
            "landscaping": landscaping,
            "others_cost": others_cost,
            "others_cost_len": len(others_cost),
            "others_revenue_cost": others_revenue_cost,
            "others_revenue_cost_len": len(others_revenue_cost),
            "other_utilities": other_utilities,
            "other_utilities_len": len(other_utilities),
            "other_expenses": other_expenses,
            "other_expenses_len": len(other_expenses),
            "investor_details": investor_details,
            "investor_details_len": len(investor_details),
            "action_url": f"/rental_property_update/{pk}",
            "heading_name": "Update Rental Property",
            "heading_url": "Update Property",
            "property_url": f"/rental_property_detail/{pk}",
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
        if pageSize == "A4":
            self.pageSize = A0
        elif pageSize == "Letter":
            self.pageSize = letter
        self.width, self.height = self.pageSize

    def report(self, pdf_data_value, title, property_address, property_image, d=None):
        doc = SimpleDocTemplate(self.buffer, pagesize=self.pageSize)
        styles = getSampleStyleSheet()
        title_style = styles["Heading1"]
        title_style.alignment = TA_CENTER
        title_style.fontSize = 50
        if property_image == "None":
            data = [
                Spacer(50, 50),
                Paragraph(f"RENTAL PROPERTY INVESTMENT PROPOSAL", title_style),
                Spacer(100, 100),
                Paragraph(f"Address {property_address}", title_style),
                Spacer(300, 300),
            ]
        else:
            data = [
                Spacer(50, 50),
                Paragraph(f"RENTAL PROPERTY INVESTMENT PROPOSAL", title_style),
                Spacer(100, 100),
                Paragraph(f"Address {property_address}", title_style),
                Spacer(100, 100),
                Image(property_image, 25 * inch, 15 * inch),
                Spacer(200, 200),
            ]
        for key, values in pdf_data_value.items():
            t = Table(values)
            t.setStyle(
                TableStyle(
                    [
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                        ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.powderblue),
                        ("FONTSIZE", (0, 0), (-1, -1), title),
                    ]
                )
            )
            # create other flowables
            p = Paragraph(key, styles["Title"])
            data.append(p)
            data.append(t)
            data.append(Spacer(150, 150))
        if d:
            data.append(
                Paragraph(
                    f"INVESTMENT SUMMARY GRAPHS AND STATISTICS", title_style)
            )
            for bar_key, bar_d in d.items():
                data.append(Spacer(150, 150))
                # if bar_key == "Cash on Cash Return (%)" or bar_key == "Investment Returns":
                #     data.append(Spacer(200, 200))
                data.append(Paragraph(bar_key, styles["Title"]))
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
        if pageSize == "A4":
            self.pageSize = A4
        elif pageSize == "Letter":
            self.pageSize = letter
        self.width, self.height = self.pageSize

    def report(self, pdf_data_value, title, d=None):
        # set some characteristics for pdf document
        doc = SimpleDocTemplate(self.buffer, pagesize=self.pageSize)
        styles = getSampleStyleSheet()
        # create document
        data = [Paragraph(title, styles["Title"])]
        t = Table(pdf_data_value)
        t.setStyle(
            TableStyle(
                [
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.black),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                    ("VALIGN", (0, 0), (-1, 0), "MIDDLE"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.powderblue),
                ]
            )
        )
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
    bar.valueAxis.labels.fontName = "Helvetica"
    bar.valueAxis.labels.fontSize = 10
    bar.valueAxis.forceZero = 1
    bar.valueAxis.rangeRound = "both"
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
        legend.fontName = "Helvetica"
        legend.fontSize = 14
        legend.boxAnchor = "w"
        legend.x = 200
        legend.y = 600
        legend.dx = 16
        legend.dy = 16
        legend.alignment = "left"
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
    property_address = request.POST["property_name"]
    property_image = request.POST["property_image"]
    scheme = request.scheme
    if property_image != "None":
        property_image = f"{scheme}://{request.META['HTTP_HOST']}{property_image}"
    invest_summary_data = request.POST["invest_summary_data"]
    yearly_projection_data = request.POST["yearly_projection_data"]
    annual_cashflow_data = request.POST["annual_cashflow_data"]
    roi_with_appreciation_dict_investors_data = request.POST[
        "roi_with_appreciation_dict_investors_data"
    ]
    roi_dict_investors_data = request.POST["roi_dict_investors_data"]
    total_return_investor_data = request.POST["total_return_investor_data"]
    net_operating_income_data = request.POST["net_operating_income_data"]
    cash_on_cash_return_data = request.POST["cash_on_cash_return_data"]
    return_on_investment_data = request.POST["return_on_investment_data"]
    debt_cov_ratio_data = request.POST["debt_cov_ratio_data"]
    property_expense_data = request.POST["property_expense_data"]
    return_investment_data = request.POST["return_investment_data"]
    revenue_yearly_data = request.POST["revenue_yearly_data"]
    expenses_yearly_data = request.POST["expenses_yearly_data"]
    yearly_return_data = request.POST["yearly_return_data"]

    invest_summary_data = json.loads(invest_summary_data)
    yearly_projection_data = json.loads(yearly_projection_data)
    annual_cashflow_data = json.loads(annual_cashflow_data)
    roi_with_appreciation_dict_investors_data = json.loads(
        roi_with_appreciation_dict_investors_data
    )
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
    return_investment_data_list = return_investment_data[0]["data"]
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

    return_dict = {
        "Annual Cashflow ": annual_cashflow_data,
        "Net Operating Income (NOI)": net_operating_income_data,
        "Return on Investment (ROI) ($) (Assuming NO Appreciation)": roi_dict_investors_data,
        "Return on Investment(ROI) ($) (WITH appreciation assumption)": roi_with_appreciation_dict_investors_data,
        f"Total {len(yearly_keys)} Year Return with Appreciation Assumption": total_return_investor_data,
    }

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

    for name in return_on_investment_data[0]["data"]:
        return_on_investment_data_list1.append(float(name.replace("%", "")))

    for name in return_on_investment_data[1]["data"]:
        return_on_investment_data_list2.append(float(name.replace("%", "")))

    for name in return_investment_data[1]["data"]:
        return_investment_data_list1.append(float(name.replace("%", "")))

    for name in return_investment_data[2]["data"]:
        return_investment_data_list2.append(float(name.replace("%", "")))

    for name in return_investment_data[3]["data"]:
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

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"attachment; filename={file_name}"
    buffer = BytesIO()
    reporti = RentalPdf(buffer, "A4")
    bar_legends = [
        (PCMYKColor(46, 51, 0, 4), return_on_investment_data[0]["name"]),
        (colors.red, return_on_investment_data[1]["name"]),
    ]
    return_bar_legends = [
        (PCMYKColor(46, 51, 0, 4), return_investment_data[0]["name"]),
        (colors.red, return_investment_data[1]["name"]),
        (colors.darkgreen, return_investment_data[2]["name"]),
        (colors.yellow, return_investment_data[3]["name"]),
    ]
    cash_on_cash_bar_chart = draw_bar_chart(
        [cash_on_cash_return_data_values], bar_label, "bar"
    )
    debt_cov_ratio_bar_chart = draw_bar_chart(
        [debt_cov_ratio_data], bar_label, "bar")
    property_expense_data_bar_chart = draw_bar_chart(
        [property_expense_data], bar_label, "bar"
    )
    return_on_investment_chart = draw_bar_chart(
        [return_on_investment_data_list1, return_on_investment_data_list2],
        bar_label,
        "return-bar",
        bar_legends,
    )
    return_investment_chart = draw_bar_chart(
        [
            return_investment_data_list,
            return_investment_data_list1,
            return_investment_data_list2,
            return_investment_data_list3,
        ],
        bar_label,
        "return-bar",
        return_bar_legends,
    )

    d = {
        "Cash on Cash Return (%)": cash_on_cash_bar_chart,
        "Return on Investment": return_on_investment_chart,
        "Debt Service Coverage Ratio": debt_cov_ratio_bar_chart,
        "Investment Returns": return_investment_chart,
        "Property Operating Expenses": property_expense_data_bar_chart,
    }

    pdf_title = 14

    if len(yearly_keys) > 45:
        pdf_title = 6
    else:
        if len(yearly_keys) >= 35:
            pdf_title = 7
        if len(yearly_keys) >= 25:
            pdf_title = 10

    pdf = reporti.report(
        {
            "INVESTMENT SUMMARY": investment_data_values,
            "YEARLY PROJECTION": yearly_projection_data_values,
            "INVESTOR RETURNS SUMMARY": annual_cashflow_data_values,
            "REVENUE": revenue_yearly_data_values,
            "PROPERTY EXPENSES": expenses_yearly_data_values,
            "INVESTMENT METRICS": yearly_return_data_values,
        },
        pdf_title,
        property_address,
        property_image,
        d,
    )
    response.write(pdf)
    return response


@login_required(login_url="/login")
@csrf_exempt
def download_pdf(request):
    if request.method == "POST":
        pdf_data_key = request.POST["csv_data_key"]
        pdf_title = request.POST["pdf_title"]
        pdf_data_value = request.POST["csv_data_value"]
        file_name = request.POST["file_name"]
        pdf_data_key = json.loads(pdf_data_key)
        pdf_data_value = json.loads(pdf_data_value)
        pdf_data_value.insert(0, pdf_data_key)
        response = HttpResponse(content_type="application/pdf")
        response["Content-Disposition"] = f"attachment; filename={file_name}"
        buffer = BytesIO()
        reporti = PdfPrint(buffer, "A4")
        print("pdf_data_value--------->", pdf_data_value)
        try:
            graph_type = request.POST["graph_type"]
            print("graph_type=======>", graph_type)
            data_label = request.POST["data_label"]
            data_value = request.POST["data_value"]
            data_label = json.loads(data_label)
            data_value = json.loads(data_value)
            print("graph_data_labels====>", data_label)
            print("graph_data_values====>", data_value)

            if graph_type == "transaction-bar":
                credit_value = request.POST["credit_value"]
                debit_value = data_value
                credit_value = json.loads(credit_value)
                bar_data = [debit_value, credit_value]
                print("colors.red========>", colors.red)
                print("colors.green========>", colors.green)

                bar_legends = [(colors.red, "Debit"), (colors.green, "Credit")]
                d = draw_bar_chart(bar_data, data_label,
                                   graph_type, bar_legends)

            if graph_type == "bar":
                print("barr")
                bar_data = [data_value]
                d = draw_bar_chart(bar_data, data_label, graph_type)
                print(d)
            if graph_type == "line":
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

            if graph_type == "pie":
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
        # To-Do  Remove bare except
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

    if request.method == "POST":
        csv_data_key = request.POST["csv_data_key"]
        csv_data_value = request.POST["csv_data_value"]
        file_name = request.POST["file_name"]
        csv_data_key = json.loads(csv_data_key)
        csv_data_value = json.loads(csv_data_value)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={file_name}"
        writer = csv.writer(response)
        writer.writerow(csv_data_key)
        for data in csv_data_value:
            writer.writerow(data)
        return response


@login_required(login_url="/login")
def transaction_upload(request):
    if request.method == "POST" and request.is_ajax:
        try:
            test_file = request.FILES["csv_file"]
            df = pd.read_csv(test_file)
            for index, row in df.iterrows():
                my_transaction = Transaction()
                user_name = request.user
                my_transaction.user = user_name
                category_name = row["Categories"]
                if type(category_name) == float:
                    return JsonResponse({"status": "Category is mandatory field"})
                category_obj = Category.objects.filter(
                    user=user_name, name=category_name
                )
                if not category_obj:
                    category_obj = Category()
                    category_obj.user = user_name
                    category_obj.name = category_name
                    category_obj.save()
                else:
                    category_obj = category_obj[0]
                my_transaction.categories = category_obj
                account = row["Account"]
                transaction_amount = row["Amount"]
                out_flow = row["Type"]
                if out_flow == "Debit":
                    out_flow = "True"
                    my_transaction.out_flow = True
                else:
                    my_transaction.out_flow = False

                cleared_amount = row["Cleared"]
                if cleared_amount:
                    cleared_amount = "True"
                transaction_date = row["Date"]
                transaction_date = datetime.datetime.strptime(
                    transaction_date, DateFormats.DD_MM_YYYY.value
                )
                bill_name = row["Bill"]
                budget_name = row["Budget"]
                transaction_tags = row["Tags"]
                if cleared_amount == "True":
                    try:
                        account_obj = Account.objects.get(
                            user=user_name, name=account)
                    # To-Do  Remove bare except
                    except:
                        return JsonResponse(
                            {"status": account + " Account not Found!!"}
                        )
                    if type(bill_name) != float:
                        bill_obj = Bill.objects.filter(
                            user=user_name, label=bill_name)
                        if not bill_obj:
                            return JsonResponse(
                                {"status": bill_name + " Bill Not Found!!"}
                            )
                        else:
                            bill_obj = bill_obj[0]
                    else:
                        bill_obj = False

                    if type(budget_name) != float:
                        budget_obj = Budget.objects.filter(
                            user=user_name, name=budget_name
                        )
                        if not budget_obj:
                            return JsonResponse(
                                {"status": budget_name + " Budget Not Found!!"}
                            )
                        else:
                            budget_obj = budget_obj[0]
                        print("budget_obj", budget_obj)
                    else:
                        budget_obj = False

                    if out_flow == "True":
                        account_obj.available_balance = round(
                            float(account_obj.available_balance) -
                            transaction_amount, 2
                        )
                    else:
                        account_obj.available_balance = round(
                            float(account_obj.available_balance) +
                            transaction_amount, 2
                        )

                    if bill_obj:
                        bill_amount = round(
                            float(bill_obj.remaining_amount), 2)
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
                            budget_obj.budget_spent = round(
                                float(budget_obj.budget_spent) +
                                transaction_amount, 2
                            )
                        else:
                            budget_obj.amount = round(
                                float(budget_obj.amount) +
                                transaction_amount, 2
                            )
                        budget_obj.save()
                        my_transaction.budgets = budget_obj
                    account_obj.transaction_count += 1
                    account_obj.save()
                    my_transaction.remaining_amount = account_obj.available_balance

                my_transaction.transaction_date = transaction_date
                my_transaction.payee = row["Payee"]
                my_transaction.account = account_obj
                my_transaction.amount = row["Amount"]
                my_transaction.tags = transaction_tags
                my_transaction.cleared = cleared_amount
                my_transaction.save()
            return JsonResponse({"status": "File Uploaded"})
        except:
            return JsonResponse(
                {"status": "Uploading Failed!! Please Check File Format"}
            )


@login_required(login_url="/login")
def stock_analysis(request):
    url = f"{stock_app_url}/api/portfolio/list/"
    portfolio_response = requests.get(
        url, data={"user_name": request.user.username}, timeout=500
    )
    portfolio_list = portfolio_response.json()

    if request.method == "POST":
        p_name = request.POST["p_name"]
    else:
        p_name = portfolio_list[0]

    my_portfolio_url = f"{stock_app_url}/api/my_portfolio/list/"
    url_response = requests.post(
        my_portfolio_url,
        data={"user_name": request.user.username, "p_name": p_name},
        timeout=500,
    )
    my_portfolio_context = url_response.json()
    my_portfolio_context["portfolio_list"] = portfolio_list
    return render(request, "stock_analysis.html", context=my_portfolio_context)


@login_required(login_url="/login")
def stock_holdings(request):
    url = f"{stock_app_url}/api/portfolio/list/"
    print("url========>", url)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0"
    }
    portfolio_response = requests.get(
        url, headers=headers, data={"user_name": request.user.username}, timeout=500
    )
    portfolio_dict = portfolio_response.json()
    if request.method == "POST":
        my_portfolio_name = request.POST["portfolio_name"]
    else:
        my_portfolio_name = portfolio_dict["portfolio_list"][0]
    my_portfolio_url = f"{stock_app_url}/api/my_portfolio/list/"
    print("url========>", my_portfolio_url)
    url_response = requests.post(
        my_portfolio_url,
        headers=headers,
        data={"user_name": request.user.username, "p_name": my_portfolio_name},
        timeout=500,
    )
    my_portfolio_context = url_response.json()
    portfolio_dict.update({"my_portfolio_name": my_portfolio_name})
    portfolio_dict.update(my_portfolio_context)
    check_networth = StockHoldings.objects.filter(
        user=request.user, port_id=portfolio_dict["portfolio_id"]
    )
    portfolio_dict.update({"check_networth": check_networth})
    print(portfolio_dict)
    return render(request, "stock_analysis.html", context=portfolio_dict)


@login_required(login_url="/login")
def add_port_in_networth(request):
    try:
        if request.method == "POST" and request.is_ajax():
            portfolio_id = int(request.POST["portfolio_id"])
            portfolio_name = request.POST["portfolio_name"]
            portfolio_value = request.POST["portfolio_value"]
            portfolio_currency = request.POST["portfolio_currency"]
            method_name = request.POST["method_name"]
            if method_name == "delete_port":
                StockHoldings.objects.get(
                    user=request.user, port_id=portfolio_id
                ).delete()
                return JsonResponse({"status": "delete"})
            else:
                end_date = today_date + datetime.timedelta(hours=2)
                StockHoldings.objects.create(
                    user=request.user,
                    port_id=portfolio_id,
                    name=portfolio_name,
                    value=portfolio_value,
                    end_at=end_date,
                    currency=PORTFOLIO_CURRENCY[portfolio_currency],
                )
                return JsonResponse({"status": "true"})
    # To-Do  Remove bare except
    except:
        return JsonResponse({"status": "false"})


# Income views
# @login_required(login_url="/login")
# def income_add(request):
#     error = False
#     user = request.user
#     if request.method == 'POST':
#         sub_category_name = request.POST['sub_category_name'].title()
#         account_name = request.POST['account_name']
#         income_amount = request.POST['amount']
#         income_date = request.POST['income_date']
#         frequency = request.POST['frequency']
#         auto_income = request.POST.get('auto_income', False)
#         auto_credit = request.POST.get('auto_credit', False)
#         if auto_income:
#             auto_income = True
#         if auto_credit:
#             auto_credit = True
#
#         subcategory_qs = SubCategory.objects.filter(category__user=user, category__name=CategoryTypes.INCOME.value,
#                                                     name=sub_category_name)
#         if not subcategory_qs:
#             sub_category = SubCategory.objects.create(category=Category.objects.get(user=user, name=CategoryTypes.INCOME.value),
#                                                       name=sub_category_name)
#         else:
#             sub_category = subcategory_qs[0]
#
#         income_qs = Income.objects.filter(user=user, sub_category=sub_category)
#         if income_qs:
#             if income_qs[0].auto_bill:
#                 error = 'Income Already Exit!!'
#             else:
#                 pass
#         else:
#             account = Account.objects.get(user=user, name=account_name)
#             created_date = datetime.datetime.strptime(income_date, '%Y-%m-%d')
#             save_income(user, sub_category, account, income_amount, income_date, auto_income, frequency, auto_credit,
#                         created_date, "True")
#             if not auto_income:
#                 income = Income.objects.get(user=user, sub_category=sub_category)
#                 income_detail_obj = save_income_details(account, income_amount, income, False, income_date)
#                 if auto_credit:
#                     account_balance = float(account.available_balance)
#                     remaining_amount = round(account_balance + income_amount, 2)
#                     tag_obj, _ = Tag.objects.get_or_create(user=income.user, name="Incomes")
#                     save_transaction(income.user, sub_category.name, income_amount, remaining_amount, income_date,
#                                      sub_category,
#                                      account,
#                                      tag_obj, False, True)
#                     account.available_balance = remaining_amount
#                     account.transaction_count += 1
#                     account.save()
#                     income_detail_obj.credited = True
#                     income_detail_obj.save()
#             create_income_request()
#             return redirect('/income_list/')
#     income_category = SubCategory.objects.filter(category__name=CategoryTypes.INCOME.value, category__user=user)
#     account_qs = Account.objects.filter(user=user, account_type__in=AccountTypes.list())
#     frequency = BudgetPeriods.list()
#     context = {
#         'error': error,
#         'account_qs': account_qs,
#         'income_category': income_category,
#         'frequency': frequency
#     }
#     return render(request, "income/income_add.html", context=context)


# @login_required(login_url="/login")
# def income_update(request, pk):
#     error = False
#     user = request.user
#     income_obj = Income.objects.get(pk=pk)
#     if request.method == 'POST':
#         sub_category_name = request.POST['sub_category_name'].title()
#         account_name = request.POST['account_name']
#         income_amount = request.POST['amount']
#         income_date = request.POST['income_date']
#         frequency = request.POST['frequency']
#         auto_income = request.POST.get('auto_income', False)
#         auto_credit = request.POST.get('auto_credit', False)
#         if auto_income:
#             auto_income = True
#         if auto_credit:
#             auto_credit = True
#         account = Account.objects.get(user=user, name=account_name)
#         income_obj.account = account
#         income_obj.income_amount = income_amount
#         income_obj.income_date = income_date
#         income_obj.auto_income = auto_income
#         income_obj.frequency = frequency
#         income_obj.auto_credit = auto_credit
#
#         if income_obj.sub_category.name != sub_category_name:
#             subcategory_qs = SubCategory.objects.filter(category__user=user, category__name=CategoryTypes.INCOME.value,
#                                                         name=sub_category_name)
#             if not subcategory_qs:
#                 sub_category = SubCategory.objects.create(category=Category.objects.get(user=user, name=CategoryTypes.INCOME.value),
#                                                           name=sub_category_name)
#             else:
#                 sub_category = subcategory_qs[0]
#             income_qs = Income.objects.filter(user=user, sub_category=sub_category)
#             if income_qs:
#                 error = 'Income Already Exit!!'
#             else:
#                 Transaction.objects.filter(user=request.user, categories=income_obj.sub_category).update(
#                     categories=sub_category)
#                 income_obj.sub_category = sub_category
#                 income_obj.save()
#                 return redirect(f"/income_details/{pk}")
#         else:
#             income_obj.save()
#             return redirect(f"/income_details/{pk}")
#
#     income_category = SubCategory.objects.filter(category__name=CategoryTypes.INCOME.value, category__user=user)
#     account_qs = Account.objects.filter(user=user, account_type__in=AccountTypes.list())
#     frequency = BudgetPeriods.list()
#     context = {
#         'error': error,
#         'account_qs': account_qs,
#         'income_category': income_category,
#         'frequency': frequency,
#         'income_data': income_obj,
#         'income_date': income_obj.income_date.strftime('%Y-%m-%d'),
#     }
#     return render(request, "income/income_update.html", context=context)


# @login_required(login_url="/login")
# def income_list(request):
#     income_data = Income.objects.filter(user=request.user)
#     context = {'income_data': income_data}
#     return render(request, "income/income_list.html", context=context)


# def income_details(request, pk):
#     income_obj = Income.objects.get(pk=pk)
#     income_qs = IncomeDetail.objects.filter(income=income_obj).order_by('-income_date')
#     transaction_data = Transaction.objects.filter(user=request.user, categories=income_obj.sub_category).order_by(
#         '-transaction_date')
#     context = {'income_data': income_obj, 'income_list': income_qs, 'transaction_data': transaction_data}
#     return render(request, "income/income_details.html", context=context)


# @login_required(login_url="/login")
# def income_delete(request, pk):
#     income_obj = Income.objects.get(pk=pk)
#     user_name = request.user
#     transaction_details = Transaction.objects.filter(user=user_name, categories=income_obj.sub_category)
#     for data in transaction_details:
#         delete_transaction_details(data.pk, user_name)
#     income_obj.delete()
#     return JsonResponse({"status": "Successfully", "path": "/income_list/"})


# def income_edit(request, pk):
#     income_obj = IncomeDetail.objects.get(pk=pk)
#     if request.method == 'POST':
#         new_amount = round(float(request.POST['amount']), 2)
#         income_date = request.POST['income_date']
#         credited = request.POST.get('credited', False)
#         old_amount = float(income_obj.income_amount)
#         account = income_obj.income.account
#         if credited:
#             credited = True
#         income_obj.income_date = income_date
#         if income_obj.credited is True and credited is True:
#             if old_amount > new_amount:
#                 remaining_amount = old_amount - new_amount
#                 account.available_balance = round(float(account.available_balance) - remaining_amount, 2)
#             if old_amount < new_amount:
#                 remaining_amount = new_amount - old_amount
#                 account.available_balance = round(float(account.available_balance) + remaining_amount, 2)
#             Transaction.objects.filter(user=income_obj.income.user, transaction_date=income_obj.income_date,
#                                        categories=income_obj.income.sub_category).update(amount=new_amount,
#                                                                                          transaction_date=income_date)
#             account.save()
#
#         if income_obj.credited is True and credited is False:
#             account.available_balance = round(float(account.available_balance) - old_amount, 2)
#             account.save()
#             Transaction.objects.filter(user=income_obj.income.user, transaction_date=income_obj.income_date,
#                                        categories=income_obj.income.sub_category).delete()
#             account.transaction_count -= 1
#
#         if income_obj.credited is False and credited is True:
#             account.available_balance = round(float(account.available_balance) + new_amount, 2)
#             tag_obj, _ = Tag.objects.get_or_create(user=income_obj.income.user, name="Incomes")
#             save_transaction(income_obj.income.user, income_obj.income.sub_category.name, new_amount,
#                              account.available_balance,
#                              income_date, income_obj.income.sub_category, account, tag_obj, False, True)
#             account.transaction_count += 1
#             account.save()
#         income_obj.income_amount = new_amount
#         income_obj.credited = credited
#         income_obj.save()
#
#         return redirect(f"/income_details/{income_obj.income.id}")
#
#     return render(request, "income/income_edit.html",
#                   {'income_data': income_obj, 'income_date': income_obj.income_date.strftime('%Y-%m-%d')})


# @login_required(login_url="/login")
# def income_date_delete(request, pk):
#     income_obj = IncomeDetail.objects.get(pk=pk)
#     user_name = income_obj.income.user
#     if income_obj.credited is True:
#         transaction_details = Transaction.objects.filter(user=user_name, transaction_date=income_obj.income_date,
#                                                          categories=income_obj.income.sub_category)
#         for data in transaction_details:
#             delete_transaction_details(data.pk, user_name)
#     income_obj.delete()
#     return JsonResponse({"status": "Successfully", "path": f"/income_details/{income_obj.income.id}"})


# @login_required(login_url="/login")
# def income_uncredited_list(request):
#     print(request.POST)
#     category_id = int(request.POST['category_id'])
#     category_obj = Category.objects.get(pk=category_id)
#     subcategory_name = request.POST['sub_category'].strip()
#     user = request.user
#     income_qs = IncomeDetail.objects.filter(income__user=user, income__sub_category__name=subcategory_name,
#                                             credited=False)
#     uncredited_income_dict = {}
#     amount_dict = {}
#     for data in income_qs:
#         uncredited_income_dict[data.pk] = data.income_date
#         amount_dict[data.pk] = data.income_amount
#
#     return JsonResponse(
#         {"status": "true", "income_dict": uncredited_income_dict, "amount_dict": json.dumps(amount_dict)})


# EXPENSES ADD
def expense_save(request, user_name, expenses_obj):
    category = request.POST["category"]
    name = request.POST["name"]
    amount = request.POST["amount"]
    month = request.POST["start_month"]
    currency = request.POST["currency"]
    category_data = Category.objects.get(user=user_name, name=category)
    month = datetime.datetime.strptime(month, DateFormats.YYYY_MM.value).date()
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
    if request.method == "POST":
        expense_save(request, user_name, None)
        if "add_other" in request.POST:
            return redirect("/expenses_add/")
        else:
            return redirect("/budget_list/")
    else:
        category_data = Category.objects.filter(user=user_name)
        current = datetime.datetime.today()
        current_month = datetime.datetime.strftime(
            current, DateFormats.YYYY_MM.value)
        context = {"current_month": current_month,
                   "category_data": category_data}
    return render(request, "expenses/expenses_add.html", context=context)


# EXPENSES UPDATE


@login_required(login_url="/login")
def expenses_update(request, pk):
    user_name = request.user
    expense_obj = Expenses.objects.get(pk=pk)
    print()
    if request.method == "POST":
        expense_save(request, user_name, expense_obj)
        return redirect("/budget_list/")
    else:
        category_data = Category.objects.filter(user=user_name)
        current_month = datetime.datetime.strftime(
            expense_obj.month, DateFormats.YYYY_MM.value
        )
        context = {
            "expense_obj": expense_obj,
            "category_data": category_data,
            "current_month": current_month,
            "currency_data": CURRENCY_DICT,
        }
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
        electric_value = "off"

    result_dict[result_type][result_name] = electric_value


def process_image(request):
    if request.method == "POST":
        # -------------- Property Details ---------------------- #
        try:
            property_image = request.FILES["property_image"]
        # To-Do  Remove bare except
        except:
            property_image = ""

        property_name = request.POST["property_name"]
        address_line1 = request.POST["address_line1"]
        address_line2 = request.POST["address_line2"]
        postcode = request.POST["postcode"]
        city = request.POST["city"]
        state = request.POST["state"]
        country = request.POST["country"]
        property_type = request.POST["property_type"]
        unit_name = request.POST.getlist("unit_name")
        bed_room_quantity = request.POST.getlist("bed_room_quantity")
        bath_room_quantity = request.POST.getlist("bath_room_quantity")
        square_feet = request.POST.getlist("square_feet")

        unit_details = []
        for i in range(len(unit_name)):
            unit_dict = {
                "name": unit_name[i],
                "details": {
                    "bed_room": bed_room_quantity[i],
                    "bath_room": bath_room_quantity[i],
                    "square_feet": square_feet[i],
                    "rent_includes": {},
                    "Amenities": {},
                },
            }
            electricity_check = request.POST.getlist(
                f"electricity_check{i}", [])
            gas_check = request.POST.getlist(f"gas_check{i}", [])
            water_check = request.POST.getlist(f"water_check{i}", [])
            int_cable_check = request.POST.getlist(f"int_cable_check{i}", [])
            ac_check = request.POST.getlist(f"ac_check{i}", [])
            pool_check = request.POST.getlist(f"pool_check{i}", [])
            pets_check = request.POST.getlist(f"pets_check{i}", [])
            furnished_check = request.POST.getlist(f"furnished_check{i}", [])
            balcony_check = request.POST.getlist(f"balcony_check{i}", [])
            hardwood_check = request.POST.getlist(f"hardwood_check{i}", [])
            wheel_check = request.POST.getlist(f"wheel_check{i}", [])
            parking_check = request.POST.getlist(f"parking_check{i}", [])

            add_checkbox_value(
                electricity_check,
                unit_dict["details"],
                "rent_includes",
                "electricity_check",
            )
            add_checkbox_value(
                gas_check, unit_dict["details"], "rent_includes", "gas_check"
            )
            add_checkbox_value(
                water_check, unit_dict["details"], "rent_includes", "water_check"
            )
            add_checkbox_value(
                int_cable_check,
                unit_dict["details"],
                "rent_includes",
                "int_cable_check",
            )
            add_checkbox_value(
                ac_check, unit_dict["details"], "Amenities", "ac_check")
            add_checkbox_value(
                pool_check, unit_dict["details"], "Amenities", "pool_check"
            )
            add_checkbox_value(
                pets_check, unit_dict["details"], "Amenities", "pets_check"
            )
            add_checkbox_value(
                furnished_check, unit_dict["details"], "Amenities", "furnished_check"
            )
            add_checkbox_value(
                balcony_check, unit_dict["details"], "Amenities", "balcony_check"
            )
            add_checkbox_value(
                hardwood_check, unit_dict["details"], "Amenities", "hardwood_check"
            )
            add_checkbox_value(
                wheel_check, unit_dict["details"], "Amenities", "wheel_check"
            )
            add_checkbox_value(
                parking_check, unit_dict["details"], "Amenities", "parking_check"
            )
            unit_details.append(unit_dict)

        property_obj = Property()

        # -------------- Rental Details ---------------------- #
        select_unit = request.POST["select_unit"]
        term_name = request.POST["term_name"]
        lease_start_date = request.POST["lease_start_date"]
        lease_end_date = request.POST["lease_end_date"]
        deposit = request.POST["deposit"]
        due_on = request.POST["due_on"]
        already_deposit = request.POST.getlist("already_deposit", [])
        rent = request.POST["rent"]
        select_due_date = request.POST["select_due_date"]
        select_due_date = request.POST["select_due_date"]
        first_rental_due_date = request.POST["first_rental_due_date"]
        invoice_date_list = request.POST["invoice_date_list"]
        invoice_amount_list = request.POST["invoice_amount_list"]

        if already_deposit:
            deposit_check = already_deposit[0]
        else:
            deposit_check = "off"

        # -------------- Tenants Details ---------------------- #
        tenant_f_name = request.POST["tenant_f_name"]
        tenant_l_name = request.POST["tenant_l_name"]
        tenant_email = request.POST["tenant_email"]
        tenant_mobile_number = request.POST["tenant_mobile_number"]

    p = pd.Period(str(today_date))
    if p.is_leap_year:
        one_year_date = today_date + datetime.timedelta(days=366)
    else:
        one_year_date = today_date + datetime.timedelta(days=365)

    currency_symbol = "$"
    return render(
        request,
        "test.html",
        context={
            "today_date": today_date,
            "one_year_date": one_year_date,
            "today_date_str": str(today_date),
            "one_year_date_str": str(one_year_date),
            "currency_symbol": currency_symbol,
        },
    )


def property_save_fun(request, property_obj, user_name, rent, total_tenants):
    # -------------- Property Details ---------------------- #
    try:
        property_image = request.FILES["property_image"]
    # To-Do  Remove bare except
    except:
        property_image = ""

    try:
        net_worth_check = request.POST["net_worth_check"]
    except:
        net_worth_check = False

    property_name = request.POST["property_name"]
    address_line1 = request.POST["address_line1"]
    address_line2 = request.POST["address_line2"]
    postcode = request.POST["postcode"]
    city = request.POST["city"]
    state = request.POST["state"]
    country = request.POST["country"]
    currency_name = request.POST["currency_name"]
    property_amount = request.POST["property_amount"]
    property_type = request.POST["property_type"]
    unit_name = request.POST.getlist("unit_name")
    bed_room_quantity = request.POST.getlist("bed_room_quantity")
    bath_room_quantity = request.POST.getlist("bath_room_quantity")
    square_feet = request.POST.getlist("square_feet")
    unit_details = []

    if net_worth_check:
        net_worth_check = True
    else:
        net_worth_check = False

    for i in range(len(unit_name)):
        unit_dict = {
            "name": unit_name[i],
            "details": {
                "bed_room": bed_room_quantity[i],
                "bath_room": bath_room_quantity[i],
                "square_feet": square_feet[i],
                "rent_includes": {},
                "Amenities": {},
            },
        }
        electricity_check = request.POST.getlist(f"electricity_check{i}", [])
        gas_check = request.POST.getlist(f"gas_check{i}", [])
        water_check = request.POST.getlist(f"water_check{i}", [])
        int_cable_check = request.POST.getlist(f"int_cable_check{i}", [])
        ac_check = request.POST.getlist(f"ac_check{i}", [])
        pool_check = request.POST.getlist(f"pool_check{i}", [])
        pets_check = request.POST.getlist(f"pets_check{i}", [])
        furnished_check = request.POST.getlist(f"furnished_check{i}", [])
        balcony_check = request.POST.getlist(f"balcony_check{i}", [])
        hardwood_check = request.POST.getlist(f"hardwood_check{i}", [])
        wheel_check = request.POST.getlist(f"wheel_check{i}", [])
        parking_check = request.POST.getlist(f"parking_check{i}", [])

        add_checkbox_value(
            electricity_check,
            unit_dict["details"],
            "rent_includes",
            "electricity_check",
        )
        add_checkbox_value(
            gas_check, unit_dict["details"], "rent_includes", "gas_check"
        )
        add_checkbox_value(
            water_check, unit_dict["details"], "rent_includes", "water_check"
        )
        add_checkbox_value(
            int_cable_check, unit_dict["details"], "rent_includes", "int_cable_check"
        )
        add_checkbox_value(
            ac_check, unit_dict["details"], "Amenities", "ac_check")
        add_checkbox_value(
            pool_check, unit_dict["details"], "Amenities", "pool_check")
        add_checkbox_value(
            pets_check, unit_dict["details"], "Amenities", "pets_check")
        add_checkbox_value(
            furnished_check, unit_dict["details"], "Amenities", "furnished_check"
        )
        add_checkbox_value(
            balcony_check, unit_dict["details"], "Amenities", "balcony_check"
        )
        add_checkbox_value(
            hardwood_check, unit_dict["details"], "Amenities", "hardwood_check"
        )
        add_checkbox_value(
            wheel_check, unit_dict["details"], "Amenities", "wheel_check"
        )
        add_checkbox_value(
            parking_check, unit_dict["details"], "Amenities", "parking_check"
        )
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


def rental_info_save(
    request, user_name, rental_obj, property_obj, invoice_data, rent, method_name
):
    # -------------- Rental Details ---------------------- #
    select_unit = request.POST["select_unit"]
    term_name = request.POST["term_name"]
    lease_start_date = request.POST["lease_start_date"]
    lease_end_date = request.POST["lease_end_date"]
    deposit = request.POST["deposit"]
    due_on = request.POST["due_on"]
    already_deposit = request.POST.getlist("already_deposit", [])
    select_due_date = request.POST["select_due_date"]
    first_rental_due_date = request.POST["first_rental_due_date"]
    invoice_date_list = ast.literal_eval(request.POST["invoice_date_list"])
    invoice_amount_list = ast.literal_eval(request.POST["invoice_amount_list"])
    first_rental_due_date = str(
        datetime.datetime.strptime(
            first_rental_due_date, DateFormats.MONTH_DD_YYYY.value
        ).date()
    )

    # -------------- Tenants Details ---------------------- #
    tenant_f_name = request.POST["tenant_f_name"]
    tenant_l_name = request.POST["tenant_l_name"]
    tenant_email = request.POST["tenant_email"]
    tenant_mobile_number = request.POST["tenant_mobile_number"]

    if already_deposit:

        deposit_check = already_deposit[0]
    else:
        deposit_check = "off"

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
        if deposit_check == "off":
            invoice_obj.invoice_status = InvoiceStatuses.UNPAID.value
            invoice_obj.already_paid = 0
            invoice_obj.balance_due = deposit
        else:
            invoice_obj.invoice_status = InvoiceStatuses.FULLY.value
            invoice_obj.already_paid = deposit
            invoice_obj.balance_due = 0
            invoice_obj.invoice_paid_date = today_date
            deposit_date = datetime.datetime.strftime(
                today_date, DateFormats.MONTH_DD_YYYY.value
            )
            invoice_obj.record_payment = [
                [
                    0,
                    invoice_obj.tenant_name,
                    deposit_date,
                    AccountTypes.CASH.value,
                    deposit,
                ]
            ]
        invoice_obj.save()

    rental_summary = []
    date_list_len = len(invoice_date_list)
    if method_name == "update":
        invoice_update_len = len(invoice_data)

    print("invoice_date_list======>", invoice_date_list)
    for i in range(date_list_len):
        if invoice_date_list[i] != "None":
            date_value = datetime.datetime.strptime(
                invoice_date_list[i], DateFormats.MONTH_DD_YYYY.value
            ).date()
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
                        record_payment_list = ast.literal_eval(
                            invoice_obj.record_payment
                        )
                balance_due = total_due - already_paid
            else:
                already_paid = 0
                quantity = "1"
                tenant_name = tenant_f_name + " " + tenant_l_name
                item_type = "Rent"
                item_description = f"Rent Due on {invoice_date_list[i]}"
                invoice_status = InvoiceStatuses.UNPAID.value
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
            rental_summary.append(
                {"due": invoice_date_list[i], "amount": total_amount})

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
    if request.method == "POST":
        user_name = request.user
        property_obj = Property()
        rental_obj = PropertyRentalInfo()
        invoice_obj = PropertyInvoice()
        rent = request.POST["rent"]
        total_tenants = 1
        property_save_fun(request, property_obj,
                          user_name, rent, total_tenants)
        rental_info_save(
            request, user_name, rental_obj, property_obj, invoice_obj, rent, "add"
        )
        return redirect("/property_list/")
    else:
        try:
            file_name = request.GET["file_name"]
            name = request.GET["name"]
            currency = request.GET["currency"]
            value = request.GET["value"]
            context = {
                "file_name": file_name,
                "name": name,
                "currency": currency,
                "value": value,
            }

        # To-Do  Remove bare except
        except:
            context = {"file_name": "False", "currency_symbol": "$"}

    p = pd.Period(str(today_date))
    if p.is_leap_year:
        one_year_date = today_date + datetime.timedelta(days=366)
    else:
        one_year_date = today_date + datetime.timedelta(days=365)

    context.update(
        {
            "today_date": today_date,
            "one_year_date": one_year_date,
            "today_date_str": str(today_date),
            "one_year_date_str": str(one_year_date),
            "month_date_dict": MONTH_DATE_DICT,
            "currency_dict": CURRENCY_DICT,
        }
    )
    return render(request, "property/property_add.html", context=context)


def update_property(request, pk, method_name):
    user_name = request.user
    context = {
        "method_type": method_name,
        "currency_dict": CURRENCY_DICT,
        "property_type_list": PROPERTY_TYPE_LIST,
        "month_date_dict": MONTH_DATE_DICT,
        "url_type": "Update",
    }
    if method_name == "property":
        result_obj = Property.objects.get(user=user_name, pk=pk)
        if request.method == "POST":
            property_save_fun(
                request,
                result_obj,
                user_name,
                result_obj.total_monthly_rent,
                result_obj.total_tenants,
            )
            return redirect(f"/property_details/{result_obj.id}")
        unit_details = ast.literal_eval(result_obj.unit_details)
        context["unit_details"] = unit_details
    else:
        result_obj = PropertyRentalInfo.objects.get(user=user_name, pk=pk)
        invoice_obj = PropertyInvoice.objects.filter(
            user=user_name,
            property_details=result_obj.property_address,
            unit_name=result_obj.unit_name,
        )
        if request.method == "POST":
            rent = request.POST["rent"]
            rental_info_save(
                request,
                user_name,
                result_obj,
                result_obj.property_address,
                invoice_obj,
                rent,
                "update",
            )
            return redirect(f"/property_details/{result_obj.property_address.id}")

        invoice_date_list = []
        invoice_amount_list = []
        rent_invoice_list = []
        for invoice_detail in invoice_obj:
            due_date = datetime.datetime.strftime(
                invoice_detail.invoice_due_date, DateFormats.MONTH_DD_YYYY.value
            )
            item_amount = float(invoice_detail.item_amount)
            rent_invoice_list.append({"due": due_date, "amount": item_amount})
            invoice_date_list.append(due_date)
            invoice_amount_list.append(item_amount)

        print(invoice_date_list)
        context["invoice_date_list"] = json.dumps(invoice_date_list)
        context["invoice_amount_list"] = json.dumps(invoice_amount_list)
        context["total_invoice_amount"] = sum(invoice_amount_list)
        context["rent_invoice_list"] = rent_invoice_list

    context["result_obj"] = result_obj
    return render(request, "property/property_update.html", context=context)


@login_required(login_url="/login")
def list_property(request):
    property_obj = Property.objects.filter(user=request.user)
    maintenance_dict = {}
    for data in property_obj:
        maintenance_obj = PropertyMaintenance.objects.filter(
            property_details__property_name=data.property_name, status="Unresolved"
        )
        maintenance_dict[data.property_name] = len(maintenance_obj)

    context = {
        "property_obj": property_obj,
        "maintenance_dict": maintenance_dict,
        "property_key": PROPERTY_KEYS,
        "property_key_dumps": json.dumps(PROPERTY_KEYS),
    }
    return render(request, "property/property_list.html", context=context)


@login_required(login_url="/login")
def property_details(request, pk):
    property_obj = Property.objects.get(user=request.user, pk=pk)
    unit_list = ast.literal_eval(property_obj.unit_details)
    maintenance_obj = PropertyMaintenance.objects.filter(
        property_details=property_obj)
    unit_details = PropertyRentalInfo.objects.filter(
        user=request.user, property_address=property_obj
    )
    remaining_unit_list = [i["name"] for i in unit_list]
    total_rent_amount_collected = 0
    other_amount_collected = 0
    collection_list = {}
    maintenance_dict = {}

    for data in unit_details:
        name_unit = data.unit_name
        remaining_unit_list.remove(name_unit)
        invoice_obj = PropertyInvoice.objects.filter(
            user=request.user, property_details=property_obj, unit_name=data.unit_name
        )
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
            if invoice_status == InvoiceStatuses.OVERDUE.value:
                overdue_list.append(data_obj.id)
            if data_obj.item_type == "Rent":
                total_rent_amount_collected += paid_amount
            else:
                other_amount_collected += paid_amount

        total_amount = total_rent_amount_collected + other_amount_collected
        collection_list[data.unit_name] = [
            total_rent_amount_collected,
            other_amount_collected,
            total_amount,
            day_diff,
            overdue_list,
        ]

    currency_symbol = property_obj.currency
    context = {
        "property_obj": property_obj,
        "unit_details": unit_details,
        "currency_symbol": currency_symbol,
        "collection_list": collection_list,
        "today_date": today_date,
        "unit_list": unit_list,
        "remaining_unit_list": remaining_unit_list,
        "maintenance_dict": maintenance_dict,
    }
    return render(request, "property/property_detail.html", context=context)


@login_required(login_url="/login")
def add_lease(request, pk, unit_name):
    username = request.user
    result_obj = Property.objects.get(user=username, pk=pk)

    if request.method == "POST":
        rental_obj = PropertyRentalInfo()
        invoice_obj = PropertyInvoice()
        rent = request.POST["rent"]
        rental_info_save(
            request, username, rental_obj, result_obj, invoice_obj, rent, "add"
        )
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

        context = {
            "today_date": today_date,
            "one_year_date": one_year_date,
            "today_date_str": str(today_date),
            "one_year_date_str": str(one_year_date),
            "method_type": "Rental Lease",
            "url_type": "Add",
            "result_obj": result_obj,
            "currency_dict": CURRENCY_DICT,
            "property_type_list": PROPERTY_TYPE_LIST,
            "month_date_dict": MONTH_DATE_DICT,
            "unit_name": unit_name,
        }
        unit_details = ast.literal_eval(result_obj.unit_details)
        context["unit_details"] = unit_details

        return render(request, "property/property_update.html", context=context)


@login_required(login_url="/login")
def delete_property(request, pk):
    property_obj = Property.objects.get(pk=pk)
    property_obj.delete()
    return JsonResponse({"status": "Successfully", "path": "/property_list/"})


# Property Maintenance


class MaintenanceList(LoginRequiredMixin, ListView):
    model = PropertyMaintenance
    template_name = "maintenance/maintenance_list.html"

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        data = super(MaintenanceList, self).get_context_data(**kwargs)
        user_name = self.request.user
        property_data = PropertyMaintenance.objects.filter(user=user_name)
        data["maintenance_key"] = MAINTENANCE_KEYS
        data["maintenance_key_dumps"] = json.dumps(MAINTENANCE_KEYS)
        data["maintenance_obj"] = property_data
        return data


class MaintenanceDetail(LoginRequiredMixin, DetailView):
    model = PropertyMaintenance
    template_name = "maintenance/maintenance_detail.html"


class MaintenanceAdd(LoginRequiredMixin, CreateView):
    model = PropertyMaintenance
    form_class = MaintenanceForm
    template_name = "maintenance/maintenance_add.html"

    def get_form_kwargs(self):
        """Passes the request object to the form class.
        This is necessary to only display members that belong to a given user"""

        kwargs = super(MaintenanceAdd, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(MaintenanceAdd, self).get_context_data(**kwargs)
        data["page"] = "Add"
        return data

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return super().form_valid(form)


class MaintenanceUpdate(LoginRequiredMixin, UpdateView):
    model = PropertyMaintenance
    form_class = MaintenanceForm
    template_name = "maintenance/maintenance_add.html"

    def get_form_kwargs(self):
        """Passes the request object to the form class.
        This is necessary to only display members that belong to a given user"""
        kwargs = super(MaintenanceUpdate, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(MaintenanceUpdate, self).get_context_data(**kwargs)
        property_id = data["propertymaintenance"].property_details.pk
        user_name = self.request.user
        unit_list, tenant_dict, currency = get_units(user_name, property_id)
        data["unit_list"] = unit_list
        data["page"] = "Update"
        data["maintenance_id"] = self.kwargs["pk"]
        return data


def delete_maintenance(request, pk):
    maintenance_obj = PropertyMaintenance.objects.get(pk=pk)
    maintenance_obj.delete()
    return JsonResponse(
        {"status": "Successfully", "path": "/property/maintenance/list/"}
    )


# Property Expenses Views
class ExpenseAdd(LoginRequiredMixin, CreateView):
    model = PropertyExpense
    form_class = ExpenseForm
    template_name = "property/expense_add.html"

    def get_form_kwargs(self):
        """Passes the request object to the form class.
        This is necessary to only display members that belong to a given user"""

        kwargs = super(ExpenseAdd, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(ExpenseAdd, self).get_context_data(**kwargs)
        data["page"] = "Add"
        return data

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return super().form_valid(form)


class ExpenseList(LoginRequiredMixin, ListView):
    model = PropertyExpense
    template_name = "property/expense_list.html"

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        data = super(ExpenseList, self).get_context_data(**kwargs)
        user_name = self.request.user
        property_data = PropertyExpense.objects.filter(user=user_name)
        data["expense_key"] = PROPERTY_EXPENSES_KEYS
        data["expense_key_dumps"] = json.dumps(PROPERTY_EXPENSES_KEYS)
        data["expense_obj"] = property_data
        return data


class ExpenseUpdate(LoginRequiredMixin, UpdateView):
    model = PropertyExpense
    form_class = ExpenseForm
    template_name = "property/expense_add.html"

    def get_form_kwargs(self):
        kwargs = super(ExpenseUpdate, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs

    def get_context_data(self, **kwargs):
        data = super(ExpenseUpdate, self).get_context_data(**kwargs)
        property_id = data["propertyexpense"].property_details.pk
        user_name = self.request.user
        unit_list, tenant_dict, currency = get_units(user_name, property_id)
        data["unit_list"] = unit_list
        data["page"] = "Update"
        data["expense_id"] = self.kwargs["pk"]
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
    incomes_list = []
    total_open_invoice = 0
    total_overdue = 0
    total_partially_paid = 0
    total_fully_paid = 0
    graph_currency = "$"

    for data in unit_obj:
        invoice_obj = PropertyInvoice.objects.filter(
            user=user_name,
            property_details=data.property_address,
            unit_name=data.unit_name,
        )
        data_list = [
            data.property_address.currency,
            data.property_address.property_name,
            data.unit_name,
        ]
        graph_currency = data.property_address.currency
        total_amount = 0
        total_paid = 0

        for item in invoice_obj:
            item_amount = float(item.item_amount) * float(item.quantity)
            item_paid = float(item.already_paid)
            total_amount += item_amount
            total_paid += item_paid
            if item.invoice_status == InvoiceStatuses.UNPAID.value:
                total_open_invoice += item_amount
            if item.invoice_status == InvoiceStatuses.PARTIALLY.value:
                total_partially_paid += item_paid
                total_open_invoice += float(item.balance_due)
            if item.invoice_status == InvoiceStatuses.FULLY.value:
                total_fully_paid += item_amount
            if item.invoice_status == InvoiceStatuses.OVERDUE.value:
                over_due_amount = float(item.balance_due)
                total_overdue += over_due_amount

        total_balance = total_amount - total_paid
        data_list += [total_amount, total_paid, total_balance]
        incomes_list.append(data_list)

    income_values = [
        total_open_invoice,
        total_overdue,
        total_partially_paid,
        total_fully_paid,
    ]

    context = {
        "income_obj": incomes_list,
        "graph_label": INCOME_LABELS,
        "graph_value": income_values,
        "graph_currency": graph_currency,
        "graph_id": "#income_pie_chart",
        "income_key": INCOME_KEYS,
        "income_key_dumps": json.dumps(INCOME_KEYS),
        "graph_label_dumps": json.dumps(INCOME_LABELS),
        "graph_value_dumps": json.dumps(income_values),
    }
    return render(
        request, "property_invoice/property_income_list.html", context=context
    )


@login_required(login_url="/login")
def property_invoice_add(request):
    user_name = request.user
    if request.method == "POST":
        property_name = request.POST["property_name"]
        invoice_due_date = request.POST["invoice_due_date"]
        unit_name = request.POST["unit_name"]
        tenant_name = request.POST["tenant_name"]
        item_type = request.POST["item_type"]
        item_description = request.POST["item_description"]
        quantity = request.POST["quantity"]
        item_amount = request.POST["item_amount"]
        already_paid = float(request.POST["already_paid"])
        total_paid = int(quantity) * float(item_amount)
        balance_due = total_paid - already_paid

        due_date = datetime.datetime.strptime(
            invoice_due_date, DateFormats.YYYY_MM_DD.value
        ).date()
        property_obj = Property.objects.get(user=user_name, pk=property_name)
        try:
            invoice_id = request.POST["invoice_id"]
            invoice_obj = PropertyInvoice.objects.get(
                user=user_name, pk=invoice_id)
            record_payment_list = ast.literal_eval(invoice_obj.record_payment)
            redirect_url = f"/property/invoice/details/{invoice_id}"
        # To-Do  Remove bare except
        except:
            invoice_obj = PropertyInvoice()
            redirect_url = (
                f"/property/invoice/list/{property_obj.property_name}/{unit_name}"
            )
            record_payment_list = []

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
            invoice_obj.invoice_status = InvoiceStatuses.PARTIALLY.value
            deposit_date = datetime.datetime.strftime(
                today_date, DateFormats.MONTH_DD_YYYY.value
            )
            invoice_obj.invoice_paid_date = today_date
            if record_payment_list:
                pass
            else:
                record_payment_list.append(
                    [
                        0,
                        tenant_name,
                        deposit_date,
                        AccountTypes.CASH.value,
                        already_paid,
                    ]
                )
            invoice_obj.record_payment = record_payment_list

        elif already_paid == total_paid:
            invoice_obj.invoice_status = InvoiceStatuses.FULLY.value

        else:
            invoice_obj.invoice_status = InvoiceStatuses.UNPAID.value

        if due_date < today_date:
            invoice_obj.invoice_status = InvoiceStatuses.OVERDUE.value

        invoice_obj.save()
        return redirect(redirect_url)
    else:
        property_list = Property.objects.filter(user=user_name)
        context = {"property_list": property_list}

    return render(
        request, "property_invoice/property_invoice_add.html", context=context
    )


@login_required(login_url="/login")
def property_invoice_list(request, property_name, unit_name):
    user_name = request.user
    invoice_details = PropertyInvoice.objects.filter(
        user=user_name,
        property_details__property_name=property_name,
        unit_name=unit_name,
    ).order_by("invoice_due_date")

    context = {
        "invoice_details": invoice_details,
        "property_name": property_name,
        "unit_name": unit_name,
        "invoice_key": INVOICE_KEYS,
        "invoice_key_dumps": json.dumps(INVOICE_KEYS),
    }
    return render(
        request, "property_invoice/property_invoice_list.html", context=context
    )


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
        text_class = "text-success"

    if days_diff > 0:
        text_message = f"Payment late {abs(days_diff)} days"
        text_class = "text-danger"
    if days_diff == 0:
        text_message = f"Payment expected at today"
        text_class = "text-warning"

    if invoice_obj.invoice_status == InvoiceStatuses.FULLY.value:
        text_message = ""

    context = {
        "invoice_obj": invoice_obj,
        "record_payment_detail": record_payment_detail,
        "today_date": str(today_date),
        "text_message": text_message,
        "text_class": text_class,
    }
    return render(
        request, "property_invoice/property_invoice_detail.html", context=context
    )


@login_required(login_url="/login")
def property_invoice_update(request, pk):
    user_name = request.user
    invoice_obj = PropertyInvoice.objects.get(user=user_name, pk=pk)
    context = {"invoice_obj": invoice_obj}
    return render(
        request, "property_invoice/property_invoice_update.html", context=context
    )


@login_required(login_url="/login")
def record_payment_save(request, pk, method_type, paid_amount, payment_index=None):
    user_name = request.user
    invoice_obj = PropertyInvoice.objects.get(user=user_name, pk=pk)
    if invoice_obj.record_payment:
        record_payments = ast.literal_eval(invoice_obj.record_payment)
    else:
        record_payments = []
    balance_due = float(invoice_obj.balance_due)
    redirect_url = f"/property/invoice/details/{invoice_obj.id}"
    if method_type == "delete_payment":
        record_payments.remove(record_payments[payment_index - 1])
        invoice_obj.already_paid = float(
            invoice_obj.already_paid) - paid_amount
        invoice_obj.balance_due = float(invoice_obj.balance_due) + paid_amount
        if invoice_obj.already_paid == 0:
            invoice_obj.invoice_status = InvoiceStatuses.UNPAID.value
        else:
            invoice_obj.invoice_status = InvoiceStatuses.PARTIALLY.value
    else:
        payment_no = len(record_payments)
        payer_name = request.POST["payer_name"]
        payment_method = request.POST["payment_method"]
        deposit_date = request.POST["deposit_date"]
        invoice_obj.invoice_paid_date = deposit_date
        deposit_date = datetime.datetime.strptime(
            deposit_date, DateFormats.YYYY_MM_DD.value
        ).date()
        deposit_date = datetime.datetime.strftime(
            deposit_date, DateFormats.MONTH_DD_YYYY.value
        )
        record_payments.append(
            [payment_no, payer_name, deposit_date, payment_method, paid_amount]
        )
        invoice_obj.already_paid = float(
            invoice_obj.already_paid) + paid_amount
        invoice_obj.balance_due = balance_due - paid_amount

        if paid_amount > 0:
            invoice_obj.invoice_status = InvoiceStatuses.PARTIALLY.value

        if paid_amount == balance_due:
            invoice_obj.invoice_status = InvoiceStatuses.FULLY.value

    invoice_obj.record_payment = record_payments
    if invoice_obj.invoice_due_date < today_date:
        invoice_obj.invoice_status = InvoiceStatuses.OVERDUE.value

    invoice_obj.save()
    return redirect_url


@login_required(login_url="/login")
def delete_invoice_payment(request, pk, payment_index, paid_amount):
    paid_amount = float(paid_amount)
    redirect_url = record_payment_save(
        request, pk, "delete_payment", paid_amount, payment_index
    )
    return redirect(redirect_url)


@login_required(login_url="/login")
def property_invoice_payment(request, pk):
    paid_amount = float(request.POST["paid_amount"])
    redirect_url = record_payment_save(
        request, pk, "record_payment", paid_amount)
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
    rental_info = PropertyRentalInfo.objects.filter(
        user=user_name, property_address=property_info
    )
    tenant_dict = {}
    for data in rental_info:
        tenant_dict[data.unit_name] = data.first_name + " " + data.last_name

    unit_list = ast.literal_eval(property_info.unit_details)
    return unit_list, tenant_dict, property_info.currency


@login_required(login_url="/login")
def property_info(request):
    if request.method == "POST" and request.is_ajax():
        property_name = request.POST["property_name"]
        user_name = request.user
        unit_list, tenant_dict, currency_symbol = get_units(
            user_name, property_name)
        return JsonResponse(
            {
                "unit_list": unit_list,
                "tenant_dict": tenant_dict,
                "currency_symbol": currency_symbol,
            }
        )


# Sample Pages


def property_sample_page(request):
    graph_currency = "$"
    context = {
        "graph_label": json.dumps(GRAPH_LABELS),
        "graph_value": GRAPH_VALUES,
        "graph_currency": graph_currency,
        "graph_id": "#income_pie_chart",
    }
    return render(request, "property_sample_page.html", context=context)


def rental_property_sample_page(request):

    context = {
        "cash_on_cash_return_data": SAMPLE_CASH_ON_CASH_RETURN_DATA,
        "projection_key": SAMPLE_PROJECTION_KEY,
        "return_on_investment_data": SAMPLE_RETURN_ON_INVESTMENT_DATA,
        "debt_cov_ratio_data": SAMPLE_DEBT_COV_RATIO_DATA,
        "return_investment_data": SAMPLE_RETURN_INVESTMENT_DATA,
        "property_expense_data": SAMPLE_PROPERTY_EXPENSE_DATA,
        "mortgage_date_data": SAMPLE_MORTGAGE_DATE_DATA,
        "mortgage_graph_data": SAMPLE_MORTGAGE_GRAPH_DATA,
    }

    return render(request, "rental_prop_sample_page.html", context=context)


def add_update_notes(request):
    """
    Handles adding, updating, and deleting user notes via AJAX POST requests.

    Args:
        request (HttpRequest): The incoming HTTP request.

    Returns:
        JsonResponse: JSON containing the operation status and updated note list.
    """

    if request.method == "POST":
        user = request.user
        title = request.POST.get("title", "").strip()
        notes = request.POST.get("notes", "").strip()
        notes_method = request.POST.get("notes_method", "").strip()
        select_title = request.POST.get("select_title", "").strip().title()
        result = {}
        notes_check = MyNotes.objects.filter(user=user, title=title).exists()

        if notes_method == "Update":
            if select_title == title:
                # Update existing note with the same title
                notes_obj = MyNotes.objects.get(user=user, title=title)
                notes_obj.title = title
                notes_obj.notes = notes
                notes_obj.save()
                result = {"status": "Updated"}
            else:
                # Check if a note with the new title already exists
                if notes_check:
                    result = {
                        "status": "This Title Named Note Already Exists!!"}
                else:
                    # Update note with a different title
                    notes_obj = MyNotes.objects.get(
                        user=user, title=select_title)
                    notes_obj.title = title
                    notes_obj.notes = notes
                    notes_obj.save()
                    result = {"status": "Updated"}

        elif notes_method == "Delete":
            # Delete the specified note
            notes_obj = MyNotes.objects.get(
                user=user,
                title=select_title,
            )
            notes_obj.delete()
            print(notes_obj)
            result = {"status": "Deleted Successfully"}

        elif notes_method == "Add":
            if notes_check:
                result = {"status": "This Title Named Note Already Exists!!"}
            else:
                # Add a new note
                notes_obj = MyNotes()
                notes_obj.user = user
                notes_obj.title = title.title()
                notes_obj.notes = notes
                notes_obj.save()
                result = {"status": "Added"}

        # Retrieve and return the updated list of user notes
        user_notes = MyNotes.objects.filter(user=user)
        notes_list = [[data.title, data.notes] for data in user_notes]

        result["user_notes"] = notes_list
        print("Notes list", notes_list)
        return JsonResponse(result)
    else:
        # Retrieve and return the updated list of user notes
        user_notes = MyNotes.objects.filter(user=request.user)
        notes_list = [[data.title, data.notes] for data in user_notes]
        result = {}
        result["user_notes"] = notes_list

        return JsonResponse(result)


# Right Sidebar Views
@login_required
@require_GET
def get_notes(request):
    try:
        print("working get notes")
        user = request.user
        notes = MyNotes.objects.filter(user=user).order_by("-id")
        data = [
            {
                "id": note.id,
                "title": note.title,
                "notes": note.notes,
                "added_on": note.added_on,
            }
            for note in notes
        ]
        return JsonResponse({"data": data, "success": "true"})
    except Exception as e:
        print(e)
        return JsonResponse({"error": "Bad Request", "success": "false"})


@login_required(login_url="/login")
@require_GET
def load_ai_chat(request):
    """
    - Only GET method is allowed.
    - Only Authenticated user is allowed.
    - This view handled user's previous chats as chat history.
    - A pagination system has added to reduce load in db.
    - Each page includes 5 pair of messages means 5 objects from database.
    - Works on AIChat database model.
    """
    user = request.user
    page = int(request.GET.get("page", 1))
    page_size = 5

    start = (page - 1) * page_size
    end = page * page_size

    messages = AIChat.objects.filter(user=user).order_by("-id")[start:end]

    messages_data = [
        {
            "id": message.id,
            "ai_msg": message.ai_response,
            "user_msg": message.message,
            "timestamp": message.created_at,
        }
        for message in messages
    ]

    has_more = AIChat.objects.filter(user=user).count() > end

    return JsonResponse({"messages": messages_data, "has_more": has_more})


@login_required(login_url="/login")
@require_POST
def send_message_to_ai(request):
    """
    - Only POST method is allowed.
    - Only Authenticated user is allowed.
    - This view handles user's chat messages and sends them to OpenAI for AI response.
    - On successful AI response, AIChat database model is used to store data.
    - Must use openai version 1.39
    """
    try:
        # Ensure the user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({"error": "User not authenticated"}, status=401)

        # Get the user message
        user_message = request.POST.get("message", "").strip()

        # Validate the user message
        if not user_message:
            return JsonResponse({"error": "Message is required"}, status=400)

        # Send the message to OpenAI
        try:
            response = ai_client.chat.completions.create(
                messages=[
                    {
                        "role": "user",  # Prompt sender type
                        "content": user_message,
                    }
                ],
                model="gpt-3.5-turbo",  # OpenAI Language Model
            )
            ai_res = response.choices[0].message.content
        except Exception as e:
            return JsonResponse({"error": "OpenAI request limit exceeded"}, status=400)

        # Save the AI response to the database
        instance = AIChat.objects.create(
            user=request.user, message=user_message, ai_response=ai_res
        )

        return JsonResponse(
            {"usr_msg": instance.message, "ai_res": instance.ai_response}, status=200
        )

    except KeyError as e:
        return JsonResponse({"error": f"KeyError: {str(e)}"}, status=400)

    except Exception as e:
        return JsonResponse({"error": f"Exception: {str(e)}"}, status=400)


# Read data from csv
@require_GET
def read_documentation_csv(request):
    """
    - Only get message allowed.
    - This view reads a CSV file & convert the data into python dictionary.
    - On successful conversion, it sends data as json response.
    - CSV file should be located at "documentation/lesson.csv".
    - On file change, have to change find() arguments.
    """
    try:
        file_path = finders.find("documentation/lesson.csv")
    except Exception:
        return JsonResponse({"error": "File not found"}, status=404)

    with open(file_path, mode="r", encoding="utf-8") as file:
        # Use DictReader for better structure
        csv_reader = csv.DictReader(file)
        # Convert rows into a list of dictionaries
        data = [row for row in csv_reader]

    return JsonResponse({"data": data, "status": "success"}, safe=False)


# Create a feedback
@login_required(login_url="/login")
@require_POST
def create_feedback(request):
    """
    - Only POST method allowed.
    - Only Authenticated user allowed.
    - This view handled user feedback request data.
    - All fields are required except screenshot.
    - On successful creation, Feedback database model is used to store data.
    """
    user = request.user
    feature = request.POST.get("feedbackFeature")
    issue = request.POST.get("feedback_issue")
    screenshot = request.FILES.get("screenshotData")
    description = request.POST.get("feedbackDetails")
    suggestion = request.POST.get("featureSuggestions")
    importance = request.POST.get("feedback_priority")
    try:
        Feedback.objects.create(
            user=user,
            feature=feature,
            issue=issue,
            screenshot=screenshot,
            description=description,
            suggestion=suggestion,
            importance=importance,
        )
    except:
        return JsonResponse({"error": "Failed to create feedback"}, status=400)
    return JsonResponse(
        {"message": "Feedback created successfully", "status": "success"}, status=201
    )


@method_decorator(login_required, name="dispatch")
class ErrorLogsList(ListView):
    """
    - Only staff user allowed.
    - This view displays all the error logs.
    - If there is no params with the url it renders the html file.
    - If there is a datatables params with the url it returns json response of all the error logs.
    """

    model = AppErrorLog
    template_name = "admin_only/app_error_logs.html"

    def render_to_response(self, context, **response_kwargs):
        if self.request.GET.get("datatables"):
            draw = int(self.request.GET.get("draw", "1"))
            length = int(self.request.GET.get("length", "10"))
            start = int(self.request.GET.get("start", "0"))
            order_column_index = int(
                self.request.GET.get("order[0][column]", "0"))
            order_direction = self.request.GET.get("order[0][dir]", "asc")
            status_filter = self.request.GET.get("status", None)
            sv = self.request.GET.get("search[value]", None)

            # Define column mapping for ordering
            order_columns = [
                "",
                "code",
                "timestamp",
                "exception_type",
                "request_path",
                "error_message",
                "count",
                "status",
                "action",
            ]
            order_column = order_columns[order_column_index]
            if order_direction == "desc":
                order_column = f"-{order_column}"

            qs = self.get_queryset().order_by(order_column)
            # Apply status filter if provided
            if status_filter:
                qs = qs.filter(status=status_filter)
            if sv:
                qs = qs.filter(
                    Q(code__icontains=sv)
                    | Q(request_path__icontains=sv)
                    | Q(error_message__icontains=sv)
                    | Q(exception_type__icontains=sv)
                )
            filtered_count = qs.count()
            qs = qs[start: start + length]

            # Serialize response data
            data = [
                {
                    "id": log.id,
                    "code": log.code,
                    "timestamp": localtime(log.timestamp).strftime("%Y-%m-%d %I:%M %p"),
                    "exception_type": log.exception_type,
                    "request_path": log.request_path,
                    "error_message": log.error_message,
                    "status": log.status,
                    "count": log.count,
                }
                for log in qs
            ]
            return JsonResponse(
                {
                    "draw": draw,
                    "recordsTotal": self.model.objects.count(),
                    "recordsFiltered": filtered_count,
                    "data": data,
                }
            )
        return super().render_to_response(context, **response_kwargs)


@require_GET
@staff_member_required
def error_report_details(request, error_id):
    """
    - Only GET Method allowed.
    - Only Admin user allowed.
    - This view collect id from url and return details of the error log.
    """
    # Retrieve the error log or return a 404
    error_log = get_object_or_404(AppErrorLog, id=error_id)

    # Define the fields to include in the response
    data = {
        "id": error_log.id,
        "code": error_log.code,
        "timestamp": localtime(error_log.timestamp).strftime("%Y-%m-%d %I:%M %p"),
        "exception_type": error_log.exception_type,
        "request_path": error_log.request_path,
        "error_message": error_log.error_message,
        "count": error_log.count,
        "status": error_log.status,
        "traceback": error_log.traceback,
    }

    return JsonResponse(data)


@csrf_exempt
@staff_member_required
@require_POST
def error_report_action(request):
    """
    - Only Admin user allowed.
    - Received 3 data: action, ids & status.
    - Handle update/delete based on action value.
    - Handle delete or update status actions for AppErrorLog.
    - Handles multiple objects/fields update & delete at once.
    """
    try:
        data = json.loads(request.body)
        action = data.get("action")
        selected_ids = data.get("selected_ids", [])

        if not selected_ids:
            return JsonResponse(
                {
                    "status": 400,
                    "message": "No logs selected.",
                    "success": "Error",
                }
            )

        logs = AppErrorLog.objects.filter(id__in=selected_ids)

        if action == "update_status":
            new_status = data.get("status")
            if new_status in [
                choice[0] for choice in AppErrorLog.StatusChoices.choices
            ]:
                logs.update(status=new_status)
                return JsonResponse(
                    {
                        "status": 200,
                        "message": "Status updated successfully.",
                        "success": "Success",
                    }
                )
            return JsonResponse(
                {
                    "status": 400,
                    "message": "Invalid status.",
                    "success": "Error",
                }
            )

        elif action == "delete":
            logs.delete()
            return JsonResponse(
                {
                    "status": 200,
                    "message": "Logs deleted successfully.",
                    "success": "Success",
                }
            )

        return JsonResponse(
            {
                "status": 400,
                "message": "Invalid action.",
                "success": "Error",
            }
        )

    except Exception as e:
        return JsonResponse(
            {
                "status": 500,
                "message": str(e),
                "success": "Error",
            }
        )


@require_GET
@staff_member_required
def fetch_error_logs(request):
    """
    - Only GET Method allowed.
    - Only Admin user allowed.
    - This view handles fetching latest 50 of error logs data.
    """

    log_file_path = settings.LOG_FILE_PATH

    # Number of lines to fetch from the end of the log file
    lines_to_fetch = 50
    try:
        with open(log_file_path, "r") as log_file:
            logs = log_file.readlines()[-lines_to_fetch:]
    except FileNotFoundError:
        logs = ["Log file not found."]
    except Exception as e:
        logs = [f"Error reading log file: {e}"]
    return JsonResponse({"logs": logs})


@require_GET
@staff_member_required
def download_log_file(request):
    """
    Serve the log file for download.
    Only available to admin users.
    """
    if not request.user.is_superuser:
        return HttpResponseNotFound("You are not authorized to access this file.")

    log_file_path = settings.LOG_FILE_PATH

    if os.path.exists(log_file_path):
        return FileResponse(
            open(log_file_path, "rb"), as_attachment=True, filename="app_errors.log"
        )
    else:
        return HttpResponseNotFound("Log file not found.")


def test_middleware(request):
    raise ValueError(
        "A forced Error to test error middleware & error log functionalities."
    )


# Page Errors


def error_404(request, exception):
    data = {"error": "Page Not Found!"}
    return render(request, "error.html", data)


def error_500(request):
    data = {"error": "Internal Server Error!"}
    return render(request, "error.html", data)


def error_403(request, exception):
    data = {"error": "Access Denied.!"}
    return render(request, "error.html", data)


def error_400(request, exception):
    data = {"error": "Bad Request!"}
    return render(request, "error.html", data)

