# GitHub Actions Deployment Guide

Complete guide for deploying the Voice-First Travel Assistant using GitHub Actions.

## 🎯 Deployment Strategy Overview

This guide provides **two deployment approaches**, both using GitHub Actions:

### Option 1: Recommended (Easiest & Free)
- **Frontend**: GitHub Actions → Vercel (automatic deployment)
- **Backend**: GitHub Actions → Railway (free tier, easy setup)

### Option 2: Fully GitHub-Based
- **Frontend**: GitHub Actions → GitHub Pages (static export)
- **Backend**: GitHub Actions → Railway/Render (still needs external hosting)

---

## 📋 Prerequisites

1. **GitHub Repository**: Your code should be in a GitHub repository
2. **API Keys**: 
   - Groq API key (for LLM)
   - Google Maps API key (optional)
   - n8n webhook URL (optional)
3. **Accounts** (free tiers available):
   - Vercel account (for frontend)
   - Railway account (for backend)

---

## 🚀 Option 1: Recommended Deployment (Vercel + Railway)

### Step 1: Set Up GitHub Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**

Add these secrets:

#### Frontend Secrets (for Vercel)
```
VERCEL_ORG_ID=your_vercel_org_id
VERCEL_PROJECT_ID=your_vercel_project_id
VERCEL_TOKEN=your_vercel_token
```

#### Backend Secrets (for Railway)
```
RAILWAY_TOKEN=your_railway_token
GROQ_API_KEY=your_groq_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_api_key (optional)
N8N_WEBHOOK_URL=your_n8n_webhook_url (optional)
```

#### Shared Secrets
```
FRONTEND_URL=https://your-frontend.vercel.app
BACKEND_URL=https://your-backend.railway.app
```

### Step 2: Get Vercel Credentials

1. **Install Vercel CLI** (one-time setup):
   ```bash
   npm i -g vercel
   ```

2. **Login to Vercel**:
   ```bash
   vercel login
   ```

3. **Link your project**:
   ```bash
   cd frontend
   vercel link
   ```
   This will create `.vercel` folder with `project.json` containing:
   - `orgId`: Your Vercel organization ID
   - `projectId`: Your Vercel project ID

4. **Get Vercel Token**:
   - Go to https://vercel.com/account/tokens
   - Create a new token
   - Copy the token

### Step 3: Get Railway Credentials

1. **Install Railway CLI**:
   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Get Railway Token**:
   - Go to https://railway.app/account/tokens
   - Create a new token
   - Copy the token

4. **Create a Railway Project** (one-time):
   - Go to https://railway.app
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository
   - Railway will auto-detect the backend

### Step 4: GitHub Actions Workflows

The workflows are already created in `.github/workflows/`:
- `deploy-frontend.yml` - Deploys frontend to Vercel
- `deploy-backend.yml` - Deploys backend to Railway

### Step 5: Configure Environment Variables

#### In Vercel Dashboard:
1. Go to your project → Settings → Environment Variables
2. Add:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   ```

#### In Railway Dashboard:
1. Go to your project → Variables
2. Add all variables from `backend/env.example`

### Step 6: Trigger Deployment

**Automatic**: Push to `main` branch triggers deployment

**Manual**: Go to Actions tab → Select workflow → Run workflow

---

## 🏗️ Option 2: GitHub Pages Deployment (Fully GitHub-Based)

### Frontend: GitHub Pages

1. **Configure Next.js for Static Export**:
   - Already configured in `next.config.js`
   - Uses `output: 'export'` for static generation

2. **GitHub Actions Workflow**:
   - `deploy-frontend-pages.yml` handles deployment
   - Automatically builds and deploys to GitHub Pages

3. **Enable GitHub Pages**:
   - Go to repository → Settings → Pages
   - Source: GitHub Actions
   - Save

4. **Update CORS in Backend**:
   - Add your GitHub Pages URL to `CORS_ORIGINS`
   - Format: `https://yourusername.github.io/your-repo-name`

### Backend: Still Needs External Hosting

Backend cannot be hosted on GitHub Pages (needs a server). Use Railway or Render.

---

## 📁 Workflow Files Structure

```
.github/
└── workflows/
    ├── deploy-frontend.yml      # Vercel deployment
    ├── deploy-backend.yml       # Railway deployment
    ├── deploy-frontend-pages.yml # GitHub Pages deployment
    └── ci.yml                   # Continuous Integration (tests)
```

