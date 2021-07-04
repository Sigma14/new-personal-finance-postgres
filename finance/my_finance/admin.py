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
admin.site.register(Property)
admin.site.register(Revenues)
admin.site.register(Expenses)
