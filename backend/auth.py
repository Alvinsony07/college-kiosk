"""
Enhanced Authentication and Security Module
Features: JWT tokens, 2FA, session management, audit logs, password policies
"""

import jwt
import pyotp
import qrcode
import io
import base64
from datetime import datetime, timedelta
import hashlib
import random
import string
import re
from functools import wraps
from flask import request, jsonify, current_app
import sqlite3
import json
from werkzeug.security import generate_password_hash, check_password_hash

class SecurityManager:
    def __init__(self, db_path, secret_key):
        self.db_path = db_path
        self.secret_key = secret_key
        self.init_security_tables()
    
    def init_security_tables(self):
        """Initialize security-related database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Audit logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                user_email TEXT,
                action TEXT,
                resource TEXT,
                resource_id TEXT,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                session_token TEXT UNIQUE,
                refresh_token TEXT UNIQUE,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                ip_address TEXT,
                user_agent TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 2FA secrets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_2fa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE,
                secret_key TEXT,
                is_enabled INTEGER DEFAULT 0,
                backup_codes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Failed login attempts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS failed_login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT,
                ip_address TEXT,
                attempt_time TEXT DEFAULT CURRENT_TIMESTAMP,
                user_agent TEXT
            )
        ''')
        
        # Password reset tokens table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token TEXT UNIQUE,
                expires_at TEXT,
                used INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Security settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE,
                setting_value TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Add new columns to users table
        def add_column_if_not_exists(table, column, definition):
            cursor.execute(f"PRAGMA table_info({table})")
            columns = [row[1] for row in cursor.fetchall()]
            if column not in columns:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        
        add_column_if_not_exists('users', 'password_changed_at', 'TEXT')
        add_column_if_not_exists('users', 'failed_login_count', 'INTEGER DEFAULT 0')
        add_column_if_not_exists('users', 'locked_until', 'TEXT')
        add_column_if_not_exists('users', 'last_login', 'TEXT')
        add_column_if_not_exists('users', 'two_fa_enabled', 'INTEGER DEFAULT 0')
        
        # Insert default security settings
        default_settings = [
            ('password_min_length', '8'),
            ('password_require_uppercase', '1'),
            ('password_require_lowercase', '1'),
            ('password_require_numbers', '1'),
            ('password_require_special', '1'),
            ('max_failed_attempts', '5'),
            ('lockout_duration_minutes', '30'),
            ('session_timeout_hours', '24'),
            ('jwt_expiry_hours', '1'),
            ('password_expiry_days', '90')
        ]
        
        for key, value in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO security_settings (setting_key, setting_value)
                VALUES (?, ?)
            ''', (key, value))
        
        conn.commit()
        conn.close()
    
    def get_security_setting(self, key, default=None):
        """Get a security setting value"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT setting_value FROM security_settings WHERE setting_key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else default
    
    def validate_password_policy(self, password):
        """Validate password against security policy"""
        errors = []
        
        min_length = int(self.get_security_setting('password_min_length', 8))
        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters long")
        
        if self.get_security_setting('password_require_uppercase', '1') == '1':
            if not re.search(r'[A-Z]', password):
                errors.append("Password must contain at least one uppercase letter")
        
        if self.get_security_setting('password_require_lowercase', '1') == '1':
            if not re.search(r'[a-z]', password):
                errors.append("Password must contain at least one lowercase letter")
        
        if self.get_security_setting('password_require_numbers', '1') == '1':
            if not re.search(r'\d', password):
                errors.append("Password must contain at least one number")
        
        if self.get_security_setting('password_require_special', '1') == '1':
            if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
                errors.append("Password must contain at least one special character")
        
        return errors
    
    def hash_password(self, password):
        """Hash password using bcrypt-style hashing"""
        return generate_password_hash(password)
    
    def check_password(self, password, hashed):
        """Check password against hash"""
        return check_password_hash(hashed, password)
    
    def generate_jwt_token(self, user_data):
        """Generate JWT access token"""
        expiry_hours = int(self.get_security_setting('jwt_expiry_hours', 1))
        payload = {
            'user_id': user_data['id'],
            'email': user_data['email'],
            'role': user_data['role'],
            'exp': datetime.utcnow() + timedelta(hours=expiry_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def generate_refresh_token(self):
        """Generate refresh token"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=64))
    
    def verify_jwt_token(self, token):
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def create_session(self, user_id, ip_address, user_agent):
        """Create a new user session"""
        session_token = self.generate_refresh_token()
        refresh_token = self.generate_refresh_token()
        session_timeout = int(self.get_security_setting('session_timeout_hours', 24))
        expires_at = datetime.utcnow() + timedelta(hours=session_timeout)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO user_sessions 
            (user_id, session_token, refresh_token, expires_at, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, session_token, refresh_token, expires_at.isoformat(), ip_address, user_agent))
        conn.commit()
        conn.close()
        
        return {
            'session_token': session_token,
            'refresh_token': refresh_token,
            'expires_at': expires_at.isoformat()
        }
    
    def validate_session(self, session_token):
        """Validate active session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.user_id, s.expires_at, u.email, u.role 
            FROM user_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_token = ? AND s.is_active = 1
        ''', (session_token,))
        result = cursor.fetchone()
        
        if result:
            expires_at = datetime.fromisoformat(result[1])
            if expires_at > datetime.utcnow():
                # Update last activity
                cursor.execute('''
                    UPDATE user_sessions 
                    SET last_activity = CURRENT_TIMESTAMP 
                    WHERE session_token = ?
                ''', (session_token,))
                conn.commit()
                conn.close()
                return {
                    'user_id': result[0],
                    'email': result[2],
                    'role': result[3]
                }
        
        conn.close()
        return None
    
    def revoke_session(self, session_token):
        """Revoke a session"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE user_sessions SET is_active = 0 WHERE session_token = ?", (session_token,))
        conn.commit()
        conn.close()
    
    def setup_2fa(self, user_id):
        """Setup 2FA for user"""
        secret = pyotp.random_base32()
        backup_codes = [
            ''.join(random.choices(string.digits, k=8))
            for _ in range(10)
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_2fa (user_id, secret_key, backup_codes)
            VALUES (?, ?, ?)
        ''', (user_id, secret, json.dumps(backup_codes)))
        conn.commit()
        conn.close()
        
        # Generate QR code
        user_email = self.get_user_email(user_id)
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="College Kiosk Admin"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'secret': secret,
            'qr_code': f"data:image/png;base64,{qr_code_data}",
            'backup_codes': backup_codes
        }
    
    def verify_2fa_token(self, user_id, token):
        """Verify 2FA token"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT secret_key, backup_codes FROM user_2fa WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False
        
        secret, backup_codes_json = result
        backup_codes = json.loads(backup_codes_json) if backup_codes_json else []
        
        # Check TOTP token
        totp = pyotp.TOTP(secret)
        if totp.verify(token, valid_window=1):
            return True
        
        # Check backup codes
        if token in backup_codes:
            # Remove used backup code
            backup_codes.remove(token)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE user_2fa SET backup_codes = ? WHERE user_id = ?",
                (json.dumps(backup_codes), user_id)
            )
            conn.commit()
            conn.close()
            return True
        
        return False
    
    def enable_2fa(self, user_id):
        """Enable 2FA for user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("UPDATE user_2fa SET is_enabled = 1 WHERE user_id = ?", (user_id,))
        cursor.execute("UPDATE users SET two_fa_enabled = 1 WHERE id = ?", (user_id,))
        conn.commit()
        conn.close()
    
    def log_audit_event(self, user_id, user_email, action, resource, resource_id=None, 
                       old_values=None, new_values=None, ip_address=None, user_agent=None):
        """Log audit event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_logs 
            (user_id, user_email, action, resource, resource_id, old_values, new_values, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, user_email, action, resource, resource_id,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            ip_address, user_agent
        ))
        conn.commit()
        conn.close()
    
    def record_failed_login(self, email, ip_address, user_agent):
        """Record failed login attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO failed_login_attempts (email, ip_address, user_agent)
            VALUES (?, ?, ?)
        ''', (email, ip_address, user_agent))
        
        # Update user failed login count
        cursor.execute("UPDATE users SET failed_login_count = failed_login_count + 1 WHERE email = ?", (email,))
        
        # Check if account should be locked
        max_attempts = int(self.get_security_setting('max_failed_attempts', 5))
        cursor.execute("SELECT failed_login_count FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        
        if result and result[0] >= max_attempts:
            lockout_duration = int(self.get_security_setting('lockout_duration_minutes', 30))
            locked_until = datetime.utcnow() + timedelta(minutes=lockout_duration)
            cursor.execute(
                "UPDATE users SET locked_until = ? WHERE email = ?",
                (locked_until.isoformat(), email)
            )
        
        conn.commit()
        conn.close()
    
    def is_account_locked(self, email):
        """Check if account is locked"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT locked_until FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            locked_until = datetime.fromisoformat(result[0])
            return locked_until > datetime.utcnow()
        
        return False
    
    def reset_failed_login_count(self, email):
        """Reset failed login count after successful login"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET failed_login_count = 0, locked_until = NULL, last_login = CURRENT_TIMESTAMP 
            WHERE email = ?
        ''', (email,))
        conn.commit()
        conn.close()
    
    def get_user_email(self, user_id):
        """Get user email by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        if token.startswith('Bearer '):
            token = token[7:]
        
        security_manager = current_app.config.get('SECURITY_MANAGER')
        if not security_manager:
            return jsonify({'error': 'Security manager not configured'}), 500
        
        payload = security_manager.verify_jwt_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        request.current_user = payload
        return f(*args, **kwargs)
    
    return decorated_function

def require_role(roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user_role = request.current_user.get('role')
            if user_role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def audit_log(action, resource):
    """Decorator to automatically log actions"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Store old values if this is an update
            old_values = None
            resource_id = kwargs.get('id') or request.view_args.get('id')
            
            if request.method in ['PUT', 'PATCH', 'DELETE'] and resource_id:
                # Fetch old values before modification
                # This would need to be customized per resource type
                pass
            
            # Execute the function
            result = f(*args, **kwargs)
            
            # Log the action
            if hasattr(request, 'current_user'):
                security_manager = current_app.config.get('SECURITY_MANAGER')
                if security_manager:
                    security_manager.log_audit_event(
                        user_id=request.current_user.get('user_id'),
                        user_email=request.current_user.get('email'),
                        action=action,
                        resource=resource,
                        resource_id=str(resource_id) if resource_id else None,
                        old_values=old_values,
                        new_values=request.get_json() if request.is_json else None,
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
            
            return result
        return decorated_function
    return decorator