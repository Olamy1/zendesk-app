# =================================================================================================
# File: backend/utils/error_handler.py
# Description:
#   Global exception handling utilities for the OAPS Zendesk App (v2.0+)
# =================================================================================================

from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from starlette import status
import traceback
import logging

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Registers global exception handlers on the provided FastAPI app instance."""
    app.add_exception_handler(Exception, generic_exception_handler)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    error_response = {
        "error": str(exc),
        "path": str(request.url.path),
    }

    # Attach traceback in debug mode only
    try:
        if getattr(request.app, "debug", False):
            error_response["detail"] = traceback.format_exc()
    except Exception:
        pass

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response,
    )

