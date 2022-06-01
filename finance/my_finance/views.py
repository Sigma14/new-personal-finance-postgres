import ast
import csv
import json
import calendar
import pandas as pd
import numpy as np
import datetime
from io import BytesIO
import base64
from collections import OrderedDict
from django.contrib.auth.decorators import login_required
import requests
from django.contrib.auth.hashers import identify_hasher
from django.db.models import Sum
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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Image
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A0, letter
from .forms import CategoryForm, LoginForm, BudgetForm, BillForm, TransactionForm, AccountForm, TemplateBudgetForm, \
    MortgageForm, LiabilityForm, MaintenanceForm, ExpenseForm
from .models import Category, Budget, Bill, Transaction, Goal, Account, SuggestiveCategory, Property, Revenues, \
    Expenses, AvailableFunds, TemplateBudget, RentalPropertyModel, PropertyPurchaseDetails, MortgageDetails, \
    ClosingCostDetails, RevenuesDetails, ExpensesDetails, CapexBudgetDetails, PropertyRentalInfo, PropertyInvoice, \
    PropertyMaintenance, PropertyExpense
from .mortgage import calculator
from reportlab.lib.colors import PCMYKColor
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.lib.units import inch
from reportlab.platypus.flowables import Spacer
from reportlab.lib.validators import Auto
from reportlab.lib.enums import TA_CENTER
from django.contrib.auth.models import User

wordpress_api_key = "YWxoyNoKNBmPmXy413m3jxYhTZ"
currency_dict = {'$': "US Dollar ($)", '€': 'Euro (€)', '₹': 'Indian rupee (₹)', '£': 'British Pound (£)'}
scenario_dict = {'best_case': "Best Case Scenario Purchase Price", 'likely_case': 'Likely Case Scenario Purchase Price',
                 'worst_case': 'Worst Case Scenario Purchase Price'}
property_type_list = ['Apartment', 'Commercial', 'Condo', 'Duplex', 'House', 'Mixed-Use', 'Other']
month_date_dict = {'1': '1st ', '2': '2nd ', '3': '3rd ', '4': '4th ', '5': '5th ', '6': '6th ', '7': '7th ', '8': '8th ', '9': '9th ', '10': '10th', '11': '11th', '12': '12th', '13': '13th', '14': '14th', '15': '15th', '16': '16th', '17': '17th', '18': '18th', '19': '19th', '20': '20th', '21': '21st', '22': '22nd', '23': '23rd', '24': '24th', '25': '25th', '26': '26th', '27': '27th', '28': '28th', '29': '29th', '30': '30th'}
today_date = datetime.date.today()


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


def update_budget_items(user_name, budget_obj, transaction_amount, transaction_out_flow):
    amount_budget = float(budget_obj.amount)
    spent_budget = round(float(budget_obj.budget_spent) - transaction_amount, 2)
    left_budget = round(float(budget_obj.budget_left) + transaction_amount, 2)
    period_budget = budget_obj.budget_period
    if transaction_out_flow:
        budget_obj.budget_spent = spent_budget
        budget_obj.budget_left = left_budget
        if period_budget == 'Yearly' or period_budget == 'Quarterly':
            data_budget = Budget.objects.filter(user=user_name, name=budget_obj.name,
                                                created_at=budget_obj.created_at,
                                                ended_at=budget_obj.ended_at)
            for budget_value in data_budget:
                if budget_value.start_date != budget_obj.start_date:
                    budget_value.budget_left = left_budget
                    budget_value.save()

    else:
        budget_obj.amount = round(amount_budget - transaction_amount, 2)
        budget_obj.budget_left = round(budget_obj.budget_left - transaction_amount, 2)

        if period_budget == 'Yearly' or period_budget == 'Quarterly':
            data_budget = Budget.objects.filter(user=user_name, name=budget_obj.name,
                                                created_at=budget_obj.created_at, ended_at=budget_obj.ended_at)
            for budget_value in data_budget:
                if budget_value.start_date != budget_obj.start_date:
                    budget_value.amount = budget_obj.amount
                    budget_value.budget_left = budget_obj.budget_left
                    budget_value.save()

    return budget_obj


def add_new_budget_items(user_name, budget_obj, transaction_amount, out_flow):
    print("add_new_budget_items")
    amount_budget = float(budget_obj.amount)
    spent_budget = round(float(budget_obj.budget_spent) + transaction_amount, 2)
    period_budget = budget_obj.budget_period

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


def save_budgets(user_name, start_date, end_date, budget_name, budget_period, budget_currency, budget_amount,
                 budget_auto, created_date, ended_date, initial_amount):
    budget_obj = Budget()
    budget_obj.user = user_name
    budget_obj.start_date = start_date
    budget_obj.end_date = end_date
    budget_obj.name = budget_name
    budget_obj.budget_period = budget_period
    budget_obj.currency = budget_currency
    budget_obj.amount = budget_amount
    budget_obj.initial_amount = initial_amount
    budget_obj.budget_left = budget_amount
    budget_obj.auto_budget = budget_auto
    budget_obj.created_at = created_date
    budget_obj.ended_at = ended_date
    budget_obj.save()


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


def start_end_date(date_value, period):
    if period == "Yearly":
        start_year_date = f"01-01-{date_value.year}"
        end_year_date = f"31-12-{date_value.year}"
        return datetime.datetime.strptime(start_year_date, "%d-%m-%Y").date(), datetime.datetime.strptime(end_year_date,
                                                                                                          "%d-%m-%Y").date()

    if period == "Quarterly":
        current_date = datetime.datetime.now()
        upcoming_quarter = int((current_date.month - 1) / 3 + 1)
        if upcoming_quarter == 4:
            upcoming_quarter_date = datetime.datetime(current_date.year, 3 * upcoming_quarter, 31)
        else:
            upcoming_quarter_date = datetime.datetime(current_date.year, 3 * upcoming_quarter + 1,
                                                      1) + datetime.timedelta(days=-1)
        quarter_value = upcoming_quarter_date.date() - datetime.timedelta(days=88)
        return upcoming_quarter_date.date(), quarter_value.replace(day=1)

    if period == "Monthly":
        start_date = date_value.replace(day=1)
        end_date = date_value.replace(day=calendar.monthrange(date_value.year, date_value.month)[1])
        return start_date, end_date

    if period == "Weekly":
        week_start = today_date - datetime.timedelta(days=today_date.weekday())
        week_end = week_start + datetime.timedelta(days=6)
        return week_start, week_end


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
                if transaction_date in credit_date_dict:
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
        'debit_graph_data_dumbs': json.dumps(debit_date_list),
        'credit_graph_data_dumbs': json.dumps(credit_date_list),
    }
    if date_list:
        context['start_date'] = date_list[0],
        context['end_date'] = date_list[-1],

    return context


