from __future__ import annotations

import httpx
from typing import Dict, Optional

from ..config import Settings


SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"


def text_search(settings: Settings, query: str, region_code: Optional[str] = None, location_bias: Optional[str] = None, field_mask: Optional[str] = None) -> Dict:
    if not settings.GOOGLE_MAPS_API_KEY:
        raise ValueError("GOOGLE_MAPS_API_KEY is not set. Set it in your .env.")

    # Prefer API key in query string (aligns with common usage and some key restrictions)
    url = f"{SEARCH_URL}?key={settings.GOOGLE_MAPS_API_KEY}"
    headers = {
        "X-Goog-FieldMask": field_mask
        or (
            "places.id,places.displayName,places.formattedAddress,places.shortFormattedAddress,"
            "places.location,places.types,places.photos,places.googleMapsUri,places.rating,places.userRatingCount"
        ),
        "Content-Type": "application/json",
    }
    payload = {
        "textQuery": query,
    }
    if region_code or settings.REGION_CODE:
        payload["regionCode"] = region_code or settings.REGION_CODE
    if location_bias or settings.LOCATION_BIAS:
        payload["locationBias"] = {"circle": _to_circle(location_bias or settings.LOCATION_BIAS)}

    with httpx.Client(timeout=settings.REQUEST_TIMEOUT) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()


def _to_circle(bias: str) -> Dict:
    # bias format: "lat,lng,radius_m"
    lat, lng, radius = bias.split(",")
    return {"center": {"latitude": float(lat), "longitude": float(lng)}, "radius": float(radius)}


