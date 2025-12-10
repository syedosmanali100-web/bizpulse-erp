# 🧪 Chatbot Draggable - Test Guide

## 🚀 Quick Test Steps

### 1️⃣ Start Server (if not running)
```bash
python app.py
```

### 2️⃣ Open Website
- **Local:** http://localhost:5000/
- **Network:** http://192.168.31.75:5000/

### 3️⃣ Test Fixed Position
1. ✅ Scroll page up and down
2. ✅ Chatbot button should stay in same position
3. ✅ Should NOT scroll with page

**Expected:** Button stays fixed in corner

---

### 4️⃣ Test Draggable

#### On Mobile:
1. ✅ **Press and hold** chatbot button for 0.5 seconds
2. ✅ Button should **scale up** and shadow should increase
3. ✅ **Drag** button to different position
4. ✅ **Release** finger
5. ✅ Button should stay in new position
6. ✅ **Refresh page** - position should be saved

**Expected:** Can move button anywhere on screen

#### On Desktop:
1. ✅ **Click and hold** chatbot button for 0.5 seconds
2. ✅ Button should **scale up** and cursor changes to "grabbing"
3. ✅ **Drag** button to different position
4. ✅ **Release** mouse
5. ✅ Button should stay in new position
6. ✅ **Refresh page** - position should be saved

**Expected:** Can move button anywhere on screen

---

### 5️⃣ Test Hide Button

#### On Desktop:
1. ✅ **Hover** mouse over chatbot button
2. ✅ **Red × button** should appear in top-right corner
3. ✅ **Click** the × button
4. ✅ Chatbot should disappear
5. ✅ Notification should show: "Chatbot hidden. Refresh page to show again."
6. ✅ **Refresh page** - chatbot should appear again

**Expected:** Can hide and show chatbot

#### On Mobile:
1. ✅ **Long press** chatbot button
2. ✅ **Red × button** might appear (depends on device)
3. ✅ **Tap** the × button if visible
4. ✅ Chatbot should disappear

**Note:** Hide button works better on desktop due to hover

---

### 6️⃣ Test Chat Functionality
1. ✅ **Quick tap/click** chatbot button (< 0.5 seconds)
2. ✅ Chat window should slide up
3. ✅ Type a message or use quick replies
4. ✅ Bot should respond
5. ✅ **Click × in header** to close chat

**Expected:** Chat opens and works normally

---

## 🎯 Visual Indicators

### Normal State:
- 🟣 Purple/maroon button
- 🟢 Green badge pulsing
- ✨ Smooth pulse animation

### Dragging State:
- 🔵 Button 15% larger
- 🌟 Darker shadow
- 🚫 No pulse animation
- 👆 Cursor: grabbing (desktop)

### Hidden State:
- 👻 Button completely invisible
- 📢 Notification appears

---

## 🐛 Troubleshooting

### Problem: Can't drag button
**Solution:**
- Make sure to **hold for 0.5 seconds** before dragging
- Quick taps will open chat instead
- Try on different browser

### Problem: Position not saving
**Solution:**
1. Open browser console (F12)
2. Check for errors
3. Clear localStorage: `localStorage.clear()`
4. Try again

### Problem: Hide button not showing
**Solution:**
- Make sure to **hover** (desktop only)
- Mobile: Try long press
- Check if CSS is loaded

### Problem: Chatbot disappeared
**Solution:**
1. Open console (F12)
2. Type: `localStorage.removeItem('chatbotHidden')`
3. Refresh page

### Problem: Button went off screen
**Solution:**
1. Open console (F12)
2. Type: `localStorage.removeItem('chatbotPosition')`
3. Refresh page

---

## ✅ Success Criteria

All these should work:
- [x] Button stays fixed when scrolling
- [x] Long press enables drag mode
- [x] Can drag to any position
- [x] Position saves after drag
- [x] Position persists after refresh
- [x] Quick tap opens chat
- [x] Hide button appears on hover
- [x] Can hide chatbot
- [x] Refresh shows chatbot again
- [x] Works on mobile
- [x] Works on desktop

---

## 📱 Device Testing

### Test on:
- [ ] Desktop Chrome
- [ ] Desktop Firefox
- [ ] Desktop Edge
- [ ] Mobile Chrome (Android)
- [ ] Mobile Safari (iOS)
- [ ] Tablet

---

## 🎉 If Everything Works:

**Congratulations!** 🎊

Your chatbot now has:
- ✅ Fixed position (no scrolling)
- ✅ Draggable (move anywhere)
- ✅ Hide functionality
- ✅ Position persistence
- ✅ Smooth animations
- ✅ Mobile & desktop support

**Enjoy your enhanced chatbot!** 🚀

---

## 📞 Need Help?

If something doesn't work:
1. Check browser console for errors (F12)
2. Clear browser cache (Ctrl + Shift + R)
3. Clear localStorage: `localStorage.clear()`
4. Restart server
5. Try different browser

**Still having issues?** Let me know! 😊
