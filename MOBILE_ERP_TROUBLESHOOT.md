# 🔧 Mobile ERP Not Loading - Troubleshooting Guide

## 🔍 Quick Checks

### 1️⃣ Check Server Status
```bash
# Is server running?
# Look for: "Running on http://192.168.31.75:5000"
```

### 2️⃣ Check Mobile Routes
Available routes:
- `http://localhost:5000/mobile`
- `http://localhost:5000/mobile-simple`
- `http://192.168.31.75:5000/mobile`
- `http://192.168.31.75:5000/mobile-simple`

### 3️⃣ Check Browser Console
1. Open mobile URL
2. Press F12 (Developer Tools)
3. Check Console tab for errors
4. Check Network tab for failed requests

---

## 🐛 Common Issues & Solutions

### Issue 1: Server Not Running
**Symptoms:**
- "This site can't be reached"
- "Connection refused"
- "ERR_CONNECTION_REFUSED"

**Solution:**
```bash
# Start server
python app.py

# Check if running
# Should see: "Running on http://192.168.31.75:5000"
```

---

### Issue 2: Wrong URL
**Symptoms:**
- 404 Not Found
- Page not found

**Solution:**
Use correct URL:
```
✅ http://localhost:5000/mobile
✅ http://localhost:5000/mobile-simple
✅ http://192.168.31.75:5000/mobile
✅ http://192.168.31.75:5000/mobile-simple

❌ http://localhost:5000/mobile-erp (wrong)
❌ http://localhost:5000/mobile-app (wrong)
```

---

### Issue 3: Template Error
**Symptoms:**
- "TemplateNotFound"
- "Internal Server Error"
- Blank page

**Solution:**
```bash
# Check if template exists
dir templates\mobile_simple_working.html

# If missing, restore from backup
copy templates\mobile_simple_working.html.bak templates\mobile_simple_working.html
```

---

### Issue 4: JavaScript Error
**Symptoms:**
- Page loads but doesn't work
- Buttons don't respond
- Modules don't show

**Solution:**
1. Open browser console (F12)
2. Look for JavaScript errors
3. Hard refresh (Ctrl + Shift + R)
4. Clear browser cache

---

### Issue 5: Network/Firewall
**Symptoms:**
- Works on localhost but not on IP
- Mobile can't access
- Timeout errors

**Solution:**
```bash
# Check firewall
# Allow port 5000

# Check if server is listening on all interfaces
# Should see: "Running on all addresses (0.0.0.0)"
```

---

## 🧪 Testing Steps

### Step 1: Test Server
```bash
# Start server
python app.py

# Should see:
# [SERVER] Running on http://localhost:5000
# [MOBILE] Mobile PWA available at: http://localhost:5000/mobile
# * Running on http://192.168.31.75:5000
```

### Step 2: Test on Desktop Browser
```
1. Open: http://localhost:5000/mobile
2. Should load mobile ERP
3. Check if login screen appears
```

### Step 3: Test on Mobile
```
1. Connect mobile to same WiFi
2. Open: http://192.168.31.75:5000/mobile
3. Should load mobile ERP
```

### Step 4: Check Console
```
1. Press F12
2. Go to Console tab
3. Look for errors (red text)
4. Share error messages
```

---

## 📱 Mobile Access Guide

### On Same WiFi:

**Desktop:**
```
http://localhost:5000/mobile
http://127.0.0.1:5000/mobile
```

**Mobile/Tablet:**
```
http://192.168.31.75:5000/mobile
(Use your computer's IP address)
```

### Find Your IP:

**Windows:**
```bash
ipconfig
# Look for: IPv4 Address
```

**Mac/Linux:**
```bash
ifconfig
# Look for: inet
```

---

## 🔧 Quick Fixes

### Fix 1: Restart Server
```bash
# Stop server (Ctrl + C)
# Start again
python app.py
```

### Fix 2: Hard Refresh Browser
```
Windows: Ctrl + Shift + R
Mac: Cmd + Shift + R
```

### Fix 3: Clear Browser Cache
```
1. Open browser settings
2. Clear browsing data
3. Select "Cached images and files"
4. Clear data
5. Refresh page
```

### Fix 4: Try Different Browser
```
✅ Chrome
✅ Firefox
✅ Edge
✅ Safari
```

### Fix 5: Check Template File
```bash
# Verify file exists
dir templates\mobile_simple_working.html

# Check file size (should be > 100KB)
```

---

## 📊 Diagnostic Commands

### Check Server:
```bash
# Is Python running?
tasklist | findstr python

# Is port 5000 in use?
netstat -ano | findstr :5000
```

### Check Template:
```bash
# List mobile templates
dir templates\mobile*.html

# Check file size
dir templates\mobile_simple_working.html
```

### Test Route:
```bash
# Test with curl (if installed)
curl http://localhost:5000/mobile

# Or use browser
# Open: http://localhost:5000/mobile
```

---

## 🚨 Error Messages & Solutions

### "TemplateNotFound: mobile_simple_working.html"
**Solution:**
```bash
# File is missing
# Check if file exists
dir templates\mobile_simple_working.html

# If missing, file was deleted
# Need to restore from backup
```

### "Internal Server Error"
**Solution:**
```bash
# Check server console for error details
# Look for Python traceback
# Share error message for help
```

### "This site can't be reached"
**Solution:**
```bash
# Server not running
# Start server: python app.py
```

### "404 Not Found"
**Solution:**
```bash
# Wrong URL
# Use: /mobile or /mobile-simple
# Not: /mobile-erp or /mobile-app
```

---

## 💡 What to Share for Help

If still not working, share:

1. **Error Message:**
   - Exact error text
   - Screenshot if possible

2. **Server Console:**
   - Last 10-20 lines
   - Any error messages

3. **Browser Console:**
   - Press F12
   - Console tab
   - Any red errors

4. **URL Used:**
   - Exact URL you're trying

5. **What You See:**
   - Blank page?
   - Error page?
   - Loading forever?

---

## 🎯 Quick Test

Run this to test:

```bash
# 1. Start server
python app.py

# 2. Open browser
# Go to: http://localhost:5000/mobile

# 3. Should see:
# - Login screen
# - Email: bizpulse.erp@gmail.com
# - Password: demo123

# 4. Login and test
```

---

## ✅ Success Checklist

- [ ] Server is running
- [ ] No errors in server console
- [ ] URL is correct (/mobile or /mobile-simple)
- [ ] Browser console has no errors
- [ ] Template file exists
- [ ] Can access on desktop browser
- [ ] Can access on mobile (same WiFi)

---

## 📞 Need More Help?

Share:
1. Error message (exact text)
2. Server console output
3. Browser console errors
4. URL you're using
5. What you see on screen

**Batao kya error aa raha hai, main fix kar dunga!** 🚀
