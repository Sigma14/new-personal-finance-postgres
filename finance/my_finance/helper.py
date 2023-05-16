import datetime
from my_finance.models import Category, SubCategory, Transaction, Account, AvailableFunds, SuggestiveCategory

sub_category_suggested_list = {
                                "Entertainment": ["Concerts", "Movies", "Music", "Games", "Hobbies"],
                                "Food": ["Groceries", "Eating Out"],
                                "Healthcare": ["Doctor", "Fitness", "Dentist", "Pharmacy", "Health"],
                                "Housing": ["Mortgage", "Rent", "Hoa Fees", "Home Improvement"],
                                "Personal Care": ["Hair", "Shopping", "Electronic Items", "Beauty", "Spa", "Clothes"],
                                "Transportation": ["Ride Share", "Parking", "Public Transportation"],
                                "Bills": ["Electricity", "Water", "Cellphone", "Internet",
                                          "Spotify Subscription", "Netflix Spotify Subscription",
                                          "Amazon Prime Spotify Subscription"],
                                "Goals": ["Phone", "Vacation", "Education", "Wedding", "Home Improvement"]
                                }


def create_category_group():
    group_list = ["Entertainment", "Food", "Healthcare", "Housing", "Personal Care", "Transportation"]

    for group in group_list:
        SuggestiveCategory.objects.create(name=group)


def create_categories(user):
    categories_dict = {"Bills": ['Electricity', 'Water', 'Cellphone'],
                       "Goals": ["Phone", "Vacation", "Education"],
                       "Funds": [],
                       "Food": ["Groceries", "Eating Out"],
                       "Personal Care": ["Electronic Items", "Clothes"]}
    for category, sub_category in categories_dict.items():
        category = Category.objects.create(user=user, name=category)
        for sub in sub_category:
            SubCategory.objects.create(category=category, name=sub)


def check_subcategory_exists(subcategory_obj, name, category_obj):
    if subcategory_obj.name != name:
        subcategory_qs = SubCategory.objects.filter(name=name, category=category_obj)
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
    transaction_obj.transaction_date = datetime.datetime.today().date()
    transaction_obj.categories = sub_category
    transaction_obj.account = account_obj
    transaction_obj.tags = "Funds"
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
