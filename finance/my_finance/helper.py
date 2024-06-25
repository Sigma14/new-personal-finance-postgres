import threading
import time
import calendar
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from my_finance.models import Category, SubCategory, Transaction, Account, AvailableFunds, SuggestiveCategory, Bill, \
    Income, IncomeDetail, Budget, Tag

sub_category_suggested_list = {
    "Entertainment": ["Concerts", "Movies", "Music", "Games", "Hobbies"],
    "Food": ["Groceries", "Eating Out"],
    "Healthcare": ["Doctor", "Fitness", "Dentist", "Pharmacy", "Health"],
    "Housing": ["Mortgage", "Rent", "Hoa Fees", "Home Improvement"],
    "Personal Care": ["Hair", "Shopping", "Electronic Items", "Beauty", "Spa", "Clothes"],
    "Transportation": ["Ride Share", "Parking", "Public Transportation"],
    "Bills & Subscriptions": ["Electricity", "Water", "Cellphone", "Internet",
              "Spotify Subscription", "Netflix Spotify Subscription",
              "Amazon Prime Spotify Subscription"],
    "Goals": ["Phone", "Vacation", "Education", "Wedding", "Home Improvement"],
    "Income": ["Job", "Business", "Bonus"],
    "Non-Monthly":["Taxes","Car Maintenance","Medical Expenses","Insurance","Gifts","Holidays","Insurance"]
}


def create_category_group():
    group_list = ["Entertainment", "Food", "Healthcare", "Housing", "Personal Care", "Transportation"]

    for group in group_list:
        SuggestiveCategory.objects.create(name=group)


def create_categories(user):
    categories_dict = {"Bills & Subscriptions": ['Electricity', 'Water', 'Cellphone'],
                       "Goals": ["Phone", "Vacation", "Education", "New Car", "New House", "Electronic", "Other"],
                       "Funds": [],
                       "Food": ["Groceries", "Eating Out"],
                       "Personal Care": ["Electronic Items", "Clothes"],
                       "Income": ["Job", "Business", "Bonus"],
                       }
    for category, sub_category in categories_dict.items():
        category = Category.objects.create(user=user, name=category)
        for sub in sub_category:
            SubCategory.objects.create(category=category, name=sub)


def check_subcategory_exists(subcategory_obj, name, category_obj):
    if subcategory_obj.name != name:
        subcategory_qs = SubCategory.objects.filter(category__user=category_obj.user, name=name)
        if subcategory_qs.exists():
            return True
    return False


def save_fund_obj(request, user_name):
    fund_data = {}
    category_name = request.POST['category']
    account_name = request.POST['account_name']
    freeze_amount = round(float(request.POST['freeze_amount']), 2)
    category = Category.objects.filter(user=user_name, name=category_name)
    account_obj = Account.objects.get(user=user_name, name=account_name)
    account_balance = float(account_obj.available_balance)

    if account_balance < freeze_amount:
        fund_data['error'] = f"Freeze amount should be less than {account_obj.name} account balance"
        return fund_data
    if not category:
        category_obj = Category.objects.create(name=category_name, user=user_name)
    else:
        category_obj = category[0]

    sub_category = SubCategory.objects.filter(category__user=user_name, name=account_name)
    if not sub_category:
        sub_category = SubCategory.objects.create(category=category_obj, name=account_name)
    else:
        sub_category = sub_category[0]

    remaining_amount = round(account_balance - freeze_amount, 2)
    account_obj.available_balance = remaining_amount
    transaction_obj = Transaction()
    transaction_obj.user = user_name
    transaction_obj.payee = "Self"
    transaction_obj.amount = freeze_amount
    transaction_obj.remaining_amount = remaining_amount
    transaction_obj.transaction_date = datetime.today().date()
    transaction_obj.categories = sub_category
    transaction_obj.account = account_obj
    tag_obj, tag_created = Tag.objects.get_or_create(user=user_name, name="Adding Funds")
    if tag_created:
        transaction_obj.tags = tag_obj
    else:
        transaction_obj.tags = tag_obj
    transaction_obj.out_flow = True
    transaction_obj.cleared = True
    transaction_obj.save()
    account_obj.transaction_count += 1
    account_obj.save()
    fund_obj = AvailableFunds.objects.filter(user=user_name, account=account_obj)
    if fund_obj:
        total_fund = round(float(fund_obj[0].total_fund) + freeze_amount, 2)
        fund_obj[0].total_fund = total_fund
        fund_obj[0].save()
    else:
        AvailableFunds.objects.create(user=user_name, account=account_obj,
                                      total_fund=freeze_amount, lock_fund=0.0)
    return fund_data


