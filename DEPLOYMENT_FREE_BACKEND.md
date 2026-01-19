# 🆓 Free Backend Deployment Options

Since Railway's free tier expired, here are the best **free alternatives** for deploying your FastAPI backend.

## ⚠️ Important: GitHub Pages Limitation

**GitHub Pages can only host static sites** (HTML, CSS, JavaScript). It **cannot** run server-side applications like FastAPI/Python backends.

You need an external hosting service for your backend.

---

## 🎯 Best Free Alternatives

### Option 1: Render (⭐ RECOMMENDED - Easiest)

**Why Render:**
- ✅ **Free tier available** - Web services free forever
- ✅ **Easy setup** - Similar to Railway
- ✅ **Auto-deploys from GitHub** - Just connect your repo
- ✅ **Automatic HTTPS** - SSL included
- ✅ **Good FastAPI support** - Works out of the box
- ✅ **No credit card required** (for free tier)

**Limitations:**
- ⚠️ **Spins down after 15 minutes of inactivity** - First request after sleep takes ~30 seconds
- ⚠️ **Limited resources** - 512MB RAM, 0.1 CPU
- ⚠️ **Free tier suitable for development/testing**

**Cost:** $0/month (free tier)

**Setup Time:** ~10 minutes

---

### Option 2: Fly.io

**Why Fly.io:**
- ✅ **Good performance** - Fast cold starts
- ✅ **Global deployment** - Edge locations
- ✅ **Free tier available** - 3 shared-cpu VMs, 3GB storage
- ✅ **Docker-based** - Easy containerization

