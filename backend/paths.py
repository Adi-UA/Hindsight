"""Filesystem paths used by the backend."""

from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

#: Where the built frontend is copied for the backend to serve at "/".
STATIC_DIR = BASE_DIR / "static"
