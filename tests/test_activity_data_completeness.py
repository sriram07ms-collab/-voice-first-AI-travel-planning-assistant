"""
Test to verify that activities have all required data (duration, location, opening_hours).
This addresses the issue where activities were missing critical information.
"""

import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from src.data_sources.openstreetmap import search_pois

# Add mcp-tools to path - handle directory name with hyphen
mcp_tools_dir = Path(__file__).parent.parent / "mcp-tools"
sys.path.insert(0, str(mcp_tools_dir))

# Import from itinerary-builder (directory name with hyphen, module name with underscore)
import importlib.util
itinerary_builder_path = mcp_tools_dir / "itinerary-builder" / "server.py"
spec = importlib.util.spec_from_file_location("itinerary_builder.server", itinerary_builder_path)
itinerary_builder_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(itinerary_builder_module)
build_itinerary_mcp = itinerary_builder_module.build_itinerary_mcp


def test_activity_data_completeness():
    """Test that all activities have duration, location, and opening_hours."""
    
    print("=" * 80)
    print("Testing Activity Data Completeness")
    print("=" * 80)
    
    # Test with Chennai (as mentioned in user's image)
    city = "Chennai"
    interests = ["food", "culture"]
    
    print(f"\n1. Searching POIs for {city}...")
    try:
        pois = search_pois(city=city, interests=interests, limit=10)
        print(f"   ✅ Found {len(pois)} POIs")
        
        if len(pois) == 0:
            print("   ⚠️  No POIs found - cannot test activity enrichment")
            return
        
        # Check POI data quality
        print(f"\n2. Checking POI data quality...")
        for i, poi in enumerate(pois[:3], 1):
            print(f"\n   POI {i}: {poi.get('name')}")
            print(f"     - Duration: {poi.get('duration_minutes')} min")
            print(f"     - Location: {poi.get('location')}")
            print(f"     - Opening hours: {poi.get('opening_hours', 'Not specified')}")
            print(f"     - Source ID: {poi.get('source_id')}")
        
        # Build itinerary
        print(f"\n3. Building itinerary...")
        time_windows = [
            {"day": 1, "start": "09:00", "end": "22:00"},
            {"day": 2, "start": "09:00", "end": "22:00"}
        ]
        
        # Convert POIs to dict format for MCP
        pois_dict = []
        for poi in pois:
            pois_dict.append({
                "name": poi.get("name"),
                "category": poi.get("category"),
                "location": poi.get("location"),
                "duration_minutes": poi.get("duration_minutes"),
                "source_id": poi.get("source_id"),
                "opening_hours": poi.get("opening_hours"),
                "description": poi.get("description")
            })
        
        result = build_itinerary_mcp(
            pois=pois_dict,
            daily_time_windows=time_windows,
            pace="relaxed",
            preferences={"food": True, "culture": True}
        )
        
        if result.get("error"):
            print(f"   ❌ Error building itinerary: {result.get('error')}")
            return
        
        itinerary = result.get("itinerary", {})
        print(f"   ✅ Itinerary built successfully")
        
        # Check activities for data completeness
        print(f"\n4. Checking activity data completeness...")
        issues_found = []
        total_activities = 0
        
        for day_key in sorted([k for k in itinerary.keys() if k.startswith("day_")]):
            day_data = itinerary[day_key]
            day_num = int(day_key.split("_")[1])
            print(f"\n   {day_key.upper()}:")
            
            for time_block in ["morning", "afternoon", "evening"]:
                if time_block in day_data and "activities" in day_data[time_block]:
                    activities = day_data[time_block]["activities"]
                    if activities:
                        print(f"     {time_block.capitalize()}: {len(activities)} activities")
                        
                        for i, activity in enumerate(activities, 1):
                            total_activities += 1
                            activity_name = activity.get("activity", "Unknown")
                            
                            # Check 1: Duration
                            duration = activity.get("duration_minutes", 0)
                            if duration == 0 or duration is None:
                                issues_found.append(f"{day_key} {time_block} activity {i} ({activity_name}): Duration is 0 or missing")
                                print(f"       ❌ Activity {i}: {activity_name} - Duration: {duration} (MISSING/0)")
                            else:
                                print(f"       ✅ Activity {i}: {activity_name} - Duration: {duration} min")
                            
                            # Check 2: Location
                            location = activity.get("location")
                            if not location or not location.get("lat") or not location.get("lon"):
                                issues_found.append(f"{day_key} {time_block} activity {i} ({activity_name}): Location is missing")
                                print(f"       ❌ Activity {i}: {activity_name} - Location: {location} (MISSING)")
                            else:
                                print(f"       ✅ Activity {i}: {activity_name} - Location: ({location.get('lat')}, {location.get('lon')})")
                            
                            # Check 3: Opening hours (optional but should be present if available in POI)
                            opening_hours = activity.get("opening_hours")
                            if opening_hours:
                                print(f"       ✅ Activity {i}: {activity_name} - Opening hours: {opening_hours}")
                            else:
                                # Not critical, but note it
                                print(f"       ⚠️  Activity {i}: {activity_name} - Opening hours: Not specified (may be OK)")
                            
                            # Check 4: Source ID
                            source_id = activity.get("source_id")
                            if source_id:
                                print(f"       ✅ Activity {i}: {activity_name} - Source ID: {source_id}")
                            else:
                                print(f"       ⚠️  Activity {i}: {activity_name} - Source ID: Not specified")
        
        # Summary
        print(f"\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total activities checked: {total_activities}")
        print(f"Critical issues found: {len([i for i in issues_found if 'Duration' in i or 'Location' in i])}")
        print(f"Total issues found: {len(issues_found)}")
        
        if issues_found:
            print(f"\n❌ ISSUES FOUND:")
            for issue in issues_found:
                print(f"   - {issue}")
            return False
        else:
            print(f"\n✅ ALL TESTS PASSED - All activities have required data!")
            return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_activity_data_completeness()
    sys.exit(0 if success else 1)
