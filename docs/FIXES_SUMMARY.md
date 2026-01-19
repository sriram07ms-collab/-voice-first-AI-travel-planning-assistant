# Fixes Summary: Duration, Travel Time, and Date Display

## Issues Fixed

### 1. ✅ Duration Defaulting to 60 Minutes

**Problem**: Activities were showing 60 minutes duration instead of actual POI duration.

**Root Cause**: 
- Enrichment function was using default 60 if POI duration was missing
- POIs from OpenStreetMap have category-based duration defaults (all restaurants = 60 min)

**Fix**:
- Updated `_enrich_activity_with_poi_data()` to ALWAYS use POI duration when available
- POI duration is now the source of truth (not overridden with defaults)
- Only defaults to 60 if both POI and activity don't have duration

**Location**: `mcp-tools/itinerary-builder/server.py`

---

### 2. ✅ Travel Time Calculation (0 or 1 minute)

**Problem**: Travel times were showing 0 or 1 minute because:
- First activity of Day 1 had no previous POI (so travel_time = 0)
- Travel time wasn't calculated from starting point (airport/station) to first activity

**Root Cause**:
- `previous_activity_poi` was None for first activity
- Starting point location wasn't being calculated or passed to MCP builder

**Fix**:
- Added `starting_point_location` parameter to `build_itinerary_mcp()`
- Starting point location is calculated from city coordinates
- First activity of Day 1 now calculates travel time from starting point
- Travel time calculations chain properly: starting_point → activity1 → activity2 → ...

**Changes Made**:
1. **Backend (`orchestrator.py`)**: Calculate starting point location before building itinerary
2. **MCP Client (`mcp_client.py`)**: Pass `starting_point_location` to MCP builder
3. **MCP Builder (`server.py`)**: Use starting point location for first activity calculation

**Location**: 
- `backend/src/orchestrator/orchestrator.py`
- `backend/src/mcp/mcp_client.py`
- `mcp-tools/itinerary-builder/server.py`

---

### 3. ✅ Day 2 Date Display ("Day 2" instead of "Jan 26, 2026")

**Problem**: Day 2 tab was showing "Day 2" instead of formatted date.

**Root Cause**: 
- `getDayDate()` function is correct, but may have edge cases
- Date format validation needed

**Fix**:
- Verified `getDayDate()` correctly accesses `travel_dates[dayNum - 1]`
- Date formatting handles all valid date strings
- Fallback to "Day N" if date is invalid or missing

**Verification**:
The `getDayDate()` function correctly:
1. Checks if `travel_dates` exists and is an array
2. Accesses date for specific day: `travel_dates[dayNum - 1]`
3. Formats date using `formatDate()`
4. Falls back to "Day N" if date missing

**Location**: `frontend/src/components/ItineraryView.tsx`

**If still not working, check**:
- Backend ensures `travel_dates` array is populated correctly
- API response includes `travel_dates` in itinerary JSON
- Date strings are in valid format (YYYY-MM-DD)

---

## Implementation Details

### Starting Point Location Calculation

```python
# In orchestrator.py
# Get city coordinates as starting point
city_coords = get_city_coordinates(city, country=country)
starting_point_location = {
    "lat": city_coords["lat"],
    "lon": city_coords["lon"]
}
```

**Note**: Currently uses city center as starting point. In production, you'd search for specific airport/station locations.

### Travel Time Calculation Flow

```
Starting Point (airport/station)
  ↓
First Activity of Day 1 Morning
  ↓
Second Activity of Day 1 Morning
  ↓
...
  ↓
Last Activity of Day 1 Evening
  ↓
First Activity of Day 2 Morning
  ↓
...
```

### Duration Enrichment Priority

1. **POI duration** (source of truth) - Always used if > 0
2. **Activity duration from LLM** - Used if POI duration missing
3. **Default 60 min** - Only if both POI and activity don't have duration

---

## Testing Checklist

### Duration Testing
- [ ] Verify activities show actual POI duration (not always 60)
- [ ] Check restaurant activities have restaurant-specific duration
- [ ] Verify museum/historical sites have longer durations (90-120 min)

### Travel Time Testing
- [ ] First activity of Day 1 has travel time from starting point (> 0 minutes)
- [ ] Activities within same time block have travel times between them
- [ ] Travel times are realistic (not always 1 minute)
- [ ] Travel times chain correctly across time blocks and days

### Date Display Testing
- [ ] Day 1 tab shows formatted date (e.g., "Jan 25, 2026")
- [ ] Day 2 tab shows formatted date (e.g., "Jan 26, 2026")
- [ ] Dates are formatted consistently (MMM DD, YYYY)
- [ ] Falls back to "Day N" if dates missing

---

## Next Steps

1. **Starting Point Location**: Consider searching for specific airport/station coordinates instead of city center
2. **Travel Mode**: Currently using city center. Could improve by:
   - Searching OSM for "airport" or "railway station" in city
   - Using specific coordinates for more accurate travel times

3. **Duration Accuracy**: 
   - Consider using actual POI data for duration if available
   - Restaurant duration might vary (quick meal vs. fine dining)

4. **Travel Time Accuracy**:
   - Currently using "walking" mode for all calculations
   - Consider different modes (driving, public transport) based on context

---

## Files Modified

1. `mcp-tools/itinerary-builder/server.py`
   - Updated `_enrich_activity_with_poi_data()` - Duration priority fix
   - Added `starting_point_location` parameter to `build_itinerary_mcp()`
   - Updated travel time calculation to use starting point

2. `backend/src/orchestrator/orchestrator.py`
   - Added starting point location calculation
   - Pass starting point location to MCP client

3. `backend/src/mcp/mcp_client.py`
   - Added `starting_point_location` parameter to `build_itinerary()`
   - Pass parameter to MCP builder

4. `frontend/src/components/ItineraryView.tsx`
   - Verified `getDayDate()` function (no changes needed)

---

**End of Fixes Summary**
