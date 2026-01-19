# n8n Itinerary Data Extraction Fix

## Problem
The email was being sent but was empty - no itinerary content and no PDF attachment. This was caused by incorrect data extraction from the webhook payload.

## Solution
Updated the "Generate HTML" node in the workflow to better handle different data structures from the webhook.

### Changes Made

1. **Improved Data Extraction**:
   - Added multiple fallback methods to extract data from webhook
   - Handles cases where data might be nested in `body` or `json` properties
   - Added debug logging to help diagnose issues

2. **Better Error Handling**:
   - Added check for empty itinerary
   - Shows helpful error message if itinerary data is malformed
   - Logs data structure for debugging

## How to Apply the Fix

### Step 1: Update the Workflow in n8n

1. **Open your n8n instance**: https://msriram.app.n8n.cloud
2. **Open the workflow**: "Travel Itinerary PDF & Email"
3. **Click on the "Generate HTML" node** (Code node)
4. **Replace the JavaScript code** with the updated code from `n8n-workflows/pdf-email-workflow.json`

   OR

5. **Re-import the workflow**:
   - In n8n, go to Workflows
   - Click "Import from File"
   - Select `n8n-workflows/pdf-email-workflow.json`
   - This will replace your current workflow

### Step 2: Verify the Workflow

1. **Check the "Generate HTML" node**:
   - Should have the updated data extraction code
   - Should include debug logging

2. **Activate the workflow**:
   - Toggle to **Active** (green)
   - Ensure webhook is enabled

### Step 3: Test

1. **Generate a test itinerary** in your app
2. **Click "Generate PDF & Send Email"**
3. **Check the email** - should now contain:
   - Full itinerary content
   - PDF attachment

## Debugging

If the issue persists:

1. **Check n8n Execution Logs**:
   - Go to n8n → Executions
   - Find the failed execution
   - Click on "Generate HTML" node
   - Check the console output for debug messages
   - Look for "WARNING: Itinerary is empty or not found"

2. **Check the Data Structure**:
   - In the "Generate HTML" node output, check what data is being received
   - Verify the structure matches: `{ itinerary: {...}, email: "...", sources: [...] }`

3. **Test the Webhook Directly**:
   ```bash
   curl -X POST https://msriram.app.n8n.cloud/webhook/generate-pdf \
     -H "Content-Type: application/json" \
     -d '{
       "itinerary": {
         "city": "Chennai",
         "duration_days": 2,
         "pace": "relaxed",
         "day_1": {
           "morning": {
             "activities": [{
               "activity": "Test Activity",
               "time": "09:00",
               "duration_minutes": 60
             }]
           }
         }
       },
       "email": "test@example.com",
       "sources": []
     }'
   ```

## Expected Data Structure

The backend sends this structure:
```json
{
  "itinerary": {
    "city": "Chennai",
    "duration_days": 2,
    "pace": "relaxed",
    "day_1": {
      "morning": {
        "activities": [...]
      },
      "afternoon": {
        "activities": [...]
      },
      "evening": {
        "activities": [...]
      }
    },
    "day_2": { ... }
  },
  "email": "user@example.com",
  "sources": [...]
}
```

The workflow should extract:
- `itinerary` - The full itinerary object
- `email` - Recipient email address
- `sources` - Array of source citations

## Common Issues

### Issue: Still getting empty email

**Possible causes:**
1. Workflow not updated - Make sure you re-imported or updated the code
2. Workflow not active - Toggle to Active
3. PDF generation failing - Check PDF API credentials
4. SMTP not configured - Check email node credentials

**Solution:**
- Check n8n execution logs
- Verify all nodes are configured correctly
- Test each node individually in n8n

### Issue: PDF not attached

**Possible causes:**
1. PDF API failing - Check PDF_API_KEY and PDF_API_URL
2. PDF generation timeout - Increase timeout in HTTP Request node
3. Binary data not passed correctly - Check "Generate PDF" node output format

**Solution:**
- Check "Generate PDF" node execution
- Verify PDF API credentials in n8n environment variables
- Check if PDF API returns binary data

---

**Last Updated**: 2024-01-17  
**Status**: ✅ Fixed
