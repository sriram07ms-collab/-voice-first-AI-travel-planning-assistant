# Sources Limit Fix - Issue 3

## Summary

Fixed the issue where sources were limited to 6 instead of showing up to 10 citations. The system now properly collects and displays 10 sources when available.

## Problem

- Sources were showing only 6 citations instead of the expected 10
- RAG context was limited to `top_k=5`, providing only 5 Wikivoyage sources
- Sources from activities weren't being supplemented with POIs when needed
- No logic to ensure we reach 10 total sources when available

## Root Causes

1. **RAG Limit**: RAG retrieval was set to `top_k=5`, limiting Wikivoyage sources to only 5
2. **No Supplementation Logic**: If activities had fewer sources, there was no logic to supplement with POIs to reach 10
3. **No Target Goal**: The code didn't actively try to reach 10 sources total

## Solution

### Changes Made

#### 1. Increased RAG Top-K (`backend/src/orchestrator/orchestrator.py`)
- **Before**: `top_k=5` (only 5 Wikivoyage sources)
- **After**: `top_k=10` (up to 10 Wikivoyage sources available)
- **Line**: Changed `retrieve_city_tips(..., top_k=5)` to `top_k=10`

#### 2. Added Source Collection Strategy
- **Target**: `MAX_TARGET_SOURCES = 10`
- **Priority Order**:
  1. All sources from itinerary activities (no limit - collect all)
  2. Supplement with POIs if less than 10 sources from activities
  3. Add Wikivoyage sources (up to 10 total)

#### 3. Improved Fallback Logic
- **Before**: Only used POIs if NO sources from activities
- **After**: Supplement with POIs if sources < 10, even if we have some from activities
- **Benefit**: Ensures we reach 10 sources whenever possible

#### 4. Deduplication Enhancement
- Added proper deduplication for Wikivoyage sources
- Uses unique keys to avoid duplicate sources
- Tracks all sources in `sources_seen` set

### Source Collection Flow

```
1. Collect ALL sources from itinerary activities
   └─> Activities (morning/afternoon/evening for all days)
   └─> No limit - collect all activities with source_id

2. If sources < 10, supplement with POIs
   └─> Add POIs up to (10 - current_count)
   └─> Skip duplicates using sources_seen set

3. Add Wikivoyage sources
   └─> Add unique Wikivoyage sources
   └─> Stop when we reach 10 total sources

Final: Up to 10 sources total (or all available if less than 10)
```

## Code Changes

### File: `backend/src/orchestrator/orchestrator.py`

#### Change 1: Increased RAG Top-K
```python
# Before
rag_context = retrieve_city_tips(city, query="travel tips and recommendations", top_k=5)

# After
rag_context = retrieve_city_tips(city, query="travel tips and recommendations", top_k=10)
```

#### Change 2: Added MAX_TARGET_SOURCES constant
```python
MAX_TARGET_SOURCES = 10  # Target maximum of 10 sources
```

#### Change 3: Supplement with POIs if needed
```python
# Supplement with POIs if we don't have enough sources from activities
if pois and len(sources) < MAX_TARGET_SOURCES:
    remaining_slots = MAX_TARGET_SOURCES - len(sources)
    # Add POIs to fill remaining slots...
```

#### Change 4: Improved Wikivoyage source addition
```python
# Add RAG/Wikivoyage sources (limit to reach 10 total)
if rag_context:
    for rag_item in rag_context:
        if len(sources) >= MAX_TARGET_SOURCES:
            break  # Stop when we reach 10 total
        # Add unique Wikivoyage sources...
```

## Expected Behavior

### Scenario 1: Many Activity Sources (15+ activities)
- ✅ Collects all activity sources (e.g., 15)
- ✅ Adds up to 10 Wikivoyage sources (if available)
- ✅ Total: Up to 25 sources (but typically limited to ~10-15)

### Scenario 2: Few Activity Sources (3-4 activities)
- ✅ Collects all 3-4 activity sources
- ✅ Supplements with 6-7 POIs to reach ~10 total
- ✅ Adds Wikivoyage sources if still below 10
- ✅ Total: 10 sources

### Scenario 3: No Activity Sources (fallback)
- ✅ Collects top 10 POIs
- ✅ Adds up to 10 Wikivoyage sources
- ✅ Total: Up to 10 sources

### Scenario 4: Limited Available Sources (< 10 total)
- ✅ Collects all available sources
- ✅ No artificial limit - shows all available
- ✅ Total: All available sources (e.g., 7 sources if only 7 exist)

## Testing

### Test Cases

1. **Trip with 8 activities**:
   - Expected: 8 activity sources + 2 POI/Wikivoyage = 10 total

2. **Trip with 3 activities**:
   - Expected: 3 activity sources + 7 POI/Wikivoyage = 10 total

3. **Trip with 15 activities**:
   - Expected: All 15 activity sources + Wikivoyage = 15+ total

4. **Trip with no activity sources**:
   - Expected: 10 POI sources + Wikivoyage = 10+ total

### Verification

Check logs for:
```
INFO: ✅ Added X sources from itinerary activities
INFO: Added Y POI sources to supplement activities (total now: Z)
INFO: Added W Wikivoyage sources (total now: TOTAL)
INFO: Total sources prepared: TOTAL (target: 10)
```

## Logging Improvements

Added detailed logging:
- Number of sources from activities
- Number of POI sources added for supplementation
- Number of Wikivoyage sources added
- Total sources count with target

Example log output:
```
INFO: ✅ Added 6 sources from itinerary activities: 4 Google Places, 2 OpenStreetMap
INFO: Supplementing with POIs: 6 sources so far, need 4 more to reach 10
INFO: Added 4 POI sources to supplement activities (total now: 10)
INFO: Added 3 Wikivoyage sources (total now: 13)
INFO: Total sources prepared: 13 (target: 10)
```

## Frontend

No changes needed - `SourcesView.tsx` already displays all sources passed to it without limits.

## Impact

- ✅ Users now see up to 10 sources instead of only 6
- ✅ Better source diversity (activities + POIs + Wikivoyage)
- ✅ More complete citations for itinerary activities
- ✅ Better transparency and trust in the system

## Notes

- If fewer than 10 sources are available in total, all available sources are shown
- Sources are deduplicated to avoid showing the same source twice
- Priority: Activities > POIs > Wikivoyage (to ensure most relevant sources first)
