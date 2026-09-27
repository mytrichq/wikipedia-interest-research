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


def studies_root() -> Path:
    """Where studies are saved: the user's project, even if the agent cd'ed into the skill."""
    custom = os.environ.get("WIR_STUDIES")
    if custom:
        return Path(custom).expanduser()
    physical = Path.cwd().resolve()
    logical = Path(os.environ.get("PWD") or physical)
    if logical.resolve() != physical:
        logical = physical
    parts = logical.parts
    for i in range(len(parts) - 1):
        if parts[i] == ".claude" and parts[i + 1] == "skills":
            return Path(*parts[:i]) / "wiki-studies"
    return physical / "wiki-studies"
