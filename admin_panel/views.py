import base64
import logging

import pickle
from collections import Counter

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.sessions.models import Session
from django.db.models import Count
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone

from core.decorators import role_required
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


@login_required
@role_required("admin")
def delete_session_view(request, session_key):
    if request.method == "POST":
        Session.objects.filter(session_key=session_key).delete()
        logger.info("Admin %s force-logged out session %s", request.user.username, session_key)
    return redirect("admin_sessions")


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