def save_transaction(user, payee, amount, remaining_amount, transaction_date, categories, account, tags, out_flow,
                     cleared, bill=None, budget=None):
    transaction_obj = Transaction()
    transaction_obj.user = user
    transaction_obj.payee = payee
    transaction_obj.amount = amount
    transaction_obj.remaining_amount = remaining_amount
    transaction_obj.transaction_date = transaction_date
    transaction_obj.categories = categories
    transaction_obj.account = account
    transaction_obj.tags = tags
    transaction_obj.out_flow = out_flow
    transaction_obj.cleared = cleared
    if bill:
        transaction_obj.bill = bill
    if budget:
        transaction_obj.budgets = budget
    transaction_obj.save()


def start_end_date(date_value, period):
    today_date = datetime.today().date()
    if period == "Yearly":
        start_year_date = f"01-01-{date_value.year}"
        end_year_date = f"31-12-{date_value.year}"
        return datetime.strptime(start_year_date, "%d-%m-%Y").date(), datetime.strptime(end_year_date,
                                                                                        "%d-%m-%Y").date()

    if period == "Quarterly":
        current_date = datetime.now()
        upcoming_quarter = int((current_date.month - 1) / 3 + 1)
        if upcoming_quarter == 4:
            upcoming_quarter_date = datetime(current_date.year, 3 * upcoming_quarter, 31)
        else:
            upcoming_quarter_date = datetime(current_date.year, 3 * upcoming_quarter + 1, 1) + timedelta(days=-1)
        quarter_value = upcoming_quarter_date.date() - timedelta(days=88)
        return upcoming_quarter_date.date(), quarter_value.replace(day=1)

    if period == "Monthly":
        start_date = date_value.replace(day=1)
        end_date = date_value.replace(day=calendar.monthrange(date_value.year, date_value.month)[1])
        return start_date, end_date

    if period == "Weekly":
        week_start = today_date - timedelta(days=today_date.weekday())
        week_end = week_start + timedelta(days=6)
        return week_start, week_end

    return date_value, ""


def get_period_date(start_date, period):
    period_date = ''
    if period == "Daily":
        period_date = start_date + relativedelta(days=1)

    if period == "Weekly":
        period_date = start_date + relativedelta(weeks=1)

    if period == "Monthly":
        period_date = start_date + relativedelta(months=1)

    if period == "Quarterly":
        period_date = start_date + relativedelta(months=3)

    if period == "Yearly":
        period_date = start_date + relativedelta(years=1)

    return period_date


def check_bill_is_due():
    """
        Check bill date is due or not
    """
    today_date = datetime.today().date()
    bill_data = Bill.objects.filter(date__lte=today_date, status="unpaid")
    for bill in bill_data:        
        bill_detail_obj = bill.bill_details
        account_obj = bill_detail_obj.account
        account_balance = float(account_obj.available_balance)
        currency = account_obj.currency
        label = bill_detail_obj.label
        bill_amount = float(bill_detail_obj.amount)
        auto_bill = bill_detail_obj.auto_bill
        auto_pay = bill_detail_obj.auto_pay
        bill_date = bill_detail_obj.date
         # Calculate the next month and year
        next_month = (today_date.month % 12) + 1
        next_year = today_date.year if next_month != 1 else today_date.year + 1

        # Check if the bill's month and year are the next month and year
        if bill_date.month == next_month and bill_date.year == next_year:
            continue
        frequency = bill_detail_obj.frequency
        next_bill_date = get_period_date(bill_date, frequency)
        bill_detail_obj.date = next_bill_date
        bill_detail_obj.save()

        if auto_bill:
            next_bill_date = get_period_date(bill_date, frequency)
            Bill.objects.create(user=bill.user, account=account_obj, currency=currency, label=label,
                                amount=bill_amount, remaining_amount=bill_amount, date=next_bill_date,
                                frequency=frequency, bill_details=bill_detail_obj, auto_bill=auto_bill,
                                auto_pay=auto_pay)

        if auto_pay:
            remaining_amount = round(account_balance - bill_amount, 2)
            categories = SubCategory.objects.get(name=label, category__user=bill.user)
            tag_obj, tag_created = Tag.objects.get_or_create(user=bill.user, name="Bills")
            save_transaction(bill.user, label, bill_amount, remaining_amount, bill.date, categories, account_obj,
                             tag_obj, True, True, bill)
            account_obj.available_balance = remaining_amount
            account_obj.transaction_count += 1
            account_obj.save()
            bill.remaining_amount = 0.0
            bill.status = "paid"
            bill.save()
        else:
            bill.status = "unpaid"
            bill.save()


