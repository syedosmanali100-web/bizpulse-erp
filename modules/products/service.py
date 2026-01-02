"""
Products service
COPIED AS-IS from app.py
"""

import sqlite3
from datetime import datetime
from modules.shared.database import get_db_connection, generate_id

class ProductsService:
    
    def get_db_connection(self):
        return get_db_connection()
    
    def get_current_timestamp(self):
        return datetime.now().isoformat()
    
    def debug_products(self):
        """Debug endpoint to see all products with barcode data"""
        conn = get_db_connection()
        products = conn.execute("SELECT id, name, code, barcode_data, price, stock FROM products WHERE is_active = 1 ORDER BY created_at DESC LIMIT 20").fetchall()
        conn.close()
        
        return {
            "success": True,
            "total_products": len(products),
            "products": [dict(p) for p in products]
        }
    
    def add_barcode_to_product(self, product_id, barcode):
        """Add barcode to existing product"""
        conn = get_db_connection()
        
        # Check if product exists
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if not product:
            conn.close()
            return {"success": False, "error": "Product not found"}
        
        # Update product with barcode
        conn.execute("""UPDATE products 
            SET barcode_data = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?""", (barcode, product_id))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Barcode {barcode} added to product {product['name']}",
            "product_id": product_id,
            "barcode": barcode
        }
    
    def search_product_by_barcode(self, barcode):
        """⚡ LIGHTNING-FAST barcode search - Optimized for instant response like RetailsDaddy"""
        # Quick validation - no logging for speed
        if not barcode or len(barcode.strip()) == 0:
            return {"success": False, "error": "Invalid barcode"}
        
        barcode = barcode.strip()
        conn = get_db_connection()
        
        # ⚡ OPTIMIZED QUERY - Single query with index lookup
        # Uses the unique index on barcode_data for instant search
        product = conn.execute("""SELECT id, code, name, category, price, cost, stock, 
                                         min_stock, unit, business_type, barcode_data, 
                                         barcode_image, image_url, is_active 
                                  FROM products 
                                  WHERE barcode_data = ? AND is_active = 1 
                                  LIMIT 1""", (barcode,)).fetchone()
        
        conn.close()
        
        if product:
            # ⚡ INSTANT RESPONSE - Return immediately with minimal data
            return {
                "success": True,
                "product": {
                    "id": product['id'],
                    "code": product['code'],
                    "name": product['name'],
                    "category": product['category'],
                    "price": product['price'],
                    "cost": product['cost'],
                    "stock": product['stock'],
                    "min_stock": product['min_stock'],
                    "unit": product['unit'],
                    "business_type": product['business_type'],
                    "barcode_data": product['barcode_data'],
                    "barcode_image": product['barcode_image'],
                    "image_url": product['image_url']
                }
            }
        else:
            # ⚡ FAST FAILURE - No debug info for speed
            return {
                "success": False,
                "message": "Product not found",
                "barcode": barcode
            }
    
    def add_product(self, data):
        """Add a new product"""
        print(f"[PRODUCT ADD] Received data: {data}")
        
        # Validate required fields
        if not data or not data.get('name') or not data.get('price'):
            return {
                "success": False,
                "error": "Product name and price are required"
            }
        
        # Extract and validate barcode data
        barcode_data = data.get('barcode_data', '').strip() if data.get('barcode_data') else None
        barcode_image = data.get('barcode_image')
        
        conn = get_db_connection()
        
        # CRITICAL: Check if barcode already exists (if provided)
        if barcode_data:
            existing_barcode = conn.execute("""SELECT id, name FROM products 
                WHERE barcode_data = ? AND is_active = 1""", (barcode_data,)).fetchone()
            
            if existing_barcode:
                conn.close()
                return {
                    "success": False,
                    "error": f"Product already exists with this barcode",
                    "existing_product": {
                        "id": existing_barcode['id'],
                        "name": existing_barcode['name']
                    },
                    "barcode": barcode_data
                }
        
        # Generate product ID and code
        product_id = generate_id()
        product_code = data.get('code', '').strip() or f"P{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Check if product code already exists
        existing_code = conn.execute('SELECT id FROM products WHERE code = ?', (product_code,)).fetchone()
        if existing_code:
            product_code = f"{product_code}_{datetime.now().strftime('%H%M%S')}"
        
        # Insert product with all validations
        try:
            conn.execute("""INSERT INTO products (
                    id, code, name, category, price, cost, stock, min_stock, 
                    unit, business_type, barcode_data, barcode_image, image_url, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", (
                product_id, 
                product_code, 
                data['name'].strip(), 
                data.get('category', 'General'),
                float(data['price']), 
                float(data.get('cost', 0)), 
                int(data.get('stock', 0)),
                int(data.get('min_stock', 0)), 
                data.get('unit', 'piece'), 
                data.get('business_type', 'both'),
                barcode_data,  # Store scanned barcode value (unique)
                barcode_image,  # Store barcode image
                data.get('image_url'),  # Store product image URL
                1  # is_active
            ))
            
            conn.commit()
            print(f"[PRODUCT ADD] Successfully added product: {product_id}")
            
        except sqlite3.IntegrityError as e:
            conn.close()
            if 'barcode_data' in str(e):
                return {
                    "success": False,
                    "error": "Product with this barcode already exists",
                    "barcode": barcode_data
                }
            else:
                return {
                    "success": False,
                    "error": f"Database constraint error: {str(e)}"
                }
        
        conn.close()
        
        return {
            "success": True,
            "message": "Product added successfully", 
            "product": {
                "id": product_id,
                "code": product_code,
                "name": data['name'],
                "barcode": barcode_data
            }
        }
    
    def update_product(self, product_id, data):
        """Update an existing product"""
        print(f"[PRODUCT UPDATE] Updating product {product_id} with data: {data}")
        
        # Validate required fields
        if not data or not data.get('name') or not data.get('price'):
            return {
                "success": False,
                "error": "Product name and price are required"
            }
        
        conn = get_db_connection()
        
        # Check if product exists
        existing_product = conn.execute("SELECT * FROM products WHERE id = ? AND is_active = 1", (product_id,)).fetchone()
        
        if not existing_product:
            conn.close()
            return {
                "success": False,
                "error": "Product not found"
            }
        
        # Extract and validate barcode data
        barcode_data = data.get('barcode_data', '').strip() if data.get('barcode_data') else None
        barcode_image = data.get('barcode_image')
        
        # Check if barcode already exists (excluding current product)
        if barcode_data:
            existing_barcode = conn.execute("""SELECT id, name FROM products 
                WHERE barcode_data = ? AND is_active = 1 AND id != ?""", (barcode_data, product_id)).fetchone()
            
            if existing_barcode:
                conn.close()
                return {
                    "success": False,
                    "error": f"Another product already exists with this barcode",
                    "existing_product": {
                        "id": existing_barcode['id'],
                        "name": existing_barcode['name']
                    },
                    "barcode": barcode_data
                }
        
        # Update product
        try:
            conn.execute("""UPDATE products SET
                    code = ?, name = ?, category = ?, price = ?, cost = ?, 
                    stock = ?, min_stock = ?, unit = ?, business_type = ?,
                    barcode_data = ?, barcode_image = ?, image_url = ?
                WHERE id = ?""", (
                data.get('code', existing_product['code']),
                data['name'].strip(), 
                data.get('category', existing_product['category']),
                float(data['price']), 
                float(data.get('cost', existing_product['cost'])), 
                int(data.get('stock', existing_product['stock'])),
                int(data.get('min_stock', existing_product['min_stock'])), 
                data.get('unit', existing_product['unit']), 
                data.get('business_type', existing_product['business_type']),
                barcode_data,
                barcode_image,
                data.get('image_url', existing_product['image_url']),  # Handle image URL
                product_id
            ))
            
            conn.commit()
            print(f"[PRODUCT UPDATE] Successfully updated product: {product_id}")
            
        except sqlite3.IntegrityError as e:
            conn.close()
            if 'barcode_data' in str(e):
                return {
                    "success": False,
                    "error": "Product with this barcode already exists",
                    "barcode": barcode_data
                }
            else:
                return {
                    "success": False,
                    "error": f"Database constraint error: {str(e)}"
                }
        
        conn.close()
        
        return {
            "success": True,
            "message": "Product updated successfully", 
            "product": {
                "id": product_id,
                "name": data['name'],
                "image_url": data.get('image_url')
            }
        }
    
    def delete_product(self, product_id):
        """Delete product completely from database"""
        print(f"[PRODUCT DELETE] Deleting product: {product_id}")
        
        conn = get_db_connection()
        
        # Check if product exists
        product = conn.execute("SELECT id, name, barcode_data FROM products WHERE id = ?", (product_id,)).fetchone()
        
        if not product:
            conn.close()
            return {
                "success": False,
                "error": "Product not found"
            }
        
        # HARD DELETE - Remove from database completely
        conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        conn.close()
        
        print(f"[PRODUCT DELETE] Successfully deleted: {product['name']}")
        
        return {
            "success": True,
            "message": f"Product '{product['name']}' deleted successfully",
            "deleted_product": {
                "id": product_id,
                "name": product['name'],
                "barcode": product['barcode_data']
            }
        }
    
    def recommend_product_images(self, product_name, category):
        """
        Recommend product images based on name and category
        Uses Unsplash API for high-quality, royalty-free images
        """
        # Build search query
        search_terms = []
        
        # Add product name (clean it up)
        clean_name = product_name.lower()
        # Remove common words that don't help with image search
        exclude_words = ['1kg', '500g', '250g', '1l', '500ml', 'pack', 'piece', 'pcs']
        for word in exclude_words:
            clean_name = clean_name.replace(word, '')
        
        search_terms.append(clean_name.strip())
        
        # Add category if provided
        if category and category.lower() != 'other':
            search_terms.append(category.lower())
        
        # Create search query
        search_query = ' '.join(search_terms)
        
        print(f"🔍 Image search for: '{product_name}' -> Query: '{search_query}'")
        
        # Try multiple search approaches for better results
        image_results = []
        
        # Method 1: Direct Unsplash search
        unsplash_images = self.search_unsplash_images(search_query)
        if unsplash_images:
            image_results.extend(unsplash_images)
        
        # Method 2: Fallback with category only if no results
        if len(image_results) < 3 and category:
            category_images = self.search_unsplash_images(category)
            if category_images:
                image_results.extend(category_images)
        
        # Method 3: Generic food/product images as last resort
        if len(image_results) < 3:
            generic_images = self.get_generic_product_images(category)
            image_results.extend(generic_images)
        
        # Remove duplicates and limit to 8 images
        seen_urls = set()
        unique_images = []
        for img in image_results:
            if img['url'] not in seen_urls and len(unique_images) < 8:
                seen_urls.add(img['url'])
                unique_images.append(img)
        
        if not unique_images:
            return {
                'success': False,
                'error': 'No suitable images found. Please try a different product name or upload your own image.'
            }
        
        return {
            'success': True,
            'images': unique_images,
            'search_query': search_query,
            'total_found': len(unique_images)
        }
    
    def search_unsplash_images(self, query, per_page=6):
        """
        Search for actual product images based on product name
        Uses curated product-specific images for reliable results
        """
        try:
            # Clean and prepare search query
            clean_query = query.strip().lower()
            
            # Remove common size indicators that don't help with image search
            size_words = ['1kg', '500g', '250g', '1l', '500ml', '2kg', '5kg', 'pack', 'piece', 'pcs', 'box', 'bottle']
            for word in size_words:
                clean_query = clean_query.replace(word, '').strip()
            
            # Handle Hindi/Hinglish to English translation for better search
            hindi_to_english = {
                'haldi': 'turmeric',
                'dhaniya': 'coriander',
                'jeera': 'cumin',
                'atta': 'wheat flour',
                'chawal': 'rice',
                'dal': 'lentils',
                'namak': 'salt',
                'chini': 'sugar',
                'tel': 'oil',
                'doodh': 'milk',
                'pyaz': 'onion',
                'aloo': 'potato',
                'tamatar': 'tomato',
                'mirch': 'chili pepper',
                'adrak': 'ginger',
                'lehsun': 'garlic',
                'methi': 'fenugreek',
                'sarson': 'mustard',
                'til': 'sesame',
                'badam': 'almonds',
                'kaju': 'cashew',
                'pista': 'pistachio'
            }
            
            # Translate Hindi words to English for better search
            search_terms = []
            words = clean_query.split()
            for word in words:
                if word in hindi_to_english:
                    search_terms.append(hindi_to_english[word])
                else:
                    search_terms.append(word)
            
            # Create final search query
            final_query = ' '.join(search_terms)
            print(f"🔍 Searching for: '{query}' → '{final_query}'")
            
            images = []
            
            # Method 1: Use curated product-specific images (primary method)
            try:
                curated_images = self.get_product_fallback_images(final_query, per_page)
                if curated_images:
                    images.extend(curated_images)
                    print(f"✅ Found {len(curated_images)} curated product-specific images")
                else:
                    print("⚠️ No curated images found for this product")
                    
            except Exception as e:
                print(f"❌ Curated images failed: {e}")
            
            # Method 2: Try external API if we need more images (optional enhancement)
            if len(images) < per_page:
                try:
                    import requests
                    # Use Pixabay's free API
                    pixabay_url = "https://pixabay.com/api/"
                    params = {
                        'key': '9656065-a4094594c34f9ac14c7fc4c39',  # Free public key
                        'q': final_query,
                        'image_type': 'photo',
                        'category': 'food',
                        'min_width': 200,
                        'min_height': 200,
                        'per_page': per_page - len(images),
                        'safesearch': 'true'
                    }
                    
                    response = requests.get(pixabay_url, params=params, timeout=10)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        for hit in data.get('hits', []):
                            if len(images) >= per_page:
                                break
                            images.append({
                                'url': hit.get('webformatURL', ''),
                                'thumbnail': hit.get('previewURL', ''),
                                'title': f"{query.title()} - {hit.get('tags', '').title()}",
                                'source': 'Pixabay',
                                'search_term': final_query
                            })
                        
                        print(f"✅ Found {len(data.get('hits', []))} additional images from Pixabay")
                    
                except Exception as e:
                    print(f"❌ Pixabay search failed: {e}")
            
            # Remove duplicates and limit results
            seen_urls = set()
            unique_images = []
            for img in images:
                if img['url'] not in seen_urls and len(unique_images) < per_page:
                    seen_urls.add(img['url'])
                    unique_images.append(img)
            
            print(f"✅ Generated {len(unique_images)} images for '{query}'")
            return unique_images
            
        except Exception as e:
            print(f"❌ Image search error: {e}")
            return self.get_guaranteed_fallback_images(query)
    
    def get_guaranteed_fallback_images(self, query):
        """
        Guaranteed fallback images that always work
        """
        try:
            images = []
            
            # Use reliable Picsum IDs
            reliable_ids = [292, 326, 431, 488, 691, 715, 835, 884]
            
            for i, img_id in enumerate(reliable_ids):
                url = f"https://picsum.photos/300/300?random={img_id}"
                images.append({
                    'url': url,
                    'thumbnail': url,
                    'title': f"{query.title()} - Fallback Image {i + 1}",
                    'source': 'Picsum (Guaranteed)',
                    'search_term': query
                })
            
            return images
            
        except Exception as e:
            print(f"❌ Even guaranteed fallback failed: {e}")
            # Last resort - return base64 placeholder
            placeholder_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Crect width='300' height='300' fill='%23f0f0f0'/%3E%3Ctext x='150' y='150' text-anchor='middle' dy='.3em' font-family='Arial' font-size='16' fill='%23999'%3EProduct Image%3C/text%3E%3C/svg%3E"
            
            return [{
                'url': placeholder_svg,
                'thumbnail': placeholder_svg,
                'title': f"{query.title()} - Placeholder",
                'source': 'SVG Placeholder',
                'search_term': query
            }]
    
    def get_product_fallback_images(self, query, count=6):
        """
        Get curated product-specific fallback images
        """
        try:
            # Product-specific image mappings with real URLs
            product_image_map = {
                'rice': [
                    'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&h=300&fit=crop',  # Basmati rice
                    'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=300&h=300&fit=crop',  # Rice grains
                    'https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?w=300&h=300&fit=crop',  # Rice bowl
                    'https://images.unsplash.com/photo-1550989460-0adf9ea622e2?w=300&h=300&fit=crop',  # White rice
                    'https://images.unsplash.com/photo-1603048297172-c92544798d5a?w=300&h=300&fit=crop',  # Rice field
                    'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=300&h=300&fit=crop'   # Cooked rice
                ],
                'turmeric': [
                    'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=300&h=300&fit=crop',  # Turmeric powder
                    'https://images.unsplash.com/photo-1609501676725-7186f734b2b0?w=300&h=300&fit=crop',  # Fresh turmeric
                    'https://images.unsplash.com/photo-1615485925763-4d5b3a9c3b3a?w=300&h=300&fit=crop',  # Turmeric root
                    'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=300&h=300&fit=crop',  # Spices
                    'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=300&h=300&fit=crop',  # Golden spice
                    'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=300&h=300&fit=crop'   # Haldi powder
                ],
                'wheat flour': [
                    'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=300&h=300&fit=crop',  # Flour
                    'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop',  # Wheat
                    'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=300&h=300&fit=crop',  # Atta
                    'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop',  # Wheat grains
                    'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=300&h=300&fit=crop',  # White flour
                    'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop'   # Whole wheat
                ],
                'sugar': [
                    'https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=300&h=300&fit=crop',  # Sugar cubes
                    'https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=300&h=300&fit=crop',  # White sugar
                    'https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=300&h=300&fit=crop',  # Sugar crystals
                    'https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=300&h=300&fit=crop',  # Granulated sugar
                    'https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=300&h=300&fit=crop',  # Sugar bowl
                    'https://images.unsplash.com/photo-1571115764595-644a1f56a55c?w=300&h=300&fit=crop'   # Sweet sugar
                ],
                'oil': [
                    'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop',  # Cooking oil
                    'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop',  # Oil bottle
                    'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop',  # Olive oil
                    'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop',  # Vegetable oil
                    'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop',  # Sunflower oil
                    'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=300&h=300&fit=crop'   # Mustard oil
                ]
            }
            
            images = []
            query_lower = query.lower()
            
            # Find matching product images
            for product, urls in product_image_map.items():
                if product in query_lower or any(word in query_lower for word in product.split()):
                    for i, url in enumerate(urls[:count]):
                        images.append({
                            'url': url,
                            'thumbnail': url,
                            'title': f"{query.title()} - {product.title()} {i+1}",
                            'source': 'Curated Unsplash',
                            'search_term': product
                        })
                    break
            
            # If no specific match found, use generic food images
            if not images:
                generic_food_urls = [
                    'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=300&h=300&fit=crop',  # Spices
                    'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=300&h=300&fit=crop',  # Ingredients
                    'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=300&h=300&fit=crop',  # Food items
                    'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=300&h=300&fit=crop',  # Grains
                    'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=300&h=300&fit=crop',  # Food products
                    'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=300&h=300&fit=crop'   # Kitchen items
                ]
                
                for i, url in enumerate(generic_food_urls[:count]):
                    images.append({
                        'url': url,
                        'thumbnail': url,
                        'title': f"{query.title()} - Food Product {i+1}",
                        'source': 'Generic Food Images',
                        'search_term': query
                    })
            
            return images[:count]
            
        except Exception as e:
            print(f"❌ Fallback images failed: {e}")
            return []
    
    def get_generic_product_images(self, category):
        """Get generic product images based on category"""
        return self.get_guaranteed_fallback_images(category or 'product')