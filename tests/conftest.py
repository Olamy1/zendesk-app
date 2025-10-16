# =================================================================================================
# File: tests/conftest.py
# Purpose:
#   Canonical pytest configuration and environment router for the OAPS Zendesk App test suite.
#
# Structural Alignment (v2.3):
#   - Supports toggle-based environment control using 0/1 flags.
#   - Defaults to APP_ENV=test unless overridden.
#   - Synchronizes UNIT_MODE and INTEGRATION_MODE as binary switches.
#   - Loads environment before backend imports for consistent startup behavior.
#
# Version: 2.3 | October 2025
# Author: Olivier Lamy
# =================================================================================================

from __future__ import annotations
import os

# 🚦 Respect integration override — only default to unit if unset
if os.getenv("INTEGRATION_MODE") != "1":
    os.environ.setdefault("APP_ENV", "unit")
    os.environ["UNIT_MODE"] = "1"
    os.environ["INTEGRATION_MODE"] = "0"
else:
    # Integration override active, don’t overwrite
    print("🧩 [Root Conftest] Integration override detected — skipping UNIT bootstrap.")

import sys
import time
import pytest
from unittest.mock import MagicMock
from rich.console import Console
from rich.table import Table
from fastapi.testclient import TestClient

# -------------------------------------------------------------------------------------------------
# 🧭 Early Environment Bootstrap
# -------------------------------------------------------------------------------------------------
APP_ENV = os.getenv("APP_ENV", "test").lower()
UNIT_MODE = os.getenv("UNIT_MODE", "0")
INTEGRATION_MODE = os.getenv("INTEGRATION_MODE", "0")

# Normalize binary flags
UNIT_MODE = "1" if UNIT_MODE == "1" else "0"
INTEGRATION_MODE = "1" if INTEGRATION_MODE == "1" else "0"

# Default to test when both off
if UNIT_MODE == "0" and INTEGRATION_MODE == "0" and APP_ENV not in ("unit", "integration"):
    APP_ENV = "test"

# Push back into environment
os.environ.update({
    "APP_ENV": APP_ENV,
    "UNIT_MODE": UNIT_MODE,
    "INTEGRATION_MODE": INTEGRATION_MODE,
})

# ✅ FIX #1 — Typo: cconsole → console
console = Console()

def _debug_log(msg: str):
    if os.getenv("DEBUG_PYTEST", "1") == "1":
        print(f"[DEBUG] {msg}")

# -------------------------------------------------------------------
# 🔍 Visual Mode Banner (Dynamic based on current environment flags)
# -------------------------------------------------------------------
mode_str = (
    "INTEGRATION" if os.getenv("INTEGRATION_MODE") == "1"
    else "UNIT" if os.getenv("UNIT_MODE") == "1"
    else "TEST"
)
print(f" [{mode_str} MODE ACTIVE] — Environment initialized.")
_debug_log(f"Bootstrap: APP_ENV={APP_ENV}, UNIT_MODE={UNIT_MODE}, INTEGRATION_MODE={INTEGRATION_MODE}")

# -------------------------------------------------------------------------------------------------
# 🌐 Import app AFTER environment setup
# -------------------------------------------------------------------------------------------------
from backend.main import app as base_app
from backend.config import get_settings

# -------------------------------------------------------------------------------------------------
# 🌍 Environment Summary Banner
# -------------------------------------------------------------------------------------------------
def _env_banner() -> None:
    table = Table(title="OAPS Zendesk App — Test Context", header_style="bold white")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Environment", APP_ENV.upper())
    table.add_row("Mode", "INTEGRATION" if INTEGRATION_MODE == "1" else ("UNIT" if UNIT_MODE == "1" else "TEST"))
    table.add_row("Python", f"{sys.version_info.major}.{sys.version_info.minor}")
    table.add_row("Timestamp", time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()))
    console.print(table)

@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    console.rule("[bold blue]Pre-Run Environment Diagnostics[/bold blue]")
    _env_banner()
    print(" Bootstrapping OAPS Zendesk Test Environment...")
    _debug_log("pytest_sessionstart hook complete.")

# -------------------------------------------------------------------------------------------------
# 🔢 Version Filtering
# -------------------------------------------------------------------------------------------------
def _normalize_version(ver: str | None) -> str | None:
    if not ver:
        return None
    s = str(ver).strip()
    return s[1:] if s.lower().startswith("v") else s

def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    target = _normalize_version(config.getoption("ver", default=None) or os.getenv("TEST_VERSION"))
    if not target:
        print("[DEBUG] No version filter set; leaving all items intact.")
        return
    selected = [
        i for i in items
        if (m := i.get_closest_marker("ver")) and m.args and _normalize_version(m.args[0]) == target
    ]
    deselected = [i for i in items if i not in selected]
    if selected:
        print(f"[DEBUG] Version filter active: v{target} → {len(selected)} selected, {len(deselected)} deselected.")
        config.hook.pytest_deselected(items=deselected)
        items[:] = selected
    else:
        print(f"[DEBUG] Version filter v{target} matched 0 tests; leaving all items intact.")

# -------------------------------------------------------------------------------------------------
# 🧱 Fixtures
# -------------------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def console_fixture() -> Console:
    return console

# Only define mocks and clients for non-integration modes
if INTEGRATION_MODE != "1":
    @pytest.fixture(scope="session")
    def mock_zendesk_service(monkeypatch):
        mock = MagicMock()
        monkeypatch.setattr("backend.services.zendesk_service", mock)
        return mock

    @pytest.fixture(scope="session")
    def test_client():
        client = TestClient(base_app)
        yield client
        client.close()

_debug_log("Global conftest.py loaded successfully.")
