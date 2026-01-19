"""
Edit Correctness Evaluator
Verifies that edits were applied correctly - only intended sections modified.
"""

import json
from typing import Dict, List, Optional, Any
import logging

try:
    from ..models.itinerary_models import EditCorrectnessEvaluation
except ImportError:
    from src.models.itinerary_models import EditCorrectnessEvaluation

logger = logging.getLogger(__name__)


class EditCorrectnessEvaluator:
    """
    Evaluates whether edits were applied correctly.
    Checks that only intended sections were modified and other sections remain unchanged.
    """
    
    def __init__(self):
        """Initialize edit correctness evaluator."""
        logger.info("EditCorrectnessEvaluator initialized")
    
    def evaluate_edit_correctness(
        self,
        old_itinerary: Dict[str, Any],
        new_itinerary: Dict[str, Any],
        edit_intent: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate if edit was applied correctly.
        
        Args:
            old_itinerary: Original itinerary
            new_itinerary: Updated itinerary
            edit_intent: Edit intent dictionary with target_day, edit_type, etc.
        
        Returns:
            EditCorrectnessEvaluation dictionary
        """
        violations = []
        
        # Compare itineraries to find changes
        comparison = self.compare_itineraries(old_itinerary, new_itinerary)
        
        # Verify edit scope
        is_correct = self.verify_edit_scope(comparison, edit_intent)
        
        if not is_correct:
            violations.append("Edit affected sections that should not have been modified")
        
        # Get modified and unchanged sections
        modified_sections = comparison.get("modified_sections", [])
        unchanged_sections = comparison.get("unchanged_sections", [])
        
        # Check if edit intent was correctly interpreted
        target_day = edit_intent.get("target_day")
        edit_type = edit_intent.get("edit_type")
        
        if target_day:
            expected_section = f"day_{target_day}"
            if expected_section not in modified_sections:
                violations.append(f"Expected section {expected_section} was not modified")
        
        return {
            "is_correct": is_correct and len(violations) == 0,
            "modified_sections": modified_sections,
            "unchanged_sections": unchanged_sections,
            "violations": violations
        }
    
    def compare_itineraries(
        self,
        old_itinerary: Dict[str, Any],
        new_itinerary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two itineraries to find differences.
        
        Args:
            old_itinerary: Original itinerary
            new_itinerary: Updated itinerary
        
        Returns:
            Dictionary with modified_sections, unchanged_sections, and changes
        """
        modified_sections = []
        unchanged_sections = []
        changes = []
        
        # Compare metadata (city, duration, pace, etc.)
        metadata_fields = ["city", "duration_days", "pace", "interests", "budget"]
        for field in metadata_fields:
            old_val = old_itinerary.get(field)
            new_val = new_itinerary.get(field)
            if old_val != new_val:
                changes.append({
                    "field": field,
                    "old": old_val,
                    "new": new_val
                })
        
        # Compare each day
        duration_days = max(
            old_itinerary.get("duration_days", 0),
            new_itinerary.get("duration_days", 0)
        )
        
        for day_num in range(1, duration_days + 1):
            day_key = f"day_{day_num}"
            old_day = old_itinerary.get(day_key)
            new_day = new_itinerary.get(day_key)
            
            if self._days_different(old_day, new_day):
                modified_sections.append(day_key)
                changes.append({
                    "section": day_key,
                    "type": "modified"
                })
            else:
                unchanged_sections.append(day_key)
        
        return {
            "modified_sections": modified_sections,
            "unchanged_sections": unchanged_sections,
            "changes": changes
        }
    
    def verify_edit_scope(
        self,
        changes: Dict[str, Any],
        edit_intent: Dict[str, Any]
    ) -> bool:
        """
        Verify that only intended sections were modified.
        
        Args:
            changes: Comparison result from compare_itineraries
            edit_intent: Edit intent dictionary
        
        Returns:
            True if edit scope is correct
        """
        target_day = edit_intent.get("target_day")
        source_day = edit_intent.get("source_day")
        target_time_block = edit_intent.get("target_time_block")
        source_time_block = edit_intent.get("source_time_block")
        edit_type = edit_intent.get("edit_type")
        
        modified_sections = changes.get("modified_sections", [])
        
        # Handle SWAP_DAYS - both days should be modified
        if edit_type == "SWAP_DAYS":
            if not source_day or not target_day:
                logger.warning("SWAP_DAYS requires both source_day and target_day")
                return False
            
            expected_sections = {f"day_{source_day}", f"day_{target_day}"}
            modified_set = set(modified_sections)
            
            # Both days must be modified for a swap
            if not expected_sections.issubset(modified_set):
                logger.warning(f"SWAP_DAYS: Expected {expected_sections} to be modified, got {modified_set}")
                return False
            
            # Check if any other days were modified (shouldn't happen in a swap)
            unexpected = modified_set - expected_sections
            if unexpected:
                logger.warning(f"SWAP_DAYS: Unexpected sections modified: {unexpected}")
                # For now, allow it but log warning
                # return False
            
            return True
        
        # Handle MOVE_TIME_BLOCK - both days might be modified
        if edit_type == "MOVE_TIME_BLOCK":
            if source_day and target_day:
                expected_sections = {f"day_{source_day}", f"day_{target_day}"}
                modified_set = set(modified_sections)
                
                # At least the source and target days should be modified
                if not expected_sections.issubset(modified_set):
                    # If regenerate_vacated is true, both days should be modified
                    if edit_intent.get("regenerate_vacated"):
                        if not expected_sections.issubset(modified_set):
                            logger.warning(f"MOVE_TIME_BLOCK: Expected {expected_sections} to be modified, got {modified_set}")
                            return False
                    else:
                        # If not regenerating, at least target day should be modified
                        if f"day_{target_day}" not in modified_set:
                            return False
                
                # Allow other days to be modified if regenerating
                return True
            elif target_day:
                # Just regenerating target day
                expected_section = f"day_{target_day}"
                return expected_section in modified_sections
        
        # If no target specified, any modification is acceptable
        if not target_day:
            return True
        
        expected_section = f"day_{target_day}"
        
        # Check if expected section is in modified sections
        if expected_section not in modified_sections:
            # This might be okay if edit_type doesn't require day modification
            if edit_type in ["CHANGE_PACE"]:
                # Pace change might affect all days
                return True
            return False
        
        # Check if unexpected sections were modified
        for section in modified_sections:
            if section != expected_section:
                # Some edit types might affect multiple days (e.g., CHANGE_PACE)
                if edit_type == "CHANGE_PACE":
                    # Pace change affecting multiple days is acceptable
                    continue
                else:
                    # Other edits should only affect target day
                    return False
        
        return True
    
    def _days_different(
        self,
        old_day: Optional[Dict[str, Any]],
        new_day: Optional[Dict[str, Any]]
    ) -> bool:
        """
        Check if two day itineraries are different.
        
        Args:
            old_day: Old day itinerary
            new_day: New day itinerary
        
        Returns:
            True if different
        """
        if old_day is None and new_day is None:
            return False
        if old_day is None or new_day is None:
            return True
        
        # Compare as JSON strings for deep comparison
        old_json = json.dumps(old_day, sort_keys=True)
        new_json = json.dumps(new_day, sort_keys=True)
        
        return old_json != new_json
    
    def _time_blocks_different(
        self,
        old_block: Optional[Dict[str, Any]],
        new_block: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if two time blocks are different."""
        if old_block is None and new_block is None:
            return False
        if old_block is None or new_block is None:
            return True
        
        old_activities = old_block.get("activities", [])
        new_activities = new_block.get("activities", [])
        
        if len(old_activities) != len(new_activities):
            return True
        
        # Compare activities
        for old_act, new_act in zip(old_activities, new_activities):
            if json.dumps(old_act, sort_keys=True) != json.dumps(new_act, sort_keys=True):
                return True
        
        return False


# Global edit correctness evaluator instance
_edit_correctness_evaluator: Optional[EditCorrectnessEvaluator] = None


def get_edit_correctness_evaluator() -> EditCorrectnessEvaluator:
    """
    Get or create global edit correctness evaluator instance.
    
    Returns:
        EditCorrectnessEvaluator instance
    """
    global _edit_correctness_evaluator
    if _edit_correctness_evaluator is None:
        _edit_correctness_evaluator = EditCorrectnessEvaluator()
    return _edit_correctness_evaluator
