# Deployment Guide

Complete guide for deploying the Voice-First Travel Assistant.

## Table of Contents

1. [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
2. [Backend Deployment (Railway/Render)](#backend-deployment-railwayrender)
3. [Environment Variables](#environment-variables)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Troubleshooting](#troubleshooting)

---

## Frontend Deployment (Vercel)

### Prerequisites

- Vercel account (free tier available)
- GitHub repository with frontend code
- Backend API URL (deployed backend)

### Step 1: Prepare Frontend

1. **Ensure build works locally:**
   ```bash
   cd frontend
   npm install
   npm run build
   ```

2. **Check `next.config.js`:**
   - Verify `NEXT_PUBLIC_API_URL` is set correctly
   - Ensure no hardcoded localhost URLs

### Step 2: Deploy to Vercel

**Option A: Via Vercel CLI**

1. **Install Vercel CLI:**
   ```bash
   npm i -g vercel
   ```

2. **Login:**
   ```bash
   vercel login
   ```

3. **Deploy:**
   ```bash
   cd frontend
   vercel
   ```

4. **Follow prompts:**
   - Link to existing project or create new
   - Set environment variables (see below)
   - Confirm deployment

**Option B: Via Vercel Dashboard**

1. **Go to [vercel.com](https://vercel.com)**
2. **Click "New Project"**
3. **Import your GitHub repository**
4. **Configure:**
   - Framework Preset: **Next.js**
   - Root Directory: `frontend`
   - Build Command: `npm run build`
   - Output Directory: `.next`
5. **Add Environment Variables** (see below)
6. **Click "Deploy"**

### Step 3: Environment Variables

Add these in Vercel Dashboard → Project → Settings → Environment Variables:

```
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

**For Production:**
- Set environment variables for **Production** environment
- Optionally set for **Preview** and **Development** if needed

### Step 4: Custom Domain (Optional)

1. Go to Project → Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions
4. Wait for DNS propagation (can take up to 48 hours)

### Step 5: Verify Deployment

1. Visit your Vercel deployment URL
2. Test voice input
3. Test API connection
4. Check browser console for errors

---

## Backend Deployment (Railway/Render)

### Option A: Railway

#### Prerequisites

- Railway account (free tier available)
- GitHub repository with backend code

#### Step 1: Deploy to Railway

1. **Go to [railway.app](https://railway.app)**
2. **Click "New Project"**
3. **Select "Deploy from GitHub repo"**
4. **Choose your repository**
5. **Railway will auto-detect:**
   - Framework: Python/FastAPI
   - Build command: Auto-detected
   - Start command: Auto-detected

#### Step 2: Configure Environment Variables

Go to Project → Variables and add:

```env
GROK_API_KEY=your_grok_api_key
GROK_API_URL=https://api.x.ai/v1
GROK_VOICE_API_KEY=your_grok_voice_api_key
GROK_VOICE_API_URL=https://api.x.ai/v1/audio
CHROMA_PERSIST_DIR=/app/chroma_db
OVERPASS_API_URL=https://overpass-api.de/api/interpreter
N8N_WEBHOOK_URL=https://your-n8n-instance.com/webhook/...
APP_NAME=Voice-First Travel Assistant
DEBUG=false
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=https://your-frontend-url.vercel.app
```

#### Step 3: Configure Build Settings

1. Go to Project → Settings
2. Set **Build Command:**
   ```bash
   cd backend && pip install -r requirements.txt
   ```
3. Set **Start Command:**
   ```bash
   cd backend && python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT
   ```

#### Step 4: Add Health Check

Railway automatically uses `/health` endpoint for health checks.

#### Step 5: Get Public URL

1. Go to Project → Settings → Networking
2. Generate public domain
3. Copy the URL (e.g., `https://your-app.railway.app`)

---

### Option B: Render

#### Prerequisites

- Render account (free tier available)
- GitHub repository with backend code

#### Step 1: Deploy to Render

1. **Go to [render.com](https://render.com)**
2. **Click "New +" → "Web Service"**
3. **Connect your GitHub repository**
4. **Configure:**
   - **Name:** `travel-assistant-backend`
   - **Environment:** `Python 3` (will use `runtime.txt` or `PYTHON_VERSION` env var)
   - **Build Command:** `cd backend && python setup_python_version.py && pip install --upgrade pip && pip install --prefer-binary -r requirements.txt`
   - **Start Command:** `cd backend && python -m uvicorn src.main:app --host 0.0.0.0 --port $PORT`
   - **Plan:** Free (or paid for better performance)

**Note:** 
- The `runtime.txt` file in the `backend` folder pins Python to 3.11.9 by default
- You can override by setting `PYTHON_VERSION` environment variable (e.g., `3.11.9` or `3.12.0`)
- Python 3.11.9 has better pre-built wheel support and avoids Rust compilation issues

#### Step 2: Environment Variables

Go to Environment tab and add all variables (same as Railway above).

#### Step 3: Health Check

1. Go to Settings → Health Check Path
2. Set to: `/health`
3. Save

#### Step 4: Get Public URL

Render provides a URL like: `https://your-app.onrender.com`

---

## Environment Variables

### Backend Required Variables

```env
# Groq API (OpenAI-compatible)
GROQ_API_KEY=required
GROQ_API_URL=https://api.groq.com/openai/v1
GROQ_MODEL=llama3-70b-8192

# Database (Optional)
DATABASE_URL=optional

# ChromaDB
CHROMA_PERSIST_DIR=./chroma_db

# External APIs
OVERPASS_API_URL=https://overpass-api.de/api/interpreter
OPEN_METEO_API_URL=https://api.open-meteo.com/v1

# n8n
N8N_WEBHOOK_URL=optional

# Application
APP_NAME=Voice-First Travel Assistant
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000

# CORS (Important!)
CORS_ORIGINS=https://your-frontend-url.vercel.app
```

### Frontend Required Variables

```env
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

---

## Post-Deployment Verification

### 1. Health Check

```bash
curl https://your-backend-url.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "Voice-First Travel Assistant",
  "version": "1.0.0"
}
```

### 2. API Endpoints

Test all endpoints:

```bash
# Root
curl https://your-backend-url.com/

# Chat
curl -X POST https://your-backend-url.com/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Plan a trip to Jaipur"}'

# Health
curl https://your-backend-url.com/health
```

### 3. Frontend Connection

1. Open frontend URL
2. Check browser console (F12)
3. Verify no CORS errors
4. Test voice input
5. Test API calls

### 4. CORS Configuration

If you see CORS errors:

1. **Check backend CORS settings:**
   - Verify `CORS_ORIGINS` includes your frontend URL
   - No trailing slashes
   - Include `https://` protocol

2. **Common CORS issues:**
   - Frontend URL not in `CORS_ORIGINS`
   - Backend not allowing credentials
   - Preflight requests failing

---

## Troubleshooting

### Backend Issues

**Problem: Build fails**
- Check Python version (3.9+)
- Verify `requirements.txt` is correct
- Check build logs for specific errors
- **If Rust/maturin error**: Ensure `backend/runtime.txt` exists with `python-3.11.9` to use Python 3.11 (better wheel support than 3.13)

**Problem: App crashes on startup**
- Check environment variables are set
- Verify `GROQ_API_KEY` is valid
- Check logs for error messages

**Problem: Health check fails**
- Verify `/health` endpoint exists
- Check server is listening on correct port
- Verify no firewall blocking requests

**Problem: CORS errors**
- Update `CORS_ORIGINS` with frontend URL
- Restart backend after changing CORS settings
- Check browser console for specific CORS error

### Frontend Issues

**Problem: Build fails**
- Check Node.js version (18+)
- Run `npm install` locally first
- Check for TypeScript errors

**Problem: API calls fail**
- Verify `NEXT_PUBLIC_API_URL` is set
- Check backend is accessible
- Verify CORS is configured

**Problem: Voice input not working**
- Check browser compatibility (Chrome/Edge/Safari)
- Verify microphone permissions
- Check browser console for errors

### Database Issues

**Problem: ChromaDB not persisting**
- Verify `CHROMA_PERSIST_DIR` is writable
- Check disk space on server
- Verify path is absolute or relative to app root

---

## Production Checklist

- [ ] All environment variables set
- [ ] CORS configured correctly
- [ ] Health check endpoint working
- [ ] Frontend connects to backend
- [ ] Voice input works
- [ ] API endpoints accessible
- [ ] Error handling works
- [ ] Logging configured
- [ ] Monitoring set up (optional)
- [ ] Custom domain configured (optional)
- [ ] SSL/HTTPS enabled
- [ ] Rate limiting configured
- [ ] Backup strategy (if using database)

---

## Monitoring

### Recommended Tools

1. **Vercel Analytics** (Frontend)
   - Built-in analytics
   - Performance monitoring

2. **Railway/Render Logs** (Backend)
   - Real-time logs
   - Error tracking

3. **Sentry** (Optional)
   - Error tracking
   - Performance monitoring

4. **Uptime Monitoring** (Optional)
   - UptimeRobot
   - Pingdom

---

## Scaling Considerations

### Backend

- Use paid Railway/Render plan for better performance
- Consider load balancing for high traffic
- Use Redis for session storage (instead of in-memory)
- Consider database for production (PostgreSQL)

### Frontend

- Vercel automatically scales
- Consider CDN for static assets
- Optimize images and assets

---

## Security Best Practices

1. **Never commit API keys** to repository
2. **Use environment variables** for all secrets
3. **Enable HTTPS** (automatic on Vercel/Railway/Render)
4. **Set up rate limiting** (already implemented)
5. **Validate all inputs** (already implemented)
6. **Use CORS** to restrict origins
7. **Regular dependency updates**

---

## Support

For issues:
1. Check logs (backend and frontend)
2. Verify environment variables
3. Test endpoints individually
4. Check browser console
5. Review this guide

**Deployment Status: Ready for Production!** 🚀
