"""
Rate limiting middleware for API endpoints.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
import time
import logging

logger = logging.getLogger(__name__)

# In-memory rate limiting store
# In production, use Redis for distributed rate limiting
_rate_limit_store: dict = defaultdict(list)


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.
    Limits requests per IP address.
    """
    
    def __init__(self, app, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip rate limiting for health check endpoint
        if request.url.path == "/health":
            return await call_next(request)
        
        # Check rate limits
        current_time = time.time()
        
        # Clean old entries (older than 1 hour)
        if client_ip in _rate_limit_store:
            _rate_limit_store[client_ip] = [
                timestamp for timestamp in _rate_limit_store[client_ip]
                if current_time - timestamp < 3600  # 1 hour
            ]
        
        # Check minute limit
        minute_ago = current_time - 60
        recent_requests = [
            timestamp for timestamp in _rate_limit_store[client_ip]
            if timestamp > minute_ago
        ]
        
        if len(recent_requests) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded (per minute) for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "error_type": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded: {self.requests_per_minute} requests per minute",
                    "retry_after": 60
                },
                headers={"Retry-After": "60"}
            )
        
        # Check hour limit
        hour_ago = current_time - 3600
        hourly_requests = [
            timestamp for timestamp in _rate_limit_store[client_ip]
            if timestamp > hour_ago
        ]
        
        if len(hourly_requests) >= self.requests_per_hour:
            logger.warning(f"Rate limit exceeded (per hour) for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "error_type": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded: {self.requests_per_hour} requests per hour",
                    "retry_after": 3600
                },
                headers={"Retry-After": "3600"}
            )
        
        # Record request
        _rate_limit_store[client_ip].append(current_time)
        
        # Continue with request
        return await call_next(request)


def get_rate_limit_status(client_ip: str) -> dict:
    """
    Get current rate limit status for an IP.
    
    Args:
        client_ip: Client IP address
    
    Returns:
        Dictionary with rate limit status
    """
    current_time = time.time()
    
    if client_ip not in _rate_limit_store:
        return {
            "requests_last_minute": 0,
            "requests_last_hour": 0,
            "limit_per_minute": 60,
            "limit_per_hour": 1000
        }
    
    timestamps = _rate_limit_store[client_ip]
    
    minute_ago = current_time - 60
    hour_ago = current_time - 3600
    
    recent_requests = [t for t in timestamps if t > minute_ago]
    hourly_requests = [t for t in timestamps if t > hour_ago]
    
    return {
        "requests_last_minute": len(recent_requests),
        "requests_last_hour": len(hourly_requests),
        "limit_per_minute": 60,
        "limit_per_hour": 1000,
        "remaining_per_minute": max(0, 60 - len(recent_requests)),
        "remaining_per_hour": max(0, 1000 - len(hourly_requests))
    }