---

## 🔧 Workflow Details

### Frontend Deployment (Vercel)

**Triggers**:
- Push to `main` branch
- Pull requests (preview deployments)
- Manual workflow dispatch

**Steps**:
1. Checkout code
2. Setup Node.js
3. Install dependencies
4. Build Next.js app
5. Deploy to Vercel using Vercel CLI

### Backend Deployment (Railway)

**Triggers**:
- Push to `main` branch
- Manual workflow dispatch

**Steps**:
1. Checkout code
2. Setup Python
3. Install Railway CLI
4. Deploy to Railway using Railway CLI

---

## 🔐 Security Best Practices

1. **Never commit secrets** to repository
2. **Use GitHub Secrets** for all sensitive data
3. **Rotate tokens** regularly
4. **Limit token permissions** (read-only when possible)
5. **Use environment-specific secrets** (production vs staging)

---

## 🧪 Testing Deployment

### 1. Health Check
```bash
curl https://your-backend.railway.app/health
```

### 2. Frontend Connection
```bash
curl https://your-frontend.vercel.app
```

### 3. API Test
```bash
curl -X POST https://your-backend.railway.app/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a trip to Jaipur"}'
```

---

## 🐛 Troubleshooting

### Frontend Issues

**Problem: Build fails**
- Check Node.js version in workflow
- Verify `package.json` dependencies
- Check build logs in GitHub Actions

**Problem: Vercel deployment fails**
- Verify `VERCEL_TOKEN` is correct
- Check `.vercel` folder exists (or set secrets manually)
- Verify project is linked in Vercel

**Problem: API calls fail**
- Check `NEXT_PUBLIC_API_URL` is set correctly
- Verify backend CORS allows frontend origin
- Check browser console for errors

### Backend Issues

**Problem: Railway deployment fails**
- Verify `RAILWAY_TOKEN` is correct
- Check Python version compatibility
- Verify all environment variables are set
- Check Railway logs

**Problem: Health check fails**
- Verify `/health` endpoint exists
- Check server is running
- Verify port configuration

**Problem: CORS errors**
- Add frontend URL to `CORS_ORIGINS`
- Restart backend after changing CORS
- Check CORS middleware configuration

---

## 📊 Monitoring

### GitHub Actions
- View workflow runs in Actions tab
- Check logs for each step
- Set up notifications for failures

### Vercel
- Built-in analytics
- Performance monitoring
- Error tracking

### Railway
- Real-time logs
- Metrics dashboard
- Error tracking

---

## 🔄 Continuous Deployment

### Automatic Deployment
- **Main branch**: Deploys to production
- **Feature branches**: Create preview deployments (Vercel)

### Manual Deployment
- Use "Run workflow" button in GitHub Actions
- Useful for testing before merging

---

## 💰 Cost Estimation

### Free Tier Limits

**Vercel**:
- 100GB bandwidth/month
- Unlimited deployments
- Preview deployments included

**Railway**:
- $5 free credit/month
- ~500 hours of runtime
- Auto-sleeps after inactivity

**GitHub Actions**:
- 2,000 minutes/month (free)
- Unlimited for public repos

**Total**: $0/month for small projects! 🎉

---

## 📝 Deployment Checklist

### Before First Deployment
- [ ] All secrets added to GitHub
- [ ] Vercel project created and linked
- [ ] Railway project created
- [ ] Environment variables configured
- [ ] CORS configured correctly
- [ ] Health check endpoint working

### After Deployment
- [ ] Frontend accessible
- [ ] Backend health check passes
- [ ] API endpoints working
- [ ] Frontend connects to backend
- [ ] Voice input works
- [ ] No CORS errors
- [ ] Error handling works

---

## 🚀 Quick Start

1. **Add secrets to GitHub** (see Step 1 above)
2. **Get Vercel credentials** (see Step 2 above)
3. **Get Railway credentials** (see Step 3 above)
4. **Push to main branch** - deployment starts automatically!
5. **Check Actions tab** for deployment status
6. **Visit your deployed app** 🎉

---

## 📚 Additional Resources

- [Vercel Documentation](https://vercel.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Next.js Deployment](https://nextjs.org/docs/deployment)

---

## 🆘 Support

If you encounter issues:
1. Check GitHub Actions logs
2. Check Vercel/Railway logs
3. Verify all secrets are set correctly
4. Test endpoints individually
5. Review this guide

**Happy Deploying!** 🚀