def request_bill():
    """
    Request bill
    """
    while True:
        check_bill_is_due()
        time.sleep(5)



def create_bill_request():
    """
    Create bill request log
    """
    # Get a list of all alive threads
    alive_threads = threading.enumerate()
    bills_thread1 = False
    for thread in alive_threads:
        if thread.name == 'bills_thread1':
            bills_thread1 = True

    if not bills_thread1:
        t1 = threading.Thread(target=request_bill, name='bills_thread1')
        t1.start()


def save_income(user, sub_category, account, income_amount, income_date, auto_income, frequency, auto_credit,
                created_date, primary):
    """
    Save income
    """
    income_obj = Income()
    income_obj.user = user
    income_obj.sub_category = sub_category
    income_obj.account = account
    income_obj.income_amount = income_amount
    income_obj.income_date = income_date
    income_obj.auto_income = auto_income
    income_obj.frequency = frequency
    income_obj.auto_credit = auto_credit
    income_obj.primary = primary
    income_obj.created_at = created_date
    income_obj.save()
    return income_obj


def save_income_details(account, income_amount, income, credited, income_date):
    """
    Save income
    """
    income_obj = IncomeDetail()
    income_obj.account = account
    income_obj.income_amount = income_amount
    income_obj.income = income
    income_obj.credited = credited
    income_obj.income_date = income_date
    income_obj.save()
    return income_obj


def check_income_date():
    """
        Check income date
    """
    today_date = datetime.today().date()
    income_data = Income.objects.filter(income_date__lte=today_date, auto_income=True)
    for income in income_data:
        account_obj = income.account
        account_balance = float(account_obj.available_balance)
        sub_category = income.sub_category
        income_amount = float(income.income_amount)
        auto_income = income.auto_income
        auto_credit = income.auto_credit
        income_date = income.income_date
        frequency = income.frequency
        income_detail_obj = save_income_details(account_obj, income_amount, income, False, income_date)
        if auto_income:
            next_bill_date = get_period_date(income_date, frequency)
            income.income_date = next_bill_date
        if auto_credit:
            remaining_amount = round(account_balance + income_amount, 2)
            tag_obj, tag_created = Tag.objects.get_or_create(user=income.user, name="Incomes")
            save_transaction(income.user, sub_category.name, income_amount, remaining_amount, income_date, sub_category,
                             account_obj,
                             tag_obj, False, True)
            account_obj.available_balance = remaining_amount
            account_obj.transaction_count += 1
            account_obj.save()
            income_detail_obj.credited = True
            income_detail_obj.save()
        income.save()


def request_income():
    """
    Request income
    """
    while True:
        check_income_date()


def create_income_request():
    """
    Create income request log
    """
    # Get a list of all alive threads
    alive_threads = threading.enumerate()
    income_thread1 = False
    for thread in alive_threads:
        if thread.name == 'income_thread1':
            income_thread1 = True

    if not income_thread1:
        t1 = threading.Thread(target=request_income, name='income_thread1')
        t1.start()


def save_budgets(user_name, start_date, end_date, budget_name, budget_period, budget_currency, budget_amount,
                 budget_auto, created_date, ended_date, initial_amount, budget_start_date, subcategory_obj=None,
                 budget_obj=None, budget_status=None):
    if not budget_obj:
        budget_obj = Budget()
    budget_obj.user = user_name
    budget_obj.start_date = start_date
    budget_obj.end_date = end_date
    budget_obj.name = budget_name
    budget_obj.category = subcategory_obj
    budget_obj.budget_period = budget_period
    budget_obj.currency = budget_currency
    budget_obj.amount = budget_amount
    budget_obj.initial_amount = initial_amount
    budget_obj.budget_left = budget_amount
    budget_obj.auto_budget = budget_auto
    budget_obj.budget_start_date = budget_start_date
    budget_obj.created_at = created_date
    budget_obj.ended_at = ended_date
    if budget_status:
        budget_obj.budget_status = budget_status
    budget_obj.save()


