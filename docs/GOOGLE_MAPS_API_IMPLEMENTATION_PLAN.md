# Google Maps API Implementation Plan

## Overview

Integrate Google Maps Directions API as the primary travel time calculation service, with OSRM as the fallback when Google Maps API fails, exceeds limits, or throws errors.

---

## Objectives

1. **Primary Service**: Google Maps Directions API for accurate travel time calculations
2. **Fallback Service**: OSRM (Open Source Routing Machine) when Google Maps fails
3. **Seamless Integration**: No breaking changes to existing code
4. **Cost Management**: Track usage and gracefully handle rate limits

---

## Implementation Strategy

### Architecture

```
calculate_travel_time()
    ↓
Try Google Maps Directions API (if API key configured)
    ↓
    Success? → Return Google Maps result
    ↓
    Failure? → Fallback to OSRM
        ↓
        Success? → Return OSRM result
        ↓
        Failure? → Fallback to distance-based estimation
```

---

## Changes Required

### 1. Configuration (`backend/src/utils/config.py`)
- Add `google_maps_api_key: Optional[str]` field
- Make it optional (not required for application startup)

### 2. Travel Time Module (`backend/src/data_sources/travel_time.py`)
- Add `calculate_travel_time_google_maps()` function
- Update `calculate_travel_time()` to try Google Maps first
- Add proper error handling and rate limit detection
- Maintain existing OSRM fallback

### 3. Environment Configuration (`backend/env.example`)
- Add `GOOGLE_MAPS_API_KEY` example entry

### 4. Dependencies (`backend/requirements.txt`)
- No additional dependencies needed (using `requests` library)

---

## Implementation Details

### Google Maps Directions API Integration

#### API Endpoint
```
https://maps.googleapis.com/maps/api/directions/json
```

#### Request Parameters
- `origin`: "{lat},{lng}"
- `destination`: "{lat},{lng}"
- `mode`: "driving", "walking", "bicycling", or "transit"
- `key`: API key from environment variable
- `alternatives`: false (we only need the primary route)

#### Response Parsing
- Extract `routes[0].legs[0].duration.value` (duration in seconds)
- Extract `routes[0].legs[0].distance.value` (distance in meters)
- Convert to minutes and kilometers for consistency

#### Error Handling
- **OVER_QUERY_LIMIT**: Rate limit exceeded → Fallback to OSRM
- **REQUEST_DENIED**: Invalid API key → Fallback to OSRM
- **INVALID_REQUEST**: Invalid parameters → Fallback to OSRM
- **UNKNOWN_ERROR**: Temporary error → Fallback to OSRM
- Network errors → Fallback to OSRM

---

## Function Signatures

### New Function: `calculate_travel_time_google_maps()`

```python
def calculate_travel_time_google_maps(
    origin: Dict[str, float],
    destination: Dict[str, float],
    mode: str = "driving"
) -> Optional[Dict[str, Any]]:
    """
    Calculate travel time using Google Maps Directions API.
    
    Args:
        origin: Dict with 'lat' and 'lon' keys
        destination: Dict with 'lat' and 'lon' keys
        mode: Travel mode ('driving', 'walking', 'bicycling', 'transit')
    
    Returns:
        Dictionary with travel time and distance info, or None if API fails
    """
```

### Updated Function: `calculate_travel_time()`

```python
def calculate_travel_time(
    origin: Dict[str, float],
    destination: Dict[str, float],
    mode: str = "walking"
) -> Dict[str, Any]:
    """
    Calculate travel time between two locations.
    Tries Google Maps API first (if configured), falls back to OSRM, 
    then to distance-based estimation.
    
    Priority: Google Maps → OSRM → Distance Estimation
    """
```

---

## Error Handling Strategy

### Google Maps API Errors

| Error Code | Meaning | Action |
|------------|---------|--------|
| `OVER_QUERY_LIMIT` | Rate limit exceeded | Fallback to OSRM, log warning |
| `REQUEST_DENIED` | Invalid API key | Fallback to OSRM, log warning |
| `INVALID_REQUEST` | Invalid parameters | Fallback to OSRM, log warning |
| `UNKNOWN_ERROR` | Server error | Fallback to OSRM, log warning |
| `ZERO_RESULTS` | No route found | Fallback to OSRM |
| Network Error | Connection failed | Fallback to OSRM |

