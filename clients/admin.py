from django.contrib import admin
from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["client_name", "contact_person", "contact_number", "email", "company_name"]
    search_fields = ["client_name", "contact_person", "company_name", "email"]
