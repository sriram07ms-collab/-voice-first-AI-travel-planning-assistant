# Fix: "Access to env vars denied" in n8n Workflow

## Problem

You're getting an error: **"access to env vars denied"** when the n8n workflow tries to access environment variables like:
- `$env.PDF_API_URL`
- `$env.PDF_API_KEY`
- `$env.SMTP_FROM_EMAIL`

---

## Root Causes

1. **Environment variables not set** in n8n
2. **Permission restrictions** in n8n.cloud (paid plans may restrict env var access)
3. **Syntax issues** when accessing env vars

---

## ✅ Solution 1: Set Environment Variables in n8n (Recommended)

### For n8n Cloud:

1. **Go to Settings**:
   - Click on your **profile icon** (top right)
   - Select **Settings**
   - Go to **Environment Variables** section

2. **Add Variables**:
   - Click **"Add Variable"** or **"+ Add"**
   - For each variable:
     - **Name**: `SMTP_FROM_EMAIL`
     - **Value**: `your-email@gmail.com`
     - Click **"Save"**
   - Repeat for:
     - `PDF_API_URL` (optional, has default)
     - `PDF_API_KEY` (required if using htmlpdfapi.com)

3. **Important**:
   - ⚠️ Some n8n.cloud plans may restrict environment variable access
   - ✅ If you can't set env vars, use **Solution 2** below

### For Self-Hosted n8n:

1. **Option A: n8n Settings**:
   - Go to **Settings** → **Environment Variables**
   - Add variables directly in the UI

2. **Option B: Environment File**:
   - Edit `.env` file where n8n is running
   - Add:
     ```bash
     SMTP_FROM_EMAIL=your-email@gmail.com
     PDF_API_URL=https://api.htmlpdfapi.com/v1/pdf
     PDF_API_KEY=your-api-key-here
     ```
   - Restart n8n

---

## ✅ Solution 2: Use Hardcoded Values (Quick Fix)

If environment variables aren't accessible, you can hardcode values directly in the workflow nodes.

### Step 1: Update "Generate PDF" Node

1. **Open the "Generate PDF" node** (HTTP Request node)
2. **Update URL field**:
   - Replace: `={{ $env.PDF_API_URL || 'https://api.htmlpdfapi.com/v1/pdf' }}`
   - With: `https://api.htmlpdfapi.com/v1/pdf` (or your PDF API URL)
3. **Update X-API-Key header**:
   - Replace: `={{ $env.PDF_API_KEY || '' }}`
   - With: `your-actual-api-key-here` (replace with your real API key)

### Step 2: Update "Send Email" Node

1. **Open the "Send Email" node**
2. **Update fromEmail field**:
   - Replace: `={{ $env.SMTP_FROM_EMAIL || 'travel-assistant@example.com' }}`
   - With: `your-email@gmail.com` (replace with your actual email)

### Step 3: Save and Test

1. Click **"Save"** to save the workflow
2. **Activate** the workflow (green toggle)
3. Test with a webhook request

---

## ✅ Solution 3: Use n8n Credentials (Alternative)

Instead of environment variables, use n8n's credential system:

### For Email:

1. **Configure SMTP credentials** (you already have this):
   - The "Send Email" node uses SMTP credentials
   - `fromEmail` can be set in the credential or hardcoded

### For PDF API:

1. **Create HTTP Header Auth credential** (if your PDF API requires API key):
   - Go to **Credentials** → **HTTP Header Auth**
   - Add your API key
   - Use this credential in the HTTP Request node instead of env var

---

## ✅ Solution 4: Update Workflow with Defaults (Best Practice)

Update the workflow to gracefully handle missing env vars by using defaults.

The workflow already has defaults, but let's verify they're correct:

### Current Configuration (in workflow):

**Generate PDF Node:**
- URL: `={{ $env.PDF_API_URL || 'https://api.htmlpdfapi.com/v1/pdf' }}` ✅ Has default
- API Key: `={{ $env.PDF_API_KEY || '' }}` ✅ Has default (empty string)

**Send Email Node:**
- fromEmail: `={{ $env.SMTP_FROM_EMAIL || 'travel-assistant@example.com' }}` ✅ Has default

If env vars are **completely denied**, the `||` fallback might not work. In that case, use **Solution 2** (hardcode values).

---

## 🔍 Troubleshooting

### Error: "Environment variable 'X' is not set"

**Fix**: Set the environment variable in n8n settings, or use hardcoded values (Solution 2).

### Error: "Access to environment variables denied"

**Possible causes**:
1. **n8n.cloud free plan** may restrict env var access
   - **Fix**: Upgrade to paid plan, or use hardcoded values

2. **Workflow permissions** restrict env var access
   - **Fix**: Check workflow settings, or use hardcoded values

3. **Self-hosted n8n** requires env var configuration
   - **Fix**: Set env vars in `.env` file or n8n settings

### Workflow works but uses wrong values

**Fix**: Check if env vars are set correctly, or switch to hardcoded values to ensure correct configuration.

---

## 📋 Quick Fix Checklist

If you need a quick fix right now:

- [ ] **Option A**: Set env vars in n8n Settings → Environment Variables
- [ ] **Option B**: Hardcode values in workflow nodes (see Solution 2)
- [ ] **Option C**: Use n8n credentials for sensitive data (API keys)

---

## 🔐 Security Best Practices

### For Production:

1. **Use Environment Variables** (if available):
   - ✅ Keeps sensitive data out of workflow JSON
   - ✅ Easy to update without modifying workflow
   - ✅ Better security

2. **If Env Vars Not Available**:
   - ✅ Use **n8n Credentials** for sensitive data (API keys, passwords)
   - ✅ Hardcode non-sensitive values (URLs, default emails)
   - ⚠️ **Never commit workflow JSON** with hardcoded secrets to version control

3. **For n8n.cloud**:
   - Consider upgrading to a plan that supports environment variables
   - Or use credentials + hardcoded non-sensitive values

---

## Example: Updated Workflow (Hardcoded Values)

If you need to hardcode values, here's what to change:

**Before (using env vars):**
```json
"url": "={{ $env.PDF_API_URL || 'https://api.htmlpdfapi.com/v1/pdf' }}"
"value": "={{ $env.PDF_API_KEY || '' }}"
"fromEmail": "={{ $env.SMTP_FROM_EMAIL || 'travel-assistant@example.com' }}"
```

**After (hardcoded):**
```json
"url": "https://api.htmlpdfapi.com/v1/pdf"
"value": "your-actual-api-key-here"
"fromEmail": "your-email@gmail.com"
```

---

## Related Documentation

- [N8N Integration Guide](./N8N_INTEGRATION_GUIDE.md)
- [N8N Testing Guide](./N8N_TESTING_GUIDE.md)
- [N8N Workflow Setup](../n8n-workflows/README.md)
