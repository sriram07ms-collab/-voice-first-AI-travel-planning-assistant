"""
Structured error logging system for automated error detection and fixing.
Logs errors in JSON format for easy parsing and automated fixes.
"""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum
import sys

logger = logging.getLogger(__name__)

# Error log directory
ERROR_LOG_DIR = Path("logs/errors")
ERROR_LOG_DIR.mkdir(parents=True, exist_ok=True)


class ErrorCategory(Enum):
    """Error categories for classification."""
    API_ERROR = "api_error"
    VALIDATION_ERROR = "validation_error"
    DATABASE_ERROR = "database_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    CONFIGURATION_ERROR = "configuration_error"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"
    PERMISSION_ERROR = "permission_error"
    RESOURCE_NOT_FOUND = "resource_not_found"
    RATE_LIMIT_ERROR = "rate_limit_error"
    TIMEOUT_ERROR = "timeout_error"
    UNKNOWN_ERROR = "unknown_error"


class ErrorLogger:
    """Structured error logger for automated error detection."""
    
    def __init__(self, log_file: str = "error_log.jsonl"):
        """
        Initialize error logger.
        
        Args:
            log_file: Name of the log file (JSON Lines format)
        """
        self.log_file = ERROR_LOG_DIR / log_file
        self.log_file.touch(exist_ok=True)
    
    def log_error(
        self,
        error: Exception,
        category: ErrorCategory,
        context: Optional[Dict[str, Any]] = None,
        request_info: Optional[Dict[str, Any]] = None,
        auto_fixable: bool = False,
        fix_suggestion: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log an error in structured JSON format.
        
        Args:
            error: The exception object
            category: Error category
            context: Additional context about the error
            request_info: Request information (if applicable)
            auto_fixable: Whether this error can be auto-fixed
            fix_suggestion: Suggested fix for the error
        
        Returns:
            Error log entry dictionary
        """
        error_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "category": category.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "auto_fixable": auto_fixable,
            "fix_suggestion": fix_suggestion,
            "context": context or {},
            "request_info": request_info or {},
            "python_version": sys.version,
        }
        
        # Write to JSONL file (one JSON object per line)
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(error_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write error log: {e}")
        
        # Also log to standard logger
        logger.error(
            f"[{category.value}] {type(error).__name__}: {str(error)}",
            extra={"error_entry": error_entry},
            exc_info=True
        )
        
        return error_entry
    
    def detect_error_pattern(self, error: Exception) -> Dict[str, Any]:
        """
        Detect error patterns for automated fixing.
        
        Args:
            error: The exception object
        
        Returns:
            Dictionary with detected pattern and fix suggestion
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        traceback_str = traceback.format_exc().lower()
        
        patterns = {
            "groq_api_model_decommissioned": {
                "pattern": "model.*decommissioned" in error_str,
                "category": ErrorCategory.EXTERNAL_SERVICE_ERROR,
                "auto_fixable": True,
                "fix_suggestion": "Update model name to latest supported version",
                "fix_action": "update_model"
            },
            "groq_api_400_max_tokens": {
                "pattern": "400" in error_str and ("max_tokens" in traceback_str or "context" in error_str),
                "category": ErrorCategory.EXTERNAL_SERVICE_ERROR,
                "auto_fixable": True,
                "fix_suggestion": "Reduce max_tokens or increase context window",
                "fix_action": "adjust_max_tokens"
            },
            "city_not_found": {
                "pattern": "city" in error_str and ("not found" in error_str or "could not find" in error_str),
                "category": ErrorCategory.RESOURCE_NOT_FOUND,
                "auto_fixable": False,
                "fix_suggestion": "Verify city name spelling or add country/state",
                "fix_action": None
            },
            "poi_search_empty": {
                "pattern": "could not find any points of interest" in error_str,
                "category": ErrorCategory.RESOURCE_NOT_FOUND,
                "auto_fixable": False,
                "fix_suggestion": "Check city name, interests, or OpenStreetMap data availability",
                "fix_action": None
            },
            "cors_error": {
                "pattern": "cors" in error_str or "access-control-allow-origin" in error_str,
                "category": ErrorCategory.CONFIGURATION_ERROR,
                "auto_fixable": True,
                "fix_suggestion": "Add origin to CORS_ORIGINS in .env",
                "fix_action": "update_cors"
            },
            "import_error": {
                "pattern": "modulenotfounderror" in error_type.lower() or "importerror" in error_type.lower(),
                "category": ErrorCategory.CONFIGURATION_ERROR,
                "auto_fixable": True,
                "fix_suggestion": "Install missing package or fix import path",
                "fix_action": "fix_import"
            },
            "connection_error": {
                "pattern": "connection" in error_str or "connectionerror" in error_type.lower(),
                "category": ErrorCategory.NETWORK_ERROR,
                "auto_fixable": False,
                "fix_suggestion": "Check network connection or service availability",
                "fix_action": None
            },
            "timeout_error": {
                "pattern": "timeout" in error_str or "timeouterror" in error_type.lower(),
                "category": ErrorCategory.TIMEOUT_ERROR,
                "auto_fixable": True,
                "fix_suggestion": "Increase timeout or optimize request",
                "fix_action": "increase_timeout"
            },
        }
        
        for pattern_name, pattern_info in patterns.items():
            if pattern_info["pattern"]:
                return pattern_info
        
        # Default pattern
        return {
            "category": ErrorCategory.UNKNOWN_ERROR,
            "auto_fixable": False,
            "fix_suggestion": "Manual investigation required",
            "fix_action": None
        }


# Global error logger instance
_error_logger: Optional[ErrorLogger] = None


def get_error_logger() -> ErrorLogger:
    """Get or create global error logger instance."""
    global _error_logger
    if _error_logger is None:
        _error_logger = ErrorLogger()
    return _error_logger


def log_error_auto(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    request_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Automatically log error with pattern detection.
    
    Args:
        error: The exception object
        context: Additional context
        request_info: Request information
    
    Returns:
        Error log entry with detected pattern
    """
    error_logger = get_error_logger()
    pattern = error_logger.detect_error_pattern(error)
    
    return error_logger.log_error(
        error=error,
        category=pattern["category"],
        context=context,
        request_info=request_info,
        auto_fixable=pattern.get("auto_fixable", False),
        fix_suggestion=pattern.get("fix_suggestion")
    )
