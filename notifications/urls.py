from django.urls import path
from . import views

urlpatterns = [
    path("", views.notification_list_view, name="notification_list"),
    path("mark-read/<int:pk>/", views.notification_mark_read, name="notification_mark_read"),
    path("mark-all-read/", views.notification_mark_all_read, name="notification_mark_all_read"),
    path("unread-count/", views.unread_count, name="unread_count"),
]
