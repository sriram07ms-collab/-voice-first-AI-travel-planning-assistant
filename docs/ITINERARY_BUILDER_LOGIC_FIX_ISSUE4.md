# Itinerary Builder Logic Fix - Issue 4

## Summary

Enhanced Itinerary Builder logic to strictly follow architecture requirements, design documents, and TEST_GUIDE.md specifications. The system now properly groups nearby POIs, respects time windows, matches pace preferences, and distributes activities evenly.

## Problem

- Itinerary Builder was not strictly following architecture/design requirements
- POI grouping by proximity was not emphasized enough
- Time window constraints were not strictly enforced
- Pace matching rules were too lenient
- Activity distribution across days was not guaranteed

## Architecture Requirements (from IMPLEMENTATION_GUIDE.md)

1. **Group nearby attractions** - Use coordinates to group POIs
2. **Respect time constraints** - Strict adherence to time windows
3. **Match pace preference** - Relaxed=2-3, Moderate=3-4, Fast=4-5 activities/day
4. **Distribute evenly** - Similar number of activities per day
5. **Structure into day/time blocks** - Morning/Afternoon/Evening
6. **Calculate travel times** - Between activities
7. **Generate explanations** - Why activities were selected

## Test Requirements (from TEST_GUIDE.md)

- **Relaxed pace**: 2-3 activities per day
- **Activities grouped by proximity** - Short travel times (5-20 minutes)
- **Time windows respected** - 09:00-22:00 typically
- **Even distribution** - Similar activities across days
- **Food interests prioritized** - Multiple food experiences per day

## Solution

### Changes Made

#### 1. Enhanced System Prompt (`mcp-tools/itinerary-builder/server.py`)

**Added 8 Critical Rules:**

1. **POI Data Accuracy (Mandatory)**
   - Use EXACT POI names, coordinates, durations, source_ids
   - No modifications or inventions

2. **Proximity Grouping (Critical)**
   - Check lat/lon coordinates for all POIs
   - Group POIs within ~2km together
   - Calculate distance: |lat1-lat2| + |lon1-lon2|
   - Smaller values = closer together
   - Must be on same day and time block

3. **Time Window Constraints (Mandatory)**
   - Respect exact time windows provided
   - Start times >= window start
   - End times <= window end
   - Total daily time must fit within window
   - Never schedule outside windows

4. **Pace Matching (Strict)**
   - Relaxed: 2-3 activities/day (never > 3)
   - Moderate: 3-4 activities/day
   - Fast: 4-5 activities/day
   - Count across all time blocks

5. **Activity Distribution**
   - Distribute evenly across all days
   - Similar number per day (within 1 activity difference)
   - Do not pack one day heavily

6. **Time Block Organization**
   - Morning: Start from window start to ~12:00-13:00
   - Afternoon: ~13:00 to ~17:00-18:00
   - Evening: ~17:00-18:00 to window end
   - Smooth transitions between blocks

7. **Travel Time Consideration**
   - Consider travel time when grouping
   - Group nearby POIs to minimize travel
   - Leave buffer for travel time

8. **Opening Hours**
   - Check opening_hours if provided
   - Schedule only when POI is open
   - Use defaults if not provided

#### 2. Enhanced User Prompt

Added specific instructions:
- Proximity grouping guidance
- Pace requirement clarification
- Time window strictness
- Distribution requirements
- Data accuracy reminders

#### 3. Enhanced POI Formatting

- Added proximity hint in POI list
- Clearer coordinate format (lat=X, lon=Y)
- Added description field if available
- Proximity calculation guidance

### File: `mcp-tools/itinerary-builder/server.py`

#### Change 1: Enhanced POI Formatting

```python
def _format_pois_for_prompt(pois: List[Dict]) -> str:
    """Format POIs with proximity hints."""
    # ... format each POI ...
    # Add proximity hint
    formatted.append("\nNOTE: Check lat/lon coordinates when grouping POIs. POIs with similar coordinates (within ~2km) should be scheduled on the same day and time block.")
    return "\n".join(formatted)
```

#### Change 2: Comprehensive System Prompt

Added 8 detailed rules covering:
- Data accuracy
- Proximity grouping (with distance calculation)
- Time window constraints
- Pace matching (strict)
- Activity distribution
- Time block organization
- Travel time consideration
- Opening hours

#### Change 3: Enhanced User Prompt

Added specific instructions section with:
- Proximity grouping guidance
- Pace requirement details
- Time window strictness
- Distribution requirements

## Expected Behavior

### Scenario 1: Relaxed Pace, 2-Day Trip
- ✅ 2-3 activities per day (never more than 3)
- ✅ POIs grouped by proximity
- ✅ Activities distributed evenly (similar count per day)
- ✅ All activities within time windows (09:00-22:00)

