from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_view, name="dashboard"),
    path("widgets/trip-activity/", views.trip_activity_widget, name="dashboard_trip_activity"),
    path("widgets/maintenance-alerts/", views.maintenance_alerts_widget, name="dashboard_maintenance_alerts"),
    path("widgets/payment-summary/", views.payment_summary_widget, name="dashboard_payment_summary"),
]
