from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Profile


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            next_url = request.GET.get("next", "dashboard")
            return redirect(next_url)
        messages.error(request, "Invalid username or password.")
    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def profile_view(request):
    return render(request, "accounts/profile.html", {"profile_user": request.user})


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
        profile.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("profile")
    return render(request, "accounts/profile_edit.html")


@login_required
def user_list_view(request):
    if request.user.profile.role not in ["admin"]:
        messages.error(request, "Access denied.")
        return redirect("dashboard")
    users = User.objects.all().select_related("profile")
    return render(request, "accounts/user_list.html", {"users": users})


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
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.profile.role = role
            user.profile.save()
            messages.success(request, "User created successfully.")
            return redirect("user_list")
    return render(request, "accounts/user_form.html")


@login_required
def user_edit_view(request, pk):
    if request.user.profile.role not in ["admin"]:
        messages.error(request, "Access denied.")
        return redirect("dashboard")
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        user.email = request.POST.get("email", "")
        user.first_name = request.POST.get("first_name", "")
        user.last_name = request.POST.get("last_name", "")
        user.save()
        user.profile.role = request.POST.get("role", user.profile.role)
        user.profile.save()
        if request.POST.get("password"):
            user.set_password(request.POST.get("password"))
            user.save()
        messages.success(request, "User updated successfully.")
        return redirect("user_list")
    return render(request, "accounts/user_form.html", {"edit_user": user})
