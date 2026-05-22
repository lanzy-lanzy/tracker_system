from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect


def root_redirect(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return redirect("login")


urlpatterns = [
    path("", root_redirect, name="root"),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("trucks/", include("trucks.urls")),
    path("drivers/", include("drivers.urls")),
    path("clients/", include("clients.urls")),
    path("trips/", include("trips.urls")),
    path("cargo/", include("cargo.urls")),
    path("maintenance/", include("maintenance.urls")),
    path("expenses/", include("expenses.urls")),
    path("payments/", include("payments.urls")),
    path("reports/", include("reports.urls")),
    path("notifications/", include("notifications.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
