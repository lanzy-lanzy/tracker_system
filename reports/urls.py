from django.urls import path
from . import views

urlpatterns = [
    path("", views.report_dashboard_view, name="report_dashboard"),
    path("trips/daily/", views.daily_trip_report, name="daily_trip_report"),
    path("trips/daily/pdf/", views.daily_trip_pdf, name="daily_trip_pdf"),
    path("trips/monthly/", views.monthly_trip_report, name="monthly_trip_report"),
    path("trips/monthly/pdf/", views.monthly_trip_pdf, name="monthly_trip_pdf"),
    path("trucks/utilization/", views.truck_utilization_report, name="truck_utilization_report"),
    path("trucks/utilization/pdf/", views.truck_utilization_pdf, name="truck_utilization_pdf"),
    path("drivers/performance/", views.driver_performance_report, name="driver_performance_report"),
    path("drivers/performance/pdf/", views.driver_performance_pdf, name="driver_performance_pdf"),
    path("maintenance/", views.maintenance_report, name="maintenance_report"),
    path("maintenance/pdf/", views.maintenance_pdf, name="maintenance_pdf"),
    path("expenses/", views.expense_report, name="expense_report"),
    path("expenses/pdf/", views.expense_pdf, name="expense_pdf"),
    path("payments/", views.payment_report, name="payment_report"),
    path("payments/pdf/", views.payment_pdf, name="payment_pdf"),
    path("profit-loss/", views.profit_loss_report, name="profit_loss_report"),
    path("profit-loss/pdf/", views.profit_loss_pdf, name="profit_loss_pdf"),
]
