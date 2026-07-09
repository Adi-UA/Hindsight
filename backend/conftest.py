"""Shared pytest fixtures."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """A FastAPI TestClient for the API."""
    from app import app

    return TestClient(app)
