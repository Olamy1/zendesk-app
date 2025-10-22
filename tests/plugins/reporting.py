# =================================================================================================
# File: tests/plugins/reporting.py
# Purpose:
#   Rich reporting + performance analytics plugin for the OAPS Zendesk App test suite.
#
# Structural Alignment (v2.2):
#   - Non-blocking Rich reporting layer.
#   - Collects module metrics without interfering with pytest execution.
#   - Outputs 3-column tables (Test / Status / Details) per module.
#   - Works in UNIT, TEST, and INTEGRATION modes.
#
# Version: 2.2.0 | October 2025
# Author: Olivier Lamy
# =================================================================================================

import os
import time
import json
import socket
import pathlib
from statistics import mean
from collections import defaultdict
import pytest
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# --- Initialization ---
console = Console()
console.print("[bold cyan]✅ OAPS Zendesk QA Analytics Plugin Loaded[/bold cyan]")

# ---------------------------------------------------------------------------------------------
# 🔧 Environment Override Detection
# ---------------------------------------------------------------------------------------------
if os.getenv("PYTEST_INTEGRATION_OVERRIDE") == "1" or os.getenv("INTEGRATION_MODE") == "1":
    os.environ["APP_ENV"] = "integration"
    os.environ["UNIT_MODE"] = "0"
    os.environ["INTEGRATION_MODE"] = "1"
    ENV_LABEL = "INTEGRATION"
else:
    os.environ.setdefault("APP_ENV", "unit")
    os.environ.setdefault("UNIT_MODE", "1")
    os.environ.setdefault("INTEGRATION_MODE", "0")
    ENV_LABEL = "UNIT"

# 🧭 Diagnostic Banner
console.rule("[bold cyan]OAPS Zendesk App — Test Context[/bold cyan]")
console.print(
    f"┌─────────────┬─────────────────────┐\n"
    f"│ Environment │ {ENV_LABEL:<19} │\n"
    f"│ Mode        │ {ENV_LABEL:<19} │\n"
    f"│ Python      │ {os.sys.version_info.major}.{os.sys.version_info.minor} │\n"
    f"│ Timestamp   │ {time.strftime('%Y-%m-%dT%H:%M:%S')} │\n"
    f"└─────────────┴─────────────────────┘"
)


# ---------------------------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------------------------
_seen_reports = set()
_module_results = defaultdict(list)
_module_exec_order = []        # Track execution order for clean reporting
_latency_by_group = defaultdict(list)
_global_totals = {"passed": 0, "failed": 0, "skipped": 0}
_suite_start_time = time.time()
_slowest_test = {"name": None, "duration": 0.0}

# ---------------------------------------------------------------------------------------------
# 🌐 Environment Diagnostics
# ---------------------------------------------------------------------------------------------
def _check_port(host, port, label):
    # Skip checks in UNIT_MODE
    if os.getenv("UNIT_MODE") == "1":
        console.print(f"☑️  {label} check skipped in UNIT MODE.")
        return True

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    try:
        sock.connect((host, port))
        console.print(f"🟢 {label} reachable at {host}:{port}")
        return True
    except Exception:
        console.print(f"🔴 {label} unreachable at {host}:{port}", style="bold red")
        return False
    finally:
        sock.close()

# ---------------------------------------------------------------------------------------------
# 🏁 Session Start
# ---------------------------------------------------------------------------------------------
def pytest_sessionstart(session):
    console.rule("[bold blue]Pre-Run Health Checks (Plugin)[/bold blue]")
    _check_port(
        os.getenv("API_HOST", "localhost"),
        int(os.getenv("API_PORT", "8000")),
        "Zendesk Reporting API"
    )
    console.print("⚙️  Environment OK — starting test suite...\n")

