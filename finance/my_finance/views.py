import json
import calendar
from datetime import date

from dateutil.relativedelta import relativedelta
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .forms import CategoryForm, LoginForm, BudgetForm, BillForm, TransactionForm, GoalForm, AccountForm,\
                   MortgageForm, LiabilityForm, PropertyForm
from .models import Category, Budget, Bill, Transaction, Goal, Account, SuggestiveCategory, Property
from .mortgage import calculator


def home(request):
    user_name = request.user
    categories = Category.objects.filter(user=user_name)
    transaction_data = Transaction.objects.filter(user=user_name)
    categories_name = []
    categories_value = []
    bills_name = []
    bill_value = []
    index = 1

    for data in transaction_data:
        if data.categories:
            if index == 1:
                categories_name.append(data.categories.name)
                categories_value.append(float(data.amount))
            else:
                if data.categories in categories_name:
                    category_index = categories_name.index(data.categories.name)
                    categories_value[category_index] = float(data.amount)
                else:
                    categories_name.append(data.categories.name)
                    categories_value.append(float(data.amount))
            index += 1

    for cat_index in range(len(categories)):
        if categories[cat_index].name in categories_name:
            pass
        else:
            categories_name.append(categories[cat_index].name)
            categories_value.append(0.0)

    context = {
                "categories_name": categories_name,
                "categories_value": categories_value
               }
    print("category_name", categories_name)
    print("categories_value", categories_value)
    return render(request, 'test.html', context=context)


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
        print("out_flow", out_flow)
        print("bill_name", bill_name)

        if cleared_amount == "True":
            account_obj = Account.objects.get(user=self.request.user, name=account)
            if bill_name:
                bill_obj = Bill.objects.filter(user=self.request.user, label=bill_name)[0]
            else:
                bill_obj = False
            if out_flow == "True":
                account_obj.balance = round(float(account_obj.balance) - transaction_amount, 2)
            else:
                account_obj.balance = round(float(account_obj.balance) + transaction_amount, 2)

            if bill_obj:
                bill_obj_amount = round(float(bill_obj.amount), 2)
                if transaction_amount == bill_obj_amount:
                    bill_obj.status = "paid"
                    bill_obj.amount = bill_obj_amount - transaction_amount
                else:
                    bill_obj.status = "unpaid"
                    bill_obj.amount = bill_obj_amount - transaction_amount
                bill_obj.save()

            account_obj.transaction_count += 1
            account_obj.save()
            obj.remaining_amount = account_obj.balance



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
        print(out_flow)
        print("out_flow======>", type(out_flow))

        if cleared_amount == "True":
            if account == update_account:
                account_obj = Account.objects.get(user=self.request.user, name=account)
                if transaction_amount != update_transaction_amount:
                    if transaction_out_flow:
                        account_obj.balance = round(float(account_obj.balance) + transaction_amount, 2)
                    else:
                        account_obj.balance = round(float(account_obj.balance) - transaction_amount, 2)

                    if out_flow:
                        account_obj.balance = round(float(account_obj.balance) - update_transaction_amount, 2)
                    else:
                        print("inFLOW")
                        account_obj.balance = round(float(account_obj.balance) + update_transaction_amount, 2)


            else:
                old_account_obj = Account.objects.get(user=self.request.user, name=account)
                account_obj = Account.objects.get(user=self.request.user, name=update_account)

                if transaction_out_flow:
                    old_account_obj.balance = round(float(old_account_obj.balance) + transaction_amount, 2)
                else:
                    old_account_obj.balance = round(float(old_account_obj.balance) - transaction_amount, 2)

                if out_flow:
                    account_obj.balance = round(float(account_obj.balance) - update_transaction_amount, 2)
                else:
                    account_obj.balance = round(float(account_obj.balance) + update_transaction_amount, 2)

                account_obj.transaction_count += 1
                old_account_obj.transaction_count -= 1

                old_account_obj.save()

            transaction_obj.remaining_amount = account_obj.balance
            transaction_obj.save()
            account_obj.save()

            if bill_name:
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

        return super().form_valid(form)


