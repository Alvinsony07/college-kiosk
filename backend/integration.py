"""
Integration & Automation Module
Features: Third-party integrations, webhooks, automated workflows, email automation
"""

import sqlite3
import json
import requests
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from datetime import datetime, timedelta
import threading
import time
import hashlib
import hmac
import uuid
from urllib.parse import urlencode
import logging

class IntegrationManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.active_workflows = {}
        
        self.init_integration_tables()
    
    def init_integration_tables(self):
        """Initialize integration tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Third-party integrations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS integrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL, -- payment, email, sms, analytics, accounting
                provider TEXT NOT NULL, -- razorpay, mailgun, twilio, google_analytics, quickbooks
                config TEXT, -- JSON configuration
                credentials TEXT, -- Encrypted credentials
                is_active INTEGER DEFAULT 1,
                test_mode INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_used TEXT,
                error_count INTEGER DEFAULT 0,
                last_error TEXT
            )
        ''')
        
        # Webhooks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                events TEXT, -- JSON array of events
                secret_key TEXT,
                is_active INTEGER DEFAULT 1,
                retry_count INTEGER DEFAULT 3,
                timeout_seconds INTEGER DEFAULT 30,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_triggered TEXT,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0
            )
        ''')
        
        # Webhook logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhook_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                webhook_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT, -- JSON payload
                response_status INTEGER,
                response_body TEXT,
                attempt_number INTEGER DEFAULT 1,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                success INTEGER DEFAULT 0,
                error_message TEXT,
                FOREIGN KEY (webhook_id) REFERENCES webhooks (id)
            )
        ''')
        
        # Automated workflows
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                trigger_type TEXT NOT NULL, -- order_created, user_registered, payment_received, etc.
                trigger_conditions TEXT, -- JSON conditions
                actions TEXT, -- JSON array of actions
                is_active INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_executed TEXT,
                execution_count INTEGER DEFAULT 0,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Workflow executions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workflow_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id INTEGER NOT NULL,
                trigger_data TEXT, -- JSON data that triggered the workflow
                status TEXT DEFAULT 'pending', -- pending, running, completed, failed
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                actions_completed INTEGER DEFAULT 0,
                total_actions INTEGER DEFAULT 0,
                error_message TEXT,
                execution_log TEXT, -- JSON log of each action
                FOREIGN KEY (workflow_id) REFERENCES workflows (id)
            )
        ''')
        
        # Email templates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                body_html TEXT,
                body_text TEXT,
                template_type TEXT, -- order_confirmation, welcome, password_reset, etc.
                variables TEXT, -- JSON array of available variables
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_modified TEXT
            )
        ''')
        
        # Email queue
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                to_email TEXT NOT NULL,
                subject TEXT NOT NULL,
                body_html TEXT,
                body_text TEXT,
                template_id INTEGER,
                template_data TEXT, -- JSON data for template variables
                status TEXT DEFAULT 'pending', -- pending, sent, failed
                priority INTEGER DEFAULT 5, -- 1 (highest) to 10 (lowest)
                scheduled_at TEXT,
                sent_at TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (template_id) REFERENCES email_templates (id)
            )
        ''')
        
        # API logs for third-party calls
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                integration_id INTEGER,
                endpoint TEXT NOT NULL,
                method TEXT DEFAULT 'POST',
                request_headers TEXT,
                request_body TEXT,
                response_status INTEGER,
                response_headers TEXT,
                response_body TEXT,
                duration_ms REAL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                success INTEGER DEFAULT 0,
                FOREIGN KEY (integration_id) REFERENCES integrations (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Insert default templates and workflows
        self.insert_default_integration_data()
    
    def insert_default_integration_data(self):
        """Insert default email templates and workflows"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Default email templates
        default_templates = [
            (
                'Order Confirmation',
                'Your Order #{order_id} has been confirmed!',
                '''
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #FF5722;">Order Confirmation</h2>
                    <p>Dear {customer_name},</p>
                    <p>Thank you for your order! Your order #{order_id} has been confirmed.</p>
                    
                    <h3>Order Details:</h3>
                    <table style="border-collapse: collapse; width: 100%;">
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Order ID:</strong></td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{order_id}</td>
                        </tr>
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Total Amount:</strong></td>
                            <td style="border: 1px solid #ddd; padding: 8px;">₹{total_amount}</td>
                        </tr>
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 8px;"><strong>Status:</strong></td>
                            <td style="border: 1px solid #ddd; padding: 8px;">{status}</td>
                        </tr>
                    </table>
                    
                    <p>We'll notify you when your order is ready!</p>
                    <p>Best regards,<br>College Kiosk Team</p>
                </body>
                </html>
                ''',
                'Dear {customer_name}, Your order #{order_id} for ₹{total_amount} has been confirmed. Status: {status}. Best regards, College Kiosk Team',
                'order_confirmation',
                '["customer_name", "order_id", "total_amount", "status", "items"]'
            ),
            (
                'Welcome Email',
                'Welcome to College Kiosk!',
                '''
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #FF5722;">Welcome to College Kiosk!</h2>
                    <p>Dear {full_name},</p>
                    <p>Welcome to College Kiosk! We're excited to have you as part of our community.</p>
                    
                    <h3>Your Account Details:</h3>
                    <ul>
                        <li><strong>Username:</strong> {username}</li>
                        <li><strong>Email:</strong> {email}</li>
                        <li><strong>Registration Date:</strong> {created_at}</li>
                    </ul>
                    
                    <p>You can now browse our menu and place orders online!</p>
                    <p>Best regards,<br>College Kiosk Team</p>
                </body>
                </html>
                ''',
                'Welcome to College Kiosk, {full_name}! Your account {username} has been created. Start ordering now!',
                'welcome',
                '["username", "email", "full_name", "created_at"]'
            ),
            (
                'Low Stock Alert',
                'Low Stock Alert - {item_name}',
                '''
                <html>
                <body style="font-family: Arial, sans-serif;">
                    <h2 style="color: #FF5722;">Low Stock Alert</h2>
                    <p>This is an automated alert to inform you that the following item is running low on stock:</p>
                    
                    <h3>Item Details:</h3>
                    <ul>
                        <li><strong>Item:</strong> {item_name}</li>
                        <li><strong>Category:</strong> {category}</li>
                        <li><strong>Current Stock:</strong> {current_stock}</li>
                        <li><strong>Minimum Stock Level:</strong> {min_stock}</li>
                    </ul>
                    
                    <p>Please restock this item as soon as possible.</p>
                    <p>Best regards,<br>Inventory Management System</p>
                </body>
                </html>
                ''',
                'Low Stock Alert: {item_name} ({category}) - Current: {current_stock}, Minimum: {min_stock}',
                'low_stock_alert',
                '["item_name", "category", "current_stock", "min_stock"]'
            )
        ]
        
        for template in default_templates:
            cursor.execute('''
                INSERT OR IGNORE INTO email_templates 
                (name, subject, body_html, body_text, template_type, variables)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', template)
        
        # Default workflows
        default_workflows = [
            (
                'Order Confirmation Workflow',
                'Send confirmation email when order is created',
                'order_created',
                '{}',  # No additional conditions
                json.dumps([
                    {
                        'type': 'send_email',
                        'template': 'order_confirmation',
                        'to': '{customer_email}',
                        'data': {
                            'customer_name': '{customer_name}',
                            'order_id': '{order_id}',
                            'total_amount': '{total_price}',
                            'status': '{status}'
                        }
                    }
                ])
            ),
            (
                'Welcome New User',
                'Send welcome email to new users',
                'user_registered',
                '{}',
                json.dumps([
                    {
                        'type': 'send_email',
                        'template': 'welcome',
                        'to': '{email}',
                        'data': {
                            'username': '{username}',
                            'email': '{email}',
                            'full_name': '{full_name}',
                            'created_at': '{created_at}'
                        }
                    }
                ])
            ),
            (
                'Low Stock Notification',
                'Send alert when inventory is low',
                'low_stock_detected',
                json.dumps({'stock_level': '<10'}),
                json.dumps([
                    {
                        'type': 'send_email',
                        'template': 'low_stock_alert',
                        'to': 'admin@collegekiosk.com',
                        'data': {
                            'item_name': '{item_name}',
                            'category': '{category}',
                            'current_stock': '{current_stock}',
                            'min_stock': '{min_stock}'
                        }
                    }
                ])
            )
        ]
        
        for workflow in default_workflows:
            cursor.execute('''
                INSERT OR IGNORE INTO workflows 
                (name, description, trigger_type, trigger_conditions, actions)
                VALUES (?, ?, ?, ?, ?)
            ''', workflow)
        
        conn.commit()
        conn.close()
    
    def add_integration(self, name, integration_type, provider, config, credentials=None):
        """Add new third-party integration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Encrypt credentials (simplified - in production use proper encryption)
        encrypted_credentials = None
        if credentials:
            encrypted_credentials = json.dumps(credentials)  # Should be properly encrypted
        
        cursor.execute('''
            INSERT INTO integrations (name, type, provider, config, credentials)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, integration_type, provider, json.dumps(config), encrypted_credentials))
        
        integration_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return integration_id
    
    def get_integration(self, integration_id):
        """Get integration configuration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM integrations WHERE id = ? AND is_active = 1', (integration_id,))
        integration = cursor.fetchone()
        conn.close()
        
        if integration:
            return {
                'id': integration[0],
                'name': integration[1],
                'type': integration[2],
                'provider': integration[3],
                'config': json.loads(integration[4]) if integration[4] else {},
                'credentials': json.loads(integration[5]) if integration[5] else {},
                'test_mode': bool(integration[7])
            }
        return None
    
    def trigger_webhook(self, event_type, data):
        """Trigger webhooks for specific event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get active webhooks for this event
        cursor.execute('''
            SELECT id, url, secret_key, retry_count, timeout_seconds
            FROM webhooks 
            WHERE is_active = 1 AND (events LIKE ? OR events LIKE ?)
        ''', (f'%"{event_type}"%', '%"*"%'))  # Support wildcard events
        
        webhooks = cursor.fetchall()
        conn.close()
        
        # Send webhooks in background threads
        for webhook in webhooks:
            webhook_id, url, secret_key, retry_count, timeout = webhook
            
            thread = threading.Thread(
                target=self._send_webhook,
                args=(webhook_id, url, event_type, data, secret_key, retry_count, timeout)
            )
            thread.daemon = True
            thread.start()
    
    def _send_webhook(self, webhook_id, url, event_type, data, secret_key=None, retry_count=3, timeout=30):
        """Send webhook request"""
        payload = {
            'event': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'CollegeKiosk-Webhook/1.0'
        }
        
        # Add signature if secret key provided
        if secret_key:
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                secret_key.encode(),
                payload_str.encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = f'sha256={signature}'
        
        # Attempt to send webhook with retries
        for attempt in range(1, retry_count + 1):
            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=timeout
                )
                
                # Log webhook attempt
                self._log_webhook_attempt(
                    webhook_id, event_type, payload, response.status_code,
                    response.text, attempt, response.status_code == 200
                )
                
                if response.status_code == 200:
                    # Update success count
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE webhooks 
                        SET success_count = success_count + 1, last_triggered = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (webhook_id,))
                    conn.commit()
                    conn.close()
                    break
                
            except Exception as e:
                # Log failed attempt
                self._log_webhook_attempt(
                    webhook_id, event_type, payload, 0, str(e), attempt, False
                )
                
                if attempt == retry_count:
                    # Update failure count
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE webhooks 
                        SET failure_count = failure_count + 1
                        WHERE id = ?
                    ''', (webhook_id,))
                    conn.commit()
                    conn.close()
                
                # Wait before retry (exponential backoff)
                if attempt < retry_count:
                    time.sleep(2 ** attempt)
    
    def _log_webhook_attempt(self, webhook_id, event_type, payload, status_code, response_body, attempt, success):
        """Log webhook attempt"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO webhook_logs 
            (webhook_id, event_type, payload, response_status, response_body, 
             attempt_number, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            webhook_id, event_type, json.dumps(payload), status_code,
            response_body, attempt, 1 if success else 0,
            None if success else response_body
        ))
        
        conn.commit()
        conn.close()
    
    def trigger_workflow(self, trigger_type, trigger_data):
        """Trigger automated workflows"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get active workflows for this trigger
        cursor.execute('''
            SELECT id, name, trigger_conditions, actions
            FROM workflows 
            WHERE trigger_type = ? AND is_active = 1
        ''', (trigger_type,))
        
        workflows = cursor.fetchall()
        
        for workflow in workflows:
            workflow_id, name, conditions_json, actions_json = workflow
            
            # Check if conditions are met
            conditions = json.loads(conditions_json) if conditions_json else {}
            if self._check_workflow_conditions(conditions, trigger_data):
                # Execute workflow in background
                thread = threading.Thread(
                    target=self._execute_workflow,
                    args=(workflow_id, trigger_data)
                )
                thread.daemon = True
                thread.start()
        
        conn.close()
    
    def _check_workflow_conditions(self, conditions, data):
        """Check if workflow conditions are met"""
        if not conditions:
            return True
        
        # Simple condition checking (can be extended)
        for key, condition in conditions.items():
            if key not in data:
                return False
            
            value = data[key]
            
            if isinstance(condition, str):
                if condition.startswith('<'):
                    threshold = float(condition[1:])
                    if not (isinstance(value, (int, float)) and value < threshold):
                        return False
                elif condition.startswith('>'):
                    threshold = float(condition[1:])
                    if not (isinstance(value, (int, float)) and value > threshold):
                        return False
                elif condition != str(value):
                    return False
            elif condition != value:
                return False
        
        return True
    
    def _execute_workflow(self, workflow_id, trigger_data):
        """Execute workflow actions"""
        # Start workflow execution
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO workflow_executions (workflow_id, trigger_data, status)
            VALUES (?, ?, ?)
        ''', (workflow_id, json.dumps(trigger_data), 'running'))
        
        execution_id = cursor.lastrowid
        
        # Get workflow actions
        cursor.execute('SELECT actions FROM workflows WHERE id = ?', (workflow_id,))
        actions_json = cursor.fetchone()[0]
        actions = json.loads(actions_json)
        
        # Update total actions count
        cursor.execute('''
            UPDATE workflow_executions 
            SET total_actions = ? WHERE id = ?
        ''', (len(actions), execution_id))
        
        conn.commit()
        
        execution_log = []
        actions_completed = 0
        
        try:
            for i, action in enumerate(actions):
                action_result = self._execute_workflow_action(action, trigger_data)
                execution_log.append({
                    'action_index': i,
                    'action_type': action.get('type'),
                    'status': 'success' if action_result['success'] else 'failed',
                    'message': action_result.get('message'),
                    'timestamp': datetime.now().isoformat()
                })
                
                if action_result['success']:
                    actions_completed += 1
                
                # Update progress
                cursor.execute('''
                    UPDATE workflow_executions 
                    SET actions_completed = ?, execution_log = ?
                    WHERE id = ?
                ''', (actions_completed, json.dumps(execution_log), execution_id))
                conn.commit()
            
            # Mark as completed
            cursor.execute('''
                UPDATE workflow_executions 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (execution_id,))
            
            # Update workflow execution count
            cursor.execute('''
                UPDATE workflows 
                SET execution_count = execution_count + 1, last_executed = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (workflow_id,))
            
        except Exception as e:
            # Mark as failed
            cursor.execute('''
                UPDATE workflow_executions 
                SET status = 'failed', completed_at = CURRENT_TIMESTAMP, 
                    error_message = ?, execution_log = ?
                WHERE id = ?
            ''', (str(e), json.dumps(execution_log), execution_id))
            
            self.logger.error(f"Workflow {workflow_id} execution failed: {e}")
        
        conn.commit()
        conn.close()
    
    def _execute_workflow_action(self, action, trigger_data):
        """Execute individual workflow action"""
        action_type = action.get('type')
        
        try:
            if action_type == 'send_email':
                return self._execute_email_action(action, trigger_data)
            elif action_type == 'webhook':
                return self._execute_webhook_action(action, trigger_data)
            elif action_type == 'update_record':
                return self._execute_update_action(action, trigger_data)
            elif action_type == 'create_notification':
                return self._execute_notification_action(action, trigger_data)
            else:
                return {'success': False, 'message': f'Unknown action type: {action_type}'}
        
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def _execute_email_action(self, action, trigger_data):
        """Execute email sending action"""
        template_name = action.get('template')
        to_email = self._substitute_variables(action.get('to'), trigger_data)
        template_data = action.get('data', {})
        
        # Substitute variables in template data
        for key, value in template_data.items():
            template_data[key] = self._substitute_variables(str(value), trigger_data)
        
        # Queue email
        email_id = self.queue_email(
            to_email=to_email,
            template_name=template_name,
            template_data=template_data
        )
        
        return {'success': True, 'message': f'Email queued with ID {email_id}'}
    
    def _execute_webhook_action(self, action, trigger_data):
        """Execute webhook action"""
        url = action.get('url')
        event_type = action.get('event', 'workflow_triggered')
        
        # Send webhook
        self.trigger_webhook(event_type, {
            'workflow_action': True,
            'trigger_data': trigger_data,
            'action_data': action.get('data', {})
        })
        
        return {'success': True, 'message': 'Webhook triggered'}
    
    def _execute_update_action(self, action, trigger_data):
        """Execute record update action"""
        table = action.get('table')
        update_data = action.get('data', {})
        conditions = action.get('conditions', {})
        
        # Build update query (simplified)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clauses = []
        values = []
        
        for key, value in update_data.items():
            set_clauses.append(f'{key} = ?')
            values.append(self._substitute_variables(str(value), trigger_data))
        
        where_clauses = []
        for key, value in conditions.items():
            where_clauses.append(f'{key} = ?')
            values.append(self._substitute_variables(str(value), trigger_data))
        
        query = f"UPDATE {table} SET {', '.join(set_clauses)}"
        if where_clauses:
            query += f" WHERE {' AND '.join(where_clauses)}"
        
        cursor.execute(query, values)
        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return {'success': True, 'message': f'Updated {rows_affected} records'}
    
    def _execute_notification_action(self, action, trigger_data):
        """Execute notification creation action"""
        # This would integrate with your notification system
        title = self._substitute_variables(action.get('title'), trigger_data)
        message = self._substitute_variables(action.get('message'), trigger_data)
        
        # Create notification (placeholder)
        return {'success': True, 'message': f'Notification created: {title}'}
    
    def _substitute_variables(self, template, data):
        """Substitute variables in template string"""
        if not isinstance(template, str):
            return template
        
        result = template
        for key, value in data.items():
            placeholder = f'{{{key}}}'
            result = result.replace(placeholder, str(value))
        
        return result
    
    def queue_email(self, to_email, subject=None, body_html=None, body_text=None, 
                   template_name=None, template_data=None, priority=5, scheduled_at=None):
        """Queue email for sending"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        template_id = None
        if template_name:
            cursor.execute('SELECT id FROM email_templates WHERE name = ? AND is_active = 1', 
                          (template_name,))
            template_result = cursor.fetchone()
            if template_result:
                template_id = template_result[0]
        
        cursor.execute('''
            INSERT INTO email_queue 
            (to_email, subject, body_html, body_text, template_id, template_data, 
             priority, scheduled_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            to_email, subject, body_html, body_text, template_id,
            json.dumps(template_data) if template_data else None,
            priority, scheduled_at
        ))
        
        email_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return email_id
    
    def process_email_queue(self, batch_size=10):
        """Process queued emails"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get pending emails
        cursor.execute('''
            SELECT eq.*, et.subject as template_subject, et.body_html, et.body_text
            FROM email_queue eq
            LEFT JOIN email_templates et ON eq.template_id = et.id
            WHERE eq.status = 'pending' 
            AND (eq.scheduled_at IS NULL OR eq.scheduled_at <= CURRENT_TIMESTAMP)
            AND eq.retry_count < eq.max_retries
            ORDER BY eq.priority ASC, eq.created_at ASC
            LIMIT ?
        ''', (batch_size,))
        
        emails = cursor.fetchall()
        
        for email in emails:
            try:
                email_id = email[0]
                to_email = email[1]
                subject = email[2] or email[13]  # Use template subject if not provided
                body_html = email[3] or email[14]
                body_text = email[4] or email[15]
                template_data = json.loads(email[6]) if email[6] else {}
                
                # Substitute variables in email content
                if template_data:
                    subject = self._substitute_variables(subject, template_data)
                    if body_html:
                        body_html = self._substitute_variables(body_html, template_data)
                    if body_text:
                        body_text = self._substitute_variables(body_text, template_data)
                
                # Send email
                self._send_email(to_email, subject, body_html, body_text)
                
                # Mark as sent
                cursor.execute('''
                    UPDATE email_queue 
                    SET status = 'sent', sent_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (email_id,))
                
            except Exception as e:
                # Update retry count and error
                cursor.execute('''
                    UPDATE email_queue 
                    SET retry_count = retry_count + 1, error_message = ?
                    WHERE id = ?
                ''', (str(e), email[0]))
                
                # Mark as failed if max retries reached
                if email[10] + 1 >= email[11]:  # retry_count + 1 >= max_retries
                    cursor.execute('''
                        UPDATE email_queue SET status = 'failed' WHERE id = ?
                    ''', (email[0],))
                
                self.logger.error(f"Failed to send email {email[0]}: {e}")
        
        conn.commit()
        conn.close()
    
    def _send_email(self, to_email, subject, body_html=None, body_text=None):
        """Send email via SMTP"""
        # This would use your SMTP configuration
        # Placeholder implementation
        self.logger.info(f"Sending email to {to_email}: {subject}")
        
        # In a real implementation, you would:
        # 1. Get SMTP configuration from integrations
        # 2. Create MimeMultipart message
        # 3. Add HTML and text parts
        # 4. Send via smtplib or email service API
        
        pass  # Placeholder
    
    def get_integration_stats(self):
        """Get integration statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Integration counts
        cursor.execute('''
            SELECT type, COUNT(*) as count, SUM(is_active) as active_count
            FROM integrations
            GROUP BY type
        ''')
        integration_stats = cursor.fetchall()
        
        # Webhook stats
        cursor.execute('''
            SELECT COUNT(*) as total, SUM(is_active) as active,
                   SUM(success_count) as total_success, SUM(failure_count) as total_failures
            FROM webhooks
        ''')
        webhook_stats = cursor.fetchone()
        
        # Email queue stats
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM email_queue
            GROUP BY status
        ''')
        email_stats = cursor.fetchall()
        
        # Workflow stats
        cursor.execute('''
            SELECT COUNT(*) as total, SUM(is_active) as active,
                   SUM(execution_count) as total_executions
            FROM workflows
        ''')
        workflow_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            'integrations': [
                {'type': stat[0], 'total': stat[1], 'active': stat[2]}
                for stat in integration_stats
            ],
            'webhooks': {
                'total': webhook_stats[0],
                'active': webhook_stats[1],
                'total_success': webhook_stats[2],
                'total_failures': webhook_stats[3]
            },
            'email_queue': [
                {'status': stat[0], 'count': stat[1]}
                for stat in email_stats
            ],
            'workflows': {
                'total': workflow_stats[0],
                'active': workflow_stats[1],
                'total_executions': workflow_stats[2]
            }
        }