def transaction_checks(username, transaction_amount, account, bill_name, budget_name, cleared_amount, out_flow,
                       transaction_date):
    if cleared_amount == "True":
        account_obj = Account.objects.get(user=username, name=account)

        if bill_name:
            bill_name = bill_name.label
            bill_obj = Bill.objects.filter(user=username, label=bill_name)[0]
        else:
            bill_obj = False

        if budget_name and budget_name != "None":
            date_check = datetime.datetime.strptime(transaction_date, "%Y-%m-%d").date()
            start_month_date, end_month_date = start_end_date(date_check, "Monthly")
            budget_obj = Budget.objects.filter(user=username, name=budget_name, start_date=start_month_date,
                                               end_date=end_month_date)[0]
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
            budget_obj = add_new_budget_items(username, budget_obj, transaction_amount, out_flow)
            budget_obj.save()
        account_obj.transaction_count += 1
        account_obj.save()
        return account_obj, budget_obj


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


@login_required(login_url="/login")
def home(request):
    user_name = request.user
    if not request.user.is_anonymous:
        categories = Category.objects.filter(user=user_name)
        all_transaction_data = Transaction.objects.filter(user=user_name).order_by('transaction_date')
        current_date = datetime.datetime.today().date()
        month_start, month_end = start_end_date(current_date, "Monthly")
        accounts_data = Account.objects.filter(user=user_name)
        property_data = Property.objects.filter(user=user_name)
        budget_data = Budget.objects.filter(user=user_name, start_date=month_start, end_date=month_end)
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
            account_date_list = []

        for data in property_data:
            property_currency_balance.append({data.currency: data.value})

        category_spent_amount(categories, user_name, categories_name, categories_value)
        budget_currency = '$'
        for data in budget_data:
            budget_currency = data.currency
            total_budget += float(data.amount)
            budget_label.append(data.name)
            budget_values.append(float(data.amount))

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
        print("account_graph_data==========>", acc_graph_data)

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
            "net_worth_dict": net_worth_dict,
            "max_value": acc_max_value,
            "min_value": acc_min_value
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
    if account_data:
        min_date = account_data[0].created_at.date()
        max_date = datetime.datetime.today().date()
        day_diff = (max_date - min_date).days
        account_date_list = [str(max_date - datetime.timedelta(days=x)) for x in range(day_diff)]
        account_date_list.append(str(min_date))
        account_date_list = account_date_list

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
        data['categories_series'] = [{'name': 'Spend', 'data': categories_value}]

        return data


class CategoryDetail(LoginRequiredMixin, DetailView):
    model = Category
    template_name = 'category/category_detail.html'


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
        category_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


def user_login(request):
    # if request.method == 'POST':
    #     try:
    #         next = request.POST['next']
    #     except:
    #         next = None
    #     username = request.POST['register-username']
    #     password = request.POST['register-password']
    #     user = authenticate(username=username, password=password)
    #     if user is None:
    #         context = {'login_error': 'Username and Password Incorrect'}
    #         return render(request, "login_page.html", context)
    #     elif not user.is_active:
    #         context = {'login_error': 'User is not active'}
    #         return render(request, "login_page.html", context)
    #     else:
    #         login(request, user)
    #         template_budget_data = TemplateBudget.objects.filter(user=user)
    #         if template_budget_data:
    #             budget_obj = TemplateBudget.objects.filter(user=user)
    #             budget_obj.delete()
    #         period_list = {'Daily': 'Going out', 'Weekly': 'Groceries', 'Monthly': 'Bills'}
    #         date_value = datetime.datetime.today().date()
    #         start_month_date, end_month_date = start_end_date(date_value, "Monthly")
    #         for key, value in period_list.items():
    #             template_obj = TemplateBudget()
    #             template_obj.user = user
    #             budget_name = value
    #             template_obj.name = budget_name
    #             template_obj.currency = "$"
    #             template_obj.auto_budget = True
    #             template_obj.budget_period = key
    #
    #             if key == 'Monthly':
    #                 template_obj.start_date = start_month_date
    #                 template_obj.end_date = end_month_date
    #                 template_obj.initial_amount = 1500
    #                 template_obj.amount = 1500
    #                 template_obj.budget_spent = 1000
    #                 template_obj.budget_left = 500
    #                 template_obj.created_at = start_month_date
    #                 template_obj.ended_at = end_month_date
    #                 template_obj.save()
    #
    #             if key == 'Weekly':
    #                 start_week_date, end_week_date = start_end_date(date_value, key)
    #                 template_obj.start_date = start_month_date
    #                 template_obj.end_date = end_month_date
    #                 template_obj.initial_amount = 200
    #                 template_obj.amount = 200
    #                 template_obj.budget_spent = 150
    #                 template_obj.budget_left = 50
    #                 template_obj.created_at = start_week_date
    #                 template_obj.ended_at = end_week_date
    #                 template_obj.save()
    #
    #             if key == 'Daily':
    #                 template_obj.start_date = start_month_date
    #                 template_obj.end_date = end_month_date
    #                 template_obj.initial_amount = 100
    #                 template_obj.amount = 100
    #                 template_obj.budget_spent = 120
    #                 template_obj.budget_left = -20
    #                 template_obj.created_at = date_value
    #                 template_obj.ended_at = date_value
    #                 template_obj.save()
    #
    #         if next:
    #             return redirect(next)
    #         else:
    #             return redirect('/')
    # else:
    #     try:
    #         next = request.GET['next']
    #     except:
    #         next = None
    #     return render(request, "login_page.html", context={'next': next})
    context = {}
    if request.method == "POST":
        username = request.POST['register-username']
        user_password = request.POST['register-password']
        search_api_url = f"https://tradingtech.org/wp-content/plugins/indeed-membership-pro/apigate.php?ihch={wordpress_api_key}&action=search_users&term_name=user_login&term_value={username}"
        try:
            api_response = requests.get(search_api_url)
            search_api_data = api_response.json()
        except:
            context['login_error'] = 'User data not accessed. Something Went Wrong!!'
            return render(request, "login_page.html", context=context)

        user_details = ""
        user = authenticate(username=username, password=user_password)
        if user:
            if user.is_superuser:
                login(request, user)
                try:
                    redirect_url = request.POST['redirect_url']
                    return redirect(redirect_url)
                except:
                    return redirect("/")

        for data in search_api_data['response']:
            user_api_url = f"https://tradingtech.org/wp-content/plugins/indeed-membership-pro/apigate.php?ihch=z16E04BIOod7A1RqYcGaPPtjua7Jbfo1zKt&action=user_get_details&uid={data['ID']}"
            print(user_api_url)
            user_api_response = requests.get(user_api_url)
            user_data = user_api_response.json()['response']
            print(user_password)
            print(user_data['user_pass'])
            print(username)

            if user_data['user_login'] == username and user_data['user_pass'] == user_password:
                if user:
                    login(request, user)
                else:
                    try:
                        user = User.objects.get(username=username)
                        user.set_password(user_password)
                        user.first_name = user_data['user_nicename']
                        user.email = user_data['user_email']
                        user.save()
                    except:
                        user = User.objects.create_user(username, user_data['user_email'], user_password)
                        user.first_name = user_data['user_nicename']
                        user.save()
                    login(request, user)
                try:
                    redirect_url = request.POST['redirect_url']
                    return redirect(redirect_url)
                except:
                    return redirect("/")
            else:
                user_details = "False"
        if user_details == "False":
            context['login_error'] = 'Username and Password Incorrect'
            return render(request, "login_page.html", context=context)
    else:
        try:
            context['redirect_url'] = request.GET['next']
        except:
            pass

        return render(request, "login_page.html", context=context)


