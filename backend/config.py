# =================================================================================================
# File: backend/config.py
# Description:
#   Centralized configuration management for the OAPS Zendesk App (v2.0+)
#
# Testing Alignment (v2.1):
#   - Default APP_ENV = "test" to ensure consistent pytest behavior.
#   - Settings loaded *after* environment bootstrap from conftest.py.
#   - Printed APP_ENV during pytest runs for transparency.
#
# Version: 2.1.0 | October 2025
# Author: Olivier Lamy
# =================================================================================================

import os
import sys
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# -------------------------------------------------------------------------------------------------
# 1️⃣  Ensure the env flags exist before Pydantic reads anything
# -------------------------------------------------------------------------------------------------
os.environ.setdefault("UNIT_MODE", "0")
os.environ.setdefault("INTEGRATION_MODE", "0")
os.environ.setdefault("APP_ENV", os.getenv("APP_ENV", "local"))

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


class Settings(BaseSettings):
    """Centralized Application configuration loaded from environment variables and .env file."""

    # --- Core ---
    APP_ENV: str = Field(default=os.getenv("APP_ENV", "local"), description="Application environment (dev|test|prod)")
    DEBUG: bool = Field(default=False, description="Enable debug mode for FastAPI")
    PROJECT_NAME: str = Field(default="Zendesk Reporting App")

    # --- Execution Modes ---
    UNIT_MODE: bool = Field(default=False)
    INTEGRATION_MODE: bool = Field(default=False)

    # --- API & CORS ---
    CORS_ORIGINS: str = Field(default="http://localhost:3000")
    API_HOST: str = Field(default="localhost")
    API_PORT: int = Field(default=8000)

    # --- Zendesk Integration ---
    ZENDESK_API_URL: str = Field(default="https://nycdoe.zendesk.com/api/v2")
    ZENDESK_API_TOKEN: str | None = Field(default=None)
    ZENDESK_USER_EMAIL: str | None = Field(default=None)

    # --- SharePoint / Azure ---
    SHAREPOINT_SITE_URL: str | None = Field(default=None)
    AZURE_APP_ID: str | None = Field(default=None)
    AZURE_SECRET_ID: str | None = Field(default=None)
    AZURE_SECRET_VALUE: str | None = Field(default=None)

    # --- Logging & Paths ---
    LOG_LEVEL: str = Field(default="INFO")
    LOG_DIR: str = Field(default="./logs")

    model_config = SettingsConfigDict(
        env_file=os.path.join(BASE_DIR, ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Dynamic Logic ---
    @property
    def effective_debug(self) -> bool:
        """Auto-compute DEBUG for different modes."""
        env = str(self.APP_ENV).lower()
        if env in {"unit", "local"}:
            return True
        if env in {"integration", "prod", "production"}:
            return False
        return self.DEBUG

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    env = str(settings.APP_ENV).lower()

    if settings.INTEGRATION_MODE or env == "integration":
        os.environ["APP_ENV"] = "integration"
        os.environ["UNIT_MODE"] = "0"
        settings.DEBUG = True  # ✅ Always show tracebacks for integration

    elif settings.UNIT_MODE or env == "unit":
        os.environ["APP_ENV"] = "unit"
        os.environ["INTEGRATION_MODE"] = "0"
        settings.DEBUG = True  # ✅ Always show tracebacks for unit

    print(
        f"⚙️ Loaded settings: APP_ENV={settings.APP_ENV}, "
        f"DEBUG={settings.DEBUG}, "
        f"UNIT_MODE={settings.UNIT_MODE}, INTEGRATION_MODE={settings.INTEGRATION_MODE}"
    )
    return settings
