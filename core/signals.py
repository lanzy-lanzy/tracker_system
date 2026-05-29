from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User
from django.utils import timezone

from .models import AuditLog


IGNORED_MODELS = {
    "auditlog",
    "session",
    "accessattempt",
    "accessattemptexpiration",
    "blacklistedtoken",
    "outstandingtoken",
    "logentry",
}


def _get_ip(request):
    if request:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
    return None


def _get_request():
    import threading
    from django.core.handlers.wsgi import WSGIRequest

    for obj_id, obj in threading.current_thread().__dict__.items():
        if isinstance(obj, WSGIRequest) or (
            hasattr(obj, "META") and hasattr(obj, "method")
        ):
            return obj

    request = getattr(threading.local(), "request", None)
    if request:
        return request
    return None


def _changed_fields(instance):
    if not instance.pk:
        return None
    try:
        old = instance.__class__.objects.get(pk=instance.pk)
    except instance.__class__.DoesNotExist:
        return None

    changes = {}
    for field in instance._meta.get_fields():
        if field.is_relation or getattr(field, "primary_key", False):
            continue
        name = field.name
        try:
            old_val = str(getattr(old, name, ""))
            new_val = str(getattr(instance, name, ""))
        except Exception:
            continue
        if old_val != new_val:
            changes[name] = {"from": old_val, "to": new_val}
    return changes if changes else None


def _log_action(sender, instance, action, request=None, **kwargs):
    model_name = sender._meta.model_name
    if model_name in IGNORED_MODELS:
        return

    if not request:
        request = _get_request()

    changes = None
    if action == "update":
        changes = _changed_fields(instance)
        if not changes:
            return

    user = None
    ip = None
    if request:
        user = getattr(request, "user", None)
        if user and not user.is_authenticated:
            user = None
        ip = _get_ip(request)

    AuditLog.objects.create(
        user=user,
        action=action,
        content_type=ContentType.objects.get_for_model(instance),
        object_id=instance.pk,
        object_repr=str(instance)[:255],
        changes=changes,
        ip_address=ip,
    )


def auto_audit_post_save(sender, instance, created, **kwargs):
    request = kwargs.get("request")
    action = "create" if created else "update"
    _log_action(sender, instance, action, request=request)


def auto_audit_post_delete(sender, instance, **kwargs):
    request = kwargs.get("request")
    _log_action(sender, instance, "delete", request=request)


def register_all_models():
    from django.apps import apps

    for model in apps.get_models():
        model_name = model._meta.model_name
        if model_name not in IGNORED_MODELS:
            post_save.connect(auto_audit_post_save, sender=model, weak=False)
            post_delete.connect(auto_audit_post_delete, sender=model, weak=False)
