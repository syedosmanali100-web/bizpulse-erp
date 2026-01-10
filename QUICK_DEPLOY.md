# 🚀 Quick Deploy to Render - 3 Simple Steps

## Step 1: Push to GitHub (5 minutes)

### Option A: Using the Script (Easiest)
Just double-click `deploy.bat` and follow the prompts!

### Option B: Manual Commands
```bash
# Add all files
git add .

# Commit
git commit -m "Deploy BizPulse ERP"

# Add your GitHub repo (create one first at github.com/new)
git remote add origin https://github.com/YOUR_USERNAME/bizpulse-erp.git

# Push
git branch -M main
git push -u origin main
```

## Step 2: Deploy on Render (2 minutes)

1. Go to: https://dashboard.render.com/
2. Click **"New +"** → **"Web Service"**
3. Click **"Connect GitHub"** and select your repository
4. Render will **automatically detect** `render.yaml` and configure everything!
5. Click **"Create Web Service"**

That's it! ✅

## Step 3: Wait & Access (5-10 minutes)

Render will:
- ✅ Install dependencies
- ✅ Build your app
- ✅ Deploy it live

You'll get a URL like: `https://bizpulse-erp-XXXX.onrender.com`

---

## 📱 Access Your Live App

**Desktop Dashboard:**
```
https://your-app.onrender.com/retail/dashboard
```

**Mobile ERP:**
```
https://your-app.onrender.com/mobile
```

**Client Management:**
```
https://your-app.onrender.com/client-management
```

---

## 🔐 Default Login Credentials

**Admin Account:**
- Email: `bizpulse.erp@gmail.com`
- Password: `demo123`

**Client Accounts:**
- Ali: `ali@gmail.com` / `123456`
- ABC Electronics: `abc_electronic` / `admin123`

---

## 🔄 Update Your Deployed App

After making changes:

```bash
git add .
git commit -m "Your update message"
git push origin main
```

Render will **automatically redeploy**! 🎉

---

## ⚠️ Important Notes

1. **Free Tier**: App sleeps after 15 min of inactivity (first request takes 30-60 sec to wake)
2. **Database**: SQLite resets on each deploy (use PostgreSQL for production)
3. **Custom Domain**: Available in Render settings

---

## 🆘 Need Help?

**Build Failed?**
- Check logs in Render dashboard
- Verify `requirements.txt` is correct
- Check Python version in `runtime.txt`

**App Not Loading?**
- Wait 5-10 minutes for first deploy
- Check application logs in Render
- Try accessing `/` first to wake up the app

---

## 🎉 That's It!

Your BizPulse ERP is now:
- ✅ Live on the internet
- ✅ Accessible from any device
- ✅ Auto-deploys on every push
- ✅ Free to use (with Render free tier)

**Enjoy your deployed app!** 🚀
