# =====================================================================
# File: tests/unit/conftest.py
# Description: Shared pytest fixtures
# =====================================================================

import pytest
from rich.console import Console
from rich.traceback import install
import shutil
import os

def pytest_sessionstart(session):
    """Automatically clear pytest and python caches at start of run."""
    # remove .pytest_cache
    if os.path.exists(".pytest_cache"):
        shutil.rmtree(".pytest_cache", ignore_errors=True)

    # remove all __pycache__ dirs
    for root, dirs, files in os.walk("."):
        for d in dirs:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)


# enable rich tracebacks
install(show_locals=True)

console = Console()

@pytest.fixture(autouse=True)
def rich_logging():
    console.rule("[bold blue]TEST START")
    yield
    console.rule("[bold red]TEST END")

@pytest.fixture
def sample_ticket():
    return {
        "id": 101,
        "subject": "Test ticket",
        "status": "open",
        "assignee_id": 1234,
        "group_id": 5678,
    }



