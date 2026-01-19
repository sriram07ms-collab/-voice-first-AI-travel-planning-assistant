"""
Itinerary Builder MCP Tool Server
Implements the build_itinerary MCP tool for creating day-wise itineraries from POIs.
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from src.utils.grok_client import get_grok_client
    from src.data_sources.travel_time import calculate_travel_time
    from src.models.itinerary_models import (
        Activity, Location, DayItinerary, TimeBlock
    )
except ImportError:
    sys.path.insert(0, str(backend_dir / "src"))
    from utils.grok_client import get_grok_client
    from data_sources.travel_time import calculate_travel_time
    from models.itinerary_models import (
        Activity, Location, DayItinerary, TimeBlock
    )

logger = logging.getLogger(__name__)


def _estimate_duration_from_category(category: str, rating: Optional[float] = None, user_rating_count: Optional[int] = None) -> int:
    """
    Estimate duration in minutes based on category (same logic as Google Places).
    Uses rating and user count to refine estimates.
    
    Args:
        category: POI category
        rating: Optional rating (0-5) from Google Places
        user_rating_count: Optional number of user ratings
    
    Returns:
        Estimated duration in minutes
    """
    # Base duration by category
    base_duration_map = {
        "restaurant": 60,
        "museum": 120,
        "attraction": 90,
        "shopping": 60,
        "park": 60,
        "nightlife": 120,
        "historical": 90,
        "nature": 60
    }
    base_duration = base_duration_map.get(category, 90)  # Default to 90 instead of 60
    
    # Adjust based on rating and popularity (if available)
    if rating and user_rating_count:
        # Higher rated and more popular places typically need more time
        if rating >= 4.5 and user_rating_count >= 100:
            # Popular, highly-rated place - add 20-30% more time
            adjustment = int(base_duration * 0.25)
            base_duration += adjustment
        elif rating >= 4.0 and user_rating_count >= 50:
            # Well-rated place - add 10-15% more time
            adjustment = int(base_duration * 0.15)
            base_duration += adjustment
        elif rating < 3.5:
            # Lower rated - reduce time slightly
            adjustment = int(base_duration * 0.1)
            base_duration = max(base_duration - adjustment, int(base_duration * 0.7))
    
    return base_duration


def _map_travel_mode_to_calculation_mode(travel_mode: Optional[str]) -> str:
    """
    Map travel_mode preference to calculate_travel_time mode.
    ALWAYS defaults to "driving" (car) for all scenarios unless "walking" is explicitly mentioned.
    
    Args:
        travel_mode: Travel mode preference ("road", "airplane", "railway", or None)
    
    Returns:
        Mode string for calculate_travel_time ("driving" by default, "walking" only if explicitly requested)
    """
    # Convert to lowercase for comparison
    if travel_mode:
        travel_mode_lower = travel_mode.lower()
        # Only use walking if explicitly mentioned
        if "walking" in travel_mode_lower or "walk" in travel_mode_lower:
            logger.info(f"🚶 Travel mode explicitly set to 'walking' (user requested)")
            return "walking"
    
    # ALWAYS default to driving (car) for all scenarios (road, airplane, railway, or not specified)
    # This ensures car/driving mode is used unless user explicitly wants walking
    logger.info(f"🚗 Using 'driving' mode for travel calculations (travel_mode input: {travel_mode or 'None'})")
    return "driving"


def _format_pois_for_prompt(pois: List[Dict]) -> str:
    """Format POIs for LLM prompt with all relevant details."""
    formatted = []
    for i, poi in enumerate(pois, 1):
        line = f"{i}. {poi['name']} ({poi['category']}) - "
        line += f"Duration: {poi['duration_minutes']} min, "
        line += f"Location: ({poi['location']['lat']}, {poi['location']['lon']})"
        if poi.get('opening_hours'):
            line += f", Opening hours: {poi['opening_hours']}"
        if poi.get('source_id'):
            line += f", Source ID: {poi['source_id']}"
        formatted.append(line)
    return "\n".join(formatted)


def _parse_llm_itinerary_response(response_text: str, num_days: int) -> Dict[str, Any]:
    """
    Parse LLM response into structured itinerary.
    Handles both JSON and natural language responses.
    """
    try:
        # Try to extract JSON from response
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            response_text = response_text[start:end].strip()
        
        # Parse JSON
        itinerary_data = json.loads(response_text)
        return itinerary_data
    
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON from LLM response, using fallback")
        # Fallback: create a simple structure
        return _create_fallback_itinerary(num_days)


def _create_fallback_itinerary(num_days: int) -> Dict[str, Any]:
    """Create a basic fallback itinerary structure."""
    itinerary = {}
    for day in range(1, num_days + 1):
        itinerary[f"day_{day}"] = {
            "morning": {"activities": []},
            "afternoon": {"activities": []},
            "evening": {"activities": []}
        }
    return itinerary


def _enrich_activity_with_poi_data(activity: Dict, poi: Dict) -> Dict:
    """Enrich activity with complete POI data to ensure all fields are present.
    
    Args:
        activity: Activity dictionary (from LLM)
        poi: POI dictionary with full details
    
    Returns:
        Enriched activity with all required fields
    """
    enriched = activity.copy()
    
    # ALWAYS use POI duration_minutes (POI is source of truth, don't override with defaults)
    poi_duration = poi.get('duration_minutes')
    if poi_duration and poi_duration > 0:
        enriched['duration_minutes'] = poi_duration
        logger.debug(f"Using POI duration for {poi.get('name')}: {poi_duration} min (from Google Places API)")
    else:
        # POI doesn't have duration - estimate from category, rating, and user count
        category = poi.get('category', 'attraction')
        rating = poi.get('rating')
        user_rating_count = poi.get('user_rating_count', 0)
        estimated_duration = _estimate_duration_from_category(category, rating, user_rating_count)
        enriched['duration_minutes'] = estimated_duration
        logger.info(f"POI '{poi.get('name')}' missing duration, estimated {estimated_duration} min from category '{category}' (rating: {rating}, reviews: {user_rating_count})")
    
    # Always preserve data_source from POI
    if poi.get('data_source'):
        enriched['data_source'] = poi.get('data_source')
        logger.debug(f"Preserved data_source '{poi.get('data_source')}' for activity '{poi.get('name')}'")
    
    # Always set location from POI (POI is source of truth)
    enriched['location'] = poi.get('location', enriched.get('location', {}))
    
    # Always set opening_hours from POI if available
    if poi.get('opening_hours'):
        enriched['opening_hours'] = poi.get('opening_hours')
    
    # Always set source_id from POI
    if poi.get('source_id'):
        enriched['source_id'] = poi.get('source_id')
    
    # Always set data_source from POI (critical for source attribution)
    if poi.get('data_source'):
        enriched['data_source'] = poi.get('data_source')
    
    # Set category from POI if not set
    if poi.get('category'):
        enriched['category'] = poi.get('category')
    
    # Set description from POI if not set
    if poi.get('description'):
        enriched['description'] = poi.get('description')
    
    # Set rating from POI if available
    if poi.get('rating'):
        enriched['rating'] = poi.get('rating')
    
    # Ensure activity name matches POI name (use POI name as source of truth)
    if poi.get('name'):
        enriched['activity'] = poi.get('name')
    
    return enriched


def _find_matching_poi(activity: Dict, pois: List[Dict]) -> Optional[Dict]:
    """Find matching POI for an activity using source_id first, then improved name matching.
    
    Args:
        activity: Activity dictionary
        pois: List of POI dictionaries to match against
    
    Returns:
        Matching POI dictionary or None
    """
    act_name = activity.get('activity', '').lower().strip()
    act_source_id = activity.get('source_id')
    
    # Strategy 1: Match by source_id (most reliable)
    if act_source_id:
        for p in pois:
            if p.get('source_id') == act_source_id:
                logger.debug(f"Matched '{activity.get('activity')}' to POI '{p['name']}' by source_id: {act_source_id}")
                return p
    
    # Strategy 2: Exact name match (case-insensitive)
    for p in pois:
        p_name = p['name'].lower().strip()
        if p_name == act_name:
            logger.debug(f"Matched '{activity.get('activity')}' to POI '{p['name']}' by exact name")
            return p
    
    # Strategy 3: Name contains (one contains the other)
    for p in pois:
        p_name = p['name'].lower().strip()
        if p_name in act_name or act_name in p_name:
            logger.debug(f"Matched '{activity.get('activity')}' to POI '{p['name']}' by name containment")
            return p
    
    # Strategy 4: Word-based matching (at least 2 significant words match)
    act_words = [w for w in act_name.split() if len(w) > 3]
    best_match = None
    best_score = 0
    
    for p in pois:
        p_name = p['name'].lower().strip()
        p_words = [w for w in p_name.split() if len(w) > 3]
        
        # Count matching words
        matching_words = set(act_words) & set(p_words)
        if len(matching_words) >= 2 or (len(act_words) == 1 and len(p_words) == 1 and matching_words):
            score = len(matching_words)
            if score > best_score:
                best_score = score
                best_match = p
    
    if best_match:
        logger.debug(f"Matched '{activity.get('activity')}' to POI '{best_match['name']}' by word matching (score: {best_score})")
        return best_match
    
    logger.warning(f"Could not find matching POI for activity '{activity.get('activity')}' - tried source_id, exact name, containment, and word matching")
    return None


def _calculate_travel_times_for_activities(activities: List[Dict], pois: List[Dict], previous_poi: Optional[Dict] = None, travel_mode: str = "driving") -> List[Dict]:
    """Calculate travel times between activities based on POI locations.
    Also enriches activities with complete POI data (duration, location, opening_hours).
    
    Args:
        activities: List of activity dictionaries
        pois: List of POI dictionaries to match against
        previous_poi: POI from previous time block or day (for cross-block travel, or starting point location)
        travel_mode: Travel mode for calculating travel times ("walking", "driving", "bicycling", etc.)
    
    Returns:
        Updated activities list with travel_time_from_previous set and all POI data enriched
    """
    updated_activities = []
    current_prev_poi = previous_poi  # Start with previous block/day's POI or starting point
    is_first_activity = previous_poi is not None and previous_poi.get('name') == 'Starting Point'
    
    for i, activity in enumerate(activities):
        # Find matching POI using improved matching logic
        poi = _find_matching_poi(activity, pois)
        
        # Enrich activity with complete POI data (duration, location, opening_hours, etc.)
        if poi:
            activity = _enrich_activity_with_poi_data(activity, poi)
            poi_source = poi.get('data_source', 'unknown')
            logger.info(f"✅ Enriched activity '{activity.get('activity')}' with POI data: duration={activity.get('duration_minutes')}min, location=({activity.get('location', {}).get('lat', 'N/A')}, {activity.get('location', {}).get('lon', 'N/A')}), source={poi_source}, opening_hours={activity.get('opening_hours', 'N/A')}")
        else:
            # No matching POI found - estimate from category instead of hardcoded 60
            activity_name = activity.get('activity', 'unknown')
            category = activity.get('category', 'attraction')
            if not activity.get('duration_minutes') or activity.get('duration_minutes') == 0:
                estimated_duration = _estimate_duration_from_category(category)
                activity['duration_minutes'] = estimated_duration
                logger.warning(f"⚠️ Activity '{activity_name}' not found in POIs, estimated {estimated_duration}min from category '{category}' (NOT using default 60min)")
            else:
                logger.warning(f"⚠️ Activity '{activity_name}' not found in POIs, but has duration={activity.get('duration_minutes')}min from LLM")
        
        # Calculate travel time
        travel_minutes = 0
        if current_prev_poi:
            # We have a previous location (previous POI or starting point)
            destination_location = None
            
            # Get destination location from POI if matched, otherwise from activity
            if poi and poi.get('location'):
                destination_location = poi['location']
            elif activity.get('location'):
                destination_location = activity['location']
            
            if destination_location and current_prev_poi.get('location'):
                try:
                    origin_name = current_prev_poi.get('name', 'previous location')
                    dest_name = poi.get('name', activity.get('activity')) if poi else activity.get('activity')
                    
                    travel_info = calculate_travel_time(
                        origin=current_prev_poi['location'],
                        destination=destination_location,
                        mode=travel_mode
                    )
                    travel_minutes = travel_info.get('duration_minutes', 0)
                    travel_source = travel_info.get('source', 'unknown')
                    
                    if is_first_activity:
                        logger.info(f"📍 Calculated travel time from starting point to first activity '{dest_name}': {travel_minutes} min (source: {travel_source}, mode: {travel_mode})")
                    else:
                        logger.info(f"🚗 Calculated travel time from '{origin_name}' to '{dest_name}': {travel_minutes} min (source: {travel_source}, mode: {travel_mode})")
                except Exception as e:
                    logger.warning(f"❌ Failed to calculate travel time from '{current_prev_poi.get('name', 'previous')}' to '{activity.get('activity')}': {e}")
                    travel_minutes = 10 if is_first_activity else 0  # Default 10 min from starting point, 0 otherwise
        
        activity['travel_time_from_previous'] = travel_minutes
        
        # Reset first activity flag after processing first activity
        if is_first_activity:
            is_first_activity = False
        
        # Update previous POI for next iteration (use POI if matched, otherwise use activity location)
        if poi:
            current_prev_poi = poi
        elif activity.get('location'):
            # Use activity location as previous for next calculation even if POI not matched
            current_prev_poi = {
                'name': activity.get('activity', 'previous location'),
                'location': activity['location']
            }
        
        updated_activities.append(activity)
    
    return updated_activities


def build_itinerary_mcp(
    pois: List[Dict],
    daily_time_windows: List[Dict[str, Any]],
    pace: str = "moderate",
    preferences: Optional[Dict[str, Any]] = None,
    starting_point_location: Optional[Dict[str, float]] = None,
    travel_mode: Optional[str] = None
) -> Dict[str, Any]:
    """
    MCP Tool: Build a day-wise itinerary from POIs.
    
    Args:
        pois: List of POI dictionaries from POI Search MCP
        daily_time_windows: List of dicts with 'day', 'start', 'end' (e.g., {"day": 1, "start": "09:00", "end": "22:00"})
        pace: Pace preference ("relaxed", "moderate", "fast")
        preferences: Optional preferences dict (e.g., {"food": True, "culture": True})
    
    Returns:
        Dictionary with MCP-compliant structure:
        {
            "itinerary": {
                "day_1": {
                    "morning": [...],
                    "afternoon": [...],
                    "evening": [...]
                },
                ...
            },
            "total_travel_time": int,
            "explanation": str
        }
    """
    try:
        logger.info(f"MCP Itinerary Builder: {len(pois)} POIs, {len(daily_time_windows)} days, pace={pace}")
        
        if not pois:
            return {
                "itinerary": {},
                "total_travel_time": 0,
                "explanation": "No POIs provided to build itinerary",
                "error": "No POIs provided"
            }
        
        num_days = len(daily_time_windows)
        
        # Build LLM prompt
        pois_text = _format_pois_for_prompt(pois)
        time_windows_text = "\n".join([
            f"Day {tw['day']}: {tw['start']} - {tw['end']}"
            for tw in daily_time_windows
        ])
        
        system_prompt = """You are an expert travel itinerary planner. Create realistic, feasible day-wise itineraries 
