# 🚀 Deploy Frontend to GitHub Pages - Quick Guide

Complete guide for deploying your frontend to GitHub Pages using GitHub Actions.

## ⚡ Quick Start (5 Steps)

### Step 1: Enable GitHub Pages (1 minute)

1. Go to your GitHub repository
2. Click **Settings** → **Pages**
3. Under **Source**, select: **GitHub Actions**
4. Save

### Step 2: Add GitHub Secret (1 minute)

Go to: **Settings** → **Secrets and variables** → **Actions**

Add this secret:
```
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
```
(Update this after backend is deployed)

### Step 3: Update Workflow (Already Done!)

The workflow `.github/workflows/deploy-frontend-pages.yml` is already configured. ✅

### Step 4: Deploy! (1 minute)

**Option A: Automatic**
- Push to `main` branch → Deployment starts automatically!

**Option B: Manual**
- Go to **Actions** tab → Select **Deploy Frontend to GitHub Pages** → **Run workflow**

### Step 5: Access Your Site

After deployment completes:
- Your site will be available at: `https://yourusername.github.io/your-repo-name`
- Or if using custom domain: Your custom domain

---

## 📋 What Happens During Deployment

```
You push to main
    ↓
GitHub Actions triggers
    ↓
Build Job:
  - Installs Node.js
  - Installs dependencies
  - Builds Next.js app (static export)
  - Creates artifact
    ↓
Deploy Job:
  - Deploys to GitHub Pages
    ↓
✅ Your site is live!
```

---

## 🔧 Configuration Details

### Next.js Config

The `frontend/next.config.js` is configured for static export:

```javascript
output: 'export',           // Enables static export
images: {
  unoptimized: true,        // Required for static export
}
```

### GitHub Pages Settings

- **Source**: GitHub Actions (not branch)
- **Custom domain**: Optional (configure in repository settings)

---

## 🌐 Custom Domain Setup (Optional)

1. Go to **Settings** → **Pages**
2. Enter your custom domain
3. Configure DNS:
   - Add CNAME record pointing to `yourusername.github.io`
   - Or add A records (see GitHub docs)
4. Wait for DNS propagation (up to 48 hours)

---

## 🔄 Workflow Details

### When It Runs

- **Push to main** (when `frontend/**` files change)
- **Manual trigger** (workflow_dispatch)

### What It Does

1. **Builds** Next.js app with static export
2. **Uploads** artifact to GitHub Pages
3. **Deploys** to GitHub Pages

### Build Output

- Static files are generated in `frontend/out/`
- All files are uploaded to GitHub Pages

---

## ✅ Verify Deployment

1. **Check Actions tab** - Workflow should complete successfully
2. **Visit your site** - `https://yourusername.github.io/your-repo-name`
3. **Test the app** - Verify it connects to backend
4. **Check browser console** - No errors

---

## 🐛 Troubleshooting

### "Workflow not running"

**Fix:**
- Make sure GitHub Pages is enabled (Settings → Pages → Source: GitHub Actions)
- Check if workflow file is in `.github/workflows/`
- Verify you're pushing to `main` branch

### "Build fails"

**Check:**
- Next.js config has `output: 'export'`
- All dependencies are in `package.json`
- Check build logs in Actions tab

### "Site not accessible"

**Fix:**
- Wait a few minutes after deployment
- Check GitHub Pages settings (Settings → Pages)
- Verify repository is public (or you have GitHub Pro)
- Clear browser cache

### "API calls fail"

**Fix:**
- Verify `NEXT_PUBLIC_API_URL` is set correctly in GitHub secrets
- Check backend is deployed and accessible
- Verify CORS is configured in backend
- Check browser console for errors

### "404 on refresh"

**Fix:**
This is a known GitHub Pages limitation. Options:

1. **Use HashRouter** (if using React Router):
   ```javascript
   import { HashRouter } from 'react-router-dom';
   ```

2. **Add 404.html** (Next.js handles this automatically with static export)

3. **Use custom domain** with proper server configuration

---

## 📊 GitHub Pages Limitations

### What Works ✅
- Static site generation
- Client-side routing (with HashRouter)
- API calls to external backend
- All React features
- CSS and assets

### What Doesn't Work ❌
- Server-side rendering (SSR)
- API routes (`/api/*`)
- Server components
- Dynamic routes with server-side data fetching
- Image optimization (uses unoptimized images)

**Note:** Your app uses client-side features only, so it's perfect for GitHub Pages! ✅

---

## 🔐 Security

### Environment Variables

- **Public variables**: Use `NEXT_PUBLIC_*` prefix (exposed to browser)
- **Secrets**: Store in GitHub Secrets (not in code)
- **API keys**: Never expose in frontend code

### CORS

Make sure your backend allows requests from:
- `https://yourusername.github.io`
- Your custom domain (if used)

---

## 📈 Performance Tips

1. **Optimize images** - Use optimized formats (WebP, AVIF)
2. **Code splitting** - Next.js does this automatically
3. **Lazy loading** - Use React.lazy() for large components
4. **CDN** - GitHub Pages uses CDN automatically

---

## 🔄 Updating Your Site

### Automatic Updates

Every push to `main` triggers a new deployment.

### Manual Updates

1. Go to **Actions** tab
2. Select **Deploy Frontend to GitHub Pages**
3. Click **Run workflow**
4. Select branch and run

---

## 📚 Additional Resources

- [GitHub Pages Documentation](https://docs.github.com/en/pages)
- [Next.js Static Export](https://nextjs.org/docs/app/building-your-application/deploying/static-exports)
- [GitHub Actions for Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site#publishing-with-a-custom-github-actions-workflow)

---

## ✅ Checklist

Before deployment:
- [ ] GitHub Pages enabled (Settings → Pages → Source: GitHub Actions)
- [ ] `NEXT_PUBLIC_API_URL` secret added
- [ ] Backend deployed and accessible
- [ ] CORS configured in backend

After deployment:
- [ ] Workflow completed successfully
- [ ] Site accessible at GitHub Pages URL
- [ ] App connects to backend
- [ ] No console errors
- [ ] All features working

---

## 🎉 That's It!

Your frontend is now hosted on GitHub Pages! 🚀

**URL Format:**
- `https://yourusername.github.io/your-repo-name`

**Next Steps:**
1. Deploy backend (see Railway deployment guide)
2. Update `NEXT_PUBLIC_API_URL` with backend URL
3. Configure CORS in backend
4. Test full integration

---

**Questions?** Check the troubleshooting section or review the workflow file.
