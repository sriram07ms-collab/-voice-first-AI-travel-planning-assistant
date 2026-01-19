"""
Pydantic models for API requests.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., min_length=1, description="User message (voice or text)")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    language: Optional[str] = Field(default="en", description="Language code")


class PlanRequest(BaseModel):
    """Request model for direct planning endpoint."""
    city: str = Field(..., min_length=1, description="City name")
    duration_days: int = Field(..., ge=1, le=30, description="Number of days")
    interests: List[str] = Field(default_factory=list, description="User interests")
    pace: Optional[str] = Field(None, description="Pace preference (relaxed/moderate/fast)")
    budget: Optional[str] = Field(None, description="Budget preference")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional constraints")


class EditRequest(BaseModel):
    """Request model for edit endpoint."""
    session_id: str = Field(..., description="Session ID")
    edit_command: str = Field(..., min_length=1, description="Edit command (voice or text)")
    edit_type: Optional[str] = Field(None, description="Edit type (CHANGE_PACE, SWAP_ACTIVITY, etc.)")


class ExplainRequest(BaseModel):
    """Request model for explanation endpoint."""
    session_id: str = Field(..., description="Session ID")
    question: str = Field(..., min_length=1, description="Question to explain")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")


class GeneratePDFRequest(BaseModel):
    """Request model for PDF generation endpoint."""
    session_id: str = Field(..., description="Session ID")
    email: Optional[str] = Field(None, description="Email address to send PDF")
    itinerary_data: Optional[Dict[str, Any]] = Field(None, description="Itinerary data (if session_id not available)")