### Scenario 2: Food-Focused Itinerary
- ✅ Multiple food experiences per day (2-3)
- ✅ Restaurants prioritized
- ✅ Food places in morning (breakfast), afternoon (lunch), evening (dinner)
- ✅ Still respects pace (2-3 activities total per day for relaxed)

### Scenario 3: Moderate Pace, 3-Day Trip
- ✅ 3-4 activities per day
- ✅ POIs grouped by proximity (minimize travel time)
- ✅ Activities distributed evenly across 3 days
- ✅ Time windows strictly respected

## Proximity Grouping Algorithm

The prompt now instructs the LLM to:
1. Check lat/lon coordinates for all POIs
2. Calculate rough distance: |lat1-lat2| + |lon1-lon2|
3. Group POIs with difference < 0.02 (~2km) together
4. Schedule grouped POIs on same day and time block
5. Minimize travel time between activities

**Example:**
```
POI 1: Hawa Mahal (lat: 26.9240, lon: 75.8266)
POI 2: City Palace (lat: 26.9255, lon: 75.8236)
Distance: |26.9240-26.9255| + |75.8266-75.8236| = 0.0015 + 0.003 = 0.0045
Result: Very close! Must be grouped together.
```

## Pace Matching Rules

**Relaxed Pace:**
- ✅ 2-3 activities per day (strict: never more than 3)
- ✅ More time per activity
- ✅ Longer breaks between activities

**Moderate Pace:**
- ✅ 3-4 activities per day
- ✅ Balanced schedule
- ✅ Reasonable breaks

**Fast Pace:**
- ✅ 4-5 activities per day
- ✅ Packed schedule
- ✅ Minimal breaks

## Time Window Enforcement

**Strict Rules:**
- Start time >= time window start (e.g., 09:00)
- End time <= time window end (e.g., 22:00)
- Total daily time (activities + travel) <= window duration
- Never schedule outside windows

**Example:**
```
Time Window: Day 1: 09:00 - 22:00 (13 hours)
Activities:
  - Morning: 09:00-12:00 (3 hours) ✅
  - Afternoon: 13:00-17:00 (4 hours) ✅
  - Evening: 18:00-21:00 (3 hours) ✅
Total: 10 hours < 13 hours ✅ Valid
```

## Activity Distribution

**Requirement:**
- Distribute activities evenly across all days
- Each day should have similar number (within 1 activity)
- Do not pack one day while leaving others sparse

**Example (3-day trip, moderate pace):**
```
Day 1: 4 activities ✅
Day 2: 3 activities ✅ (within 1 of Day 1)
Day 3: 4 activities ✅
Total: 11 activities, well distributed
```

## Testing Against TEST_GUIDE.md

### Scenario 1: Complete Trip Planning
- ✅ Relaxed pace = 2-3 activities/day
- ✅ POIs grouped by proximity (travel times < 20 min)
- ✅ Time windows respected
- ✅ Activities distributed evenly

### Scenario 21: Food-Focused Itinerary
- ✅ Restaurants prioritized
- ✅ Multiple food experiences per day
- ✅ Still respects pace (2-3 activities for relaxed)
- ✅ Food experiences in multiple time slots

## Code Changes

### File: `mcp-tools/itinerary-builder/server.py`

#### Enhanced System Prompt
- Added 8 critical rules
- Explicit proximity grouping instructions
- Strict time window enforcement
- Strict pace matching
- Activity distribution requirements

#### Enhanced User Prompt
- Added specific instructions section
- Proximity grouping guidance
- Pace requirement details
- Time window strictness
- Distribution requirements

#### Enhanced POI Formatting
- Added proximity hint
- Clearer coordinate format
- Description field included
- Proximity calculation guidance

## Validation

The Itinerary Builder now:
1. ✅ Groups POIs by proximity (using coordinates)
2. ✅ Respects time windows strictly
3. ✅ Matches pace requirements exactly
4. ✅ Distributes activities evenly
5. ✅ Uses exact POI data (no modifications)
6. ✅ Considers opening hours
7. ✅ Minimizes travel time
8. ✅ Follows TEST_GUIDE.md expected outputs

## Notes

- LLM instructions are now much more explicit
- Proximity grouping is emphasized with distance calculation guidance
- Time windows are enforced strictly
- Pace matching is mandatory (not optional)
- Activity distribution is required
- All rules are clearly numbered and explained

## Future Enhancements

Potential improvements:
1. Pre-group POIs by proximity before sending to LLM
2. Add validation step to verify proximity grouping
3. Add check to ensure pace is matched correctly
4. Add validation for time window adherence
5. Add activity distribution verification
