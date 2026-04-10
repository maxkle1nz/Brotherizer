"""Path resolution helpers for source checkouts and installed packages."""

from __future__ import annotations

import os
from importlib.resources import files
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parent.parent


def _source_candidate(*parts: str) -> Path:
    return SOURCE_ROOT.joinpath(*parts)


def source_layout_available() -> bool:
    return _source_candidate("configs", "brotherizer_modes.json").exists()


def resource_path(*parts: str) -> Path:
    candidate = _source_candidate(*parts)
    if candidate.exists():
        return candidate
    return Path(files("brotherizer_assets").joinpath(*parts))


def writable_root() -> Path:
    explicit = os.environ.get("BROTHERIZER_HOME", "").strip()
    if explicit:
        return Path(explicit).expanduser()
    if source_layout_available():
        return SOURCE_ROOT
    return Path.home() / ".brotherizer"


def writable_path(*parts: str) -> Path:
    return writable_root().joinpath(*parts)
