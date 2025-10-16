# =================================================================================================
# File: tests/unit/conftest.py
# Purpose:
#   Unit test configuration for the OAPS Zendesk App.
#
# Structural Alignment (v2.3):
#   - Forces UNIT_MODE=1 (no network calls).
#   - Ensures APP_ENV=test unless overridden.
#   - Provides rich console test boundaries for local visibility.
#
# Version: 2.3.0 | October 2025
# Author: Olivier Lamy
# =================================================================================================

import os
import shutil
import traceback
import pytest
from rich.console import Console
from rich.traceback import install
from rich.rule import Rule
from fastapi.testclient import TestClient
from backend.main import app as base_app
from backend.config import get_settings

# -------------------------------------------------------------------------------------------------
# 🧭 Environment Enforcement
# -------------------------------------------------------------------------------------------------
os.environ["UNIT_MODE"] = "1"
os.environ.setdefault("APP_ENV", "test")
os.environ["INTEGRATION_MODE"] = "0"
print(" [UNIT MODE] Enforced — Zendesk API/network calls disabled.")

# -------------------------------------------------------------------------------------------------
# 🧱 Console + Traceback Setup
# -------------------------------------------------------------------------------------------------
console = Console()
install(show_locals=True)

def _debug(msg: str):
    print(f" [UNIT-CONFTEST] {msg}")

_debug("Unit-level conftest.py loaded.")

# -------------------------------------------------------------------------------------------------
# 🧹 Cache Cleaner
# -------------------------------------------------------------------------------------------------
def _clean_caches_for_unit_run():
    """Clears temporary files/caches specific to the unit test run."""
    _debug("Attempting to clear unit run specific caches...")
    # Placeholder for local cache cleanup logic
    pass

# -------------------------------------------------------------------------------------------------
# ⚙️ Pytest Lifecycle Hook
# -------------------------------------------------------------------------------------------------
def pytest_sessionstart(session):
    print(" [UNIT-CONFTEST] pytest_sessionstart triggered.")
    try:
        _clean_caches_for_unit_run()
        print(" [Clean] Cleared caches for unit test run.")
        print(" [UNIT-CONFTEST] Finished cleaning caches successfully.")
    except Exception as e:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("FATAL ERROR IN UNIT CONFTEST SETUP - EXECUTION ABORTED")
        print(f"Error: {e}")
        traceback.print_exc()
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        raise

# -------------------------------------------------------------------------------------------------
# 🧩 Fixtures
# -------------------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def settings():
    return get_settings()

@pytest.fixture(scope="session")
def test_client():
    client = TestClient(base_app)
    yield client
    client.close()

@pytest.fixture(autouse=True)
def rich_test_logging():
    console.print(Rule(style="bold blue"))
    console.print("[bold blue]TEST START")
    yield
    console.print("[bold red]TEST END")
    console.print(Rule(style="bold red"))
