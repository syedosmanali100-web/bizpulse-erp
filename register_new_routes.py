"""
Register New Production-Grade API Routes
This file integrates the new clean billing/invoice backend with app.py
"""

def register_new_routes(app):
    """Register all new production-grade API routes"""
    
    # Import blueprints
    from api.billing_routes import billing_bp
    from api.invoice_routes import invoice_bp
    from api.sales_routes import sales_bp
    from api.inventory_routes import inventory_bp
    from api.product_routes import product_bp
    
    # Register blueprints
    app.register_blueprint(billing_bp)
    app.register_blueprint(invoice_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(product_bp)
    
    print("✅ New production-grade API routes registered successfully!")
    print("📋 Available endpoints:")
    print("   • POST /api/bills - Create bill")
    print("   • GET /api/bills - Get bills")
    print("   • GET /api/bills/<id> - Get bill by ID")
    print("   • DELETE /api/bills/<id> - Delete bill")
    print("   • POST /api/invoices - Create invoice")
    print("   • GET /api/invoices - Get invoices")
    print("   • GET /api/invoices/<id> - Get invoice by ID")
    print("   • DELETE /api/invoices/<id> - Delete invoice")
    print("   • GET /api/invoices/summary - Get invoice summary")
    print("   • GET /api/sales - Get sales data")
    print("   • GET /api/sales/summary - Get sales summary")
    print("   • GET /api/sales/by-product - Get sales by product")
    print("   • GET /api/sales/by-category - Get sales by category")
    print("   • GET /api/inventory - Get inventory status")
    print("   • GET /api/inventory/low-stock - Get low stock items")
    print("   • POST /api/inventory/sync - Sync inventory")
    print("   • GET /api/products - Get products")
    print("   • POST /api/products - Create product")
    print("   • GET /api/products/<id> - Get product by ID")
    print("   • PUT /api/products/<id> - Update product")
    print("   • DELETE /api/products/<id> - Delete product")
    print("   • GET /api/products/barcode/<barcode> - Get product by barcode")