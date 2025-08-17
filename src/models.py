from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel


class Transcript(BaseModel):
    language: Optional[str] = None
    segments: List[dict]
    full_text: str


class FrameText(BaseModel):
    timestamp: str
    text: str


class PlaceCandidate(BaseModel):
    name: str
    alt_names: List[str] = []
    city_hint: Optional[str] = None
    neighborhood_hint: Optional[str] = None
    country_hint: Optional[str] = None
    category_hint: Optional[str] = None  # restaurant|cafe|bar|bakery|...
    menu_highlights: List[str] = []
    creator_review: Optional[str] = None
    sentiment: Optional[Literal["positive", "neutral", "negative"]] = None
    timecodes: List[str] = []


class Extraction(BaseModel):
    source_shortcode: str
    places: List[PlaceCandidate]


class MatchedPlace(BaseModel):
    source_shortcode: str
    candidate_name: str
    match_confidence: float
    place_id: str
    display_name: str
    formatted_address: str
    lat: float
    lng: float
    types: List[str]
    website: Optional[str] = None
    phone: Optional[str] = None
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    price_level: Optional[int] = None
    maps_url: str
    creator_review: Optional[str] = None
    sentiment: Optional[str] = None
    menu_highlights: List[str] = []
    timecodes: List[str] = []


