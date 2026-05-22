from django.urls import path
from . import views

urlpatterns = [
    path("", views.maintenance_list_view, name="maintenance_list"),
    path("create/", views.maintenance_create_view, name="maintenance_create"),
    path("<int:pk>/", views.maintenance_detail_view, name="maintenance_detail"),
    path("<int:pk>/edit/", views.maintenance_edit_view, name="maintenance_edit"),
    path("<int:pk>/delete/", views.maintenance_delete_view, name="maintenance_delete"),
    path("create/modal/", views.maintenance_modal_create, name="maintenance_modal_create"),
    path("<int:pk>/detail/modal/", views.maintenance_modal_detail, name="maintenance_modal_detail"),
    path("<int:pk>/edit/modal/", views.maintenance_modal_edit, name="maintenance_modal_edit"),
    path("<int:pk>/delete/modal/", views.maintenance_modal_delete, name="maintenance_modal_delete"),
]
