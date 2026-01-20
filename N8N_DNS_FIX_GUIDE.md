# n8n DNS Resolution Fix Guide

## Problem
You're seeing this error:
```
DNS resolution failed for n8n webhook URL: https://msriram.app.n8n.cloud/webhook/generate-pdf
```

## Quick Diagnosis

✅ **Good News**: Your n8n instance is accessible (tested successfully)
❌ **Issue**: Backend cannot connect due to DNS/network configuration

## Solutions (Choose One)

### Option 1: Fix DNS Resolution (Recommended)

#### For Windows:

1. **Change DNS Server**:
   - Open Network Settings → Change adapter options
   - Right-click your network adapter → Properties
   - Select "Internet Protocol Version 4 (TCP/IPv4)" → Properties
   - Select "Use the following DNS server addresses"
   - Set:
     - Preferred: `8.8.8.8` (Google DNS)
     - Alternate: `1.1.1.1` (Cloudflare DNS)
   - Click OK and restart your network adapter

2. **Flush DNS Cache**:
   ```powershell
   ipconfig /flushdns
   ```

3. **Disable VPN** (if active):
   - Corporate VPNs often redirect DNS to internal servers
   - Try disconnecting VPN and test again

4. **Restart Backend Server**:
   - Stop the backend (Ctrl+C)
   - Restart: `cd backend/src && python main.py`

### Option 2: Temporarily Disable PDF Generation

If you don't need PDF generation right now, you can disable it:

1. **Edit `backend/.env` file**:
   ```env
   # Comment out or remove this line:
   # N8N_WEBHOOK_URL=https://msriram.app.n8n.cloud/webhook/generate-pdf
   ```

2. **Restart Backend Server**:
   ```bash
   # Stop the backend (Ctrl+C)
   # Start it again
   cd backend/src
   python main.py
   ```

3. **Result**: PDF generation will be disabled, but other features will work normally.

### Option 3: Verify Webhook URL

1. **Open n8n**:
   - Go to https://msriram.app.n8n.cloud in your browser
   - Log in to your n8n account

2. **Check Workflow**:
   - Open "Travel Itinerary PDF & Email" workflow
   - Make sure it's **Active** (green toggle)

3. **Get Production Webhook URL**:
   - Click on the **Webhook** node (first node)
   - Copy the **Production URL** (not Test URL)
   - Format should be: `https://msriram.app.n8n.cloud/webhook/xxxxx`

4. **Update `.env` file**:
   ```env
   N8N_WEBHOOK_URL=<paste-the-production-url-here>
   ```

5. **Restart Backend**

## Testing

After applying a fix, test the connection:

```powershell
# Test DNS resolution
nslookup msriram.app.n8n.cloud

# Test backend connection
Invoke-WebRequest -Uri http://localhost:8000/api/test-n8n -UseBasicParsing
```

Expected response:
```json
{
  "success": true,
  "dns_resolved": true,
  "ip_address": "...",
  "http_status": 200
}
```

## Why This Happens

- **Corporate Networks**: Your DNS resolves to a private IP (10.x.x.x) which is likely a corporate proxy
- **VPN Interference**: VPNs often redirect DNS queries
- **DNS Cache**: Old DNS records cached locally
- **Network Configuration**: Firewall or proxy blocking external connections

## Still Not Working?

1. Check backend logs: `backend/logs/app.log`
2. Verify n8n instance is running and workflow is active
3. Try accessing the webhook directly in browser (should show n8n interface)
4. Check if you can reach other external services from your backend

---

**Note**: The improved error handling will now provide better diagnostics. Check the error message for specific suggestions based on your network configuration.
