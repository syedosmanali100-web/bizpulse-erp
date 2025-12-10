"""
Test Script for WhatsApp Daily Reports System
Run this to verify everything is working correctly
"""

import sys
import os
from datetime import date, datetime
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        from services.report_service import ReportService
        from services.whatsapp_service import WhatsAppService
        from services.pdf_generator import PDFGenerator
        print("✅ All service modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        return False

def test_database_connection():
    """Test database connection and tables"""
    print("\n🔍 Testing database connection...")
    
    try:
        import sqlite3
        conn = sqlite3.connect('billing.db')
        
        # Check if required tables exist
        tables = ['companies', 'invoices', 'whatsapp_reports_log']
        for table in tables:
            cursor = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if cursor.fetchone():
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' missing")
                return False
        
        # Check if default company exists
        cursor = conn.execute("SELECT * FROM companies WHERE id = 'default_company'")
        company = cursor.fetchone()
        if company:
            print("✅ Default company found")
        else:
            print("❌ Default company not found")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False

def test_pdf_generation():
    """Test PDF generation"""
    print("\n🔍 Testing PDF generation...")
    
    try:
        from services.pdf_generator import PDFGenerator
        from services.report_service import ReportService
        
        # Initialize services
        pdf_generator = PDFGenerator()
        report_service = ReportService()
        
        # Get default company data
        companies = report_service.get_companies_for_reports()
        if not companies:
            print("❌ No companies found for testing")
            return False
        
        company_data = companies[0]
        
        # Sample report data
        report_data = {
            'total_sales': 15750.50,
            'total_profit': 3150.10,
            'total_invoices': 25
        }
        
        # Generate PDF
        pdf_path = pdf_generator.generate_daily_sales_report(
            company_data, 
            report_data, 
            date.today()
        )
        
        if os.path.exists(pdf_path):
            print(f"✅ PDF generated successfully: {pdf_path}")
            
            # Clean up
            pdf_generator.cleanup_temp_files(pdf_path)
            print("✅ PDF cleanup successful")
            return True
        else:
            print("❌ PDF file not created")
            return False
            
    except Exception as e:
        print(f"❌ PDF generation error: {str(e)}")
        return False

def test_whatsapp_config():
    """Test Free WhatsApp service"""
    print("\n🔍 Testing Free WhatsApp service...")
    
    try:
        from services.whatsapp_service import WhatsAppService
        
        whatsapp_service = WhatsAppService()
        validation = whatsapp_service.validate_configuration()
        
        if validation['valid']:
            print("✅ Free WhatsApp service is ready!")
            print(f"   Service: {validation.get('service', 'N/A')}")
            print(f"   Method: {validation.get('method', 'N/A')}")
            print(f"   Status: {validation.get('status', 'N/A')}")
            print(f"   Support: {validation.get('support_phone', 'N/A')}")
            return True
        else:
            print(f"❌ WhatsApp service not ready: {validation['error']}")
            print(f"   Details: {validation.get('details', 'N/A')}")
            return False
            
    except Exception as e:
        print(f"❌ WhatsApp service error: {str(e)}")
        return False

def test_report_service():
    """Test report service functionality"""
    print("\n🔍 Testing report service...")
    
    try:
        from services.report_service import ReportService
        
        report_service = ReportService()
        
        # Test getting companies
        companies = report_service.get_companies_for_reports()
        print(f"✅ Found {len(companies)} companies configured for reports")
        
        if companies:
            company = companies[0]
            print(f"   Company: {company['business_name']}")
            print(f"   WhatsApp: {company.get('whatsapp_number', 'Not set')}")
            
            # Test getting sales data
            sales_data = report_service.get_daily_sales_data(company['id'], date.today())
            print(f"✅ Sales data retrieved:")
            print(f"   Total Sales: ₹{sales_data['total_sales']:,.2f}")
            print(f"   Total Profit: ₹{sales_data['total_profit']:,.2f}")
            print(f"   Total Invoices: {sales_data['total_invoices']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Report service error: {str(e)}")
        return False

def test_full_workflow():
    """Test complete workflow (PDF generation only, no WhatsApp sending)"""
    print("\n🔍 Testing complete workflow (PDF only)...")
    
    try:
        from services.report_service import ReportService
        
        report_service = ReportService()
        
        # Generate report for default company
        result = report_service.generate_daily_report('default_company', date.today())
        
        if result['success']:
            print("✅ Complete workflow test successful")
            print(f"   Company: {result['company_data']['business_name']}")
            print(f"   Sales: ₹{result['report_data']['total_sales']:,.2f}")
            print(f"   Profit: ₹{result['report_data']['total_profit']:,.2f}")
            print(f"   PDF: {result['pdf_path']}")
            
            # Clean up
            from services.pdf_generator import PDFGenerator
            pdf_generator = PDFGenerator()
            pdf_generator.cleanup_temp_files(result['pdf_path'])
            
            return True
        else:
            print(f"❌ Workflow test failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Workflow test error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 BizPulse WhatsApp Reports System Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Database Test", test_database_connection),
        ("PDF Generation Test", test_pdf_generation),
        ("WhatsApp Config Test", test_whatsapp_config),
        ("Report Service Test", test_report_service),
        ("Full Workflow Test", test_full_workflow)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your WhatsApp Reports system is ready!")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        
        if passed >= 4:  # If most tests pass
            print("\n💡 TIPS:")
            print("   - WhatsApp config test may fail if API credentials not set")
            print("   - This is normal for initial setup")
            print("   - Set WHATSAPP_PHONE_ID and WHATSAPP_ACCESS_TOKEN in .env file")
    
    print("\n📞 Support: +91 7093635305 | bizpulse.erp@gmail.com")

if __name__ == "__main__":
    main()