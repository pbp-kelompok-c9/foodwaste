from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_safe

from .forms import EventForm
from .models import Event
from .permissions import eo_required, is_eo


@require_safe
def main(request):
    query = request.GET.get("q", "").strip()[:200]
    events = Event.objects.select_related("created_by")
    if query:
        events = events.filter(Q(name__icontains=query) | Q(location__icontains=query))
    page = Paginator(events, 12).get_page(request.GET.get("page"))
    return render(request, "event_management/main.html", {
        "events": page.object_list,
        "page_obj": page,
        "q": query,
        "is_eo": is_eo(request.user),
    })


@require_safe
def event_detail(request, event_id):
    event = get_object_or_404(Event.objects.select_related("created_by"), pk=event_id)
    return render(request, "event_management/detail.html", {
        "event": event,
        "is_owner": is_eo(request.user) and event.created_by_id == request.user.pk,
    })


@eo_required
@require_http_methods(["GET", "POST"])
def event_create(request):
    form = EventForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        event = form.save(commit=False)
        event.created_by = request.user
        event.save()
        messages.success(request, "Acara berhasil dibuat.")
        return redirect("event_management:detail", event_id=event.pk)
    return render(request, "event_management/form.html", {
        "form": form, "title": "Tambah acara",
    })


@eo_required
@require_http_methods(["GET", "POST"])
def event_update(request, event_id):
    event = get_object_or_404(Event, pk=event_id, created_by=request.user)
    form = EventForm(request.POST if request.method == "POST" else None, instance=event)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Acara berhasil diperbarui.")
        return redirect("event_management:detail", event_id=event.pk)
    return render(request, "event_management/form.html", {
        "form": form, "title": "Edit acara", "event": event,
    })


@eo_required
@require_http_methods(["GET", "POST"])
def event_delete(request, event_id):
    event = get_object_or_404(Event, pk=event_id, created_by=request.user)
    if request.method == "POST":
        try:
            event.delete()
        except ProtectedError:
            messages.error(request, "Acara tidak bisa dihapus karena sudah memiliki laporan.")
            return redirect("event_management:detail", event_id=event.pk)
        messages.success(request, "Acara berhasil dihapus.")
        return redirect("event_management:main")
    return render(request, "event_management/confirm_delete.html", {"event": event})