**Limitations:**
- ⚠️ **New users may need paid plan** - Free tier shrinking
- ⚠️ **Requires credit card** (but won't charge on free tier)
- ⚠️ **More complex setup** - Need Dockerfile

**Cost:** $0/month (free tier, if available)

**Setup Time:** ~15 minutes

---

### Option 3: Google Cloud Run (Always Free)

**Why Cloud Run:**
- ✅ **Truly free** - 2 million requests/month free
- ✅ **Scales to zero** - No cost when idle
- ✅ **Container-based** - Docker support
- ✅ **No sleep issues** - Always available

**Limitations:**
- ⚠️ **Requires Google Cloud account** - Credit card needed
- ⚠️ **More complex setup** - Need to configure Cloud Run
- ⚠️ **Region restrictions** - Free tier only in certain regions

**Cost:** $0/month (within free tier limits)

**Setup Time:** ~20 minutes

---

### Option 4: PythonAnywhere

**Why PythonAnywhere:**
- ✅ **Simple setup** - No Docker needed
- ✅ **Python-focused** - Built for Python apps
- ✅ **Free tier available** - Good for small apps

**Limitations:**
- ⚠️ **Apps sleep** - After inactivity
- ⚠️ **Limited resources** - CPU and storage limits
- ⚠️ **No custom domain on free tier**

**Cost:** $0/month (free tier)

**Setup Time:** ~15 minutes

---

## 🚀 Recommended: Render Setup

I've already created a workflow for Render deployment. Here's how to set it up:

### Step 1: Create Render Account (2 minutes)

1. Go to https://render.com
2. Sign up with GitHub (recommended)
3. Verify your email

### Step 2: Create Web Service (5 minutes)

1. Click **New +** → **Web Service**
2. Connect your GitHub repository
3. Configure:
   - **Name**: `travel-assistant-backend`
   - **Environment**: `Python 3` (will use `runtime.txt` or `PYTHON_VERSION` env var)
   - **Build Command**: `cd backend && python setup_python_version.py && pip install --upgrade pip && pip install --prefer-binary -r requirements.txt`
   - **Start Command**: `cd backend && python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: **Free**

**Note:** 
- The `runtime.txt` file in the `backend` folder pins Python to 3.11.9 by default
- You can override by setting `PYTHON_VERSION` environment variable (e.g., `3.11.9`)
- Python 3.11.9 has better pre-built wheel support and avoids Rust compilation issues

### Step 3: Add Environment Variables (2 minutes)

In Render dashboard → Your Service → Environment:

Add all variables from `backend/env.example`:
```
GROQ_API_KEY=your_groq_api_key
GROQ_API_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama-3.3-70b-versatile
GOOGLE_MAPS_API_KEY=your_google_maps_key (optional)
N8N_WEBHOOK_URL=your_n8n_webhook (optional)
CHROMA_PERSIST_DIR=./chroma_db
OVERPASS_API_URL=https://overpass-api.de/api/interpreter
OPEN_METEO_API_URL=https://api.open-meteo.com/v1
APP_NAME=Voice-First Travel Assistant
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=https://yourusername.github.io
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
PYTHON_VERSION=3.11.9 (optional - overrides runtime.txt)
```

### Step 4: Get Render API Key (1 minute)

1. Go to https://dashboard.render.com/account/api-keys
2. Create a new API key
3. Copy the key

### Step 5: Update GitHub Secrets (2 minutes)

Go to: **GitHub Repo → Settings → Secrets → Actions**

Add:
```
RENDER_API_KEY=your_render_api_key
RENDER_SERVICE_ID=your_render_service_id
```

**To get SERVICE_ID:**
- Go to Render dashboard → Your service
- Check the URL: `https://dashboard.render.com/web/your-service-id`
- Or check service settings

### Step 6: Update Workflow (Already Done!)

The workflow `.github/workflows/deploy-backend-render.yml` is ready. Just make sure it's enabled.

### Step 7: Deploy! (1 minute)

**Option A:** Push to `main` → Auto-deploys!

**Option B:** Manually trigger in Render dashboard → **Manual Deploy**

---

## 🔄 Using GitHub Actions with Render

The workflow will:
1. Build your backend
2. Deploy to Render using Render API
3. Run health check

**Note:** Render also auto-deploys on GitHub push if you connected the repo. You can use either:
- **Render auto-deploy** (simpler, no GitHub Actions needed)
- **GitHub Actions deploy** (more control, CI/CD integration)

---

## 📊 Comparison Table

| Platform | Free Tier | Sleep? | Setup | Best For |
|----------|-----------|--------|-------|----------|
| **Render** ⭐ | Yes | 15 min idle | Easy | Development, testing |
| **Fly.io** | Limited | No | Medium | Production-ready |
| **Cloud Run** | Yes | No | Hard | Always-on apps |
| **PythonAnywhere** | Yes | Yes | Easy | Simple Python apps |

---

## 🐛 Troubleshooting

### Render Issues

**"Service spins down"**
- This is normal on free tier
- First request after sleep takes ~30 seconds
- Consider upgrading to paid ($7/month) for always-on

**"Build fails"**
- Check build logs in Render dashboard
- Verify `requirements.txt` is correct
- Check Python version (3.10+)
- **"maturin/Rust error"**: 
  1. Ensure `backend/runtime.txt` exists with `python-3.11.9` to pin Python version
  2. Use build command with `--prefer-binary` flag: `pip install --upgrade pip && pip install --prefer-binary -r requirements.txt`
  3. Python 3.11 has better pre-built wheel support than 3.13

**"Deployment fails"**
- Verify `RENDER_API_KEY` is correct
- Check `RENDER_SERVICE_ID` matches your service
- Review GitHub Actions logs

---

## 💡 Pro Tips

1. **Use Render auto-deploy** - Simpler than GitHub Actions
2. **Monitor sleep times** - Free tier sleeps after 15 min idle
3. **Upgrade if needed** - $7/month for always-on (optional)
4. **Set up health checks** - Keep service awake (if allowed)

---

## 🎯 Quick Start: Render

1. **Sign up**: https://render.com
2. **Create service**: New + → Web Service
3. **Connect GitHub**: Link your repository
4. **Configure**: Use settings above
5. **Deploy**: Click "Create Web Service"

**That's it!** Your backend will be live in ~5 minutes.

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [FastAPI on Render](https://render.com/docs/deploy-fastapi)
- [Render Free Tier](https://render.com/docs/free)

---

**Status:** ✅ Ready to deploy  
**Recommended:** Render (easiest, free tier available)  
**Cost:** $0/month (free tier)
