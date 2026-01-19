# n8n Send Email Node - Parameter Configuration Guide

A guide to correctly configure the "Send Email" node parameters in n8n.

## 🔧 Send Email Node Parameters

### Correct Configuration

Here are the correct parameter values for the "Send Email" node:

| Parameter | Value | Notes |
|-----------|-------|-------|
| **From Email** | Your Gmail address (e.g., `yourname@gmail.com`) | See "From Email Fix" below |
| **To Email** | `{{ $('Generate HTML').item.json.email }}` | ✅ Correct |
| **Subject** | `Your Travel Itinerary: {{ $('Generate HTML').item.json.city }}` | ✅ Correct |
| **Email Format** | `Text` | ✅ Correct |
| **Text** | See email body template below | ✅ Correct |
| **Attachments** | `{{ [{ name: 'itinerary.pdf', data: $binary.data.data, type: 'application/pdf' }] }}` | ✅ Correct |

---

## ❌ Problem: "access to env vars denied" Error

### Error Message
```
[ERROR: access to env vars denied]
```

### Cause
n8n is not allowing access to environment variables in the expression. This can happen if:
1. Environment variables are disabled in n8n settings
2. The expression syntax is incorrect
3. n8n version doesn't support `$env` in expressions

---

## ✅ Solution: Fix "From Email" Parameter

### Option 1: Use Direct Email Address (Simplest)

**Replace the expression with your actual Gmail address:**

```
yourname@gmail.com
```

**Steps:**
1. Click on the **"From Email"** field
2. **Delete** the expression: `{{ $env.SMTP_FROM_EMAIL || 'travel-assistant@example.com' }}`
3. **Type** your Gmail address directly: `yourname@gmail.com`
4. Click outside the field to save

**Pros:**
- ✅ Works immediately
- ✅ No configuration needed
- ✅ Simple and reliable

**Cons:**
- ⚠️ Hardcoded email address (not dynamic)

---

### Option 2: Enable Environment Variables (Recommended for Production)

**Step 1: Enable Environment Variables in n8n**

1. **Go to n8n Settings**:
   - Click **Settings** (gear icon) in top-right
   - Or go to: `http://localhost:5678/settings`

2. **Enable Environment Variables**:
   - Look for **"Environment Variables"** section
   - Make sure it's enabled/allowed
   - Some n8n versions require this to be enabled explicitly

3. **Set the Environment Variable**:
   - Go to **Settings** → **Environment Variables**
   - Click **Add Variable**
   - **Name**: `SMTP_FROM_EMAIL`
   - **Value**: `yourname@gmail.com`
   - Click **Save**

**Step 2: Update Expression Syntax**

Try these alternative expressions (one should work):

**Option A: Simple Environment Variable**
```
{{ $env.SMTP_FROM_EMAIL }}
```

**Option B: With Fallback**
```
{{ $env.SMTP_FROM_EMAIL || 'yourname@gmail.com' }}
```

**Option C: Using getenv() function**
```
{{ getenv('SMTP_FROM_EMAIL') || 'yourname@gmail.com' }}
```

**Option D: Direct Reference (if using n8n cloud)**
```
{{ $env.SMTP_FROM_EMAIL }}
```

**Steps:**
1. Click on **"From Email"** field
2. Try each expression option above
3. Test which one works in your n8n version
4. Use the one that doesn't show an error

---

### Option 3: Use Code Node to Set From Email

If environment variables don't work, use a Code node before the Send Email node:

1. **Add a Code Node** before "Send Email"
2. **Set the from email** in the code node output
3. **Reference it** in the Send Email node

**Code Node JavaScript:**
```javascript
const fromEmail = process.env.SMTP_FROM_EMAIL || 'yourname@gmail.com';

return {
  json: {
    fromEmail: fromEmail,
    // ... other data
  }
};
```

**Then in Send Email node:**
- **From Email**: `{{ $json.fromEmail }}`

---

## 📝 Complete Email Body Template

Here's the complete email body text for the **"Text"** parameter:

```
Please find your travel itinerary attached.

Trip: {{ $('Generate HTML').item.json.city }}
Duration: {{ $('Generate HTML').item.json.durationDays }} days

Enjoy your trip!
```

---

## ✅ Complete Parameter Checklist

Verify all parameters are set correctly:

- [ ] **From Email**: Your Gmail address (fixed - no env var error)
- [ ] **To Email**: `{{ $('Generate HTML').item.json.email }}`
- [ ] **Subject**: `Your Travel Itinerary: {{ $('Generate HTML').item.json.city }}`
- [ ] **Email Format**: `Text`
- [ ] **Text**: Email body with dynamic content
- [ ] **Attachments**: `{{ [{ name: 'itinerary.pdf', data: $binary.data.data, type: 'application/pdf' }] }}`
- [ ] **SMTP Credential**: Gmail SMTP credential is selected

---

## 🔍 Testing the Configuration

### Step 1: Test Expression

1. **Click "Execute previous nodes"** button (left side)
2. **Check OUTPUT** panel (right side)
3. **Verify** expressions resolve correctly:
   - To Email should show the recipient email
   - Subject should show the city name
   - From Email should show your Gmail address

### Step 2: Test Email Sending

1. **Click "Execute step"** button (red button, right side)
2. **Check for errors** in the output
3. **Verify** email is sent successfully

---

## 🐛 Troubleshooting

### Problem: "access to env vars denied" persists

**Solutions:**
1. **Use Option 1** (direct email address) - simplest fix
2. **Check n8n version** - older versions may not support `$env`
3. **Check n8n settings** - ensure environment variables are enabled
4. **Use Code node** (Option 3) - workaround for env var issues

### Problem: Expressions not resolving

**Solutions:**
1. **Check node names** - ensure "Generate HTML" node exists
2. **Verify data flow** - execute previous nodes first
3. **Check expression syntax** - use correct n8n expression format
4. **Test expressions** - use "Execute previous nodes" to test

### Problem: Email not sending

**Solutions:**
1. **Check SMTP credential** - verify Gmail SMTP is configured
2. **Check From Email** - must match Gmail address in SMTP credential
3. **Verify attachments** - ensure PDF binary data is available
4. **Check n8n logs** - review execution logs for errors

---

## 📋 Quick Reference

### Minimal Working Configuration

**From Email**: `yourname@gmail.com` (direct value, no expression)

**To Email**: `{{ $('Generate HTML').item.json.email }}`

**Subject**: `Your Travel Itinerary: {{ $('Generate HTML').item.json.city }}`

**Text**: 
```
Please find your travel itinerary attached.

Trip: {{ $('Generate HTML').item.json.city }}
Duration: {{ $('Generate HTML').item.json.durationDays }} days

Enjoy your trip!
```

**Attachments**: `{{ [{ name: 'itinerary.pdf', data: $binary.data.data, type: 'application/pdf' }] }}`

---

## 💡 Best Practices

1. **Use direct email** for From Email if env vars don't work
2. **Test expressions** before saving
3. **Verify SMTP credential** is selected
4. **Check execution logs** if email fails
5. **Use consistent email format** (Text or HTML)

---

## 📚 Related Documentation

- [Gmail App Password Guide](./GMAIL_APP_PASSWORD_GUIDE.md)
- [n8n Integration Guide](./N8N_INTEGRATION_GUIDE.md)
- [n8n Quick Reference](./N8N_QUICK_REFERENCE.md)

---

**Last Updated**: 2024-01-15  
**Status**: ✅ Complete Configuration Guide
