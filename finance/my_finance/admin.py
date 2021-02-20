from django.contrib import admin
from .models import Category,Budget,Bill,Transaction,Goal,Account,MortgageCalculator

# Register your models here.

admin.site.register(Category)
admin.site.register(Budget)
admin.site.register(Bill)
admin.site.register(Transaction)
admin.site.register(Goal)
admin.site.register(Account)
admin.site.register(MortgageCalculator)