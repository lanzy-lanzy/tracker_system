from django.contrib import admin
from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["expense_type", "trip", "truck", "amount", "date"]
    list_filter = ["expense_type"]
    search_fields = ["notes", "trip__reference_number"]
