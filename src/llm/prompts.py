TRANSCRIPT_SYSTEM = "You are a helpful assistant that accurately transcribes speech from short social videos."

OCR_SYSTEM = "You detect short on-screen texts (overlays, stickers, captions) and output time-coded text."

EXTRACTION_SYSTEM = (
    "You extract a structured list of places and the creator's mini-reviews from the transcript and on-screen text. "
    "Use concise names and capture any sentiment cues and menu highlights."
)

EXTRACTION_INSTRUCTIONS = (
    "Return JSON strictly with keys: source_shortcode, places[]. Each place has: "
    "name, alt_names, city_hint, neighborhood_hint, country_hint, category_hint, menu_highlights, "
    "creator_review, sentiment, timecodes."
)


