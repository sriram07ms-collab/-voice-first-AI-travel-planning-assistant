"""
Grounding Evaluator
Verifies that all data is grounded in sources (POIs have source IDs, tips have citations).
"""

from typing import Dict, List, Optional, Any
import logging
import re

try:
    from ..models.itinerary_models import GroundingEvaluation
except ImportError:
    from src.models.itinerary_models import GroundingEvaluation

logger = logging.getLogger(__name__)


class GroundingEvaluator:
    """
    Evaluates grounding of itinerary data.
    Checks that all POIs have source IDs and all tips have citations.
    """
    
    def __init__(self):
        """Initialize grounding evaluator."""
        logger.info("GroundingEvaluator initialized")
    
    def evaluate_grounding(
        self,
        itinerary: Dict[str, Any],
        explanations: Optional[List[Dict[str, Any]]] = None,
        sources: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate grounding of itinerary and explanations.
        
        Args:
            itinerary: Itinerary dictionary
            explanations: List of explanation dictionaries
            sources: List of source dictionaries
        
        Returns:
            GroundingEvaluation dictionary
        """
        missing_citations = []
        uncertain_data = []
        
        # Check POI sources
        poi_sources_result = self.check_poi_sources(itinerary)
        all_pois_have_sources = poi_sources_result["all_have_sources"]
        missing_poi_sources = poi_sources_result["missing_sources"]
        
        if missing_poi_sources:
            missing_citations.extend(missing_poi_sources)
        
        # Check citations in explanations
        if explanations:
            explanation_citations = self.check_citations(explanations)
            missing_citations.extend(explanation_citations.get("missing", []))
        
        # Check sources list
        if sources:
            for source in sources:
                if source.get("type") == "wikivoyage" and not source.get("url"):
                    missing_citations.append(f"Wikivoyage source missing URL: {source.get('topic', 'unknown')}")
        
        # Identify missing data
        missing_data = self.identify_missing_data(itinerary)
        uncertain_data.extend(missing_data)
        
        # Calculate score
        total_pois = poi_sources_result.get("total_pois", 0)
        pois_with_sources = poi_sources_result.get("pois_with_sources", 0)
        
        score = 1.0
        if total_pois > 0:
            poi_score = pois_with_sources / total_pois
            score = poi_score
        
        # Penalize for missing citations
        if missing_citations:
            score -= len(missing_citations) * 0.1
        
        score = max(0.0, min(1.0, score))
        
        is_grounded = all_pois_have_sources and len(missing_citations) == 0
        
        return {
            "is_grounded": is_grounded,
            "score": round(score, 2),
            "missing_citations": missing_citations,
            "uncertain_data": uncertain_data,
            "all_pois_have_sources": all_pois_have_sources
        }
    
    def check_poi_sources(
        self,
        itinerary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if all POIs in itinerary have valid source IDs.
        
        Args:
            itinerary: Itinerary dictionary
        
        Returns:
            Dictionary with source check results
        """
        missing_sources = []
        total_pois = 0
        pois_with_sources = 0
        
        duration_days = itinerary.get("duration_days", 0)
        
        for day_num in range(1, duration_days + 1):
            day_key = f"day_{day_num}"
            day_data = itinerary.get(day_key)
            
            if not day_data:
                continue
            
            # Check all time blocks
            for time_block in ["morning", "afternoon", "evening"]:
                activities = day_data.get(time_block, {}).get("activities", [])
                
                for activity in activities:
                    total_pois += 1
                    source_id = activity.get("source_id")
                    activity_name = activity.get("activity", "Unknown")
                    
                    if source_id:
                        # Validate source_id format (should be like "way:123456" or "node:123456")
                        if self._is_valid_source_id(source_id):
                            pois_with_sources += 1
                        else:
                            missing_sources.append(
                                f"POI '{activity_name}' has invalid source_id format: {source_id}"
                            )
                    else:
                        missing_sources.append(
                            f"POI '{activity_name}' (Day {day_num}, {time_block}) missing source_id"
                        )
        
        all_have_sources = pois_with_sources == total_pois and total_pois > 0
        
        return {
            "all_have_sources": all_have_sources,
            "total_pois": total_pois,
            "pois_with_sources": pois_with_sources,
            "missing_sources": missing_sources
        }
    
    def check_citations(
        self,
        explanations: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check if explanations have proper citations.
        
        Args:
            explanations: List of explanation dictionaries
        
        Returns:
            Dictionary with missing citations
        """
        missing = []
        
        for explanation in explanations:
            sources = explanation.get("sources", [])
            
            # Check if explanation mentions facts but has no sources
            explanation_text = explanation.get("explanation", "")
            
            # Simple heuristic: if explanation is long and has no sources, might be missing citations
            if len(explanation_text) > 200 and len(sources) == 0:
                # Check if it mentions specific places or facts
                if any(keyword in explanation_text.lower() for keyword in ["famous", "popular", "known", "historic"]):
                    missing.append("Explanation mentions facts but has no citations")
            
            # Check if sources are valid
            for source in sources:
                if source.get("type") == "wikivoyage":
                    if not source.get("url"):
                        missing.append(f"Wikivoyage source missing URL: {source.get('topic', 'unknown')}")
        
        return {
            "missing": missing
        }
    
    def identify_missing_data(
        self,
        itinerary: Dict[str, Any]
    ) -> List[str]:
        """
        Identify missing or uncertain data in itinerary.
        
        Args:
            itinerary: Itinerary dictionary
        
        Returns:
            List of missing data descriptions
        """
        missing_data = []
        
        duration_days = itinerary.get("duration_days", 0)
        
        for day_num in range(1, duration_days + 1):
            day_key = f"day_{day_num}"
            day_data = itinerary.get(day_key)
            
            if not day_data:
                continue
            
            # Check all activities
            for time_block in ["morning", "afternoon", "evening"]:
                activities = day_data.get(time_block, {}).get("activities", [])
                
                for activity in activities:
                    activity_name = activity.get("activity", "Unknown")
                    
                    # Check for missing opening hours
                    if not activity.get("opening_hours"):
                        missing_data.append(
                            f"Opening hours not available for '{activity_name}'"
                        )
                    
                    # Check for missing description
                    if not activity.get("description"):
                        missing_data.append(
                            f"Description not available for '{activity_name}'"
                        )
                    
                    # Check for missing travel time
                    if activity.get("travel_time_from_previous") is None:
                        # This is okay for first activity, but should be noted
                        pass
        
        return missing_data
    
    def _is_valid_source_id(self, source_id: str) -> bool:
        """
        Validate source ID format.
        Should be like "way:123456" or "node:123456".
        
        Args:
            source_id: Source ID string
        
        Returns:
            True if valid format
        """
        if not source_id:
            return False
        
        # Check format: type:id (e.g., "way:123456", "node:789012")
        pattern = r'^(way|node|relation):\d+$'
        return bool(re.match(pattern, source_id))


# Global grounding evaluator instance
_grounding_evaluator: Optional[GroundingEvaluator] = None


def get_grounding_evaluator() -> GroundingEvaluator:
    """
    Get or create global grounding evaluator instance.
    
    Returns:
        GroundingEvaluator instance
    """
    global _grounding_evaluator
    if _grounding_evaluator is None:
        _grounding_evaluator = GroundingEvaluator()
    return _grounding_evaluator