@login_required(login_url="/login")
def user_logout(request):
    logout(request)
    return redirect('/login')


def make_budgets_values(user_name, budget_data, page_method):
    total_budget = 0
    total_spent = 0
    total_left = 0
    spent_data = []
    left_data = []
    budget_names_list = []
    over_spent_data = []
    all_budgets = []
    if budget_data:
        print("innnnnnnnnnnnnnnn", budget_data, user_name)
        for data in budget_data:
            budget_create_date = data.created_at
            budget_end_date = data.ended_at
            budget_amount = float(data.amount)
            spent_amount = float(data.budget_spent)
            left_amount = float(data.budget_left)
            budget_names_list.append(data.name)
            if budget_create_date:
                budget_start_date = datetime.datetime.strftime(budget_create_date, "%b %d, %Y")
                budget_end_date = datetime.datetime.strftime(budget_end_date, "%b %d, %Y")
            else:
                budget_start_date = False
                budget_end_date = False

            if spent_amount > budget_amount:
                over_spent_data.append(spent_amount - budget_amount)
                left_data.append(0)
                spent_data.append(budget_amount)
            else:
                over_spent_data.append(0)
                left_data.append(left_amount)
                spent_data.append(spent_amount)

            budget_value = [data.name, budget_amount, spent_amount, left_amount, data.id, data.budget_period,
                            budget_start_date, budget_end_date]
            all_budgets.append(budget_value)
            total_budget += budget_amount
            total_spent += spent_amount
            total_left += left_amount
            budget_currency = data.currency

        if page_method == "budget_page":
            earliest = Budget.objects.filter(user=user_name, start_date__isnull=False).order_by('start_date')
        else:
            earliest = TemplateBudget.objects.filter(user=user_name, start_date__isnull=False).order_by('start_date')

        start, end = earliest[0].start_date, earliest[len(earliest) - 1].start_date
        list_of_months = list(OrderedDict(
            ((start + datetime.timedelta(_)).strftime("%b-%Y"), None) for _ in range((end - start).days + 1)).keys())
        budget_values = [total_spent, total_left]
    else:
        list_of_months = []
        budget_values = []
        budget_currency = None

    budget_graph_data = [{'name': 'Spent', 'data': spent_data},
                         {'name': 'Left', 'data': left_data},
                         {'name': 'OverSpent', 'data': over_spent_data}]

    return all_budgets, budget_graph_data, budget_values, budget_currency, list_of_months, budget_names_list


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

    budget_data = Budget.objects.filter(user=user_name, start_date=start_date, end_date=end_date)
    print(budget_data)
    template_budget_data = TemplateBudget.objects.filter(user=user_name, start_date=start_date, end_date=end_date)
    budget_key = ['Name', 'budgeted', 'Spent', 'Left']
    budget_label = ['Total Spent', 'Total Left']
    all_budgets, budget_graph_data, budget_values, budget_currency, list_of_months, budget_names_list = make_budgets_values(
        user_name, budget_data, "budget_page")
    template_all_budgets, template_budget_graph_data, template_budget_values, template_budget_currency, \
    template_list_of_months, template_budget_names_list = make_budgets_values(user_name, template_budget_data,
                                                                              "template_page")

    # COMPARE BUDGETS :-

    current_date = datetime.datetime.today().date()
    week_start, week_end = start_end_date(current_date, "Weekly")
    month_start, month_end = start_end_date(current_date, "Monthly")
    quart_end, quart_start = start_end_date(current_date, "Quarterly")
    yearly_start, yearly_end = start_end_date(current_date, "Yearly")
    monthly_budget_transaction_data, cmp_month_list, monthly_cmp_budgets_dict, monthly_cmp_transaction_budgets = compare_budgets(
        user_name, month_start, month_end, budget_names_list)
    week_budget_transaction_data, cmp_week_list, week_cmp_budgets_dict, week_cmp_transaction_budgets = compare_budgets(
        user_name, week_start, week_end, budget_names_list)
    quart_budget_transaction_data, cmp_quart_list, quart_cmp_budgets_dict, quart_cmp_transaction_budgets = compare_budgets(
        user_name, quart_start, quart_end, budget_names_list)
    yearly_budget_transaction_data, cmp_yearly_list, yearly_cmp_budgets_dict, yearly_cmp_transaction_budgets = compare_budgets(
        user_name, yearly_start, yearly_end, budget_names_list)

    revenue_values = []
    revenue_data = Revenues.objects.filter(user=user_name)
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
    currency_name = "$"
    non_primary_dict = {}
    index = 1
    for month_name in revenue_month[::-1]:
        obj_data = {'S.No.': index, 'month': datetime.datetime.strftime(month_name, "%B, %y")}
        index += 1
        for name in revenue_name:
            revenue_obj = Revenues.objects.filter(user=user_name, month=month_name, name=name)
            if revenue_obj:
                currency_name = revenue_obj[0].currency
                obj_data[revenue_obj[0].id] = revenue_obj[0].currency + revenue_obj[0].amount
                if revenue_obj[0].non_primary:
                    non_primary_amount = float(revenue_obj[0].amount)
                    if name in non_primary_dict:
                        non_primary_dict[name] += non_primary_amount
                    else:
                        non_primary_dict[name] = non_primary_amount
            else:
                new_revenue_obj = Revenues()
                new_revenue_obj.non_primary = True
                revenue_save(new_revenue_obj, user_name, name, "0", month_name, currency_name)
                obj_data[new_revenue_obj.id] = currency_name + "0"
        revenue_values.append(obj_data)

    expenses_data = Expenses.objects.filter(user=user_name)
    non_primary_label = list(non_primary_dict.keys())
    non_primary_value = list(non_primary_dict.values())
    revenue_name.insert(0, 'S.NO')
    revenue_name.insert(1, 'Month')
    if not budget_names_list:
        budget_page = ""
        template_page = "active"

    context = {'all_budgets': all_budgets, 'budget_graph_data': budget_graph_data, 'budget_names': budget_names_list,
               'list_of_months': list_of_months, "budget_graph_value": budget_values,
               "budget_graph_currency": budget_currency, "budget_bar_id": "#budgets-bar",
               "template_budget_bar_id": "#template-budgets-bar", "template_budget_graph_id": "#template_total_budget",
               'template_all_budgets': template_all_budgets, 'template_budget_graph_data': template_budget_graph_data,
               'template_budget_names': template_budget_names_list, 'template_list_of_months': template_list_of_months,
               "template_budget_graph_value": template_budget_values,
               "template_budget_graph_currency": template_budget_currency, 'budget_key': budget_key,
               'budget_key_dumbs': json.dumps(budget_key),
               'revenue_keys': revenue_name, 'graph_label': non_primary_label, 'graph_value': non_primary_value,
               'graph_currency': currency_name, "graph_id": "#budget-chart", 'revenue_values': revenue_values,
               'expenses_data': expenses_data,
               "current_month": current_month, "budget_graph_label": budget_label,
               "budget_graph_value": budget_values,
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
               "cmp_yearly_list_id": "#cmp_yearly_list", "budget_page": budget_page, "template_page": template_page
               }
    return context