class TransactionDelete(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        transaction_obj = Transaction.objects.get(pk=self.kwargs['pk'])
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
        current_balance = float(account_obj.balance)
        transaction_data = Transaction.objects.filter(user=self.request.user, account__pk=account_pk).order_by('transaction_date')
        date_list = []
        balance_graph_data = []
        index = 1
        same_value_list = []
        for data in transaction_data:
            if index == 1:
                graph_dict = {'x': str(data.transaction_date), 'y': round(float(data.remaining_amount), 2)}
                date_list.append(str(data.transaction_date))
                balance_graph_data.append(graph_dict)
            else:
                if str(data.transaction_date) in date_list:
                    date_index = date_list.index(str(data.transaction_date))
                    balance_graph_data[date_index]['y'] = round(float(data.remaining_amount), 2)
                else:
                    graph_dict = {'x': str(data.transaction_date),
                                  'y': round(float(data.remaining_amount), 2)}
                    current_balance -= float(data.amount)
                    balance_graph_data.append(graph_dict)
                    date_list.append(str(data.transaction_date))

            index += 1

        # key_index = 1
        # insider_index = 0
        # index_cond = True
        # while insider_index < len(transaction_data):
        #     transaction_date = transaction_data[insider_index].transaction_date.date()
        #     remaining_value = float(transaction_data[insider_index].remaining_amount)
        #     out_flow = transaction_data[insider_index].out_flow
        #     print("transaction_date====>", transaction_date)
        #     while index_cond:
        #         if key_index != len(transaction_data):
        #             check_transaction_date = transaction_data[key_index].transaction_date.date()
        #             check_remaining_value = float(transaction_data[key_index].remaining_amount)
        #             check_outflow = transaction_data[key_index].out_flow
        #             print("check_transaction_date====>", check_transaction_date)
        #             if transaction_date == check_transaction_date:
        #                 remaining_value = check_remaining_value
        #
        #                 key_index += 1
        #             else:
        #                 insider_index = key_index
        #                 key_index += 1
        #                 break
        #         else:
        #             insider_index = key_index
        #             break
        #     balance_graph_data.append({'x': str(transaction_date), 'y': round(remaining_value, 2)})

        print("balance_graph", balance_graph_data)
        context['balance_graph_data'] = balance_graph_data
        context['transaction_data'] = transaction_data
        return context


class AccountAdd(LoginRequiredMixin, CreateView):
    model = Account
    form_class = AccountForm
    template_name = 'account/account_add.html'

    def form_valid(self, form):
        total_balance = float(form.cleaned_data.get('balance'))
        lock_amount = form.cleaned_data.get('lock_amount')
        print(lock_amount)
        if lock_amount != "None" and lock_amount:
            available_balance = total_balance - float(lock_amount)
        else:
            available_balance = total_balance
        obj = form.save(commit=False)
        obj.user = self.request.user
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
        if lock_amount != "None":
            available_balance = total_balance - float(lock_amount)
        else:
            available_balance = total_balance
        obj = form.save(commit=False)
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
        print(request.POST)
        name = request.POST['name']
        currency = request.POST['currency']
        liability_type = request.POST['liability_type']
        balance = request.POST['balance']
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
        liability_obj.balance = balance
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
        account__pk = self.kwargs['pk']
        transaction_data = Transaction.objects.filter(user=self.request.user, account=account__pk).order_by('transaction_date')
        balance_graph_data = []
        key_index = 1
        insider_index = 0
        index_cond = True
        while insider_index < len(transaction_data):
            transaction_date = transaction_data[insider_index].transaction_date.date()
            remaining_value = float(transaction_data[insider_index].remaining_amount)
            out_flow = transaction_data[insider_index].out_flow
            print("transaction_date====>", transaction_date)
            while index_cond:
                if key_index != len(transaction_data):
                    check_transaction_date = transaction_data[key_index].transaction_date.date()
                    check_remaining_value = float(transaction_data[key_index].remaining_amount)
                    check_outflow = transaction_data[key_index].out_flow
                    print("check_transaction_date====>", check_transaction_date)
                    if transaction_date == check_transaction_date:
                        remaining_value = check_remaining_value

                        key_index += 1
                    else:
                        insider_index = key_index
                        key_index += 1
                        break
                else:
                    insider_index = key_index
                    break
            balance_graph_data.append({'x': str(transaction_date), 'y': round(remaining_value, 2)})

        # for data in transaction_data:
        #     graph_dict = {'x': str(data.transaction_date), 'y': data.current_balance}
        #     balance_graph_data.append(graph_dict)
        print("balance_graph", balance_graph_data)
        context['balance_graph_data'] = balance_graph_data
        context['transaction_data'] = transaction_data
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
        return redirect("/bills")

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
        return redirect(f"/bills/{pk}")

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
        last_date = date.today() + relativedelta(months=+total_month)
        last_month = f'{calendar.month_name[last_date.month]} {last_date.year}'
        print("data======>", data)
        balance_data = []
        principle_data = []
        interest_data = []
        mortgage_date_data = [month for month in range(1, total_month + 1)]
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
    account_obj = Account.objects.filter(user=user_name)
    context = {'fund_data': account_obj}
    return render(request, 'funds.html', context=context)