"""
Unit tests for Edit Correctness Evaluator.
Tests edit correctness evaluation logic.
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
from src.evaluation.edit_correctness_eval import get_edit_correctness_evaluator


class TestEditCorrectnessEvaluator:
    """Test cases for Edit Correctness Evaluator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = get_edit_correctness_evaluator()
    
    def test_correct_edit_single_day(self):
        """Test edit that correctly modifies only one day."""
        old_itinerary = {
            "city": "Jaipur",
            "duration_days": 2,
            "day_1": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Hawa Mahal",
                            "time": "09:00 - 10:30",
                            "duration_minutes": 90
                        }
                    ]
                },
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            },
            "day_2": {
                "morning": {
                    "activities": [
                        {
                            "activity": "City Palace",
                            "time": "09:00 - 11:00",
                            "duration_minutes": 120
                        }
                    ]
                },
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            }
        }
        
        new_itinerary = {
            "city": "Jaipur",
            "duration_days": 2,
            "day_1": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Hawa Mahal",
                            "time": "09:00 - 10:30",
                            "duration_minutes": 90
                        }
                    ]
                },
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            },
            "day_2": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Amber Fort",  # Changed
                            "time": "09:00 - 11:00",
                            "duration_minutes": 120
                        }
                    ]
                },
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            }
        }
        
        edit_intent = {
            "edit_type": "CHANGE_ACTIVITY",
            "target_day": 2,
            "target_section": "morning"
        }
        
        result = self.evaluator.evaluate_edit_correctness(
            old_itinerary,
            new_itinerary,
            edit_intent
        )
        
        assert result["is_correct"] == True
        assert "day_2" in result["modified_sections"]
        assert "day_1" in result["unchanged_sections"]
        assert len(result["violations"]) == 0
    
    def test_incorrect_edit_multiple_days(self):
        """Test edit that incorrectly modifies multiple days."""
        old_itinerary = {
            "city": "Jaipur",
            "duration_days": 2,
            "day_1": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Hawa Mahal",
                            "time": "09:00 - 10:30",
                            "duration_minutes": 90
                        }
                    ]
                },
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            },
            "day_2": {
                "morning": {
                    "activities": [
                        {
                            "activity": "City Palace",
                            "time": "09:00 - 11:00",
                            "duration_minutes": 120
                        }
                    ]
                },
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            }
        }
        
        new_itinerary = {
            "city": "Jaipur",
            "duration_days": 2,
            "day_1": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Changed Activity",  # Should not be changed
                            "time": "09:00 - 10:30",
                            "duration_minutes": 90
                        }
                    ]
                },
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            },
            "day_2": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Amber Fort",  # Intended change
                            "time": "09:00 - 11:00",
                            "duration_minutes": 120
                        }
                    ]
                },
                "afternoon": {"activities": []},
                "evening": {"activities": []}
            }
        }
        
        edit_intent = {
            "edit_type": "CHANGE_ACTIVITY",
            "target_day": 2,
            "target_section": "morning"
        }
        
        result = self.evaluator.evaluate_edit_correctness(
            old_itinerary,
            new_itinerary,
            edit_intent
        )
        
        # Should detect that day_1 was incorrectly modified
        assert result["is_correct"] == False or len(result["violations"]) > 0
    
    def test_pace_change_edit(self):
        """Test pace change edit."""
        old_itinerary = {
            "city": "Jaipur",
            "duration_days": 1,
            "pace": "fast",
            "day_1": {
                "morning": {
                    "activities": [
                        {"activity": "Activity 1", "time": "09:00", "duration_minutes": 60},
                        {"activity": "Activity 2", "time": "10:30", "duration_minutes": 60}
                    ]
                },
                "afternoon": {
                    "activities": [
                        {"activity": "Activity 3", "time": "13:00", "duration_minutes": 60},
                        {"activity": "Activity 4", "time": "14:30", "duration_minutes": 60}
                    ]
                },
                "evening": {"activities": []}
            }
        }
        
        new_itinerary = {
            "city": "Jaipur",
            "duration_days": 1,
            "pace": "relaxed",  # Changed
            "day_1": {
                "morning": {
                    "activities": [
                        {"activity": "Activity 1", "time": "09:00", "duration_minutes": 120}  # Longer duration
                    ]
                },
                "afternoon": {
                    "activities": [
                        {"activity": "Activity 2", "time": "14:00", "duration_minutes": 120}
                    ]
                },
                "evening": {"activities": []}
            }
        }
        
        edit_intent = {
            "edit_type": "CHANGE_PACE",
            "target_day": 1,
            "new_pace": "relaxed"
        }
        
        result = self.evaluator.evaluate_edit_correctness(
            old_itinerary,
            new_itinerary,
            edit_intent
        )
        
        assert result["is_correct"] == True
        assert "day_1" in result["modified_sections"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
