from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import List


def ffprobe_duration(path: str) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=duration",
        "-of",
        "json",
        path,
    ]
    out = subprocess.check_output(cmd)
    data = json.loads(out)
    streams = data.get("streams", [])
    if streams and streams[0].get("duration"):
        return float(streams[0]["duration"])
    return 0.0


