# n8n Workflow Testing Guide

Complete guide to testing the n8n workflow for PDF generation and email delivery.

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Unit Tests](#unit-tests)
3. [Direct Webhook Testing](#direct-webhook-testing)
4. [Workflow Testing in n8n UI](#workflow-testing-in-n8n-ui)
5. [Integration Testing](#integration-testing)
6. [End-to-End Testing](#end-to-end-testing)
7. [Testing Checklist](#testing-checklist)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before testing, ensure:

- [ ] n8n instance is running (cloud or self-hosted)
- [ ] Workflow is imported and **Active** (green toggle)
- [ ] Environment variables are configured in n8n:
  - `SMTP_FROM_EMAIL`
  - `PDF_API_URL` (optional, has default)
  - `PDF_API_KEY` (if using htmlpdfapi.com)
- [ ] Backend server is running
- [ ] `N8N_WEBHOOK_URL` is set in `backend/.env`
- [ ] SMTP credentials are configured in n8n

---

## Unit Tests

Test the backend code and models without calling n8n.

### Run Unit Tests

```bash
cd tests
pytest test_phase8.py -v
```

Or run directly:

```bash
cd tests
python test_phase8.py
```

### What Gets Tested

1. ✅ **n8n Client Initialization** - Verifies client can be created with valid URL
2. ✅ **n8n Client (No URL)** - Tests error handling when URL is missing
3. ✅ **n8n Workflow File** - Validates workflow JSON file is valid
4. ✅ **PDF Endpoint Integration** - Tests request/response models

### Expected Output

```
==================================================
Phase 8: n8n Integration - Test Suite
==================================================
[PASS]: n8n Client Initialization
[PASS]: n8n Client (No URL)
[PASS]: n8n Workflow File
[PASS]: PDF Endpoint Integration

Total: 4/4 tests passed

[SUCCESS] All Phase 8 tests passed!
```

---

## Direct Webhook Testing

Test the n8n webhook directly without going through the backend.

### Step 1: Get Your Webhook URL

1. Open your n8n workflow
2. Click on the **Webhook** node
3. Copy the **Production URL** (not Test URL)
   - ✅ Production: `https://xxx.app.n8n.cloud/webhook/xxx`
   - ❌ Test: `https://xxx.app.n8n.cloud/webhook-test/xxx`

### Step 2: Test with curl

**Minimal Test Payload:**

```bash
curl -X POST https://your-instance.n8n.cloud/webhook/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "itinerary": {
      "city": "Jaipur",
      "duration_days": 3,
      "pace": "moderate",
      "day_1": {
        "morning": {
          "activities": [
            {
              "activity": "Hawa Mahal",
              "time": "09:00",
              "duration_minutes": 60,
              "travel_time_from_previous": 0,
              "description": "Famous palace in Jaipur"
            }
          ]
        },
        "afternoon": { "activities": [] },
        "evening": { "activities": [] }
      }
    },
    "sources": [
      {
        "type": "openstreetmap",
        "poi": "Hawa Mahal",
        "source_id": "way:123456",
        "url": "https://www.openstreetmap.org/way/123456"
      }
    ],
    "email": "test@example.com"
  }'
```

**Expected Response:**

```json
{
  "status": "success",
  "message": "PDF generated and emailed successfully",
  "email_sent": true,
  "email_address": "test@example.com",
  "generated_at": "2024-01-15T12:00:00.000Z"
}
```

### Step 3: Check Results

1. **Check n8n Executions**:
   - Go to **Executions** tab in n8n
   - Verify workflow ran successfully
   - Check execution time and status

2. **Check Email**:
   - Check your inbox (and spam folder)
   - Verify PDF attachment is present
   - Verify email subject and body

3. **Check Workflow Output**:
   - Click on execution to see node outputs
   - Verify HTML generation worked
   - Verify PDF generation succeeded
   - Verify email was sent

---

## Workflow Testing in n8n UI

Test each node individually in n8n.

### Step 1: Test Webhook Node

1. Open workflow in n8n
2. Click on **Webhook** node
3. Click **"Test URL"** button
4. Or click **"Execute Node"** with sample data

### Step 2: Test HTML Generation Node

1. Click on **"Generate HTML"** node (Code node)
2. Click **"Execute Node"**
3. Check output:
   - HTML should be generated
   - Verify formatting and structure
   - Check all itinerary data is included

### Step 3: Test PDF Generation Node

1. Click on **"Generate PDF"** node (HTTP Request)
2. Click **"Execute Node"**
3. Check output:
   - Binary PDF data should be present
   - Verify no errors occurred
   - Check execution logs if failed

### Step 4: Test Email Node

1. Click on **"Send Email"** node
2. Click **"Execute Node"**
3. Check output:
   - Email should be sent
   - Verify recipient email matches
   - Check for SMTP errors

### Step 5: Test Full Workflow

1. Click **"Execute Workflow"** button (top right)
2. Use test payload from documentation
3. Monitor execution progress
4. Verify all nodes succeeded

---

## Integration Testing

Test the complete flow from backend API to n8n.

### Step 1: Start Backend

```bash
cd backend
python -m uvicorn src.main:app --reload
```

### Step 2: Create a Test Session

**Option A: Using curl**

```bash
curl -X POST http://localhost:8000/api/plan \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "user_input": "Plan a 3-day trip to Jaipur"
  }'
```

**Option B: Using Frontend**

1. Open the application in browser
2. Plan a trip through the UI
3. Note the `session_id` from browser developer tools or response

### Step 3: Generate PDF

```bash
curl -X POST http://localhost:8000/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "email": "your-email@example.com"
  }'
```

### Step 4: Verify Response

**Success Response:**

```json
{
  "status": "success",
  "message": "PDF generated and emailed successfully",
  "email_sent": true,
  "email_address": "your-email@example.com",
  "generated_at": "2024-01-15T12:00:00.000Z"
}
```

**Error Response Examples:**

```json
{
  "status": "error",
  "error_type": "SESSION_NOT_FOUND",
  "message": "Session not found. Please plan a trip first."
}
```

### Step 5: Check Results

1. **Backend Logs**: Check console for any errors
2. **n8n Executions**: Verify workflow was triggered
3. **Email**: Check inbox for PDF attachment
4. **Response**: Verify API returned success

---

## End-to-End Testing

Complete user flow from frontend to email delivery.

### Test Scenario 1: Happy Path

1. **Start Services**:
   ```bash
   # Terminal 1: Backend
   cd backend
   python -m uvicorn src.main:app --reload
   
   # Terminal 2: Frontend (if needed)
   cd frontend
   npm run dev
   ```

2. **Plan Trip**:
   - Open application in browser
   - Enter trip details (e.g., "3-day trip to Jaipur")
   - Complete planning flow
   - Verify itinerary is displayed

3. **Generate PDF**:
   - Click "Generate PDF" button (if available)
   - Enter email address
   - Submit request
   - Wait for confirmation

4. **Verify**:
   - ✅ Success message shown
   - ✅ Email received with PDF
   - ✅ PDF contains correct itinerary
   - ✅ No errors in browser console
   - ✅ No errors in backend logs
   - ✅ Workflow executed in n8n

### Test Scenario 2: Error Handling

**Test Missing Session:**

```bash
curl -X POST http://localhost:8000/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "non-existent-session",
    "email": "test@example.com"
  }'
```

**Expected:** 404 error with "Session not found" message

**Test Missing n8n Configuration:**

1. Remove `N8N_WEBHOOK_URL` from `.env`
2. Restart backend
3. Try to generate PDF

**Expected:** 503 error with "PDF generation service is not configured" message

**Test Invalid Email:**

```bash
curl -X POST http://localhost:8000/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "email": "invalid-email"
  }'
```

**Expected:** 400 error or email validation error

---

## Testing Checklist

Use this checklist to ensure complete testing:

### Pre-Testing

- [ ] n8n instance is accessible
- [ ] Workflow is imported and active
- [ ] Environment variables are set
- [ ] SMTP credentials are configured
- [ ] Backend server is running
- [ ] `N8N_WEBHOOK_URL` is set correctly

### Unit Tests

- [ ] All unit tests pass (`test_phase8.py`)
- [ ] No errors in test output
- [ ] All test cases covered

### Webhook Testing

- [ ] Webhook URL is correct (production, not test)
- [ ] Webhook responds to POST requests
- [ ] Workflow executes when webhook is called
- [ ] All nodes in workflow execute successfully

### Node Testing

- [ ] Webhook node receives data correctly
- [ ] HTML generation node creates valid HTML
- [ ] PDF generation node produces PDF binary
- [ ] Email node sends email successfully
- [ ] Response node returns correct format

### Integration Testing

- [ ] Backend can create sessions
- [ ] Backend can retrieve itinerary
- [ ] Backend calls n8n webhook correctly
- [ ] n8n workflow processes request
- [ ] Email is sent with PDF attachment
- [ ] Backend receives response from n8n

### End-to-End Testing

- [ ] Complete flow works from UI
- [ ] PDF contains all itinerary data
- [ ] PDF formatting is correct
- [ ] Email subject and body are correct
- [ ] Error messages are user-friendly
- [ ] Loading states work correctly

### Error Scenarios

- [ ] Missing session handled correctly
- [ ] Missing n8n configuration handled
- [ ] Invalid email handled correctly
- [ ] Network errors handled gracefully
- [ ] n8n errors propagate to frontend

---

## Troubleshooting

### Webhook Not Receiving Requests

**Symptoms:** Workflow doesn't trigger

**Solutions:**
1. Verify workflow is **Active** (green toggle)
2. Check webhook URL is correct (production URL)
3. Test webhook directly with curl
4. Check n8n logs for errors
5. Verify no authentication required (or it's configured)

### PDF Generation Fails

**Symptoms:** Workflow stops at PDF node

**Solutions:**
1. Check `PDF_API_URL` environment variable
2. Verify `PDF_API_KEY` is set (if required)
3. Check API key is valid and not expired
4. Review n8n execution logs for detailed error
5. Test PDF API directly

### Email Not Sending

**Symptoms:** PDF generated but email not received

**Solutions:**
1. Verify SMTP credentials are correct
2. Check email is not in spam folder
3. Verify `SMTP_FROM_EMAIL` environment variable
4. Test SMTP connection separately
5. Check email service quotas/limits
6. Review n8n execution logs for email errors

### HTML Generation Issues

**Symptoms:** PDF formatting is incorrect

**Solutions:**
1. Check HTML output in n8n "Generate HTML" node
2. Verify CSS styles are included
3. Test HTML in browser first
4. Adjust PDF node margins if needed
5. Check for missing data in itinerary

### Backend Returns 503 Error

**Symptoms:** "PDF generation service is not configured"

**Solutions:**
1. Check `N8N_WEBHOOK_URL` is set in `.env`
2. Restart backend after updating `.env`
3. Verify URL format is correct
4. Check backend logs for configuration errors

### Backend Returns 404 Error

**Symptoms:** "Session not found"

**Solutions:**
1. Ensure trip is planned first (session exists)
2. Verify `session_id` is correct
3. Check session hasn't expired
4. Review conversation manager logs

---

## Quick Test Commands

### Test Webhook Directly

```bash
curl -X POST https://your-n8n-instance.com/webhook/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Test Backend Health

```bash
curl http://localhost:8000/health
```

### Test PDF Endpoint

```bash
curl -X POST http://localhost:8000/api/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "email": "test@example.com"
  }'
```

### View n8n Logs (Docker)

```bash
docker logs n8n
```

---

## Next Steps

After testing:

1. ✅ Document any issues found
2. ✅ Update workflow if needed
3. ✅ Test error scenarios
4. ✅ Verify email deliverability
5. ✅ Test with different itinerary sizes
6. ✅ Monitor execution times
7. ✅ Check resource usage

---

**Need Help?** 

- Check [N8N_INTEGRATION_GUIDE.md](./N8N_INTEGRATION_GUIDE.md) for setup details
- Check [N8N_PDF_FIX.md](./N8N_PDF_FIX.md) for PDF generation issues
- Check [N8N_WEBHOOK_TROUBLESHOOTING.md](./N8N_WEBHOOK_TROUBLESHOOTING.md) for webhook issues
- Review n8n execution logs for detailed error messages