@login_required(login_url="/login")
def budget_list(request):
    context = budgets_page_data(request, "active", "")
    return render(request, 'budget/budget_list.html', context=context)


@login_required(login_url="/login")
def budget_details(request, pk):
    user_name = request.user
    budget_obj = Budget.objects.get(pk=pk)
    transaction_key = ['S.No.', 'Date', 'Amount', 'Payee', 'Account', 'Categories', 'Bill', 'Budget', 'Cleared']

    if request.method == "POST":
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        transaction_data = Transaction.objects.filter(user=user_name, budgets=budget_obj,
                                                      transaction_date__range=(start_date, end_date)).order_by(
            'transaction_date')
    else:
        start_date = False
        end_date = False
        transaction_data = Transaction.objects.filter(user=user_name, budgets=budget_obj).order_by('transaction_date')
    context = {
        'budget_obj': budget_obj, 'budget_transaction_data': transaction_data,
        'transaction_key': transaction_key, 'transaction_key_dumbs': json.dumps(transaction_key),
        'start_date': start_date, 'end_date': end_date
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

        if budget_period == 'Monthly':
            obj.start_date = start_month_date
            obj.end_date = end_month_date
            obj.initial_amount = budget_amount
            obj.budget_left = budget_amount
            obj.created_at = start_month_date
            obj.ended_at = end_month_date
            obj.save()

        if budget_period == 'Weekly':
            start_week_date, end_week_date = start_end_date(date_value, budget_period)
            obj.start_date = start_month_date
            obj.end_date = end_month_date
            obj.initial_amount = budget_amount
            obj.budget_left = budget_amount
            obj.created_at = start_week_date
            obj.ended_at = end_week_date
            obj.save()

        if budget_period == 'Daily':
            obj.start_date = start_month_date
            obj.end_date = end_month_date
            obj.initial_amount = budget_amount
            obj.budget_left = budget_amount
            obj.created_at = date_value
            obj.ended_at = date_value
            obj.save()

        if budget_period == 'Yearly':
            start_year_date, end_year_date = start_end_date(date_value, budget_period)
            year_list = list(OrderedDict(((start_year_date + datetime.timedelta(_)).replace(day=1), None) for _ in
                                         range((end_year_date - start_year_date).days + 1)).keys())
            year_list = list(dict.fromkeys(year_list))
            make_month_obj(obj, user_name, year_list, start_year_date, end_year_date, budget_name,
                           budget_period, budget_currency, budget_amount, budget_auto)

        if budget_period == 'Quarterly':
            upcoming_quarter_date, quarter_value = start_end_date(date_value, budget_period)
            quarter_list = list(OrderedDict(((quarter_value + datetime.timedelta(_)).replace(day=1), None) for _ in
                                            range((upcoming_quarter_date - quarter_value).days + 1)).keys())
            quarter_list = list(dict.fromkeys(quarter_list))
            make_month_obj(obj, user_name, quarter_list, quarter_value, upcoming_quarter_date, budget_name,
                           budget_period, budget_currency, budget_amount, budget_auto)

        add_remains_budget(user_name)
        return super().form_valid(form)


class BudgetUpdate(LoginRequiredMixin, UpdateView):
    model = Budget
    form_class = BudgetForm
    template_name = 'budget/budget_update.html'

    def form_valid(self, form):
        user_name = self.request.user
        budget_obj = Budget.objects.get(user=user_name, pk=self.kwargs['pk'])
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
        budgets_data = Budget.objects.filter(user=user_name, name=budget_obj.name, created_at=budget_obj.created_at,
                                             ended_at=budget_obj.ended_at)
        for data in budgets_data:
            if data != budget_obj:
                data.amount = update_amount
                data.budget_left = float(budget_obj.budget_left) + extra_amount
                data.save()

        return super().form_valid(form)


class BudgetDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        budget_obj = Budget.objects.get(pk=self.kwargs['pk'])
        user_name = self.request.user
        all_obj = Budget.objects.filter(user=user_name, name=budget_obj.name)
        for budget_data in all_obj:
            budget_data.delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


@login_required(login_url="/login")
def template_budget_list(request):
    context = budgets_page_data(request, "", "active")
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


@login_required(login_url="/login")
def transaction_list(request):
    user_name = request.user
    if request.method == "POST":
        tag_name = request.POST['tag_name']
        tags_data = request.POST['tags_data']
        print("tags_data", tags_data)
        if tag_name != 'All':
            transaction_data = Transaction.objects.filter(user=user_name, tags=tag_name).order_by('transaction_date')
        else:
            transaction_data = Transaction.objects.filter(user=user_name).order_by('transaction_date')
        select_filter = tag_name
    else:
        transaction_data = Transaction.objects.filter(user=user_name).order_by('transaction_date')
        select_filter = 'All'

    context = transaction_summary(transaction_data, select_filter)
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
        if tag_name != 'All':
            transaction_data = Transaction.objects.filter(user=user_name,
                                                          transaction_date__range=(start_date, end_date),
                                                          tags=tag_name).order_by('transaction_date')
        else:
            transaction_data = Transaction.objects.filter(user=user_name,
                                                          transaction_date__range=(start_date, end_date)).order_by(
                'transaction_date')
        select_filter = tag_name
    else:
        start_date = request.GET['start_date']
        end_date = request.GET['end_date']
        if start_date != "" and end_date != "":
            transaction_data = Transaction.objects.filter(user=user_name,
                                                          transaction_date__range=(start_date, end_date)).order_by(
                'transaction_date')
            select_filter = 'All'
        else:
            return redirect("/transaction_list/")

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

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        user_name = self.request.user
        data = super(TransactionAdd, self).get_context_data(**kwargs)
        data['budgets_name'] = get_budgets(user_name)

        return data

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
        budget_name = self.request.POST['budget_name']
        transaction_date = form.cleaned_data.get('transaction_date')
        account = account.name
        account_obj, budget_obj = transaction_checks(user_name, transaction_amount, account, bill_name,
                                                     budget_name, cleared_amount, out_flow, transaction_date)
        obj.remaining_amount = account_obj.available_balance
        if budget_obj:
            obj.budgets = budget_obj
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
        try:
            select_budget_name = transaction_obj.budgets.name
        except:
            select_budget_name = "Select Budget"
        data['budgets_name'] = get_budgets(user_name)
        data['select_name'] = select_budget_name

        return data

    def form_valid(self, form):
        transaction_obj = Transaction.objects.get(pk=self.kwargs['pk'])
        obj = form.save(commit=False)
        account = transaction_obj.account.name.title()
        user_name = self.request.user
        transaction_amount = round(float(transaction_obj.amount), 2)
        transaction_out_flow = transaction_obj.out_flow
        print("transaction_out_flow======>", transaction_out_flow)
        print("transaction_amount======>", transaction_amount)
        update_account = form.cleaned_data.get('account').name.title()
        update_transaction_amount = round(float(form.cleaned_data.get('amount')), 2)
        out_flow = form.cleaned_data.get('out_flow')
        cleared_amount = form.cleaned_data.get('cleared')
        bill_name = form.cleaned_data.get('bill')
        budget_name = self.request.POST['budget_name']
        transaction_date = form.cleaned_data.get('transaction_date')

        print(out_flow)
        print("out_flow======>", type(out_flow))

        if cleared_amount == "True":
            if account == update_account:
                account_obj = Account.objects.get(user=user_name, name=account)
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
                old_account_obj = Account.objects.get(user=user_name, name=account)
                account_obj = Account.objects.get(user=user_name, name=update_account)

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

            if bill_name:
                bill_name = bill_name.label
                bill_obj = Bill.objects.filter(user=user_name, label=bill_name)[0]
            else:
                bill_obj = False

            if bill_obj:
                transaction_bill_name = transaction_obj.bill
                bill_obj_amount = round(float(bill_obj.amount), 2)
                if transaction_bill_name == bill_name:
                    if transaction_amount != update_transaction_amount:
                        bill_obj_amount = bill_obj_amount + transaction_amount
                else:
                    old_bill_obj = Bill.objects.filter(user=user_name, label=transaction_bill_name)
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
                date_check = datetime.datetime.strptime(transaction_date, "%Y-%m-%d").date()
                start_month_date, end_month_date = start_end_date(date_check, "Monthly")
                budget_obj = Budget.objects.filter(user=user_name, name=budget_name, start_date=start_month_date,
                                                   end_date=end_month_date)[0]
            else:
                try:
                    transaction_budget_name = transaction_obj.budgets.name
                    transaction_start_date, transaction_end_date = start_end_date(transaction_obj.transaction_date,
                                                                                  "Monthly")

                    budget_obj = Budget.objects.filter(user=user_name, name=transaction_budget_name,
                                                       start_date=transaction_start_date,
                                                       end_date=transaction_end_date)[0]

                    budget_obj = update_budget_items(user_name, budget_obj, transaction_amount, transaction_out_flow)
                    budget_obj.save()

                    budget_obj = None
                except:
                    budget_obj = None

            if budget_obj:
                try:
                    transaction_budget_name = transaction_obj.budgets.name
                    transaction_start_date, transaction_end_date = start_end_date(transaction_obj.transaction_date,
                                                                                  "Monthly")
                    if transaction_budget_name == budget_name:
                        if out_flow != transaction_out_flow or transaction_amount != update_transaction_amount:
                            budget_obj = update_budget_items(user_name, budget_obj, transaction_amount,
                                                             transaction_out_flow)
                            budget_obj = add_new_budget_items(user_name, budget_obj, update_transaction_amount,
                                                              out_flow)
                    else:
                        old_budget_obj = Budget.objects.get(user=user_name, name=transaction_budget_name,
                                                            start_date=transaction_start_date,
                                                            end_date=transaction_end_date)
                        old_budget_obj = update_budget_items(user_name, old_budget_obj, transaction_amount,
                                                             transaction_out_flow)
                        old_budget_obj.save()
                        budget_obj = add_new_budget_items(user_name, budget_obj, update_transaction_amount, out_flow)
                except:
                    budget_obj = add_new_budget_items(user_name, budget_obj, update_transaction_amount, out_flow)
                budget_obj.save()

            obj.budgets = budget_obj
        return super().form_valid(form)


class TransactionDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        user_name = self.request.user
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

        if cleared_amount:
            account_obj = Account.objects.get(user=user_name, name=account.name)

            if bill_name:
                bill_name = bill_name.label
                bill_obj = Bill.objects.filter(user=user_name, label=bill_name)[0]
                if out_flow:
                    bill_obj.amount = round(float(bill_obj.amount) + transaction_amount, 2)
                else:
                    bill_obj.amount = round(float(bill_obj.amount) - transaction_amount, 2)

                bill_obj.amount = bill_obj.amount
                bill_obj.save()

            if budget_name:
                budget_obj = update_budget_items(user_name, budget_name, transaction_amount, out_flow)
                budget_obj.save()

            if out_flow:
                account_obj.available_balance = round(float(account_obj.available_balance) + transaction_amount, 2)
            else:
                account_obj.available_balance = round(float(account_obj.available_balance) - transaction_amount, 2)

            account_obj.transaction_count -= 1
            account_obj.save()

        transaction_obj.delete()
        return JsonResponse({"status": "Successfully", "path": "None"})


def calculate_available_lock_amount(user_name, account_obj):
    fund_data = AvailableFunds.objects.filter(user=user_name, account=account_obj).order_by('created_at')[::-1]
    if fund_data:
        lock_amount = fund_data[0].lock_fund
    goal_data = Goal.objects.filter(user=user_name, account=account_obj)
    total_allocate_amount = 0
    for data in goal_data:
        total_allocate_amount += float(data.allocate_amount)

    available_lock_amount = float(lock_amount) - total_allocate_amount
    return available_lock_amount


@login_required(login_url="/login")
def goal_obj_save(request, goal_obj, user_name, fun_name=None):
    label = request.POST['label']
    goal_amount = request.POST['goal_amount']
    currency = request.POST['currency']
    goal_date = request.POST['goal_date']
    account_name = request.POST['account_name']
    allocate_amount = request.POST['allocate_amount']
    account_obj = Account.objects.get(name=account_name)
    available_lock_amount = calculate_available_lock_amount(user_name, account_obj)
    if float(allocate_amount) > available_lock_amount:
        context = {'currency_dict': currency_dict, 'error': 'Lock Amount Insufficient Please Add More..'}
        if fun_name:
            print("fun_name")
            return render(request, 'goal/goal_update.html', context=context)
        else:
            print("fun_name====>", context)
            return render(request, 'goal/goal_add.html', context=context)
    else:
        goal_obj.user = user_name
        goal_obj.account = account_obj
        goal_obj.goal_amount = goal_amount
        goal_obj.currency = currency
        goal_obj.goal_date = goal_date
        goal_obj.label = label
        goal_obj.allocate_amount = allocate_amount
        goal_obj.save()
        return redirect("/goal_list")


class GoalList(LoginRequiredMixin, ListView):
    model = Goal
    template_name = 'goal/goal_list.html'

    def get_context_data(self, **kwargs):
        # self.request = kwargs.pop('request')
        data = super(GoalList, self).get_context_data(**kwargs)
        user_name = self.request.user
        goal_data = Goal.objects.filter(user=user_name)
        fund_value = show_current_funds(user_name, fun_name='goal_funds')
        fund_key = ['S.No.', 'See Overtime Graph', 'Account Name', 'Total Fund', 'Lock Fund', 'Available Lock fund',
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
    if request.method == 'POST':
        goal_obj = Goal()
        return goal_obj_save(request, goal_obj, user_name)

    else:
        account_data = Account.objects.filter(user=user_name)
        context = {'currency_dict': currency_dict, 'account_data': account_data}
        return render(request, 'goal/goal_add.html', context=context)


@login_required(login_url="/login")
def goal_update(request, pk):
    user_name = request.user
    goal_data = Goal.objects.get(pk=pk)
    if request.method == 'POST':
        return goal_obj_save(request, goal_data, user_name, fun_name='goal_update')
    else:
        goal_date = datetime.datetime.strftime(goal_data.goal_date, '%Y-%m-%d')
        account_data = Account.objects.filter(user=user_name)
        context = {'goal_data': goal_data, 'currency_dict': currency_dict, 'goal_date': goal_date,
                   'account_data': account_data}
        return render(request, 'goal/goal_update.html', context=context)


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
        print("total Balance", total_balance)
        lock_amount = form.cleaned_data.get('lock_amount')
        lock_check = form.cleaned_data.get('lock_check')
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

        fund_obj = AvailableFunds()
        fund_obj.user = self.request.user
        fund_obj.account = obj
        fund_obj.lock_fund = lock_amount
        fund_obj.total_fund = total_balance
        fund_obj.save()

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
                fund_value.append(
                    [fund_obj.account.name, fund_obj.total_fund, fund_obj.lock_fund, available_lock_amount,
                     obj.available_balance, fund_obj.id])
            else:
                fund_value.append([fund_obj.account.name, fund_obj.total_fund, fund_obj.lock_fund,
                                   obj.available_balance, fund_obj.id])

    return fund_value


class FundList(LoginRequiredMixin, ListView):
    model = AvailableFunds
    template_name = 'funds/funds_list.html'

    def get_context_data(self, **kwargs):
        data = super(FundList, self).get_context_data(**kwargs)
        user_name = self.request.user
        fund_value = show_current_funds(user_name)
        fund_key = ['S.No.', 'See Overtime Graph', 'Account Name', 'Total Fund', 'Lock Fund', 'Available Fund',
                    'Action']
        data['fund_key'] = fund_key
        data['fund_value'] = fund_value
        return data


@login_required(login_url="/login")
def fund_overtime(request):
    if request.method == 'POST' and request.is_ajax():
        user_name = request.user
        account_name = request.POST['account_name']
        account_data = Account.objects.get(user=user_name, name=account_name)
        transaction_data = Transaction.objects.filter(user=user_name, account=account_data)
        account_min_date = account_data.created_at.date()
        print(transaction_data)
        if transaction_data:
            transaction_min_date = transaction_data[0].transaction_date
            if transaction_min_date <= account_min_date:
                min_date = transaction_min_date
            else:
                min_date = account_min_date
        else:
            min_date = account_min_date
        max_date = datetime.datetime.today().date()
        day_diff = (max_date - min_date).days
        account_date_list = [str(max_date - datetime.timedelta(days=x)) for x in range(day_diff)]
        account_date_list.append(str(min_date))
        account_date_list = account_date_list[::-1]
        print("account_date_list=======>", account_date_list)
        total_fund_data = []
        lock_fund_data = []
        fund_graph_data = []
        initial_fund = AvailableFunds.objects.filter(user=user_name, account=account_data)[0]
        total_fund = float(initial_fund.total_fund)
        lock_fund = float(initial_fund.lock_fund)
        account_transaction_value = []
        acc_create_date = account_data.created_at.date()
        amount_date_dict = {}
        if account_data.lock_amount:
            acc_current_balance = float(account_data.balance) - float(account_data.lock_amount)
        else:
            acc_current_balance = float(account_data.balance)

        acc_available_balance = float(acc_current_balance)
        acc_transaction_data = Transaction.objects.filter(user=user_name, account=account_data).order_by(
            'transaction_date')
        multi_acc_chart(acc_transaction_data, amount_date_dict, acc_current_balance, account_date_list,
                        acc_create_date, account_transaction_value, acc_available_balance)
        print("account_transaction_value", account_transaction_value)
        for name in account_date_list:
            check_date = datetime.datetime.strptime(name, '%Y-%m-%d').date()
            fund_data = AvailableFunds.objects.filter(user=user_name, account=account_data, created_at=check_date)
            print(fund_data)
            if fund_data:
                for fund_value in fund_data:
                    total_fund = float(fund_value.total_fund)
                    lock_fund = float(fund_value.lock_fund)
                total_fund_data.append(round(total_fund, 2))
                lock_fund_data.append(round(lock_fund, 2))

            else:
                total_fund_data.append(total_fund)
                lock_fund_data.append(lock_fund)

        result_list = total_fund_data + lock_fund_data + account_transaction_value
        max_value = max(result_list)
        min_value = min(result_list)
        fund_graph_data.append({'label_name': 'Total Fund', 'data_value': total_fund_data})
        fund_graph_data.append({'label_name': 'Lock Fund', 'data_value': lock_fund_data})
        fund_graph_data.append({'label_name': 'Available Fund', 'data_value': account_transaction_value})

    return JsonResponse({'fund_data': fund_graph_data, 'date_range_list': account_date_list,
                         'max_value': max_value, 'min_value': min_value})


@login_required(login_url="/login")
def fund_update(request, pk):
    fund_obj = AvailableFunds.objects.get(pk=pk)
    total_fund = float(fund_obj.total_fund)
    lock_fund = float(fund_obj.lock_fund)
    if request.method == 'POST':
        user_name = request.user
        update_total_fund = float(request.POST['total_fund'])
        update_lock_fund = float(request.POST['lock_fund'])
        if update_total_fund < total_fund:
            context = {'fund_obj': fund_obj, 'error': 'Please Enter Total Fund Greater Than Current Total Fund'}
        else:
            if update_total_fund == total_fund and update_lock_fund == lock_fund:
                context = {'fund_obj': fund_obj}
            else:
                current_balance = float(fund_obj.account.available_balance)
                account_obj = Account.objects.get(name=fund_obj.account.name)
                new_fund_obj = AvailableFunds()
                new_fund_obj.user = fund_obj.user
                new_fund_obj.account = account_obj
                new_fund_obj.lock_fund = update_lock_fund
                new_fund_obj.total_fund = update_total_fund
                new_fund_obj.save()
                transaction_obj = Transaction()
                try:
                    category_obj = Category.objects.get(user=user_name, name='Funds')
                except:
                    category_obj = Category()
                    category_obj.user = user_name
                    category_obj.name = 'Funds'
                    category_obj.save()

                transaction_obj.user = user_name
                transaction_obj.remaining_amount = current_balance
                transaction_obj.transaction_date = datetime.datetime.today().date()
                transaction_obj.categories = category_obj
                transaction_obj.account = account_obj
                transaction_obj.payee = 'Self'
                transaction_obj.tags = 'Funds'
                transaction_obj.cleared = True

                if update_total_fund != total_fund:
                    new_fund_amount = update_total_fund - total_fund
                    transaction_obj.amount = new_fund_amount
                    transaction_obj.out_flow = False
                    account_obj.available_balance = round(current_balance + new_fund_amount, 2)
                    account_obj.save()
                    transaction_obj.save()
                    return redirect("/funds_list")
                elif update_lock_fund > lock_fund:
                    new_fund_amount = update_lock_fund - lock_fund
                    account_obj.available_balance = round(current_balance - new_fund_amount, 2)
                    transaction_obj.amount = new_fund_amount
                    transaction_obj.out_flow = True
                    account_obj.save()
                    transaction_obj.save()
                    return redirect("/funds_list")
                else:
                    context = {'fund_obj': fund_obj, 'error': 'Please Enter Lock Fund Greater Than Current Lock Fund'}
    else:
        context = {'fund_obj': fund_obj}

    return render(request, 'funds/funds_update.html', context=context)


# class FundUpdate(UpdateView):
#     model = AvailableFunds
#     form_class = FundForm
#     template_name = 'funds/funds_update.html'


# BILL VIEWS

@login_required(login_url="/login")
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


@login_required(login_url="/login")
def bill_detail(request, pk):
    bill_obj = Bill.objects.get(pk=pk)
    transaction_data = Transaction.objects.filter(bill=bill_obj)
    context = {"bill_data": bill_obj, 'transaction_data': transaction_data}
    return render(request, "bill/bill_detail.html", context)


@login_required(login_url="/login")
def bill_add(request):
    form = BillForm(request.POST or None)
    error = ''
    if form.is_valid():
        label = form.cleaned_data.get('label').title()
        amount = form.cleaned_data.get('amount')
        bill_date = form.cleaned_data.get('date')
        frequency = form.cleaned_data.get('frequency')
        currency = form.cleaned_data.get('currency')

        check_bill_obj = Bill.objects.filter(user=request.user, label=label, currency=currency)
        if check_bill_obj:
            error = 'Bill Already Added!!'
        else:
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
        'form': form,
        'error': error
    }
    return render(request, "bill/bill_add.html", context=context)


@login_required(login_url="/login")
def bill_update(request, pk):
    bill_obj = Bill.objects.get(pk=pk)
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


@login_required(login_url="/login")
def bill_delete(request, pk):
    bill_obj = Bill.objects.get(pk=pk)
    bill_obj.delete()
    return JsonResponse({"status": "Successfully", "path": "/bill_list/"})


@login_required(login_url="/login")
def bill_automatic_amount(request):
    bill_id = request.POST['bill_id']
    bill_obj = Bill.objects.get(pk=bill_id)
    return JsonResponse({'bill_amount': bill_obj.remaining_amount})


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
        amount = form.cleaned_data.get('amount')
        interest = form.cleaned_data.get('interest')
        tenure = form.cleaned_data.get('tenure')
        mortgage_date = form.cleaned_data.get('mortgage_date')
        table = calculator(amount, interest, tenure)
        total_payment = abs(table['principle'].sum() + table['interest'].sum())
        total_month = tenure * 12
        json_records = table.reset_index().to_json(orient='records')
        data = json.loads(json_records)
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
            'mortgage_key_dumbs': json.dumps(mortgage_key),
            'mortgage_graph_data': mortgage_graph_data,
            'mortgage_date_data': mortgage_date_data
        }
        return render(request, 'mortgagecalculator_add.html', context)

    context = {
        'form': form
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
    monthly_payment = data[0]['principle'] + data[0]['interest']
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
        investor_contribution = round(float(units) / total_investor_contributions * 100, 2)
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

        expenses_ratio = round(total_expense / total_revenue * 100, 2)
        cash_flow_value = total_revenue - total_expense - (monthly_payment * 12)
        cash_return_value = cash_flow_value / total_investement * 100
        income_value = round(total_revenue - total_expense, 2)
        debt_value = round(income_value / (monthly_payment * 12), 2)
        net_income_value = round(income_value - mortgage_interest, 2)
        roi_value = round(cash_flow_value + mortgage_principle, 2)
        roi_p_value = round(roi_value / total_investement * 100, 2)
        roi_with_appreciation_value = round(roi_value + appreciation_assumption_value, 2)
        roi_p_with_appreciation_value = round(roi_with_appreciation_value / total_investement * 100, 2)
        cap_rate_value = round(income_value / selected_price * 100, 2)
        cap_rate_include_closing_cost_value = round(income_value / all_investment * 100, 2)

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
                              {'name': 'Net Operating Income(NOI)', 'data': [x[1:] for x in net_operating_income_list]},
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
        'investment_data_dumbs': json.dumps(investment_data), "projection_value_dumbs": json.dumps(projection_value),
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
        try:
            property_image = request.FILES['file']
        except:
            property_image = ""
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
        context = {
            'currency_dict': currency_dict,
            'scenario_dict': scenario_dict,
            'action_url': "/rental_property_add/",
            'heading_name': "Add Rental Property",
            'heading_url': "Add Property",
            'property_url': "/rental_property_list/",

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
                   'property_url': "/rental_property_detail/{pk}",
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
    url = "https://stock.tradingtech.org/api/portfolio/list/"
    portfolio_response = requests.get(url, data={'user_name': request.user.username}, timeout=500)
    portfolio_list = portfolio_response.json()

    if request.method == 'POST':
        p_name = request.POST['p_name']
    else:
        p_name = portfolio_list[0]

    my_portfolio_url = "https://stock.tradingtech.org/api/my_portfolio/list/"
    url_response = requests.post(my_portfolio_url, data={'user_name': request.user.username, 'p_name': p_name},
                                 timeout=500)
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


@login_required(login_url="/login")
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
                months_list = list(OrderedDict(((month + datetime.timedelta(_)).strftime(r"%b-%y"), None) for _ in
                                               range((today_month - month).days + 1)).keys())
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

@login_required(login_url="/login")
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

@login_required(login_url="/login")
def revenue_delete(request):
    return render(request, "revenue/revenue_add.html")


@login_required(login_url="/login")
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


def delete_expense(request, pk):
    expense_obj = PropertyExpense.objects.get(pk=pk)
    expense_obj.delete()
    return JsonResponse({"status": "Successfully", "path": "/property/expense/list/"})


# Income & Invoices


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

    return render(request, "property_invoice/property_invoice_add.html",  context=context)


def property_invoice_list(request, property_name, unit_name):
    user_name = request.user
    invoice_details = PropertyInvoice.objects.filter(user=user_name, property_details__property_name=property_name,
                                                     unit_name=unit_name).order_by('invoice_due_date')

    invoice_key = ['Invoice Id', 'Due on', 'Paid on', 'Amount', 'Paid', 'Balance', 'Status']
    context = {'invoice_details': invoice_details, 'property_name': property_name, 'unit_name': unit_name,
               'invoice_key': invoice_key, 'invoice_key_dumps': json.dumps(invoice_key)
               }
    return render(request, "property_invoice/property_invoice_list.html", context=context)


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


def property_invoice_update(request, pk):
    user_name = request.user
    invoice_obj = PropertyInvoice.objects.get(user=user_name, pk=pk)
    context = {'invoice_obj': invoice_obj}
    return render(request, "property_invoice/property_invoice_update.html", context=context)


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


def delete_invoice_payment(request, pk, payment_index, paid_amount):
    paid_amount = float(paid_amount)
    redirect_url = record_payment_save(request, pk, 'delete_payment', paid_amount, payment_index)
    return redirect(redirect_url)


def property_invoice_payment(request, pk):
    paid_amount = float(request.POST['paid_amount'])
    redirect_url = record_payment_save(request, pk, 'record_payment', paid_amount)
    return redirect(redirect_url)


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


def property_info(request):
    if request.method == 'POST' and request.is_ajax():
        property_name = request.POST['property_name']
        user_name = request.user
        unit_list, tenant_dict, currency_symbol = get_units(user_name, property_name)
        return JsonResponse({'unit_list': unit_list, 'tenant_dict': tenant_dict, 'currency_symbol': currency_symbol})

