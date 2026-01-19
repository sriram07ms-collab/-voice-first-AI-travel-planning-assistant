"""
Feasibility Evaluator
Evaluates whether an itinerary is feasible based on time constraints, travel times, and pace.
"""

from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta

try:
    from ..models.itinerary_models import FeasibilityEvaluation
except ImportError:
    from src.models.itinerary_models import FeasibilityEvaluation

logger = logging.getLogger(__name__)


class FeasibilityEvaluator:
    """
    Evaluates itinerary feasibility.
    Checks daily duration, travel times, and pace consistency.
    """
    
    # Time window defaults (9 AM to 10 PM = 13 hours = 780 minutes)
    DEFAULT_START_TIME = "09:00"
    DEFAULT_END_TIME = "22:00"
    DEFAULT_AVAILABLE_MINUTES = 780  # 13 hours
    
    # Pace rules: activities per day
    PACE_RULES = {
        "relaxed": {"min": 2, "max": 3},
        "moderate": {"min": 3, "max": 4},
        "fast": {"min": 4, "max": 5}
    }
    
    # Travel time limits (in minutes)
    MAX_WALKING_TIME = 30
    MAX_TRANSPORT_TIME = 60
    
    def __init__(self):
        """Initialize feasibility evaluator."""
        logger.info("FeasibilityEvaluator initialized")
    
    def evaluate_feasibility(
        self,
        itinerary: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate overall feasibility of an itinerary.
        
        Args:
            itinerary: Itinerary dictionary
            constraints: Optional constraints (time windows, etc.)
        
        Returns:
            FeasibilityEvaluation dictionary
        """
        violations = []
        warnings = []
        score = 1.0
        
        duration_days = itinerary.get("duration_days", 0)
        pace = itinerary.get("pace", "moderate")
        
        # Check each day
        for day_num in range(1, duration_days + 1):
            day_key = f"day_{day_num}"
            day_data = itinerary.get(day_key)
            
            if not day_data:
                continue
            
            # Get time window for this day
            time_window = self._get_time_window(constraints, day_num)
            
            # Check daily duration
            daily_result = self.check_daily_duration(day_data, time_window)
            if not daily_result["is_feasible"]:
                violations.extend(daily_result["violations"])
                score -= 0.2
            if daily_result.get("warnings"):
                warnings.extend(daily_result["warnings"])
            
            # Check travel times for this day
            travel_result = self.check_travel_times_day(day_data)
            if travel_result.get("violations"):
                violations.extend(travel_result["violations"])
                score -= 0.15
            if travel_result.get("warnings"):
                warnings.extend(travel_result["warnings"])
            
            # Check pace consistency
            pace_result = self.check_pace_consistency_day(day_data, pace)
            if not pace_result["is_consistent"]:
                warnings.append(f"Day {day_num}: {pace_result['message']}")
                score -= 0.1
        
        # Overall pace consistency check
        overall_pace = self.check_pace_consistency(itinerary, pace)
        if not overall_pace["is_consistent"]:
            warnings.append(overall_pace["message"])
            score -= 0.1
        
        # Ensure score is between 0 and 1
        score = max(0.0, min(1.0, score))
        
        is_feasible = len(violations) == 0
        
        return {
            "is_feasible": is_feasible,
            "score": round(score, 2),
            "violations": violations,
            "warnings": warnings
        }
    
    def check_daily_duration(
        self,
        day_itinerary: Dict[str, Any],
        time_window: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if daily activities fit within time window.
        
        Args:
            day_itinerary: Day itinerary dictionary
            time_window: Time window dict with 'start' and 'end' (HH:MM format)
        
        Returns:
            Dictionary with is_feasible, violations, warnings
        """
        violations = []
        warnings = []
        
        # Calculate available time
        start_time = time_window.get("start", self.DEFAULT_START_TIME)
        end_time = time_window.get("end", self.DEFAULT_END_TIME)
        available_minutes = self._time_diff_minutes(start_time, end_time)
        
        # Calculate total time needed
        total_activity_time = 0
        total_travel_time = 0
        
        for time_block in ["morning", "afternoon", "evening"]:
            activities = day_itinerary.get(time_block, {}).get("activities", [])
            
            for activity in activities:
                duration = activity.get("duration_minutes", 0)
                travel_time = activity.get("travel_time_from_previous", 0)
                
                total_activity_time += duration
                total_travel_time += travel_time
        
        total_time_needed = total_activity_time + total_travel_time
        
        # Check if it fits
        if total_time_needed > available_minutes:
            violations.append(
                f"Total time needed ({total_time_needed} min) exceeds available time ({available_minutes} min)"
            )
            return {
                "is_feasible": False,
                "violations": violations,
                "warnings": warnings
            }
        
        # Check if too tight (within 30 minutes of limit)
        if total_time_needed > available_minutes * 0.95:
            warnings.append(
                f"Schedule is very tight ({total_time_needed}/{available_minutes} minutes used)"
            )
        
        return {
            "is_feasible": True,
            "violations": violations,
            "warnings": warnings,
            "total_time_needed": total_time_needed,
            "available_minutes": available_minutes
        }
    
    def check_travel_times(
        self,
        itinerary: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check travel times between activities across all days.
        
        Args:
            itinerary: Itinerary dictionary
        
        Returns:
            List of violations/warnings for travel times
        """
        all_issues = []
        duration_days = itinerary.get("duration_days", 0)
        
        for day_num in range(1, duration_days + 1):
            day_key = f"day_{day_num}"
            day_data = itinerary.get(day_key)
            
            if not day_data:
                continue
            
            day_issues = self.check_travel_times_day(day_data)
            for issue in day_issues.get("violations", []):
                all_issues.append({"day": day_num, "type": "violation", "message": issue})
            for issue in day_issues.get("warnings", []):
                all_issues.append({"day": day_num, "type": "warning", "message": issue})
        
        return all_issues
    
    def check_travel_times_day(
        self,
        day_itinerary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check travel times for a single day.
        
        Args:
            day_itinerary: Day itinerary dictionary
        
        Returns:
            Dictionary with violations and warnings
        """
        violations = []
        warnings = []
        
        # Collect all activities in order
        all_activities = []
        for time_block in ["morning", "afternoon", "evening"]:
            activities = day_itinerary.get(time_block, {}).get("activities", [])
            all_activities.extend(activities)
        
        # Check travel times between consecutive activities
        for i in range(1, len(all_activities)):
            prev_activity = all_activities[i - 1]
            curr_activity = all_activities[i]
            
            travel_time = curr_activity.get("travel_time_from_previous", 0)
            
            if travel_time > self.MAX_TRANSPORT_TIME:
                violations.append(
                    f"Travel time between '{prev_activity.get('activity', 'previous')}' and "
                    f"'{curr_activity.get('activity', 'next')}' is {travel_time} minutes "
                    f"(exceeds {self.MAX_TRANSPORT_TIME} min limit)"
                )
            elif travel_time > self.MAX_WALKING_TIME:
                warnings.append(
                    f"Travel time between '{prev_activity.get('activity', 'previous')}' and "
                    f"'{curr_activity.get('activity', 'next')}' is {travel_time} minutes "
                    f"(may require transport)"
                )
        
        return {
            "violations": violations,
            "warnings": warnings
        }
    
    def check_pace_consistency(
        self,
        itinerary: Dict[str, Any],
        pace: str
    ) -> Dict[str, Any]:
        """
        Check if activities per day match the pace preference.
        
        Args:
            itinerary: Itinerary dictionary
            pace: Pace preference ("relaxed", "moderate", "fast")
        
        Returns:
            Dictionary with is_consistent and message
        """
        if pace not in self.PACE_RULES:
            return {
                "is_consistent": True,
                "message": f"Unknown pace '{pace}', skipping consistency check"
            }
        
        rules = self.PACE_RULES[pace]
        min_activities = rules["min"]
        max_activities = rules["max"]
        
        duration_days = itinerary.get("duration_days", 0)
        inconsistent_days = []
        
        for day_num in range(1, duration_days + 1):
            day_key = f"day_{day_num}"
            day_data = itinerary.get(day_key)
            
            if not day_data:
                continue
            
            # Count activities
            total_activities = 0
            for time_block in ["morning", "afternoon", "evening"]:
                activities = day_data.get(time_block, {}).get("activities", [])
                total_activities += len(activities)
            
            if total_activities < min_activities or total_activities > max_activities:
                inconsistent_days.append(day_num)
        
        if inconsistent_days:
            return {
                "is_consistent": False,
                "message": f"Days {inconsistent_days} don't match {pace} pace ({min_activities}-{max_activities} activities/day)"
            }
        
        return {
            "is_consistent": True,
            "message": f"All days match {pace} pace ({min_activities}-{max_activities} activities/day)"
        }
    
    def check_pace_consistency_day(
        self,
        day_itinerary: Dict[str, Any],
        pace: str
    ) -> Dict[str, Any]:
        """Check pace consistency for a single day."""
        if pace not in self.PACE_RULES:
            return {"is_consistent": True, "message": ""}
        
        rules = self.PACE_RULES[pace]
        min_activities = rules["min"]
        max_activities = rules["max"]
        
        # Count activities
        total_activities = 0
        for time_block in ["morning", "afternoon", "evening"]:
            activities = day_itinerary.get(time_block, {}).get("activities", [])
            total_activities += len(activities)
        
        if total_activities < min_activities or total_activities > max_activities:
            return {
                "is_consistent": False,
                "message": f"{total_activities} activities doesn't match {pace} pace ({min_activities}-{max_activities} expected)"
            }
        
        return {
            "is_consistent": True,
            "message": ""
        }
    
    def _get_time_window(
        self,
        constraints: Optional[Dict[str, Any]],
        day_num: int
    ) -> Dict[str, str]:
        """Get time window for a day."""
        if constraints and "daily_time_windows" in constraints:
            for tw in constraints["daily_time_windows"]:
                if tw.get("day") == day_num:
                    return {
                        "start": tw.get("start", self.DEFAULT_START_TIME),
                        "end": tw.get("end", self.DEFAULT_END_TIME)
                    }
        
        return {
            "start": self.DEFAULT_START_TIME,
            "end": self.DEFAULT_END_TIME
        }
    
    def _time_diff_minutes(self, start_time: str, end_time: str) -> int:
        """
        Calculate difference between two times in minutes.
        
        Args:
            start_time: Start time in HH:MM format
            end_time: End time in HH:MM format
        
        Returns:
            Difference in minutes
        """
        try:
            start = datetime.strptime(start_time, "%H:%M")
            end = datetime.strptime(end_time, "%H:%M")
            
            if end < start:
                # Assume next day
                end += timedelta(days=1)
            
            diff = end - start
            return int(diff.total_seconds() / 60)
        
        except ValueError:
            logger.warning(f"Invalid time format: {start_time} or {end_time}")
            return self.DEFAULT_AVAILABLE_MINUTES


# Global feasibility evaluator instance
_feasibility_evaluator: Optional[FeasibilityEvaluator] = None


def get_feasibility_evaluator() -> FeasibilityEvaluator:
    """
    Get or create global feasibility evaluator instance.
    
    Returns:
        FeasibilityEvaluator instance
    """
    global _feasibility_evaluator
    if _feasibility_evaluator is None:
        _feasibility_evaluator = FeasibilityEvaluator()
    return _feasibility_evaluator
