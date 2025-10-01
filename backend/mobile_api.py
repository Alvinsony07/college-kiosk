"""
Mobile API Module
Features: RESTful API for mobile apps, push notifications, offline sync
"""

from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from functools import wraps
import jwt
import sqlite3
import json
from datetime import datetime, timedelta
import uuid
import hashlib
import os

class MobileAPIManager:
    def __init__(self, app, db_path, secret_key):
        self.app = app
        self.db_path = db_path
        self.secret_key = secret_key
        self.api = Api(app)
        
        # Initialize mobile-specific tables
        self.init_mobile_tables()
        
        # Register API endpoints
        self.register_endpoints()
    
    def init_mobile_tables(self):
        """Initialize mobile API tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Mobile app registrations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mobile_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                device_type TEXT, -- ios, android
                device_model TEXT,
                app_version TEXT,
                os_version TEXT,
                push_token TEXT,
                is_active INTEGER DEFAULT 1,
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # API tokens for mobile authentication
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                device_id TEXT,
                token_hash TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_used TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (device_id) REFERENCES mobile_devices (device_id)
            )
        ''')
        
        # Push notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS push_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                device_id TEXT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                data TEXT, -- JSON data
                notification_type TEXT, -- order_update, promotion, alert
                status TEXT DEFAULT 'pending', -- pending, sent, failed, delivered
                scheduled_at TEXT,
                sent_at TEXT,
                delivered_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (device_id) REFERENCES mobile_devices (device_id)
            )
        ''')
        
        # Offline sync queue
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                entity_type TEXT NOT NULL, -- order, menu, user
                entity_id INTEGER NOT NULL,
                action TEXT NOT NULL, -- create, update, delete
                data TEXT, -- JSON data
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                synced INTEGER DEFAULT 0,
                sync_attempts INTEGER DEFAULT 0,
                last_sync_attempt TEXT,
                FOREIGN KEY (device_id) REFERENCES mobile_devices (device_id)
            )
        ''')
        
        # API usage analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                user_id INTEGER,
                device_id TEXT,
                response_time REAL,
                status_code INTEGER,
                ip_address TEXT,
                user_agent TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (device_id) REFERENCES mobile_devices (device_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_endpoints(self):
        """Register mobile API endpoints"""
        # Authentication endpoints
        self.api.add_resource(MobileAuthResource, '/api/mobile/auth/login',
                             resource_class_kwargs={'manager': self})
        self.api.add_resource(MobileAuthResource, '/api/mobile/auth/register',
                             resource_class_kwargs={'manager': self})
        self.api.add_resource(MobileAuthResource, '/api/mobile/auth/refresh',
                             resource_class_kwargs={'manager': self})
        
        # Menu endpoints
        self.api.add_resource(MobileMenuResource, '/api/mobile/menu',
                             '/api/mobile/menu/<int:item_id>',
                             resource_class_kwargs={'manager': self})
        
        # Order endpoints
        self.api.add_resource(MobileOrderResource, '/api/mobile/orders',
                             '/api/mobile/orders/<int:order_id>',
                             resource_class_kwargs={'manager': self})
        
        # User profile endpoints
        self.api.add_resource(MobileUserResource, '/api/mobile/profile',
                             resource_class_kwargs={'manager': self})
        
        # Device management
        self.api.add_resource(MobileDeviceResource, '/api/mobile/device',
                             resource_class_kwargs={'manager': self})
        
        # Sync endpoints
        self.api.add_resource(MobileSyncResource, '/api/mobile/sync',
                             resource_class_kwargs={'manager': self})
    
    def authenticate_token(self, token):
        """Authenticate API token"""
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            token_id = payload.get('token_id')
            user_id = payload.get('user_id')
            device_id = payload.get('device_id')
            
            # Verify token in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, device_id FROM api_tokens
                WHERE token_id = ? AND user_id = ? AND is_active = 1
                AND expires_at > CURRENT_TIMESTAMP
            ''', (token_id, user_id))
            
            token_data = cursor.fetchone()
            
            if token_data:
                # Update last used timestamp
                cursor.execute('''
                    UPDATE api_tokens SET last_used = CURRENT_TIMESTAMP
                    WHERE token_id = ?
                ''', (token_id,))
                
                # Update device last seen
                cursor.execute('''
                    UPDATE mobile_devices SET last_seen = CURRENT_TIMESTAMP
                    WHERE device_id = ?
                ''', (device_id,))
                
                conn.commit()
                conn.close()
                
                return {
                    'user_id': token_data[0],
                    'device_id': token_data[1]
                }
            
            conn.close()
            return None
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def generate_api_token(self, user_id, device_id, expires_hours=24):
        """Generate API token for mobile app"""
        token_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(hours=expires_hours)
        
        # Create JWT payload
        payload = {
            'token_id': token_id,
            'user_id': user_id,
            'device_id': device_id,
            'exp': expires_at,
            'iat': datetime.now()
        }
        
        # Generate JWT token
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Store token in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_tokens (token_id, user_id, device_id, token_hash, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (token_id, user_id, device_id, token_hash, expires_at.isoformat()))
        
        conn.commit()
        conn.close()
        
        return token
    
    def register_device(self, device_data, user_id=None):
        """Register mobile device"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if device already exists
        cursor.execute('''
            SELECT id FROM mobile_devices WHERE device_id = ?
        ''', (device_data['device_id'],))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update existing device
            cursor.execute('''
                UPDATE mobile_devices 
                SET user_id = ?, device_type = ?, device_model = ?, 
                    app_version = ?, os_version = ?, push_token = ?,
                    last_seen = CURRENT_TIMESTAMP
                WHERE device_id = ?
            ''', (
                user_id,
                device_data.get('device_type'),
                device_data.get('device_model'),
                device_data.get('app_version'),
                device_data.get('os_version'),
                device_data.get('push_token'),
                device_data['device_id']
            ))
        else:
            # Insert new device
            cursor.execute('''
                INSERT INTO mobile_devices 
                (device_id, user_id, device_type, device_model, app_version, 
                 os_version, push_token)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                device_data['device_id'],
                user_id,
                device_data.get('device_type'),
                device_data.get('device_model'),
                device_data.get('app_version'),
                device_data.get('os_version'),
                device_data.get('push_token')
            ))
        
        conn.commit()
        conn.close()
    
    def send_push_notification(self, user_id=None, device_id=None, title=None, 
                              message=None, data=None, notification_type='general'):
        """Send push notification"""
        notification_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO push_notifications 
            (notification_id, user_id, device_id, title, message, data, 
             notification_type, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            notification_id, user_id, device_id, title, message,
            json.dumps(data) if data else None, notification_type, 'pending'
        ))
        
        conn.commit()
        
        # Get devices to send to
        if device_id:
            cursor.execute('''
                SELECT device_id, push_token FROM mobile_devices
                WHERE device_id = ? AND push_token IS NOT NULL AND is_active = 1
            ''', (device_id,))
        elif user_id:
            cursor.execute('''
                SELECT device_id, push_token FROM mobile_devices
                WHERE user_id = ? AND push_token IS NOT NULL AND is_active = 1
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT device_id, push_token FROM mobile_devices
                WHERE push_token IS NOT NULL AND is_active = 1
            ''')
        
        devices = cursor.fetchall()
        conn.close()
        
        # Send notifications (this would integrate with FCM/APNS)
        for device_id, push_token in devices:
            try:
                # Placeholder for actual push notification sending
                # self._send_fcm_notification(push_token, title, message, data)
                
                # Update notification status
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE push_notifications 
                    SET status = 'sent', sent_at = CURRENT_TIMESTAMP
                    WHERE notification_id = ?
                ''', (notification_id,))
                conn.commit()
                conn.close()
                
            except Exception as e:
                # Update notification status to failed
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE push_notifications 
                    SET status = 'failed'
                    WHERE notification_id = ?
                ''', (notification_id,))
                conn.commit()
                conn.close()
        
        return notification_id
    
    def add_to_sync_queue(self, device_id, entity_type, entity_id, action, data=None):
        """Add item to sync queue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sync_queue (device_id, entity_type, entity_id, action, data)
            VALUES (?, ?, ?, ?, ?)
        ''', (device_id, entity_type, entity_id, action, json.dumps(data) if data else None))
        
        conn.commit()
        conn.close()
    
    def get_sync_data(self, device_id, last_sync_timestamp=None):
        """Get sync data for device"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if last_sync_timestamp:
            cursor.execute('''
                SELECT entity_type, entity_id, action, data, timestamp
                FROM sync_queue
                WHERE device_id = ? AND timestamp > ? AND synced = 0
                ORDER BY timestamp ASC
            ''', (device_id, last_sync_timestamp))
        else:
            cursor.execute('''
                SELECT entity_type, entity_id, action, data, timestamp
                FROM sync_queue
                WHERE device_id = ? AND synced = 0
                ORDER BY timestamp ASC
            ''', (device_id,))
        
        sync_items = cursor.fetchall()
        conn.close()
        
        return [
            {
                'entity_type': item[0],
                'entity_id': item[1],
                'action': item[2],
                'data': json.loads(item[3]) if item[3] else None,
                'timestamp': item[4]
            }
            for item in sync_items
        ]
    
    def mark_synced(self, device_id, sync_items):
        """Mark items as synced"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in sync_items:
            cursor.execute('''
                UPDATE sync_queue 
                SET synced = 1
                WHERE device_id = ? AND entity_type = ? AND entity_id = ? 
                AND timestamp = ?
            ''', (device_id, item['entity_type'], item['entity_id'], item['timestamp']))
        
        conn.commit()
        conn.close()
    
    def log_api_usage(self, endpoint, method, user_id=None, device_id=None, 
                     response_time=None, status_code=None, ip_address=None, user_agent=None):
        """Log API usage for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_usage 
            (endpoint, method, user_id, device_id, response_time, status_code, 
             ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (endpoint, method, user_id, device_id, response_time, status_code, 
              ip_address, user_agent))
        
        conn.commit()
        conn.close()


# API Resource Classes
def require_auth(f):
    """Decorator for API authentication"""
    @wraps(f)
    def decorated_function(self, *args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return {'error': 'Authentication required'}, 401
        
        token = token.replace('Bearer ', '')
        auth_data = self.manager.authenticate_token(token)
        
        if not auth_data:
            return {'error': 'Invalid or expired token'}, 401
        
        request.user_id = auth_data['user_id']
        request.device_id = auth_data['device_id']
        
        return f(self, *args, **kwargs)
    return decorated_function


class MobileAuthResource(Resource):
    def __init__(self, manager):
        self.manager = manager
    
    def post(self):
        """Handle mobile authentication"""
        endpoint = request.endpoint
        data = request.get_json()
        
        if 'login' in endpoint:
            return self.login(data)
        elif 'register' in endpoint:
            return self.register(data)
        elif 'refresh' in endpoint:
            return self.refresh_token(data)
    
    def login(self, data):
        """Mobile login"""
        email = data.get('email')
        password = data.get('password')
        device_data = data.get('device', {})
        
        if not email or not password:
            return {'error': 'Email and password required'}, 400
        
        # Authenticate user
        conn = sqlite3.connect(self.manager.db_path)
        cursor = conn.cursor()
        
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute('''
            SELECT id, username, full_name, role FROM users
            WHERE email = ? AND password = ? AND is_active = 1
        ''', (email, hashed_password))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return {'error': 'Invalid credentials'}, 401
        
        user_id = user[0]
        
        # Register device
        if device_data.get('device_id'):
            self.manager.register_device(device_data, user_id)
        
        # Generate API token
        token = self.manager.generate_api_token(user_id, device_data.get('device_id'))
        
        return {
            'token': token,
            'user': {
                'id': user[0],
                'username': user[1],
                'full_name': user[2],
                'role': user[3]
            }
        }
    
    def register(self, data):
        """Mobile registration"""
        # Similar to login but creates new user
        required_fields = ['username', 'email', 'password', 'full_name']
        for field in required_fields:
            if not data.get(field):
                return {'error': f'{field} is required'}, 400
        
        # Create user (simplified)
        conn = sqlite3.connect(self.manager.db_path)
        cursor = conn.cursor()
        
        hashed_password = hashlib.sha256(data['password'].encode()).hexdigest()
        
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (data['username'], data['email'], hashed_password, 
                  data['full_name'], 'customer'))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Register device and generate token
            device_data = data.get('device', {})
            if device_data.get('device_id'):
                self.manager.register_device(device_data, user_id)
            
            token = self.manager.generate_api_token(user_id, device_data.get('device_id'))
            
            return {
                'token': token,
                'user': {
                    'id': user_id,
                    'username': data['username'],
                    'full_name': data['full_name'],
                    'role': 'customer'
                }
            }
            
        except sqlite3.IntegrityError:
            conn.close()
            return {'error': 'User already exists'}, 400


class MobileMenuResource(Resource):
    def __init__(self, manager):
        self.manager = manager
    
    def get(self, item_id=None):
        """Get menu items"""
        conn = sqlite3.connect(self.manager.db_path)
        cursor = conn.cursor()
        
        if item_id:
            cursor.execute('''
                SELECT id, name, description, price, category, image_url, is_available
                FROM menu WHERE id = ? AND is_available = 1
            ''', (item_id,))
            item = cursor.fetchone()
            
            if not item:
                return {'error': 'Menu item not found'}, 404
            
            return {
                'id': item[0],
                'name': item[1],
                'description': item[2],
                'price': item[3],
                'category': item[4],
                'image_url': item[5],
                'is_available': bool(item[6])
            }
        else:
            cursor.execute('''
                SELECT id, name, description, price, category, image_url, is_available
                FROM menu WHERE is_available = 1
                ORDER BY category, name
            ''')
            items = cursor.fetchall()
            
            menu_items = []
            for item in items:
                menu_items.append({
                    'id': item[0],
                    'name': item[1],
                    'description': item[2],
                    'price': item[3],
                    'category': item[4],
                    'image_url': item[5],
                    'is_available': bool(item[6])
                })
            
            return {'menu_items': menu_items}
        
        conn.close()


class MobileOrderResource(Resource):
    def __init__(self, manager):
        self.manager = manager
    
    @require_auth
    def get(self, order_id=None):
        """Get user orders"""
        conn = sqlite3.connect(self.manager.db_path)
        cursor = conn.cursor()
        
        if order_id:
            cursor.execute('''
                SELECT id, customer_name, customer_email, items, total_price, 
                       status, created_at, updated_at
                FROM orders 
                WHERE id = ? AND customer_email = (
                    SELECT email FROM users WHERE id = ?
                )
            ''', (order_id, request.user_id))
            
            order = cursor.fetchone()
            if not order:
                return {'error': 'Order not found'}, 404
            
            return {
                'id': order[0],
                'customer_name': order[1],
                'customer_email': order[2],
                'items': json.loads(order[3]),
                'total_price': order[4],
                'status': order[5],
                'created_at': order[6],
                'updated_at': order[7]
            }
        else:
            cursor.execute('''
                SELECT id, customer_name, items, total_price, status, created_at
                FROM orders 
                WHERE customer_email = (
                    SELECT email FROM users WHERE id = ?
                )
                ORDER BY created_at DESC
                LIMIT 20
            ''', (request.user_id,))
            
            orders = cursor.fetchall()
            
            return {
                'orders': [
                    {
                        'id': order[0],
                        'customer_name': order[1],
                        'items': json.loads(order[2]),
                        'total_price': order[3],
                        'status': order[4],
                        'created_at': order[5]
                    }
                    for order in orders
                ]
            }
        
        conn.close()
    
    @require_auth
    def post(self):
        """Create new order"""
        data = request.get_json()
        
        # Get user details
        conn = sqlite3.connect(self.manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT username, email, full_name FROM users WHERE id = ?', 
                      (request.user_id,))
        user = cursor.fetchone()
        
        if not user:
            return {'error': 'User not found'}, 404
        
        # Create order
        cursor.execute('''
            INSERT INTO orders (customer_name, customer_email, items, total_price, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            user[2] or user[0],  # full_name or username
            user[1],             # email
            json.dumps(data.get('items', [])),
            data.get('total_price', 0),
            'Pending'
        ))
        
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Add to sync queue for other devices
        self.manager.add_to_sync_queue(
            request.device_id, 'order', order_id, 'create',
            {'order_id': order_id, 'status': 'Pending'}
        )
        
        # Send push notification
        self.manager.send_push_notification(
            user_id=request.user_id,
            title='Order Placed',
            message=f'Your order #{order_id} has been placed successfully',
            notification_type='order_update',
            data={'order_id': order_id}
        )
        
        return {'order_id': order_id, 'status': 'created'}, 201


class MobileUserResource(Resource):
    def __init__(self, manager):
        self.manager = manager
    
    @require_auth
    def get(self):
        """Get user profile"""
        conn = sqlite3.connect(self.manager.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, email, full_name, phone, role, created_at, last_login
            FROM users WHERE id = ?
        ''', (request.user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return {'error': 'User not found'}, 404
        
        return {
            'username': user[0],
            'email': user[1],
            'full_name': user[2],
            'phone': user[3],
            'role': user[4],
            'created_at': user[5],
            'last_login': user[6]
        }
    
    @require_auth
    def put(self):
        """Update user profile"""
        data = request.get_json()
        
        conn = sqlite3.connect(self.manager.db_path)
        cursor = conn.cursor()
        
        # Update allowed fields
        allowed_fields = ['full_name', 'phone']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in data:
                updates.append(f'{field} = ?')
                values.append(data[field])
        
        if updates:
            values.append(request.user_id)
            cursor.execute(f'''
                UPDATE users SET {', '.join(updates)} WHERE id = ?
            ''', values)
            
            conn.commit()
        
        conn.close()
        
        return {'status': 'updated'}


class MobileDeviceResource(Resource):
    def __init__(self, manager):
        self.manager = manager
    
    @require_auth
    def post(self):
        """Update device information"""
        data = request.get_json()
        data['device_id'] = request.device_id
        
        self.manager.register_device(data, request.user_id)
        
        return {'status': 'updated'}


class MobileSyncResource(Resource):
    def __init__(self, manager):
        self.manager = manager
    
    @require_auth
    def get(self):
        """Get sync data"""
        last_sync = request.args.get('last_sync')
        sync_data = self.manager.get_sync_data(request.device_id, last_sync)
        
        return {
            'sync_data': sync_data,
            'timestamp': datetime.now().isoformat()
        }
    
    @require_auth
    def post(self):
        """Mark items as synced"""
        data = request.get_json()
        sync_items = data.get('synced_items', [])
        
        self.manager.mark_synced(request.device_id, sync_items)
        
        return {'status': 'synced'}