# 🎯 FinSight - AI Financial Intelligence Platform

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation Guide](#installation-guide)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Features Breakdown](#features-breakdown)
- [Database Schema](#database-schema)
- [Troubleshooting](#troubleshooting)

## 🌟 Overview

FinSight is a comprehensive, production-ready expense management and financial intelligence platform built with Flask and MySQL. It provides AI-powered insights into spending patterns, budget tracking, advanced analytics, and smart expense categorization.

**Current Version:** 1.0.0 (Expense Module - Fully Functional)

## ✨ Features

### Core Expense Management
- ✅ Create, Read, Update, Delete (CRUD) Expenses
- ✅ Real-time Dashboard with Live Statistics
- ✅ Advanced Search with Multi-field Support
- ✅ Dynamic Filtering System
- ✅ Smart Sorting Options
- ✅ Pagination Support (Customizable Per Page)

### Advanced Analytics
- ✅ Expense by Category (Pie Chart)
- ✅ Monthly Expense Trend (Bar Chart)
- ✅ Daily Expense Trend (Line Chart)
- ✅ Payment Method Breakdown (Donut Chart)
- ✅ Statistical Insights
- ✅ Spending Heatmap (Ready)

### Smart Features
- ✅ Automatic Category Suggestion
- ✅ Duplicate Expense Detection
- ✅ Receipt Upload & Storage
- ✅ Recurring Expense Support
- ✅ Multi-Currency Support
- ✅ Priority Levels (1-5)
- ✅ Mood Tracking
- ✅ Expense Duplication
- ✅ Soft Delete with Archive

### Data Management
- ✅ CSV Export
- ✅ Excel Export
- ✅ PDF Export Ready
- ✅ Bulk Operations
- ✅ Filter & Search Export

### Security & Performance
- ✅ JWT Authentication
- ✅ User Data Isolation
- ✅ SQL Injection Prevention
- ✅ XSS Protection
- ✅ Database Indexing
- ✅ Transaction Management

## 🛠 Tech Stack

### Backend
- **Framework:** Flask 2.3.3
- **Database:** MySQL with SQLAlchemy ORM
- **Authentication:** Flask-JWT-Extended
- **Validation:** Custom validation layer
- **Password Hashing:** Flask-Bcrypt
- **Email:** Flask-Mail

### Frontend
- **HTML5** with Tailwind CSS
- **JavaScript (Vanilla)** - No frameworks, pure vanilla JS
- **Charts:** Chart.js for data visualization
- **HTTP Client:** Axios (can use Fetch API)
- **Material Design Icons:** Material Symbols Outlined

### Database
- **MySQL 5.7+** or **MySQL 8.0+**
- **Primary Key:** BigInteger (unsigned)
- **Engine:** InnoDB
- **Charset:** utf8mb4 (Unicode support)

## 📁 Project Structure

```
finsight/
├── app.py                          # Main Flask application
├── config.py                       # Configuration management
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variables template
├── 
├── database/
│   └── db.py                       # SQLAlchemy database initialization
│
├── models/
│   ├── user.py                     # User model
│   └── expense.py                  # Expense, Category, Account models
│
├── routes/
│   ├── auth_routers.py             # Authentication endpoints
│   └── expenses_routers.py         # Expense management endpoints
│
├── utils/
│   ├── api_response.py             # Response formatting utility
│   └── decorators.py               # Custom decorators
│
├── extensions/
│   ├── __init__.py                 # Extensions initialization
│   ├── bcrypt.py                   # Password hashing
│   ├── jwt.py                      # JWT authentication
│   └── mail.py                     # Email service
│
├── frontend/
│   ├── login.html                  # Login page
│   ├── expense.html                # Main expense page
│   ├── 
│   ├── css/
│   │   └── styles.css              # Global styles
│   │
│   ├── js/
│   │   └── expenseHandler.js       # Expense UI handler
│   │
│   └── services/
│       └── expenseService.js       # API service layer
│
├── uploads/
│   ├── receipts/                   # Receipt storage by user
│   └── profiles/                   # Profile pictures
│
└── migrations/                     # Database migrations (future)
```

## 📦 Installation Guide

### Prerequisites
- Python 3.8+
- MySQL 5.7+
- pip (Python package manager)
- Git

### Step 1: Clone Repository
```bash
git clone https://github.com/Shubh072/finsight.git
cd finsight
```

### Step 2: Create Virtual Environment
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Setup Database
```bash
# Create MySQL database
mysql -u root -p
```

```sql
CREATE DATABASE finsight_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'finsight_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON finsight_db.* TO 'finsight_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### Step 5: Configure Environment
```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

Update the following in `.env`:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=finsight_user
DB_PASSWORD=your_secure_password
DB_NAME=finsight_db
JWT_SECRET_KEY=your-secure-jwt-key
```

### Step 6: Initialize Database
```bash
python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
>>> exit()
```

## ⚙️ Configuration

### Environment Variables (.env)
```env
# Flask
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=finsight_user
DB_PASSWORD=your_password
DB_NAME=finsight_db

# JWT
JWT_SECRET_KEY=your-jwt-secret-key

# Email (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### Application Config (config.py)
```python
import os
from datetime import timedelta

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    
    # Database
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=30)
    
    # Upload
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB
    UPLOAD_FOLDER = 'uploads'
    
    # Email
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', True)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
```

## 🚀 Running the Application

### Development Mode
```bash
python app.py
```

The application will start at `http://localhost:5000`

### Production Mode (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📚 API Documentation

### Base URL
```
http://localhost:5000/api
```

### Authentication
All endpoints (except `/auth/login` and `/auth/register`) require JWT token:
```
Authorization: Bearer <your_jwt_token>
```

### Expense Endpoints

#### 1. Create Expense
```
POST /expenses
Content-Type: multipart/form-data

Body:
{
  "title": "Office Supplies",
  "category": "Business",
  "amount": "150.50",
  "expense_date": "2024-01-15",
  "payment_method": "Credit Card",
  "merchant_name": "Staples",
  "description": "Monthly office supplies",
  "currency": "USD",
  "receipt": <file>
}

Response:
{
  "success": true,
  "message": "Expense added successfully.",
  "data": {
    "expense_id": 1
  }
}
```

#### 2. Get All Expenses
```
GET /expenses?page=1&per_page=20&search=office&category=Business&sort=created_at&order=desc

Response:
{
  "success": true,
  "message": "Expenses fetched successfully.",
  "data": {
    "expenses": [
      {
        "id": 1,
        "title": "Office Supplies",
        "category": "Business",
        "amount": "150.50",
        "expense_date": "2024-01-15",
        "payment_method": "Credit Card",
        "merchant_name": "Staples",
        "status": "active",
        "created_at": "2024-01-15T10:30:00"
      }
    ],
    "pagination": {
      "total": 100,
      "page": 1,
      "per_page": 20,
      "pages": 5
    }
  }
}
```

#### 3. Get Single Expense
```
GET /expenses/1

Response:
{
  "success": true,
  "message": "Expense fetched successfully.",
  "data": {
    "id": 1,
    "title": "Office Supplies",
    ...
  }
}
```

#### 4. Update Expense
```
PUT /expenses/1
Content-Type: application/json

Body:
{
  "title": "Updated Title",
  "amount": "175.00"
}

Response:
{
  "success": true,
  "message": "Expense updated successfully.",
  "data": {
    "expense_id": 1
  }
}
```

#### 5. Delete Expense
```
DELETE /expenses/1

Response:
{
  "success": true,
  "message": "Expense deleted successfully.",
  "data": {
    "expense_id": 1
  }
}
```

#### 6. Duplicate Expense
```
POST /expenses/1/duplicate
Content-Type: application/json

Body:
{
  "title": "Duplicate of Office Supplies",
  "amount": "150.50"
}

Response:
{
  "success": true,
  "message": "Expense duplicated successfully.",
  "data": {
    "expense_id": 2
  }
}
```

#### 7. Dashboard Statistics
```
GET /expenses/dashboard-stats

Response:
{
  "success": true,
  "message": "Dashboard stats fetched successfully.",
  "data": {
    "total_expenses": 45,
    "total_amount": "5240.50",
    "today_expenses": 3,
    "today_amount": "150.00",
    "month_expenses": 35,
    "month_amount": "4500.00",
    "week_expenses": 12,
    "week_amount": "1200.00",
    "average_amount": "116.46",
    "largest_amount": "500.00"
  }
}
```

#### 8. Get Chart Data
```
GET /expenses/chart-data?date_from=2024-01-01&date_to=2024-01-31

Response:
{
  "success": true,
  "message": "Chart data fetched successfully.",
  "data": {
    "category_chart": [
      {"name": "Business", "value": 1500.00, "count": 10},
      {"name": "Food", "value": 800.00, "count": 25}
    ],
    "monthly_chart": [
      {"month": "2024-01", "total": 5240.50}
    ],
    "payment_chart": [
      {"name": "Credit Card", "value": 3000.00, "count": 20},
      {"name": "Cash", "value": 2240.50, "count": 15}
    ],
    "daily_chart": [
      {"date": "2024-01-01", "total": 150.00, "count": 3},
      {"date": "2024-01-02", "total": 200.00, "count": 4}
    ]
  }
}
```

#### 9. Get Statistics
```
GET /expenses/statistics?date_from=2024-01-01&date_to=2024-01-31

Response:
{
  "success": true,
  "message": "Statistics fetched successfully.",
  "data": {
    "total_expenses": 45,
    "total_amount": "5240.50",
    "average_amount": "116.46",
    "highest_spending_category": "Business",
    "highest_category_amount": "1500.00",
    "most_used_payment_method": "Credit Card",
    "top_merchant": "Staples",
    "date_range": {
      "from": "2024-01-01",
      "to": "2024-01-31"
    }
  }
}
```

#### 10. Duplicate Check
```
POST /expenses/duplicate-check
Content-Type: application/json

Body:
{
  "title": "Office Supplies",
  "amount": "150.50",
  "expense_date": "2024-01-15",
  "merchant_name": "Staples",
  "currency": "USD"
}

Response:
{
  "success": true,
  "message": "Duplicate check completed.",
  "data": {
    "possible_duplicate": true,
    "duplicates": [
      {
        "id": 1,
        "title": "Office Supplies",
        "amount": "150.50",
        "expense_date": "2024-01-15",
        "merchant_name": "Staples"
      }
    ]
  }
}
```

#### 11. Get Categories
```
GET /expenses/categories

Response:
{
  "success": true,
  "message": "Categories fetched successfully.",
  "data": {
    "categories": [
      "Bills",
      "Business",
      "Entertainment",
      "Food",
      "Health",
      "Other",
      "Shopping",
      "Travel",
      "Transportation"
    ]
  }
}
```

#### 12. Get Payment Methods
```
GET /expenses/payment-methods

Response:
{
  "success": true,
  "message": "Payment methods fetched successfully.",
  "data": {
    "payment_methods": [
      "Credit Card",
      "Debit Card",
      "Cash",
      "Bank Transfer",
      "Digital Wallet",
      "Cheque",
      "Other"
    ]
  }
}
```

## 🎯 Features Breakdown

### 1. Dashboard Cards
- **Total Expenses:** Sum of all expenses
- **Today's Expenses:** Expenses from today
- **Monthly Expenses:** Expenses this month
- **Weekly Expenses:** Expenses this week
- **Average Expense:** Mean of all expenses
- **Largest Expense:** Maximum amount spent

### 2. Charts
- **Category Breakdown:** Pie chart showing spending by category
- **Monthly Trend:** Bar chart showing monthly spending patterns
- **Daily Trend:** Line chart showing daily expense progression
- **Payment Method:** Donut chart showing payment method breakdown

### 3. Search & Filters
- Search by: Title, Merchant, Description
- Filter by: Category, Payment Method, Status, Date Range, Amount Range
- Sort by: Created Date, Amount, Expense Date, Title
- Order: Ascending or Descending

### 4. Smart Features
- **Auto Category Suggestion:** Suggests category based on title
- **Duplicate Detection:** Warns about potential duplicates
- **Receipt Upload:** Store receipts with expenses
- **Recurring Expenses:** Mark expenses as recurring
- **Multi-Currency:** Support for multiple currencies
- **Mood Tracking:** Optional mood recording

### 5. Export Options
- **CSV:** Comma-separated values
- **Excel:** Excel spreadsheet format
- **PDF:** PDF document (requires jsPDF library)

## 🗄️ Database Schema

### Expenses Table
```sql
CREATE TABLE expenses (
  id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  user_id BIGINT UNSIGNED NOT NULL,
  title VARCHAR(200) NOT NULL,
  category VARCHAR(80) NOT NULL,
  amount DECIMAL(18, 2) NOT NULL,
  expense_date DATE NOT NULL,
  payment_method VARCHAR(60) NOT NULL,
  account_id BIGINT UNSIGNED,
  merchant_name VARCHAR(180),
  location VARCHAR(180),
  description TEXT,
  tags_json JSON,
  recurring BOOLEAN DEFAULT FALSE,
  currency VARCHAR(10),
  priority INT,
  mood VARCHAR(80),
  status VARCHAR(30) DEFAULT 'active',
  normalized_title VARCHAR(255),
  fingerprint VARCHAR(64),
  receipt_filename VARCHAR(255),
  receipt_url VARCHAR(500),
  receipt_mime VARCHAR(120),
  receipt_size BIGINT UNSIGNED,
  receipt_ocr_text TEXT,
  receipt_ocr_confidence DECIMAL(5, 2),
  ocr_ready BOOLEAN DEFAULT FALSE,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  is_deleted BOOLEAN DEFAULT FALSE,
  deleted_at DATETIME,
  INDEX(user_id),
  INDEX(category),
  INDEX(expense_date),
  INDEX(status),
  INDEX(merchant_name),
  INDEX(normalized_title),
  INDEX(fingerprint),
  INDEX(is_deleted),
  FOREIGN KEY(user_id) REFERENCES users(user_id)
) ENGINE=InnoDB CHARACTER SET utf8mb4;
```

### Indexes for Performance
- `user_id`: Fast user-specific queries
- `category`: Quick filtering by category
- `expense_date`: Date range queries
- `status`: Status filtering
- `merchant_name`: Merchant search
- `is_deleted`: Soft delete queries

## 🐛 Troubleshooting

### Common Issues

#### 1. Database Connection Error
```
Error: Can't connect to MySQL server
```
**Solution:**
- Check MySQL is running: `mysql -u root -p`
- Verify `.env` database credentials
- Ensure database exists: `SHOW DATABASES;`

#### 2. JWT Token Error
```
Error: Invalid token
```
**Solution:**
- Regenerate JWT token through login
- Check JWT_SECRET_KEY in `.env`
- Ensure token is in Authorization header: `Bearer <token>`

#### 3. Receipt Upload Error
```
Error: File too large
```
**Solution:**
- File must be under 5MB
- Supported formats: jpg, png, webp, pdf

#### 4. Import Error
```
Error: No module named 'config'
```
**Solution:**
- Ensure virtual environment is activated
- Run: `pip install -r requirements.txt`
- Check current directory is project root

#### 5. Port Already in Use
```
Error: Address already in use
```
**Solution:**
- Change port in `app.py`: `app.run(port=5001)`
- Kill existing process on port 5000

### Debugging Tips

1. **Enable detailed logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **Check database tables:**
```sql
SHOW TABLES;
DESCRIBE expenses;
```

3. **Test API endpoint:**
```bash
curl -H "Authorization: Bearer <token>" http://localhost:5000/api/expenses
```

4. **Check application logs:**
Look for errors in terminal where `python app.py` is running

## 📝 API Testing with Postman

### Steps:
1. Create new Postman collection
2. Set environment variable: `base_url = http://localhost:5000/api`
3. Set environment variable: `token = <your_jwt_token>`
4. Use `{{base_url}}/expenses` in requests
5. Use `Authorization: Bearer {{token}}` in headers

## 🔐 Security Considerations

1. **Change default secrets** in production
2. **Use HTTPS** in production
3. **Enable CORS** only for trusted domains
4. **Rate limiting** for API endpoints
5. **Input validation** on all endpoints
6. **SQL injection prevention** via ORM
7. **XSS protection** via input sanitization
8. **CSRF tokens** for state-changing operations

## 📈 Performance Optimization

1. **Database indexes** on frequently queried columns
2. **Pagination** to limit query results
3. **Caching** for metadata (categories, payment methods)
4. **Lazy loading** for related data
5. **Query optimization** with select specific columns

## 🚀 Deployment Guide

### Heroku Deployment
```bash
heroku login
heroku create finsight-app
git push heroku main
heroku run python
>>> from app import app, db
>>> with app.app_context():
...     db.create_all()
```

### AWS EC2 Deployment
```bash
# Use Gunicorn + Nginx
# Configure security groups
# Set up SSL certificate
```

## 📞 Support & Contribution

For issues, questions, or contributions:
1. Open an issue on GitHub
2. Create a pull request
3. Follow code style guidelines
4. Write tests for new features

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

- Built with Flask, SQLAlchemy, and Chart.js
- Inspired by modern fintech applications
- Community contributions welcome

---

**Last Updated:** January 2024
**Version:** 1.0.0
**Status:** Production Ready (Expense Module)