that group nearby attractions, respect time constraints, and match the user's pace preference.

Return a JSON object with this exact structure:
{
    "day_1": {
        "morning": {
            "activities": [
                {
                    "activity": "Activity name (must match POI name exactly)",
                    "time": "09:00 - 10:30",
                    "duration_minutes": 90,
                    "location": {"lat": 26.9240, "lon": 75.8266},
                    "category": "historical",
                    "source_id": "way:123456",
                    "description": "Brief description",
                    "opening_hours": "Mo-Su 09:00-18:00"
                }
            ]
        },
        "afternoon": {"activities": [...]},
        "evening": {"activities": [...]}
    },
    "day_2": {...},
    ...
}

CRITICAL RULES:
- Use EXACT POI names, locations (lat/lon), source_ids, and duration_minutes from the provided list
- ALWAYS include opening_hours if provided in POI data
- duration_minutes MUST be greater than 0 (use POI duration_minutes value)
- location MUST include both lat and lon (use POI location values)
- Group nearby POIs together (check coordinates)
- Respect time windows (start/end times)
- Match pace: relaxed=2-3 activities/day, moderate=3-4, fast=4-5
- Distribute activities evenly across days
- Only return valid JSON, no other text"""
        
        user_prompt = f"""Create a {num_days}-day itinerary with pace: {pace}

