from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            role = getattr(getattr(request.user, "profile", None), "role", None)
            if role not in allowed_roles:
                messages.error(request, "Access denied.")
                return redirect("dashboard")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
