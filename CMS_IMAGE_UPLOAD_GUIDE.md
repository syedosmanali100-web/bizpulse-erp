# 🖼️ CMS Image Upload - Complete Guide

## 📸 CMS Mein Images Kahan-Kahan Add Kar Sakte Ho?

---

### 1. **Site Settings** (`/cms/settings`)

**Upload Kar Sakte Ho:**
- ✅ **Logo** - Company/Website ka main logo
- ✅ **Favicon** - Browser tab mein chota icon

**Website Pe Kahan Dikhega:**
```
Navbar (Top)
├── Logo (Top-left corner)
└── Favicon (Browser tab icon)
```

**Kaise Upload Karein:**
1. CMS Dashboard → Site Settings
2. "Logo" section mein file choose karein
3. Image upload hogi
4. Save Settings button click karein
5. Done! Logo navbar mein dikhai dega

---

### 2. **Hero Section** (`/cms/hero`)

**Upload Kar Sakte Ho:**
- ✅ **Background Image** - Homepage ka main banner

**Website Pe Kahan Dikhega:**
```
Homepage
└── Hero Section (Top full-width banner)
    └── Background Image (Behind title & button)
```

**Kaise Upload Karein:**
1. CMS Dashboard → Hero Section
2. "Background Image" section mein file choose karein
3. Image upload hogi
4. Preview dikhega
5. Save button click karein
6. Done! Homepage banner background ban jayega

---

### 3. **Features** (`/cms/features`)

**Upload Kar Sakte Ho:**
- ✅ **Feature Icons** - Har feature ke liye icon/image

**Website Pe Kahan Dikhega:**
```
Homepage
└── Features Section
    ├── Feature 1 (Icon + Title + Description)
    ├── Feature 2 (Icon + Title + Description)
    └── Feature 3 (Icon + Title + Description)
```

**Kaise Upload Karein:**
1. CMS Dashboard → Features
2. "Add Feature" button click karein
3. Title aur Description fill karein
4. "Icon Image" mein file choose karein
5. Image upload hogi
6. Save button click karein
7. Done! Feature card mein icon dikhai dega

---

### 4. **Pricing Plans** (`/cms/pricing`)

**Upload Kar Sakte Ho:**
- ❌ Currently no image upload
- ℹ️ Only text-based pricing plans

**Website Pe Kahan Dikhega:**
```
Homepage/Pricing Page
└── Pricing Section
    ├── Plan 1 (Name, Price, Features)
    ├── Plan 2 (Name, Price, Features)
    └── Plan 3 (Name, Price, Features)
```

---

### 5. **Testimonials** (`/cms/testimonials`)

**Upload Kar Sakte Ho:**
- ✅ **Avatar/Profile Picture** - Customer ka photo

**Website Pe Kahan Dikhega:**
```
Homepage
└── Testimonials Section
    ├── Testimonial 1
    │   ├── Avatar (Customer photo)
    │   ├── Name & Role
    │   └── Review Message
    └── Testimonial 2
        ├── Avatar (Customer photo)
        ├── Name & Role
        └── Review Message
```

**Kaise Upload Karein:**
1. CMS Dashboard → Testimonials
2. "Add Testimonial" button click karein
3. Name, Role, Company, Message fill karein
4. "Avatar Image" mein customer ka photo upload karein
5. Rating select karein
6. Save button click karein
7. Done! Testimonial mein photo dikhai dega

---

### 6. **FAQs** (`/cms/faqs`)

**Upload Kar Sakte Ho:**
- ❌ No image upload
- ℹ️ Only text-based Q&A

**Website Pe Kahan Dikhega:**
```
Homepage/FAQ Page
└── FAQ Section
    ├── Question 1 → Answer 1
    ├── Question 2 → Answer 2
    └── Question 3 → Answer 3
```

---

### 7. **Gallery** (`/cms/gallery`) ⭐ **MAIN FEATURE**

**Upload Kar Sakte Ho:**
- ✅ **Any Images** - Products, Team, Office, Events, etc.
- ✅ **Multiple Categories** - Organize by type
- ✅ **Unlimited Images** - Jitne chahiye utne

**Website Pe Kahan Dikhega:**
```
Gallery Page
└── Image Grid (Category-wise)
    ├── Products Category
    │   ├── Product Image 1
    │   ├── Product Image 2
    │   └── Product Image 3
    ├── Team Category
    │   ├── Team Photo 1
    │   └── Team Photo 2
    └── Office Category
        ├── Office Photo 1
        └── Office Photo 2
```

**Kaise Upload Karein:**
1. CMS Dashboard → Gallery
2. **"Add Image"** button click karein
3. **Form fill karein:**
   - Title: Image ka naam
   - Description: Image ke baare mein
   - Category: Products/Team/Office/Events/etc.
   - Image: File choose karein (upload hoga)
   - Display Order: Kaunsa pehle dikhana hai
