# Billing Debug Guide 🔧

## Issue: Bills Not Working

### What I Fixed:

1. **Enhanced Error Logging** ✅
   - Added detailed console logging in frontend
   - Shows HTTP status, response body, error details
   - Better error messages for debugging

2. **Created Test Page** ✅
   - URL: `http://192.168.31.75:5000/test-billing-api`
   - Test Create Bill API directly
   - Test Get Bills API
   - See exact request/response

## How to Debug:

### Step 1: Test the API Directly
Visit: `http://192.168.31.75:5000/test-billing-api`

Click "Test Create Bill" button:
- ✅ If success → API is working
- ❌ If error → Check error message

### Step 2: Test in Billing Page
Visit: `http://192.168.31.75:5000/retail/billing`

1. Open Browser Console (F12)
2. Select a product
3. Add to bill
4. Click "Generate Bill"
5. Check console for:
   - "Sending Bill Data:" - Request data
   - "Response status:" - HTTP status code
   - "Response body:" - Server response
   - "Bill Created:" - Success data

### Step 3: Check Server Logs

Look at the terminal where server is running for:
- Request received
- Any Python errors
- Database errors
- Success messages

## Common Issues & Solutions:

### Issue 1: "HTTP 401 Unauthorized"
**Cause:** Authentication required
**Solution:** The `@require_auth` decorator should be pass-through for demo
**Check:** Line 208-216 in app.py

### Issue 2: "HTTP 500 Internal Server Error"
**Cause:** Backend Python error
**Solution:** Check server terminal for error traceback
**Common causes:**
- Database connection error
- Missing fields in request
- SQL syntax error

### Issue 3: "Network Error" or "Failed to fetch"
**Cause:** Server not running or wrong URL
**Solution:** 
- Check server is running on port 5000
- Check URL is correct
- Check CORS settings

### Issue 4: "Product ID not found"
**Cause:** Product IDs in dropdown don't match database
**Solution:** Check product IDs in HTML match database

## API Endpoint Details:

### POST /api/bills

**Request:**
```json
{
  "customer_id": null,
  "business_type": "retail",
  "payment_method": "cash",
  "items": [
    {
      "product_id": "prod-1",
      "product_name": "Rice (1kg)",
      "quantity": 2,
      "unit_price": 80,
      "total_price": 160
    }
  ],
  "subtotal": 160,
  "tax_amount": 28.8,
  "total_amount": 188.8
}
```

**Success Response (201):**
```json
{
  "message": "Bill created successfully",
  "bill_id": "abc123...",
  "bill_number": "BILL-20251206-abc12345",
  "hourly_update": {
    "hour": "21:00",
    "transactions": 1,
    "sales": 188.8,
    "avg_order_value": 188.8
  }
}
```

**Error Response (500):**
```json
{
  "error": "Error message here"
}
```

## Testing Checklist:

- [ ] Server is running (check terminal)
- [ ] Visit test page: `/test-billing-api`
- [ ] Click "Test Create Bill"
- [ ] Check if API works
- [ ] If API works, test billing page
- [ ] Open browser console (F12)
- [ ] Add product to bill
- [ ] Click "Generate Bill"
- [ ] Check console logs
- [ ] Check server terminal
- [ ] Check for error messages

## Quick Test Commands:

### Test with curl:
```bash
curl -X POST http://localhost:5000/api/bills \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": null,
    "business_type": "retail",
    "payment_method": "cash",
    "items": [{
      "product_id": "prod-1",
      "product_name": "Rice (1kg)",
      "quantity": 2,
      "unit_price": 80,
      "total_price": 160
    }],
    "subtotal": 160,
    "tax_amount": 28.8,
    "total_amount": 188.8
  }'
```

### Test with PowerShell:
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/bills" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"customer_id":null,"business_type":"retail","payment_method":"cash","items":[{"product_id":"prod-1","product_name":"Rice (1kg)","quantity":2,"unit_price":80,"total_price":160}],"subtotal":160,"tax_amount":28.8,"total_amount":188.8}'
```

## Next Steps:

1. Visit test page and click "Test Create Bill"
2. If it works → Problem is in billing page frontend
3. If it fails → Problem is in backend API
4. Check console and server logs for exact error
5. Share the error message for further help

## Test URLs:

- Test API: `http://192.168.31.75:5000/test-billing-api`
- Billing Page: `http://192.168.31.75:5000/retail/billing`
- Mobile Diagnostic: `http://192.168.31.75:5000/mobile-diagnostic`
