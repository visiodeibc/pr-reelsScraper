from __future__ import annotations

from typing import Dict

import httpx

from ..config import Settings


DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"


def place_details(settings: Settings, place_id: str, field_mask: str) -> Dict:
    if not settings.GOOGLE_MAPS_API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY is not set. Set it in your .env.")

    headers = {
        "X-Goog-FieldMask": field_mask,
    }
    url = DETAILS_URL.format(place_id=place_id) + f"?key={settings.GOOGLE_MAPS_API_KEY}"
    with httpx.Client(timeout=settings.REQUEST_TIMEOUT) as client:
        resp = client.get(url, headers=headers)
        resp.raise_for_status()
        return resp.json()


def maps_url_for_place(place_id: str) -> str:
    # Build a Google Maps URL using query_place_id param
    # https://www.google.com/maps/search/?api=1&query_place_id=PLACE_ID
    from urllib.parse import urlencode

    return "https://www.google.com/maps/search/?" + urlencode({"api": 1, "query_place_id": place_id})


