# =================================================================================================
# File: tests/conftest.py
# Purpose:
#   Canonical pytest configuration and environment router for the OAPS Zendesk App test suite.
#
# Structural Alignment (v2.3.4):
#   - Ensures APP_ENV is locked *before* any backend import occurs.
#   - Auto-detects mode (unit/integration) based on path or flags.
#   - Prevents double initialization and ensures consistent environment values.
#   - Preserves console banner, debug logs, and version filter logic.
#
#   Both (separate stages)
#   pytest -q # unit
#   pytest -m integration -q -o addopts='' # integration
#
# Author: Olivier Lamy | October 2025
# =================================================================================================

from __future__ import annotations
import os
import sys
import time
import pytest
from unittest.mock import MagicMock
from rich.console import Console
from rich.table import Table
from fastapi.testclient import TestClient

# =================================================================================================
# 🔒 Early Environment Lock (Absolute First Step)
# =================================================================================================

if not os.getenv("PYTEST_ENV_LOCKED"):
    def _detect_test_mode() -> str:
        """Detect whether pytest was invoked for unit or integration tests."""
        args = " ".join(sys.argv).lower()
        if "tests/integration" in args or "tests\\integration" in args:
            return "integration"
        return "unit"

    mode = _detect_test_mode()
    print(f"🧩 [Bootstrap] Resolving environment from path → {mode.upper()}")

    # Apply environment
    os.environ.update({
        "APP_ENV": mode,
        "UNIT_MODE": "1" if mode == "unit" else "0",
        "INTEGRATION_MODE": "1" if mode == "integration" else "0",
        "PYTEST_ENV_LOCKED": "1",
        "PYTEST_INTEGRATION_OVERRIDE": "1" if mode == "integration" else "0",
    })

print(f"🔐 [Env Locked] APP_ENV={os.getenv('APP_ENV')} | UNIT_MODE={os.getenv('UNIT_MODE')} | INTEGRATION_MODE={os.getenv('INTEGRATION_MODE')}")

# =================================================================================================
# 🌐 Runtime Initialization
# =================================================================================================

APP_ENV = os.getenv("APP_ENV", "test").lower()
UNIT_MODE = "1" if os.getenv("UNIT_MODE") == "1" else "0"
INTEGRATION_MODE = "1" if os.getenv("INTEGRATION_MODE") == "1" else "0"

# Fallback safety
if UNIT_MODE == "0" and INTEGRATION_MODE == "0":
    APP_ENV = "test"

os.environ.update({
    "APP_ENV": APP_ENV,
    "UNIT_MODE": UNIT_MODE,
    "INTEGRATION_MODE": INTEGRATION_MODE,
})

console = Console()

def _debug_log(msg: str):
    if os.getenv("DEBUG_PYTEST", "1") == "1":
        print(f"[DEBUG] {msg}")

# -------------------------------------------------------------------
# 🔍 Visual Mode Banner
# -------------------------------------------------------------------
mode_str = (
    "INTEGRATION" if INTEGRATION_MODE == "1"
    else "UNIT" if UNIT_MODE == "1"
    else "TEST"
)
print(f" [{mode_str} MODE ACTIVE] — Environment initialized.")
_debug_log(f"Bootstrap: APP_ENV={APP_ENV}, UNIT_MODE={UNIT_MODE}, INTEGRATION_MODE={INTEGRATION_MODE}")


# -------------------------------------------------------------------------------------------------
# 🚫 Disable Security Middleware for UNIT_MODE
# -------------------------------------------------------------------------------------------------
if UNIT_MODE == "1":
    _debug_log("UNIT_MODE active → Patching SecurityMiddleware to bypass auth checks.")
    try:
        import backend.middleware.security as security

        def _bypass_auth_middleware(app):
            """Replaces SecurityMiddleware with a no-op during unit tests."""
            _debug_log("Bypassing SecurityMiddleware (UNIT_MODE).")
            return app

        security.SecurityMiddleware = _bypass_auth_middleware
    except Exception as e:
        print(f"[WARN] Could not patch SecurityMiddleware: {e}")

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
    table.add_row("Mode", mode_str)
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
# 🔢 Version Filtering (Preserved)
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
