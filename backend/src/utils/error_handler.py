"""
Error handling middleware and custom exceptions.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
import logging
import traceback

logger = logging.getLogger(__name__)


class TravelAssistantException(Exception):
    """Base exception for travel assistant errors."""
    def __init__(self, message: str, error_type: str = "UNKNOWN_ERROR", status_code: int = 500, details: Optional[dict] = None):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class CityNotFoundError(TravelAssistantException):
    """Raised when city is not found."""
    def __init__(self, city: str, suggestions: Optional[list] = None):
        super().__init__(
            message=f"City '{city}' not found. Please check the spelling or provide country/state.",
            error_type="CITY_NOT_FOUND",
            status_code=404,
            details={"city": city, "suggestions": suggestions or []}
        )


class POINotFoundError(TravelAssistantException):
    """Raised when POIs cannot be found for a city."""
    def __init__(self, city: str):
        super().__init__(
            message=f"Could not find points of interest for '{city}'.",
            error_type="POI_NOT_FOUND",
            status_code=404,
            details={"city": city}
        )


class ItineraryGenerationError(TravelAssistantException):
    """Raised when itinerary generation fails."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_type="ITINERARY_GENERATION_ERROR",
            status_code=500,
            details=details or {}
        )


class EditValidationError(TravelAssistantException):
    """Raised when edit validation fails."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            error_type="EDIT_VALIDATION_ERROR",
            status_code=400,
            details=details or {}
        )


class SessionNotFoundError(TravelAssistantException):
    """Raised when session is not found."""
    def __init__(self, session_id: str):
        super().__init__(
            message=f"Session '{session_id}' not found.",
            error_type="SESSION_NOT_FOUND",
            status_code=404,
            details={"session_id": session_id}
        )


class MCPConnectionError(TravelAssistantException):
    """Raised when MCP connection fails."""
    def __init__(self, tool_name: str):
        super().__init__(
            message=f"Failed to connect to MCP tool '{tool_name}'.",
            error_type="MCP_CONNECTION_ERROR",
            status_code=503,
            details={"tool_name": tool_name}
        )


class RAGRetrievalError(TravelAssistantException):
    """Raised when RAG retrieval fails."""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            error_type="RAG_RETRIEVAL_ERROR",
            status_code=500
        )


class EvaluationError(TravelAssistantException):
    """Raised when evaluation fails."""
    def __init__(self, message: str, evaluator_type: str):
        super().__init__(
            message=message,
            error_type="EVALUATION_ERROR",
            status_code=500,
            details={"evaluator_type": evaluator_type}
        )


async def error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global error handler for FastAPI with automated error logging.
    
    Args:
        request: FastAPI request object
        exc: Exception that was raised
    
    Returns:
        JSONResponse with error details
    """
    # Import error logger
    from .error_logger import log_error_auto, ErrorCategory
    
    # Prepare request info
    request_info = {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "client": request.client.host if request.client else None,
    }
    
    # Handle custom exceptions
    if isinstance(exc, TravelAssistantException):
        # Log with error logger
        log_error_auto(exc, context={"details": exc.details}, request_info=request_info)
        
        logger.error(f"{exc.error_type}: {exc.message}", extra={"details": exc.details})
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error_type": exc.error_type,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    # Handle HTTPException
    if isinstance(exc, HTTPException):
        logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "error_type": "HTTP_ERROR",
                "message": exc.detail,
                "details": {}
            }
        )
    
    # Handle validation errors (Pydantic)
    if "pydantic" in str(type(exc)).lower():
        logger.error(f"Validation error: {exc}")
        return JSONResponse(
            status_code=422,
            content={
                "status": "error",
                "error_type": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": str(exc)}
            }
        )
    
    # Handle unexpected errors
    # Log with automated error logger
    error_entry = log_error_auto(exc, context={}, request_info=request_info)
    
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    error_traceback = traceback.format_exc()
    
    # In production, don't expose full traceback
    # Check both app.debug and settings.debug
    show_traceback = False
    if hasattr(request.app, 'debug'):
        show_traceback = request.app.debug
    # Also check settings if available
    try:
        from src.utils.config import settings
        show_traceback = show_traceback or settings.debug
    except:
        pass
    
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_type": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {
                "traceback": error_traceback if show_traceback else None
            }
        }
    )


def handle_api_error(error: Exception, context: str = "") -> dict:
    """
    Handle API-related errors and return formatted error dict.
    
    Args:
        error: Exception that occurred
        context: Additional context string
    
    Returns:
        Formatted error dictionary
    """
    error_msg = f"{context}: {str(error)}" if context else str(error)
    logger.error(error_msg, exc_info=True)
    
    if isinstance(error, TravelAssistantException):
        return {
            "status": "error",
            "error_type": error.error_type,
            "message": error.message,
            "details": error.details
        }
    
    return {
        "status": "error",
        "error_type": "API_ERROR",
        "message": error_msg,
        "details": {}
    }
