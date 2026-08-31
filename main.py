"""
GuardWAF Root Entrypoint
Exposes the modular FastAPI application defined in app.main.
"""

from app.main import app

__all__ = ["app"]
