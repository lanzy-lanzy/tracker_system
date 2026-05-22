from django.urls import path
from . import views

urlpatterns = [
    path("", views.client_list_view, name="client_list"),
    path("create/", views.client_create_view, name="client_create"),
    path("<int:pk>/", views.client_detail_view, name="client_detail"),
    path("<int:pk>/edit/", views.client_edit_view, name="client_edit"),
    path("<int:pk>/delete/", views.client_delete_view, name="client_delete"),
    path("create/modal/", views.client_modal_create, name="client_modal_create"),
    path("<int:pk>/edit/modal/", views.client_modal_edit, name="client_modal_edit"),
    path("<int:pk>/detail/modal/", views.client_modal_detail, name="client_modal_detail"),
    path("<int:pk>/delete/modal/", views.client_modal_delete, name="client_modal_delete"),
]
