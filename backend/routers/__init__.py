# =================================================================================================
# File: backend/routers/__init__.py
# Purpose:
#   Centralized router imports for the OAPS Zendesk App.
#
# Ensures that routers are accessible under `backend.routers.*` for inclusion in FastAPI.
# =================================================================================================

from backend.routers import tickets, users

__all__ = ["tickets", "users"]



