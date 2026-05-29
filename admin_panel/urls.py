from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard_view, name="admin_dashboard"),
    path("sessions/", views.sessions_view, name="admin_sessions"),
    path("sessions/<str:session_key>/delete/", views.delete_session_view, name="admin_delete_session"),
    path("sessions/<str:session_key>/delete/modal/", views.admin_session_modal_delete, name="admin_session_modal_delete"),
    path("tokens/", views.tokens_view, name="admin_tokens"),
    path("tokens/<int:token_id>/revoke/", views.revoke_token_view, name="admin_revoke_token"),
    path("audit-log/", views.audit_log_view, name="admin_audit_log"),
    path("backup/", views.backup_view, name="admin_backup"),
    path("backup/export/<str:filename>/", views.backup_export_view, name="admin_backup_export"),
]
