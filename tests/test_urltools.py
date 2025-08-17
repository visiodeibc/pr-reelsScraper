from __future__ import annotations

import pytest

from src.urltools import normalize_permalink, shortcode_from_url


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("https://www.instagram.com/reel/ABC123/", "https://www.instagram.com/reel/ABC123/"),
        ("https://www.instagram.com/reel/ABC123?utm_source=ig_web_copy_link", "https://www.instagram.com/reel/ABC123/"),
        ("https://www.instagram.com/p/XYZ-9_/", "https://www.instagram.com/p/XYZ-9_/"),
        ("https://www.instagram.com/p/XYZ-9_", "https://www.instagram.com/p/XYZ-9_/"),
        ("https://instagram.com/p/abcdEF12/?igshid=123", "https://instagram.com/p/abcdEF12/"),
    ],
)
def test_normalize_permalink(raw: str, expected: str) -> None:
    assert normalize_permalink(raw) == expected


@pytest.mark.parametrize(
    "url,code",
    [
        ("https://www.instagram.com/reel/ABC123/", "ABC123"),
        ("https://www.instagram.com/p/XYZ-9_/", "XYZ-9_"),
        ("https://instagram.com/p/abcdEF12/?igshid=123", "abcdEF12"),
        ("https://instagram.com/p/abcdEF12", "abcdEF12"),
        ("https://instagram.com/reel/abcdEF12?x=y", "abcdEF12"),
    ],
)
def test_shortcode_from_url_valid(url: str, code: str) -> None:
    assert shortcode_from_url(url) == code


@pytest.mark.parametrize(
    "url",
    [
        "https://www.instagram.com/abc/",
        "https://www.instagram.com/stories/ABC123/",
        "https://example.com/reel/ABC123/",
        "not a url",
    ],
)
def test_shortcode_from_url_invalid(url: str) -> None:
    assert shortcode_from_url(url) is None


