from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def is_eo(user):
    """EO membership is independent of staff and superuser flags."""
    return user.is_authenticated and user.is_active and user.groups.filter(name="EO").exists()


def eo_required(view):
    @wraps(view)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not is_eo(request.user):
            raise PermissionDenied("Hanya EO yang boleh mengelola acara.")
        return view(request, *args, **kwargs)

    return wrapper
