from rest_framework import status, viewsets
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Report
from .serializers import ReportSerializer


class ReportViewSet(viewsets.ModelViewSet):
    """
    list     GET    /api/reports/?name=<text>
    create   POST   /api/reports/
    retrieve GET    /api/reports/<uuid>/
    update   PUT    /api/reports/<uuid>/
    partial  PATCH  /api/reports/<uuid>/
    destroy  DELETE /api/reports/<uuid>/
    """

    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        qs = Report.objects.filter(reported_by=self.request.user).select_related(
            "related_event", "reported_by"
        )

        if self.action == "list":
            name = self.request.query_params.get("name", "").strip()
            if name:
                qs = qs.filter(food_name__icontains=name)

        return qs

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            {"message": "Laporan berhasil dibuat!", "report": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        response.data = {"message": "Laporan berhasil diedit!", "report": response.data}
        return response

    def destroy(self, request, *args, **kwargs):
        self.get_object().delete()
        return Response(
            {"message": "Laporan berhasil dihapus!"}, status=status.HTTP_200_OK
        )