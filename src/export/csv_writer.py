from __future__ import annotations

import csv
from typing import Iterable

from ..models import MatchedPlace


FULL_HEADERS = [
    "source_shortcode",
    "candidate_name",
    "match_confidence",
    "place_id",
    "display_name",
    "formatted_address",
    "lat",
    "lng",
    "types",
    "website",
    "phone",
    "rating",
    "rating_count",
    "price_level",
    "maps_url",
    "creator_review",
    "sentiment",
    "menu_highlights",
    "timecodes",
]


def write_full_csv(path: str, rows: Iterable[MatchedPlace]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FULL_HEADERS)
        w.writeheader()
        for m in rows:
            w.writerow({
                "source_shortcode": m.source_shortcode,
                "candidate_name": m.candidate_name,
                "match_confidence": f"{m.match_confidence:.3f}",
                "place_id": m.place_id,
                "display_name": m.display_name,
                "formatted_address": m.formatted_address,
                "lat": m.lat,
                "lng": m.lng,
                "types": ",".join(m.types or []),
                "website": m.website or "",
                "phone": m.phone or "",
                "rating": m.rating if m.rating is not None else "",
                "rating_count": m.rating_count if m.rating_count is not None else "",
                "price_level": m.price_level if m.price_level is not None else "",
                "maps_url": m.maps_url,
                "creator_review": m.creator_review or "",
                "sentiment": m.sentiment or "",
                "menu_highlights": ", ".join(m.menu_highlights or []),
                "timecodes": ", ".join(m.timecodes or []),
            })


def write_mymaps_csv(path: str, rows: Iterable[MatchedPlace]) -> None:
    # Minimal schema for Google My Maps import
    headers = ["Name", "Description", "Latitude", "Longitude"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        for m in rows:
            name = m.display_name
            desc = f"{m.formatted_address}\n{m.maps_url}\n\nReview: {m.creator_review or ''}"
            w.writerow([name, desc, m.lat, m.lng])


