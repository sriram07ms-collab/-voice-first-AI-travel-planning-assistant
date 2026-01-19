"""
Unit tests for Feasibility Evaluator.
Tests feasibility evaluation logic.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Set dummy API key for testing
if not os.getenv('GROK_API_KEY'):
    os.environ['GROK_API_KEY'] = 'test_key_for_testing_only'

import pytest
from src.evaluation.feasibility_eval import get_feasibility_evaluator


class TestFeasibilityEvaluator:
    """Test cases for Feasibility Evaluator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = get_feasibility_evaluator()
    
    def test_feasible_itinerary(self):
        """Test a feasible itinerary."""
        itinerary = {
            "city": "Jaipur",
            "duration_days": 1,
            "pace": "moderate",
            "day_1": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Hawa Mahal",
                            "time": "09:00 - 10:30",
                            "duration_minutes": 90,
                            "travel_time_from_previous": 0
                        }
                    ]
                },
                "afternoon": {
                    "activities": [
                        {
                            "activity": "City Palace",
                            "time": "14:00 - 16:00",
                            "duration_minutes": 120,
                            "travel_time_from_previous": 15
                        }
                    ]
                },
                "evening": {
                    "activities": []
                }
            }
        }
        
        result = self.evaluator.evaluate_feasibility(itinerary)
        
        assert result["is_feasible"] == True
        assert result["score"] >= 0.8
        assert len(result["violations"]) == 0
    
    def test_infeasible_daily_duration(self):
        """Test itinerary that exceeds daily time limit."""
        itinerary = {
            "city": "Jaipur",
            "duration_days": 1,
            "pace": "fast",
            "day_1": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Activity 1",
                            "time": "09:00 - 12:00",
                            "duration_minutes": 180,
                            "travel_time_from_previous": 0
                        },
                        {
                            "activity": "Activity 2",
                            "time": "12:30 - 15:30",
                            "duration_minutes": 180,
                            "travel_time_from_previous": 30
                        }
                    ]
                },
                "afternoon": {
                    "activities": [
                        {
                            "activity": "Activity 3",
                            "time": "16:00 - 19:00",
                            "duration_minutes": 180,
                            "travel_time_from_previous": 30
                        },
                        {
                            "activity": "Activity 4",
                            "time": "19:30 - 22:30",
                            "duration_minutes": 180,
                            "travel_time_from_previous": 30
                        }
                    ]
                },
                "evening": {
                    "activities": []
                }
            }
        }
        
        result = self.evaluator.evaluate_feasibility(itinerary)
        
        # Should detect that total time exceeds available time
        assert result["is_feasible"] == False or len(result["violations"]) > 0
    
    def test_pace_consistency(self):
        """Test pace consistency evaluation."""
        # Relaxed pace - should have 2-3 activities
        relaxed_itinerary = {
            "city": "Jaipur",
            "duration_days": 1,
            "pace": "relaxed",
            "day_1": {
                "morning": {
                    "activities": [
                        {"activity": "Activity 1", "time": "09:00", "duration_minutes": 120, "travel_time_from_previous": 0}
                    ]
                },
                "afternoon": {
                    "activities": [
                        {"activity": "Activity 2", "time": "14:00", "duration_minutes": 120, "travel_time_from_previous": 15}
                    ]
                },
                "evening": {
                    "activities": []
                }
            }
        }
        
        result = self.evaluator.evaluate_feasibility(relaxed_itinerary)
        # Relaxed pace with 2 activities should be feasible
        assert result["is_feasible"] == True
        
        # Fast pace - should have 4-5 activities
        fast_itinerary = {
            "city": "Jaipur",
            "duration_days": 1,
            "pace": "fast",
            "day_1": {
                "morning": {
                    "activities": [
                        {"activity": "Activity 1", "time": "09:00", "duration_minutes": 60, "travel_time_from_previous": 0},
                        {"activity": "Activity 2", "time": "10:30", "duration_minutes": 60, "travel_time_from_previous": 30}
                    ]
                },
                "afternoon": {
                    "activities": [
                        {"activity": "Activity 3", "time": "13:00", "duration_minutes": 60, "travel_time_from_previous": 30},
                        {"activity": "Activity 4", "time": "14:30", "duration_minutes": 60, "travel_time_from_previous": 30}
                    ]
                },
                "evening": {
                    "activities": []
                }
            }
        }
        
        result = self.evaluator.evaluate_feasibility(fast_itinerary)
        # Fast pace with 4 activities should be feasible
        assert result["is_feasible"] == True
    
    def test_travel_time_limits(self):
        """Test travel time limit checks."""
        itinerary = {
            "city": "Jaipur",
            "duration_days": 1,
            "pace": "moderate",
            "day_1": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Activity 1",
                            "time": "09:00 - 10:00",
                            "duration_minutes": 60,
                            "travel_time_from_previous": 0
                        }
                    ]
                },
                "afternoon": {
                    "activities": [
                        {
                            "activity": "Activity 2",
                            "time": "11:00 - 12:00",
                            "duration_minutes": 60,
                            "travel_time_from_previous": 90  # Exceeds walking limit
                        }
                    ]
                },
                "evening": {
                    "activities": []
                }
            }
        }
        
        result = self.evaluator.evaluate_feasibility(itinerary)
        
        # Should flag excessive travel time
        assert len(result["warnings"]) > 0 or len(result["violations"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