def check_budget_date():
    """
        Check budget date
    """
    today_date = datetime.today().date()
    budget_data = Budget.objects.filter(ended_at__lt=today_date, auto_budget=True, budget_status=False)
    for budget in budget_data:
        print("===========auto pay budget call================")
        budget_name = budget.name
        budget_start_date = budget.ended_at + relativedelta(days=1)
        budget_period = budget.budget_period
        subcategory = budget.category
        currency = budget.currency
        amount = budget.amount
        budget_created_date = budget.budget_start_date
        auto_budget = budget.auto_budget
        start_month_date, end_month_date = start_end_date(budget_start_date, "Monthly")
        print("budget_period=======>", budget_period)
        print("budget_name=======>", budget_name)
        budget_end_date = get_period_date(budget_start_date, budget_period) - relativedelta(days=1)
        if budget_period == 'Quarterly':
            for month_value in range(3):
                if month_value == 2:
                    budget_status = False
                else:
                    budget_status = True
                save_budgets(budget.user, start_month_date, end_month_date, budget_name, budget_period,
                             currency, amount, auto_budget, budget_start_date, budget_end_date, amount,
                             budget_created_date, subcategory, None, budget_status)
                start_month_date = start_month_date + relativedelta(months=1)
                start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")

        if budget_period == 'Yearly':
            for month_value in range(12):
                if month_value == 11:
                    budget_status = False
                else:
                    budget_status = True
                save_budgets(budget.user, start_month_date, end_month_date, budget_name, budget_period,
                             currency, amount, auto_budget, budget_start_date, budget_end_date, amount,
                             budget_created_date, subcategory, None, budget_status)
                start_month_date = start_month_date + relativedelta(months=1)
                start_month_date, end_month_date = start_end_date(start_month_date, "Monthly")

        if budget_period == 'Daily' or budget_period == 'Weekly' or budget_period == 'Monthly':
            save_budgets(budget.user, start_month_date, end_month_date, budget_name, budget_period,
                         currency, amount, auto_budget, budget_start_date, budget_end_date, amount,
                         budget_created_date, subcategory)
        budget.budget_status = True
        budget.save()


def request_budget():
    """
    Request budget
    """
    while True:
        check_budget_date()
        time.sleep(60 * 60)


def create_budget_request():
    """
    Create budget request log
    """
    # Get a list of all alive threads
    alive_threads = threading.enumerate()
    budget_thread1 = False
    for thread in alive_threads:
        if thread.name == 'budget_thread1':
            budget_thread1 = True

    if not budget_thread1:
        t1 = threading.Thread(target=request_budget, name='budget_thread1')
        t1.start()


def dict_value_to_list(result_dict):
    result_list = []
    for key, value in result_dict.items():
        result_list.append(value)
    return result_list


def get_template_budget():
    # Get the current year and month
    now = datetime.now()
    year = now.year
    month = now.month

    # Get the number of days in the current month
    num_days = calendar.monthrange(year, month)[1]

    # Generate a list of all dates in the current month
    dates = [datetime(year, month, day) for day in range(1, num_days + 1)]
    template_end_date = dates[0]
    template_name_list = ['Hobbies', 'Clothes', 'Study', 'Entertainment', 'Health']
    tem_daily_amount = 0
    tem_daily_spent = 0
    tem_weekly_amount = 0
    tem_weekly_spent = 0

    template_dict = {'Yearly': [], 'Quarterly': [], 'Monthly': [],
                     'Weekly': [['Entertainment', 500.0, 0.0, 500.0, 20]], 'Daily': [['Health', 500.0, 0.0, 500.0, 10]]}
    for tem_date in dates:
        if tem_date == template_end_date:
            template_end_date = get_period_date(tem_date, "Weekly")
            temp_start_date = datetime.strftime(tem_date, "%b %d, %Y")
            temp_end_date = datetime.strftime(template_end_date - relativedelta(days=1), "%b %d, %Y")
            template_dict['Weekly'].append(
                ['Entertainment', 50.0, 30.0, 20.0, 1973, 'Weekly', temp_start_date, temp_end_date])
            tem_weekly_amount += 50.0
            tem_weekly_spent += 30.0

        if not template_dict['Monthly'] or not template_dict['Quarterly'] or not template_dict['Quarterly']:
            temp_month_end_date = datetime.strftime(
                get_period_date(tem_date, "Monthly") - relativedelta(days=1), "%b %d, %Y")
            temp_month_start_date = datetime.strftime(tem_date, "%b %d, %Y")
            template_dict['Monthly'].append(
                ['Hobbies', 150.0, 100.0, 50.0, 1979, 'Monthly', temp_month_start_date, temp_month_end_date])
            temp_quart_end_date = datetime.strftime(
                get_period_date(tem_date, "Quarterly") - relativedelta(days=1), "%b %d, %Y")
            temp_quart_start_date = datetime.strftime(tem_date, "%b %d, %Y")
            template_dict['Quarterly'].append(
                ['Clothes', 200.0, 50.0, 150.0, 1979, 'Quarterly', temp_quart_start_date, temp_quart_end_date])
            temp_year_end_date = datetime.strftime(get_period_date(tem_date, "Yearly") - relativedelta(days=1),
                                                   "%b %d, %Y")
            temp_year_start_date = datetime.strftime(tem_date, "%b %d, %Y")
            template_dict['Yearly'].append(
                ['Study', 2500.0, 1000.0, 1500.0, 1979, 'Yearly', temp_year_start_date, temp_year_end_date])

        template_dict['Daily'].append(
            ['Health', 50.0, 40.0, 10.0, 1973, 'Daily', datetime.strftime(tem_date, "%b %d, %Y"),
             datetime.strftime(tem_date, "%b %d, %Y")])
        tem_daily_amount += 50.0
        tem_daily_spent += 40.0

    template_dict['Daily'][0][1] = tem_daily_amount
    template_dict['Daily'][0][2] = tem_daily_spent
    template_dict['Daily'][0][3] = tem_daily_amount - tem_daily_spent
    template_dict['Weekly'][0][1] = tem_weekly_amount
    template_dict['Weekly'][0][2] = tem_weekly_spent
    template_dict['Weekly'][0][3] = tem_weekly_amount - tem_weekly_spent
    total_spent = tem_daily_spent + tem_weekly_spent + 100.0 + 50.0 + 1000.0
    total_amount = tem_daily_amount + tem_weekly_amount + 150.0 + 200.0 + 2500.0
    total_left = total_amount - total_spent
    template_values = [total_spent, total_left]
    template_graph_data = [{'name': 'Spent', 'data': [1000.0, 50.0, 100.0, tem_weekly_spent, tem_daily_spent]},
                           {'name': 'Left', 'data': [1500.0, 150.0, 50.0, template_dict['Weekly'][0][3], template_dict['Daily'][0][3]]},
                           {'name': 'OverSpent', 'data': [0, 0, 0, 0, 0]}]
    return template_dict, template_values, template_name_list, template_graph_data


