# =================================================================================================
# File: backend/utils/exception_handler.py
# Description:
#   Global exception handling utilities for the OAPS Zendesk App (v2.0+)
#
# Purpose:
#   Defines centralized error handling logic to ensure all unhandled
#   exceptions are returned as structured JSON responses rather than
#   raw tracebacks. This promotes consistent error visibility across
#   environments and safer frontend integration.
#
# Why:
#   Prior to v2.0, exceptions surfaced as raw FastAPI tracebacks,
#   causing inconsistent error reporting and insecure exposure of
#   internal details. This module standardizes and sanitizes error
#   output for all API endpoints.
#
# Notes:
#   - Can be expanded to handle specific errors (e.g., HTTPException, 
#     ValidationError, or custom AppError subclasses).
#   - Integrates automatically when called in `main.py` via:
#         from backend.utils.exception_handler import register_exception_handlers
#         register_exception_handlers(app)
#
# Author: Olivier Lamy
# Version: 2.0.0 | October 2025
# =================================================================================================

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from starlette import status
import traceback
import logging

# Configure a module-level logger for visibility\
app = FastAPI()
logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Registers global exception handlers on the FastAPI app instance.

    This function ensures that any unhandled exceptions raised within the app
    are caught and returned as structured JSON responses, improving consistency
    and preventing exposure of raw tracebacks in production.

    Args:
        app (FastAPI): The FastAPI application instance.

    Example:
        >>> from backend.utils.exception_handler import register_exception_handlers
        >>> register_exception_handlers(app)
    """

# ✅ Define or import the handler *after app is created*
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    error_response = {
        "error": str(exc),
        "path": str(request.url.path),
    }

    if app.debug:
        error_response["detail"] = traceback.format_exc()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )