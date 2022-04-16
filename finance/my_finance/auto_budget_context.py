from my_finance.views import start_end_date, add_remains_budget, save_budgets
from .models import Budget, Bill, Revenues
from datetime import datetime, timedelta
import calendar
from collections import OrderedDict


def budgets_save(user_name, start_date, end_date, budget_name, budget_period, budget_currency, budget_amount,
                 budget_auto, create_date, ended_date, initial_amount):
    budget_data = Budget.objects.filter(user=user_name, name=budget_name, start_date=start_date, end_date=end_date)
    if budget_data:
        data_obj = budget_data[0]
        data_obj.amount = budget_amount
        data_obj.budget_spent = 0
        data_obj.budget_left = budget_amount
        data_obj.created_at = create_date
        data_obj.ended_at = ended_date
        data_obj.save()

    else:
        save_budgets(user_name, start_date, end_date, budget_name, budget_period, budget_currency, budget_amount,
                     budget_auto, create_date, ended_date, initial_amount)


def auto_month_obj(user_name, quarter_list, quarter_value, upcoming_quarter_date, budget_name, budget_period, budget_currency,
                   budget_amount, budget_auto, initial_amount):
    for month_date in quarter_list:
        start_date = month_date
        end_date = month_date.replace(day=calendar.monthrange(month_date.year, month_date.month)[1])
        budgets_save(user_name, start_date, end_date, budget_name, budget_period, budget_currency, budget_amount,
                     budget_auto, quarter_value, upcoming_quarter_date, initial_amount)


def check_frequency_date(period, start_date):
    if period == "Daily":
        end_date = start_date + timedelta(days=1)

    if period == "Weekly":
        end_date = start_date + timedelta(days=7)

    if period == "Monthly":
        month_days = calendar.monthrange(start_date.year, start_date.month)[1]
        print("month_days====>", month_days)
        end_date = start_date + timedelta(days=month_days)

    if period == "Quarterly":
        quarter_days = 0
        quarter_month = start_date.month
        for i in range(3):
            quarter_days += calendar.monthrange(start_date.year, quarter_month)[1]
            quarter_month = (start_date + timedelta(days=quarter_days)).month

        end_date = start_date + timedelta(days=90)
        print("end_date=====>", end_date)

    if period == "Yearly":
        end_date = start_date + timedelta(days=365)

    return end_date


