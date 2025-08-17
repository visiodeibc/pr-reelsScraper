from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Tuple

from ..models import Transcript, FrameText, Extraction


class LLMAdapter(ABC):
    @abstractmethod
    def transcribe(self, video_path: str) -> Transcript:
        raise NotImplementedError

    @abstractmethod
    def ocr_overlays(self, video_path: str, fps: float, max_frames: int) -> List[FrameText]:
        raise NotImplementedError

    @abstractmethod
    def extract_places(self, transcript: Transcript, overlays: List[FrameText], caption_text: str | None, shortcode: str) -> Extraction:
        raise NotImplementedError


