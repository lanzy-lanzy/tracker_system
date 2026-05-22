from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["trip", "client", "amount_due", "amount_paid", "balance", "payment_status", "payment_date"]
    list_filter = ["payment_status"]
    search_fields = ["trip__reference_number", "client__client_name"]
