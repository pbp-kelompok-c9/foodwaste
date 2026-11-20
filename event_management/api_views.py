from django.db.models import Q
from django.db.models.deletion import ProtectedError
from rest_framework import generics, permissions, serializers
from rest_framework.pagination import PageNumberPagination

from .models import Event
from .permissions import can_manage_event, can_manage_events
from .serializers import EventSerializer


class EventPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or can_manage_events(request.user)

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS or can_manage_event(request.user, obj)


class EventPagination(PageNumberPagination):
    page_size = 12


class EventListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = EventSerializer
    permission_classes = [EventPermission]
    pagination_class = EventPagination

    def get_queryset(self):
        events = Event.objects.select_related("created_by")
        query = self.request.query_params.get("q", "").strip()
        if query:
            events = events.filter(Q(name__icontains=query) | Q(location__icontains=query))
        return events

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class EventDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Event.objects.select_related("created_by")
    serializer_class = EventSerializer
    permission_classes = [EventPermission]

    def perform_destroy(self, instance):
        try:
            instance.delete()
        except ProtectedError:
            raise serializers.ValidationError(
                {"detail": "Acara tidak bisa dihapus karena sudah memiliki laporan."}
            )
