from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

router = DefaultRouter()
router.register("users", views.UserViewSet, basename="api-users")
router.register("profiles", views.ProfileViewSet, basename="api-profiles")
router.register("clients", views.ClientViewSet, basename="api-clients")
router.register("trucks", views.TruckViewSet, basename="api-trucks")
router.register("drivers", views.DriverViewSet, basename="api-drivers")
router.register("trips", views.TripViewSet, basename="api-trips")
router.register("cargo", views.CargoViewSet, basename="api-cargo")
router.register("maintenance", views.MaintenanceViewSet, basename="api-maintenance")
router.register("expenses", views.ExpenseViewSet, basename="api-expenses")
router.register("payments", views.PaymentViewSet, basename="api-payments")
router.register("notifications", views.NotificationViewSet, basename="api-notifications")

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="api-token-obtain-pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
    path("meta/choices/", views.ChoiceMetadataView.as_view(), name="api-choice-metadata"),
    path("dashboard/summary/", views.DashboardSummaryView.as_view(), name="api-dashboard-summary"),
    path("reports/trips/daily/", views.DailyTripReportView.as_view(), name="api-daily-trip-report"),
    path("reports/monthly-trips/", views.MonthlyTripReportView.as_view(), name="api-monthly-trip-report"),
    path("reports/trucks/utilization/", views.TruckUtilizationReportView.as_view(), name="api-truck-utilization-report"),
    path("reports/truck-utilization/", views.TruckUtilizationReportView.as_view(), name="api-truck-utilization-report-legacy"),
    path("reports/drivers/performance/", views.DriverPerformanceReportView.as_view(), name="api-driver-performance-report"),
    path("reports/maintenance/", views.MaintenanceReportView.as_view(), name="api-maintenance-report"),
    path("reports/expenses/", views.ExpenseReportView.as_view(), name="api-expense-report"),
    path("reports/payments/", views.PaymentReportView.as_view(), name="api-payment-report"),
    path("reports/profit-loss/", views.ProfitLossReportView.as_view(), name="api-profit-loss-report"),
    path("notifications/unread-count/", views.unread_notification_count, name="api-unread-count"),
    path("notifications/mark-all-read/", views.mark_all_notifications_read, name="api-mark-all-read"),
]

urlpatterns += router.urls
