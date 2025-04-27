from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Category)
admin.site.register(SuggestiveCategory)
admin.site.register(Budget)
admin.site.register(Bill)
admin.site.register(BillDetail)
admin.site.register(Transaction)
admin.site.register(Goal)
admin.site.register(Account)
admin.site.register(Income)
admin.site.register(IncomeDetail)
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
admin.site.register(SubCategory)
admin.site.register(StockHoldings)
admin.site.register(Tag)
admin.site.register(UserBudgets)
admin.site.register(MyNotes)
admin.site.register(AIChat)
admin.site.register(Feedback)


# Error Log Admin
@admin.register(AppErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "exception_type",
        "code",
        "status",
        "error_message",
        "request_path",
        "count",
    )
    search_fields = (
        "exception_type",
        "error_message",
        "request_path",
        "code",
        "users__username",
    )
    list_filter = ("exception_type", "code",
                   "timestamp", "request_path", "status")
    readonly_fields = (
        "timestamp",
        "exception_type",
        "error_message",
        "traceback",
        "request_path",
        "code",
        "count",
        "users",
    )

    def has_add_permission(self, request):
        return False
