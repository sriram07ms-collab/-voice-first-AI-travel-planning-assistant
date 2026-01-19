"""
Pydantic models for API responses.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from .itinerary_models import Itinerary, Source, Evaluation


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    status: str = Field(..., description="Response status (success, clarifying, error)")
    message: Optional[str] = Field(None, description="Response message")
    itinerary: Optional[Itinerary] = Field(None, description="Generated itinerary")
    sources: Optional[List[Source]] = Field(default_factory=list, description="Sources and citations")
    evaluation: Optional[Evaluation] = Field(None, description="Evaluation results")
    session_id: str = Field(..., description="Session ID")
    clarifying_questions_count: Optional[int] = Field(None, ge=0, le=6, description="Number of clarifying questions asked")
    question: Optional[str] = Field(None, description="Clarifying question if status is 'clarifying'")


class PlanResponse(BaseModel):
    """Response model for plan endpoint."""
    status: str = Field(..., description="Response status")
    itinerary: Itinerary = Field(..., description="Generated itinerary")
    sources: List[Source] = Field(default_factory=list, description="Sources and citations")
    evaluation: Evaluation = Field(..., description="Evaluation results")
    explanation: Optional[str] = Field(None, description="Explanation of itinerary decisions")
    message: Optional[str] = Field(None, description="Additional message")


class EditResponse(BaseModel):
    """Response model for edit endpoint."""
    status: str = Field(..., description="Response status")
    edit_type: str = Field(..., description="Type of edit performed")
    modified_section: str = Field(..., description="Section that was modified")
    itinerary: Itinerary = Field(..., description="Updated itinerary")
    evaluation: Optional[Evaluation] = Field(None, description="Evaluation results")
    explanation: Optional[str] = Field(None, description="Explanation of changes")
    previous_travel_time: Optional[int] = Field(None, description="Previous total travel time")
    total_travel_time: Optional[int] = Field(None, description="New total travel time")


class ExplainResponse(BaseModel):
    """Response model for explain endpoint."""
    status: str = Field(..., description="Response status")
    explanation: str = Field(..., description="Explanation text")
    sources: List[Source] = Field(default_factory=list, description="Sources and citations")
    reasoning: Optional[Dict[str, Any]] = Field(None, description="Detailed reasoning")
    alternatives: Optional[List[Dict[str, Any]]] = Field(None, description="Alternative options if applicable")
    uncertainty: Optional[bool] = Field(None, description="Whether data is uncertain")


class PDFResponse(BaseModel):
    """Response model for PDF generation endpoint."""
    status: str = Field(..., description="Response status")
    message: str = Field(..., description="Response message")
    email_sent: bool = Field(..., description="Whether email was sent")
    pdf_url: Optional[HttpUrl] = Field(None, description="PDF download URL")
    email_address: Optional[str] = Field(None, description="Email address used")
    generated_at: Optional[str] = Field(None, description="Generation timestamp")


class ErrorResponse(BaseModel):
    """Response model for errors."""
    status: str = Field(default="error", description="Error status")
    error_type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    suggestions: Optional[List[str]] = Field(None, description="Suggestions to fix the error")
