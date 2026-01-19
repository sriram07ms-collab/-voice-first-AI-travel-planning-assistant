# Google Places API POI Search Integration

## Overview

Integrated Google Places API (New) as the primary POI search service, with OpenStreetMap/Overpass API as the fallback when Google Places API fails, exceeds limits, or throws errors.

---

## Implementation Summary

### Architecture

```
search_pois() [Main Entry Point]
    ↓
Try Google Places API (if API key configured)
    ↓
    Success? → Return Google Places results
    ↓
    Failed/No Key? → Fallback to OpenStreetMap/Overpass API
        ↓
        Success? → Return Overpass results
        ↓
        Failed? → Return empty list
```

---

## Files Created

### 1. `backend/src/data_sources/google_places.py`
- New Google Places API integration module
- Uses Places API (New) - Text Search endpoint
- Maps interests to Google Places API place types
- Converts Google Places results to POI model format

### 2. `backend/src/data_sources/poi_search.py`
- Unified POI search entry point
- Tries Google Places API first
- Falls back to OpenStreetMap/Overpass API
- Maintains backward compatibility

---

## Files Modified

### 1. `backend/src/data_sources/openstreetmap.py`
- Renamed `search_pois()` → `search_pois_overpass()`
- Now serves as fallback implementation
- All existing Overpass logic preserved

### 2. `backend/src/data_sources/__init__.py`
- Exports new `search_pois()` from `poi_search.py`
- Exports `search_pois_google_places()` and `search_pois_overpass()`
- Maintains backward compatibility

### 3. `mcp-tools/poi-search/server.py`
- Updated to use unified `search_pois()` function
- Automatically uses Google Places first, Overpass fallback
- No breaking changes to MCP interface

### 4. `backend/src/utils/config.py`
- Already has `google_maps_api_key` configuration (from previous work)
- No changes needed

### 5. `backend/env.example`
- Already has `GOOGLE_MAPS_API_KEY` entry (from previous work)
- No changes needed

---

## Google Places API Details

### API Endpoint
```
POST https://places.googleapis.com/v1/places:searchText
```

### Request Format
- **Method**: POST with JSON body
- **Headers**: 
  - `Content-Type: application/json`
  - `X-Goog-Api-Key: {API_KEY}`
  - `X-Goog-FieldMask: places.id,places.displayName,...`

### Request Body
```json
{
  "textQuery": "restaurants in Chennai, India",
  "maxResultCount": 20,
  "locationBias": {
    "circle": {
      "center": {"latitude": 13.0827, "longitude": 80.2707},
      "radius": 10000.0
    }
  },
  "includedType": ["restaurant", "cafe"],
  "languageCode": "en"
}
```

### Response Format
```json
{
  "places": [
    {
      "id": "ChIJ...",
      "displayName": {"text": "Restaurant Name"},
      "location": {"latitude": 13.0827, "longitude": 80.2707},
      "types": ["restaurant", "food", "point_of_interest"],
      "rating": 4.5,
      "formattedAddress": "123 Main St, Chennai",
      "currentOpeningHours": {...}
    }
  ]
}
```

---

## Interest Mapping

### User Interests → Google Places Types

| User Interest | Google Places Types |
|---------------|---------------------|
| `food` | restaurant, cafe, meal_takeaway, bakery, food, meal_delivery |
| `culture` | museum, art_gallery, tourist_attraction, church, hindu_temple, mosque, synagogue, place_of_worship |
| `shopping` | shopping_mall, store, clothing_store, jewelry_store, supermarket |
| `nightlife` | bar, night_club, casino |
| `nature` | park, zoo, aquarium |
| `beaches` | beach |
| `religion` | place_of_worship, church, hindu_temple, mosque, synagogue |
| `historical` | tourist_attraction, museum, art_gallery |

### Google Places Types → Internal Categories

| Google Type | Internal Category |
|-------------|-------------------|
| restaurant, cafe, meal_takeaway, bakery | restaurant |
| museum, art_gallery | museum |
| tourist_attraction | attraction |
| shopping_mall, store, clothing_store | shopping |
| park, zoo, aquarium | park |
| bar, night_club, casino | nightlife |
| church, hindu_temple, mosque, synagogue | historical |
| beach | nature |

---

## Error Handling

### Google Places API Errors

| Error | Action |
|-------|--------|
| API key not configured | Skip Google Places, use Overpass |
| `REQUEST_DENIED` | Invalid API key → Fallback to Overpass |
| `OVER_QUERY_LIMIT` | Rate limit exceeded → Fallback to Overpass |
| `INVALID_REQUEST` | Invalid parameters → Fallback to Overpass |
| Network error | Connection failed → Fallback to Overpass |
| No results | Empty list → Fallback to Overpass |

