from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

import httpx

from wir import __version__

PROJECT_URL = "https://github.com/mytrichq/wikipedia-interest-research"
DATA_DIR = Path(__file__).resolve().parent / "data"


def user_agent() -> str:
    contact = os.environ.get("WIR_CONTACT") or PROJECT_URL
    return f"wikipedia-interest-research/{__version__} ({contact}) httpx/{httpx.__version__}"


def home_dir() -> Path:
    custom = os.environ.get("WIR_HOME")
    default = Path.home() / ".cache" / "wikipedia-interest-research"
    path = Path(custom).expanduser() if custom else default
    path.mkdir(parents=True, exist_ok=True)
    return path


def offline() -> bool:
    return os.environ.get("WIR_OFFLINE", "").strip() not in ("", "0", "false")


def today() -> dt.date:
    pinned = os.environ.get("WIR_TODAY")
    return dt.date.fromisoformat(pinned) if pinned else dt.date.today()
