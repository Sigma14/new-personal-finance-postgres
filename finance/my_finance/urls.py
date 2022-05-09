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

    path('budget_list/', budget_list, name='budget_list'),
    path('budget_detail/<int:pk>', budget_details, name='budget_detail'),
    path('budget_add/', BudgetAdd.as_view(), name='budget_add'),
    path('budget_update/<int:pk>', BudgetUpdate.as_view(), name='budget_update'),
    path('budget_delete/<int:pk>', BudgetDelete.as_view(), name='budget_delete'),

    # Template Budget urls :-

    path('template_budget_list/', template_budget_list, name='template_budget_list'),
    # path('template_budget_detail/<int:pk>', template_budget_details, name='template_budget_detail'),
    path('template_budget_add/', TemplateAdd.as_view(), name='template_budget_add'),
    path('template_budget_update/<int:pk>', TemplateUpdate.as_view(), name='template_budget_update'),
    path('template_budget_delete/<int:pk>', TemplateDelete.as_view(), name='template_budget_delete'),

    # Transaction urls :-

    path('transaction_list/', transaction_list, name='transaction_list'),
    path('transaction_detail/<int:pk>', TransactionDetail.as_view(), name='transaction_detail'),
    path('transaction_add/', TransactionAdd.as_view(), name='transaction_add'),
    path('transaction_update/<int:pk>', TransactionUpdate.as_view(), name='transaction_update'),
    path('transaction_delete/<int:pk>', TransactionDelete.as_view(), name='transaction_delete'),
    path('transaction_upload', transaction_upload, name='transaction_upload'),
    path('transaction_report', transaction_report, name='transaction_report'),

    # Goal urls :-
    path('goal_add/', goal_add, name='goal_add'),
    path('goal_list/', GoalList.as_view(), name='goal_list'),
    path('goal_update/<int:pk>', goal_update, name='goal_update'),
    path('goal_detail/<int:pk>', GoalDetail.as_view(), name='goal_detail'),
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
    path('bill_detail/<int:pk>', bill_detail, name='bill_detail'),
    path('bill_add/', bill_add, name='bill_add'),
    path('bill_update/<int:pk>', bill_update, name='bill_update'),
    path('bill_delete/<int:pk>', bill_delete, name='bill_delete'),
    path('bill/automatic_amount', bill_automatic_amount, name='bill_automatic_amount'),

    # Rental Property Models Urls:-
    path('rental_property_list/', RentalPropertyList.as_view(), name='rental_property_list'),
    path('rental_property_detail/<int:pk>', rental_property_details, name='rental_property_detail'),
    path('rental_property_add/', rental_property_add, name='rental_property_add'),
    path('rental_property_update/<int:pk>', rental_property_update, name='rental_property_update'),
    path('rental_property_delete/<int:pk>', rental_property_delete, name='rental_property_delete'),

    # Property Urls:-
    path('property_add/', add_property, name='property_add'),
    path('property_list/', list_property, name='property_list'),
    path('update/<int:pk>/<str:method_name>', update_property, name='property_update'),
    path('property_details/<int:pk>', property_details, name='property_details'),
    path('property_delete/<int:pk>', delete_property, name='property_delete'),
    path('lease_add/<int:pk>/<str:unit_name>', add_lease, name='add_lease'),

    # Property Maintenance
    path('property/maintenance/add/', MaintenanceAdd.as_view(), name='property_maintenance_add'),
    path('property/maintenance/list/', MaintenanceList.as_view(), name='property_maintenance_list'),
    path('property/maintenance/details/<int:pk>', MaintenanceDetail.as_view(), name='property_maintenance_details'),
    path('property/maintenance/update/<int:pk>', MaintenanceUpdate.as_view(), name='property_maintenance_update'),
    path('property/maintenance/delete/<int:pk>', delete_maintenance, name='property_maintenance_delete'),
    path('property/property_info/', property_info, name='property_info'),

    # Revenue Urls :-
    path('revenue_add/', revenue_add, name='revenue_add'),
    path('revenue_update/<str:pk>', revenue_update, name='revenue_update'),
    path('revenue_update_name/<str:pk>', revenue_update_name, name='revenue_update_name'),

    # Revenue Urls :-
    path('expenses_add/', expenses_add, name='expenses_add'),
    path('expenses_update/<int:pk>', expenses_update, name='expenses_update'),
    path('expenses_delete/<int:pk>', expenses_delete, name='expenses_delete'),

    # Available Funds urls :-

    path('funds_list/', FundList.as_view(), name='fund_list'),
    path('fund_update/<int:pk>', fund_update, name='fund_update'),
    path('fund_overtime', fund_overtime, name='fund_overtime'),

    # Calculators

    path('mortgagecalculator/', mortgagecalculator, name='mortgagecalculator_list'),
    path('future-net-worth-calculator/', future_net_worth_calculator, name='future_net_worth_calculator'),

    path('login', user_login, name='user_login'),
    path('logout', user_logout, name='user_logout'),
    path('net_worth', net_worth, name='net_worth'),

    # path('mortgagecalculator_list/', MortgageCalculatorList.as_view(), name='mortgagecalculator_list'),
    # path('mortgagecalculator_detail/<int:pk>', MortgageCalculatorDetail.as_view(), name='mortgagecalculator_detail'),
    # path('mortgagecalculator_add/', MortgageCalculatorAdd.as_view(), name='mortgagecalculator_add'),
    # path('mortgagecalculator_update/<int:pk>', MortgageCalculatorUpdate.as_view(), name='mortgagecalculator_update'),
    # path('mortgagecalculator_delete/<int:pk>', MortgageCalculatorDelete.as_view(), name='mortgagecalculator_delete'),

    # STOCK ANALYSIS

    path('stock-analysis', stock_analysis, name='stock_analysis'),

    # DOWNLOADS FILE OPTIONS

    path('download/pdf', download_pdf, name='download_pdf'),
    path('download/csv', download_csv, name='download_scv'),
    path('download/rental_pdf', download_rental_pdf, name='download_rental_pdf'),
    path('process_image', process_image, name='property_checkout'),

]
