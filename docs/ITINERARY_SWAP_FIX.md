# Itinerary Swap & Edit Fix

## Problem
The itinerary swap functionality was not working correctly:
- "I want to swap day 1 itinerary with day 2" was not being recognized as a day swap
- Edit type was incorrectly identified as SWAP_ACTIVITY instead of SWAP_DAYS
- Edit correctness evaluator was flagging swaps as incorrect
- Response messages were generic instead of specific

## Root Causes

1. **Intent Classifier Override**: The intent classifier was detecting "swap" and setting edit_type to "SWAP_ACTIVITY", which was overriding the LLM's correct detection of "SWAP_DAYS"

2. **Insufficient Fallback Parsing**: The fallback parser didn't have robust patterns to detect day swaps

3. **Edit Correctness Evaluator**: The evaluator didn't understand that SWAP_DAYS should modify BOTH days, so it flagged swaps as incorrect

4. **Missing Validation**: No validation to ensure source_day and target_day were extracted correctly

## Solutions Applied

### 1. Enhanced LLM Prompt
- Added explicit examples for day swap patterns
- Made it clear that two day numbers + "swap" = SWAP_DAYS
- Added validation rules in the prompt

### 2. Improved Fallback Parser
- Added multiple regex patterns to detect day swaps:
  - "swap day X with day Y"
  - "swap day X itinerary with day Y"
  - "I want to swap day X with day Y"
  - "swap day X and day Y"
- Added pattern to extract both day numbers when swap is mentioned

### 3. Smart Merge Logic
- Prevents overriding SWAP_DAYS or MOVE_TIME_BLOCK from LLM
- Only merges intent classifier results if LLM didn't detect complex edit types
- Added validation to extract day numbers from description if missing

### 4. Fixed Edit Correctness Evaluator
- Updated `verify_edit_scope()` to handle SWAP_DAYS correctly
- Recognizes that both source_day and target_day should be modified
- Handles MOVE_TIME_BLOCK correctly (both days may be modified)
- No longer flags swaps as incorrect

### 5. Enhanced Swap Function
- Added comprehensive validation
- Added verification that swap actually occurred
- Better error messages and logging
- Type checking for day numbers

### 6. Improved Logging
- Added detailed logging for swap operations
- Logs when SWAP_DAYS is detected
- Logs validation failures
- Verifies swap was successful

## Supported Swap Commands

### Day Swaps (Entire Day)
- ✅ "I want to swap day 1 itinerary with day 2"
- ✅ "swap day 1 and day 2"
- ✅ "swap Day 1 itinerary to Day 2 and vice versa"
- ✅ "swap day 1 with day 2"
- ✅ "swap day 1 to day 2"

### Time Block Swaps
- ✅ "move Day 1 evening to Day 2 evening"
- ✅ "swap Day 1 evening with Day 2 evening"
- ✅ "Day 1 evening in Day 2 evening"

### Time Block Moves with Regeneration
- ✅ "move Day 2 evening to Day 1 evening and plan something new for Day 2 evening"
- ✅ "I need to Day 2 evening in Day 1 evening and plan something new in Day 2 evening"

## How It Works Now

### Step 1: Parse Command
1. Intent classifier provides initial classification
2. LLM parses with detailed prompt (detects SWAP_DAYS)
3. Fallback parser handles edge cases
4. Smart merge prevents overriding complex edit types

### Step 2: Validate
1. Checks if source_day and target_day are present
2. Extracts from description if missing
3. Validates day numbers are integers
4. Verifies days exist in itinerary

### Step 3: Apply Swap
1. Creates deep copy of itinerary
2. Swaps entire day data structures
3. Verifies swap was successful
4. Logs the operation

### Step 4: Evaluate
1. Edit correctness evaluator checks both days were modified
2. Recognizes this is expected for SWAP_DAYS
3. No longer flags as incorrect

### Step 5: Respond
1. Generates specific message: "I've swapped Day X and Day Y"
2. No warning message if swap was correct
3. Updates session with swapped itinerary

## Testing

To test the swap functionality:

```python
# Test parsing
python scripts/test_swap_parsing.py

# Or test via API
curl -X POST http://localhost:8000/api/edit \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session",
    "message": "I want to swap day 1 itinerary with day 2"
  }'
```

## Verification Checklist

After making a swap request:
- [ ] Check backend logs for "✅ Parsed SWAP_DAYS"
- [ ] Check logs for "✅ Successfully swapped Day X with Day Y"
- [ ] Verify response message says "I've swapped Day X and Day Y"
- [ ] Verify no "unexpected sections" warning
- [ ] Check itinerary in session - days should be swapped
- [ ] Verify PDF generation uses swapped itinerary

## Common Issues & Fixes

### Issue: Still getting "I've updated Day X" instead of "I've swapped..."

**Cause**: Edit type not correctly identified as SWAP_DAYS

**Fix**: 
1. Check backend logs for parsed edit command
2. Verify edit_type is "SWAP_DAYS"
3. Verify source_day and target_day are both present
4. Check if fallback parser is being used (look for "using fallback")

### Issue: "Some unexpected sections may have been modified"

**Cause**: Edit correctness evaluator flagging swap as incorrect

**Fix**: 
- This should be fixed now with the updated evaluator
- If still happening, check that both days are in modified_sections
- Verify edit_type is correctly set to SWAP_DAYS

### Issue: Swap not happening

**Cause**: Days not found or validation failing

**Fix**:
1. Check logs for "One or both days not found"
2. Verify itinerary has day_1, day_2, etc.
3. Check if day numbers are being extracted correctly
4. Look for validation errors in logs

---

**Last Updated**: 2024-01-17  
**Status**: ✅ Fixed