4. **"Save Image"** button click karein
5. **Done!** Image gallery mein add ho jayega

**Categories Available:**
- General (Default)
- Products (Product photos)
- Team (Team members)
- Office (Office photos)
- Events (Event photos)
- Customers (Customer photos)

---

## 🎯 Gallery Features (NEW!)

### ✅ What You Can Do:

1. **Add Images**
   - Upload any image
   - Add title & description
   - Choose category
   - Set display order

2. **Edit Images**
   - Change title/description
   - Change category
   - Replace image
   - Update display order

3. **Delete Images**
   - Remove unwanted images
   - Confirmation before delete

4. **View Images**
   - Click image to view full size
   - Lightbox view
   - Close with X button

5. **Organize**
   - Category-wise organization
   - Display order control
   - Grid layout

---

## 📂 Image Storage

**Where Images Are Stored:**
```
BizPulse_ERP/
└── static/
    └── uploads/
        ├── 20241207_123456_logo.png
        ├── 20241207_123457_hero-bg.jpg
        ├── 20241207_123458_feature-icon.svg
        └── 20241207_123459_gallery-image.jpg
```

**Image URL Format:**
```
/static/uploads/TIMESTAMP_FILENAME.ext
```

**Example:**
```
/static/uploads/20241207_143022_product-photo.jpg
```

---

## 🎨 Image Guidelines

### Recommended Sizes:

**Logo:**
- Width: 200-300px
- Height: 50-80px
- Format: PNG (transparent background)

**Favicon:**
- Size: 32x32px or 64x64px
- Format: PNG or ICO

**Hero Background:**
- Width: 1920px
- Height: 1080px
- Format: JPG (optimized)

**Feature Icons:**
- Size: 64x64px or 128x128px
- Format: PNG or SVG

**Testimonial Avatars:**
- Size: 100x100px or 200x200px
- Format: JPG or PNG (square)

**Gallery Images:**
- Width: 800-1200px
- Height: 600-900px
- Format: JPG (optimized)

### File Size:
- Maximum: 16MB
- Recommended: Under 2MB
- Optimize before upload

### Allowed Formats:
- ✅ PNG
- ✅ JPG/JPEG
- ✅ GIF
- ✅ SVG
- ✅ WEBP

---

## 🚀 Quick Start - Gallery Upload

### Step-by-Step:

1. **Login to CMS**
   ```
   http://localhost:5000/cms/login
   Username: admin
   Password: admin123
   ```

2. **Go to Gallery**
   - Click "Gallery" card on dashboard
   - Or visit: `http://localhost:5000/cms/gallery`

3. **Click "Add Image"**
   - Modal will open

4. **Fill Form:**
   ```
   Title: "Our New Product"
   Description: "Latest product launch 2024"
   Category: Products
   Image: [Choose file from computer]
   Display Order: 0
   ```

5. **Upload Image:**
   - Click "Choose File"
   - Select image from computer
   - Image will upload automatically
   - Preview will show

6. **Save:**
   - Click "Save Image"
   - Image added to gallery!

7. **View:**
   - Image appears in grid
   - Click to view full size
   - Edit or Delete anytime

---

## 💡 Pro Tips

### For Best Results:

1. **Optimize Images:**
   - Use tools like TinyPNG
   - Compress before upload
   - Faster loading

2. **Use Categories:**
   - Organize by type
   - Easy to find
   - Better presentation

3. **Add Descriptions:**
   - SEO friendly
   - Better context
   - Professional look

4. **Display Order:**
   - 0 = First
   - 1 = Second
   - 2 = Third
   - Control sequence

5. **Consistent Naming:**
   - Use clear titles
   - Descriptive names
   - Easy to manage

---

## 🎯 Summary

**Total Image Upload Points: 5**

1. ✅ **Site Settings** - Logo & Favicon
2. ✅ **Hero Section** - Background Image
3. ✅ **Features** - Feature Icons
4. ✅ **Testimonials** - Customer Avatars
5. ✅ **Gallery** - Any Images (Main Feature)

**Gallery is the MAIN place** for uploading multiple images!

**All images stored in:** `/static/uploads/`

**All images accessible via:** `http://localhost:5000/static/uploads/FILENAME`

---

## 🌐 Website Integration

**To Display Gallery on Website:**

```html
<!-- Add this to your website page -->
<div id="gallery"></div>

<script>
fetch('/api/cms/gallery')
    .then(res => res.json())
    .then(images => {
        const gallery = document.getElementById('gallery');
        images.forEach(img => {
            gallery.innerHTML += `
                <div class="gallery-item">
                    <img src="${img.image_url}" alt="${img.title}">
                    <h3>${img.title}</h3>
                    <p>${img.description}</p>
                </div>
            `;
        });
    });
</script>
```

---

**Perfect! Ab aap Gallery mein unlimited images upload kar sakte ho! 🎉**
