# 📁 BizPulse ERP - File Organization Guide

## 🎯 Naming Convention

### Web Version (Desktop)
- **Prefix:** `web_`
- **Purpose:** Main website pages for desktop users
- **Examples:** 
  - `web_landing_page.html` (Homepage)
  - `web_login_page.html` (Login)
  - `web_register_page.html` (Registration)

### Mobile Version
- **Prefix:** `mobile_`
- **Purpose:** Mobile-optimized PWA pages
- **Examples:**
  - `mobile_web_app.html` (Main mobile app)
  - `mobile_test.html` (Testing page)

### Retail Module (Web)
- **Prefix:** `retail_`
- **Purpose:** Retail business management pages
- **Examples:**
  - `retail_dashboard.html` (Main dashboard)
  - `retail_billing.html` (Billing/POS)
  - `retail_invoices.html` (Invoice list)
  - `retail_invoice_detail.html` (Single invoice view)
  - `retail_products.html` (Product management)
  - `retail_customers.html` (Customer management)
  - `retail_sales.html` (Sales reports)
  - `retail_profile.html` (Business profile)

### Hotel Module (Web)
- **Prefix:** `hotel_`
- **Purpose:** Hotel business management pages
- **Examples:**
  - `hotel_dashboard.html` (Hotel dashboard)
  - `hotel_profile.html` (Hotel profile)

---

## 📂 Current File Structure

### `/templates` Directory

#### Web Pages (Public)
```
web_landing_page.html       → Homepage (/)
web_login_page.html         → Login page (/login)
web_register_page.html      → Registration (/register)
contact.html                → Contact page (/contact)
```

#### Retail Module Pages
```
retail_dashboard.html       → Retail dashboard (/retail/dashboard)
retail_billing.html         → Billing & POS (/retail/billing)
retail_invoices.html        → Invoice list (/retail/invoices) ✅ NEW
retail_invoice_detail.html  → Invoice details (/retail/invoice/<id>) ✅ NEW
retail_products.html        → Product management (/retail/products)
retail_customers.html       → Customer management (/retail/customers)
retail_sales.html           → Sales reports (/retail/sales)
retail_profile.html         → Business profile (/retail/profile)
```

#### Hotel Module Pages
```
hotel_dashboard.html        → Hotel dashboard (/hotel/dashboard)
hotel_profile.html          → Hotel profile (/hotel/profile)
```

#### Mobile App Pages
```
mobile_web_app.html         → Main mobile PWA (/mobile)
mobile_test.html            → Mobile testing (/mobile-test)
mobile_diagnostic.html      → Diagnostics (/mobile-diagnostic)
```

#### Management Pages
```
sales_management.html       → Sales management (/sales-management)
low_stock_management.html   → Low stock alerts (/inventory/low-stock)
```

#### Legacy/Backup Files
```
index.html                  → Old homepage (keep for compatibility)
login.html                  → Old login (keep for compatibility)
register.html               → Old register (keep for compatibility)
index_old_backup.html       → Backup
low_stock_management_backup.html → Backup
mobile_app.html             → Old mobile
mobile_clean.html           → Old mobile
```

---

## 🗺️ Route Mapping

### Public Routes
| Route | File | Description |
|-------|------|-------------|
| `/` | `web_landing_page.html` or `index.html` | Homepage |
| `/login` | `web_login_page.html` or `login.html` | Login |
| `/register` | `web_register_page.html` or `register.html` | Register |
| `/contact` | `contact.html` | Contact |

### Retail Routes
| Route | File | Description |
|-------|------|-------------|
| `/retail/dashboard` | `retail_dashboard.html` | Main dashboard |
| `/retail/billing` | `retail_billing.html` | Billing & POS |
| `/retail/invoices` | `retail_invoices.html` | Invoice list ✅ |
| `/retail/invoice/<id>` | `retail_invoice_detail.html` | Invoice detail ✅ |
| `/retail/products` | `retail_products.html` | Products |
| `/retail/customers` | `retail_customers.html` | Customers |
| `/retail/sales` | `retail_sales.html` | Sales reports |
| `/retail/profile` | `retail_profile.html` | Profile |

### Hotel Routes
| Route | File | Description |
|-------|------|-------------|
| `/hotel/dashboard` | `hotel_dashboard.html` | Hotel dashboard |
| `/hotel/profile` | `hotel_profile.html` | Hotel profile |

### Mobile Routes
| Route | File | Description |
|-------|------|-------------|
| `/mobile` | `mobile_web_app.html` | Mobile PWA |
| `/mobile-test` | `mobile_test.html` | Testing |
| `/mobile-diagnostic` | `mobile_diagnostic.html` | Diagnostics |

### Management Routes
| Route | File | Description |
|-------|------|-------------|
| `/sales-management` | `sales_management.html` | Sales management |
| `/inventory/low-stock` | `low_stock_management.html` | Low stock |

---

## 🎨 Module Structure

### Retail Module Navigation
```
Dashboard (📊)
├── Sales (💰) → /sales-management
├── Billing (🧾) → /retail/billing
├── Invoices (📄) → /retail/invoices ✅ NEW
├── Products (📦) → /retail/products
├── Inventory (📋) → /inventory/low-stock
├── Customers (👥) → /retail/customers
├── Reports (📈) → /retail/sales
└── Settings (⚙️) → (placeholder)
```

---

## 📋 Invoice Module Files

