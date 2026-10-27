from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def is_eo(user):
    """EO membership is independent of staff and superuser flags."""
    return user.is_authenticated and user.is_active and user.groups.filter(name="EO").exists()


def can_manage_events(user):
    return user.is_authenticated and user.is_active and (user.is_superuser or is_eo(user))


def can_manage_event(user, event):
    return can_manage_events(user) and (user.is_superuser or event.created_by_id == user.pk)


def event_manager_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not can_manage_events(request.user):
            raise PermissionDenied("Hanya EO atau superuser yang boleh mengelola acara.")
        return view(request, *args, **kwargs)

    return wrapper
