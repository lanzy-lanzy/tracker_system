from django.urls import path
from . import views

urlpatterns = [
    path("", views.expense_list_view, name="expense_list"),
    path("pdf/", views.expense_list_pdf, name="expense_list_pdf"),
    path("create/", views.expense_create_view, name="expense_create"),
    path("<int:pk>/edit/", views.expense_edit_view, name="expense_edit"),
    path("<int:pk>/delete/", views.expense_delete_view, name="expense_delete"),
    path("create/modal/", views.expense_modal_create, name="expense_modal_create"),
    path("<int:pk>/edit/modal/", views.expense_modal_edit, name="expense_modal_edit"),
    path("<int:pk>/delete/modal/", views.expense_modal_delete, name="expense_modal_delete"),
]
