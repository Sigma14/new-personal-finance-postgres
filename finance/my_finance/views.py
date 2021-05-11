import json
import calendar
import datetime

from dateutil.relativedelta import relativedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import CategoryForm, LoginForm, BudgetForm, BillForm, TransactionForm, GoalForm, AccountForm, \
    MortgageForm, LiabilityForm, PropertyForm
from .models import Category, Budget, Bill, Transaction, Goal, Account, SuggestiveCategory, Property
from .mortgage import calculator


def net_worth_cal(account_data, property_data, date_compare, fun_name=None):
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
    base = max(date_compare)
    min_date = min(date_compare)
    num_days = base - min_date
    num_days = num_days.days
    date_range_list = [str(base - datetime.timedelta(days=x)) for x in range(num_days)]
    date_range_list.append(str(min_date))

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
        return net_worth_dict, assets_data, liability_data, total_asset_amount_dict, total_liability_dict,\
               total_property_dict, asset_currency_balance, liability_currency_balance, property_currency_balance,\
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
    if user_name != "AnonymousUser":
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
        bills_name = []
        bill_value = []
        account_graph_data = []
        category_index = 1
        date_compare = []
        min_max_value_list = []
        asset_currency_balance = []
        liability_currency_balance = []
        property_currency_balance = []

        for data in property_data:
            property_currency_balance.append({data.currency: data.value})

        for obj in all_transaction_data:
            date_compare.append(obj.account.created_at.date())
            date_compare.append(obj.transaction_date)

        if accounts_data:
            base = max(date_compare)
            min_date = min(date_compare)
            num_days = base - min_date
            num_days = num_days.days
            print(num_days)
            date_range_list = [str(base - datetime.timedelta(days=x)) for x in range(num_days)]
            date_range_list.append(str(min_date))
        else:
            date_range_list = []

        for acc_obj in accounts_data:
            transaction_data = Transaction.objects.filter(user=user_name, account__pk=acc_obj.pk).order_by(
                'transaction_date')[::-1]
            current_balance = float(acc_obj.available_balance)
            balance_graph_dict = {}
            balance_graph_data = []
            date_list = []

            if acc_obj.liability_type != "Debt" and acc_obj.liability_type != "Loan" and acc_obj.liability_type != "Mortgage":
                overtime_account_data(transaction_data, current_balance, balance_graph_dict, date_list, balance_graph_data,
                                      date_range_list)
                asset_currency_balance.append({acc_obj.currency: balance_graph_data[::-1]})
                graph_dict = {'label_name': acc_obj.name, 'data_value': balance_graph_data[::-1]}
                account_graph_data.append(graph_dict)
                min_max_value_list.append(min(balance_graph_data))
                min_max_value_list.append(max(balance_graph_data))
            else:
                overtime_account_data(transaction_data, current_balance, balance_graph_dict, date_list, balance_graph_data,
                                      date_range_list)
                liability_currency_balance.append({acc_obj.currency: balance_graph_data[::-1]})

        for data in all_transaction_data:
            if data.categories and data.out_flow:
                if category_index == 1:
                    categories_name.append(data.categories.name)
                    categories_value.append(float(data.amount))
                else:
                    if data.categories.name in categories_name:
                        category_index = categories_name.index(data.categories.name)
                        categories_value[category_index] += float(data.amount)
                    else:
                        categories_name.append(data.categories.name)
                        categories_value.append(float(data.amount))
                category_index += 1

        for cat_index in range(len(categories)):
            if categories[cat_index].name in categories_name:
                pass
            else:
                categories_name.append(categories[cat_index].name)
                categories_value.append(0.0)

        for data in budget_data:
            total_budget += float(data.amount)
            budget_label.append(data.name)
            budget_values.append(float(data.amount))

        for value in budget_values:
            result = round((value / total_budget) * 100, 2)
            budget_percentage.append(result)

        net_worth_dict = net_worth_cal(accounts_data, property_data, date_compare, fun_name="dash_board")

        if min_max_value_list:
            max_value = max(min_max_value_list)
            min_value = min(min_max_value_list)
        else:
            max_value = 0
            min_value = 0

        print("Assets_currency_data", asset_currency_balance)
        print("Liabiliy_currency_data", liability_currency_balance)
        print("Property_currency_data", property_currency_balance)

        context = {
            "categories_name": categories_name,
            "categories_value": categories_value,
            "account_graph_data": account_graph_data,
            "date_range_list": date_range_list[::-1],
            "graph_label": budget_label,
            "graph_value": budget_percentage,
            "net_worth_dict": net_worth_dict,
            "max_value": max_value,
            "min_value": min_value
        }
    else:
        context = {}
    return render(request, 'test.html', context=context)


