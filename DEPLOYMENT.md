# BizPulse ERP - Render Deployment Guide

## Quick Deploy to Render

### Prerequisites
1. GitHub account
2. Render account (free tier available)
3. Git installed on your computer

### Step 1: Push to GitHub

1. **Initialize Git repository** (if not already done):
```bash
git init
git add .
git commit -m "Initial commit - BizPulse ERP"
```

2. **Create a new repository on GitHub**:
   - Go to https://github.com/new
   - Name: `bizpulse-erp`
   - Make it Private or Public
   - Don't initialize with README (we already have files)

3. **Push to GitHub**:
```bash
git remote add origin https://github.com/YOUR_USERNAME/bizpulse-erp.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy on Render

#### Option A: Automatic Deploy (Recommended)

1. **Go to Render Dashboard**: https://dashboard.render.com/

2. **Click "New +"** → **"Web Service"**

3. **Connect GitHub Repository**:
   - Click "Connect account" if not connected
   - Select your `bizpulse-erp` repository

4. **Render will auto-detect** the `render.yaml` file and configure everything automatically!

5. **Click "Create Web Service"**

6. **Wait for deployment** (5-10 minutes)

7. **Your app will be live** at: `https://bizpulse-erp-XXXX.onrender.com`

#### Option B: Manual Configuration

If automatic detection doesn't work:

1. **New Web Service** → Connect your repo

2. **Configure**:
   - **Name**: `bizpulse-erp`
   - **Region**: Singapore (or closest to you)
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT app:app --workers 2 --timeout 120`
   - **Plan**: Free

3. **Environment Variables** (optional):
   - `PYTHON_VERSION`: `3.11.0`
   - `PORT`: `5000`

4. **Click "Create Web Service"**

### Step 3: Access Your Deployed App

Once deployed, you'll get a URL like:
```
https://bizpulse-erp-XXXX.onrender.com
```

**Default Login Credentials**:
- Admin: `bizpulse.erp@gmail.com` / `demo123`
- Client: `ali@gmail.com` / `123456`

### Important Notes

1. **Free Tier Limitations**:
   - App sleeps after 15 minutes of inactivity
   - First request after sleep takes 30-60 seconds to wake up
   - 750 hours/month free (enough for 24/7 if only one service)

2. **Database**:
   - SQLite database will reset on each deployment
   - For production, consider upgrading to PostgreSQL
   - Or use Render's persistent disk (paid feature)

3. **Custom Domain** (Optional):
   - Go to Settings → Custom Domain
   - Add your domain and configure DNS

### Troubleshooting

**Build Failed?**
- Check `requirements.txt` has all dependencies
- Check Python version in `runtime.txt`
- View build logs in Render dashboard

**App Not Starting?**
- Check start command in `Procfile`
- View application logs in Render dashboard
- Ensure `app.py` is in root directory

**Database Issues?**
- SQLite works but resets on redeploy
- Consider PostgreSQL for production
- Enable persistent disk in Render settings

### Updating Your App

After making changes:

```bash
git add .
git commit -m "Your update message"
git push origin main
```

Render will automatically redeploy!

### Support

For issues:
- Check Render logs: Dashboard → Your Service → Logs
- Check Render status: https://status.render.com/
- Contact: support@bizpulse.com

---

## Alternative: Deploy to Other Platforms

### Heroku
```bash
heroku create bizpulse-erp
git push heroku main
```

### Railway
1. Go to https://railway.app/
2. New Project → Deploy from GitHub
3. Select your repository
4. Railway auto-detects and deploys

### PythonAnywhere
1. Upload code via Files tab
2. Create new web app
3. Configure WSGI file to point to `app.py`

---

**Deployed Successfully?** 🎉

Your BizPulse ERP is now live and accessible from anywhere!
