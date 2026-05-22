from django.contrib import admin
from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ["reference_number", "client", "assigned_truck", "assigned_driver", "status", "scheduled_pickup", "scheduled_delivery"]
    list_filter = ["status"]
    search_fields = ["reference_number", "client__client_name", "pickup_location", "dropoff_location"]
