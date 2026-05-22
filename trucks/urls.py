from django.urls import path
from . import views

urlpatterns = [
    path("", views.truck_list_view, name="truck_list"),
    path("create/", views.truck_create_view, name="truck_create"),
    path("<int:pk>/", views.truck_detail_view, name="truck_detail"),
    path("<int:pk>/edit/", views.truck_edit_view, name="truck_edit"),
    path("<int:pk>/delete/", views.truck_delete_view, name="truck_delete"),
    path("create/modal/", views.truck_modal_create, name="truck_modal_create"),
    path("<int:pk>/edit/modal/", views.truck_modal_edit, name="truck_modal_edit"),
    path("<int:pk>/detail/modal/", views.truck_modal_detail, name="truck_modal_detail"),
    path("<int:pk>/delete/modal/", views.truck_modal_delete, name="truck_modal_delete"),
]
