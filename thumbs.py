from __future__ import annotations

from pathlib import Path

import requests


def download_thumbnail(url: str, destination: str | Path, timeout: int = 30) -> Path:
    if not url:
        raise ValueError("Thumbnail URL is empty")
    dest_path = Path(destination)
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    dest_path.write_bytes(response.content)
    return dest_path
