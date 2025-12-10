# 🚀 BizPulse ERP - Complete Business Management System

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## 🎯 Overview

**BizPulse ERP** is a complete business management system built with Python Flask. It includes everything you need to run a modern business - from inventory management to client accounts and automated WhatsApp reports.

## ✨ Features

### 🏪 **Core ERP System**
- **Dashboard** - Real-time business analytics
- **Product Management** - Inventory tracking with low stock alerts
- **Customer Management** - Complete customer database
- **Billing System** - Professional invoicing with GST
- **Sales Reports** - Detailed analytics and insights
- **Multi-Business Support** - Handle multiple companies

### 👥 **Client Management**
- **Auto-Generated Accounts** - Create client logins automatically
- **Username/Password System** - Secure client authentication
- **Client Dashboard Access** - Full ERP access for clients
- **Account Management** - Activate/deactivate, reset passwords

### 📱 **WhatsApp Reports (FREE)**
- **Daily Sales Reports** - Automated PDF generation
- **Professional Templates** - Beautiful branded reports
- **Free WhatsApp Integration** - No API keys required
- **Scheduled Delivery** - Automatic daily sending

### 📱 **Mobile ERP App**
- **Responsive Design** - Works on all devices
- **Touch-Friendly Interface** - Optimized for mobile
- **Full Feature Access** - All desktop features available
- **PWA Support** - Install as mobile app

## 🌐 Live Demo

- **Website**: [Your Render URL]
- **Mobile App**: [Your Render URL]/mobile-simple
- **Admin Login**: bizpulse.erp@gmail.com / demo123

## 🚀 Quick Deploy to Render.com

### Method 1: One-Click Deploy
1. Click the "Deploy to Render" button above
2. Connect your GitHub account
3. Your app will be live in 2-3 minutes!

### Method 2: Manual Deploy
1. Fork this repository
2. Create account on [Render.com](https://render.com)
3. Connect your GitHub repo
4. Deploy automatically!

## 💻 Local Development

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/BizPulse_ERP.git
cd BizPulse_ERP

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### Access Points
- **Main Website**: http://localhost:5000
- **Mobile App**: http://localhost:5000/mobile-simple
- **Client Management**: http://localhost:5000/client-management
- **WhatsApp Reports**: http://localhost:5000/whatsapp-sender

## 📊 System Architecture

```
BizPulse ERP/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── Procfile              # Render.com deployment config
├── render.yaml           # Render.com service config
├── billing.db            # SQLite database
├── templates/            # HTML templates
│   ├── index.html        # Homepage
│   ├── login.html        # Login page
│   ├── retail_dashboard.html  # Main dashboard
│   ├── client_management.html # Client management
│   ├── whatsapp_sender.html   # WhatsApp reports
│   └── mobile_simple_working.html # Mobile app
├── static/               # CSS, JS, Images
├── services/             # Backend services
│   ├── pdf_generator.py  # PDF report generation
│   ├── whatsapp_service.py # WhatsApp integration
│   └── report_service.py # Report orchestration
└── translations/         # Multi-language support
```

## 🔧 Configuration

### Environment Variables (Optional)
```bash
FLASK_ENV=production
WHATSAPP_PHONE_ID=your_phone_id    # Optional for premium WhatsApp
WHATSAPP_ACCESS_TOKEN=your_token   # Optional for premium WhatsApp
```

### Database
- **Type**: SQLite (included)
- **File**: billing.db
- **Auto-initialization**: Yes
- **Sample Data**: Included

## 📱 Mobile App Features

### 🏠 Dashboard
- Sales analytics
- Quick stats
- Recent transactions

### 📦 Products
- Add/edit products
- Stock management
- Category organization

### 🧾 Billing
- Create invoices
- GST calculations
- Payment tracking

### 👥 Customers
- Customer database
- Contact management
- Purchase history

### 📊 Reports
- Sales reports
- Profit analysis
- Export options

## 👥 Client Management System

### Create Client Accounts
1. Go to Client Management
2. Enter company details
3. System generates username/password
4. Share credentials with client

### Client Login Process
1. Client visits login page
2. Clicks "Client Login" tab
3. Enters username/password
4. Gets full ERP access

## 📱 WhatsApp Reports

### Features
- **Daily Reports**: Automated generation
- **Professional PDFs**: Branded templates
- **Free Service**: No API keys needed
- **Multiple Formats**: PDF + WhatsApp message

### Sample Report
```
📊 DAILY SALES REPORT

🏪 ABC Store
📅 Date: 10/12/2024

💰 Total Sales: ₹15,750.50
📈 Total Profit: ₹3,150.10
🧾 Total Invoices: 25

Generated by BizPulse ERP
📞 Support: 7093635305
```

## 🔐 Security Features

- **Password Hashing**: SHA-256 encryption
- **Session Management**: Secure user sessions
- **Input Validation**: SQL injection prevention
- **CORS Protection**: Cross-origin security
- **Client Isolation**: Secure multi-tenant system

## 📈 Performance

- **Database**: Optimized SQLite queries
- **Caching**: Static file caching
- **Compression**: Gzip compression
- **CDN Ready**: Static asset optimization
- **Mobile Optimized**: Fast mobile loading

## 🛠️ Tech Stack

### Backend
- **Python 3.8+**
- **Flask 2.3.3** - Web framework
- **SQLite** - Database
- **WeasyPrint** - PDF generation
- **Jinja2** - Template engine

### Frontend
- **HTML5/CSS3** - Modern web standards
- **JavaScript ES6** - Interactive features
- **Responsive Design** - Mobile-first approach
- **PWA Support** - Progressive web app

### Services
- **WhatsApp Integration** - Free messaging service
- **PDF Generation** - Professional reports
- **Email Support** - Contact system
- **Multi-language** - i18n support

## 📞 Support

- **Phone**: 7093635305
- **Email**: bizpulse.erp@gmail.com
- **WhatsApp**: 7093635305

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🎉 Acknowledgments

- Built with ❤️ for small businesses
- Inspired by modern ERP systems
- Designed for ease of use
- Free and open source

---

**⭐ Star this repository if you find it helpful!**

**🚀 Deploy your own BizPulse ERP system today!**