import base64
import logging

import pickle
from collections import Counter

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.db.models import Count
from django.http import FileResponse, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django_ratelimit.decorators import ratelimit

from admin_panel import backup_utils
from core.decorators import role_required
from core.models import AuditLog
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

User = get_user_model()
logger = logging.getLogger(__name__)


def _decode_user_id(session_data):
    try:
        decoded = base64.b64decode(session_data)
        data = pickle.loads(decoded)
        return data.get("_auth_user_id")
    except Exception:
        return None


@login_required
@role_required("admin")
def dashboard_view(request):
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()

    now = timezone.now()
    all_sessions = Session.objects.filter(expire_date__gt=now)
    session_count = all_sessions.count()

    user_sessions = Counter()
    for s in all_sessions:
        uid = _decode_user_id(s.session_data)
        if uid:
            user_sessions[uid] += 1

    active_sessions_count = sum(1 for v in user_sessions.values() if v > 0)
    unique_logged_in = len(user_sessions)

    outstanding = OutstandingToken.objects.count()
    blacklisted = BlacklistedToken.objects.count()

    return render(request, "admin_panel/dashboard.html", {
        "total_users": total_users,
        "active_users": active_users,
        "session_count": session_count,
        "active_sessions_count": active_sessions_count,
        "unique_logged_in": unique_logged_in,
        "outstanding_tokens": outstanding,
        "blacklisted_tokens": blacklisted,
        "section": "dashboard",
    })


@login_required
@role_required("admin")
def sessions_view(request):
    now = timezone.now()
    all_sessions = Session.objects.filter(expire_date__gt=now).order_by("-expire_date")
    session_list = []
    for s in all_sessions:
        uid = _decode_user_id(s.session_data)
        user = None
        if uid:
            try:
                user = User.objects.get(pk=uid)
            except User.DoesNotExist:
                pass
        session_list.append({
            "session_key": s.session_key,
            "user": user,
            "expire_date": s.expire_date,
            "created_at": s.expire_date - timezone.timedelta(days=14),
        })

    return render(request, "admin_panel/sessions.html", {
        "sessions": session_list,
        "section": "sessions",
    })


@ratelimit(key="ip", rate="10/m", method="POST", block=True)
@login_required
@role_required("admin")
def delete_session_view(request, session_key):
    if request.method == "POST":
        Session.objects.filter(session_key=session_key).delete()
        logger.info("Admin %s force-logged out session %s", request.user.username, session_key)
    return redirect("admin_sessions")


@login_required
@role_required("admin")
def admin_session_modal_delete(request, session_key):
    session = get_object_or_404(Session, session_key=session_key)
    username = None
    try:
        data = session.get_decoded()
        user_id = data.get("_auth_user_id")
        if user_id:
            User = get_user_model()
            user = User.objects.filter(pk=user_id).first()
            if user:
                username = user.username
    except Exception:
        pass
    if request.method == "POST":
        session.delete()
        logger.info("Admin %s force-logged out session %s", request.user.username, session_key)
        response = HttpResponse()
        response["HX-Trigger"] = "closeModal"
        response["HX-Redirect"] = reverse("admin_sessions")
        return response
    return render(request, "admin_panel/_session_delete_modal.html", {
        "session_key": session_key,
        "username": username,
    })


@login_required
@role_required("admin")
def tokens_view(request):
    now = timezone.now()
    outstanding = OutstandingToken.objects.select_related("user").order_by("-created_at")
    blacklisted_ids = set(
        BlacklistedToken.objects.values_list("token_id", flat=True)
    )
    token_list = []
    for t in outstanding:
        token_list.append({
            "id": t.id,
            "user": t.user,
            "jti": t.jti,
            "created_at": t.created_at,
            "expires_at": t.expires_at,
            "is_blacklisted": t.id in blacklisted_ids,
        })
    return render(request, "admin_panel/tokens.html", {
        "tokens": token_list,
        "section": "tokens",
    })


