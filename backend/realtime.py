"""
Real-time Features Module using WebSocket
Features: Live order updates, real-time notifications, live dashboard, chat support
"""

from flask import Flask, request, session, emit
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect
import sqlite3
import json
from datetime import datetime, timedelta
import uuid
import logging
from functools import wraps
import jwt
from collections import defaultdict

class RealTimeManager:
    def __init__(self, app, db_path, secret_key):
        self.app = app
        self.db_path = db_path
        self.secret_key = secret_key
        
        # Initialize SocketIO
        self.socketio = SocketIO(
            app, 
            cors_allowed_origins="*",
            logger=True,
            engineio_logger=True,
            async_mode='threading'
        )
        
        # Track connected clients
        self.connected_clients = defaultdict(dict)  # {user_id: {session_id: socket_info}}
        self.admin_clients = set()  # Set of admin session IDs
        self.room_clients = defaultdict(set)  # {room_name: {session_ids}}
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize real-time tables
        self.init_realtime_tables()
        
        # Register event handlers
        self.register_event_handlers()
    
    def init_realtime_tables(self):
        """Initialize real-time related tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Real-time notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS realtime_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                type TEXT DEFAULT 'info', -- info, success, warning, error
                data TEXT, -- JSON additional data
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                delivered INTEGER DEFAULT 0,
                read INTEGER DEFAULT 0,
                read_at TEXT,
                expires_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Chat messages for customer support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT UNIQUE NOT NULL,
                chat_session_id TEXT NOT NULL,
                sender_id INTEGER,
                sender_type TEXT DEFAULT 'customer', -- customer, staff, admin
                message TEXT NOT NULL,
                message_type TEXT DEFAULT 'text', -- text, image, file, system
                file_url TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0,
                FOREIGN KEY (sender_id) REFERENCES users (id)
            )
        ''')
        
        # Chat sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                assigned_staff_id INTEGER,
                status TEXT DEFAULT 'active', -- active, closed, waiting
                priority TEXT DEFAULT 'normal', -- low, normal, high, urgent
                subject TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                closed_at TEXT,
                last_message_at TEXT,
                message_count INTEGER DEFAULT 0,
                satisfaction_rating INTEGER, -- 1-5 stars
                FOREIGN KEY (customer_id) REFERENCES users (id),
                FOREIGN KEY (assigned_staff_id) REFERENCES users (id)
            )
        ''')
        
        # Live dashboard metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS live_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_key TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metric_type TEXT DEFAULT 'counter', -- counter, gauge, histogram
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT
            )
        ''')
        
        # Active sessions tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                socket_id TEXT,
                user_type TEXT, -- customer, staff, admin
                connected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_activity TEXT DEFAULT CURRENT_TIMESTAMP,
                ip_address TEXT,
                user_agent TEXT,
                status TEXT DEFAULT 'active', -- active, idle, disconnected
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_event_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect(auth):
            """Handle client connection"""
            try:
                # Authenticate user
                token = auth.get('token') if auth else None
                user_data = self.authenticate_websocket_token(token)
                
                if user_data:
                    user_id = user_data['user_id']
                    user_type = user_data['user_type']
                    
                    # Store session info
                    session['user_id'] = user_id
                    session['user_type'] = user_type
                    session['authenticated'] = True
                    
                    # Track connection
                    session_id = request.sid
                    self.connected_clients[user_id][session_id] = {
                        'socket_id': session_id,
                        'user_type': user_type,
                        'connected_at': datetime.now().isoformat(),
                        'ip_address': request.environ.get('REMOTE_ADDR')
                    }
                    
                    # Join user-specific room
                    join_room(f'user_{user_id}')
                    
                    # Join role-based rooms
                    if user_type in ['admin', 'staff']:
                        join_room('staff_room')
                        self.admin_clients.add(session_id)
                    
                    if user_type == 'admin':
                        join_room('admin_room')
                    
                    # Log connection
                    self.log_connection(user_id, session_id, 'connected')
                    
                    # Send welcome message
                    emit('connection_status', {
                        'status': 'connected',
                        'user_id': user_id,
                        'message': 'Successfully connected to real-time updates'
                    })
                    
                    # Send pending notifications
                    self.send_pending_notifications(user_id)
                    
                    self.logger.info(f"User {user_id} connected with session {session_id}")
                    
                else:
                    emit('connection_status', {
                        'status': 'error',
                        'message': 'Authentication failed'
                    })
                    disconnect()
                    
            except Exception as e:
                self.logger.error(f"Connection error: {e}")
                emit('connection_status', {
                    'status': 'error', 
                    'message': 'Connection failed'
                })
                disconnect()
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            user_id = session.get('user_id')
            session_id = request.sid
            
            if user_id:
                # Remove from tracking
                if user_id in self.connected_clients:
                    self.connected_clients[user_id].pop(session_id, None)
                    if not self.connected_clients[user_id]:
                        del self.connected_clients[user_id]
                
                # Remove from admin clients if applicable
                self.admin_clients.discard(session_id)
                
                # Log disconnection
                self.log_connection(user_id, session_id, 'disconnected')
                
                self.logger.info(f"User {user_id} disconnected from session {session_id}")
        
        @self.socketio.on('join_room')
        def handle_join_room(data):
            """Handle room joining"""
            if not session.get('authenticated'):
                emit('error', {'message': 'Not authenticated'})
                return
            
            room_name = data.get('room')
            if room_name:
                join_room(room_name)
                self.room_clients[room_name].add(request.sid)
                emit('room_status', {'room': room_name, 'status': 'joined'})
        
        @self.socketio.on('leave_room')
        def handle_leave_room(data):
            """Handle room leaving"""
            room_name = data.get('room')
            if room_name:
                leave_room(room_name)
                self.room_clients[room_name].discard(request.sid)
                emit('room_status', {'room': room_name, 'status': 'left'})
        
        @self.socketio.on('send_message')
        def handle_send_message(data):
            """Handle chat message sending"""
            if not session.get('authenticated'):
                emit('error', {'message': 'Not authenticated'})
                return
            
            user_id = session.get('user_id')
            chat_session_id = data.get('chat_session_id')
            message = data.get('message')
            message_type = data.get('type', 'text')
            
            if not all([chat_session_id, message]):
                emit('error', {'message': 'Missing required fields'})
                return
            
            # Save message
            message_id = self.save_chat_message(
                chat_session_id, user_id, message, message_type
            )
            
            # Broadcast to chat participants
            self.broadcast_chat_message(chat_session_id, {
                'message_id': message_id,
                'chat_session_id': chat_session_id,
                'sender_id': user_id,
                'message': message,
                'type': message_type,
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('mark_notification_read')
        def handle_mark_notification_read(data):
            """Mark notification as read"""
            if not session.get('authenticated'):
                emit('error', {'message': 'Not authenticated'})
                return
            
            user_id = session.get('user_id')
            notification_id = data.get('notification_id')
            
            if notification_id:
                self.mark_notification_read(user_id, notification_id)
                emit('notification_read', {'notification_id': notification_id})
        
        @self.socketio.on('request_dashboard_data')
        def handle_dashboard_request(data):
            """Handle dashboard data request"""
            if not session.get('authenticated'):
                emit('error', {'message': 'Not authenticated'})
                return
            
            user_type = session.get('user_type')
            if user_type not in ['admin', 'staff']:
                emit('error', {'message': 'Access denied'})
                return
            
            # Send current dashboard data
            dashboard_data = self.get_live_dashboard_data()
            emit('dashboard_data', dashboard_data)
        
        @self.socketio.on('heartbeat')  
        def handle_heartbeat():
            """Handle client heartbeat"""
            if session.get('authenticated'):
                user_id = session.get('user_id')
                self.update_last_activity(user_id, request.sid)
                emit('heartbeat_ack', {'timestamp': datetime.now().isoformat()})
    
    def authenticate_websocket_token(self, token):
        """Authenticate WebSocket connection token"""
        if not token:
            return None
        
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            if not user_id:
                return None
            
            # Get user info from database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, role FROM users 
                WHERE id = ? AND is_active = 1
            ''', (user_id,))
            
            user = cursor.fetchone()
            conn.close()
            
            if user:
                return {
                    'user_id': user[0],
                    'username': user[1],
                    'user_type': user[2]
                }
            
            return None
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            self.logger.error(f"Token authentication error: {e}")
            return None
    
    def send_notification(self, user_id=None, title=None, message=None, 
                         notification_type='info', data=None, room=None):
        """Send real-time notification"""
        notification_id = str(uuid.uuid4())
        
        # Save notification to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO realtime_notifications 
            (notification_id, user_id, title, message, type, data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (notification_id, user_id, title, message, notification_type, 
              json.dumps(data) if data else None))
        
        conn.commit()
        conn.close()
        
        # Prepare notification payload
        notification_payload = {
            'notification_id': notification_id,
            'title': title,
            'message': message,
            'type': notification_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Send to specific user
        if user_id:
            self.socketio.emit('notification', notification_payload, 
                             room=f'user_{user_id}')
        
        # Send to room
        if room:
            self.socketio.emit('notification', notification_payload, room=room)
        
        return notification_id
    
    def send_order_update(self, order_id, status, customer_email=None):
        """Send real-time order status update"""
        # Get order details
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, customer_name, customer_email, total_price 
            FROM orders WHERE id = ?
        ''', (order_id,))
        
        order = cursor.fetchone()
        
        if order and customer_email:
            # Get customer user ID
            cursor.execute('SELECT id FROM users WHERE email = ?', (customer_email,))
            customer = cursor.fetchone()
            
            if customer:
                customer_id = customer[0]
                
                # Send notification to customer
                self.send_notification(
                    user_id=customer_id,
                    title='Order Update',
                    message=f'Your order #{order_id} is now {status}',
                    notification_type='info',
                    data={
                        'order_id': order_id,
                        'status': status,
                        'total_price': order[3]
                    }
                )
                
                # Send detailed update to customer room
                self.socketio.emit('order_update', {
                    'order_id': order_id,
                    'status': status,
                    'customer_name': order[1],
                    'total_price': order[3],
                    'timestamp': datetime.now().isoformat()
                }, room=f'user_{customer_id}')
        
        # Send update to staff/admin room
        self.socketio.emit('staff_order_update', {
            'order_id': order_id,
            'status': status,
            'customer_name': order[1] if order else 'Unknown',
            'customer_email': customer_email,
            'total_price': order[3] if order else 0,
            'timestamp': datetime.now().isoformat()
        }, room='staff_room')
        
        conn.close()
    
    def send_inventory_alert(self, item_name, current_stock, min_stock):
        """Send real-time inventory alert"""
        self.send_notification(
            title='Low Stock Alert',
            message=f'{item_name} is running low (Current: {current_stock}, Min: {min_stock})',
            notification_type='warning',
            data={
                'item_name': item_name,
                'current_stock': current_stock,
                'min_stock': min_stock,
                'alert_type': 'low_stock'
            },
            room='staff_room'
        )
    
    def create_chat_session(self, customer_id, subject=None):
        """Create new chat session"""
        session_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_sessions (session_id, customer_id, subject)
            VALUES (?, ?, ?)
        ''', (session_id, customer_id, subject))
        
        conn.commit()
        conn.close()
        
        # Notify staff about new chat session
        self.send_notification(
            title='New Chat Session',
            message=f'Customer has started a new chat session',
            notification_type='info',
            data={
                'chat_session_id': session_id,
                'customer_id': customer_id,
                'subject': subject
            },
            room='staff_room'
        )
        
        return session_id
    
    def save_chat_message(self, chat_session_id, sender_id, message, message_type='text'):
        """Save chat message to database"""
        message_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get sender type
        cursor.execute('SELECT role FROM users WHERE id = ?', (sender_id,))
        sender_role = cursor.fetchone()
        sender_type = sender_role[0] if sender_role else 'customer'
        
        cursor.execute('''
            INSERT INTO chat_messages 
            (message_id, chat_session_id, sender_id, sender_type, message, message_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (message_id, chat_session_id, sender_id, sender_type, message, message_type))
        
        # Update chat session
        cursor.execute('''
            UPDATE chat_sessions 
            SET last_message_at = CURRENT_TIMESTAMP, message_count = message_count + 1
            WHERE session_id = ?
        ''', (chat_session_id,))
        
        conn.commit()
        conn.close()
        
        return message_id
    
    def broadcast_chat_message(self, chat_session_id, message_data):
        """Broadcast chat message to relevant users"""
        # Get chat session participants
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT customer_id, assigned_staff_id FROM chat_sessions 
            WHERE session_id = ?
        ''', (chat_session_id,))
        
        session_info = cursor.fetchone()
        conn.close()
        
        if session_info:
            customer_id, staff_id = session_info
            
            # Send to customer
            if customer_id:
                self.socketio.emit('chat_message', message_data, 
                                 room=f'user_{customer_id}')
            
            # Send to assigned staff
            if staff_id:
                self.socketio.emit('chat_message', message_data, 
                                 room=f'user_{staff_id}')
            
            # Send to all staff if no specific staff assigned
            if not staff_id:
                self.socketio.emit('chat_message', message_data, room='staff_room')
    
    def send_pending_notifications(self, user_id):
        """Send pending notifications to newly connected user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT notification_id, title, message, type, data, created_at
            FROM realtime_notifications
            WHERE user_id = ? AND delivered = 0 
            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ORDER BY created_at DESC
            LIMIT 10
        ''', (user_id,))
        
        notifications = cursor.fetchall()
        
        for notification in notifications:
            self.socketio.emit('notification', {
                'notification_id': notification[0],
                'title': notification[1],
                'message': notification[2],
                'type': notification[3],
                'data': json.loads(notification[4]) if notification[4] else None,
                'timestamp': notification[5]
            }, room=f'user_{user_id}')
            
            # Mark as delivered
            cursor.execute('''
                UPDATE realtime_notifications SET delivered = 1 WHERE notification_id = ?
            ''', (notification[0],))
        
        conn.commit()
        conn.close()
    
    def mark_notification_read(self, user_id, notification_id):
        """Mark notification as read"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE realtime_notifications 
            SET read = 1, read_at = CURRENT_TIMESTAMP
            WHERE notification_id = ? AND user_id = ?
        ''', (notification_id, user_id))
        
        conn.commit()
        conn.close()
    
    def get_live_dashboard_data(self):
        """Get live dashboard data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current metrics
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        
        # Today's orders
        cursor.execute('''
            SELECT COUNT(*), SUM(total_price), status
            FROM orders 
            WHERE DATE(created_at) = ?
            GROUP BY status
        ''', (today,))
        
        order_stats = cursor.fetchall()
        
        # Active users (connected in last 5 minutes)
        five_minutes_ago = (now - timedelta(minutes=5)).isoformat()
        cursor.execute('''
            SELECT COUNT(DISTINCT user_id) FROM active_sessions
            WHERE last_activity > ? AND status = 'active'
        ''', (five_minutes_ago,))
        
        active_users = cursor.fetchone()[0]
        
        # Pending orders
        cursor.execute('''
            SELECT COUNT(*) FROM orders WHERE status = 'Pending'
        ''')
        pending_orders = cursor.fetchone()[0]
        
        # Low stock items
        cursor.execute('''
            SELECT COUNT(*) FROM inventory_items 
            WHERE current_stock <= minimum_stock
        ''')
        low_stock_items = cursor.fetchone()[0] if cursor.fetchone() else 0
        
        conn.close()
        
        return {
            'timestamp': now.isoformat(),
            'order_stats': [
                {'status': stat[2], 'count': stat[0], 'revenue': stat[1]}
                for stat in order_stats
            ],
            'active_users': active_users,
            'pending_orders': pending_orders,
            'low_stock_items': low_stock_items,
            'connected_clients': len(self.connected_clients),
            'admin_clients': len(self.admin_clients)
        }
    
    def update_live_metric(self, metric_key, value, metric_type='counter'):
        """Update live metric"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Set expiration time (1 hour)
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
        
        cursor.execute('''
            INSERT INTO live_metrics (metric_key, metric_value, metric_type, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (metric_key, value, metric_type, expires_at))
        
        conn.commit()
        conn.close()
        
        # Broadcast to admin dashboard
        self.socketio.emit('metric_update', {
            'metric_key': metric_key,
            'value': value,
            'type': metric_type,
            'timestamp': datetime.now().isoformat()
        }, room='admin_room')
    
    def log_connection(self, user_id, session_id, action):
        """Log connection/disconnection"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if action == 'connected':
            cursor.execute('''
                INSERT INTO active_sessions 
                (session_id, user_id, socket_id, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_id, user_id, session_id, 
                  request.environ.get('REMOTE_ADDR'),
                  request.environ.get('HTTP_USER_AGENT', '')))
        
        elif action == 'disconnected':
            cursor.execute('''
                UPDATE active_sessions 
                SET status = 'disconnected' 
                WHERE session_id = ?
            ''', (session_id,))
        
        conn.commit()
        conn.close()
    
    def update_last_activity(self, user_id, session_id):
        """Update last activity timestamp"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE active_sessions 
            SET last_activity = CURRENT_TIMESTAMP 
            WHERE session_id = ? AND user_id = ?
        ''', (session_id, user_id))
        
        conn.commit()
        conn.close()
    
    def cleanup_expired_data(self):
        """Clean up expired data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clean expired notifications
        cursor.execute('''
            DELETE FROM realtime_notifications 
            WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
        ''')
        
        # Clean expired metrics
        cursor.execute('''
            DELETE FROM live_metrics 
            WHERE expires_at IS NOT NULL AND expires_at < CURRENT_TIMESTAMP
        ''')
        
        # Clean old active sessions (older than 24 hours)
        yesterday = (datetime.now() - timedelta(hours=24)).isoformat()
        cursor.execute('''
            DELETE FROM active_sessions 
            WHERE last_activity < ?
        ''', (yesterday,))
        
        conn.commit()
        conn.close()
    
    def get_connection_stats(self):
        """Get real-time connection statistics"""
        return {
            'total_connected': sum(len(sessions) for sessions in self.connected_clients.values()),
            'unique_users': len(self.connected_clients),
            'admin_sessions': len(self.admin_clients),
            'rooms': {room: len(clients) for room, clients in self.room_clients.items()},
            'timestamp': datetime.now().isoformat()
        }