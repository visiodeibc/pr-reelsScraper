from __future__ import annotations

import re
from typing import Iterable

from rapidfuzz import fuzz


def normalize_name(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"\s+", " ", s)
    return s


def similarity(a: str, b: str) -> float:
    return float(fuzz.token_set_ratio(normalize_name(a), normalize_name(b))) / 100.0


