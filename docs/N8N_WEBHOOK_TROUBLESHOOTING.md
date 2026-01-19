# n8n Webhook Troubleshooting Guide

This guide helps troubleshoot common issues with n8n webhook integration for PDF generation.

## 🔴 Error: 404 Not Found

### Problem
```
404 Client Error: Not Found for url: https://xxx.app.n8n.cloud/webhook/xxx
```

### Possible Causes

1. **Webhook URL is incorrect**
   - Check that the webhook URL in your `.env` file matches the actual webhook URL from n8n
   - Ensure you're using the **production webhook** URL, not the test webhook URL

2. **Workflow is not active**
   - In n8n, go to your workflow
   - Click the toggle switch to activate the workflow
   - The workflow must be **active** (green) for webhooks to work

3. **Webhook node is not enabled**
   - Open your workflow in n8n
   - Check that the Webhook node is enabled (not grayed out)
   - Ensure the webhook node is properly configured

4. **Using test webhook instead of production**
   - Test webhook URLs: `https://xxx.app.n8n.cloud/webhook-test/xxx`
   - Production webhook URLs: `https://xxx.app.n8n.cloud/webhook/xxx`
   - Make sure you're using the production webhook URL in your `.env` file

### Solution Steps

1. **Get the correct webhook URL**:
   - Open your n8n workflow
   - Click on the Webhook node
   - Copy the **Production URL** (not the Test URL)
   - It should look like: `https://xxx.app.n8n.cloud/webhook/xxx`

2. **Update your `.env` file**:
   ```env
   N8N_WEBHOOK_URL=https://xxx.app.n8n.cloud/webhook/xxx
   ```

3. **Activate the workflow**:
   - In n8n, toggle the workflow to **Active** (green)
   - Wait a few seconds for it to activate

4. **Test the webhook**:
   - You can test the webhook directly in n8n by clicking "Test URL" in the Webhook node
   - Or use curl:
     ```bash
     curl -X POST https://xxx.app.n8n.cloud/webhook/xxx \
       -H "Content-Type: application/json" \
       -d '{"test": "data"}'
     ```

---

## 🔴 Error: 401 Unauthorized

### Problem
```
401 Client Error: Unauthorized
```

### Possible Causes

1. **Webhook requires authentication**
   - Some n8n webhooks require authentication
   - Check if your webhook node has authentication enabled

### Solution

1. **Disable authentication** (if not needed):
   - Open the Webhook node in n8n
   - Go to "Authentication" settings
   - Set to "None" if authentication is not required

2. **Or configure authentication**:
   - If authentication is required, you'll need to update the n8n client to include auth headers
   - Contact your n8n administrator for credentials

---

## 🔴 Error: 500 Internal Server Error

### Problem
```
500 Internal Server Error
```

### Possible Causes

1. **Workflow has an error**
   - The n8n workflow itself may have an error
   - A node in the workflow may be failing

### Solution

1. **Check n8n execution logs**:
   - Go to n8n → Executions
   - Find the failed execution
   - Check the error message

2. **Test the workflow manually**:
   - In n8n, click "Execute Workflow" to test
   - Check which node is failing
   - Fix the error in that node

3. **Common workflow errors**:
   - Missing credentials (Gmail SMTP, etc.)
   - Invalid data format
   - Missing required fields

---

## 🔴 Error: Timeout

### Problem
```
PDF generation timed out. The workflow may be taking longer than expected.
```

### Possible Causes

1. **Workflow is too slow**
   - PDF generation can take time
   - The workflow may be processing slowly

### Solution

1. **Check workflow performance**:
   - Review n8n execution logs
   - Identify slow nodes
   - Optimize the workflow

2. **Increase timeout** (if needed):
   - The current timeout is 120 seconds (2 minutes)
   - If your workflow takes longer, you may need to optimize it

---

## ✅ How to Get the Correct Webhook URL

### Step-by-Step

1. **Log in to n8n**:
   - Go to your n8n instance (e.g., `https://xxx.app.n8n.cloud`)

2. **Open your workflow**:
   - Find the workflow that generates PDFs
   - Click to open it

3. **Find the Webhook node**:
   - Look for the Webhook node (usually the first node)
   - Click on it

4. **Copy the Production URL**:
   - In the Webhook node settings, you'll see:
     - **Test URL**: `https://xxx.app.n8n.cloud/webhook-test/xxx` ❌ (Don't use this)
     - **Production URL**: `https://xxx.app.n8n.cloud/webhook/xxx` ✅ (Use this)

5. **Activate the workflow**:
   - Toggle the workflow to **Active** (green switch)
   - The webhook URL only works when the workflow is active

6. **Update your `.env` file**:
   ```env
   N8N_WEBHOOK_URL=https://xxx.app.n8n.cloud/webhook/xxx
   ```

7. **Restart your backend**:
   - After updating `.env`, restart the backend server
   - The new webhook URL will be loaded

---

## 🧪 Testing the Webhook

### Method 1: Test in n8n

1. Open the Webhook node
2. Click "Test URL" button
3. Check if it responds correctly

### Method 2: Test with curl

```bash
curl -X POST https://xxx.app.n8n.cloud/webhook/xxx \
  -H "Content-Type: application/json" \
  -d '{
    "itinerary": {
      "city": "Jaipur",
      "duration_days": 3
    },
    "sources": [],
    "email": "test@example.com"
  }'
```

### Method 3: Test from the UI

1. Generate an itinerary in the app
2. Click "Generate PDF & Send Email"
3. Enter your email
4. Check the response

---

## 📋 Checklist

Before reporting an issue, check:

- [ ] Webhook URL is correct (production URL, not test URL)
- [ ] Workflow is **active** (green toggle in n8n)
- [ ] Webhook node is enabled
- [ ] `.env` file has `N8N_WEBHOOK_URL` set correctly
- [ ] Backend server was restarted after updating `.env`
- [ ] No authentication required (or authentication is configured)
- [ ] Workflow executes successfully when tested in n8n

---

## 🔍 Debugging Tips

1. **Check backend logs**:
   ```bash
   # Look for n8n webhook calls
   tail -f logs/app.log | grep n8n
   ```

2. **Check n8n execution logs**:
   - Go to n8n → Executions
   - Find the failed execution
   - Check the error details

3. **Verify webhook URL format**:
   - Should be: `https://xxx.app.n8n.cloud/webhook/xxx`
   - Should NOT be: `https://xxx.app.n8n.cloud/webhook-test/xxx`
   - Should NOT be: `https://xxx.app.n8n.cloud/workflow/xxx`

4. **Test webhook directly**:
   - Use curl or Postman to test the webhook
   - This helps isolate if the issue is with the webhook or the backend

---

## 📞 Getting Help

If you're still having issues:

1. **Check the error message** in the backend logs
2. **Check n8n execution logs** for workflow errors
3. **Verify the webhook URL** is correct
4. **Test the webhook** directly with curl
5. **Check if the workflow is active** in n8n

---

**Last Updated**: 2024-01-15
