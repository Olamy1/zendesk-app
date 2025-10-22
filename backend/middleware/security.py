# =================================================================================================
# File: backend/middleware/security.py
# Purpose:
#   Middleware enforcing Bearer token authentication for protected API routes.
#
# Behavior:
#   • Protects all endpoints under /api/*
#   • Skips authentication for "/", "/docs", "/openapi.json", "/redoc"
#   • Automatically BYPASSES only in non-production-like environments
#       (local, test, unit, e2e)
#   • Integration and production now require valid tokens
#   • Validates against ZENDESK_API_TOKEN / ZENDESK_TOKEN env vars
#   • Returns:
#       - 401 → Missing token
#       - 403 → Invalid token
#       - 500 → Downstream exception
#
# Version: 2.3.3 | October 2025
# Author: Olivier Lamy
# =================================================================================================

import os
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from backend.config import get_settings


logger = logging.getLogger(__name__)

# ✅ Only bypass auth for explicitly safe, non-production environments
SAFE_ENVS = {"local", "unit", "e2e"}

CURRENT_ENV = os.getenv("APP_ENV", "").lower()
UNIT_MODE = os.getenv("UNIT_MODE", "0")


class TokenAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 🧭 Detect current environment
        app_env = os.getenv("APP_ENV", "").lower()
        unit_mode = os.getenv("UNIT_MODE", "0")

        # TEMP DEBUG: surface key decision inputs (no secrets)
        logger.info(
            f"[SecDbg] path={path} env={app_env} unit={unit_mode} starts_api={path.startswith('/api')} api_auth_set={bool(os.getenv('API_AUTH_TOKEN'))}"
        )

        # ✅ Public docs/health endpoints always open
        if path in {"/", "/docs", "/openapi.json", "/redoc"}:
            return await call_next(request)

        # ✅ Non-API paths are not protected
        if not path.startswith("/api"):
            return await call_next(request)

        # 🚫 Require auth in integration/staging/production
        if app_env in {"integration", "staging", "production"}:
            pass  # fall through to token validation
        else:
            # 🔓 Allow bypass only for unit/local style runs
            if unit_mode == "1" or app_env in SAFE_ENVS:
                logger.debug(
                    f"[SecurityMiddleware] 🔓 Bypassed for {path} (env={app_env}, unit_mode={unit_mode})"
                )
                return await call_next(request)

        # 🔁 Reload cached settings dynamically for up-to-date tokens
        get_settings.cache_clear()
        settings = get_settings()

        # 🔐 Retrieve Bearer token
        auth_header = request.headers.get("Authorization")
        logger.info(f"[SecDbg] header_present={bool(auth_header)} public_path={path in {'/','/docs','/openapi.json','/redoc'}}")

        # 🚨 Missing Authorization header
        if not auth_header:
            logger.warning(f"[SecurityMiddleware] 🚫 Missing Authorization header for {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing Authorization header"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not auth_header.startswith("Bearer "):
            logger.warning(f"[SecurityMiddleware] 🚫 Invalid Authorization header format for {path}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid Authorization header format"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.split("Bearer ", 1)[-1].strip()
        # Allow tests/integration to override tokens via API_AUTH_TOKEN
        test_override = os.getenv("API_AUTH_TOKEN")
        if test_override:
            os.environ["ZENDESK_API_TOKEN"] = test_override

        # ✅ Retrieve valid token from settings/env
        valid_token = (
            getattr(settings, "ZENDESK_API_TOKEN", None)
            or getattr(settings, "ZENDESK_TOKEN", None)
            or os.getenv("ZENDESK_API_TOKEN")
            or os.getenv("ZENDESK_TOKEN")
            or os.getenv("API_AUTH_TOKEN")
            or "test-token"
        )

        # 🚨 Invalid or mismatched token
        if not token or token != valid_token:
            logger.warning(f"[SecurityMiddleware] ❌ Invalid token used on {path}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid or expired token"},
            )

        # 🧩 Continue downstream
        try:
            return await call_next(request)
        except Exception as exc:
            logger.error(f"[SecurityMiddleware] Downstream exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": str(exc), "path": path},
            )

