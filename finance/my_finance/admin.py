from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Category)
admin.site.register(SuggestiveCategory)
admin.site.register(Budget)
admin.site.register(Bill)
admin.site.register(Transaction)
admin.site.register(Goal)
admin.site.register(Account)
admin.site.register(MortgageCalculator)
admin.site.register(Revenues)
admin.site.register(Expenses)
admin.site.register(AvailableFunds)
admin.site.register(TemplateBudget)
admin.site.register(MortgageDetails)
admin.site.register(ClosingCostDetails)
admin.site.register(RevenuesDetails)
admin.site.register(ExpensesDetails)
admin.site.register(PropertyPurchaseDetails)
admin.site.register(RentalPropertyModel)
admin.site.register(CapexBudgetDetails)
admin.site.register(Property)
admin.site.register(PropertyRentalInfo)
admin.site.register(PropertyInvoice)
admin.site.register(PropertyMaintenance)
admin.site.register(PropertyExpense)
admin.site.register(PlaidItem)

