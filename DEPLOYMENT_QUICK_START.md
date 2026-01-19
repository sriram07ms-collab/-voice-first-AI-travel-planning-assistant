# 🚀 Deployment Quick Start Guide

Get your Voice-First Travel Assistant deployed in 10 minutes!

## ⚡ Recommended Path: GitHub Pages (Frontend) + Railway (Backend)

**Want GitHub Pages?** See [DEPLOYMENT_QUICK_START_GITHUB_PAGES.md](DEPLOYMENT_QUICK_START_GITHUB_PAGES.md) for the GitHub Pages quick start guide.

## ⚡ Alternative Path: Vercel + Railway

### Step 1: Get Your Tokens (5 minutes)

#### Vercel Setup
1. Go to https://vercel.com and sign up/login
2. Install Vercel CLI: `npm i -g vercel`
3. In your project: `cd frontend && vercel link`
4. Get your tokens:
   - Go to https://vercel.com/account/tokens → Create token
   - Check `.vercel/project.json` for `orgId` and `projectId`

#### Railway Setup
1. Go to https://railway.app and sign up/login
2. Create new project → Deploy from GitHub repo
3. Get your token:
   - Go to https://railway.app/account/tokens → Create token

### Step 2: Add GitHub Secrets (2 minutes)

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**

Add these secrets:

```
# Vercel
VERCEL_TOKEN=your_vercel_token
VERCEL_ORG_ID=your_org_id
VERCEL_PROJECT_ID=your_project_id

# Railway
RAILWAY_TOKEN=your_railway_token

# API Keys
GROQ_API_KEY=your_groq_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_key (optional)
N8N_WEBHOOK_URL=your_n8n_webhook (optional)

# URLs (set after first deployment)
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
CORS_ORIGINS=https://your-frontend.vercel.app
BACKEND_URL=https://your-backend.railway.app
```

### Step 3: Configure Vercel Environment Variables (1 minute)

1. Go to Vercel Dashboard → Your Project → Settings → Environment Variables
2. Add:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   ```
   (Update this after backend is deployed)

### Step 4: Configure Railway Environment Variables (1 minute)

1. Go to Railway Dashboard → Your Project → Variables
2. Add all variables from `backend/env.example`
3. Set `CORS_ORIGINS` to your Vercel URL (after frontend is deployed)

### Step 5: Deploy! (1 minute)

**Option A: Automatic**
- Push to `main` branch → Deployment starts automatically!

**Option B: Manual**
- Go to Actions tab → Select workflow → Run workflow

### Step 6: Update URLs (1 minute)

After first deployment:

1. **Get your URLs:**
   - Frontend: Check Vercel dashboard
   - Backend: Check Railway dashboard

2. **Update secrets:**
   - Update `NEXT_PUBLIC_API_URL` in GitHub secrets
   - Update `CORS_ORIGINS` in Railway variables
   - Update `NEXT_PUBLIC_API_URL` in Vercel environment variables

3. **Redeploy:**
   - Push a commit or manually trigger workflows

## ✅ Verify Deployment

1. **Frontend**: Visit your Vercel URL
2. **Backend**: `curl https://your-backend.railway.app/health`
3. **Test**: Try planning a trip!

## 🎯 That's It!

Your app is now live! 🎉

For detailed information, see [docs/GITHUB_ACTIONS_DEPLOYMENT.md](docs/GITHUB_ACTIONS_DEPLOYMENT.md)

## 🆘 Troubleshooting

**Deployment fails?**
- Check GitHub Actions logs
- Verify all secrets are set
- Check Vercel/Railway logs

**CORS errors?**
- Make sure `CORS_ORIGINS` includes your frontend URL
- Restart backend after updating CORS

**API not working?**
- Verify `NEXT_PUBLIC_API_URL` is set correctly
- Check backend health endpoint
- Verify API keys are correct
