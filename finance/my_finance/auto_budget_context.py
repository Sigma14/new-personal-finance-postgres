from .models import Budget, Bill, Revenues
from datetime import datetime, timedelta


def check_frequency_date(period, start_date):
    if period == "Daily":
        end_date = start_date + timedelta(days=1)

    if period == "Weekly":
        end_date = start_date + timedelta(days=7)

    if period == "Monthly":
        end_date = start_date + timedelta(days=30)

    if period == "Quarterly":
        end_date = start_date + timedelta(days=90)

    if period == "Yearly":
        end_date = start_date + timedelta(days=365)

    return end_date


def check_auto_budget(request):
    if request.user.is_anonymous:
        pass
    else:
        user_name = request.user
        budget_data = Budget.objects.filter(user=user_name)
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
                next_amount = bill_amount + remaining_amount
                data.amount = next_amount
                data.remaining_amount = next_amount
                data.status = 'unpaid'
                data.save()

        for data in budget_data:
            budget_period = data.budget_period
            budget_date = data.updated_at.date()
            budget_amount = float(data.amount)
            budget_spent = float(data.budget_spent)
            budget_left = budget_amount - budget_spent
            budget_end_date = check_frequency_date(budget_period, budget_date)
            print("budget_end_date", budget_end_date)
            if budget_end_date <= today_date:
                print("date complete")
                data.amount = budget_amount + budget_left
                data.budget_spent = 0.0
                data.updated_at = today_date
                data.save()

    context = {"ki": ""}
    return context