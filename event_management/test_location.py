import io
import json
from datetime import timedelta
from urllib.error import HTTPError, URLError
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import OperationalError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .location import LocationSearchError, search_locations
from .models import LocationSearchState


SAMPLE = [{
    "display_name": "Universitas Indonesia, Depok, Jawa Barat",
    "lat": "-6.36212345",
    "lon": "106.82712345",
}]


@override_settings(
    NOMINATIM_SEARCH_URL="https://nominatim.openstreetmap.org/search",
    NOMINATIM_USER_AGENT="FoodWasteyTests/1.0 (+https://example.com/contact)",
)
class LocationClientTests(TestCase):
    def response(self, payload):
        return io.BytesIO(json.dumps(payload).encode("utf-8"))

    @patch("event_management.location.urlopen")
    def test_request_is_identified_bounded_and_coordinates_are_valid(self, upstream):
        upstream.return_value = self.response(SAMPLE)
        results = search_locations("Universitas Indonesia")
        self.assertEqual(results, [{
            "name": SAMPLE[0]["display_name"],
            "latitude": "-6.362123",
            "longitude": "106.827123",
        }])
        request = upstream.call_args.args[0]
        self.assertIn("format=jsonv2", request.full_url)
        self.assertIn("limit=5", request.full_url)
        self.assertIn("q=Universitas+Indonesia", request.full_url)
        self.assertEqual(request.get_header("User-agent"), "FoodWasteyTests/1.0 (+https://example.com/contact)")
        self.assertEqual(upstream.call_args.kwargs["timeout"], 5)

    @patch("event_management.location.urlopen")
    def test_normalized_cache_hits_do_not_consume_upstream_gate(self, upstream):
        upstream.return_value = self.response(SAMPLE)
        first = search_locations("  Universitas   Indonesia ")
        self.assertEqual(search_locations("universitas indonesia"), first)
        self.assertEqual(upstream.call_count, 1)

    @patch("event_management.location.urlopen")
    def test_empty_results_are_cached(self, upstream):
        upstream.return_value = self.response([])
        self.assertEqual(search_locations("Tempat Tidak Ada"), [])
        self.assertEqual(search_locations("tempat tidak ada"), [])
        upstream.assert_called_once()

    @patch("event_management.location.urlopen")
    def test_gate_applies_across_different_queries_and_all_users(self, upstream):
        upstream.side_effect = [self.response(SAMPLE), self.response(SAMPLE)]
        search_locations("Depok pertama")
        with self.assertRaises(LocationSearchError) as error:
            search_locations("Depok kedua")
        self.assertEqual(error.exception.status, 429)
        self.assertGreaterEqual(error.exception.retry_after, 1)
        self.assertEqual(upstream.call_count, 1)
        LocationSearchState.objects.filter(key="__gate__").update(
            expires_at=timezone.now() - timedelta(seconds=1)
        )
        search_locations("Depok kedua")
        self.assertEqual(upstream.call_count, 2)

    @patch("event_management.location.urlopen")
    def test_active_lease_prevents_another_upstream_request(self, upstream):
        LocationSearchState.objects.create(
            key="__gate__", expires_at=timezone.now() + timedelta(seconds=20)
        )
        with self.assertRaises(LocationSearchError) as error:
            search_locations("Jakarta")
        self.assertEqual(error.exception.status, 429)
        upstream.assert_not_called()

    @patch("event_management.location.urlopen")
    def test_expired_cache_is_refreshed(self, upstream):
        upstream.side_effect = [self.response(SAMPLE), self.response([])]
        search_locations("Jakarta")
        LocationSearchState.objects.all().update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(search_locations("Jakarta"), [])
        self.assertEqual(upstream.call_count, 2)

    @patch("event_management.location.urlopen")
    def test_switching_provider_does_not_reuse_old_provider_cache(self, upstream):
        upstream.side_effect = [self.response(SAMPLE), self.response([])]
        search_locations("Jakarta")
        LocationSearchState.objects.filter(key="__gate__").update(expires_at=timezone.now() - timedelta(seconds=1))
        with override_settings(NOMINATIM_SEARCH_URL="https://locations.example.com/search"):
            self.assertEqual(search_locations("Jakarta"), [])
        self.assertEqual(upstream.call_count, 2)

    @patch("event_management.location.urlopen")
    def test_invalid_queries_never_call_upstream(self, upstream):
        for query in ("", " a ", "ab", "x" * 201):
            with self.subTest(query=query), self.assertRaises(LocationSearchError) as error:
                search_locations(query)
            self.assertEqual(error.exception.status, 400)
        upstream.assert_not_called()

    @patch("event_management.location.urlopen")
    def test_configuration_must_use_https_and_identifying_agent(self, upstream):
        for endpoint in ("http://nominatim.openstreetmap.org/search", "https://user:password@example.com/search", "https://example.com/search?q=other", "https://example.com/search#fragment", "https://example.com:bad/search", "https://bad host/search", "file:///search"):
            with self.subTest(endpoint=endpoint), override_settings(NOMINATIM_SEARCH_URL=endpoint):
                with self.assertRaises(LocationSearchError):
                    search_locations("Jakarta")
        with override_settings(NOMINATIM_USER_AGENT=""):
            with self.assertRaises(LocationSearchError):
                search_locations("Jakarta")
        upstream.assert_not_called()

    @patch("event_management.location.urlopen")
    def test_invalid_result_rows_are_ignored_and_limit_is_enforced(self, upstream):
        payload = [None, {"display_name": "Invalid", "lat": "NaN", "lon": "1"}, {"display_name": "Invalid", "lat": "91", "lon": "1"}, {"display_name": "Invalid", "lat": "0", "lon": "181"}, {"display_name": "Invalid", "lat": "1e999999999", "lon": "0"}] + SAMPLE * 9
        upstream.return_value = self.response(payload)
        self.assertEqual(len(search_locations("Jakarta")), 5)

    @patch("event_management.location.urlopen")
    def test_long_result_names_fit_event_location_field(self, upstream):
        upstream.return_value = self.response([{**SAMPLE[0], "display_name": "J" * 300}])
        self.assertEqual(len(search_locations("Jakarta")[0]["name"]), 255)

    @patch("event_management.location.urlopen")
    def test_malformed_json_is_recoverable_and_gate_releases(self, upstream):
        upstream.return_value = io.BytesIO(b"invalid JSON")
        before = timezone.now()
        with self.assertRaises(LocationSearchError) as error:
            search_locations("Jakarta")
        self.assertEqual(error.exception.status, 503)
        gate = LocationSearchState.objects.get(key="__gate__")
        self.assertGreaterEqual(gate.expires_at, before + timedelta(seconds=1))
        self.assertLess(gate.expires_at, before + timedelta(seconds=5))

    @patch("event_management.location.urlopen")
    def test_non_list_response_is_rejected(self, upstream):
        upstream.return_value = self.response({"message": "error"})
        with self.assertRaises(LocationSearchError):
            search_locations("Jakarta")

    @patch("event_management.location.urlopen")
    def test_response_size_is_bounded(self, upstream):
        upstream.return_value = io.BytesIO(b" " * (64 * 1024 + 1))
        with self.assertRaises(LocationSearchError):
            search_locations("Jakarta")

    @patch("event_management.location.urlopen")
    def test_timeouts_and_network_errors_are_recoverable(self, upstream):
        for failure in (TimeoutError(), URLError("offline"), HTTPError("https://example.com", 500, "error", {}, None)):
            with self.subTest(failure=type(failure).__name__):
                LocationSearchState.objects.all().delete()
                upstream.side_effect = failure
                with self.assertRaises(LocationSearchError) as error:
                    search_locations("Jakarta")
                self.assertEqual(error.exception.status, 503)

    @patch("event_management.location.urlopen")
    def test_provider_rate_limit_is_respected(self, upstream):
        upstream.side_effect = HTTPError("https://example.com", 429, "rate limited", {"Retry-After": "120"}, None)
        before = timezone.now()
        with self.assertRaises(LocationSearchError) as error:
            search_locations("Jakarta")
        self.assertEqual(error.exception.status, 429)
        self.assertEqual(error.exception.retry_after, 120)
        self.assertGreaterEqual(LocationSearchState.objects.get(key="__gate__").expires_at, before + timedelta(seconds=120))

    @patch("event_management.location.urlopen")
    @patch("event_management.location._cached", side_effect=OperationalError("database unavailable"))
    def test_database_unavailable_fails_closed(self, cached, upstream):
        with self.assertRaises(LocationSearchError) as error:
            search_locations("Jakarta")
        self.assertEqual(error.exception.status, 503)
        upstream.assert_not_called()


class LocationEndpointTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        user_model = get_user_model()
        cls.eo = user_model.objects.create_user("location-eo", password="test-password")
        cls.eo.groups.add(Group.objects.get_or_create(name="EO")[0])
        cls.participant = user_model.objects.create_user("location-participant", password="test-password")
        cls.staff = user_model.objects.create_user("location-staff", password="test-password", is_staff=True)
        cls.superuser = user_model.objects.create_superuser("location-superuser", password="test-password")

    def setUp(self):
        self.url = reverse("event_management:location_search")

    @patch("event_management.location_views.search_locations")
    def test_anonymous_is_redirected_and_non_eo_is_forbidden(self, search):
        self.assertEqual(self.client.get(self.url, {"q": "Jakarta"}).status_code, 302)
        for user in (self.participant, self.staff):
            self.client.force_login(user)
            self.assertEqual(self.client.get(self.url, {"q": "Jakarta"}).status_code, 403)
        search.assert_not_called()

    @patch("event_management.location_views.search_locations", return_value=[])
    def test_eo_without_staff_can_search_and_post_is_rejected(self, search):
        self.assertFalse(self.eo.is_staff)
        self.client.force_login(self.eo)
        response = self.client.get(self.url, {"q": "Jakarta"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": []})
        self.assertEqual(response["Cache-Control"], "no-store")
        self.assertEqual(self.client.post(self.url, {"q": "Jakarta"}).status_code, 405)
        search.assert_called_once_with("Jakarta")

    @patch("event_management.location_views.search_locations")
    def test_error_contract_and_retry_header(self, search):
        self.client.force_login(self.eo)
        search.side_effect = LocationSearchError("Tunggu sebentar.", status=429, retry_after=2)
        response = self.client.get(self.url, {"q": "Jakarta"})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json(), {"error": "Tunggu sebentar.", "retry_after": 2})
        self.assertEqual(response["Retry-After"], "2")

    @patch("event_management.location_views.search_locations", return_value=[])
    def test_superuser_without_eo_group_can_search_locations(self, search):
        self.assertFalse(self.superuser.groups.exists())
        self.client.force_login(self.superuser)
        response = self.client.get(self.url, {"q": "Jakarta"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"results": []})
        self.assertEqual(self.client.post(self.url, {"q": "Jakarta"}).status_code, 405)
        search.assert_called_once_with("Jakarta")
