# =================================================================================================
# File: backend/main.py
# Description:
#   Entry point for the OAPS Zendesk App (v2.0+)
#
# Purpose:
#   Initializes the FastAPI application, loads configuration,
#   registers routers, applies middleware, and attaches global
#   exception handlers for the unified Zendesk Reporting API.
#
# Why:
#   Prior versions (v1.x) relied on static configuration and manual
#   endpoint registration. This refactor establishes a maintainable,
#   versioned API structure with unified exception handling and
#   environment-driven configuration.
#
# Notes:
#   - Maintains backward compatibility with v1 routes while
#     introducing versioned `/api/v2/...` endpoints.
#   - Integrates dotenv configuration via config.py.
#   - Serves as the foundation for v2.0_app_infra (environment + routing).
#
# Author: Olivier Lamy
# Version: 2.0.1 | October 2025
# =================================================================================================

import os
import logging
import traceback
from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.routers import tickets, users
from backend.middleware import security_middleware

app.include_router(tickets.router, prefix="/tickets", tags=["Tickets"])
app.include_router(users.router, prefix="/users", tags=["Users"])

# ---------------------------------------------------------------------------------------------
# 🧭 Early Bootstrap — Load .env and Normalize Environment
# ---------------------------------------------------------------------------------------------
load_dotenv()  # must run before any internal imports

# Ensure integration/unit mode is correct before get_settings() runs
if os.getenv("INTEGRATION_MODE") == "1":
    os.environ["APP_ENV"] = "integration"
    os.environ["UNIT_MODE"] = "0"
elif os.getenv("UNIT_MODE") == "1":
    os.environ.setdefault("APP_ENV", "unit")
else:
    os.environ.setdefault("APP_ENV", "local")

print(
    f"[BOOTSTRAP] APP_ENV={os.getenv('APP_ENV')}, "
    f"UNIT_MODE={os.getenv('UNIT_MODE')}, "
    f"INTEGRATION_MODE={os.getenv('INTEGRATION_MODE')}"
)

# ---------------------------------------------------------------------------------------------
# 🧩 Internal Imports (now safe)
# ---------------------------------------------------------------------------------------------
from backend.config import get_settings
from backend.utils.error_handler import register_exception_handlers
from backend.middleware.security import TokenAuthMiddleware
from backend.middleware.rate_limit import RateLimitMiddleware
from backend.routers import tickets, users

# Load settings once
settings = get_settings()

# ---------------------------------------------------------------------------------------------
# 🚀 App Initialization
# ---------------------------------------------------------------------------------------------
app = FastAPI(
    title="OAPS Zendesk App",
    description="Internal DOE tool for bi-weekly Zendesk reporting, reassignment, and export.",
    version="2.0.0",
)

# ---------------------------------------------------------------------------------------------
# 🌐 CORS Configuration
# ---------------------------------------------------------------------------------------------
origins = os.getenv("CORS_ORIGINS", "").split(",")
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ---------------------------------------------------------------------------------------------
# 🔐 Middleware
# ---------------------------------------------------------------------------------------------
app.add_middleware(TokenAuthMiddleware)
app.add_middleware(RateLimitMiddleware)

# ---------------------------------------------------------------------------------------------
# 🧩 Router Registration
# ---------------------------------------------------------------------------------------------
# v1 legacy
app.include_router(tickets.router, prefix="/api/tickets", tags=["Tickets"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
# v2 current
app.include_router(tickets.router, prefix="/api/v2/tickets", tags=["Tickets"])
app.include_router(users.router, prefix="/api/v2/users", tags=["Users"])

# ---------------------------------------------------------------------------------------------
# ⚙️ Exception Handling
# ---------------------------------------------------------------------------------------------
register_exception_handlers(app)
logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler ensuring JSON response even for uncaught errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    error_response = {"error": str(exc), "path": str(request.url.path)}
    if getattr(app, "debug", False):
        error_response["detail"] = traceback.format_exc()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )

# ---------------------------------------------------------------------------------------------
# 🩺 Health Check
# ---------------------------------------------------------------------------------------------
@app.get("/", tags=["Health"])
def read_root() -> dict[str, str]:
    return {"status": "ok", "message": "Zendesk Reporting API is running"}

# ---------------------------------------------------------------------------------------------
# 🧠 Lifespan Hook
# ---------------------------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        print(f"[Startup] Running in {settings.APP_ENV} mode | Debug={settings.DEBUG}")
    except Exception as e:
        print(f"[Startup Warning] Environment configuration load failed: {e}")
    yield
    print("[Shutdown] Application shutting down gracefully.")
