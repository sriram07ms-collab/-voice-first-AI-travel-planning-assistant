# 🚀 Quick Start: Deploy Backend to Render (Free)

Get your backend deployed to Render in 10 minutes!

## ⚡ Why Render?

- ✅ **Free tier available** - No credit card needed
- ✅ **Easy setup** - Similar to Railway
- ✅ **Auto-deploys from GitHub** - Just connect repo
- ✅ **Automatic HTTPS** - SSL included

**Note:** Free tier spins down after 15 min idle (first request takes ~30 sec)

---

## 🚀 Quick Start (5 Steps)

### Step 1: Create Render Account (2 min)

1. Go to https://render.com
2. Click **Get Started for Free**
3. Sign up with **GitHub** (recommended)
4. Verify your email

### Step 2: Create Web Service (3 min)

1. Click **New +** → **Web Service**
2. Click **Connect account** → Select your GitHub account
3. Find your repository: `-voice-first-AI-travel-planning-assistant`
4. Click **Connect**

5. Configure service:
   - **Name**: `travel-assistant-backend`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3` (will use `runtime.txt` or `PYTHON_VERSION` env var)
   - **Build Command**: `python setup_python_version.py && pip install --upgrade pip && pip install --prefer-binary -r requirements.txt`
   - **Start Command**: `python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Select **Free**

**Important:** 
- The `runtime.txt` file in the `backend` folder pins Python to 3.11.9 by default
- You can override this by setting `PYTHON_VERSION` environment variable (e.g., `3.11.9` or `3.12.0`)
- Python 3.11.9 has better pre-built wheel support and avoids Rust compilation issues

6. Click **Create Web Service**

### Step 3: Add Environment Variables (2 min)

In Render dashboard → Your service → **Environment** tab:

Click **Add Environment Variable** and add:

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
# Note: CORS_ORIGINS can be a single URL or comma-separated: https://site1.com,https://site2.com
CORS_ALLOW_CREDENTIALS=true
CORS_ALLOW_METHODS=*
CORS_ALLOW_HEADERS=*
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
PYTHON_VERSION=3.11.9 (optional - overrides runtime.txt)
```

**Important:** 
- Update `CORS_ORIGINS` with your GitHub Pages URL after frontend is deployed!
- `PYTHON_VERSION` is optional - if not set, will use `runtime.txt` (default: 3.11.9)

### Step 4: Get Your Backend URL (1 min)

1. Wait for deployment to complete (~3-5 minutes)
2. Check **Logs** tab to see build progress
3. Once deployed, you'll see your URL:
   - Format: `https://travel-assistant-backend-xxxx.onrender.com`
   - Copy this URL

### Step 5: Update Frontend Configuration (1 min)

1. Go to GitHub → Your repo → **Settings** → **Secrets** → **Actions**
2. Update `NEXT_PUBLIC_API_URL` with your Render URL:
   ```
   NEXT_PUBLIC_API_URL=https://travel-assistant-backend-xxxx.onrender.com
   ```
3. Update `CORS_ORIGINS` in Render with your GitHub Pages URL

---

## ✅ Verify Deployment

1. **Check Render dashboard** - Service should show "Live"
2. **Test health endpoint**:
   ```bash
   curl https://your-backend.onrender.com/health
   ```
3. **Test API**:
   ```bash
   curl https://your-backend.onrender.com/
   ```

---

## 🎯 That's It!

Your backend is now live on Render! 🎉

**Backend URL:** `https://your-backend.onrender.com`

---

## 🔄 Auto-Deployment

Render automatically deploys when you:
- Push to `main` branch
- Merge a pull request

**No GitHub Actions needed!** (But you can use it if you want more control)

---

## 🐛 Troubleshooting

### ⚠️ Build Error: "maturin failed" or "Rust compilation error"

**If you see this error:**
```
error: failed to create directory `/usr/local/cargo/registry/...`
Read-only file system (os error 30)
💥 maturin failed
```

**This happens when:**
- Render uses Python 3.13 (too new, no pre-built wheels)
- Packages try to compile Rust code from source

**Fix (2 steps):**

1. **Set Python version** (choose one method):
   - **Option A (Environment Variable)**: In Render dashboard → Environment tab, add:
     ```
     PYTHON_VERSION=3.11.9
     ```
   - **Option B (runtime.txt)**: Ensure `backend/runtime.txt` exists with:
     ```
     python-3.11.9
     ```

2. **Update build command** in Render dashboard:
   - Go to your service → **Settings** → **Build & Deploy**
   - Update **Build Command** to:
     ```
     python setup_python_version.py && pip install --upgrade pip && pip install --prefer-binary -r requirements.txt
     ```
   - Click **Save Changes**
   - Click **Manual Deploy** → **Deploy latest commit**

This ensures Python 3.11 is used (with pre-built wheels) and forces pip to prefer binary wheels.

---

**"Service spins down"**
- Normal on free tier after 15 min idle
- First request takes ~30 seconds to wake up
- Consider upgrading to paid ($7/month) for always-on

**"Build fails" (other errors)**
- Check **Logs** tab in Render
- Verify `requirements.txt` is correct
- Check Python version (needs 3.10+)

**"Deployment takes long"**
- First deployment takes ~5 minutes
- Subsequent deployments are faster (~2-3 min)

**"CORS errors"**
- Make sure `CORS_ORIGINS` includes your frontend URL
- Restart service after updating CORS
- Check format: `https://yourusername.github.io` (no trailing slash)

---

## 💡 Pro Tips

1. **Monitor logs** - Check Render dashboard for errors
2. **Keep service awake** - Make requests every 10-15 min (if needed)
3. **Upgrade later** - $7/month for always-on (optional)
4. **Use auto-deploy** - Render handles deployments automatically

---

## 📚 More Information

- **Complete Guide**: See `DEPLOYMENT_FREE_BACKEND.md`
- **Render Docs**: https://render.com/docs
- **FastAPI on Render**: https://render.com/docs/deploy-fastapi

---

**Status:** ✅ Ready to deploy  
**Time:** ~10 minutes  
**Cost:** $0/month (free tier)

**Ready?** Follow the steps above! 🚀
