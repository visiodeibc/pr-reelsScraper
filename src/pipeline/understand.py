from __future__ import annotations

import json
from pathlib import Path
import glob
import shutil
from typing import List, Tuple

from ..config import Settings
from ..llm.openai_impl import OpenAILLM
from ..models import Transcript, FrameText, Extraction


def run_understanding(settings: Settings, shortcode: str, video_path: str, caption_text: str | None) -> Tuple[Transcript, List[FrameText], Extraction]:
    outdir = Path(settings.OUT_DIR) / "reels" / shortcode
    outdir.mkdir(parents=True, exist_ok=True)

    llm = OpenAILLM(settings)
    # Resolve video path robustly
    vpath = Path(video_path)
    if not vpath.exists():
        candidates = [
            Path(settings.OUT_DIR) / "reels" / f"{shortcode}.mp4",
            Path(settings.OUT_DIR) / "reels" / shortcode / f"{shortcode}.mp4",
        ]
        candidates += [Path(p) for p in glob.glob(f"{settings.OUT_DIR}/reels/*/{shortcode}.mp4")]
        for c in candidates:
            if c.exists():
                vpath = c
                break
    if not vpath.exists():
        raise FileNotFoundError(
            f"Video not found for shortcode {shortcode}. Expected at {video_path} or under {settings.OUT_DIR}/reels/. Run the download step first."
        )

    transcript = llm.transcribe(str(vpath))
    # Run OCR only if ffmpeg is available; otherwise skip overlays gracefully
    overlays = []
    if shutil.which("ffmpeg") is not None:
        try:
            overlays = llm.ocr_overlays(str(vpath), fps=settings.DEFAULT_FPS, max_frames=settings.MAX_FRAMES)
        except Exception:
            # Any ffmpeg/decoding/GPU errors: proceed without overlays
            overlays = []
    extraction = llm.extract_places(transcript, overlays, caption_text, shortcode)

    (outdir / "transcript.json").write_text(json.dumps(transcript.model_dump(), ensure_ascii=False, indent=2))
    (outdir / "overlays.json").write_text(json.dumps([o.model_dump() for o in overlays], ensure_ascii=False, indent=2))
    (outdir / "extraction.json").write_text(json.dumps(extraction.model_dump(), ensure_ascii=False, indent=2))

    return transcript, overlays, extraction


