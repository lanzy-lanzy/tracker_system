from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django_ratelimit.decorators import ratelimit
from drivers.models import Driver
from trucks.models import Truck
from .models import Profile


ALLOWED_PROFILE_IMAGE_TYPES = {"image/jpeg", "image/png"}


DRIVER_REQUIRED_FIELDS = {
    "contact_number": "Contact number",
    "license_number": "License number",
    "license_expiry": "License expiry",
}


def _user_form_context(edit_user=None):
    return {
        "edit_user": edit_user,
        "trucks": Truck.objects.filter(status="available"),
        "employment_statuses": Driver.EMPLOYMENT_STATUS,
    }


def _driver_full_name(user):
    return user.get_full_name().strip() or user.username


def _missing_driver_fields(request):
    return [
        label
        for field, label in DRIVER_REQUIRED_FIELDS.items()
        if not request.POST.get(field, "").strip()
    ]


def _sync_driver_profile(user, request):
    driver, _ = Driver.objects.get_or_create(
        user=user,
        defaults={
            "full_name": _driver_full_name(user),
            "contact_number": request.POST.get("contact_number", "").strip(),
            "license_number": request.POST.get("license_number", "").strip(),
            "license_expiry": request.POST.get("license_expiry"),
        },
    )
    driver.full_name = _driver_full_name(user)
    driver.contact_number = request.POST.get("contact_number", "").strip()
    driver.address = request.POST.get("address", "").strip()
    driver.license_number = request.POST.get("license_number", "").strip()
    driver.license_expiry = request.POST.get("license_expiry")
    driver.assigned_truck_id = request.POST.get("assigned_truck") or None
    driver.employment_status = request.POST.get("employment_status", "active")
    driver.emergency_contact_name = request.POST.get("emergency_contact_name", "").strip()
    driver.emergency_contact_number = request.POST.get("emergency_contact_number", "").strip()
    driver.remarks = request.POST.get("remarks", "").strip()
    driver.save()
    return driver


def _save_profile_picture(profile, uploaded):
    if not uploaded:
        return
    content_type = uploaded.content_type or ""
    if content_type not in ALLOWED_PROFILE_IMAGE_TYPES:
        raise ValueError("Only JPG and PNG profile pictures are allowed.")
    profile.profile_picture_data = uploaded.read()
    profile.profile_picture_mime_type = content_type
    profile.profile_picture_filename = uploaded.name
    profile.profile_picture = None


@ratelimit(key="ip", rate="10/m", method="POST", block=True)
def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
                return redirect(next_url)
            return redirect("dashboard")
        messages.error(request, "Invalid username or password.")
    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def profile_view(request):
    return render(request, "accounts/profile.html", {"profile_user": request.user})


@ratelimit(key="ip", rate="10/m", method="POST", block=True)
@login_required
def profile_edit_view(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        user.email = request.POST.get("email", "")
        user.save()
        profile = user.profile
        profile.phone = request.POST.get("phone", "")
        profile.address = request.POST.get("address", "")
        try:
            _save_profile_picture(profile, request.FILES.get("profile_picture"))
        except ValueError as exc:
            messages.error(request, str(exc))
            return render(request, "accounts/profile_edit.html")
        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("profile")
    return render(request, "accounts/profile_edit.html")


@ratelimit(key="ip", rate="10/m", method="POST", block=True)
@login_required
def profile_edit_modal_view(request):
    if request.method == "POST":
        user = request.user
        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        user.email = request.POST.get("email", "")
        user.save()
        profile = user.profile
        profile.phone = request.POST.get("phone", "")
        profile.address = request.POST.get("address", "")
        try:
            _save_profile_picture(profile, request.FILES.get("profile_picture"))
        except ValueError as exc:
            return render(request, "accounts/_profile_edit_modal.html", {
                "user": request.user,
                "error": str(exc),
            })
        profile.save()
        response = HttpResponse()
        response["HX-Trigger"] = "profileUpdated"
        response["HX-Redirect"] = reverse("profile")
        return response
    return render(request, "accounts/_profile_edit_modal.html", {"user": request.user})


@login_required
def profile_picture_view(request, pk):
    profile = get_object_or_404(Profile, user_id=pk)
    if profile.profile_picture_data:
        response = HttpResponse(
            bytes(profile.profile_picture_data),
            content_type=profile.profile_picture_mime_type or "application/octet-stream",
        )
        response["Cache-Control"] = "private, max-age=3600"
        return response
    if profile.profile_picture:
        return FileResponse(profile.profile_picture.open("rb"), content_type="application/octet-stream")
    raise Http404("Profile picture not found.")


@login_required
def user_list_view(request):
    if request.user.profile.role not in ["admin"]:
        messages.error(request, "Access denied.")
        return redirect("dashboard")
    users = User.objects.all().select_related("profile")
    return render(request, "accounts/user_list.html", {"users": users})


@ratelimit(key="ip", rate="5/m", method="POST", block=True)
@login_required
def user_create_view(request):
    if request.user.profile.role not in ["admin"]:
        messages.error(request, "Access denied.")
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")
        if role == "driver":
            missing_fields = _missing_driver_fields(request)
            if missing_fields:
                messages.error(request, f"Driver profile requires: {', '.join(missing_fields)}.")
                return render(request, "accounts/user_form.html", _user_form_context())
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=request.POST.get("first_name", ""),
                last_name=request.POST.get("last_name", ""),
            )
            user.profile.role = role
            user.profile.save()
            if role == "driver":
                _sync_driver_profile(user, request)
            messages.success(request, "User created successfully.")
            return redirect("user_list")
    return render(request, "accounts/user_form.html", _user_form_context())


@ratelimit(key="ip", rate="5/m", method="POST", block=True)
@login_required
def user_edit_view(request, pk):
    if request.user.profile.role not in ["admin"]:
        messages.error(request, "Access denied.")
        return redirect("dashboard")
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        role = request.POST.get("role", user.profile.role)
        if role == "driver":
            missing_fields = _missing_driver_fields(request)
            if missing_fields:
                messages.error(request, f"Driver profile requires: {', '.join(missing_fields)}.")
                return render(request, "accounts/user_form.html", _user_form_context(user))
        user.email = request.POST.get("email", "")
        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        user.save()
        user.profile.role = role
        user.profile.save()
        if request.POST.get("password"):
            user.set_password(request.POST.get("password"))
            user.save()
        if role == "driver":
            _sync_driver_profile(user, request)
        messages.success(request, "User updated successfully.")
        return redirect("user_list")
    return render(request, "accounts/user_form.html", _user_form_context(user))


@login_required
def user_toggle_active_view(request, pk):
    if request.user.profile.role not in ["admin"]:
        messages.error(request, "Access denied.")
        return redirect("dashboard")
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect("user_list")
    user.is_active = not user.is_active
    user.save()
    status = "activated" if user.is_active else "deactivated"
    messages.success(request, f"User {user.username} {status} successfully.")
    return redirect("user_list")
