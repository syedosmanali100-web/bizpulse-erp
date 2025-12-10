# 📅 Quick Date Filters - User Guide

## ✅ Yesterday Ke Invoices Download Karne Ka Tarika

### **Super Easy Method (NEW!):**

```
Step 1: Invoice page kholo
http://localhost:5000/retail/invoices

Step 2: "📅 Yesterday" button click karo
(Filters section me top pe)

Step 3: Automatically yesterday ki date set ho jayegi

Step 4: Sirf yesterday ke invoices dikhenge

Step 5: "Export" button click karo

Step 6: Format choose karo (CSV/Excel/PDF/JSON)

Step 7: Done! Yesterday ke invoices download! ✅
```

---

## 🎯 Quick Date Filter Buttons

### **5 Quick Buttons Added:**

```
┌─────────────────────────────────────────────────────┐
│  [📅 Today] [📅 Yesterday] [📅 This Week]          │
│  [📅 This Month] [✖️ Clear]                         │
└─────────────────────────────────────────────────────┘
```

### **1. Today Button**
- **Click:** Shows today's invoices only
- **Date Range:** Today → Today
- **Use Case:** Check today's sales

### **2. Yesterday Button** ⭐
- **Click:** Shows yesterday's invoices only
- **Date Range:** Yesterday → Yesterday
- **Use Case:** Download yesterday's report

### **3. This Week Button**
- **Click:** Shows this week's invoices
- **Date Range:** Week start (Sunday) → Today
- **Use Case:** Weekly reports

### **4. This Month Button**
- **Click:** Shows this month's invoices
- **Date Range:** Month start (1st) → Today
- **Use Case:** Monthly reports

### **5. Clear Button**
- **Click:** Removes all filters
- **Shows:** All invoices
- **Use Case:** Reset filters

---

## 📊 Visual Guide

### **Invoice Page Layout:**

```
┌─────────────────────────────────────────────────────┐
│  ← Back to Dashboard                                │
│                                                     │
│  📄 Invoices                                        │
│  [🏠 Dashboard] [Export ▼] [New Invoice]          │
│                                                     │
│  [Stats Cards: Total, Amount, Paid, Pending]      │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ Quick Filters:                                │ │
│  │ [📅 Today] [📅 Yesterday] [📅 Week] [Month]  │ │ ← NEW!
│  │ [✖️ Clear]                                    │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  ┌───────────────────────────────────────────────┐ │
│  │ Status: [All ▼]                               │ │
│  │ From Date: [Auto-filled]                      │ │
│  │ To Date: [Auto-filled]                        │ │
│  │ Search: [          ]                          │ │
│  └───────────────────────────────────────────────┘ │
│                                                     │
│  [Invoice Table with filtered results]            │
└─────────────────────────────────────────────────────┘
```

---

## 🎯 Use Cases

### **Scenario 1: Yesterday Ke Invoices**
```
Problem: Kal ke sab invoices chahiye
Solution: 
1. Click "📅 Yesterday"
2. Click "Export ▼"
3. Choose "Excel"
4. Done! ✅
```

### **Scenario 2: Today Ke Invoices**
```
Problem: Aaj ke invoices check karne hain
Solution:
1. Click "📅 Today"
2. Table me sirf aaj ke invoices
3. Export if needed
```

### **Scenario 3: Weekly Report**
```
Problem: Is hafte ki report chahiye
Solution:
1. Click "📅 This Week"
2. Click "Export ▼"
3. Choose "PDF"
4. Print/Save report
```

### **Scenario 4: Monthly Report**
```
Problem: Is mahine ki report chahiye
Solution:
1. Click "📅 This Month"
2. Click "Export ▼"
3. Choose "Excel"
4. Analysis karo
```

---

## 🔧 Technical Details

### **How It Works:**

#### Yesterday Button:
```javascript
function setQuickDate('yesterday') {
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    
    // Set both dates to yesterday
    fromDate = formatDateForInput(yesterday);
    toDate = formatDateForInput(yesterday);
    
    // Apply filter
    filterInvoices();
}
```

#### Date Format:
```
Input: Date object
Output: "YYYY-MM-DD"
Example: "2024-12-05"
```

---

## 📅 Date Calculations

### **Today:**
```
Date: Current date
Example: 2024-12-06
```

### **Yesterday:**
```
Calculation: Today - 1 day
Example: 2024-12-05
```

### **This Week:**
```
Start: Last Sunday (or today if Sunday)
End: Today
Example: 2024-12-03 to 2024-12-06
```

### **This Month:**
```
Start: 1st of current month
End: Today
Example: 2024-12-01 to 2024-12-06
```

---

## 🎨 Button Styles

