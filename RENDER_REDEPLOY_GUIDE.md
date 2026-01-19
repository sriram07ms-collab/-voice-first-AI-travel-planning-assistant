# Render Redeployment Guide - CORS Fix

## When You Update Environment Variables

When you update `CORS_ORIGINS` (or any environment variable) in Render:

### Automatic Redeployment

✅ **Render automatically redeploys** when you save environment variable changes.

**What happens:**
1. You click "Save Changes"
2. Render detects the change
3. Render automatically starts a new deployment
4. Old deployment is cancelled/replaced
5. New deployment uses the updated environment variables

### Do You Need to Manually Restart?

**Usually NO** - Render handles it automatically. But here's when you might need to:

#### Option 1: Wait for Automatic Redeployment (Recommended)

1. **Check if deployment is in progress:**
   - Go to Render Dashboard → Your service
   - Look at the top - should show "Deploying..." or "Live"
   - Check **Logs** tab - should show build/deploy activity

2. **If you see "Deploying...":**
   - ✅ Just wait (2-3 minutes)
   - The new deployment will use your updated `CORS_ORIGINS`
   - No action needed

3. **If service is "Live" but CORS still not working:**
   - The deployment might have completed before you saved the env var
   - Go to Option 2

#### Option 2: Manual Redeploy (If Needed)

If the service is "Live" and you just updated `CORS_ORIGINS`:

1. **Go to Render Dashboard:**
   - https://dashboard.render.com
   - Click your service: `travel-planning-assistant`

2. **Manual Deploy:**
   - Click **Manual Deploy** button (top right)
   - Select **Deploy latest commit**
   - Click **Deploy**
   - Wait 2-3 minutes

3. **Or Cancel and Redeploy:**
   - If there's a deployment in progress
   - Click **Cancel** (if available)
   - Then click **Manual Deploy** → **Deploy latest commit**

## Verify CORS is Fixed

After deployment completes:

1. **Check CORS config:**
   ```
   https://travel-planning-assistant.onrender.com/api/cors-config
   ```
   - Should show `https://sriram07ms-collab.github.io` in `cors_origins`

2. **Test your frontend:**
   - Go to your GitHub Pages site
   - Try sending a message
   - CORS error should be gone!

## Current Status Check

**If `/api/cors-config` still shows only localhost:**
- Environment variable change hasn't been applied yet
- Either wait for automatic redeploy, or manually trigger one

**If `/api/cors-config` shows your GitHub Pages URL:**
- ✅ CORS is configured correctly
- Test your frontend - it should work!

## Quick Checklist

- [ ] Updated `CORS_ORIGINS` in Render Environment tab
- [ ] Clicked "Save Changes"
- [ ] Checked if deployment is in progress
- [ ] Waited 2-3 minutes OR manually triggered redeploy
- [ ] Verified `/api/cors-config` shows your GitHub Pages URL
- [ ] Tested frontend - CORS error resolved

## Note About Spaces

I noticed in your screenshot there are spaces after some commas:
```
http://localhost:3000, http://localhost:3001,https://sriram07ms-collab.github.io
```

The backend code handles spaces (strips them), so this should work fine. But for consistency, you can remove spaces:
```
http://localhost:3000,http://localhost:3001,https://sriram07ms-collab.github.io
```

Both formats will work, but the second one is cleaner.