def check_auto_budget(request):
    if request.user.is_anonymous:
        pass
    else:
        user_name = request.user
        budget_data = Budget.objects.filter(user=user_name, ended_at__lt=datetime.today().date(), auto_budget=True)
        print("budget_data-===========>", budget_data)
        bill_data = Bill.objects.filter(user=user_name)
        revenue_data = Revenues.objects.filter(user=user_name, primary=True).order_by('-month')
        today_date = datetime.today().date()
        print("today_date", today_date)
        for obj in revenue_data:
            previous_month_date = obj.month
            revenue_end_date = obj.end_month
            next_month_date = (previous_month_date.replace(day=1) + timedelta(days=32)).replace(day=1)
            if next_month_date <= today_date and revenue_end_date >= next_month_date:
                revenue_obj = Revenues()
                revenue_obj.user = user_name
                revenue_obj.name = obj.name
                revenue_obj.month = next_month_date
                revenue_obj.end_month = obj.end_month
                revenue_obj.amount = obj.amount
                revenue_obj.currency = obj.currency
                revenue_obj.primary = obj.primary
                revenue_obj.save()
            break

        for data in bill_data:
            bill_period = data.frequency
            bill_date = data.date
            bill_amount = data.amount
            remaining_amount = data.remaining_amount
            if bill_date <= today_date:
                next_bill_date = check_frequency_date(bill_period, bill_date)
                data.date = next_bill_date
                next_amount = float(bill_amount) + float(remaining_amount)
                data.remaining_amount = next_amount
                data.status = 'unpaid'
                data.save()

        budget_quarter_spent = 0
        budget_year_spent = 0

        for data in budget_data:
            budget_period = data.budget_period
            budget_date = data.created_at
            budget_currency = data.currency
            budget_auto = data.auto_budget
            budget_name = data.name
            budget_end_date = data.ended_at
            if budget_end_date and budget_auto:
                if budget_end_date < today_date:
                    initial_amount = float(data.initial_amount)
                    budget_amount = float(data.amount)
                    budget_spent = float(data.budget_spent)
                    budget_left = budget_amount - budget_spent
                    budget_amount = initial_amount + budget_left
                    start_month_date, end_month_date = start_end_date(today_date, "Monthly")
                    if budget_period == 'Monthly':
                        budgets_save(user_name, start_month_date, end_month_date, budget_name, budget_period, budget_currency,
                                     budget_amount, budget_auto,
                                     start_month_date, end_month_date, initial_amount)
                        data.budget_status = True
                        data.save()

                    if budget_period == 'Weekly':
                        start_week_date, end_week_date = start_end_date(today_date, budget_period)
                        if start_month_date > data.start_date:
                            budgets_save(user_name, start_month_date, end_month_date, budget_name, budget_period,
                                         budget_currency,
                                         budget_amount, budget_auto,
                                         start_week_date, end_week_date, initial_amount)
                            data.created_at = None
                            data.ended_at = None
                            data.budget_status = True
                            data.save()
                        else:
                            data.start_date = start_month_date
                            data.end_date = None
                            data.ended_at = None
                            data.budget_status = True
                            data.save()
                            budgets_save(user_name, start_month_date, end_month_date, budget_name, budget_period,
                                         budget_currency, budget_amount, budget_auto, start_week_date, end_week_date, initial_amount)

                    if budget_period == 'Daily':
                        if start_month_date > data.start_date:
                            budgets_save(user_name, start_month_date, end_month_date, budget_name, budget_period,
                                         budget_currency, budget_amount, budget_auto, today_date, today_date, initial_amount)
                            data.created_at = None
                            data.ended_at = None
                            data.budget_status = True
                            data.save()

                        else:
                            data.start_date = start_month_date
                            data.end_date = None
                            data.ended_at = None
                            data.budget_status = True
                            data.save()
                            budgets_save(user_name, start_month_date, end_month_date, budget_name, budget_period,
                                         budget_currency, budget_amount, budget_auto, today_date, today_date, initial_amount)

                    if budget_period == 'Yearly':
                        budget_year_spent += budget_spent
                        if data.end_date < today_date:
                            budget_year_amount = budget_amount + (budget_amount - budget_year_spent)
                            start_year_date, end_year_date = start_end_date(today_date, budget_period)
                            year_list = list(OrderedDict(
                                ((start_year_date + timedelta(_)).replace(day=1), None) for _ in
                                range((end_year_date - start_year_date).days + 1)).keys())
                            year_list = list(dict.fromkeys(year_list))
                            auto_month_obj(user_name, year_list, start_year_date, end_year_date, budget_name,
                                           budget_period, budget_currency, budget_year_amount, budget_auto, initial_amount)
                            data.budget_status = True
                            data.save()

                    if budget_period == 'Quarterly':
                        budget_quarter_spent += budget_spent
                        if data.end_date < today_date:
                            budget_quarter_amount = budget_amount + (budget_amount - budget_quarter_spent)
                            upcoming_quarter_date, quarter_value = start_end_date(today_date, budget_period)
                            quarter_list = list(OrderedDict(
                                ((quarter_value + timedelta(_)).replace(day=1), None) for _ in
                                range((upcoming_quarter_date - quarter_value).days + 1)).keys())
                            quarter_list = list(dict.fromkeys(quarter_list))
                            auto_month_obj(user_name, quarter_list, quarter_value, upcoming_quarter_date, budget_name,
                                           budget_period, budget_currency, budget_quarter_amount, budget_auto, initial_amount)
                            data.budget_status = True
                            data.save()

                    add_remains_budget(user_name)

    context = {"ki": ""}
    return context