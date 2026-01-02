# BizPulse Mobile ERP - File Structure Map

## Project Structure (After Cleanup)

```
/
├── frontend/                    # Frontend application files
│   ├── screens/                # Mobile/desktop screen components
│   │   ├── dashboard/          # Dashboard screens
│   │   ├── billing/            # Billing interface screens
│   │   ├── inventory/          # Inventory management screens
│   │   ├── sales/              # Sales reporting screens
│   │   └── auth/               # Authentication screens
│   ├── components/             # Reusable UI components
│   │   ├── forms/              # Form components
│   │   ├── tables/             # Data table components
│   │   └── modals/             # Modal dialogs
│   ├── services/               # Frontend API services
│   │   ├── api.js              # API client configuration
│   │   ├── billing.js          # Billing API calls
│   │   ├── products.js         # Product API calls
│   │   └── auth.js             # Authentication API calls
│   ├── assets/                 # Static assets
│   │   ├── css/                # Stylesheets
│   │   ├── js/                 # JavaScript files
│   │   ├── images/             # Image assets
│   │   └── icons/              # Icon files
│   └── utils/                  # Frontend utilities
│       ├── formatters.js       # Data formatting utilities
│       ├── validators.js       # Form validation
│       └── constants.js        # Frontend constants
│
├── backend/                    # Backend application files
│   ├── routes/                 # API route definitions
│   │   ├── __init__.py         # Blueprint registration
│   │   ├── auth_routes.py      # Authentication endpoints
│   │   ├── billing_routes.py   # Billing API endpoints
│   │   ├── product_routes.py   # Product management endpoints
│   │   ├── sales_routes.py     # Sales reporting endpoints
│   │   ├── inventory_routes.py # Inventory management endpoints
│   │   └── invoice_routes.py   # Invoice generation endpoints
│   ├── controllers/            # Request/response handling
│   │   ├── __init__.py
│   │   ├── auth_controller.py  # Authentication logic
│   │   ├── billing_controller.py # Billing request handling
│   │   └── base_controller.py  # Base controller class
│   ├── services/               # Business logic layer
│   │   ├── __init__.py
│   │   ├── billing_service.py  # Billing business logic
│   │   ├── product_service.py  # Product management logic
│   │   ├── sales_service.py    # Sales analytics logic
│   │   ├── inventory_service.py # Inventory management logic
│   │   ├── invoice_service.py  # Invoice generation logic
│   │   ├── pdf_generator.py    # PDF generation service
│   │   └── whatsapp_service.py # WhatsApp integration
│   ├── models/                 # Data models and database
│   │   ├── __init__.py
│   │   ├── database.py         # Database connection and setup
│   │   ├── bill.py             # Bill data model
│   │   ├── product.py          # Product data model
│   │   ├── customer.py         # Customer data model
│   │   └── user.py             # User data model
│   ├── middlewares/            # Request middlewares
│   │   ├── __init__.py
│   │   ├── auth_middleware.py  # Authentication middleware
│   │   ├── cors_middleware.py  # CORS handling
│   │   └── error_middleware.py # Error handling
│   └── config/                 # Configuration files
│       ├── __init__.py
│       ├── database_config.py  # Database configuration
│       ├── app_config.py       # Application configuration
│       └── api_config.py       # API configuration
│
├── shared/                     # Shared utilities and constants
│   ├── constants/              # Application constants
│   │   ├── __init__.py
│   │   ├── api_constants.py    # API-related constants
│   │   ├── business_constants.py # Business logic constants
│   │   └── ui_constants.py     # UI-related constants
│   └── helpers/                # Shared helper functions
│       ├── __init__.py
│       ├── date_helpers.py     # Date/time utilities
│       ├── validation_helpers.py # Validation utilities
│       └── format_helpers.py   # Data formatting utilities
│
├── docs/                       # Documentation
│   ├── FILE_MAP.md             # This file
│   ├── API_DOCUMENTATION.md    # API endpoint documentation
│   ├── DEPLOYMENT_GUIDE.md     # Deployment instructions
│   └── CODEBASE_AUDIT_REPORT.md # Audit findings
│
├── translations/               # Internationalization
│   ├── en.json                 # English translations
│   └── hi.json                 # Hindi translations
│
├── app.py                      # Main Flask application entry point
├── requirements.txt            # Python dependencies
├── billing.db                  # SQLite database file
└── README.md                   # Project documentation
```

## Entry Points

### Backend Entry Points
- **`app.py`** - Main Flask application server
- **`backend/routes/__init__.py`** - API blueprint registration
- **`backend/services/`** - Business logic services

### Frontend Entry Points
- **`frontend/screens/dashboard/`** - Main dashboard interface
- **`frontend/screens/auth/login.html`** - User authentication
- **`frontend/screens/billing/billing.html`** - Billing interface

### Mobile Entry Points
- **`frontend/screens/mobile/dashboard.html`** - Mobile dashboard
- **`frontend/services/api.js`** - Mobile API client

## Data Flow Architecture

### Billing Process Flow
```
Mobile App → API Routes → Controllers → Services → Models → Database
     ↓
frontend/screens/billing/ → backend/routes/billing_routes.py → backend/services/billing_service.py → backend/models/bill.py → billing.db
```

### Inventory Management Flow
```
Dashboard → Inventory API → Inventory Service → Product Model → Database
     ↓
frontend/screens/inventory/ → backend/routes/inventory_routes.py → backend/services/inventory_service.py → backend/models/product.py → billing.db
```

### Sales Reporting Flow
```
Sales Screen → Sales API → Sales Service → Sales Model → Database
     ↓
frontend/screens/sales/ → backend/routes/sales_routes.py → backend/services/sales_service.py → backend/models/ → billing.db
```

## Key Responsibilities

### Frontend Layer
- **Screens**: User interface components and layouts
- **Components**: Reusable UI elements (forms, tables, modals)
- **Services**: API communication and data fetching
- **Assets**: Static files (CSS, JS, images)
- **Utils**: Client-side utilities and helpers

### Backend Layer
- **Routes**: HTTP endpoint definitions and routing
- **Controllers**: Request/response handling and validation
- **Services**: Business logic and data processing
- **Models**: Data access layer and database operations
- **Middlewares**: Cross-cutting concerns (auth, CORS, errors)
- **Config**: Application configuration and settings

### Shared Layer
- **Constants**: Application-wide constants and enums
- **Helpers**: Utility functions used by both frontend and backend

## Database Schema
- **Products**: Product catalog and inventory
- **Bills**: Billing transactions and line items
- **Customers**: Customer information and credit management
- **Sales**: Sales analytics and reporting data
- **Users**: Authentication and user management

## API Architecture
- **RESTful Design**: Standard HTTP methods and status codes
- **JSON Communication**: All API requests/responses in JSON
- **Authentication**: Session-based authentication with middleware
- **Error Handling**: Consistent error response format
- **Validation**: Input validation at controller level

## Security Considerations
- **Authentication**: Required for all protected endpoints
- **Authorization**: Role-based access control
- **Input Validation**: Server-side validation for all inputs
- **SQL Injection Prevention**: Parameterized queries
- **CORS**: Configured for mobile app access

## Performance Optimizations
- **Database Indexing**: Optimized queries for frequent operations
- **Caching**: Static asset caching and API response caching
- **Pagination**: Large dataset pagination for better performance
- **Lazy Loading**: On-demand loading of heavy components