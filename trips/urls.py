from django.urls import path
from . import views

urlpatterns = [
    path("", views.trip_list_view, name="trip_list"),
    path("create/", views.trip_create_view, name="trip_create"),
    path("<int:pk>/", views.trip_detail_view, name="trip_detail"),
    path("<int:pk>/edit/", views.trip_edit_view, name="trip_edit"),
    path("<int:pk>/delete/", views.trip_delete_view, name="trip_delete"),
    path("<int:pk>/status/<str:status>/", views.trip_update_status, name="trip_update_status"),
    path("<int:pk>/upload-proof/", views.trip_upload_proof, name="trip_upload_proof"),
    path("filter/", views.trip_filter_view, name="trip_filter"),
    path("search/", views.trip_search_view, name="trip_search"),
    path("create/modal/", views.trip_modal_create, name="trip_modal_create"),
    path("<int:pk>/edit/modal/", views.trip_modal_edit, name="trip_modal_edit"),
    path("<int:pk>/detail/modal/", views.trip_modal_detail, name="trip_modal_detail"),
    path("<int:pk>/delete/modal/", views.trip_modal_delete, name="trip_modal_delete"),
]
