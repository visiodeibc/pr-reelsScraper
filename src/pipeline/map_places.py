from __future__ import annotations

import json
from pathlib import Path
from typing import List

from ..config import Settings
from ..models import Extraction, MatchedPlace
from ..places.search import text_search
from ..places.rank import score_candidates
from ..places.details import place_details, maps_url_for_place


def _price_enum_to_int(value):
    if not value:
        return None
    v = str(value).upper()
    mapping = {
        "PRICE_LEVEL_FREE": 0,
        "PRICE_LEVEL_INEXPENSIVE": 1,
        "PRICE_LEVEL_MODERATE": 2,
        "PRICE_LEVEL_EXPENSIVE": 3,
        "PRICE_LEVEL_VERY_EXPENSIVE": 4,
        "PRICE_LEVEL_UNSPECIFIED": None,
    }
    return mapping.get(v, None)


def run_mapping(settings: Settings, shortcode: str, extraction: Extraction) -> List[MatchedPlace]:
    outdir = Path(settings.OUT_DIR) / "reels" / shortcode
    outdir.mkdir(parents=True, exist_ok=True)

    all_matches: List[MatchedPlace] = []
    matches_debug = []

    for cand in extraction.places:
        query_parts = [cand.name]
        if cand.city_hint:
            query_parts.append(cand.city_hint)
        if cand.country_hint:
            query_parts.append(cand.country_hint)
        query = ", ".join([p for p in query_parts if p])

        search_json = text_search(settings, query=query)
        places = search_json.get("places", [])
        scored = score_candidates(cand.name, places)
        chosen, confidence = (None, 0.0)
        if scored:
            chosen, confidence = scored[0]

        chosen_id = chosen.get("id") if chosen else None
        details = {}
        if chosen_id:
            details = place_details(
                settings,
                place_id=chosen_id,
                field_mask=(
                    "id,displayName,formattedAddress,location,types,websiteUri,internationalPhoneNumber,rating,userRatingCount,priceLevel"
                ),
            )

        if chosen and details:
            loc = details.get("location", {})
            price_level_int = _price_enum_to_int(details.get("priceLevel"))
            mp = MatchedPlace(
                source_shortcode=extraction.source_shortcode,
                candidate_name=cand.name,
                match_confidence=confidence,
                place_id=details.get("id", chosen.get("id")),
                display_name=(details.get("displayName", {}) or {}).get("text") or (chosen.get("displayName", {}) or {}).get("text", ""),
                formatted_address=details.get("formattedAddress", chosen.get("formattedAddress", "")),
                lat=loc.get("latitude", 0.0),
                lng=loc.get("longitude", 0.0),
                types=details.get("types", chosen.get("types", [])),
                website=details.get("websiteUri"),
                phone=details.get("internationalPhoneNumber"),
                rating=details.get("rating"),
                rating_count=details.get("userRatingCount"),
                price_level=price_level_int,
                maps_url=maps_url_for_place(details.get("id", chosen.get("id"))),
                creator_review=cand.creator_review,
                sentiment=cand.sentiment,
                menu_highlights=cand.menu_highlights,
                timecodes=cand.timecodes,
            )
            all_matches.append(mp)

        matches_debug.append({
            "candidate": cand.model_dump(),
            "search": search_json,
            "chosen": chosen,
            "confidence": confidence,
            "details": details,
        })

    (outdir / "matches.json").write_text(json.dumps(matches_debug, ensure_ascii=False, indent=2))
    return all_matches


