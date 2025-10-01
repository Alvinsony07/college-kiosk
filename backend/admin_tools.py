"""
Advanced Admin Tools Module
Features: Role-based permissions, bulk operations, configuration management, audit trails
"""

import sqlite3
import json
import csv
import io
from datetime import datetime, timedelta
import hashlib
import uuid
from functools import wraps
import logging

class AdminToolsManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_admin_tables()
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
    
    def init_admin_tables(self):
        """Initialize admin tools tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Roles and permissions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT UNIQUE NOT NULL,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Permissions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permission_name TEXT UNIQUE NOT NULL,
                category TEXT, -- user_management, menu_management, orders, reports, system
                description TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        # Role permissions mapping
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_id INTEGER NOT NULL,
                permission_id INTEGER NOT NULL,
                granted_by INTEGER,
                granted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (role_id) REFERENCES roles (id),
                FOREIGN KEY (permission_id) REFERENCES permissions (id),
                FOREIGN KEY (granted_by) REFERENCES users (id),
                UNIQUE(role_id, permission_id)
            )
        ''')
        
        # User roles mapping
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                assigned_by INTEGER,
                assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (role_id) REFERENCES roles (id),
                FOREIGN KEY (assigned_by) REFERENCES users (id)
            )
        ''')
        
        # System configuration
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT,
                data_type TEXT DEFAULT 'string', -- string, integer, float, boolean, json
                category TEXT, -- general, security, performance, features
                description TEXT,
                is_editable INTEGER DEFAULT 1,
                requires_restart INTEGER DEFAULT 0,
                last_modified_by INTEGER,
                last_modified_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (last_modified_by) REFERENCES users (id)
            )
        ''')
        
        # Audit trail
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_trail (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                action TEXT NOT NULL,
                entity_type TEXT, -- user, menu, order, role, config
                entity_id INTEGER,
                old_values TEXT, -- JSON
                new_values TEXT, -- JSON
                ip_address TEXT,
                user_agent TEXT,
                session_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Bulk operations log
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bulk_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_id TEXT UNIQUE NOT NULL,
                operation_type TEXT NOT NULL, -- import, export, update, delete
                entity_type TEXT, -- users, menu_items, orders
                status TEXT DEFAULT 'pending', -- pending, running, completed, failed
                initiated_by INTEGER,
                initiated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                total_records INTEGER DEFAULT 0,
                processed_records INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0,
                errors TEXT, -- JSON array of error messages
                file_path TEXT,
                notes TEXT,
                FOREIGN KEY (initiated_by) REFERENCES users (id)
            )
        ''')
        
        # Scheduled tasks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                task_type TEXT NOT NULL, -- backup, report, cleanup, notification
                schedule_expression TEXT, -- cron-like expression
                is_active INTEGER DEFAULT 1,
                last_run TEXT,
                next_run TEXT,
                run_count INTEGER DEFAULT 0,
                parameters TEXT, -- JSON
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Insert default data
        self.insert_default_admin_data()
    
    def insert_default_admin_data(self):
        """Insert default roles and permissions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Default roles
        default_roles = [
            ('super_admin', 'Super Administrator with full access'),
            ('admin', 'Administrator with most privileges'),
            ('manager', 'Manager with operational privileges'),
            ('staff', 'Staff member with limited access'),
            ('viewer', 'Read-only access to reports')
        ]
        
        for role_name, description in default_roles:
            cursor.execute('''
                INSERT OR IGNORE INTO roles (role_name, description)
                VALUES (?, ?)
            ''', (role_name, description))
        
        # Default permissions
        default_permissions = [
            # User Management
            ('user.create', 'user_management', 'Create new users'),
            ('user.read', 'user_management', 'View user information'),
            ('user.update', 'user_management', 'Update user information'),
            ('user.delete', 'user_management', 'Delete users'),
            ('user.list', 'user_management', 'List all users'),
            
            # Menu Management
            ('menu.create', 'menu_management', 'Create menu items'),
            ('menu.read', 'menu_management', 'View menu items'),
            ('menu.update', 'menu_management', 'Update menu items'),
            ('menu.delete', 'menu_management', 'Delete menu items'),
            ('menu.list', 'menu_management', 'List all menu items'),
            
            # Order Management
            ('order.create', 'orders', 'Create orders'),
            ('order.read', 'orders', 'View orders'),
            ('order.update', 'orders', 'Update order status'),
            ('order.delete', 'orders', 'Cancel orders'),
            ('order.list', 'orders', 'List all orders'),
            
            # Reports
            ('report.sales', 'reports', 'View sales reports'),
            ('report.inventory', 'reports', 'View inventory reports'),
            ('report.users', 'reports', 'View user reports'),
            ('report.financial', 'reports', 'View financial reports'),
            ('report.export', 'reports', 'Export reports'),
            
            # System Administration
            ('system.config', 'system', 'Manage system configuration'),
            ('system.backup', 'system', 'Create backups'),
            ('system.logs', 'system', 'View system logs'),
            ('system.monitoring', 'system', 'View system monitoring'),
            ('system.maintenance', 'system', 'Perform system maintenance'),
            
            # Role Management
            ('role.create', 'role_management', 'Create roles'),
            ('role.read', 'role_management', 'View roles'),
            ('role.update', 'role_management', 'Update roles'),
            ('role.delete', 'role_management', 'Delete roles'),
            ('role.assign', 'role_management', 'Assign roles to users'),
            
            # Bulk Operations
            ('bulk.import', 'bulk_operations', 'Import data in bulk'),
            ('bulk.export', 'bulk_operations', 'Export data in bulk'),
            ('bulk.update', 'bulk_operations', 'Update data in bulk'),
            ('bulk.delete', 'bulk_operations', 'Delete data in bulk'),
        ]
        
        for permission, category, description in default_permissions:
            cursor.execute('''
                INSERT OR IGNORE INTO permissions (permission_name, category, description)
                VALUES (?, ?, ?)
            ''', (permission, category, description))
        
        # Default system configuration
        default_configs = [
            ('app_name', 'College Kiosk', 'string', 'general', 'Application name'),
            ('app_version', '2.0.0', 'string', 'general', 'Application version'),
            ('max_login_attempts', '5', 'integer', 'security', 'Maximum login attempts before lockout'),
            ('session_timeout', '3600', 'integer', 'security', 'Session timeout in seconds'),
            ('password_min_length', '8', 'integer', 'security', 'Minimum password length'),
            ('enable_2fa', 'false', 'boolean', 'security', 'Enable two-factor authentication'),
            ('backup_retention_days', '30', 'integer', 'general', 'Backup retention period in days'),
            ('enable_email_notifications', 'true', 'boolean', 'features', 'Enable email notifications'),
            ('default_order_timeout', '1800', 'integer', 'general', 'Default order timeout in seconds'),
            ('enable_inventory_alerts', 'true', 'boolean', 'features', 'Enable low inventory alerts'),
            ('cache_ttl', '3600', 'integer', 'performance', 'Cache time-to-live in seconds'),
            ('max_file_upload_size', '10485760', 'integer', 'general', 'Maximum file upload size in bytes'),
        ]
        
        for key, value, data_type, category, description in default_configs:
            cursor.execute('''
                INSERT OR IGNORE INTO system_config 
                (config_key, config_value, data_type, category, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (key, value, data_type, category, description))
        
        conn.commit()
        conn.close()
        
        # Assign permissions to default roles
        self.setup_default_role_permissions()
    
    def setup_default_role_permissions(self):
        """Setup default permissions for roles"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get role IDs
        cursor.execute("SELECT id, role_name FROM roles")
        roles = {name: role_id for role_id, name in cursor.fetchall()}
        
        # Get permission IDs
        cursor.execute("SELECT id, permission_name FROM permissions")
        permissions = {name: perm_id for perm_id, name in cursor.fetchall()}
        
        # Super admin gets all permissions
        if 'super_admin' in roles:
            for perm_id in permissions.values():
                cursor.execute('''
                    INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                    VALUES (?, ?)
                ''', (roles['super_admin'], perm_id))
        
        # Admin gets most permissions except sensitive system operations
        admin_permissions = [p for p in permissions.keys() 
                           if not p.startswith('role.') and p != 'system.maintenance']
        if 'admin' in roles:
            for perm_name in admin_permissions:
                cursor.execute('''
                    INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                    VALUES (?, ?)
                ''', (roles['admin'], permissions[perm_name]))
        
        # Manager gets operational permissions
        manager_permissions = [
            'menu.read', 'menu.update', 'order.read', 'order.update', 'order.list',
            'report.sales', 'report.inventory', 'user.read', 'user.list'
        ]
        if 'manager' in roles:
            for perm_name in manager_permissions:
                if perm_name in permissions:
                    cursor.execute('''
                        INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                        VALUES (?, ?)
                    ''', (roles['manager'], permissions[perm_name]))
        
        # Staff gets basic permissions
        staff_permissions = [
            'menu.read', 'order.create', 'order.read', 'order.update'
        ]
        if 'staff' in roles:
            for perm_name in staff_permissions:
                if perm_name in permissions:
                    cursor.execute('''
                        INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                        VALUES (?, ?)
                    ''', (roles['staff'], permissions[perm_name]))
        
        # Viewer gets read-only permissions
        viewer_permissions = [
            'menu.read', 'order.read', 'report.sales', 'report.inventory'
        ]
        if 'viewer' in roles:
            for perm_name in viewer_permissions:
                if perm_name in permissions:
                    cursor.execute('''
                        INSERT OR IGNORE INTO role_permissions (role_id, permission_id)
                        VALUES (?, ?)
                    ''', (roles['viewer'], permissions[perm_name]))
        
        conn.commit()
        conn.close()
    
    def log_audit_trail(self, user_id, action, entity_type, entity_id=None, 
                       old_values=None, new_values=None, ip_address=None, 
                       user_agent=None, session_id=None):
        """Log action to audit trail"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_trail 
            (user_id, action, entity_type, entity_id, old_values, new_values, 
             ip_address, user_agent, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, action, entity_type, entity_id,
            json.dumps(old_values) if old_values else None,
            json.dumps(new_values) if new_values else None,
            ip_address, user_agent, session_id
        ))
        
        conn.commit()
        conn.close()
    
    def check_permission(self, user_id, permission_name):
        """Check if user has specific permission"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM user_roles ur
            JOIN role_permissions rp ON ur.role_id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE ur.user_id = ? AND p.permission_name = ? 
            AND ur.is_active = 1 AND p.is_active = 1
            AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
        ''', (user_id, permission_name))
        
        has_permission = cursor.fetchone()[0] > 0
        conn.close()
        return has_permission
    
    def get_user_permissions(self, user_id):
        """Get all permissions for a user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT p.permission_name, p.category, p.description
            FROM user_roles ur
            JOIN role_permissions rp ON ur.role_id = rp.role_id
            JOIN permissions p ON rp.permission_id = p.id
            WHERE ur.user_id = ? AND ur.is_active = 1 AND p.is_active = 1
            AND (ur.expires_at IS NULL OR ur.expires_at > CURRENT_TIMESTAMP)
            ORDER BY p.category, p.permission_name
        ''', (user_id,))
        
        permissions = cursor.fetchall()
        conn.close()
        
        # Group by category
        grouped = {}
        for perm_name, category, description in permissions:
            if category not in grouped:
                grouped[category] = []
            grouped[category].append({
                'name': perm_name,
                'description': description
            })
        
        return grouped
    
    def assign_role_to_user(self, user_id, role_id, assigned_by, expires_at=None):
        """Assign role to user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_roles (user_id, role_id, assigned_by, expires_at)
            VALUES (?, ?, ?, ?)
        ''', (user_id, role_id, assigned_by, expires_at))
        
        conn.commit()
        conn.close()
        
        # Log audit trail
        self.log_audit_trail(
            assigned_by, 'role_assigned', 'user', user_id,
            None, {'role_id': role_id, 'expires_at': expires_at}
        )
    
    def revoke_role_from_user(self, user_id, role_id, revoked_by):
        """Revoke role from user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_roles SET is_active = 0
            WHERE user_id = ? AND role_id = ? AND is_active = 1
        ''', (user_id, role_id))
        
        conn.commit()
        conn.close()
        
        # Log audit trail
        self.log_audit_trail(
            revoked_by, 'role_revoked', 'user', user_id,
            {'role_id': role_id}, None
        )
    
    def bulk_import_users(self, csv_data, imported_by, password_policy=None):
        """Bulk import users from CSV"""
        operation_id = str(uuid.uuid4())
        
        # Start bulk operation
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO bulk_operations 
            (operation_id, operation_type, entity_type, initiated_by, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (operation_id, 'import', 'users', imported_by, 'running'))
        
        bulk_op_id = cursor.lastrowid
        conn.commit()
        
        # Process CSV data
        errors = []
        success_count = 0
        processed_count = 0
        
        try:
            csv_file = io.StringIO(csv_data)
            reader = csv.DictReader(csv_file)
            total_records = sum(1 for _ in reader)
            csv_file.seek(0)
            reader = csv.DictReader(csv_file)
            
            # Update total records count
            cursor.execute('''
                UPDATE bulk_operations SET total_records = ? WHERE id = ?
            ''', (total_records, bulk_op_id))
            conn.commit()
            
            for row in reader:
                processed_count += 1
                
                try:
                    # Validate required fields
                    required_fields = ['email', 'username', 'password']
                    for field in required_fields:
                        if not row.get(field):
                            raise ValueError(f"Missing required field: {field}")
                    
                    # Create user
                    hashed_password = hashlib.sha256(row['password'].encode()).hexdigest()
                    
                    cursor.execute('''
                        INSERT INTO users (username, email, password, full_name, phone, role)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        row['username'],
                        row['email'],
                        hashed_password,
                        row.get('full_name', ''),
                        row.get('phone', ''),
                        row.get('role', 'customer')
                    ))
                    
                    success_count += 1
                    
                    # Update progress
                    cursor.execute('''
                        UPDATE bulk_operations 
                        SET processed_records = ?, success_count = ?
                        WHERE id = ?
                    ''', (processed_count, success_count, bulk_op_id))
                    
                except Exception as e:
                    errors.append(f"Row {processed_count}: {str(e)}")
                    
                    cursor.execute('''
                        UPDATE bulk_operations 
                        SET processed_records = ?, error_count = error_count + 1
                        WHERE id = ?
                    ''', (processed_count, bulk_op_id))
                
                conn.commit()
            
            # Mark operation as completed
            cursor.execute('''
                UPDATE bulk_operations 
                SET status = ?, completed_at = ?, errors = ?
                WHERE id = ?
            ''', ('completed', datetime.now().isoformat(), json.dumps(errors), bulk_op_id))
            
        except Exception as e:
            # Mark operation as failed
            cursor.execute('''
                UPDATE bulk_operations 
                SET status = ?, completed_at = ?, errors = ?
                WHERE id = ?
            ''', ('failed', datetime.now().isoformat(), json.dumps([str(e)]), bulk_op_id))
        
        conn.commit()
        conn.close()
        
        return {
            'operation_id': operation_id,
            'total_records': processed_count,
            'success_count': success_count,
            'error_count': len(errors),
            'errors': errors
        }
    
    def bulk_export_data(self, entity_type, exported_by, filters=None):
        """Bulk export data to CSV"""
        operation_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Start bulk operation
        cursor.execute('''
            INSERT INTO bulk_operations 
            (operation_id, operation_type, entity_type, initiated_by, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (operation_id, 'export', entity_type, exported_by, 'running'))
        
        bulk_op_id = cursor.lastrowid
        conn.commit()
        
        try:
            csv_data = io.StringIO()
            
            if entity_type == 'users':
                cursor.execute('''
                    SELECT id, username, email, full_name, phone, role, 
                           is_active, created_at, last_login
                    FROM users
                    ORDER BY created_at DESC
                ''')
                
                fieldnames = ['id', 'username', 'email', 'full_name', 'phone', 
                             'role', 'is_active', 'created_at', 'last_login']
                
            elif entity_type == 'menu_items':
                cursor.execute('''
                    SELECT id, name, description, price, category, image_url,
                           is_available, created_at
                    FROM menu
                    ORDER BY category, name
                ''')
                
                fieldnames = ['id', 'name', 'description', 'price', 'category',
                             'image_url', 'is_available', 'created_at']
            
            elif entity_type == 'orders':
                cursor.execute('''
                    SELECT id, customer_name, customer_email, items, total_price,
                           status, created_at, updated_at
                    FROM orders
                    ORDER BY created_at DESC
                ''')
                
                fieldnames = ['id', 'customer_name', 'customer_email', 'items',
                             'total_price', 'status', 'created_at', 'updated_at']
            
            else:
                raise ValueError(f"Unsupported entity type: {entity_type}")
            
            data = cursor.fetchall()
            
            writer = csv.writer(csv_data)
            writer.writerow(fieldnames)
            writer.writerows(data)
            
            # Mark operation as completed
            cursor.execute('''
                UPDATE bulk_operations 
                SET status = ?, completed_at = ?, total_records = ?, success_count = ?
                WHERE id = ?
            ''', ('completed', datetime.now().isoformat(), len(data), len(data), bulk_op_id))
            
            conn.commit()
            conn.close()
            
            return {
                'operation_id': operation_id,
                'csv_data': csv_data.getvalue(),
                'record_count': len(data)
            }
            
        except Exception as e:
            cursor.execute('''
                UPDATE bulk_operations 
                SET status = ?, completed_at = ?, errors = ?
                WHERE id = ?
            ''', ('failed', datetime.now().isoformat(), json.dumps([str(e)]), bulk_op_id))
            
            conn.commit()
            conn.close()
            
            raise
    
    def get_system_config(self, category=None):
        """Get system configuration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if category:
            cursor.execute('''
                SELECT config_key, config_value, data_type, description, is_editable
                FROM system_config
                WHERE category = ?
                ORDER BY config_key
            ''', (category,))
        else:
            cursor.execute('''
                SELECT config_key, config_value, data_type, category, description, is_editable
                FROM system_config
                ORDER BY category, config_key
            ''')
        
        configs = cursor.fetchall()
        conn.close()
        
        result = {}
        for config in configs:
            key = config[0]
            value = config[1]
            data_type = config[2]
            
            # Convert value based on data type
            if data_type == 'integer':
                value = int(value) if value else 0
            elif data_type == 'float':
                value = float(value) if value else 0.0
            elif data_type == 'boolean':
                value = value.lower() in ('true', '1', 'yes') if value else False
            elif data_type == 'json':
                value = json.loads(value) if value else {}
            
            if category:
                result[key] = {
                    'value': value,
                    'description': config[3],
                    'editable': bool(config[4])
                }
            else:
                if config[3] not in result:
                    result[config[3]] = {}
                result[config[3]][key] = {
                    'value': value,
                    'description': config[4],
                    'editable': bool(config[5])
                }
        
        return result
    
    def update_system_config(self, config_key, config_value, updated_by):
        """Update system configuration"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current value for audit
        cursor.execute('''
            SELECT config_value, data_type FROM system_config 
            WHERE config_key = ? AND is_editable = 1
        ''', (config_key,))
        
        current = cursor.fetchone()
        if not current:
            conn.close()
            raise ValueError(f"Configuration key '{config_key}' not found or not editable")
        
        old_value = current[0]
        data_type = current[1]
        
        # Validate and convert value based on data type
        if data_type == 'integer':
            config_value = str(int(config_value))
        elif data_type == 'float':
            config_value = str(float(config_value))
        elif data_type == 'boolean':
            config_value = 'true' if str(config_value).lower() in ('true', '1', 'yes') else 'false'
        elif data_type == 'json':
            # Validate JSON
            json.loads(config_value)
        
        # Update configuration
        cursor.execute('''
            UPDATE system_config 
            SET config_value = ?, last_modified_by = ?, last_modified_at = ?
            WHERE config_key = ?
        ''', (config_value, updated_by, datetime.now().isoformat(), config_key))
        
        conn.commit()
        conn.close()
        
        # Log audit trail
        self.log_audit_trail(
            updated_by, 'config_updated', 'system_config', None,
            {'key': config_key, 'value': old_value},
            {'key': config_key, 'value': config_value}
        )
    
    def get_audit_trail(self, filters=None, limit=100):
        """Get audit trail with optional filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = '''
            SELECT at.*, u.username
            FROM audit_trail at
            LEFT JOIN users u ON at.user_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if filters:
            if filters.get('user_id'):
                query += ' AND at.user_id = ?'
                params.append(filters['user_id'])
            
            if filters.get('action'):
                query += ' AND at.action = ?'
                params.append(filters['action'])
            
            if filters.get('entity_type'):
                query += ' AND at.entity_type = ?'
                params.append(filters['entity_type'])
            
            if filters.get('start_date'):
                query += ' AND at.timestamp >= ?'
                params.append(filters['start_date'])
            
            if filters.get('end_date'):
                query += ' AND at.timestamp <= ?'
                params.append(filters['end_date'])
        
        query += ' ORDER BY at.timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        trail = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': row[0],
                'timestamp': row[1],
                'user_id': row[2],
                'username': row[12],
                'action': row[3],
                'entity_type': row[4],
                'entity_id': row[5],
                'old_values': json.loads(row[6]) if row[6] else None,
                'new_values': json.loads(row[7]) if row[7] else None,
                'ip_address': row[8]
            }
            for row in trail
        ]
    
    def get_bulk_operation_status(self, operation_id):
        """Get status of bulk operation"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM bulk_operations WHERE operation_id = ?
        ''', (operation_id,))
        
        operation = cursor.fetchone()
        conn.close()
        
        if not operation:
            return None
        
        return {
            'operation_id': operation[1],
            'type': operation[2],
            'entity_type': operation[3],
            'status': operation[4],
            'initiated_at': operation[6],
            'completed_at': operation[7],
            'total_records': operation[8],
            'processed_records': operation[9],
            'success_count': operation[10],
            'error_count': operation[11],
            'errors': json.loads(operation[12]) if operation[12] else []
        }

def require_permission(permission_name):
    """Decorator to check user permission"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # This would need to be integrated with your auth system
            # For now, it's a placeholder
            user_id = kwargs.get('user_id') or getattr(func, 'current_user_id', None)
            if not user_id:
                raise PermissionError("User not authenticated")
            
            admin_tools = AdminToolsManager('college.db')  # This should be injected
            if not admin_tools.check_permission(user_id, permission_name):
                raise PermissionError(f"Permission denied: {permission_name}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator