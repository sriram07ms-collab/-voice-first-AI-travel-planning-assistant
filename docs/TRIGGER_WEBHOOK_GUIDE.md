# How to Trigger the n8n Webhook

## Understanding "Waiting for Trigger Event"

When you see **"Waiting for trigger event"** in your n8n workflow, this is **NORMAL**. The webhook is waiting for a POST request from your backend application.

---

## 🔄 Trigger Flow

```
User Action → Frontend → Backend → n8n Webhook → Workflow Executes
```

### Step-by-Step:

1. **User Action**:
   - User plans a trip in the frontend (gets an itinerary)
   - User clicks **"Generate PDF & Send Email"** button

2. **Frontend** (`frontend/src/app/page.tsx`):
   - Calls `apiClient.generatePDF()` with session ID and email
   - Sends POST request to backend: `POST /api/generate-pdf`

3. **Backend** (`backend/src/main.py`):
   - Receives the request
   - Gets itinerary from session
   - Calls n8n webhook via `n8n_client.generate_pdf_and_email()`

4. **n8n Webhook** (`n8n_client.py`):
   - Sends POST request to your webhook URL:
     ```
     POST https://msriram.app.n8n.cloud/webhook/generate-pdf
     Content-Type: application/json
     
     {
       "itinerary": { ... },
       "sources": [ ... ],
       "email": "user@example.com"
     }
     ```

5. **n8n Workflow**:
   - Webhook receives the POST request ✅
   - Workflow starts executing
   - Generates HTML → PDF → Email

---

## ✅ Prerequisites Checklist

Before the webhook can be triggered, ensure:

- [ ] **Workflow is ACTIVE** (green toggle in n8n, not paused)
- [ ] **Webhook node is enabled** in the workflow
- [ ] **Production webhook URL** is configured (not test URL)
- [ ] **Backend `.env` file** has `N8N_WEBHOOK_URL` set correctly
- [ ] **Backend server is running** (port 8000)
- [ ] **Frontend server is running** (port 3000)
- [ ] **You have an itinerary** (plan a trip first)

---

## 🧪 How to Test the Trigger

### Method 1: Use the Frontend (Recommended)

1. **Start your servers**:
   ```powershell
   # Backend (if not running)
   cd backend
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

   # Frontend (if not running)
   cd frontend
   npm run dev
   ```

2. **Open the application**:
   - Go to: `http://localhost:3000`

3. **Plan a trip**:
   - Type: "Plan a 3-day trip to Jaipur, I like shopping"
   - Wait for the itinerary to be generated

4. **Generate PDF**:
   - Click the **"Generate PDF & Send Email"** button
   - Enter your email when prompted
   - This will trigger the webhook!

5. **Check n8n**:
   - Go to **Executions** tab in n8n
   - You should see a new execution appear
   - The workflow should run and send the email

### Method 2: Direct Webhook Test (curl)

Test the webhook directly without the frontend:

```powershell
curl -X POST https://msriram.app.n8n.cloud/webhook/generate-pdf `
  -H "Content-Type: application/json" `
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
    "sources": [],
    "email": "test@example.com"
  }'
```

**Expected Response**:
```json
{
  "status": "success",
  "message": "PDF generated and emailed successfully",
  "email_sent": true,
  "email_address": "test@example.com",
  "generated_at": "2024-01-15T12:00:00.000Z"
}
```

### Method 3: Test via Backend API

```powershell
# First, plan a trip to get a session_id
curl -X POST http://localhost:8000/api/chat `
  -H "Content-Type: application/json" `
  -d '{
    "message": "Plan a 2-day trip to Jaipur",
    "session_id": "test-session-123"
  }'

# Then generate PDF (use the session_id from above)
curl -X POST http://localhost:8000/api/generate-pdf `
  -H "Content-Type: application/json" `
  -d '{
    "session_id": "test-session-123",
    "email": "test@example.com"
  }'
```

---

## 🔍 Troubleshooting

### Issue: Workflow still shows "Waiting for trigger event"

**Possible causes:**

1. **Workflow is NOT ACTIVE**:
   - ✅ **Fix**: Toggle the workflow to **ACTIVE** (green) in n8n
   - The workflow must be active (not paused) to receive webhooks

2. **Wrong webhook URL**:
   - ✅ **Fix**: Use **Production URL** (not Test URL)
   - Production: `https://xxx.app.n8n.cloud/webhook/xxx`
   - Test: `https://xxx.app.n8n.cloud/webhook-test/xxx` ❌

3. **Backend `.env` file not configured**:
   - ✅ **Fix**: Check `backend/.env` has:
     ```
     N8N_WEBHOOK_URL=https://msriram.app.n8n.cloud/webhook/generate-pdf
     ```

4. **Backend server not running**:
   - ✅ **Fix**: Start backend server:
     ```powershell
     cd backend
     python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
     ```

5. **No itinerary available**:
   - ✅ **Fix**: Plan a trip first before generating PDF
   - The button won't appear until an itinerary exists

### Issue: Webhook receives request but workflow doesn't execute

- Check **Executions** tab in n8n for errors
- Check if all nodes are configured correctly
- Verify SMTP credentials are set
- Check PDF API credentials (if using htmlpdfapi.com)

### Issue: 404 Error when triggering

- Verify the webhook path is correct: `/webhook/generate-pdf`
- Check the `webhookId` in the workflow matches: `generate-pdf`
- Ensure the workflow is active

---

## 📋 Quick Verification Steps

Run these commands to verify everything is set up:

```powershell
# 1. Check backend is running
curl http://localhost:8000/health

# 2. Check backend can reach n8n (if network allows)
# Note: This might fail if n8n requires authentication or is behind firewall

# 3. Verify webhook URL in environment
# Check backend/.env file contains N8N_WEBHOOK_URL
```

---

## 🎯 Summary

**The trigger is:**
- ✅ A **POST request** from your backend to the n8n webhook URL
- ✅ **Automatic** when user clicks "Generate PDF & Send Email" in frontend
- ✅ **Manual** if you use curl or Postman to test directly

**"Waiting for trigger event" is NORMAL** - it means the webhook is ready and waiting for requests.

**To trigger it:**
1. Make sure workflow is **ACTIVE** (green toggle)
2. Use the frontend: Plan a trip → Click "Generate PDF & Send Email"
3. Or test directly with curl using the webhook URL

---

## 📚 Related Documentation

- [N8N Integration Guide](./N8N_INTEGRATION_GUIDE.md)
- [N8N Testing Guide](./N8N_TESTING_GUIDE.md)
- [N8N Webhook Troubleshooting](./N8N_WEBHOOK_TROUBLESHOOTING.md)
