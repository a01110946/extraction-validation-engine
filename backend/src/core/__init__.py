# File: backend/src/core/__init__.py
"""Core configuration and infrastructure."""

from .config import settings
from .database import database

__all__ = ["settings", "database"]
