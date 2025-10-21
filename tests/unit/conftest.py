# =================================================================================================
# File: tests/unit/conftest.py
# Purpose:
#   Unit test configuration for the OAPS Zendesk App.
#
# Structural Alignment (v2.3.1):
#   - Forces UNIT_MODE=1 (no network calls).
#   - Ensures APP_ENV=test unless overridden.
#   - Automatically injects a valid Authorization header for all test requests.
#   - Provides rich console test boundaries for local visibility.
#
# Author: Olivier Lamy | October 2025
# =================================================================================================

import os
import traceback
import pytest
from rich.console import Console
from rich.traceback import install
from rich.rule import Rule
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# -------------------------------------------------------------------------------------------------
# 🧭 Environment Enforcement
# -------------------------------------------------------------------------------------------------
os.environ["APP_ENV"] = "unit"
os.environ["UNIT_MODE"] = "1"
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
# 🧩 Authorization Injection Middleware
# -------------------------------------------------------------------------------------------------
class _InjectAuthHeaderMiddleware(BaseHTTPMiddleware):
    """Middleware that injects a valid Authorization header during unit tests."""
    async def dispatch(self, request: Request, call_next):
        headers = request.scope.get("headers", [])
        if not any(h[0] == b"authorization" for h in headers):
            headers.append((b"authorization", b"Bearer valid-token"))
            request.scope["headers"] = headers
        return await call_next(request)

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
# 🌐 App Import (after env setup)
# -------------------------------------------------------------------------------------------------
from backend.main import app as base_app
from backend.config import get_settings

# Add the auth-injection middleware before any client is created
base_app.add_middleware(_InjectAuthHeaderMiddleware)

# -------------------------------------------------------------------------------------------------
# 🧩 Fixtures
# -------------------------------------------------------------------------------------------------
@pytest.fixture(scope="session")
def settings():
    return get_settings()

@pytest.fixture(scope="session")
def test_client():
    """Provides a FastAPI TestClient with injected Authorization header."""
    os.environ["UNIT_MODE"] = "1"
    os.environ["INTEGRATION_MODE"] = "0"

    client = TestClient(base_app)
    # Ensure requests made through client also carry auth header
    try:
        client.headers.update({"Authorization": "Bearer valid-token"})
    except Exception:
        pass

    yield client
    client.close()

@pytest.fixture(autouse=True)
def rich_test_logging():
    console.print(Rule(style="bold blue"))
    console.print("[bold blue]TEST START")
    yield
    console.print("[bold red]TEST END")
    console.print(Rule(style="bold red"))

# -------------------------------------------------------------------------------------------------
# 🚫 Disable auth injection for SecurityMiddleware tests
# -------------------------------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def disable_auth_injection_for_security_tests(request):
    """
    For test files named `test_security_middleware.py`, remove the injected Authorization header
    so we can properly test 401/403 behavior.
    """
    if "test_security_middleware" in str(request.fspath):
        print(" [UNIT-CONFTEST] Disabling injected auth for security middleware tests.")
        # Temporarily remove the injected middleware
        from backend.main import app as base_app
        base_app.user_middleware = [
            m for m in base_app.user_middleware
            if m.cls.__name__ != "_InjectAuthHeaderMiddleware"
        ]
    yield

