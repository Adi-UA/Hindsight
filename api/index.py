"""Vercel serverless entry point.

Exposes the FastAPI app so Vercel's Python runtime can serve the `/api/*`
routes. The backend package lives in `../backend`, so add it to the path
before importing the app.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import app  # noqa: E402  (path is configured above before import)

__all__ = ["app"]
