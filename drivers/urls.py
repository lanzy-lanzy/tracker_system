from django.urls import path
from . import views

urlpatterns = [
    path("", views.driver_list_view, name="driver_list"),
    path("dashboard/", views.driver_dashboard_view, name="driver_dashboard"),
    path("create/", views.driver_create_view, name="driver_create"),
    path("<int:pk>/", views.driver_detail_view, name="driver_detail"),
    path("<int:pk>/edit/", views.driver_edit_view, name="driver_edit"),
    path("<int:pk>/delete/", views.driver_delete_view, name="driver_delete"),
    path("create/modal/", views.driver_modal_create, name="driver_modal_create"),
    path("<int:pk>/edit/modal/", views.driver_modal_edit, name="driver_modal_edit"),
    path("<int:pk>/detail/modal/", views.driver_modal_detail, name="driver_modal_detail"),
    path("<int:pk>/delete/modal/", views.driver_modal_delete, name="driver_modal_delete"),
]