### **Design:**
- **Size:** Small (0.5rem padding)
- **Color:** Secondary (light background)
- **Icon:** Calendar emoji (📅)
- **Hover:** Slight color change
- **Layout:** Horizontal row, wraps on mobile

### **CSS:**
```css
.btn btn-secondary {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
    background: var(--secondary);
    color: var(--primary);
}
```

---

## 📊 Filter Combination

### **Quick Date + Other Filters:**

You can combine quick date with other filters:

```
Example 1: Yesterday + Completed
1. Click "📅 Yesterday"
2. Select Status: "Completed"
3. Shows only completed invoices from yesterday

Example 2: This Week + Search
1. Click "📅 This Week"
2. Type customer name in search
3. Shows that customer's invoices from this week

Example 3: This Month + Pending
1. Click "📅 This Month"
2. Select Status: "Pending"
3. Shows pending invoices from this month
```

---

## 🚀 Complete Workflow

### **Yesterday Ke Invoices Download:**

```
┌─────────────────────────────────────────┐
│  1. Open Invoice Page                   │
│     http://localhost:5000/retail/invoices│
│                                         │
│  2. Click "📅 Yesterday" Button         │
│     ↓                                   │
│     Automatically sets:                 │
│     From Date: 2024-12-05              │
│     To Date: 2024-12-05                │
│                                         │
│  3. Table Shows Yesterday's Invoices    │
│     ↓                                   │
│     Only yesterday's data visible       │
│                                         │
│  4. Click "Export ▼" Button            │
│     ↓                                   │
│     Dropdown menu appears               │
│                                         │
│  5. Choose Format                       │
│     - CSV (spreadsheet)                 │
│     - Excel (MS Excel)                  │
│     - PDF (report)                      │
│     - JSON (data)                       │
│                                         │
│  6. File Downloads                      │
│     invoices_2024-12-05.csv            │
│     (Only yesterday's invoices)         │
│                                         │
│  ✅ Done!                               │
└─────────────────────────────────────────┘
```

---

## 💡 Pro Tips

### **Tip 1: Quick Export**
```
Fastest way to export yesterday:
1. Click "📅 Yesterday"
2. Click "Export ▼"
3. Click "Excel"
Done in 3 clicks! ⚡
```

### **Tip 2: Clear Filters**
```
To see all invoices again:
Click "✖️ Clear" button
All filters removed instantly
```

### **Tip 3: Custom Date Range**
```
For specific dates:
1. Don't use quick buttons
2. Manually select From/To dates
3. More flexible control
```

### **Tip 4: Combine Filters**
```
For specific results:
1. Use quick date button
2. Add status filter
3. Add search term
4. Very precise results
```

---

## 📋 Comparison

### **Before (Manual):**
```
1. Click From Date field
2. Select date from calendar
3. Click To Date field
4. Select same date again
5. Wait for filter to apply
Total: 5 steps
```

### **After (Quick Button):**
```
1. Click "📅 Yesterday"
Total: 1 step ⚡
```

**Time Saved:** 80% faster!

---

## ✅ Features Summary

### **Quick Date Buttons:**
- ✅ Today - Current day
- ✅ Yesterday - Previous day ⭐
- ✅ This Week - Week to date
- ✅ This Month - Month to date
- ✅ Clear - Remove all filters

### **Benefits:**
- ✅ One-click filtering
- ✅ No manual date selection
- ✅ Automatic date calculation
- ✅ Works with export
- ✅ Combines with other filters
- ✅ Mobile-friendly
- ✅ Saves time

---

## 🎯 Common Questions

### **Q: Yesterday button kahan hai?**
**A:** Filters section ke top pe, stats cards ke neeche

### **Q: Kya multiple dates select kar sakte hain?**
**A:** Haan, manually From/To dates use karo

### **Q: Export me kya include hoga?**
**A:** Sirf filtered invoices (jo table me dikh rahe hain)

### **Q: Kya filters save hote hain?**
**A:** Nahi, page refresh pe reset ho jate hain

### **Q: Mobile pe kaam karega?**
**A:** Haan, buttons wrap ho jayenge mobile pe

---

## ✅ Summary

**Yesterday ke invoices download karne ke liye:**

1. ✅ Click "📅 Yesterday" button
2. ✅ Click "Export ▼" button
3. ✅ Choose format (CSV/Excel/PDF/JSON)
4. ✅ File downloads automatically

**Super easy! Just 3 clicks! ⚡**

---

**Created:** December 6, 2024  
**Status:** ✅ Complete  
**Buttons Added:** 5 (Today, Yesterday, Week, Month, Clear)  
**Time Saved:** 80% faster than manual
