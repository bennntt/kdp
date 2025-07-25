# 🚀 KdpToolHub - Professional KDP Tools Platform

A comprehensive web application providing 8 powerful tools for Amazon Kindle Direct Publishing (KDP) authors.

## ✨ Features

### 🛠️ **8 Professional KDP Tools**
1. **Title Generator** - Create compelling book titles
2. **Subtitle Generator** - Generate perfect subtitles
3. **Description Generator** - Write persuasive book descriptions
4. **Author Name Generator** - Create professional pen names
5. **Keyword Research** - Discover high-traffic keywords
6. **Category Finder** - Find optimal Amazon categories
7. **Royalty Calculator** - Calculate KDP earnings
8. **Trademark Search** - Check for trademark conflicts

### 👥 **User Management**
- Free users: 3 daily tool uses
- Premium users: Unlimited access
- Google OAuth integration
- Email verification system
- Admin dashboard

### 💳 **Payment System**
- Stripe integration
- Monthly subscription ($15/month)
- Secure payment processing

### 🤖 **AI-Powered**
- GROQ API integration
- Llama3-8b-8192 model
- Intelligent content generation

## 🏗️ **Installation & Setup**

### **Prerequisites**
- Python 3.12+
- XAMPP (MySQL)
- Git

### **Quick Start**

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd KdpToolHub
   ```

2. **Start XAMPP MySQL**
   - Open XAMPP Control Panel
   - Start MySQL service

3. **Run the application**
   ```bash
   # Option 1: Using batch file (Windows)
   start.bat
   
   # Option 2: Using Python
   python run_venv.py
   
   # Option 3: Manual setup
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python start_app.py
   ```

4. **Access the application**
   - Main site: http://localhost:5000
   - Admin panel: http://localhost:5000/admin

### **Admin Credentials**
- **Email:** admin@kdptools.com
- **Password:** admin123
- ⚠️ **Change password after first login!**

## 🗄️ **Database Setup**

The application automatically creates the MySQL database `db_kdp` and all required tables.

### **Manual Database Setup**
```bash
python setup_db.py
```

## 🔧 **Configuration**

### **Environment Variables (.env)**
```env
# Database
DATABASE_URL=mysql+pymysql://root:@localhost/db_kdp

# Flask
SESSION_SECRET=your-secret-key
FLASK_ENV=development

# GROQ AI (for content generation)
GROQ_API_KEY=your-groq-api-key

# Google OAuth (optional)
GOOGLE_OAUTH_CLIENT_ID=your-client-id
GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret

# Stripe (for payments)
STRIPE_SECRET_KEY=sk_test_your-key
STRIPE_PUBLIC_KEY=pk_test_your-key

# Email (optional)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

## 📁 **Project Structure**

```
KdpToolHub/
├── app.py                 # Main Flask application
├── models.py              # Database models
├── forms.py               # WTForms forms
├── tools.py               # Tool routes and logic
├── admin.py               # Admin panel
├── auth.py                # Authentication
├── utils.py               # Utility functions
├── generator.py           # AI content generation
├── config_loader.py       # Dynamic configuration
├── templates/             # Jinja2 templates
│   ├── base.html
│   ├── index.html
│   ├── admin/
│   ├── auth/
│   └── tools/
├── static/                # CSS, JS, images
│   ├── css/
│   ├── js/
│   └── images/
├── venv/                  # Virtual environment
└── instance/              # Instance-specific files
```

## 🔍 **Testing & Diagnostics**

### **Run Comprehensive Check**
```bash
python check_app.py
```

This will verify:
- ✅ Database connection
- ✅ Flask app initialization
- ✅ Model imports
- ✅ Server response
- ✅ Admin login functionality
- ✅ Required files

## 🎛️ **Admin Features**

### **Dashboard**
- User statistics
- Revenue analytics
- Tool usage metrics
- System monitoring

### **User Management**
- View/edit users
- Manage subscriptions
- Send admin messages
- Tool restrictions

### **Site Configuration**
- Dynamic content editing
- Color customization
- Logo/favicon upload
- SEO settings

### **Tools Management**
- Enable/disable tools
- Usage limits
- Tool-specific settings

## 🔐 **Security Features**

- Password hashing (Werkzeug)
- Session management
- CSRF protection (Flask-WTF)
- SQL injection prevention (SQLAlchemy)
- Brute force protection
- Activity logging

## 📊 **Analytics & Tracking**

- Google Analytics integration
- Google Tag Manager support
- Facebook Pixel support
- Custom event tracking
- User activity logs

## 🚀 **Deployment**

### **Development**
```bash
python start_app.py
```

### **Production**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **Database Connection Error**
   - Ensure XAMPP MySQL is running
   - Check database credentials
   - Verify `db_kdp` database exists

2. **Import Errors**
   - Activate virtual environment
   - Install requirements: `pip install -r requirements.txt`

3. **Template Errors**
   - Check `site_config` context processor
   - Verify template files exist

4. **Port Already in Use**
   - Kill existing Python processes
   - Change port in `start_app.py`

### **Logs & Debugging**
- Check console output for errors
- Enable Flask debug mode
- Review database logs
- Check browser developer tools

## 📝 **API Integration**

### **GROQ AI Setup**
1. Get API key from https://console.groq.com
2. Add to `.env` file: `GROQ_API_KEY=your-key`
3. Restart application

### **Stripe Setup**
1. Create Stripe account
2. Get test/live API keys
3. Configure webhook endpoints
4. Update `.env` file

### **Google OAuth Setup**
1. Go to Google Cloud Console
2. Create OAuth 2.0 credentials
3. Add redirect URI: `http://localhost:5000/google_login/callback`
4. Update `.env` file

## 🤝 **Contributing**

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📄 **License**

This project is proprietary software. All rights reserved.

## 📞 **Support**

For support and questions:
- Email: admin@kdptools.com
- Admin Panel: http://localhost:5000/admin

---

**Made with ❤️ for KDP Authors**