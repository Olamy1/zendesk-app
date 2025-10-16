# =================================================================================================
# File: backend/middleware/rate_limit.py
# Purpose: Lightweight in-memory rate limiter for FastAPI API routes.
# Author: Olivier Lamy | Version: 2.0.1 | October 2025
# =================================================================================================

import os
import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

# -------------------------------------------------------------------------------------------------
# Configuration
# -------------------------------------------------------------------------------------------------
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))   # seconds
MAX_REQUESTS_PER_IP = int(os.getenv("MAX_REQUESTS_PER_IP", "30"))

# Tracks timestamps of recent requests per IP
_request_cache: dict[str, list[float]] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    =================================================================================================
    Class: RateLimitMiddleware
    Purpose:
        Provides a lightweight, per-IP in-memory rate limiter for API endpoints.

    Behavior:
        • Enforces a configurable request cap (`MAX_REQUESTS_PER_IP`) within a rolling window
          defined by `RATE_LIMIT_WINDOW` (in seconds).
        • Applies only to API routes (`/api/*`), skipping documentation and health endpoints.
        • Designed for simplicity and local environments—does not rely on external stores like Redis.
        • Raises HTTP 429 when request frequency exceeds configured threshold.

    Bypass Conditions:
        • `UNIT_MODE=1` → Used during local/unit tests to skip enforcement.
        • `APP_ENV ∈ {local, test}` → Skips enforcement in development/test environments.
        • Requests to "/", "/docs", "/openapi.json", or "/redoc" are always ignored.

    Proxy Awareness:
        • Honors `X-Forwarded-For` header when running behind proxies or load balancers
          (e.g., Nginx, Azure Front Door, Cloudflare).
        • Falls back to `request.client.host` when header is missing.

    Configuration:
        - RATE_LIMIT_WINDOW: Duration (seconds) of the sliding window. Default: 60.
        - MAX_REQUESTS_PER_IP: Maximum number of allowed requests per IP in the window. Default: 30.

    Example .env:
        RATE_LIMIT_WINDOW=60
        MAX_REQUESTS_PER_IP=30

    Raises:
        HTTPException(429): When an IP exceeds the maximum number of allowed requests
                            within the configured window.

    Notes:
        • This middleware is stateless and thread-safe for single-process FastAPI apps.
        • For distributed deployments, use a shared cache backend (e.g., Redis) instead.
    =================================================================================================
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path or ""

        # Skip for non-API routes, docs, and test/local environments
        if (
            not path.startswith("/api")
            or path in {"/", "/docs", "/openapi.json", "/redoc"}
            or os.getenv("UNIT_MODE") == "1"
            or os.getenv("APP_ENV", "").lower() in {"local", "test"}
        ):
            return await call_next(request)

        # Determine client IP (use X-Forwarded-For if present)
        xff = request.headers.get("X-Forwarded-For")
        client_ip = (xff.split(",")[0].strip() if xff else None) or request.client.host

        now = time.time()
        history = _request_cache.get(client_ip, [])

        # Retain only timestamps within current window
        history = [t for t in history if now - t < RATE_LIMIT_WINDOW]
        history.append(now)

        if len(history) > MAX_REQUESTS_PER_IP:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Try again in {RATE_LIMIT_WINDOW} seconds."
                },
            )

        # Update cache and proceed
        _request_cache[client_ip] = history
        return await call_next(request)
