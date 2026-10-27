"""Small, explicitly triggered Nominatim client with a shared database gate."""

import hashlib
import json
import math
import time
from datetime import timedelta
from decimal import Decimal, DecimalException
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.conf import settings
from django.db import DatabaseError
from django.utils import timezone

from .models import LocationSearchState

MAX_RESULTS = 5
MAX_RESPONSE_BYTES = 64 * 1024
NETWORK_TIMEOUT = 5
RESPONSE_DEADLINE = 10
LEASE_SECONDS = 30
CACHE_SECONDS = 24 * 60 * 60


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        # Keep the configured provider fixed and avoid chains of network timeouts.
        return None


urlopen = build_opener(_NoRedirect).open


class LocationSearchError(Exception):
    def __init__(self, message, *, status=503, retry_after=None):
        super().__init__(message)
        self.status = status
        self.retry_after = retry_after


def _configuration():
    endpoint = getattr(
        settings, "NOMINATIM_SEARCH_URL", "https://nominatim.openstreetmap.org/search"
    ).strip()
    user_agent = getattr(
        settings,
        "NOMINATIM_USER_AGENT",
        "FoodWastey/1.0 (+https://github.com/pbp-kelompok-c9/foodwaste)",
    ).strip()
    try:
        parsed = urlsplit(endpoint)
        valid = (
            parsed.scheme == "https"
            and parsed.hostname
            and not any(character.isspace() for character in parsed.hostname)
            and (parsed.port is None or 1 <= parsed.port <= 65535)
            and not parsed.username
            and not parsed.password
            and not parsed.query
            and not parsed.fragment
        )
    except ValueError:
        valid = False
    if not valid or not user_agent or "\r" in user_agent or "\n" in user_agent:
        raise LocationSearchError("Layanan pencarian lokasi belum dikonfigurasi dengan benar.")
    return endpoint, user_agent


def _read_response(response, deadline):
    chunks = []
    length = 0
    while True:
        if time.monotonic() >= deadline:
            raise TimeoutError
        chunk = response.read1(min(8192, MAX_RESPONSE_BYTES + 1 - length))
        if not chunk:
            break
        length += len(chunk)
        if length > MAX_RESPONSE_BYTES:
            raise LocationSearchError("Respons layanan lokasi terlalu besar. Coba lokasi lain.")
        chunks.append(chunk)
    return b"".join(chunks)


def _coordinate(value, maximum):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number.copy_abs() > maximum:
            return None
        return format(number.quantize(Decimal("0.000001")), "f")
    except (DecimalException, ValueError, TypeError):
        return None


def _parse_results(payload):
    if not isinstance(payload, list):
        raise LocationSearchError("Layanan lokasi mengirim respons yang tidak dapat dibaca.")
    results = []
    for item in payload[:40]:
        if not isinstance(item, dict):
            continue
        name = item.get("display_name")
        latitude = _coordinate(item.get("lat"), 90)
        longitude = _coordinate(item.get("lon"), 180)
        if not isinstance(name, str) or not name.strip() or latitude is None or longitude is None:
            continue
        results.append({
            "name": " ".join(name.split())[:255],
            "latitude": latitude,
            "longitude": longitude,
        })
        if len(results) == MAX_RESULTS:
            break
    return results


def _fetch(query, endpoint, user_agent):
    params = urlencode({"q": query, "format": "jsonv2", "limit": MAX_RESULTS})
    request = Request(
        f"{endpoint}?{params}",
        headers={
            "User-Agent": user_agent,
            "Accept": "application/json",
            "Accept-Language": "id,en",
        },
    )
    try:
        deadline = time.monotonic() + RESPONSE_DEADLINE
        with urlopen(request, timeout=NETWORK_TIMEOUT) as response:
            body = _read_response(response, deadline)
        return _parse_results(json.loads(body.decode("utf-8")))
    except HTTPError as exc:
        if exc.code == 429:
            try:
                wait = max(60, min(3600, int(exc.headers.get("Retry-After", "60"))))
            except (ValueError, TypeError, AttributeError):
                wait = 60
            raise LocationSearchError(
                "Penyedia lokasi sedang membatasi pencarian. Coba lagi nanti.",
                status=429,
                retry_after=wait,
            ) from exc
        raise LocationSearchError("Layanan lokasi sedang tidak tersedia. Alamat tetap bisa diisi manual.") from exc
    except (URLError, TimeoutError, OSError, HTTPException) as exc:
        raise LocationSearchError("Layanan lokasi belum merespons. Alamat tetap bisa diisi manual.") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LocationSearchError("Layanan lokasi mengirim respons yang tidak dapat dibaca.") from exc


def _cached(key):
    entry = LocationSearchState.objects.filter(
        key=key, expires_at__gt=timezone.now()
    ).first()
    return entry.payload if entry is not None else None


def _search(query, endpoint, user_agent):
    key = hashlib.sha256(f"{endpoint}\n{query.casefold()}".encode("utf-8")).hexdigest()
    cached = _cached(key)
    if cached is not None:
        return cached

    now = timezone.now()
    LocationSearchState.objects.get_or_create(key="__gate__", defaults={"expires_at": now})
    lease_end = now + timedelta(seconds=LEASE_SECONDS)
    acquired = LocationSearchState.objects.filter(
        key="__gate__", expires_at__lte=now
    ).update(expires_at=lease_end)
    if not acquired:
        gate = LocationSearchState.objects.get(key="__gate__")
        wait = max(1, math.ceil((gate.expires_at - now).total_seconds()))
        raise LocationSearchError(
            "Pencarian lokasi sedang digunakan. Tunggu sebentar lalu coba lagi.",
            status=429,
            retry_after=wait,
        )

    cooldown = 1
    try:
        # Another request may have filled this key before this lease was acquired.
        cached = _cached(key)
        if cached is not None:
            return cached
        results = _fetch(query, endpoint, user_agent)
        LocationSearchState.objects.update_or_create(
            key=key,
            defaults={
                "payload": results,
                "expires_at": timezone.now() + timedelta(seconds=CACHE_SECONDS),
            },
        )
        LocationSearchState.objects.filter(expires_at__lte=timezone.now()).exclude(
            key="__gate__"
        ).delete()
        return results
    except LocationSearchError as exc:
        cooldown = max(cooldown, exc.retry_after or 1)
        raise
    finally:
        # Matching the lease prevents an expired worker from releasing a newer lease.
        LocationSearchState.objects.filter(key="__gate__", expires_at=lease_end).update(
            expires_at=timezone.now() + timedelta(seconds=cooldown)
        )


def search_locations(raw_query):
    query = " ".join(str(raw_query).split())
    if not 3 <= len(query) <= 200:
        raise LocationSearchError("Masukkan nama tempat atau alamat sepanjang 3–200 karakter.", status=400)
    endpoint, user_agent = _configuration()
    try:
        return _search(query, endpoint, user_agent)
    except DatabaseError as exc:
        # Fail closed: no shared gate means no upstream request is allowed.
        raise LocationSearchError("Pencarian lokasi belum tersedia. Alamat tetap bisa diisi manual.") from exc
