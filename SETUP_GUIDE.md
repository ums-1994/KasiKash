# KasiKash Application Setup Guide

## Overview
KasiKash is a Flask-based financial management application for stokvels (community savings groups). It includes user authentication, stokvel management, contributions tracking, and an AI chatbot.

## Prerequisites

### 1. Python Environment
- **Python 3.8 or higher** (recommended: Python 3.11)
- **pip** (Python package installer)

### 2. Database
- **PostgreSQL** (recommended) or **SQLite** (fallback)
- For PostgreSQL: Install PostgreSQL server and create a database

### 3. External Services (Optional but Recommended)
- **Firebase** account for authentication
- **SendGrid** account for email notifications
- **OpenRouter** account for AI chatbot features
- **Backblaze B2** for file storage (optional)

## Installation Steps

### Step 1: Clone and Navigate to Project
```bash
cd KasiKash
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
1. Copy the environment template:
```bash
cp env_template.txt .env
```

2. Edit `.env` file with your configuration:
```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kasikash_db
DB_USER=kasikash_user
DB_PASSWORD=kasikash_password

# Firebase Configuration (Required)
FIREBASE_SERVICE_ACCOUNT_KEY_PATH=path/to/your/firebase-service-account.json
FIREBASE_PROJECT_ID=your-firebase-project-id

# Email Configuration
MAIL_SENDER_EMAIL=your-email@gmail.com
MAIL_SENDER_NAME=KasiKash App
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# SendGrid Configuration (Optional)
SENDGRID_API_KEY=your-sendgrid-api-key

# OpenRouter Configuration (Optional - for chatbot)
OPENROUTER_API_KEY=your-openrouter-api-key

# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production
FLASK_ENV=development
```

### Step 5: Database Setup

#### Option A: PostgreSQL (Recommended)
1. Install PostgreSQL
2. Create database and user:
```sql
CREATE DATABASE kasikash_db;
CREATE USER kasikash_user WITH PASSWORD 'kasikash_password';
GRANT ALL PRIVILEGES ON DATABASE kasikash_db TO kasikash_user;
```

3. Initialize database:
```bash
python init_db.py
```

#### Option B: SQLite (Simpler Setup)
1. Use SQLite for development:
```bash
python init_sqlite_db.py
```

### Step 6: Firebase Setup (Required)
1. Create a Firebase project at https://console.firebase.google.com/
2. Enable Authentication (Email/Password)
3. Download service account key JSON file
4. Place it in your project directory
5. Update `FIREBASE_SERVICE_ACCOUNT_KEY_PATH` in `.env`

### Step 7: Create Required Directories
```bash
mkdir -p static/profile_pics
mkdir -p static/kyc_docs
mkdir -p flask_session_data
```

## Running the Application

### Development Mode
```bash
python main.py
```

### Production Mode
```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

The application will be available at: `http://localhost:5000`

## Key Features

### 1. User Management
- Registration and login via Firebase
- Email verification
- Profile management
- KYC document upload

### 2. Stokvel Management
- Create and join stokvels
- Manage members
- Track contributions
- Generate statements

### 3. Financial Features
- Contribution tracking
- Payout requests
- Savings goals
- Payment methods

### 4. Admin Features
- User management
- Loan approvals
- KYC approvals
- System notifications

### 5. AI Chatbot
- Financial advice
- Transaction queries
- General assistance

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Check database credentials in `.env`
   - Ensure PostgreSQL is running
   - Verify database exists

2. **Firebase Authentication Error**
   - Verify service account key path
   - Check Firebase project configuration
   - Ensure Authentication is enabled

3. **Email Not Working**
   - Check SMTP credentials
   - Verify SendGrid API key (if using)
   - Test with Gmail app password

4. **Import Errors**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt`
   - Check Python version compatibility

### Debug Mode
Enable debug mode by setting in `.env`:
```env
FLASK_ENV=development
FLASK_DEBUG=1
```

## File Structure
```
KasiKash/
├── main.py                 # Main application file
├── requirements.txt        # Python dependencies
├── .env                   # Environment configuration
├── static/                # Static files (CSS, JS, images)
├── templates/             # HTML templates
├── admin/                 # Admin blueprint
├── migrations/            # Database migrations
├── support.py             # Database utilities
└── utils.py               # Utility functions
```

## Security Notes
- Change default secret keys in production
- Use HTTPS in production
- Secure database credentials
- Regularly update dependencies
- Enable Firebase security rules

## Support
For issues and questions:
1. Check the troubleshooting section
2. Review error logs
3. Verify configuration settings
4. Test with minimal setup first 