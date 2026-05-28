from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def load_environment() -> None:
    load_dotenv(ENV_PATH)


def get_env(name: str, default: str | None = None, required: bool = False) -> str | None:
    load_environment()
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def data_dir() -> Path:
    return ROOT / "data"


def stages_dir() -> Path:
    return data_dir() / "stages"


def packages_dir() -> Path:
    return ROOT / "packages"
