# CORS Verification Steps - Quick Fix Guide

## Current Issue

Your backend is running, but CORS is blocking requests from:
- **Frontend:** `https://sriram07ms-collab.github.io`
- **Backend:** `https://travel-planning-assistant.onrender.com`

## Quick Fix (3 Steps)

### Step 1: Verify Current CORS Configuration

1. **Open this URL in your browser:**
   ```
   https://travel-planning-assistant.onrender.com/api/cors-config
   ```

2. **Check the response** - It will show what CORS origins are currently configured

3. **Look for:** `https://sriram07ms-collab.github.io` in the `cors_origins` array

### Step 2: Update CORS_ORIGINS in Render

1. **Go to Render Dashboard:**
   - https://dashboard.render.com
   - Click on: `travel-planning-assistant`

2. **Go to Environment Tab:**
   - Click **Environment** in the left sidebar

3. **Find CORS_ORIGINS:**
   - Scroll down to find `CORS_ORIGINS`
   - Click **Edit** (pencil icon)

4. **Update the value:**
   
   **If it's currently:**
   ```
   http://localhost:3000,http://localhost:3001
   ```
   
   **Change it to:**
   ```
   http://localhost:3000,http://localhost:3001,https://sriram07ms-collab.github.io
   ```
   
   **Important:**
   - No spaces around commas
   - No trailing slash
   - Exact format: `https://sriram07ms-collab.github.io`

5. **Save:**
   - Click **Save Changes**
   - Render will automatically redeploy (wait 2-3 minutes)

### Step 3: Verify the Fix

1. **Wait for deployment** (check Logs tab - should show "Live")

2. **Check CORS config again:**
   ```
   https://travel-planning-assistant.onrender.com/api/cors-config
   ```
   - Should now show `https://sriram07ms-collab.github.io` in the list

3. **Test your frontend:**
   - Go to: `https://sriram07ms-collab.github.io/-voice-first-AI-travel-planning-assistant`
   - Try sending a message
   - CORS error should be gone!

## Common Mistakes

❌ **Wrong:**
```
https://sriram07ms-collab.github.io/  (trailing slash)
https://sriram07ms-collab.github.io/-voice-first-AI-travel-planning-assistant  (with path)
http://sriram07ms-collab.github.io  (http instead of https)
```

✅ **Correct:**
```
https://sriram07ms-collab.github.io
```

## Still Not Working?

1. **Check the exact error in browser console**
2. **Verify the CORS config endpoint shows your URL**
3. **Check Render logs for any errors**
4. **Make sure service status is "Live"**
5. **Try hard refresh (Ctrl+Shift+R)**

## Test CORS Directly

You can test if CORS is working with this curl command:

```bash
curl -H "Origin: https://sriram07ms-collab.github.io" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     https://travel-planning-assistant.onrender.com/api/chat \
     -v
```

Look for this in the response:
```
< Access-Control-Allow-Origin: https://sriram07ms-collab.github.io
```

If you see that header, CORS is configured correctly!
