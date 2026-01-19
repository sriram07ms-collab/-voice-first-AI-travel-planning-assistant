"""
Unit tests for Grounding Evaluator.
Tests grounding evaluation logic.
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
from src.evaluation.grounding_eval import get_grounding_evaluator


class TestGroundingEvaluator:
    """Test cases for Grounding Evaluator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.evaluator = get_grounding_evaluator()
    
    def test_well_grounded_itinerary(self):
        """Test itinerary with all POIs having source IDs."""
        itinerary = {
            "city": "Jaipur",
            "duration_days": 1,
            "day_1": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Hawa Mahal",
                            "time": "09:00 - 10:30",
                            "duration_minutes": 90,
                            "source_id": "way:123456"
                        }
                    ]
                },
                "afternoon": {
                    "activities": [
                        {
                            "activity": "City Palace",
                            "time": "14:00 - 16:00",
                            "duration_minutes": 120,
                            "source_id": "way:789012"
                        }
                    ]
                },
                "evening": {
                    "activities": []
                }
            }
        }
        
        sources = [
            {
                "type": "openstreetmap",
                "poi": "Hawa Mahal",
                "source_id": "way:123456",
                "url": "https://www.openstreetmap.org/way/123456"
            },
            {
                "type": "openstreetmap",
                "poi": "City Palace",
                "source_id": "way:789012",
                "url": "https://www.openstreetmap.org/way/789012"
            }
        ]
        
        result = self.evaluator.evaluate_grounding(itinerary, sources=sources)
        
        assert result["is_grounded"] == True
        assert result["score"] >= 0.9
        assert result["all_pois_have_sources"] == True
        assert len(result["missing_citations"]) == 0
    
    def test_missing_source_ids(self):
        """Test itinerary with missing source IDs."""
        itinerary = {
            "city": "Jaipur",
            "duration_days": 1,
            "day_1": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Hawa Mahal",
                            "time": "09:00 - 10:30",
                            "duration_minutes": 90
                            # Missing source_id
                        }
                    ]
                },
                "afternoon": {
                    "activities": []
                },
                "evening": {
                    "activities": []
                }
            }
        }
        
        result = self.evaluator.evaluate_grounding(itinerary)
        
        assert result["is_grounded"] == False
        assert result["all_pois_have_sources"] == False
        assert len(result["missing_citations"]) > 0
    
    def test_sources_with_urls(self):
        """Test sources with URLs are properly detected."""
        itinerary = {
            "city": "Jaipur",
            "duration_days": 1,
            "day_1": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Hawa Mahal",
                            "time": "09:00 - 10:30",
                            "duration_minutes": 90,
                            "source_id": "way:123456"
                        }
                    ]
                },
                "afternoon": {
                    "activities": []
                },
                "evening": {
                    "activities": []
                }
            }
        }
        
        sources = [
            {
                "type": "wikivoyage",
                "topic": "Jaipur travel tips",
                "url": "https://en.wikivoyage.org/wiki/Jaipur"
            }
        ]
        
        result = self.evaluator.evaluate_grounding(itinerary, sources=sources)
        
        # Should detect Wikivoyage source
        assert result["is_grounded"] == True or len(result["uncertain_data"]) == 0
    
    def test_explanation_grounding(self):
        """Test grounding of explanations."""
        itinerary = {
            "city": "Jaipur",
            "duration_days": 1,
            "day_1": {
                "morning": {
                    "activities": [
                        {
                            "activity": "Hawa Mahal",
                            "time": "09:00 - 10:30",
                            "duration_minutes": 90,
                            "source_id": "way:123456"
                        }
                    ]
                },
                "afternoon": {
                    "activities": []
                },
                "evening": {
                    "activities": []
                }
            }
        }
        
        explanations = [
            {
                "text": "Hawa Mahal is a famous palace in Jaipur.",
                "sources": [
                    {
                        "type": "openstreetmap",
                        "source_id": "way:123456"
                    }
                ]
            }
        ]
        
        sources = [
            {
                "type": "openstreetmap",
                "poi": "Hawa Mahal",
                "source_id": "way:123456"
            }
        ]
        
        result = self.evaluator.evaluate_grounding(
            itinerary,
            explanations=explanations,
            sources=sources
        )
        
        assert result["is_grounded"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
