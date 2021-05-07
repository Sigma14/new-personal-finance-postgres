from django.urls import path
from .views import *

urlpatterns = [

    # Home url:-
    path('', home, name='home'),

    # Category urls :-

    path('category_list/', CategoryList.as_view(), name='category_list'),
    path('category_detail/<int:pk>', CategoryDetail.as_view(), name='category_detail'),
    path('category_add/', CategoryAdd.as_view(), name='category_add'),
    path('category_update/<int:pk>', CategoryUpdate.as_view(), name='category_update'),
    path('category_delete/<int:pk>', CategoryDelete.as_view(), name='category_delete'),

    # Budget urls :-

    path('budget_list/', BudgetList.as_view(), name='budget_list'),
    path('budget_detail/<int:pk>', BudgetDetail.as_view(), name='budget_detail'),
    path('budget_add/', BudgetAdd.as_view(), name='budget_add'),
    path('budget_update/<int:pk>', BudgetUpdate.as_view(), name='budget_update'),
    path('budget_delete/<int:pk>', BudgetDelete.as_view(), name='budget_delete'),

    # Transaction urls :-

    path('transaction_list/', TransactionList.as_view(), name='transaction_list'),
    path('transaction_detail/<int:pk>', TransactionDetail.as_view(), name='transaction_detail'),
    path('transaction_add/', TransactionAdd.as_view(), name='transaction_add'),
    path('transaction_update/<int:pk>', TransactionUpdate.as_view(), name='transaction_update'),
    path('transaction_delete/<int:pk>', TransactionDelete.as_view(), name='transaction_delete'),

    # Goal urls :-

    path('goal_list/', GoalList.as_view(), name='goal_list'),
    path('goal_detail/<int:pk>', GoalDetail.as_view(), name='goal_detail'),
    path('goal_add/', GoalAdd.as_view(), name='goal_add'),
    path('goal_update/<int:pk>', GoalUpdate.as_view(), name='goal_update'),
    path('goal_delete/<int:pk>', GoalDelete.as_view(), name='goal_delete'),

    # Account urls :-

    path('account_list/', AccountList.as_view(), name='account_list'),
    path('account_detail/<int:pk>', AccountDetail.as_view(), name='account_detail'),
    path('account_add/', AccountAdd.as_view(), name='account_add'),
    path('account_update/<int:pk>', AccountUpdate.as_view(), name='account_update'),
    path('account_delete/<int:pk>', AccountDelete.as_view(), name='account_delete'),

    # Liability Urls:-
    path('liability_list/', LiabilityList.as_view(), name='liability_list'),
    path('liability_detail/<int:pk>', LiabilityDetail.as_view(), name='liability_detail'),
    path('liability_add/', LiabilityAdd.as_view(), name='liability_add'),
    path('liability_update/<int:pk>', LiabilityUpdate.as_view(), name='liability_update'),
    path('liability_delete/<int:pk>', LiabilityDelete.as_view(), name='liability_delete'),

    # Bill Urls:-
    path('bill_list/', bill_list, name='bill_list'),
    path('bill_details/<int:pk>', bill_detail, name='bill_detail'),
    path('bill_add/', bill_add, name='bill_add'),
    path('bill_update/<int:pk>', bill_update, name='bill_update'),
    path('bill_delete/<int:pk>', bill_delete, name='bill_delete'),

    # Property Urls:-
    path('property_list/', PropertyList.as_view(), name='property_list'),
    path('property_detail/<int:pk>', PropertyDetail.as_view(), name='property_detail'),
    path('property_add/', PropertyAdd.as_view(), name='property_add'),
    path('property_update/<int:pk>', PropertyUpdate.as_view(), name='property_update'),
    path('property_delete/<int:pk>', PropertyDelete.as_view(), name='property_delete'),

    # Available Funds urls :-

    path('funds/', fund_list, name='fund_list'),

    path('login', user_login, name='user_login'),
    path('mortgagecalculator/', mortgagecalculator, name='mortgagecalculator_list'),
    # path('mortgagecalculator_list/', MortgageCalculatorList.as_view(), name='mortgagecalculator_list'),
    # path('mortgagecalculator_detail/<int:pk>', MortgageCalculatorDetail.as_view(), name='mortgagecalculator_detail'),
    # path('mortgagecalculator_add/', MortgageCalculatorAdd.as_view(), name='mortgagecalculator_add'),
    # path('mortgagecalculator_update/<int:pk>', MortgageCalculatorUpdate.as_view(), name='mortgagecalculator_update'),
    # path('mortgagecalculator_delete/<int:pk>', MortgageCalculatorDelete.as_view(), name='mortgagecalculator_delete'),

]
