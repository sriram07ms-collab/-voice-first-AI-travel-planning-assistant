# Test Guide: New Features (Travel Mode, Dates, Activity Data Completeness)

This guide covers testing for the recently implemented features:
1. Travel Mode Clarifying Question
2. Travel Dates Clarifying Question
3. Starting Point Logic
4. Date Display in Frontend
5. Activity Data Completeness

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Test Scenarios](#test-scenarios)
3. [Test Data](#test-data)
4. [Validation Checklist](#validation-checklist)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Environment Setup
- Backend server running on `http://localhost:8000`
- Frontend server running on `http://localhost:3000`
- Groq API key configured in `.env`
- n8n webhook configured (optional, for PDF testing)

### Pre-test Checklist
- [ ] Clear browser cache/session storage
- [ ] Backend logs accessible for debugging
- [ ] Frontend console open (F12)
- [ ] Network tab open to monitor API calls

---

## Test Scenarios

### Test 1: Travel Mode Clarifying Question

**Objective**: Verify that system asks about travel mode after city and duration are provided.

#### Test Steps:

1. **Initial Planning Request**
   ```
   User: "I want to plan a 2 day trip to Chennai"
   ```

2. **Expected Flow**:
   - System asks: "Which city would you like to visit?"
   - User: "Chennai"
   - System asks: "How many days would you like to spend on this trip?"
   - User: "2"
   - **NEW**: System asks: "How are you traveling to the destination? (road/airplane/railway)"

3. **Test Travel Mode Responses**:

   **Test 1.1: Road Travel**
   ```
   User: "road"
   Expected: Starting point should be "Chennai Central Railway Station"
   ```

   **Test 1.2: Airplane Travel**
   ```
   User: "airplane"
   Expected: Starting point should be "Chennai Airport"
   ```

   **Test 1.3: Railway Travel**
   ```
   User: "railway"
   Expected: Starting point should be "Chennai Central Railway Station"
   ```

   **Test 1.4: Alternative Phrasings**
   ```
   User: "by car" → should map to "road"
   User: "by flight" → should map to "airplane"
   User: "by train" → should map to "railway"
   ```

#### Validation Points:
- [ ] System asks travel mode question after city and duration are known
- [ ] Travel mode is correctly extracted from user input
- [ ] Starting point is set correctly based on travel mode
- [ ] Starting point appears in itinerary JSON response

#### Backend Validation:
Check API response in Network tab:
```json
{
  "status": "success",
  "itinerary": {
    "travel_mode": "road|airplane|railway",
    "starting_point": "[City] Central Railway Station" OR "[City] Airport",
    ...
  }
}
```

---

### Test 2: Travel Dates Clarifying Question

**Objective**: Verify that system asks for travel dates and displays them correctly.

#### Test Steps:

1. **After Travel Mode Question**
   ```
   System asks: "What are your travel dates? (Please provide start date, e.g., January 25, 2026)"
   ```

2. **Test Date Formats**:

   **Test 2.1: Full Date Format**
   ```
   User: "January 25, 2026"
   Expected: travel_dates = ["2026-01-25", "2026-01-26"] (for 2-day trip)
   ```

   **Test 2.2: Numeric Date Format**
   ```
   User: "01/25/2026"
   Expected: travel_dates = ["2026-01-25", "2026-01-26"]
   ```

   **Test 2.3: ISO Date Format**
   ```
   User: "2026-01-25"
   Expected: travel_dates = ["2026-01-25", "2026-01-26"]
   ```

   **Test 2.4: Date Range**
   ```
   User: "January 25 to January 26, 2026"
   Expected: travel_dates = ["2026-01-25", "2026-01-26"]
   ```

3. **Verify Date Display in Frontend**:
   - Open itinerary tab
   - Day tabs should show: "Jan 25, 2026" and "Jan 26, 2026" instead of "Day 1" and "Day 2"
   - Check if dates are formatted correctly (MMM DD, YYYY)

#### Validation Points:
- [ ] System asks for travel dates after travel mode is provided
- [ ] Dates are correctly parsed from various formats
- [ ] Full date list is generated for multi-day trips
- [ ] Frontend displays actual dates in day tabs
- [ ] Dates persist in itinerary JSON

#### Backend Validation:
Check API response:
```json
{
  "itinerary": {
    "travel_dates": ["2026-01-25", "2026-01-26"],
    ...
  }
}
```

#### Frontend Validation:
- Inspect day tab buttons in browser DevTools
- Should show formatted dates like "Jan 25, 2026"
- Check `getDayDate()` function output in console

---

### Test 3: Complete Flow Test (All Clarifying Questions)

**Objective**: Test the complete flow from initial request to itinerary generation.

#### Test Steps:

1. **Complete Conversation Flow**:
   ```
   User: "I want to plan a trip to Chennai"
   
   System: "Which city would you like to visit?"
   User: "Chennai"
   
   System: "How many days would you like to spend on this trip?"
   User: "2"
   
   System: "How are you traveling to the destination? (road/airplane/railway)"
   User: "airplane"
   
   System: "What are your travel dates? (Please provide start date, e.g., January 25, 2026)"
   User: "January 25, 2026"
   
   System: [Generates itinerary]
   ```

2. **Expected Itinerary Structure**:
   ```json
   {
     "city": "Chennai",
     "duration_days": 2,
     "travel_mode": "airplane",
     "travel_dates": ["2026-01-25", "2026-01-26"],
     "starting_point": "Chennai Airport",
     "day_1": {...},
     "day_2": {...}
   }
   ```

#### Validation Points:
- [ ] All clarifying questions are asked in correct order
- [ ] System proceeds to itinerary generation after all required info is collected
- [ ] Itinerary includes all new fields (travel_mode, travel_dates, starting_point)
- [ ] Frontend displays dates correctly

---

### Test 4: Activity Data Completeness

**Objective**: Verify that all activities have complete data (duration, location, opening_hours).

#### Test Steps:

1. **Generate an Itinerary**:
   - Complete the planning flow as in Test 3
   - Wait for itinerary generation

2. **Inspect Activity Data**:
   - Open browser DevTools → Network tab
   - Find the `/api/chat` response with itinerary
   - Expand `itinerary.day_1.morning.activities[0]`

3. **Check Each Activity**:

   **Required Fields:**
   - `duration_minutes`: Must be > 0 (typically 60, 90, 120)
   - `location`: Must have `lat` and `lon` (both numbers)
   - `opening_hours`: Should be present if available from POI (optional but preferred)

   **Optional Fields:**
   - `source_id`: Should be present (e.g., "way:123456")
   - `category`: Should be present (e.g., "historical", "restaurant")
   - `description`: Should be present if available

#### Validation Checklist:

For each activity in itinerary:
- [ ] `duration_minutes` is present and > 0
- [ ] `location.lat` is present and is a valid number
- [ ] `location.lon` is present and is a valid number
- [ ] `opening_hours` is present (if available in POI data)
- [ ] `source_id` is present
- [ ] `category` is present
- [ ] `time` field is present and formatted correctly (e.g., "09:00 - 10:30")

#### Test Multiple Activities:
- Check morning activities
- Check afternoon activities
- Check evening activities
- Check activities across multiple days

#### Sample Validation Script:

Run in browser console after itinerary is loaded:
```javascript
// Get itinerary from Redux/state or DOM
const itinerary = // ... get from your state management

function validateActivity(activity, dayNum, timeBlock, index) {
  const issues = [];
  
  if (!activity.duration_minutes || activity.duration_minutes === 0) {
    issues.push(`Duration is 0 or missing`);
  }
  
  if (!activity.location || !activity.location.lat || !activity.location.lon) {
    issues.push(`Location is missing or incomplete`);
  }
  
  if (!activity.opening_hours) {
    issues.push(`Opening hours not specified (may be OK)`);
  }
  
  if (issues.length > 0) {
    console.error(`Day ${dayNum} ${timeBlock} Activity ${index} (${activity.activity}):`, issues);
    return false;
  }
  
  console.log(`✓ Day ${dayNum} ${timeBlock} Activity ${index} (${activity.activity}): All required fields present`);
  return true;
}

// Validate all activities
Object.keys(itinerary).forEach(dayKey => {
  if (dayKey.startsWith('day_')) {
    const dayNum = dayKey.split('_')[1];
    const day = itinerary[dayKey];
    
    ['morning', 'afternoon', 'evening'].forEach(timeBlock => {
      if (day[timeBlock] && day[timeBlock].activities) {
        day[timeBlock].activities.forEach((activity, idx) => {
          validateActivity(activity, dayNum, timeBlock, idx);
        });
      }
    });
  }
});
```

---

### Test 5: Frontend Date Display

**Objective**: Verify that dates are displayed correctly in the UI.

#### Test Steps:

1. **Generate Itinerary with Dates**:
   - Complete planning flow with travel dates
   - Navigate to Itinerary tab

2. **Visual Inspection**:
   - Day tabs should show formatted dates: "Jan 25, 2026", "Jan 26, 2026"
   - Not "Day 1", "Day 2"

3. **Test Edge Cases**:

   **Test 5.1: No Dates Provided**
   - Generate itinerary without travel dates
   - Should fallback to "Day 1", "Day 2"

   **Test 5.2: Invalid Date Format**
   - If backend sends invalid date, should gracefully fallback to "Day N"

   **Test 5.3: Single Day Trip**
   - Plan 1-day trip
   - Should show single date: "Jan 25, 2026"

#### Validation Points:
- [ ] Day tabs display formatted dates when available
- [ ] Date format is correct (MMM DD, YYYY)
- [ ] Fallback to "Day N" works when dates are missing
- [ ] Dates update correctly when itinerary is edited

---

### Test 6: Itinerary Editing with New Fields

**Objective**: Verify that new fields persist after editing.

#### Test Steps:

1. **Generate Itinerary**:
   - Complete planning flow with travel_mode and travel_dates

2. **Perform Edit**:
   ```
   User: "Swap Day 1 and Day 2"
   ```

3. **Verify Persistence**:
   - Check that `travel_mode`, `travel_dates`, `starting_point` are still present
   - Verify dates are still displayed correctly in frontend

#### Validation Points:
- [ ] travel_mode persists after edit
- [ ] travel_dates persist after edit
- [ ] starting_point persists after edit
- [ ] Date display remains correct after edit

---

### Test 7: Backend API Validation

**Objective**: Verify backend correctly handles all new fields.

#### API Endpoint: `POST /api/chat`

#### Test Request:
```json
{
  "message": "I want to plan a 2 day trip to Chennai",
  "session_id": "test-session-123"
}
```

#### Expected Response Flow:

**Response 1: Clarifying Question (City)**
```json
{
  "status": "clarifying",
  "message": "Which city would you like to visit?",
  "question": "Which city would you like to visit?",
  "session_id": "test-session-123"
}
```

**Response 2: Clarifying Question (Duration)**
```json
{
  "status": "clarifying",
  "message": "How many days would you like to spend on this trip?",
  "session_id": "test-session-123"
}
```

**Response 3: Clarifying Question (Travel Mode)**
```json
{
  "status": "clarifying",
  "message": "How are you traveling to the destination? (road/airplane/railway)",
  "session_id": "test-session-123"
}
```

**Response 4: Clarifying Question (Travel Dates)**
```json
{
  "status": "clarifying",
  "message": "What are your travel dates? (Please provide start date, e.g., January 25, 2026)",
  "session_id": "test-session-123"
}
```

**Response 5: Success with Itinerary**
```json
{
  "status": "success",
  "message": "I've created a 2-day itinerary for Chennai...",
  "itinerary": {
    "city": "Chennai",
    "duration_days": 2,
    "travel_mode": "airplane",
    "travel_dates": ["2026-01-25", "2026-01-26"],
    "starting_point": "Chennai Airport",
    "day_1": {
      "morning": {
        "activities": [
          {
            "activity": "Activity Name",
            "duration_minutes": 90,
            "location": {"lat": 13.0827, "lon": 80.2707},
            "opening_hours": "Mo-Su 09:00-18:00",
            "source_id": "way:123456",
            "time": "09:00 - 10:30",
            ...
          }
        ]
      },
      ...
    },
    ...
  },
  "sources": [...],
  "session_id": "test-session-123"
}
```

#### Validation:
- [ ] All clarifying questions are returned with correct status
- [ ] Itinerary response includes all new fields
- [ ] Activities have complete data (duration, location, opening_hours)
- [ ] Response structure matches expected format

---

## Test Data

### Sample Test Cities
- Chennai (India)
- Mumbai (India)
- Jaipur (India)
- New Delhi (India)

### Sample Date Formats to Test
- "January 25, 2026"
- "Jan 25, 2026"
- "01/25/2026"
- "25-01-2026"
- "2026-01-25"

### Sample Travel Modes to Test
- "road", "car", "bus", "drive"
- "airplane", "flight", "air", "plane"
- "railway", "train", "rail"

---

## Validation Checklist

### Pre-Planning Phase
- [ ] System asks for city
- [ ] System asks for duration
- [ ] **NEW**: System asks for travel mode
- [ ] **NEW**: System asks for travel dates

### Planning Phase
- [ ] Itinerary is generated successfully
- [ ] **NEW**: `travel_mode` is set in itinerary
- [ ] **NEW**: `travel_dates` array is populated
- [ ] **NEW**: `starting_point` is set correctly based on travel mode

### Activity Data
- [ ] All activities have `duration_minutes` > 0
- [ ] All activities have `location` with `lat` and `lon`
- [ ] Activities have `opening_hours` when available from POI
- [ ] Activities have `source_id`
- [ ] Activities have `category`
- [ ] Activities have `time` field

### Frontend Display
- [ ] **NEW**: Day tabs show formatted dates instead of "Day 1", "Day 2"
- [ ] Dates are formatted correctly (MMM DD, YYYY)
- [ ] Activities are displayed correctly
- [ ] All activity details are visible when expanded

### Post-Editing
- [ ] New fields persist after edits
- [ ] Date display remains correct after edits
- [ ] Activity data remains complete after edits

---

## Troubleshooting

### Issue: Travel mode question not asked

**Possible Causes:**
1. City or duration not properly extracted
2. Clarifying question logic not triggered

**Debug Steps:**
1. Check backend logs for preference extraction
2. Verify `_check_missing_info()` returns "travel_mode"
3. Check if `can_ask_clarifying_question()` returns true

**Fix:**
- Ensure city and duration are set before travel_mode question
- Check `MAX_CLARIFYING_QUESTIONS` setting

---

### Issue: Dates not displayed in frontend

**Possible Causes:**
1. `travel_dates` not in itinerary JSON
2. Frontend date formatting function error
3. Date parsing error

**Debug Steps:**
1. Check browser console for errors
2. Verify `itinerary.travel_dates` exists in API response
3. Test `getDayDate()` function in console

**Fix:**
- Ensure backend includes `travel_dates` in itinerary
- Check date format in `ItineraryView.tsx`
- Verify date parsing handles all formats

---

### Issue: Activities missing duration/location/opening_hours

**Possible Causes:**
1. POI data doesn't have opening_hours
2. Enrichment function not called
3. LLM not generating complete activities

**Debug Steps:**
1. Check backend logs for "Enriched activity" messages
2. Verify POI data includes all fields
3. Check `_enrich_activity_with_poi_data()` is called

**Fix:**
- Ensure enrichment function runs after LLM generation
- Check POI search returns complete data
- Verify enrichment copies all POI fields

---

### Issue: Starting point not set correctly

**Possible Causes:**
1. Travel mode not extracted correctly
2. City name not available when setting starting point

**Debug Steps:**
1. Check `preferences.get("travel_mode")` in logs
2. Verify city name is normalized correctly
3. Check starting point logic in `plan_trip()`

**Fix:**
- Ensure travel mode extraction handles all variations
- Verify city name is available when setting starting point
- Check starting point logic matches travel mode

---

## Automated Testing

### Run Activity Data Completeness Test

```bash
# From project root
cd backend
python ../tests/test_activity_data_completeness.py
```

### Expected Output:
- ✅ All activities have duration > 0
- ✅ All activities have location with lat/lon
- ✅ Activities have opening_hours when available
- ✅ Test passes with no critical issues

---

## Test Report Template

### Test Execution Report

**Date**: _____________  
**Tester**: _____________  
**Environment**: Frontend (localhost:3000) / Backend (localhost:8000)

#### Test Results Summary

| Test Scenario | Status | Notes |
|--------------|--------|-------|
| Travel Mode Question | ⬜ Pass / ⬜ Fail | |
| Travel Dates Question | ⬜ Pass / ⬜ Fail | |
| Starting Point Logic | ⬜ Pass / ⬜ Fail | |
| Date Display | ⬜ Pass / ⬜ Fail | |
| Activity Data Completeness | ⬜ Pass / ⬜ Fail | |
| Complete Flow | ⬜ Pass / ⬜ Fail | |

#### Issues Found

1. **Issue**: _____________  
   **Severity**: High / Medium / Low  
   **Status**: Open / Fixed  
   **Notes**: _____________

2. **Issue**: _____________  
   **Severity**: High / Medium / Low  
   **Status**: Open / Fixed  
   **Notes**: _____________

#### Recommendations

- _____________
- _____________
- _____________

---

## Additional Notes

- All date calculations assume UTC timezone
- Date formatting uses browser's locale settings
- Activity enrichment happens after LLM generation to ensure data completeness
- Starting point logic uses city name from preferences, not normalized name

---

**End of Test Guide**