# ---------------------------------------------------------------------------------------------
# 🧩 Log Reports
# ---------------------------------------------------------------------------------------------
def pytest_runtest_logreport(report):
    if report.when != "call" or report.nodeid in _seen_reports:
        return
    _seen_reports.add(report.nodeid)

    module_path = str(pathlib.Path(report.fspath).resolve())
    if module_path not in _module_exec_order:
        _module_exec_order.append(module_path)

    test_name = report.nodeid.split("::")[-1]
    duration = float(getattr(report, "duration", 0.0) or 0.0)

    if duration > _slowest_test["duration"]:
        _slowest_test.update({"name": test_name, "duration": duration})

    # Categorize by keyword for group latency metrics
    group = "misc"
    name_lower = test_name.lower()
    if "ticket" in name_lower:
        group = "tickets"
    elif "user" in name_lower:
        group = "users"
    elif "export" in name_lower:
        group = "export"
    _latency_by_group[group].append(duration)

    # Outcome handling
    if report.outcome == "failed":
        _global_totals["failed"] += 1
        status = "Failed"
        detail = f"❌ {getattr(report.longrepr, 'reprcrash', None) or 'Failure'}"
        color = "red"
    elif report.outcome == "skipped":
        _global_totals["skipped"] += 1
        status = "Skipped"
        detail = "⚠︎ Skipped"
        color = "yellow"
    else:
        _global_totals["passed"] += 1
        status = "Passed"
        detail = "✔︎ OK"
        color = "green"

    _module_results[module_path].append((test_name, status, detail, color, duration))

# ---------------------------------------------------------------------------------------------
# 📊 Summary & Reporting
# ---------------------------------------------------------------------------------------------
@pytest.hookimpl(tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    suite_runtime = time.time() - _suite_start_time
    summary_json = {"modules": {}, "totals": _global_totals, "runtime": suite_runtime}

    if not session.items:
        return

    # === Per-module reports ===
    for module_path in _module_exec_order:
        results = _module_results[module_path]
        if not results:
            continue

        rel_path = os.path.relpath(module_path, os.getcwd())
        console.rule(f"[bold cyan]{rel_path} Results[/bold cyan]")

        # 3-column table setup
        table = Table(show_header=True, header_style="bold white")
        table.add_column("Test", style="white", no_wrap=True)
        table.add_column("Status", justify="center", width=10)
        table.add_column("Details", justify="left")

        passed = failed = skipped = 0

        for test_name, status, detail, color, _ in results:
            if status == "Passed":
                passed += 1
            elif status in ("Failed", "Error"):
                failed += 1
            else:
                skipped += 1

            table.add_row(
                f"[white]{test_name}[/white]",
                f"[{color}]{status}[/{color}]",
                f"[{color}]{detail}[/{color}]",
            )

        summary_json["modules"][rel_path] = {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
        }

        console.print(table)
        console.print(
            f"[green]{passed} passed[/green], "
            f"[red]{failed} failed[/red], "
            f"[yellow]{skipped} skipped[/yellow]\n"
        )

    # === Global Summary ===
    console.rule("[bold magenta]Global Test Summary[/bold magenta]")
    summary_text = (
        f"[green]{_global_totals['passed']} passed[/green] | "
        f"[red]{_global_totals['failed']} failed[/red] | "
        f"[yellow]{_global_totals['skipped']} skipped[/yellow]"
    )
    console.print(f"🧮 Results ({suite_runtime:.2f}s): {summary_text}")
    console.print(f"🐢 Slowest Test: {_slowest_test['name']} ({_slowest_test['duration']:.2f}s)")

    if _global_totals["failed"] == 0:
        console.print(Panel("✅ All tests passed — system healthy.", style="green"))
    else:
        console.print(Panel("❌ Some tests failed — investigate immediately.", style="red"))

    # === Write JSON summary ===
    output_path = pathlib.Path("zendesk_test_summary.json")
    with output_path.open("w") as f:
        json.dump(summary_json, f, indent=2)
    console.print(f"🗂 Summary written to {output_path.resolve()}", style="dim")

# =================================================================================================
# END OF FILE
# =================================================================================================
