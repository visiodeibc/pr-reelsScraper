from __future__ import annotations

from typing import Dict, List, Tuple

from ..utils.text import similarity


def score_candidates(candidate_name: str, results: List[Dict]) -> List[Tuple[Dict, float]]:
    scored: List[Tuple[Dict, float]] = []
    for r in results:
        display = r.get("displayName", {}).get("text") or r.get("displayName")
        if not display:
            continue
        s = similarity(candidate_name, str(display))
        scored.append((r, s))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored


