# CORS Error Troubleshooting Guide

## Current Error

```
Access to XMLHttpRequest at 'https://travel-planning-assistant.onrender.com/api/chat' 
from origin 'https://sriram07ms-collab.github.io' has been blocked by CORS policy: 
Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

## Step-by-Step Fix

### Step 1: Verify Backend is Running

First, check if your backend is accessible:

1. **Test the health endpoint:**
   ```bash
   curl https://travel-planning-assistant.onrender.com/health
   ```
   
   Or open in browser: https://travel-planning-assistant.onrender.com/health

2. **If you get a timeout or error:**
   - The service might be sleeping (free tier spins down after 15 min idle)
   - Wait 30-60 seconds and try again (first request wakes it up)
   - Check Render dashboard → Logs tab for errors

### Step 2: Verify CORS_ORIGINS in Render

1. **Go to Render Dashboard:**
   - https://dashboard.render.com
   - Click on your service: `travel-planning-assistant`

2. **Check Environment Variables:**
   - Go to **Environment** tab
   - Find `CORS_ORIGINS`
   - **It should contain:**
     ```
     http://localhost:3000,http://localhost:3001,https://sriram07ms-collab.github.io
     ```
   
3. **If it's missing or incorrect:**
   - Click **Edit** next to `CORS_ORIGINS`
   - Update to:
     ```
     http://localhost:3000,http://localhost:3001,https://sriram07ms-collab.github.io
     ```
   - Click **Save Changes**
   - **Wait for automatic redeployment** (2-3 minutes)

### Step 3: Verify CORS Methods and Headers

While you're in the Environment tab, also check:

1. **CORS_ALLOW_METHODS** should be:
   ```
   *
   ```
   Or:
   ```
   GET,POST,PUT,DELETE,OPTIONS
   ```

2. **CORS_ALLOW_HEADERS** should be:
   ```
   *
   ```

3. **CORS_ALLOW_CREDENTIALS** should be:
   ```
   true
   ```

### Step 4: Check Deployment Status

1. **In Render Dashboard:**
   - Go to **Logs** tab
   - Check if the latest deployment completed successfully
   - Look for any errors during startup

2. **Verify the service is "Live":**
   - The service status should show "Live" (green)
   - If it shows "Sleeping" or "Building", wait for it to complete

### Step 5: Test CORS Directly

Test if CORS is working by checking the response headers:

1. **Open browser DevTools** (F12)
2. **Go to Network tab**
3. **Make a request from your frontend**
4. **Check the OPTIONS request (preflight):**
   - Look for `Access-Control-Allow-Origin` header
   - Should contain: `https://sriram07ms-collab.github.io`

5. **Or test with curl:**
   ```bash
   curl -H "Origin: https://sriram07ms-collab.github.io" \
        -H "Access-Control-Request-Method: POST" \
        -H "Access-Control-Request-Headers: Content-Type" \
        -X OPTIONS \
        https://travel-planning-assistant.onrender.com/api/chat \
        -v
   ```
   
   Look for:
   ```
   < Access-Control-Allow-Origin: https://sriram07ms-collab.github.io
   ```

### Step 6: Clear Browser Cache

Sometimes browsers cache CORS responses:

1. **Hard refresh:**
   - Windows/Linux: `Ctrl + Shift + R`
   - Mac: `Cmd + Shift + R`

2. **Or clear cache:**
   - Open DevTools (F12)
   - Right-click refresh button → "Empty Cache and Hard Reload"

### Step 7: Check Backend Logs

1. **In Render Dashboard:**
   - Go to **Logs** tab
   - Look for any CORS-related errors
   - Check if the service started correctly

2. **Look for startup messages:**
   - Should see: "Application startup complete"
   - Should see: CORS origins being loaded

## Common Issues

### Issue 1: Service is Sleeping

**Symptom:** First request times out, subsequent requests work

**Fix:** 
- Wait 30-60 seconds for service to wake up
- Or upgrade to paid tier ($7/month) for always-on

### Issue 2: CORS_ORIGINS Not Updated

**Symptom:** Still seeing CORS errors after adding origin

**Fix:**
- Double-check the exact value in Render
- Make sure there are no extra spaces
- Ensure it's saved and service redeployed

### Issue 3: Wrong Origin Format

**Symptom:** CORS still failing

**Fix:**
- Use: `https://sriram07ms-collab.github.io` (no trailing slash)
- Don't use: `https://sriram07ms-collab.github.io/` (with slash)
- Don't use: `https://sriram07ms-collab.github.io/-voice-first-AI-travel-planning-assistant` (with path)

### Issue 4: Service Not Redeployed

**Symptom:** Changes saved but not taking effect

**Fix:**
- Check if deployment is in progress
- Wait for deployment to complete (2-3 minutes)
- Check Logs tab for deployment status

## Quick Test: Allow All Origins (Temporary)

If you want to test if CORS is the issue, temporarily allow all origins:

1. **In Render, set CORS_ORIGINS to:**
   ```
   *
   ```

2. **Save and wait for redeployment**

3. **Test your frontend** - if it works, CORS was the issue

4. **Then change back to specific origins:**
   ```
   http://localhost:3000,http://localhost:3001,https://sriram07ms-collab.github.io
   ```

⚠️ **Warning:** Only use `*` for testing. Change back to specific origins for security.

## Verification Checklist

- [ ] Backend health endpoint responds: `/health`
- [ ] CORS_ORIGINS includes: `https://sriram07ms-collab.github.io`
- [ ] CORS_ALLOW_METHODS is: `*` or includes `OPTIONS,POST`
- [ ] CORS_ALLOW_HEADERS is: `*`
- [ ] Service status is "Live" in Render
- [ ] Latest deployment completed successfully
- [ ] Browser cache cleared
- [ ] Tested with hard refresh

## Still Not Working?

If you've tried everything above:

1. **Check the exact error in browser console:**
   - Open DevTools → Console tab
   - Copy the full error message

2. **Check Network tab:**
   - Look at the failed request
   - Check Request Headers (especially `Origin`)
   - Check Response Headers (look for CORS headers)

3. **Verify backend logs:**
   - Check Render logs for any startup errors
   - Look for CORS configuration being loaded

4. **Test backend directly:**
   ```bash
   curl -X POST https://travel-planning-assistant.onrender.com/api/chat \
        -H "Content-Type: application/json" \
        -H "Origin: https://sriram07ms-collab.github.io" \
        -d '{"message": "test"}'
   ```

## Need More Help?

If the issue persists, provide:
1. The exact CORS_ORIGINS value from Render
2. Backend logs from Render (startup section)
3. Browser console error (full message)
4. Network tab screenshot showing the failed request
