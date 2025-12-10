# 🚀 ngrok Setup Guide - Access Your ERP from Anywhere!

## ✅ ngrok is Already Downloaded!

## Quick Start (3 Steps):

### Step 1: Sign up for ngrok (Free)
1. Go to: https://dashboard.ngrok.com/signup
2. Sign up with email (takes 30 seconds)
3. Copy your authtoken from: https://dashboard.ngrok.com/get-started/your-authtoken

### Step 2: Authenticate ngrok
Open Command Prompt in this folder and run:
```bash
ngrok config add-authtoken YOUR_TOKEN_HERE
```
Replace `YOUR_TOKEN_HERE` with your actual token from ngrok dashboard.

### Step 3: Start Everything!
Just double-click: **start_with_ngrok.bat**

This will:
- Start your Flask server
- Start ngrok tunnel
- Give you a public URL like: `https://abc123.ngrok.io`

## 📱 Access from Mobile:

Once ngrok starts, you'll see something like:
```
Forwarding    https://1234-abc-def.ngrok.io -> http://localhost:5000
```

Use this URL on your mobile:
- **Mobile App**: `https://1234-abc-def.ngrok.io/mobile-pwa`
- **Desktop**: `https://1234-abc-def.ngrok.io/`

## 🎯 URLs to Access:

- `/mobile-pwa` - Mobile Progressive Web App (Best for mobile)
- `/retail/dashboard` - Retail Dashboard
- `/retail/products` - Products Management
- `/retail/billing` - Billing System
- `/retail/customers` - Customer Management

## ⚠️ Important Notes:

1. **Free tier limits**: 
   - URL changes every time you restart ngrok
   - 40 connections/minute limit
   - Session expires after 2 hours (just restart)

2. **Keep both windows open**:
   - Flask server window
   - ngrok tunnel window

3. **To stop**: Close both command windows

## 🔧 Manual Method (if batch file doesn't work):

**Terminal 1** - Start Flask:
```bash
python app.py
```

**Terminal 2** - Start ngrok:
```bash
ngrok http 5000
```

## 🆘 Troubleshooting:

**Issue**: "ngrok not found"
**Fix**: Make sure you're in the project folder

**Issue**: "authentication required"
**Fix**: Run the authtoken command from Step 2

**Issue**: "port already in use"
**Fix**: Close any other Flask servers running

## 🌟 Pro Tips:

1. **Save the ngrok URL** - Share it with team members
2. **Test on mobile** - Open in Chrome/Safari on your phone
3. **Install as PWA** - Click "Add to Home Screen" on mobile
4. **Bookmark it** - Save the URL for quick access

## 📞 Need Help?

If you face any issues:
1. Make sure Flask server is running (check Terminal 1)
2. Make sure ngrok is authenticated
3. Check if port 5000 is free
4. Try restarting both services

---

**Ready to go?** 
1. Get your authtoken from ngrok.com
2. Run: `ngrok config add-authtoken YOUR_TOKEN`
3. Double-click: `start_with_ngrok.bat`
4. Copy the https URL and use it on your mobile!