### Frontend Files
```
✅ templates/retail_invoices.html
   - Invoice list page
   - Stats cards (Total, Amount, Paid, Pending)
   - Filters (Status, Date, Search)
   - Invoice table with pagination
   - Actions (View, Print, Download, Export)

✅ templates/retail_invoice_detail.html
   - Individual invoice view
   - Business & customer details
   - Items table
   - Totals breakdown
   - Print-ready layout
```

### Backend Routes (app.py)
```python
@app.route('/retail/invoices')
def retail_invoices():
    return render_template('retail_invoices.html')

@app.route('/retail/invoice/<invoice_id>')
def retail_invoice_detail(invoice_id):
    return render_template('retail_invoice_detail.html', invoice_id=invoice_id)
```

### API Endpoints (app.py)
```python
@app.route('/api/invoices', methods=['GET'])
def get_invoices():
    # Returns all invoices

@app.route('/api/invoices/<invoice_id>', methods=['GET'])
def get_invoice_details(invoice_id):
    # Returns invoice with items and payments
```

---

## 🔧 How Navigation Works

### Retail Dashboard Navigation Flow
```
1. User clicks "Invoices" in sidebar
   ↓
2. onclick="showModule('invoices')" triggered
   ↓
3. showModule() function called
   ↓
4. loadModuleContent('invoices') called
   ↓
5. Checks: if (module === 'invoices')
   ↓
6. Redirects: window.location.href = '/retail/invoices'
   ↓
7. Flask route handles: @app.route('/retail/invoices')
   ↓
8. Renders: retail_invoices.html
   ↓
9. Page loads with invoice list
```

---

## 📊 File Categories

### Active Production Files
```
✅ Web pages (web_*, index.html, login.html, register.html)
✅ Retail module (retail_*.html)
✅ Hotel module (hotel_*.html)
✅ Mobile app (mobile_web_app.html)
✅ Management pages (sales_management.html, low_stock_management.html)
```

### Backup/Legacy Files
```
⚠️ index_old_backup.html
⚠️ low_stock_management_backup.html
⚠️ mobile_app.html
⚠️ mobile_clean.html
⚠️ mobile_test.html
⚠️ mobile_diagnostic.html
```

---

## 🚀 Quick Reference

### Finding Files

**Need login page?**
- New: `web_login_page.html`
- Old: `login.html`
- Route: `/login`

**Need invoice list?**
- File: `retail_invoices.html`
- Route: `/retail/invoices`
- Nav: Dashboard → Invoices

**Need invoice detail?**
- File: `retail_invoice_detail.html`
- Route: `/retail/invoice/<id>`
- Access: Click "View" on invoice list

**Need billing page?**
- File: `retail_billing.html`
- Route: `/retail/billing`
- Nav: Dashboard → Billing

**Need products page?**
- File: `retail_products.html`
- Route: `/retail/products`
- Nav: Dashboard → Products

---

## 🎯 Best Practices

### Naming Convention
```
✅ DO: web_login_page.html
✅ DO: retail_invoices.html
✅ DO: mobile_web_app.html
❌ DON'T: login123.html
❌ DON'T: new_page.html
❌ DON'T: temp_file.html
```

### File Organization
```
✅ DO: Keep related files together
✅ DO: Use clear, descriptive names
✅ DO: Follow module prefixes
❌ DON'T: Mix different modules
❌ DON'T: Use generic names
❌ DON'T: Create duplicate files
```

### Route Naming
```
✅ DO: /retail/invoices
✅ DO: /hotel/dashboard
✅ DO: /mobile
❌ DON'T: /page1
❌ DON'T: /new_feature
❌ DON'T: /test123
```

---

## 📝 Maintenance

### Adding New Page

1. **Create file with proper naming:**
   ```
   templates/retail_new_feature.html
   ```

2. **Add route in app.py:**
   ```python
   @app.route('/retail/new-feature')
   def retail_new_feature():
       return render_template('retail_new_feature.html')
   ```

3. **Add navigation in retail_dashboard.html:**
   ```html
   <div class="nav-item" onclick="showModule('new-feature')">
       <span class="nav-icon">🆕</span>
       <span class="nav-text">New Feature</span>
   </div>
   ```

4. **Add redirect in loadModuleContent():**
   ```javascript
   if (module === 'new-feature') {
       window.location.href = '/retail/new-feature';
       return;
   }
   ```

---

## ✅ Current Status

### Completed Modules
- ✅ Web landing page
- ✅ Login/Register
- ✅ Retail Dashboard
- ✅ Billing & POS
- ✅ **Invoices (NEW!)** ← Just added
- ✅ Products
- ✅ Customers
- ✅ Sales Reports
- ✅ Low Stock Management
- ✅ Mobile PWA

### In Progress
- 🚧 Hotel module (basic structure)
- 🚧 Settings page
- 🚧 Advanced reports

---

## 📞 Quick Help

**Can't find a file?**
- Check this document
- Look for module prefix (web_, retail_, hotel_, mobile_)
- Check route in app.py

**Navigation not working?**
- Check retail_dashboard.html navigation items
- Check loadModuleContent() function
- Check route exists in app.py

**Page not loading?**
- Check file exists in templates/
- Check route in app.py
- Check server is running
- Check browser console for errors

---

**Last Updated:** December 6, 2024  
**Status:** ✅ Organized & Documented  
**Invoice Module:** ✅ Fully Integrated
