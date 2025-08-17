from __future__ import annotations

import sys

import pytest

from src.cli import main


def test_cli_parses_and_exits_with_invalid_url_code(monkeypatch):
    # Avoid any real network by giving an invalid URL that fails fast on shortcode
    argv = [
        "--urls",
        "https://www.instagram.com/invalid/",
        "--verbose",
    ]
    code = main(argv)
    assert code in {2, 64}


