from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification


@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(user=request.user)
    return render(request, "notifications/notification_list.html", {"notifications": notifications})


@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    if request.headers.get("HX-Request"):
        return render(request, "notifications/partials/notification_item.html", {"n": notification})
    return redirect(request.META.get("HTTP_REFERER", "notification_list"))


@login_required
def notification_mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    if request.headers.get("HX-Request"):
        return render(request, "notifications/partials/notification_badge.html", {"unread_count": 0})
    return redirect("notification_list")


@login_required
def unread_count(request):
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({"count": count})
