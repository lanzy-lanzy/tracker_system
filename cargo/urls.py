from django.urls import path
from . import views

urlpatterns = [
    path("", views.cargo_list_view, name="cargo_list"),
    path("create/", views.cargo_create_view, name="cargo_create"),
    path("<int:pk>/edit/", views.cargo_edit_view, name="cargo_edit"),
    path("<int:pk>/delete/", views.cargo_delete_view, name="cargo_delete"),
    path("create/modal/", views.cargo_modal_create, name="cargo_modal_create"),
    path("<int:pk>/edit/modal/", views.cargo_modal_edit, name="cargo_modal_edit"),
    path("<int:pk>/delete/modal/", views.cargo_modal_delete, name="cargo_modal_delete"),
]
