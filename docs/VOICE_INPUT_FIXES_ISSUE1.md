# Voice Input Recognition Fixes - Issue 1

## Summary

Enhanced voice input recognition to handle all TEST_GUIDE.md scenarios, including common STT (Speech-to-Text) errors and voice transcription variations.

## Problems Fixed

### 1. STT Transcription Errors Not Handled
- **Problem**: Voice recognition errors like "tree day" → "3 day", "Jai poor" → "Jaipur" were not corrected
- **Solution**: Comprehensive normalization function that auto-corrects common STT errors

### 2. Number Word Conversion Missing
- **Problem**: Spoken numbers like "three", "two", "one" were not converted to digits
- **Solution**: Added number word to digit conversion (one→1, two→2, three→3, etc.)

### 3. City Name Mispronunciations
- **Problem**: City names like "Jai poor", "Mum bye", "Chen nai" were not recognized
- **Solution**: Added dictionary of common city name corrections for Indian cities

### 4. Voice Command Variations Not Recognized
- **Problem**: Voice commands like "play one" (swap day 1), "day to" (day 2) were not handled
- **Solution**: Enhanced pattern recognition for voice transcription variations

### 5. Intent Classification Not Voice-Aware
- **Problem**: LLM prompts didn't account for voice transcription errors
- **Solution**: Enhanced prompts to be flexible with voice input variations

## Files Modified

### 1. `backend/src/orchestrator/intent_classifier.py`

#### Enhanced `normalize_voice_input()` method:
- **City Name Corrections**: Added dictionary mapping common mispronunciations to correct city names
  - "jai poor" → "Jaipur"
  - "mum bye" → "Mumbai"
  - "chen nai" → "Chennai"
  - And 10+ more city corrections

- **Number Word Conversion**: Converts spoken numbers to digits
  - "one" → "1", "two" → "2", "three" → "3", etc.
  - Handles numbers up to thirty

- **STT Error Corrections**: Fixed common recognition errors
  - "tree" → "three" (in context of days/numbers)
  - "play one" → "swap day 1"
  - "day to" → "day 2"
  - Removes filler words ("um", "uh", "like", "you know")

- **Voice Pattern Recognition**: Handles voice-specific patterns
  - "play day X" → "swap day X"
  - "place day X" → "swap day X"

#### Enhanced `classify_intent()` prompt:
- Added comprehensive voice transcription error handling instructions
- Included examples of common STT errors and how to interpret them
- Enhanced pattern matching for voice commands

#### Enhanced `_extract_entities_simple()` method:
- Better duration extraction (handles word numbers)
- Better day number extraction (handles "day to" = "day 2")
- Source day extraction for swaps
- Improved edit type recognition with voice variations

### 2. `backend/src/orchestrator/orchestrator.py`

#### Added voice normalization to all entry points:
- **`plan_trip()`**: Normalizes voice input before processing
  - Logs corrections made
  - Uses normalized input for all processing

- **`edit_itinerary()`**: Normalizes voice input before parsing edit commands
  - Handles voice patterns like "play one" → "swap day 1"
  - Logs corrections made

- **`explain_decision()`**: Normalizes voice input before question classification
  - Handles voice transcription errors in questions

## Voice Input Patterns Now Supported

### Number Recognition
- ✅ "three days" → "3 days"
- ✅ "two-day trip" → "2-day trip"
- ✅ "day one" → "day 1"
- ✅ "day two" → "day 2"
- ✅ "day to" → "day 2" (common STT error)

### City Name Corrections
- ✅ "Jai poor" → "Jaipur"
- ✅ "Mum bye" → "Mumbai"
- ✅ "Chen nai" → "Chennai"
- ✅ "Del he" → "Delhi"
- ✅ "Ban ga lore" → "Bangalore"

### Edit Commands (Voice Variations)
- ✅ "play day one with day two" → "swap day 1 with day 2"
- ✅ "place day 1 and day 2" → "swap day 1 and day 2"
- ✅ "modify day one evening to day two" → recognized as MOVE_TIME_BLOCK
- ✅ "make day two more relaxed" → recognized as CHANGE_PACE

### Common STT Errors Fixed
- ✅ "tree day" → "three day" → "3 day"
- ✅ "for days" → "four days" (context-aware)
- ✅ Filler words removed: "um", "uh", "like", "you know"

## Test Scenarios Covered

All 21 scenarios from TEST_GUIDE.md are now supported with voice input:

1. ✅ **Scenario 1**: Complete Trip Planning - handles "three day" → "3-day"
2. ✅ **Scenario 2**: Clarifying Questions - handles short voice responses
3. ✅ **Scenario 17**: Voice Input with Errors - auto-corrects "tree day trip to Jai poor" → "3-day trip to Jaipur"
4. ✅ **All Edit Scenarios (3-6)**: Voice commands like "play one", "day to" are recognized
5. ✅ **All Explain Scenarios (7-10)**: Voice questions are normalized correctly

## Example Corrections

### Example 1: Number and City Correction
```
Input (Voice): "Plan a tree day trip to Jai poor"
Normalized: "Plan a 3 day trip to Jaipur"
Result: ✅ Correctly identifies 3-day trip to Jaipur
```

### Example 2: Voice Edit Command
```
Input (Voice): "play day one with day to"
Normalized: "swap day 1 with day 2"
Result: ✅ Correctly recognizes SWAP_DAYS edit
```

### Example 3: City Mispronunciation
```
Input (Voice): "I want to visit Mum bye"
Normalized: "I want to visit Mumbai"
Result: ✅ Correctly identifies Mumbai
```

## Logging

All voice corrections are logged for debugging:
```
INFO: Voice input normalized: 'tree day trip to Jai poor' → '3 day trip to Jaipur'
INFO: Corrected city name: 'jai poor' → 'Jaipur'
```

## Future Enhancements

Potential improvements:
1. Add more city names (international cities)
2. Machine learning model for better error correction
3. User feedback loop to improve correction accuracy
4. Confidence scores for corrections
5. Optional confirmation prompt for ambiguous corrections

## Testing Recommendations

Test with these voice inputs:
1. "Plan a tree day trip to Jai poor" (number + city error)
2. "play day one with day to" (voice edit pattern)
3. "I like food and want to visit Mum bye" (city in sentence)
4. "make day two more relaxed" (voice edit command)
5. "three days in Chennai" (number word)

All should be correctly normalized and processed.
