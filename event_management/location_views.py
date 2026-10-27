from django.http import JsonResponse
from django.views.decorators.http import require_GET

from .location import LocationSearchError, search_locations
from .permissions import eo_required


@eo_required
@require_GET
def location_search(request):
    try:
        results = search_locations(request.GET.get("q", ""))
    except LocationSearchError as exc:
        data = {"error": str(exc)}
        if exc.retry_after is not None:
            data["retry_after"] = exc.retry_after
        response = JsonResponse(data, status=exc.status)
        if exc.retry_after is not None:
            response["Retry-After"] = str(exc.retry_after)
        response["Cache-Control"] = "no-store"
        return response
    response = JsonResponse({"results": results})
    response["Cache-Control"] = "no-store"
    return response