@ratelimit(key="ip", rate="10/m", method="POST", block=True)
@login_required
@role_required("admin")
def revoke_token_view(request, token_id):
    if request.method == "POST":
        token = get_object_or_404(OutstandingToken, id=token_id)
        BlacklistedToken.objects.get_or_create(token=token)
        logger.info(
            "Admin %s revoked token %s for user %s",
            request.user.username,
            token.jti,
            token.user,
        )
    return redirect("admin_tokens")


@login_required
@role_required("admin")
def audit_log_view(request):
    page = request.GET.get("page", 1)
    action = request.GET.get("action", "")
    model = request.GET.get("model", "")
    user_id = request.GET.get("user", "")

    logs = AuditLog.objects.select_related("user", "content_type")
    if action:
        logs = logs.filter(action=action)
    if model:
        logs = logs.filter(content_type__model=model)
    if user_id:
        logs = logs.filter(user_id=user_id)

    try:
        page = int(page)
    except ValueError:
        page = 1
    page_size = 50
    total = logs.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    offset = (page - 1) * page_size

    logs_page = logs[offset : offset + page_size]

    model_choices = (
        AuditLog.objects.values_list("content_type__model", flat=True)
        .distinct()
        .order_by("content_type__model")
    )

    return render(request, "admin_panel/audit_log.html", {
        "logs": logs_page,
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "action_filter": action,
        "model_filter": model,
        "user_filter": user_id,
        "model_choices": model_choices,
        "section": "audit",
    })

def _database_label(kind):
    return {
        "postgresql": "PostgreSQL",
        "sqlite": "SQLite",
    }.get(kind, "Unsupported")


def _audit_backup_action(request, action, object_repr, changes):
    AuditLog.objects.create(
        user=request.user,
        action=action,
        object_repr=object_repr,
        changes=changes,
        ip_address=request.META.get("REMOTE_ADDR"),
    )


@login_required
@role_required("admin")
def backup_view(request):
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "create":
                backup = backup_utils.create_backup()
                _audit_backup_action(
                    request,
                    "create",
                    f"Database backup: {backup.name}",
                    {"filename": backup.name, "action": "created"},
                )
                messages.success(request, f"Backup created: {backup.name}")

            elif action == "import":
                backup = backup_utils.save_uploaded_backup(request.FILES.get("backup_file"))
                _audit_backup_action(
                    request,
                    "create",
                    f"Backup uploaded: {backup.name}",
                    {"filename": backup.name, "action": "uploaded"},
                )
                messages.success(request, f"Backup file uploaded: {backup.name}")

            elif action == "restore":
                filename = request.POST.get("filename", "").strip()
                if not filename:
                    raise backup_utils.BackupError("No backup file specified.")

                result = backup_utils.restore_backup(filename)
                _audit_backup_action(
                    request,
                    "create",
                    f"Database restored: {result.restored_backup.name}",
                    {
                        "filename": result.restored_backup.name,
                        "action": "restore",
                        "pre_restore_backup": result.pre_restore_backup.name,
                    },
                )
                messages.success(
                    request,
                    f"Database restored from {result.restored_backup.name}. "
                    f"Current data backed up as {result.pre_restore_backup.name}.",
                )

            else:
                messages.error(request, "Unknown backup action.")
        except backup_utils.BackupError as exc:
            messages.error(request, str(exc))
        return redirect("admin_backup")

    database_kind = backup_utils.database_kind()

    return render(request, "admin_panel/backup.html", {
        "backups": backup_utils.list_backups(database_kind),
        "allowed_ext": backup_utils.allowed_extension(database_kind),
        "database_kind": database_kind,
        "database_label": _database_label(database_kind),
        "section": "backup",
    })


@login_required
@role_required("admin")
def backup_export_view(request, filename):
    backup_path = backup_utils.safe_backup_path(filename)
    if not backup_path or not backup_path.exists() or not backup_path.is_file():
        return HttpResponseBadRequest("Backup file not found.")
    return FileResponse(
        open(backup_path, "rb"),
        as_attachment=True,
        filename=filename,
        content_type="application/octet-stream",
    )