def get_cmp_diff_data(budget_names, user_name, month_start, month_end, budget_bar_value, budget_graph_value,
                      budget_transaction_data_dict, budget_income_graph_value, budget_income_bar_value, expense_bdgt_names, income_bdgt_names, total_bgt_spend_amount=None, total_bgt_earned_amount=None):
    for bgt_name in budget_names:
        transaction_budget = Transaction.objects.filter(user=user_name, categories__name=bgt_name,
                                                        transaction_date__range=(month_start, month_end)).order_by(
            '-transaction_date')
        total_spent_amount = 0
        total_earn_amount = 0
        trans_type = "spend"
        budget_transaction_data_dict[bgt_name] = []
        for t in transaction_budget:
            if t.categories.category.name == "Income":
                total_earn_amount += float(t.amount)
                total_bgt_earned_amount += float(t.amount)
                trans_type = "earned"
            else:
                total_spent_amount += float(t.amount)
                total_bgt_spend_amount += float(t.amount)

            budget_transaction_data_dict[bgt_name].append([str(t.transaction_date), float(t.amount), trans_type])

        if trans_type == "spend":
            budget_graph_value.append(total_spent_amount)
            budget_transaction_data_dict[bgt_name].insert(0, [bgt_name, total_spent_amount])
            budget_bar_value[0]['data'].append(total_spent_amount)
            expense_bdgt_names.append(bgt_name)
        else:
            budget_income_graph_value.append(total_earn_amount)
            budget_income_bar_value[0]['data'].append(total_earn_amount)
            budget_transaction_data_dict[bgt_name].insert(0, [bgt_name, total_earn_amount])
            income_bdgt_names.append(bgt_name)

    return budget_bar_value, budget_graph_value, budget_income_graph_value, budget_income_bar_value, expense_bdgt_names, income_bdgt_names, budget_transaction_data_dict, total_bgt_spend_amount,\
           total_bgt_earned_amount


def get_cmp_data(budget_names, user_name, month_start, month_end, budget_bar_value, budget_graph_value,
                 budget_transaction_data_dict):
    for bgt_name in budget_names:
        transaction_budget = Transaction.objects.filter(user=user_name, categories__name=bgt_name,
                                                        transaction_date__range=(month_start, month_end)).order_by(
            '-transaction_date')
        total_spent_amount = 0
        budget_transaction_data_dict[bgt_name] = []
        for t in transaction_budget:
            total_spent_amount += float(t.amount)
            budget_transaction_data_dict[bgt_name].append([str(t.transaction_date), float(t.amount)])

        budget_graph_value.append(total_spent_amount)
        budget_transaction_data_dict[bgt_name].insert(0, [bgt_name, total_spent_amount])
        budget_bar_value[0]['data'].append(total_spent_amount)

    return budget_bar_value, budget_graph_value, budget_transaction_data_dict
