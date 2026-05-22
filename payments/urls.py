from django.urls import path
from . import views

urlpatterns = [
    path("", views.payment_list_view, name="payment_list"),
    path("create/", views.payment_create_view, name="payment_create"),
    path("<int:pk>/edit/", views.payment_edit_view, name="payment_edit"),
    path("<int:pk>/delete/", views.payment_delete_view, name="payment_delete"),
    path("create/modal/", views.payment_modal_create, name="payment_modal_create"),
    path("<int:pk>/edit/modal/", views.payment_modal_edit, name="payment_modal_edit"),
    path("<int:pk>/delete/modal/", views.payment_modal_delete, name="payment_modal_delete"),
]
