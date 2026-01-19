# CORS Fix for GitHub Pages Frontend

## Problem

You're seeing this error:
```
Access to XMLHttpRequest at 'https://travel-planning-assistant.onrender.com/api/chat' 
from origin 'https://sriram07ms-collab.github.io' has been blocked by CORS policy: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

This happens because the backend on Render doesn't have your GitHub Pages frontend URL in its allowed CORS origins.

## Solution

Add your GitHub Pages frontend URL to the `CORS_ORIGINS` environment variable in Render.

### Step 1: Get Your Frontend URL

Your frontend is deployed at:
```
https://sriram07ms-collab.github.io/-voice-first-AI-travel-planning-assistant
```

**Note:** For CORS, you typically need to include the base domain without the path:
```
https://sriram07ms-collab.github.io
```

However, if you want to be more specific, you can include the full path.

### Step 2: Update Render Environment Variables

1. **Go to your Render Dashboard**
   - Navigate to: https://dashboard.render.com
   - Find your backend service: `travel-planning-assistant`

2. **Open Environment Variables**
   - Click on your service
   - Go to the **Environment** tab
   - Find the `CORS_ORIGINS` variable

3. **Update CORS_ORIGINS**
   
   **Current value (example):**
   ```
   http://localhost:3000,http://localhost:3001
   ```
   
   **New value (add your GitHub Pages URL):**
   ```
   http://localhost:3000,http://localhost:3001,https://sriram07ms-collab.github.io
   ```
   
   **Or if you want to include the full path:**
   ```
   http://localhost:3000,http://localhost:3001,https://sriram07ms-collab.github.io,https://sriram07ms-collab.github.io/-voice-first-AI-travel-planning-assistant
   ```

4. **Save and Redeploy**
   - Click **Save Changes**
   - Render will automatically redeploy your service
   - Wait for deployment to complete (usually 2-3 minutes)

### Step 3: Verify the Fix

1. **Check the deployment logs** in Render to ensure it started successfully
2. **Test the frontend** - Try sending a message from your GitHub Pages site
3. **Check browser console** - The CORS error should be gone

## Alternative: Allow All Origins (Development Only)

⚠️ **Warning:** Only use this for development/testing. Not recommended for production.

If you want to allow all origins temporarily:

```
CORS_ORIGINS=*
```

Or in the environment variable, set:
```
*
```

**Note:** The backend code supports `*` as a wildcard, but it's better to be specific for security.

## Format Notes

- **Comma-separated:** Multiple origins should be separated by commas
- **No spaces:** Avoid spaces around commas (though the code handles them)
- **Protocol required:** Always include `http://` or `https://`
- **No trailing slash:** Don't include trailing slashes in the origin URL

## Example CORS_ORIGINS Values

**For local development only:**
```
http://localhost:3000,http://localhost:3001,http://localhost:3002
```

**For GitHub Pages deployment:**
```
http://localhost:3000,https://sriram07ms-collab.github.io
```

**For multiple deployments:**
```
http://localhost:3000,https://sriram07ms-collab.github.io,https://your-custom-domain.com
```

## Troubleshooting

### Still seeing CORS errors?

1. **Wait for deployment** - Render needs to fully restart the service
2. **Clear browser cache** - Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
3. **Check the exact origin** - Open browser DevTools → Network tab → Check the "Origin" header in the request
4. **Verify environment variable** - In Render, check that `CORS_ORIGINS` is set correctly
5. **Check backend logs** - Look for any CORS-related errors in Render logs

### Preflight request failing?

If you see "preflight request doesn't pass access control check", also verify:
- `CORS_ALLOW_METHODS` includes the methods you're using (usually `*` or `GET,POST,PUT,DELETE,OPTIONS`)
- `CORS_ALLOW_HEADERS` includes the headers you're sending (usually `*` or specific headers)

## Quick Reference

**Your Frontend URL:**
```
https://sriram07ms-collab.github.io
```

**Your Backend URL:**
```
https://travel-planning-assistant.onrender.com
```

**CORS_ORIGINS should include:**
```
https://sriram07ms-collab.github.io
```
