# Fix: "Header name must be a valid HTTP token" Error in n8n

## Problem

You're getting an error in the "Generate PDF" node:
```
Problem in node 'Generate PDF'
Header name must be a valid HTTP token ["groq api key"]
```

---

## Root Cause

HTTP header names **cannot contain spaces**. The header name `"groq api key"` is invalid because:
- HTTP header names must be valid tokens
- Spaces are not allowed in header names
- Only alphanumeric characters, hyphens (`-`), and underscores (`_`) are allowed

---

## ✅ Solution: Fix Header Name

### Step 1: Open "Generate PDF" Node

1. Click on the **"Generate PDF"** node in your workflow
2. Make sure you're on the **"Parameters"** tab

### Step 2: Check Headers Section

1. Find the **"Header Parameters"** or **"Headers"** section
2. Look for any header with name containing spaces

### Step 3: Fix Invalid Header Names

**Invalid Header Names (with spaces):**
- ❌ `groq api key`
- ❌ `API Key`
- ❌ `X API Key`

**Valid Header Names (no spaces):**
- ✅ `X-API-Key` (recommended for htmlpdfapi.com)
- ✅ `Authorization` (standard header)
- ✅ `api-key`
- ✅ `X-Groq-API-Key` (if you want to name it for Groq)

### Step 4: Update Header Configuration

For the "Generate PDF" node using htmlpdfapi.com, use:

1. **Header Name**: `X-API-Key` (exactly as shown - with hyphen, no spaces)
2. **Header Value**: Your actual API key (e.g., `your-api-key-here`)

**Example Configuration:**
```
Headers:
  Name: X-API-Key
  Value: your-actual-api-key-here
```

**Alternative (if using different PDF service):**
```
Headers:
  Name: Authorization
  Value: Bearer your-api-key-here
```

---

## 🔍 Common Mistakes

### Mistake 1: Spaces in Header Name
```
❌ Name: "groq api key"
✅ Name: "X-API-Key"
```

### Mistake 2: Using Header Name as Value
```
❌ Name: "groq api key"
   Value: "X-API-Key"
✅ Name: "X-API-Key"
   Value: "your-actual-api-key"
```

### Mistake 3: Missing Header for htmlpdfapi.com
If using htmlpdfapi.com, you **must** include:
- **Header Name**: `X-API-Key`
- **Header Value**: Your API key from htmlpdfapi.com

---

## 📋 Correct Configuration for htmlpdfapi.com

Here's the exact configuration for the "Generate PDF" node when using htmlpdfapi.com:

**URL:**
```
https://api.htmlpdfapi.com/v1/pdf
```

**Headers (Header Parameters):**
```
Name: X-API-Key
Value: your-actual-htmlpdfapi-key-here
```

**Content-Type Header (if separate):**
```
Name: Content-Type
Value: application/json
```

**Body:**
```json
{
  "html": {{ $json.html }},
  "format": "A4",
  "margin": {
    "top": "20mm",
    "right": "20mm",
    "bottom": "20mm",
    "left": "20mm"
  },
  "printBackground": true
}
```

---

## 🧪 Testing After Fix

After fixing the header name:

1. **Save the workflow**
2. **Activate** the workflow (green toggle)
3. **Test with a webhook request**:
   ```powershell
   $body = @{itinerary=@{city="Jaipur";duration_days=1;day_1=@{morning=@{activities=@()};afternoon=@{activities=@()};evening=@{activities=@()}}};sources=@();email="test@example.com"} | ConvertTo-Json -Depth 10
   Invoke-RestMethod -Uri "https://msriram.app.n8n.cloud/webhook/generate-pdf" -Method Post -ContentType "application/json" -Body $body
   ```

4. **Check n8n Executions** to see if the PDF generation succeeds

---

## 📝 Summary

**The fix is simple:**
- ❌ Remove any spaces from header names
- ✅ Use `X-API-Key` (or similar valid name) for the PDF API key header
- ✅ Put your actual API key in the **Value** field, not the **Name** field

**HTTP Header Rules:**
- Header names cannot contain spaces
- Use hyphens (`-`) or underscores (`_`) instead
- Common examples: `X-API-Key`, `Authorization`, `Content-Type`

---

## Related Documentation

- [N8N Integration Guide](./N8N_INTEGRATION_GUIDE.md)
- [N8N Testing Guide](./N8N_TESTING_GUIDE.md)
- [N8N Env Vars Fix](./N8N_ENV_VARS_FIX.md)
