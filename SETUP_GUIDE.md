# College Kiosk Enterprise System - Setup & Running Guide

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.8 or higher
- Git (for version control)
- Redis (for caching and real-time features)
- Optional: PostgreSQL (for production use)

### 1. Environment Setup

#### Create Virtual Environment

```bash
# Navigate to your project directory
cd "C:\Users\Alvin Sony\Desktop\colege kiosk with blue white theme\college-kiosk\college-kiosk"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

#### Install Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# If you encounter any installation issues, install core packages first:
pip install Flask Flask-CORS SQLAlchemy pandas numpy requests
```

### 2. Database Setup

#### Initialize Database

```bash
# The database will be automatically created when you first run the app
# Located at: college.db in the root directory
```

#### Optional: PostgreSQL Setup (Production)

```bash
# Install PostgreSQL
# Update connection string in app.py if using PostgreSQL
```

### 3. Redis Setup (Optional - for advanced features)

#### Install Redis

```bash
# Windows (using Chocolatey):
choco install redis-64

# Or download from: https://redis.io/download
# Start Redis server:
redis-server
```

### 4. Configuration

#### Environment Variables (Optional)

Create a `.env` file in the root directory:

```env
# Database Configuration
DATABASE_URL=sqlite:///college.db
# For PostgreSQL: postgresql://username:password@localhost/college_kiosk

# Security
SECRET_KEY=your-super-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# Redis Configuration (if using)
REDIS_URL=redis://localhost:6379/0

# Email Configuration (for notifications)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Third-party API Keys (optional)
STRIPE_SECRET_KEY=sk_test_...
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
```

## 🏃‍♂️ Running the Application

### Method 1: Basic Development Server

```bash
# Navigate to backend directory
cd backend

# Run the Flask application
python app.py
```

### Method 2: Enhanced Development with All Features

```bash
# Start Redis (in separate terminal)
redis-server

# Run the main application
python backend/app.py

# The application will be available at:
# http://localhost:5000
```

### Method 3: Production Server

```bash
# Using Gunicorn (recommended for production)
gunicorn --bind 0.0.0.0:5000 --workers 4 backend.app:app

# Or with more advanced configuration:
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 --keep-alive 2 backend.app:app
```

## 🌐 Accessing the Application

### Main Application

- **Frontend**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin.html
- **Staff Dashboard**: http://localhost:5000/staff.html
- **User Registration**: http://localhost:5000/register.html

### API Documentation

- **Interactive API Docs**: http://localhost:5000/docs/
- **Swagger UI**: http://localhost:5000/docs/swagger/
- **Postman Collection**: http://localhost:5000/docs/postman

### Advanced Features

- **Analytics Dashboard**: http://localhost:5000/analytics/dashboard
- **Real-time Dashboard**: http://localhost:5000/realtime/dashboard
- **Business Intelligence**: http://localhost:5000/bi/dashboard
- **Testing Suite**: http://localhost:5000/testing/dashboard

## 🔧 Development Tools

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test types
python backend/testing_suite.py

# Access test dashboard
# http://localhost:5000/testing/dashboard
```

### Code Quality

```bash
# Format code
black backend/

# Lint code
flake8 backend/

# Check for security issues
bandit -r backend/
```

## 📱 Mobile App Setup (Optional)

### Expo/React Native (if using mobile app)

```bash
# Install Expo CLI
npm install -g @expo/cli

# Navigate to mobile directory (if exists)
cd mobile

# Install dependencies
npm install

# Start development server
expo start
```

## 🔐 Security Configuration

### SSL/HTTPS Setup (Production)

```bash
# Generate SSL certificates
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Run with SSL
python app.py --ssl-context=adhoc
# Or configure in production web server (nginx, Apache)
```

### Firewall Configuration

```bash
# Allow application port
# Windows Firewall:
netsh advfirewall firewall add rule name="College Kiosk" dir=in action=allow protocol=TCP localport=5000

# Linux UFW:
sudo ufw allow 5000
```

## 📊 Monitoring & Maintenance

### Health Checks

- **System Health**: http://localhost:5000/health
- **Database Status**: http://localhost:5000/db-status
- **Performance Metrics**: http://localhost:5000/performance/metrics

### Log Files

- **Application Logs**: `logs/app.log`
- **Error Logs**: `logs/error.log`
- **Access Logs**: `logs/access.log`

### Database Maintenance

```bash
# Backup database
python scripts/backup_db.py

# Database cleanup (if needed)
python scripts/cleanup_db.py
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# If you get module import errors:
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

#### 2. Database Errors

```bash
# If database initialization fails:
# Delete college.db and restart the application
rm college.db
python backend/app.py
```

#### 3. Port Already in Use

```bash
# If port 5000 is busy:
# Find and kill the process:
netstat -ano | findstr :5000
taskkill /PID <PID_NUMBER> /F

# Or run on different port:
export FLASK_RUN_PORT=5001
python backend/app.py
```

#### 4. Redis Connection Issues

```bash
# If Redis features don't work:
# Make sure Redis is running:
redis-cli ping
# Should return "PONG"
```

### Performance Optimization

#### 1. Database Optimization

```sql
-- Create indexes for better performance
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_menu_items_category ON menu_items(category);
```

#### 2. Caching Setup

```python
# Redis caching is automatically configured
# Monitor cache hit rates at: /performance/cache-stats
```

## 📈 Scaling & Production Deployment

### Docker Deployment (Optional)

```dockerfile
# Dockerfile (create this if needed)
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "backend.app:app"]
```

### Load Balancer Configuration

```nginx
# Nginx configuration (if using)
upstream college_kiosk {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://college_kiosk;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🎯 Feature-Specific Setup

### Real-time Features

- Requires WebSocket support
- Redis recommended for scaling
- Enable in browser: Allow notifications

### Machine Learning Features

- Requires scikit-learn, pandas, numpy
- Auto-trains models on startup
- Access ML insights at: `/bi/dashboard`

### Payment Processing

- Configure payment provider API keys in .env
- Test with sandbox credentials first
- Enable webhooks for real-time updates

### Mobile API

- CORS is pre-configured
- API documentation at: `/docs/`
- Mobile-specific endpoints at: `/mobile/api/`

## 📞 Support & Resources

### Default Admin Account

- **Email**: admin@collegekiosk.com
- **Password**: admin123
- **Access**: http://localhost:5000/admin.html

### API Testing

- Use Postman collection: http://localhost:5000/docs/postman
- Interactive testing: http://localhost:5000/docs/swagger/
- API key generation: http://localhost:5000/docs/test-key

### Documentation

- Full API documentation available at startup
- Feature guides in each module's docstrings
- Database schema auto-documented

---

## 🎉 You're Ready to Go!

Your College Kiosk Enterprise System includes:

- ✅ 14 Enterprise modules
- ✅ 200+ Features
- ✅ Real-time capabilities
- ✅ Machine learning insights
- ✅ Comprehensive testing
- ✅ Production-ready architecture

**Start Command**: `python backend/app.py`
**Access URL**: http://localhost:5000

Happy coding! 🚀