### Logging

- **INFO**: Using Google Maps API for travel time calculation
- **WARNING**: Google Maps API failed, falling back to OSRM (with reason)
- **DEBUG**: Detailed API request/response information

---

## Mode Mapping

### Travel Mode Conversion

| Current Mode | Google Maps Mode | OSRM Profile |
|--------------|------------------|--------------|
| `walking` | `walking` | `walking` |
| `driving` | `driving` | `driving` |
| `public_transit` | `transit` | `driving` (fallback) |
| `cycling` | `bicycling` | `cycling` |

---

## Testing Strategy

### Unit Tests
1. Test Google Maps API success case
2. Test fallback to OSRM when API key missing
3. Test fallback to OSRM on rate limit error
4. Test fallback to OSRM on invalid request
5. Test fallback to distance estimation when both APIs fail

### Integration Tests
1. Test with valid Google Maps API key
2. Test with invalid Google Maps API key
3. Test with no API key (should use OSRM)
4. Test with network failure (should fallback)

---

## Rate Limit Considerations

### Google Maps API Limits
- **Free Tier**: 10,000 requests/month
- **Rate Limit**: 60,000 elements/minute (Distance Matrix)
- **Rate Limit**: Varies by account (Directions API)

### Handling Strategy
1. Catch `OVER_QUERY_LIMIT` errors
2. Immediately fallback to OSRM
3. Log warning for monitoring
4. Continue using OSRM for remaining requests

### Cost Monitoring
- Log Google Maps API usage (optional)
- Track free tier usage
- Alert when approaching limits (future enhancement)

---

## Migration Path

### Phase 1: Implementation (Current)
- Add Google Maps API support
- Keep OSRM as fallback
- Make API key optional

### Phase 2: Monitoring (Future)
- Add usage tracking
- Monitor costs
- Set up alerts for quota limits

### Phase 3: Optimization (Future)
- Implement caching for repeated routes
- Batch requests where possible
- Add retry logic with exponential backoff

---

## Configuration

### Environment Variable

```bash
# Google Maps API (Optional - falls back to OSRM if not set)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

### Settings Class

```python
google_maps_api_key: Optional[str] = Field(None, env="GOOGLE_MAPS_API_KEY")
```

---

## File Changes Summary

### Files to Modify
1. `backend/src/utils/config.py` - Add Google Maps API key configuration
2. `backend/src/data_sources/travel_time.py` - Add Google Maps integration
3. `backend/env.example` - Add Google Maps API key example

### Files to Create
- None (implementation in existing files)

### Dependencies
- No new dependencies required (using existing `requests` library)

---

## Success Criteria

1. ✅ Google Maps API is used when API key is configured
2. ✅ OSRM fallback works when Google Maps fails
3. ✅ No breaking changes to existing functionality
4. ✅ Proper error handling and logging
5. ✅ Travel time calculations work correctly
6. ✅ System works with or without Google Maps API key

---

## Getting a Google Maps API Key

### Steps
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Directions API" and "Distance Matrix API"
4. Go to "Credentials" → "Create Credentials" → "API Key"
5. (Optional) Restrict API key to specific APIs and IPs
6. Copy API key to `.env` file

### Free Tier
- 10,000 free requests/month per API
- No credit card required (with billing account setup)
- Pay-as-you-go after free tier

---

## Rollout Plan

### Step 1: Implementation
- Implement Google Maps API integration
- Add configuration and error handling

### Step 2: Testing
- Test with valid API key
- Test without API key (fallback)
- Test error scenarios

### Step 3: Deployment
- Deploy to development environment
- Monitor logs and errors
- Verify fallback behavior

### Step 4: Production
- Deploy to production
- Monitor usage and costs
- Adjust if needed

---

## Future Enhancements

1. **Caching**: Cache Google Maps API responses for repeated routes
2. **Batching**: Use Distance Matrix API for batch calculations
3. **Traffic Data**: Use real-time traffic data from Google Maps
4. **Transit Data**: Better support for public transit routes
5. **Cost Tracking**: Track API usage and costs
6. **Quota Alerts**: Alert when approaching free tier limits

---

## Notes

- Google Maps API key is **optional** - system works without it
- OSRM remains as a reliable free fallback
- No breaking changes to existing code
- All travel time calculations maintain backward compatibility
