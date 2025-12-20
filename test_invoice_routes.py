#!/usr/bin/env python3
"""
Test invoice routes and APIs
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
import json

def test_invoice_routes():
    """Test invoice routes"""
    
    print("🧪 Testing Invoice Routes")
    print("=" * 40)
    
    with app.test_client() as client:
        
        # Test 1: Invoice list page
        print("📋 Testing /retail/invoices route...")
        response = client.get('/retail/invoices')
        if response.status_code == 200:
            print("✅ Invoice list page: Working")
        else:
            print(f"❌ Invoice list page failed: {response.status_code}")
        
        # Test 2: Invoice detail page
        print("📋 Testing /retail/invoice/<id> route...")
        response = client.get('/retail/invoice/test-id')
        if response.status_code == 200:
            print("✅ Invoice detail page: Working")
        else:
            print(f"❌ Invoice detail page failed: {response.status_code}")
        
        # Test 3: Invoice demo page
        print("📋 Testing /invoice-demo route...")
        response = client.get('/invoice-demo')
        if response.status_code == 200:
            print("✅ Invoice demo page: Working")
        else:
            print(f"❌ Invoice demo page failed: {response.status_code}")
        
        # Test 4: Invoice API
        print("📋 Testing /api/invoices API...")
        response = client.get('/api/invoices')
        if response.status_code == 200:
            data = response.get_json()
            print(f"✅ Invoice API: Working ({len(data)} invoices found)")
        else:
            print(f"❌ Invoice API failed: {response.status_code}")
        
        # Test 5: Invoice detail API (with existing bill)
        print("📋 Testing /api/invoices/<id> API...")
        
        # First create a test bill to get a real ID
        test_bill_data = {
            "customer_id": None,
            "business_type": "retail",
            "subtotal": 100.0,
            "tax_amount": 18.0,
            "total_amount": 118.0,
            "payment_method": "cash",
            "items": [
                {
                    "product_id": "test-product-1",
                    "product_name": "Test Product",
                    "quantity": 1,
                    "unit_price": 100.0,
                    "total_price": 100.0
                }
            ]
        }
        
        bill_response = client.post(
            '/api/bills',
            data=json.dumps(test_bill_data),
            content_type='application/json'
        )
        
        if bill_response.status_code == 201:
            bill_result = bill_response.get_json()
            bill_id = bill_result.get('bill_id')
            
            # Test invoice detail API with real bill ID
            invoice_response = client.get(f'/api/invoices/{bill_id}')
            if invoice_response.status_code == 200:
                invoice_data = invoice_response.get_json()
                print(f"✅ Invoice detail API: Working")
                print(f"   Invoice: {invoice_data['invoice']['bill_number']}")
                print(f"   Items: {len(invoice_data['items'])}")
                print(f"   Payments: {len(invoice_data['payments'])}")
            else:
                print(f"❌ Invoice detail API failed: {invoice_response.status_code}")
        else:
            print("❌ Could not create test bill for invoice detail API test")

def test_invoice_templates():
    """Check if invoice templates exist"""
    
    print("\n🧪 Checking Invoice Templates")
    print("=" * 40)
    
    templates = [
        'invoices_professional.html',
        'retail_invoice_detail.html', 
        'invoice_demo.html'
    ]
    
    for template in templates:
        template_path = f'templates/{template}'
        if os.path.exists(template_path):
            print(f"✅ {template}: Found")
        else:
            print(f"❌ {template}: Missing")

if __name__ == "__main__":
    print("🚀 Testing Invoice Module")
    print("=" * 50)
    
    test_invoice_routes()
    test_invoice_templates()
    
    print("\n🎉 Invoice module testing complete!")