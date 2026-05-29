def get_user_role(user):
    return getattr(getattr(user, "profile", None), "role", None)


def is_driver(user):
    return get_user_role(user) == "driver"


def is_admin_or_dispatcher(user):
    role = get_user_role(user)
    return role in ("admin", "dispatcher")


def filter_trips_for_user(user, queryset):
    role = get_user_role(user)
    if role == "driver" and hasattr(user, "driver_profile"):
        return queryset.filter(assigned_driver=user.driver_profile)
    return queryset


def filter_cargo_for_user(user, queryset):
    role = get_user_role(user)
    if role == "driver" and hasattr(user, "driver_profile"):
        return queryset.filter(trip__assigned_driver=user.driver_profile)
    return queryset
