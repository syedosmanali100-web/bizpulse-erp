# Billing Software API Documentation

## Complete Backend System Ready! 🚀

### Authentication APIs
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login with JWT tokens
- `GET /login` - Login page
- `GET /register` - Registration page

### Dashboard APIs
- `GET /api/dashboard/stats?type=kirana|hotel` - Real-time dashboard statistics
- `GET /api/dashboard/activity?type=kirana|hotel` - Recent activity feed
- `GET /api/notifications` - System notifications and alerts

### Kirana Store APIs
- `GET /api/kirana/sales` - Sales analytics (today/week/month)
- `GET /api/kirana/inventory` - Inventory management data
- `POST /api/kirana/billing/new` - Create new bill with automatic stock updates

### Hotel Management APIs
- `GET /api/hotel/reservations` - Reservation management
- `GET /api/hotel/rooms/status` - Real-time room status grid
- `POST /api/hotel/checkin` - Guest check-in process
- `POST /api/hotel/checkout` - Guest check-out with billing
- `POST /api/hotel/services/bill` - Add services to guest bills

### Product Management APIs
- `GET /api/products` - Get all products
- `POST /api/products` - Add new product
- `PUT /api/products/<id>` - Update product
- `DELETE /api/products/<id>` - Delete product

### Customer Management APIs
- `GET /api/customers` - Get all customers
- `POST /api/customers` - Add new customer
- Customer credit management with balance tracking

### Hotel Guest APIs
- `GET /api/hotel/guests` - Guest management
- `POST /api/hotel/guests` - Add new guest
- `POST /api/hotel/guests/<id>/checkin` - Check-in process

### Hotel Services APIs
- `GET /api/hotel/services` - Service catalog
- `POST /api/hotel/services` - Add new service

### Billing & Invoicing APIs
- `GET /api/bills` - Get all bills
- `POST /api/bills` - Create new bill
- Payment processing with multiple methods

### Reports & Analytics APIs
- `GET /api/reports/sales` - Comprehensive sales reports
- Date range filtering and analytics

### Search & Utility APIs
- `GET /api/search?q=<query>&type=<type>` - Global search
- `GET /api/settings/business` - Business settings
- `PUT /api/settings/business` - Update business settings

## Features Implemented

### 🛒 Kirana Store Features
✅ **Real-time Dashboard** - Live stats, revenue, orders, inventory alerts
✅ **Quick Billing System** - Barcode scanning, multiple payment methods
✅ **Inventory Management** - Stock tracking, low stock alerts, automatic updates
✅ **Customer Management** - Credit sales, balance tracking, payment history
✅ **Sales Analytics** - Daily/weekly/monthly reports with trends

### 🏨 Hotel Management Features
✅ **Hotel Dashboard** - Occupancy rates, revenue, guest statistics
✅ **Room Management** - Visual room status grid (occupied/available/maintenance)
✅ **Guest Management** - Check-in/out process, guest profiles
✅ **Reservation System** - Booking management, room assignments
✅ **Service Billing** - Add hotel services to guest bills
✅ **Revenue Tracking** - Real-time revenue and occupancy analytics

### 🔐 Security & Authentication
✅ **JWT Authentication** - Secure token-based authentication
✅ **User Management** - Registration, login, profile management
✅ **Session Management** - Automatic token validation
✅ **Business Settings** - User-specific business configuration

### 📊 Real-time Features
✅ **Live Dashboard Updates** - Auto-refresh every 30 seconds
✅ **Notification System** - Real-time alerts and badges
✅ **Activity Feed** - Live transaction and activity tracking
✅ **Search Functionality** - Global search across all modules

### 💾 Database Features
✅ **SQLite Database** - Complete schema with relationships
✅ **Sample Data** - Pre-loaded demo data for testing
✅ **Data Integrity** - Foreign key constraints and validation
✅ **Automatic Backups** - Built-in data protection

## Technology Stack
- **Backend**: Python Flask with SQLite
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Authentication**: JWT tokens with secure hashing
- **Database**: SQLite with comprehensive schema
- **API**: RESTful APIs with JSON responses
- **UI**: Responsive design with modern CSS

## Demo Credentials
- **Email**: admin@demo.com
- **Password**: demo123

## Installation & Setup
```bash
# Install dependencies
pip install flask flask-cors

# Run server
python app.py

# Access application
http://localhost:5000
```

## API Response Format
```json
{
  "message": "Success message",
  "data": {...},
  "status": "success|error"
}
```

## Error Handling
- Comprehensive error messages
- HTTP status codes
- Validation errors
- Database error handling
- Authentication failures

## Next Steps (Optional Enhancements)
- [ ] Advanced reporting with charts
- [ ] Email notifications
- [ ] SMS integration
- [ ] Barcode scanner integration
- [ ] Receipt printer support
- [ ] Multi-location support
- [ ] Advanced user roles
- [ ] Data export/import
- [ ] Mobile app API
- [ ] Cloud deployment

## Complete System Ready! 🎉
The billing software now has a complete backend with all dashboard features working with real data, authentication, and comprehensive retail management capabilities for both retail stores and hotels.