### Fallback Behavior

- If Google Places returns empty list → Try Overpass
- If Google Places throws error → Try Overpass
- If both fail → Return empty list with warning

---

## Rate Limits & Costs

### Google Places API
- **Free Tier**: 10,000 requests/month (Text Search)
- **Rate Limit**: Varies by account
- **Cost**: ~$17 per 1,000 requests (after free tier)

### Overpass API
- **Free**: Unlimited (with rate limiting)
- **Rate Limit**: 1 request/second recommended
- **Cost**: $0

---

## Usage Flow

### Example: Search for "food" in Chennai

```
1. User: "Plan a trip to Chennai, I like food"
   ↓
2. System calls: search_pois(city="Chennai", interests=["food"])
   ↓
3. poi_search.py → search_pois_google_places()
   ↓
4. Google Places API called with:
   - textQuery: "restaurants in Chennai, India"
   - includedType: ["restaurant", "cafe", ...]
   - locationBias: circle around Chennai center
   ↓
5. Google Places returns 20 restaurants
   ↓
6. Results converted to POI objects
   ↓
7. Return to itinerary builder
```

### If Google Places Fails:

```
1. Google Places API returns error or empty
   ↓
2. poi_search.py → search_pois_overpass()
   ↓
3. OpenStreetMap/Overpass API called
   ↓
4. Results returned (if available)
```

---

## Testing

### Test with Google Places API Key

1. Ensure `GOOGLE_MAPS_API_KEY` is set in `.env`
2. Plan a trip: "Plan a 2-day trip to Chennai, I like food"
3. Check logs for: `"✅ Google Places API returned X POIs"`

### Test Fallback (No API Key)

1. Remove or comment out `GOOGLE_MAPS_API_KEY` in `.env`
2. Plan a trip: "Plan a 2-day trip to Chennai, I like food"
3. Check logs for: `"Google Places API key not configured, skipping Google Places API"`
4. Check logs for: `"✅ OpenStreetMap/Overpass API returned X POIs"`

---

## Benefits

### ✅ Advantages of Google Places API

1. **Better Coverage**: More comprehensive POI database
2. **Ratings & Reviews**: Includes user ratings and review counts
3. **Opening Hours**: Real-time opening hours data
4. **Addresses**: Formatted addresses included
5. **Price Levels**: Budget information available
6. **Reliability**: More stable than Overpass (less timeout issues)

### ✅ Fallback Benefits

1. **Cost-Free**: Overpass API is free and unlimited
2. **No API Key Required**: Works without Google Maps API key
3. **Backup Option**: Ensures POI search always works
4. **Global Coverage**: Overpass has good global coverage

---

## Configuration

### Required: Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable "Places API (New)" (not Legacy)
3. Create API key
4. Add to `.env`: `GOOGLE_MAPS_API_KEY=your_key_here`

### Optional: Overpass API Endpoints

Already configured in `openstreetmap.py`:
- Primary: `https://overpass-api.de/api/interpreter`
- Fallback: `https://overpass.kumi.systems/api/interpreter`
- Fallback: `https://lz4.overpass-api.de/api/interpreter`

---

## Logging

### Success Logs
```
INFO: Searching POIs for Chennai using Google Places API
INFO: Mapped interests ['food'] to Google Places types: ['restaurant', 'cafe', ...]
INFO: Google Places API returned 20 places
INFO: Parsed 20 POIs from Google Places API
INFO: ✅ Google Places API returned 20 POIs for Chennai
```

### Fallback Logs
```
DEBUG: Google Maps API key not configured, skipping Google Places API
INFO: Google Places API returned no results, falling back to OpenStreetMap/Overpass API
INFO: ✅ OpenStreetMap/Overpass API returned 15 POIs for Chennai
```

### Error Logs
```
WARNING: Google Places API returned status 403: API key not valid
INFO: Google Places API returned no results, falling back to OpenStreetMap/Overpass API
```

---

## Data Source Field

POIs now include `data_source` field:
- `"google_places"` - From Google Places API
- `"openstreetmap"` - From Overpass API

This helps track which API provided the data.

---

## Summary

✅ Google Places API integrated as primary POI search  
✅ OpenStreetMap/Overpass API as fallback  
✅ Unified `search_pois()` function maintains backward compatibility  
✅ All existing code continues to work  
✅ No breaking changes to MCP interface  
✅ Automatic fallback on errors or missing API key  
✅ Better POI coverage and data quality with Google Places  

The system now uses Google Places API by default when configured, with Overpass as a reliable free fallback! 🎉
