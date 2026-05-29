from django.contrib import admin
from .models import Trip, StatusHistory


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ["reference_number", "client", "assigned_truck", "assigned_driver", "status", "scheduled_pickup", "scheduled_delivery"]
    list_filter = ["status"]
    search_fields = ["reference_number", "client__client_name", "pickup_location", "dropoff_location"]


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ["trip", "status", "timestamp", "changed_by"]
    list_filter = ["status"]
    search_fields = ["trip__reference_number"]
    date_hierarchy = "timestamp"
