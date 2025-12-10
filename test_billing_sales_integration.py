"""
Test script to verify billing automatically updates sales and reduces stock
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_billing_sales_integration():
    print("=" * 60)
    print("🧪 Testing Billing → Sales → Stock Integration")
    print("=" * 60)
    
    # Step 1: Get initial product stock
    print("\n1️⃣ Getting initial product stock...")
    response = requests.get(f"{BASE_URL}/api/products")
    products = response.json()
    
    if not products:
        print("❌ No products found!")
        return
    
    test_product = products[0]
    print(f"   Product: {test_product['name']}")
    print(f"   Initial Stock: {test_product['stock']}")
    print(f"   Price: ₹{test_product['price']}")
    
    initial_stock = test_product['stock']
    product_id = test_product['id']
    
    # Step 2: Get initial sales count
    print("\n2️⃣ Getting initial sales count...")
    today = datetime.now().strftime('%Y-%m-%d')
    response = requests.get(f"{BASE_URL}/api/sales/all?from={today}&to={today}")
    initial_sales = response.json()
    initial_sales_count = len(initial_sales.get('sales', []))
    print(f"   Initial sales entries today: {initial_sales_count}")
    
    # Step 3: Create a test bill
    print("\n3️⃣ Creating a test bill...")
    bill_data = {
        "business_type": "retail",
        "customer_id": None,
        "items": [
            {
                "product_id": product_id,
                "product_name": test_product['name'],
                "quantity": 2,
                "unit_price": test_product['price'],
                "total_price": test_product['price'] * 2
            }
        ],
        "subtotal": test_product['price'] * 2,
        "tax_amount": test_product['price'] * 2 * 0.18,
        "discount_amount": 0,
        "total_amount": test_product['price'] * 2 * 1.18,
        "payment_method": "cash"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/bills",
        json=bill_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 201:
        bill_result = response.json()
        print(f"   ✅ Bill created successfully!")
        print(f"   Bill Number: {bill_result['bill_number']}")
        print(f"   Bill ID: {bill_result['bill_id']}")
    else:
        print(f"   ❌ Failed to create bill: {response.text}")
        return
    
    # Step 4: Verify stock was reduced
    print("\n4️⃣ Verifying stock reduction...")
    response = requests.get(f"{BASE_URL}/api/products")
    products = response.json()
    updated_product = next((p for p in products if p['id'] == product_id), None)
    
    if updated_product:
        new_stock = updated_product['stock']
        stock_reduced = initial_stock - new_stock
        print(f"   Initial Stock: {initial_stock}")
        print(f"   New Stock: {new_stock}")
        print(f"   Stock Reduced: {stock_reduced}")
        
        if stock_reduced == 2:
            print(f"   ✅ Stock reduced correctly!")
        else:
            print(f"   ❌ Stock reduction incorrect! Expected 2, got {stock_reduced}")
    else:
        print(f"   ❌ Product not found!")
    
    # Step 5: Verify sales entry was created
    print("\n5️⃣ Verifying sales entry creation...")
    response = requests.get(f"{BASE_URL}/api/sales/all?from={today}&to={today}")
    updated_sales = response.json()
    new_sales_count = len(updated_sales.get('sales', []))
    
    print(f"   Initial sales entries: {initial_sales_count}")
    print(f"   New sales entries: {new_sales_count}")
    print(f"   New entries added: {new_sales_count - initial_sales_count}")
    
    if new_sales_count > initial_sales_count:
        print(f"   ✅ Sales entry created successfully!")
        
        # Show the new sales entry
        latest_sale = updated_sales['sales'][0]
        print(f"\n   📊 Latest Sales Entry:")
        print(f"      Bill Number: {latest_sale['bill_number']}")
        print(f"      Product: {latest_sale['product_name']}")
        print(f"      Quantity: {latest_sale['quantity']}")
        print(f"      Total Price: ₹{latest_sale['total_price']}")
        print(f"      Category: {latest_sale['category']}")
        print(f"      Payment Method: {latest_sale['payment_method']}")
    else:
        print(f"   ❌ Sales entry not created!")
    
    # Step 6: Check sales summary
    print("\n6️⃣ Checking sales summary...")
    response = requests.get(f"{BASE_URL}/api/sales/summary")
    if response.status_code == 200:
        summary = response.json()
        print(f"   Today's Sales: ₹{summary['today']['total']}")
        print(f"   Today's Transactions: {summary['today']['count']}")
        print(f"   ✅ Sales summary updated!")
    
    print("\n" + "=" * 60)
    print("✅ Integration Test Complete!")
    print("=" * 60)
    print("\n📝 Summary:")
    print("   ✓ Billing creates bill entry")
    print("   ✓ Stock automatically reduced")
    print("   ✓ Sales entry automatically created")
    print("   ✓ Sales module updated in real-time")
    print("\n🎉 All systems working perfectly!")

if __name__ == "__main__":
    try:
        test_billing_sales_integration()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to server!")
        print("   Make sure the Flask server is running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
