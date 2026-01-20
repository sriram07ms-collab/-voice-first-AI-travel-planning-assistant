# Testing Google Maps API Integration Locally

This guide will help you test the Google Maps API (Google Places) integration locally.

## Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Maps API Key** with the following APIs enabled:
   - Places API (New)
   - Geocoding API
   - Maps JavaScript API (optional, for frontend)

## Step 1: Get Google Maps API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the required APIs:
   - Go to **APIs & Services** > **Library**
   - Search for "Places API (New)" and enable it
   - Search for "Geocoding API" and enable it
4. Create an API key:
   - Go to **APIs & Services** > **Credentials**
   - Click **Create Credentials** > **API Key**
   - Copy your API key
   - (Optional) Restrict the API key to specific APIs for security

## Step 2: Set Up Environment Variables

### Option A: Using `.env` file (Recommended)

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Copy the example env file if you don't have one:
   ```bash
   cp env.example .env
   ```

3. Edit `.env` file and add your Google Maps API key:
   ```env
   GOOGLE_MAPS_API_KEY=your_actual_api_key_here
   ```

### Option B: Using Environment Variables Directly

**Windows (PowerShell):**
```powershell
$env:GOOGLE_MAPS_API_KEY="your_actual_api_key_here"
```

**Windows (CMD):**
```cmd
set GOOGLE_MAPS_API_KEY=your_actual_api_key_here
```

**Linux/Mac:**
```bash
export GOOGLE_MAPS_API_KEY="your_actual_api_key_here"
```

## Step 3: Install Dependencies

Make sure you have all required Python packages:

```bash
cd backend
pip install -r requirements.txt
```

## Step 4: Run the Backend Server

### Option A: Using Python directly

```bash
cd backend/src
python main.py
```

The server should start on `http://localhost:8000`

### Option B: Using uvicorn directly

```bash
cd backend
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### Verify Backend is Running

Test the health endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

## Step 5: Test Google Places API Integration

### Method 1: Using the Test Script

Run the Chennai POI search test script:

```bash
cd scripts
python test_poi_search_chennai.py
```

This will test POI search for Chennai and show which API is being used.

### Method 2: Test via API Endpoint

Test the POI search directly via the API:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Plan a 2-day trip to Chennai. I like food.",
    "session_id": "test-session-123"
  }'
```

### Method 3: Test via Frontend

1. Start the frontend (if not already running):
   ```bash
   cd frontend
   npm run dev
   ```

2. Open `http://localhost:3000` in your browser

3. Try planning a trip:
   - Type or say: "Plan a 2-day trip to Chennai. I like food."
   - Watch the console logs to see which API is being used

## Step 6: Verify Google Places API is Being Used

### Check Backend Logs

When you make a POI search request, you should see logs like:

**If Google Maps API key is configured:**
```
✅ Google Maps API key is configured, using Google Places API for Chennai
🔍 Searching POIs for Chennai - PRIORITY: Google Places API first
✅ Google Places API returned 20 POIs for Chennai (20 with google_places data_source)
📊 Sample POI: Saravana Bhavan (data_source: google_places, duration: 90min, rating: 4.5)
```

**If Google Maps API key is NOT configured:**
```
⚠️ Google Maps API key not configured. Set GOOGLE_MAPS_API_KEY environment variable to use Google Places API. Falling back to OpenStreetMap.
⚠️ Using OpenStreetMap/Overpass API (Google Places API not configured)
```

### Check Response Data Source

When Google Places API is used, the POIs will have:
- `data_source: "google_places"`
- `source_id: "place_id:ChIJ..."` (Google Place ID format)
- `rating: 4.5` (Google Places rating)

When OpenStreetMap is used, the POIs will have:
- `data_source: "openstreetmap"`
- `source_id: "node:123456"` or `"way:123456"` (OSM format)

## Step 7: Test Different Cities

Test with various Indian cities to verify Google Places API works:

```bash
# Test Chennai
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a trip to Chennai. I like food.", "session_id": "test-1"}'

# Test Mumbai
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a trip to Mumbai. I like culture.", "session_id": "test-2"}'

# Test Jaipur
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a trip to Jaipur. I like shopping.", "session_id": "test-3"}'
```

## Troubleshooting

### Issue: "Google Maps API key not configured"

**Solution:**
- Make sure `GOOGLE_MAPS_API_KEY` is set in your `.env` file or environment variables
- Restart the backend server after setting the environment variable
- Check that the API key is valid and not expired

### Issue: "Google Places API returned no results"

**Possible causes:**
1. API key doesn't have Places API (New) enabled
2. API key has restrictions that block the request
3. Billing is not enabled on the Google Cloud project
4. API quota exceeded

**Solution:**
- Check Google Cloud Console > APIs & Services > Enabled APIs
- Verify billing is enabled
- Check API usage and quotas
- Try a different city to see if it's city-specific

### Issue: "Both Google Places and OpenStreetMap returned no POIs"

**Solution:**
- Check your internet connection
- Verify the city name is correct
- Try with a different city (e.g., "Mumbai" instead of "Chennai")
- Check backend logs for detailed error messages

### Issue: Still seeing OpenStreetMap errors

**Solution:**
- Verify the API key is correctly set: `echo $GOOGLE_MAPS_API_KEY` (Linux/Mac) or `echo %GOOGLE_MAPS_API_KEY%` (Windows)
- Check backend logs to see if Google Places API is being called
- Make sure you restarted the backend after setting the environment variable

## Expected Behavior

### With Google Maps API Key Configured:

1. **POI Search**: Uses Google Places API first
2. **Sources**: Shows `google_places` as data source
3. **Source URLs**: Uses Google Place IDs (e.g., `place_id:ChIJ...`)
4. **Error Messages**: Mentions "Google Places API" if it fails
5. **Fallback**: Only falls back to OpenStreetMap if Google Places fails

### Without Google Maps API Key:

1. **POI Search**: Uses OpenStreetMap directly
2. **Sources**: Shows `openstreetmap` as data source
3. **Source URLs**: Uses OSM format (e.g., `node:123456`)
4. **Error Messages**: Mentions "OpenStreetMap API"
5. **No Fallback**: Directly uses OpenStreetMap

## Next Steps

Once Google Places API is working:

1. **Test Itinerary Generation**: Plan a complete trip and verify sources
2. **Test PDF Generation**: Generate PDF and verify Google Places sources are included
3. **Test Source Links**: Click on source links to verify they point to Google Places
4. **Monitor API Usage**: Check Google Cloud Console for API usage and costs

## Additional Resources

- [Google Places API Documentation](https://developers.google.com/maps/documentation/places/web-service)
- [Google Cloud Console](https://console.cloud.google.com/)
- [API Key Best Practices](https://developers.google.com/maps/api-security-best-practices)
