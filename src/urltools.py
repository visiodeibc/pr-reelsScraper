from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit


_SHORTCODE_REGEX = re.compile(r"^/(?:reel|p)/([A-Za-z0-9_-]+)(?:/|$)")


def normalize_permalink(url: str) -> str:
    """Normalize an Instagram permalink.

    - Strips query and fragment
    - Ensures trailing slash
    """
    parts = urlsplit(url)
    path = parts.path or "/"
    if not path.endswith("/"):
        path = path + "/"
    return urlunsplit((parts.scheme, parts.netloc, path, "", ""))


def shortcode_from_url(url: str) -> str | None:
    """Extract shortcode from supported Instagram URLs.

    Supports:
    - https://www.instagram.com/reel/<code>/
    - https://www.instagram.com/p/<code>/
    """
    parts = urlsplit(url)
    match = _SHORTCODE_REGEX.match(parts.path)
    if not match:
        return None
    return match.group(1)


