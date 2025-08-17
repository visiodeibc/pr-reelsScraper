from __future__ import annotations

import base64
import io
from typing import List

import ffmpeg
from openai import OpenAI

from ..config import Settings
from ..models import Transcript, FrameText, Extraction, PlaceCandidate
from .adapter import LLMAdapter
from .prompts import TRANSCRIPT_SYSTEM, OCR_SYSTEM, EXTRACTION_SYSTEM, EXTRACTION_INSTRUCTIONS


class OpenAILLM(LLMAdapter):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def transcribe(self, video_path: str) -> Transcript:
        # Uses the audio transcription model via the Audio API
        with open(video_path, "rb") as f:
            audio_bytes = f.read()
        resp = self.client.audio.transcriptions.create(
            model=self.settings.OPENAI_MODEL_TRANSCRIBE,
            file=("audio.mp4", audio_bytes),
        )
        # Assume response contains segments; if not, synthesize
        full_text = resp.text if hasattr(resp, "text") else ""  # type: ignore[attr-defined]
        segments = []
        if hasattr(resp, "segments") and resp.segments:  # type: ignore[attr-defined]
            for s in resp.segments:  # type: ignore[attr-defined]
                segments.append({"start": float(s.get("start", 0.0)), "end": float(s.get("end", 0.0)), "text": s.get("text", "")})
        else:
            segments.append({"start": 0.0, "end": 0.0, "text": full_text})
        return Transcript(language=getattr(resp, "language", None), segments=segments, full_text=full_text)

    def ocr_overlays(self, video_path: str, fps: float, max_frames: int) -> List[FrameText]:
        # Sample frames via ffmpeg-python and send small batches to GPT-4o-mini with image understanding
        overlays: List[FrameText] = []
        out, _ = (
            ffmpeg
            .input(video_path)
            .filter("fps", fps=fps)
            .output("pipe:", format="image2", vframes=max_frames, vcodec="png")
            .run(capture_stdout=True, capture_stderr=True)
        )
        # The stream contains concatenated PNGs; we decode iteratively
        # For brevity, assume every frame is a standalone PNG separated by the signature
        png_sig = b"\x89PNG\r\n\x1a\n"
        chunks = [png_sig + part for part in out.split(png_sig) if part]
        for idx, img_bytes in enumerate(chunks[:max_frames]):
            b64 = base64.b64encode(img_bytes).decode("ascii")
            prompt = [{"type": "text", "text": "Extract any readable on-screen text."}, {"type": "input_image", "image_data": b64}]
            msg = self.client.chat.completions.create(
                model=self.settings.OPENAI_MODEL_VISION,
                messages=[{"role": "system", "content": OCR_SYSTEM}, {"role": "user", "content": prompt}],
                temperature=0,
            )
            text = msg.choices[0].message.content.strip() if msg.choices and msg.choices[0].message.content else ""
            overlays.append(FrameText(timestamp=str(idx), text=text))
        return overlays

    def extract_places(self, transcript: Transcript, overlays: List[FrameText], caption_text: str | None, shortcode: str) -> Extraction:
        user_content = (
            f"Shortcode: {shortcode}\n\n"
            f"Transcript:\n{transcript.full_text}\n\n"
            f"Overlays:\n" + "\n".join(f"[{o.timestamp}] {o.text}" for o in overlays) + "\n\n"
            f"Caption:\n{caption_text or ''}"
        )
        msg = self.client.chat.completions.create(
            model=self.settings.OPENAI_MODEL_TEXT,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM},
                {"role": "user", "content": EXTRACTION_INSTRUCTIONS + "\n\n" + user_content},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        content = msg.choices[0].message.content
        import json as _json

        raw = {"source_shortcode": shortcode, "places": []}
        try:
            if content:
                raw = _json.loads(content)
        except Exception:
            raw = {"source_shortcode": shortcode, "places": []}

        norm_places = []
        for p in (raw.get("places") or []):
            if not isinstance(p, dict):
                continue
            # Coerce nulls to lists where required
            if p.get("timecodes") is None:
                p["timecodes"] = []
            if p.get("menu_highlights") is None:
                p["menu_highlights"] = []
            if p.get("alt_names") is None:
                p["alt_names"] = []
            # Normalize sentiment to one of {positive, neutral, negative} or None
            sent = p.get("sentiment")
            if isinstance(sent, str):
                s = sent.strip().lower()
                if any(k in s for k in ["neg", "bad", "poor", "hate", "terrible", "awful"]):
                    p["sentiment"] = "negative"
                elif any(k in s for k in ["pos", "good", "great", "love", "amazing", "excellent", "high"]):
                    p["sentiment"] = "positive"
                elif "neutral" in s or "meh" in s or "ok" in s:
                    p["sentiment"] = "neutral"
                else:
                    p["sentiment"] = None
            norm_places.append(PlaceCandidate(**p))

        return Extraction(source_shortcode=shortcode, places=norm_places)


