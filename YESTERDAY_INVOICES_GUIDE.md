# Yesterday ke Invoices Download Kaise Karein? 📅

## Quick Steps (Bahut Easy!)

### Method 1: Quick Date Filter Button (Sabse Fast!)
1. **Invoice Module** kholo (`/retail/invoices`)
2. Upar **"📅 Yesterday"** button pe click karo
3. Automatically yesterday ki date set ho jayegi
4. Ab **"Export"** button pe click karo
5. Format choose karo:
   - **CSV** - Excel me open hoga
   - **Excel** - Direct Excel file
   - **PDF** - Print ke liye
   - **JSON** - Data backup ke liye

### Method 2: Manual Date Selection
1. **Invoice Module** kholo
2. **From Date** aur **To Date** dono me yesterday ki date select karo
3. **Export** button pe click karo
4. Format choose karo

---

## Quick Date Filter Buttons 🎯

Invoice page pe 5 quick buttons hain:

1. **📅 Today** - Aaj ke invoices
2. **📅 Yesterday** - Kal ke invoices ⭐
3. **📅 This Week** - Is hafte ke invoices
4. **📅 This Month** - Is mahine ke invoices
5. **✖️ Clear** - Sab filters clear karo

---

## Export Formats 📊

### CSV Format
- Excel me easily open hota hai
- Data analysis ke liye best
- Comma-separated values

### Excel Format (.xls)
- Direct Excel file
- UTF-8 encoding with BOM
- Hindi text bhi sahi se dikhega

### PDF Format
- Print-ready document
- Professional look
- Sharing ke liye best

### JSON Format
- Complete data structure
- Backup ke liye
- Technical use ke liye

---

## Example Workflow 🔄

**Yesterday ke invoices download karne ke liye:**

```
1. Invoice Module Open Karo
   ↓
2. "📅 Yesterday" Button Click Karo
   ↓
3. Automatically Yesterday ki Date Set Ho Jayegi
   ↓
4. "Export" Dropdown Click Karo
   ↓
5. "Export as Excel" Select Karo
   ↓
6. File Download Ho Jayegi: invoices_2025-12-05.xls
```

---

## Features ✨

### Automatic Date Setting
- Yesterday button click karte hi automatically date set ho jati hai
- From Date aur To Date dono same (yesterday) set hote hain
- Manual typing ki zarurat nahi

### Smart Filtering
- Sirf filtered invoices export hote hain
- Status filter bhi apply hota hai
- Search filter bhi work karta hai

### Smart Filename
- Automatic date-based filename
- Format: `invoices_YYYY-MM-DD.ext`
- Example: `invoices_2025-12-05.csv`

---

## Tips & Tricks 💡

1. **Multiple Filters Combine Kar Sakte Ho:**
   - Yesterday button + Status filter
   - Yesterday button + Customer search
   - Sab filters ek saath work karte hain

2. **Export Before Clearing:**
   - Pehle export karo
   - Phir "Clear" button se filters clear karo

3. **Quick Access:**
   - Yesterday button sabse fast hai
   - Manual date selection se better

4. **Verify Before Export:**
   - Table me filtered results dekh lo
   - Count check kar lo
   - Phir export karo

---

## Troubleshooting 🔧

### Problem: Yesterday ke invoices nahi dikh rahe
**Solution:** 
- Check karo ki yesterday actually koi invoice tha ya nahi
- Database me data hai ya nahi verify karo

### Problem: Export button kaam nahi kar raha
**Solution:**
- Browser console check karo (F12)
- Page refresh karo
- Phir se try karo

### Problem: Downloaded file empty hai
**Solution:**
- Filters check karo
- Yesterday ke invoices exist karte hain ya nahi
- Status filter "All Status" pe set karo

---

## Technical Details 🔧

### Date Calculation Logic
```javascript
const yesterday = new Date(today);
yesterday.setDate(yesterday.getDate() - 1);
fromDate = toDate = formatDateForInput(yesterday);
```

### Date Format
- Input format: `YYYY-MM-DD`
- Display format: `DD MMM YYYY`
- Example: `2025-12-05` → `05 Dec 2025`

---

## Summary 📝

**Sabse Easy Tarika:**
1. Invoice module kholo
2. "📅 Yesterday" button click karo
3. "Export" → "Export as Excel" select karo
4. Done! File download ho jayegi

**Time Required:** 5 seconds ⚡

**Difficulty Level:** Bahut Easy! 😊

---

## Next Steps 🚀

Agar aur koi specific date range chahiye:
- Manual date selection use karo
- Ya custom quick filter button add kar sakte hain
- Last 7 days, Last 30 days, etc.

---

**Happy Exporting! 🎉**
