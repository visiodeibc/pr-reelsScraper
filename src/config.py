from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):
    """Runtime configuration loaded from environment and CLI overrides."""
    OUT_DIR: str = Field(default="./out")
    REQUEST_TIMEOUT: int = Field(default=60)
    MAX_CONNECTION_ATTEMPTS: int = Field(default=3)
    SESSION_FILE: Optional[str] = Field(default=None)
    IG_USERNAME: Optional[str] = Field(default=None)
    IG_PASSWORD: Optional[str] = Field(default=None)
    USER_AGENT: Optional[str] = Field(default=None)
    # LLM (OpenAI)
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL_TRANSCRIBE: str = Field(default="gpt-4o-transcribe")
    OPENAI_MODEL_VISION: str = Field(default="gpt-4o-mini")
    OPENAI_MODEL_TEXT: str = Field(default="gpt-4o-mini")
    # Google Places
    GOOGLE_MAPS_API_KEY: Optional[str] = Field(default=None)
    REGION_CODE: str = Field(default="SG")
    LOCATION_BIAS: Optional[str] = Field(default=None)  # "lat,lng,radius_m"
    # Processing
    DEFAULT_FPS: float = Field(default=1.0)
    MAX_FRAMES: int = Field(default=120)
    PROVIDER: str = Field(default="openai")

    def ensure_out_dir(self) -> None:
        Path(self.OUT_DIR).mkdir(parents=True, exist_ok=True)


def _coerce_int(value: Optional[str], default: int) -> int:
    if value is None or value == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_float(value: Optional[str], default: float) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_settings(overrides: Optional[Dict[str, Any]] = None) -> Settings:
    """Load settings from .env and environment, then apply any CLI overrides.

    - Ensures OUT_DIR exists on disk.
    """
    load_dotenv()  # loads .env if present

    env = os.environ
    settings = Settings(
        OUT_DIR=(
            overrides.get("out_dir")
            if overrides and overrides.get("out_dir") is not None
            else env.get("OUT_DIR", "./out")
        ),
        REQUEST_TIMEOUT=_coerce_int(
            (str(overrides.get("request_timeout")) if overrides and overrides.get("request_timeout") is not None else env.get("REQUEST_TIMEOUT")),
            60,
        ),
        MAX_CONNECTION_ATTEMPTS=_coerce_int(
            (str(overrides.get("max_connection_attempts")) if overrides and overrides.get("max_connection_attempts") is not None else env.get("MAX_CONNECTION_ATTEMPTS")),
            3,
        ),
        SESSION_FILE=(overrides.get("session_file") if overrides and overrides.get("session_file") is not None else (env.get("SESSION_FILE") or None)) or None,
        IG_USERNAME=(overrides.get("username") if overrides and overrides.get("username") is not None else (env.get("IG_USERNAME") or None)) or None,
        IG_PASSWORD=(overrides.get("password") if overrides and overrides.get("password") is not None else (env.get("IG_PASSWORD") or None)) or None,
        USER_AGENT=(overrides.get("user_agent") if overrides and overrides.get("user_agent") is not None else (env.get("USER_AGENT") or None)) or None,
        # OpenAI
        OPENAI_API_KEY=env.get("OPENAI_API_KEY") or None,
        OPENAI_MODEL_TRANSCRIBE=env.get("OPENAI_MODEL_TRANSCRIBE", "gpt-4o-transcribe"),
        OPENAI_MODEL_VISION=env.get("OPENAI_MODEL_VISION", "gpt-4o-mini"),
        OPENAI_MODEL_TEXT=env.get("OPENAI_MODEL_TEXT", "gpt-4o-mini"),
        # Google Places
        GOOGLE_MAPS_API_KEY=env.get("GOOGLE_MAPS_API_KEY") or None,
        REGION_CODE=env.get("REGION_CODE", "SG"),
        LOCATION_BIAS=env.get("LOCATION_BIAS") or None,
        # Processing
        DEFAULT_FPS=_coerce_float(env.get("DEFAULT_FPS"), 1.0),
        MAX_FRAMES=_coerce_int(env.get("MAX_FRAMES"), 120),
        PROVIDER=env.get("PROVIDER", "openai"),
    )

    settings.ensure_out_dir()
    return settings


