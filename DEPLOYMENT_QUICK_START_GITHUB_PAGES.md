# 🚀 Deployment Quick Start - GitHub Pages Edition

Get your Voice-First Travel Assistant deployed with frontend on GitHub Pages!

## ⚡ Fastest Path: GitHub Pages (Frontend) + Railway (Backend)

### Step 1: Enable GitHub Pages (1 minute)

1. Go to your GitHub repository
2. Click **Settings** → **Pages**
3. Under **Source**, select: **GitHub Actions**
4. Click **Save**

### Step 2: Get Railway Token (2 minutes)

**Railway Setup:**
1. Go to https://railway.app and sign up/login
2. Create new project → Deploy from GitHub repo
3. Get your token:
   - Go to https://railway.app/account/tokens → Create token
4. Get IDs from Railway dashboard:
   - `PROJECT_ID` - Found in project settings
   - `SERVICE_ID` - Found in service settings

### Step 3: Add GitHub Secrets (2 minutes)

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**

Add these secrets:

```
# Railway (Backend)
RAILWAY_TOKEN=your_railway_token
RAILWAY_PROJECT_ID=your_railway_project_id
RAILWAY_SERVICE_ID=your_railway_service_id

# API Keys
GROQ_API_KEY=your_groq_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_key (optional)
N8N_WEBHOOK_URL=your_n8n_webhook (optional)

# URLs (set after first deployment)
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
CORS_ORIGINS=https://yourusername.github.io
BACKEND_URL=https://your-backend.railway.app
```

### Step 4: Configure Railway Environment Variables (1 minute)

1. Go to Railway Dashboard → Your Project → Variables
2. Add all variables from `backend/env.example`
3. Set `CORS_ORIGINS` to your GitHub Pages URL:
   ```
   CORS_ORIGINS=https://yourusername.github.io
   ```
   (Update this after frontend is deployed)

### Step 5: Deploy! (1 minute)

**Option A: Automatic**
- Push to `main` branch → Deployment starts automatically!

**Option B: Manual**
- Go to Actions tab → Select workflow → Run workflow

### Step 6: Get Your URLs (1 minute)

After first deployment:

1. **Frontend URL:**
   - Format: `https://yourusername.github.io/your-repo-name`
   - Check in repository Settings → Pages

2. **Backend URL:**
   - Check Railway dashboard
   - Format: `https://your-app.railway.app`

3. **Update secrets:**
   - Update `NEXT_PUBLIC_API_URL` in GitHub secrets with backend URL
   - Update `CORS_ORIGINS` in Railway with frontend URL
   - Redeploy both (push a commit or trigger workflows)

## ✅ Verify Deployment

1. **Frontend**: Visit `https://yourusername.github.io/your-repo-name`
2. **Backend**: `curl https://your-backend.railway.app/health`
3. **Test**: Try planning a trip!

## 🎯 That's It!

Your app is now live on GitHub Pages! 🎉

- **Frontend**: Hosted on GitHub Pages (free, forever)
- **Backend**: Hosted on Railway (free tier available)

## 🆘 Troubleshooting

**GitHub Pages not working?**
- Make sure Pages is enabled (Settings → Pages → Source: GitHub Actions)
- Check Actions tab for workflow status
- Verify repository is public (or you have GitHub Pro)

**Deployment fails?**
- Check GitHub Actions logs
- Verify all secrets are set
- Check Railway logs

**CORS errors?**
- Make sure `CORS_ORIGINS` includes your GitHub Pages URL
- Format: `https://yourusername.github.io`
- Restart backend after updating CORS

**API not working?**
- Verify `NEXT_PUBLIC_API_URL` is set correctly in GitHub secrets
- Check backend health endpoint
- Verify API keys are correct

## 📚 More Information

- **Detailed GitHub Pages Guide**: See `DEPLOYMENT_GITHUB_PAGES.md`
- **Full Deployment Guide**: See `docs/GITHUB_ACTIONS_DEPLOYMENT.md`
- **Strategy Analysis**: See `docs/DEPLOYMENT_STRATEGY.md`

---

**Time to deploy:** ~10 minutes  
**Cost:** $0/month (free tier)  
**Frontend hosting:** GitHub Pages (free forever)  
**Backend hosting:** Railway (free tier available)
