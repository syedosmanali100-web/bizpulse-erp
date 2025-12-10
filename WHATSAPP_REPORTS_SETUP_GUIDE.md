# WhatsApp Daily Reports Setup Guide

## 🎯 Overview

This system automatically generates daily sales & profit reports as PDF files and sends them to clients via WhatsApp Cloud API. Perfect for retail ERP systems like Vyapar.

## 📋 Features

- ✅ **Automated Daily Reports** - Runs at 11:55 PM daily
- ✅ **Professional PDF Generation** - Beautiful, branded reports
- ✅ **WhatsApp Cloud API Integration** - Direct delivery to clients
- ✅ **Multi-Company Support** - Handle multiple businesses
- ✅ **Comprehensive Logging** - Track all sent reports
- ✅ **Manual Triggers** - Send reports on-demand
- ✅ **Error Handling** - Robust error management

## 🚀 Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. WhatsApp Business API Setup

1. **Create Meta Business Account**
   - Go to [Meta Business Manager](https://business.facebook.com/)
   - Create a business account

2. **Set up WhatsApp Business API**
   - Go to [Meta Developers](https://developers.facebook.com/)
   - Create a new app → Business → WhatsApp
   - Get your `Phone Number ID` and `Access Token`

3. **Configure Environment Variables**
   ```bash
   # Copy example file
   cp .env.example .env
   
   # Edit .env file
   WHATSAPP_PHONE_ID=your_phone_number_id_here
   WHATSAPP_ACCESS_TOKEN=your_access_token_here
   ```

### 3. Database Setup

The system automatically creates required tables:
- `companies` - Business information
- `invoices` - Sales data with profit tracking
- `whatsapp_reports_log` - Report delivery logs

### 4. Start the System

```bash
# Start main server
python app.py

# Start scheduler (in separate terminal)
python scheduler.py
```

## 📊 API Endpoints

### Manual Report Generation

```bash
# Generate report for specific company
POST /api/whatsapp-reports/generate
{
  "company_id": "default_company",
  "report_date": "2024-12-10"
}

# Send reports to all companies
POST /api/whatsapp-reports/send-all
{
  "report_date": "2024-12-10"
}

# Test report generation (PDF only, no sending)
POST /api/whatsapp-reports/test
{
  "company_id": "default_company",
  "report_date": "2024-12-10"
}
```

### Report Logs & Management

```bash
# Get report logs
GET /api/whatsapp-reports/logs?company_id=default_company&days=7

# Get companies configured for reports
GET /api/whatsapp-reports/companies

# Validate WhatsApp configuration
GET /api/whatsapp-reports/config/validate
```

### Company Management

```bash
# Get all companies
GET /api/companies

# Create new company
POST /api/companies
{
  "business_name": "My Store",
  "phone_number": "+917093635305",
  "whatsapp_number": "+917093635305",
  "email": "store@example.com",
  "send_daily_report": true,
  "report_time": "23:55:00"
}

# Update company
PUT /api/companies/{company_id}
```

## 📱 Report Content

Each PDF report includes:

### 📈 Summary Cards
- **Total Sales** - Daily revenue with invoice count
- **Total Profit** - Net profit with margin percentage
- **Performance Status** - Business health indicator

### 📊 Detailed Metrics
- Total invoices count
- Average invoice value
- Total revenue & costs
- Profit margin analysis

### 💡 Business Insights
- Performance indicators
- Automated recommendations
- Trend analysis

### 🏪 Company Branding
- Company name and contact info
- Professional layout
- BizPulse ERP branding

## 🔧 Configuration Options

### Company Settings

```sql
-- Enable/disable reports for a company
UPDATE companies SET send_daily_report = 1 WHERE id = 'company_id';

-- Change report time
UPDATE companies SET report_time = '23:55:00' WHERE id = 'company_id';

-- Update WhatsApp number
UPDATE companies SET whatsapp_number = '+917093635305' WHERE id = 'company_id';
```

### Scheduler Configuration

Edit `scheduler.py` to change timing:

```python
# Daily at 11:55 PM
schedule.every().day.at("23:55").do(run_daily_reports)

# Or multiple times per day
schedule.every().day.at("12:00").do(run_daily_reports)  # Noon
schedule.every().day.at("18:00").do(run_daily_reports)  # 6 PM
schedule.every().day.at("23:55").do(run_daily_reports)  # 11:55 PM
```

## 🔍 Testing & Debugging

### 1. Test WhatsApp Configuration

```bash
curl -X GET "http://localhost:5000/api/whatsapp-reports/config/validate"
```

### 2. Test Report Generation

```bash
curl -X POST "http://localhost:5000/api/whatsapp-reports/test" \
  -H "Content-Type: application/json" \
  -d '{"company_id": "default_company"}'
```

### 3. Manual Report Sending

```bash
curl -X POST "http://localhost:5000/api/whatsapp-reports/generate" \
  -H "Content-Type: application/json" \
  -d '{"company_id": "default_company"}'
```

### 4. Check Logs

```bash
# View scheduler logs
tail -f scheduler.log

# Check report logs via API
curl -X GET "http://localhost:5000/api/whatsapp-reports/logs"
```

## 🚨 Troubleshooting

### Common Issues

1. **WhatsApp API Errors**
   ```
   Error: Invalid access token
   Solution: Check WHATSAPP_ACCESS_TOKEN in .env file
   ```

2. **PDF Generation Fails**
   ```
   Error: WeasyPrint installation issue
   Solution: pip install WeasyPrint --upgrade
   ```

3. **No Sales Data**
   ```
   Error: Report shows zero sales
   Solution: Check invoices table has data for the date
   ```

4. **Phone Number Format**
   ```
   Error: Invalid WhatsApp number
   Solution: Use format +917093635305 (with country code)
   ```

### Debug Mode

Enable detailed logging:

```python
# In app.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📅 Production Deployment

### 1. Windows Task Scheduler

Create a batch file `start_scheduler.bat`:

```batch
@echo off
cd /d "C:\path\to\your\project"
python scheduler.py
```

Schedule it to run at startup.

### 2. Linux Cron Job

```bash
# Edit crontab
crontab -e

# Add this line to run scheduler at startup
@reboot cd /path/to/project && python scheduler.py

# Or run the job directly at 11:55 PM
55 23 * * * cd /path/to/project && python -c "from app import run_daily_reports_job; run_daily_reports_job()"
```

### 3. Environment Variables

Set production environment variables:

```bash
# Linux/Mac
export WHATSAPP_PHONE_ID="your_phone_id"
export WHATSAPP_ACCESS_TOKEN="your_token"

# Windows
set WHATSAPP_PHONE_ID=your_phone_id
set WHATSAPP_ACCESS_TOKEN=your_token
```

## 📞 Support

- **Phone**: +91 7093635305
- **Email**: bizpulse.erp@gmail.com
- **WhatsApp**: +91 7093635305

## 🔐 Security Notes

- Keep your WhatsApp Access Token secure
- Use HTTPS in production
- Regularly rotate API tokens
- Monitor API usage limits
- Backup report logs regularly

## 📈 Monitoring

Track system health:

1. **Report Success Rate** - Monitor via logs API
2. **API Rate Limits** - WhatsApp has daily limits
3. **PDF Generation Time** - Monitor performance
4. **Database Growth** - Clean old logs periodically

---

**🎉 Your WhatsApp Daily Reports system is now ready!**

The system will automatically send beautiful PDF reports to your clients every day at 11:55 PM, helping you maintain professional communication and keep clients informed about their business performance.