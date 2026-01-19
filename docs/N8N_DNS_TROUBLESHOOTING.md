# n8n DNS Resolution Troubleshooting

## Issue: DNS Resolution Failed

If you see an error like:
```
DNS resolution failed for n8n webhook URL: https://msriram.app.n8n.cloud/webhook/generate-pdf
Failed to resolve 'msriram.app.n8n.cloud'
```

## Quick Diagnosis

### Step 1: Test Connection

Use the test endpoint to diagnose the issue:

```bash
# Via API endpoint
curl http://localhost:8000/api/test-n8n

# Or use the Python script
python scripts/test_n8n_connection.py
```

### Step 2: Check DNS Resolution

Test if the domain can be resolved:

**Windows (PowerShell):**
```powershell
nslookup msriram.app.n8n.cloud
# or
Test-NetConnection msriram.app.n8n.cloud -Port 443
```

**Linux/Mac:**
```bash
nslookup msriram.app.n8n.cloud
# or
ping msriram.app.n8n.cloud
```

### Step 3: Test in Browser

Try accessing the n8n instance in your browser:
- https://msriram.app.n8n.cloud

If this doesn't load, the domain may not exist or the n8n instance was deleted.

## Common Causes & Solutions

### 1. Domain Doesn't Exist

**Symptoms:**
- DNS resolution fails
- Browser can't access the domain
- nslookup returns "Non-existent domain"

**Solutions:**
- Verify the domain is correct in your `.env` file
- Check if the n8n instance was deleted or moved
- Get the correct webhook URL from your n8n workflow

### 2. Network/DNS Issues

**Symptoms:**
- Intermittent DNS failures
- Works sometimes, fails other times

**Solutions:**
- Try using a different DNS server:
  - Google DNS: `8.8.8.8`, `8.8.4.4`
  - Cloudflare DNS: `1.1.1.1`, `1.0.0.1`
- Check your network connection
- Disable VPN if active
- Check firewall settings

### 3. Workflow Not Active (404 Error)

**Symptoms:**
- DNS resolves successfully
- HTTP status 404 when accessing webhook

**Solutions:**
- Open your n8n workflow
- Toggle the workflow to **Active** (green)
- Verify the webhook path matches: `/webhook/generate-pdf`
- Check the Webhook node is enabled

### 4. Incorrect Webhook URL

**Symptoms:**
- DNS resolves but wrong path
- 404 or other HTTP errors

**Solutions:**
1. Open your n8n workflow
2. Click on the **Webhook** node
3. Copy the **Production URL** (not Test URL)
4. Update your `.env` file:
   ```env
   N8N_WEBHOOK_URL=https://your-instance.app.n8n.cloud/webhook/your-path
   ```
5. Restart the backend server

## Testing the Connection

### Method 1: API Endpoint

```bash
curl http://localhost:8000/api/test-n8n
```

Expected response if working:
```json
{
  "success": true,
  "dns_resolved": true,
  "ip_address": "104.26.12.13",
  "http_status": 200,
  "webhook_url": "https://msriram.app.n8n.cloud/webhook/generate-pdf"
}
```

### Method 2: Python Script

```bash
python scripts/test_n8n_connection.py
```

### Method 3: Direct curl Test

```bash
curl -X POST https://msriram.app.n8n.cloud/webhook/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

## Getting the Correct Webhook URL

1. **Log in to n8n:**
   - Go to your n8n instance (e.g., `https://msriram.app.n8n.cloud`)

2. **Open your workflow:**
   - Find the "Travel Itinerary PDF & Email" workflow
   - Click to open it

3. **Get the webhook URL:**
   - Click on the **Webhook** node (first node)
   - Copy the **Production URL** (not Test URL)
   - Format: `https://xxx.app.n8n.cloud/webhook/xxx`

4. **Activate the workflow:**
   - Toggle the workflow to **Active** (green switch)
   - The webhook only works when the workflow is active

5. **Update `.env` file:**
   ```env
   N8N_WEBHOOK_URL=https://your-instance.app.n8n.cloud/webhook/your-path
   ```

6. **Restart backend:**
   ```bash
   # Stop the backend (Ctrl+C)
   # Start it again
   cd backend
   python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Verification Checklist

- [ ] DNS resolves (test with `nslookup` or `ping`)
- [ ] Can access n8n instance in browser
- [ ] Webhook URL is correct (Production URL, not Test URL)
- [ ] Workflow is **Active** (green toggle in n8n)
- [ ] Webhook node is enabled
- [ ] `.env` file has correct `N8N_WEBHOOK_URL`
- [ ] Backend server was restarted after updating `.env`
- [ ] Connection test passes: `GET /api/test-n8n`

## Still Having Issues?

1. **Check backend logs:**
   ```bash
   tail -f backend/logs/app.log | grep n8n
   ```

2. **Check n8n execution logs:**
   - Go to n8n → Executions
   - Look for failed executions
   - Check error details

3. **Verify webhook URL format:**
   - ✅ Correct: `https://xxx.app.n8n.cloud/webhook/xxx`
   - ❌ Wrong: `https://xxx.app.n8n.cloud/webhook-test/xxx` (test URL)
   - ❌ Wrong: `https://xxx.app.n8n.cloud/workflow/xxx` (workflow URL)

4. **Test webhook directly:**
   - Use curl or Postman to test the webhook
   - This helps isolate if the issue is with the webhook or the backend

---

**Last Updated**: 2024-01-15
