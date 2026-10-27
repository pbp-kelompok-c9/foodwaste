
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models.deletion import ProtectedError
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from .models import Event
from .forms import EventForm


def eo_required(view_func):
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        is_eo = request.user.groups.filter(name="EO").exists()

        if not is_eo:
            raise PermissionDenied("Hanya EO yang boleh mengelola event.")

        return view_func(request, *args, **kwargs)

    return wrapper


def main(request):
    events = Event.objects.select_related(
        "created_by"
    ).order_by("-event_date")

    is_eo = (
        request.user.is_authenticated
        and request.user.groups.filter(name="EO").exists()
    )

    return render(request, "event_management/main.html", {
        "events": events,
        "is_eo": is_eo,
    })


def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)

    is_owner = (
        request.user.is_authenticated
        and event.created_by_id == request.user.id
        and request.user.groups.filter(name="EO").exists()
    )

    return render(request, "event_management/detail.html", {
        "event": event,
        "is_owner": is_owner,
    })


@eo_required
def event_create(request):
    if request.method == "POST":
        form = EventForm(request.POST)

        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            return redirect("event_management:main")
    else:
        form = EventForm()

    return render(request, "event_management/form.html", {
        "form": form,
        "title": "Tambah Event",
    })


@eo_required
def event_update(request, event_id):
    event = get_object_or_404(
        Event, pk=event_id, created_by=request.user
    )

    if request.method == "POST":
        form = EventForm(request.POST, instance=event)

        if form.is_valid():
            form.save()
            return redirect("event_management:detail", event_id=event.id)
    else:
        form = EventForm(instance=event)

    return render(request, "event_management/form.html", {
        "form": form,
        "title": "Edit Event",
    })


@eo_required
def event_delete(request, event_id):
    event = get_object_or_404(
        Event, pk=event_id, created_by=request.user
    )

    if request.method == "POST":
        try:
            event.delete()
            messages.success(request, "Event berhasil dihapus.")
        except ProtectedError:
            messages.error(
                request,
                "Event tidak bisa dihapus karena sudah memiliki laporan."
            )

        return redirect("event_management:main")

    return render(
        request,
        "event_management/confirm_delete.html",
        {"event": event}
    )
