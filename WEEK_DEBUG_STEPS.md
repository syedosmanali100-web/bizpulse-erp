# 🔍 Week Filter Debug Steps

## Issue: Both Dates Same (12/07/2025)

**Screenshot shows:**
- From Date: 12/07/2025
- To Date: 12/07/2025

**Expected:**
- From Date: 12/02/2025 (Monday)
- To Date: 12/07/2025 (Saturday - Today)

---

## Debug Steps 🧪

### Step 1: Open Test Page
```bash
# Open this file in browser:
test_week_calculation.html
```

This will show:
- Current date and day
- Week start calculation
- Expected date range

### Step 2: Check Console Logs

1. Open invoice page: `http://localhost:5000/retail/invoices`
2. Open browser console (F12)
3. Click "📅 This Week" button
4. Check console output:

**Expected Logs:**
```
🔍 Week Calculation Debug:
Today: Sat Dec 07 2025
Day of Week: 6 Sat
Days to Monday: 5
Week Start: Mon Dec 02 2025

🔍 Quick Date Filter: week
📅 From: 2025-12-02, To: 2025-12-07
📊 Total invoices: X
✅ Filtered invoices: Y
```

### Step 3: Manual Console Test

Open console and run:
```javascript
// Test the calculation manually
const today = new Date();
console.log('Today:', today.toDateString());
console.log('Day of Week:', today.getDay());

const dayOfWeek = today.getDay();
const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
console.log('Days to Monday:', daysToMonday);

const weekStart = new Date(today);
weekStart.setDate(today.getDate() - daysToMonday);
console.log('Week Start:', weekStart.toDateString());

function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

console.log('From:', formatDateForInput(weekStart));
console.log('To:', formatDateForInput(today));
```

**Expected Output (for Saturday, Dec 7):**
```
Today: Sat Dec 07 2025
Day of Week: 6
Days to Monday: 5
Week Start: Mon Dec 02 2025
From: 2025-12-02
To: 2025-12-07
```

---

## Possible Issues 🔧

### Issue 1: Date Format Display
**Problem:** Date input shows MM/DD/YYYY but value is YYYY-MM-DD

**Check:**
```javascript
// In console
console.log('From Date Value:', document.getElementById('fromDate').value);
console.log('To Date Value:', document.getElementById('toDate').value);
```

**Expected:**
```
From Date Value: 2025-12-02
To Date Value: 2025-12-07
```

**Display:** Browser shows as 12/02/2025 and 12/07/2025 (this is normal!)

---

### Issue 2: Cache Problem
**Solution:**
1. Hard refresh: Ctrl + Shift + R (Windows) or Cmd + Shift + R (Mac)
2. Clear cache and reload
3. Try in incognito/private window

---

### Issue 3: Code Not Updated
**Check:**
```javascript
// In console, check if function exists
console.log(setQuickDate.toString());
```

Look for the new code with `daysToMonday` calculation.

---

## Quick Fix Test 🚀

### Test in Console:
```javascript
// Simulate "This Week" button click
const today = new Date();
const dayOfWeek = today.getDay();
const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
const weekStart = new Date(today);
weekStart.setDate(today.getDate() - daysToMonday);

function formatDateForInput(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

const fromDate = formatDateForInput(weekStart);
const toDate = formatDateForInput(today);

console.log('Setting dates:');
console.log('From:', fromDate);
console.log('To:', toDate);

document.getElementById('fromDate').value = fromDate;
document.getElementById('toDate').value = toDate;

console.log('Verify:');
console.log('From field:', document.getElementById('fromDate').value);
console.log('To field:', document.getElementById('toDate').value);
```

---

## Expected Results for Today (Saturday, Dec 7) 📊

| Field | Value | Display |
|-------|-------|---------|
| From Date | 2025-12-02 | 12/02/2025 |
| To Date | 2025-12-07 | 12/07/2025 |

**Week Range:** Monday (Dec 2) to Saturday (Dec 7) = 6 days

**Invoices:** Should show Dec 2, 3, 4, 5, 6, 7

---

## Verification Checklist ✅

- [ ] Console shows correct "Week Start" date (Dec 2)
- [ ] Console shows correct date range (2025-12-02 to 2025-12-07)
- [ ] From Date field value is 2025-12-02
- [ ] To Date field value is 2025-12-07
- [ ] Table shows invoices from Dec 2-7
- [ ] Stats show count of filtered invoices

---

## If Still Not Working 🔧

### Check 1: File Updated?
```bash
# Check file modification time
# Look for recent changes in retail_invoices.html
```

### Check 2: Server Restarted?
```bash
# Restart Flask server
Ctrl + C
python app.py
```

### Check 3: Browser Cache?
```
1. Open DevTools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"
```

### Check 4: Correct File?
```
Make sure you're editing:
templates/retail_invoices.html

Not:
templates/invoice_demo.html (wrong file!)
```

---

## Debug Output Example 📝

**Good Output (Working):**
```
🔍 Week Calculation Debug:
Today: Sat Dec 07 2025
Day of Week: 6 Sat
Days to Monday: 5
Week Start: Mon Dec 02 2025

🔍 Quick Date Filter: week
📅 From: 2025-12-02, To: 2025-12-07
✅ Filtered invoices: 15
```

**Bad Output (Not Working):**
```
🔍 Quick Date Filter: week
📅 From: 2025-12-07, To: 2025-12-07
✅ Filtered invoices: 3
```

If you see bad output, the code didn't update properly!

---

## Manual Fix Test 🛠️

If automatic button not working, test manually:

1. Open invoice page
2. Manually set dates:
   - From: 12/02/2025 (Monday)
   - To: 12/07/2025 (Today)
3. Check if invoices show correctly

If manual works but button doesn't:
- Code update issue
- Cache issue
- Need hard refresh

---

## Contact Info 📞

**If still not working, provide:**
1. Console logs (full output)
2. Screenshot of date fields
3. Browser name and version
4. Did you hard refresh?

---

**Next Steps:**
1. Open `test_week_calculation.html` in browser
2. Check console logs when clicking "This Week"
3. Report what you see

---

**Status: Debugging Mode** 🔍

Let me know what the console shows!