def net_worth(request):
    user_name = request.user
    account_data = Account.objects.filter(user=user_name)
    property_data = Property.objects.filter(user=user_name)
    all_transaction_data = Transaction.objects.filter(user=user_name)
    date_compare = []

    for obj in all_transaction_data:
        date_compare.append(obj.account.created_at.date())
        date_compare.append(obj.transaction_date)

    currency_dict = {
        "$": 'US Dollar ($)',
        "€": 'Euro (€)',
        "₹": 'Indian rupee (₹)',
        "£": 'British Pound (£)',
    }
    net_worth_dict, assets_data, liability_data, total_asset_amount_dict, total_liability_dict, \
    total_property_dict, asset_currency_balance, liability_currency_balance, property_currency_balance,\
    total_currency_list, date_range_list = net_worth_cal(account_data, property_data, date_compare)

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
                sum_liab_data = [x + y for (x, y) in zip(liability_total_dict[liability_currency_name], liability_balance_data)]
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

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)


class CategoryDetail(DetailView):
    model = Category
    template_name = 'category/category_detail.html'


class CategoryAdd(CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'category/category_add.html'

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user
        obj.save()
        return super().form_valid(form)


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
    logout(request)
    return redirect('/login')


class BudgetList(LoginRequiredMixin, ListView):
    model = Budget
    template_name = 'budget/budget_list.html'

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)


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


class TransactionList(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = 'transaction/transaction_list.html'

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


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

    def form_valid(self, form):
        obj = form.save(commit=False)
        obj.user = self.request.user

        account = form.cleaned_data.get('account')
        transaction_amount = round(float(form.cleaned_data.get('amount')), 2)
        out_flow = form.cleaned_data.get('out_flow')
        cleared_amount = form.cleaned_data.get('cleared')
        bill_name = form.cleaned_data.get('bill')
        budget_name = form.cleaned_data.get('budgets')
        account = account.name
        if cleared_amount == "True":
            account_obj = Account.objects.get(user=self.request.user, name=account)

            if bill_name:
                bill_name = bill_name.label
                bill_obj = Bill.objects.filter(user=self.request.user, label=bill_name)[0]
            else:
                bill_obj = False

            if budget_name:
                budget_name = budget_name.name
                budget_obj = Budget.objects.filter(user=self.request.user, name=budget_name)[0]
            else:
                budget_obj = False

            if out_flow == "True":
                account_obj.available_balance = round(float(account_obj.available_balance) - transaction_amount, 2)
            else:
                account_obj.available_balance = round(float(account_obj.available_balance) + transaction_amount, 2)

            if bill_obj:
                bill_obj_amount = round(float(bill_obj.amount), 2)
                if transaction_amount == bill_obj_amount:
                    bill_obj.status = "paid"
                    bill_obj.amount = bill_obj_amount - transaction_amount
                else:
                    bill_obj.status = "unpaid"
                    bill_obj.amount = bill_obj_amount - transaction_amount
                bill_obj.save()

            if budget_name:
                if out_flow == "True":
                    budget_obj.amount = round(float(budget_obj.amount) - transaction_amount, 2)
                else:
                    budget_obj.amount = round(float(budget_obj.amount) + transaction_amount, 2)
                budget_obj.save()

            account_obj.transaction_count += 1
            account_obj.save()
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
                budget_obj = False

            if budget_obj:
                transaction_budget_name = transaction_obj.budgets
                budget_obj_amount = round(float(budget_obj.amount), 2)
                if transaction_budget_name == budget_name:
                    if transaction_amount != update_transaction_amount:
                        budget_obj_amount = budget_obj_amount + transaction_amount
                else:
                    old_budget_obj = Budget.objects.filter(user=self.request.user, name=transaction_budget_name)
                    if old_budget_obj:
                        old_budget_obj_amount = round(float(old_budget_obj.amount), 2)
                        old_budget_obj.amount = old_budget_obj_amount + transaction_amount
                        old_bill_obj.save()

                budget_obj.amount = budget_obj_amount - update_transaction_amount
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
                    budget_obj.amount = round(float(budget_obj.amount) + transaction_amount, 2)
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

        print(balance_graph_data)
        context['balance_graph_data'] = balance_graph_data
        context['transaction_data'] = transaction_data
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

        print(balance_graph_data)
        context['balance_graph_data'] = balance_graph_data
        context['transaction_data'] = transaction_data
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
        print("mortage_data", mortgage_graph_data)
        context = {
            'form': form,
            'data': data,
            'monthly_payment': monthly_payment,
            'last_month': last_month,
            'days': total_month,
            'total_payment': total_payment,
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
    context = {'fund_data': fund_data}
    return render(request, 'funds.html', context=context)