Available POIs:
{pois_text}

Time Windows:
{time_windows_text}

Preferences: {preferences or {}}

Return the JSON itinerary structure as specified."""
        
        # Call Grok API
        grok_client = get_grok_client()
        response = grok_client.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=3000
        )
        
        # Parse response
        itinerary_data = _parse_llm_itinerary_response(response, num_days)
        
        # Map travel_mode to calculation mode (road -> driving, others -> walking)
        calculation_mode = _map_travel_mode_to_calculation_mode(travel_mode)
        logger.info(f"Using travel mode '{calculation_mode}' for within-city travel calculations (travel_mode: {travel_mode})")
        
        # Calculate travel times - need to account for:
        # 1. Travel from starting point to first activity of Day 1
        # 2. Travel between activities within a time block
        # 3. Travel between time blocks (morning->afternoon, afternoon->evening)
        # 4. Travel between days (last activity of day N to first activity of day N+1)
        total_travel_time = 0
        previous_activity_poi = None  # Track last activity's POI across all blocks/days
        
        # If starting point location provided, use it as previous POI for first activity of Day 1
        if starting_point_location:
            previous_activity_poi = {
                "name": "Starting Point",
                "location": starting_point_location
            }
            logger.info(f"Using starting point location for travel calculations: {starting_point_location}")
        
        day_keys = sorted([k for k in itinerary_data.keys() if k.startswith("day_")])
        is_first_activity_of_day_1 = True  # Track first activity to calculate from starting point
        
        for day_key in day_keys:
            day_data = itinerary_data[day_key]
            time_blocks = ["morning", "afternoon", "evening"]
            
            for time_block in time_blocks:
                if time_block in day_data and "activities" in day_data[time_block]:
                    activities = day_data[time_block]["activities"]
                    updated_activities = _calculate_travel_times_for_activities(activities, pois, previous_activity_poi, travel_mode=calculation_mode)
                    day_data[time_block]["activities"] = updated_activities
                    
                    # After processing first activity of Day 1, reset is_first_activity flag
                    if is_first_activity_of_day_1 and updated_activities:
                        is_first_activity_of_day_1 = False
                    
                    # Sum travel times and update previous POI
                    for act in updated_activities:
                        travel_time = act.get('travel_time_from_previous', 0)
                        total_travel_time += travel_time
                        
                        # Log travel time for debugging
                        if travel_time > 0:
                            logger.debug(f"Travel time: {travel_time} min from previous to {act.get('activity', 'unknown')}")
                        
                        # Update previous_activity_poi for next calculation
                        # Use enriched activity data if available, otherwise find matching POI
                        if act.get('location') and act.get('location').get('lat') and act.get('location').get('lon'):
                            # Use enriched activity location (more reliable than re-matching)
                            previous_activity_poi = {
                                'name': act.get('activity', 'previous location'),
                                'location': act['location']
                            }
                            # Try to find matching POI to get full POI data for next calculation
                            matched_poi = _find_matching_poi(act, pois)
                            if matched_poi:
                                previous_activity_poi = matched_poi
                        else:
                            # Fallback: find matching POI by name
                            matched_poi = _find_matching_poi(act, pois)
                            if matched_poi:
                                previous_activity_poi = matched_poi
        
        # Generate explanation
        travel_hours = total_travel_time // 60
        travel_minutes = total_travel_time % 60
        travel_time_str = f"{travel_hours}h {travel_minutes}m" if travel_hours > 0 else f"{travel_minutes}m"
        
        explanation = f"Created a {num_days}-day {pace} pace itinerary with {len(pois)} POIs, " \
                      f"grouping nearby attractions and respecting time constraints. " \
                      f"Total estimated travel time: {travel_time_str}."
        
        logger.info(f"MCP Itinerary Builder: Created itinerary with {num_days} days, total travel time: {total_travel_time} min ({travel_time_str})")
        
        return {
            "itinerary": itinerary_data,
            "total_travel_time": total_travel_time,
            "explanation": explanation,
            "num_days": num_days,
            "pace": pace
        }
    
    except Exception as e:
        logger.error(f"MCP Itinerary Builder error: {e}", exc_info=True)
        return {
            "itinerary": {},
            "total_travel_time": 0,
            "explanation": f"Error building itinerary: {str(e)}",
            "error": str(e)
        }


# For direct testing
if __name__ == "__main__":
    # Test the MCP tool
    test_pois = [
        {
            "name": "Hawa Mahal",
            "category": "historical",
            "location": {"lat": 26.9240, "lon": 75.8266},
            "duration_minutes": 90,
            "source_id": "way:123456"
        },
        {
            "name": "City Palace",
            "category": "historical",
            "location": {"lat": 26.9250, "lon": 75.8270},
            "duration_minutes": 120,
            "source_id": "way:123457"
        }
    ]
    
    time_windows = [
        {"day": 1, "start": "09:00", "end": "22:00"},
        {"day": 2, "start": "09:00", "end": "22:00"}
    ]
    
    result = build_itinerary_mcp(
        pois=test_pois,
        daily_time_windows=time_windows,
        pace="moderate"
    )
    print(f"Built itinerary: {result.get('explanation', 'N/A')}")
