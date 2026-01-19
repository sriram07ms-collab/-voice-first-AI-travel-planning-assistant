"""
Pydantic models for itinerary data structures.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, HttpUrl
from datetime import time


class Location(BaseModel):
    """Geographic location coordinates."""
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")


class POI(BaseModel):
    """Point of Interest model."""
    name: str = Field(..., description="Name of the POI")
    category: str = Field(..., description="Category (e.g., 'historical', 'restaurant')")
    location: Location = Field(..., description="Geographic coordinates")
    duration_minutes: int = Field(..., ge=0, description="Estimated visit duration in minutes")
    data_source: str = Field(default="openstreetmap", description="Data source")
    source_id: str = Field(..., description="Source ID from data provider (e.g., 'way:123456')")
    rating: Optional[float] = Field(None, ge=0, le=5, description="Rating if available")
    description: Optional[str] = Field(None, description="Description of the POI")
    opening_hours: Optional[str] = Field(None, description="Opening hours if available")
    travel_time_from_previous: Optional[int] = Field(None, ge=0, description="Travel time from previous activity in minutes")


class Activity(BaseModel):
    """Individual activity in itinerary."""
    activity: str = Field(..., description="Activity name")
    time: str = Field(..., description="Time slot (e.g., '09:00 - 10:30')")
    duration_minutes: int = Field(..., ge=0, description="Duration in minutes")
    travel_time_from_previous: Optional[int] = Field(None, ge=0, description="Travel time from previous activity")
    location: Optional[Location] = Field(None, description="Location coordinates")
    category: Optional[str] = Field(None, description="Activity category")
    source_id: Optional[str] = Field(None, description="Source ID")
    description: Optional[str] = Field(None, description="Activity description")
    indoor: Optional[bool] = Field(None, description="Whether activity is indoors")
    note: Optional[str] = Field(None, description="Additional notes")
    opening_hours: Optional[str] = Field(None, description="Opening hours if available")


class TimeBlock(BaseModel):
    """Time block (morning/afternoon/evening) with activities."""
    activities: List[Activity] = Field(default_factory=list, description="Activities in this time block")


class DayItinerary(BaseModel):
    """Itinerary for a single day."""
    morning: TimeBlock = Field(default_factory=lambda: TimeBlock(), description="Morning activities")
    afternoon: TimeBlock = Field(default_factory=lambda: TimeBlock(), description="Afternoon activities")
    evening: TimeBlock = Field(default_factory=lambda: TimeBlock(), description="Evening activities")


class Source(BaseModel):
    """Source/citation for information."""
    type: str = Field(..., description="Source type (e.g., 'openstreetmap', 'wikivoyage')")
    poi: Optional[str] = Field(None, description="POI name if applicable")
    topic: Optional[str] = Field(None, description="Topic if applicable")
    source_id: Optional[str] = Field(None, description="Source ID")
    url: Optional[HttpUrl] = Field(None, description="Source URL")
    section: Optional[str] = Field(None, description="Section name")
    snippet: Optional[str] = Field(None, description="Relevant snippet")


class FeasibilityEvaluation(BaseModel):
    """Feasibility evaluation results."""
    is_feasible: bool = Field(..., description="Whether itinerary is feasible")
    score: float = Field(..., ge=0, le=1, description="Feasibility score (0-1)")
    violations: List[str] = Field(default_factory=list, description="List of violations")
    warnings: List[str] = Field(default_factory=list, description="List of warnings")


class GroundingEvaluation(BaseModel):
    """Grounding evaluation results."""
    is_grounded: bool = Field(..., description="Whether all data is grounded")
    score: float = Field(..., ge=0, le=1, description="Grounding score (0-1)")
    missing_citations: List[str] = Field(default_factory=list, description="Missing citations")
    uncertain_data: List[str] = Field(default_factory=list, description="Uncertain or missing data")
    all_pois_have_sources: bool = Field(..., description="Whether all POIs have source IDs")


class EditCorrectnessEvaluation(BaseModel):
    """Edit correctness evaluation results."""
    is_correct: bool = Field(..., description="Whether edit was correct")
    modified_sections: List[str] = Field(default_factory=list, description="Sections that were modified")
    unchanged_sections: List[str] = Field(default_factory=list, description="Sections that should remain unchanged")
    violations: List[str] = Field(default_factory=list, description="List of violations")


class Evaluation(BaseModel):
    """Complete evaluation results."""
    feasibility: Optional[FeasibilityEvaluation] = Field(None, description="Feasibility evaluation")
    grounding: Optional[GroundingEvaluation] = Field(None, description="Grounding evaluation")
    edit_correctness: Optional[EditCorrectnessEvaluation] = Field(None, description="Edit correctness evaluation")


class Itinerary(BaseModel):
    """Complete itinerary model."""
    city: str = Field(..., description="City name")
    duration_days: int = Field(..., ge=1, le=30, description="Number of days")
    pace: Optional[str] = Field(None, description="Pace preference (relaxed/moderate/fast)")
    interests: Optional[List[str]] = Field(default_factory=list, description="User interests")
    budget: Optional[str] = Field(None, description="Budget preference")
    travel_dates: Optional[List[str]] = Field(None, description="List of travel dates in YYYY-MM-DD format")
    travel_mode: Optional[str] = Field(None, description="Travel mode: road, airplane, or railway")
    starting_point: Optional[str] = Field(None, description="Starting point based on travel mode")
    day_1: Optional[DayItinerary] = Field(None, description="Day 1 itinerary")
    day_2: Optional[DayItinerary] = Field(None, description="Day 2 itinerary")
    day_3: Optional[DayItinerary] = Field(None, description="Day 3 itinerary")
    # Support up to 30 days
    total_travel_time: Optional[int] = Field(None, ge=0, description="Total travel time in minutes")
    
    def get_day(self, day_number: int) -> Optional[DayItinerary]:
        """Get itinerary for a specific day."""
        return getattr(self, f"day_{day_number}", None)
    
    def set_day(self, day_number: int, day_itinerary: DayItinerary):
        """Set itinerary for a specific day."""
        setattr(self, f"day_{day_number}", day_itinerary)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return self.model_dump(exclude_none=True)
