#!/usr/bin/env python3
"""
Database Migration Script for College Kiosk Enterprise Upgrade
This script updates your existing database to support all enterprise features
"""

import sqlite3
import os
from datetime import datetime

# Database path
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'college.db'))

def add_column_if_not_exists(cursor, table, column, definition):
    """Add column to table if it doesn't exist"""
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        if column not in existing_columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            print(f"✅ Added column '{column}' to table '{table}'")
            return True
        else:
            print(f"ℹ️  Column '{column}' already exists in table '{table}'")
            return False
    except Exception as e:
        print(f"❌ Error adding column '{column}' to table '{table}': {str(e)}")
        return False

def migrate_database():
    """Migrate database to enterprise schema"""
    print("🚀 Starting College Kiosk Enterprise Database Migration...")
    print(f"📍 Database path: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print("❌ Database file not found! Please run the application first to create the database.")
        return False
    
    # Backup database
    backup_path = f"{DB_PATH}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"💾 Database backed up to: {backup_path}")
    except Exception as e:
        print(f"⚠️  Could not create backup: {str(e)}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("\n📊 Migrating existing tables...")
        
        # Update users table for enterprise features
        add_column_if_not_exists(cursor, 'users', 'last_login', 'TEXT')
        add_column_if_not_exists(cursor, 'users', 'login_attempts', 'INTEGER DEFAULT 0')
        add_column_if_not_exists(cursor, 'users', 'is_locked', 'INTEGER DEFAULT 0')
        add_column_if_not_exists(cursor, 'users', 'phone', 'TEXT')
        add_column_if_not_exists(cursor, 'users', 'preferences', 'TEXT')
        add_column_if_not_exists(cursor, 'users', 'loyalty_points', 'INTEGER DEFAULT 0')
        
        # Update menu table for advanced inventory
        add_column_if_not_exists(cursor, 'menu', 'description', 'TEXT')
        add_column_if_not_exists(cursor, 'menu', 'ingredients', 'TEXT')
        add_column_if_not_exists(cursor, 'menu', 'nutrition_info', 'TEXT')
        add_column_if_not_exists(cursor, 'menu', 'allergens', 'TEXT')
        add_column_if_not_exists(cursor, 'menu', 'preparation_time', 'INTEGER DEFAULT 15')
        add_column_if_not_exists(cursor, 'menu', 'popularity_score', 'REAL DEFAULT 0')
        add_column_if_not_exists(cursor, 'menu', 'cost_price', 'REAL DEFAULT 0')
        add_column_if_not_exists(cursor, 'menu', 'profit_margin', 'REAL DEFAULT 0')
        
        # Update orders table for enhanced tracking
        add_column_if_not_exists(cursor, 'orders', 'delivery_address', 'TEXT')
        add_column_if_not_exists(cursor, 'orders', 'phone_number', 'TEXT')
        add_column_if_not_exists(cursor, 'orders', 'payment_method', 'TEXT')
        add_column_if_not_exists(cursor, 'orders', 'payment_status', 'TEXT DEFAULT "pending"')
        add_column_if_not_exists(cursor, 'orders', 'estimated_time', 'INTEGER')
        add_column_if_not_exists(cursor, 'orders', 'actual_time', 'INTEGER')
        add_column_if_not_exists(cursor, 'orders', 'rating', 'INTEGER')
        add_column_if_not_exists(cursor, 'orders', 'feedback', 'TEXT')
        add_column_if_not_exists(cursor, 'orders', 'loyalty_points_earned', 'INTEGER DEFAULT 0')
        add_column_if_not_exists(cursor, 'orders', 'discount_applied', 'REAL DEFAULT 0')
        
        print("\n🏗️  Creating new enterprise tables...")
        
        # Security logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT,
                user_email TEXT,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created security_logs table")
        
        # Financial records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_type TEXT,
                amount REAL,
                description TEXT,
                category TEXT,
                reference_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT
            )
        ''')
        print("✅ Created financial_records table")
        
        # Inventory transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                transaction_type TEXT,
                quantity INTEGER,
                unit_price REAL,
                supplier TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT
            )
        ''')
        print("✅ Created inventory_transactions table")
        
        # Suppliers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                contact_person TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                payment_terms TEXT,
                rating REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Created suppliers table")
        
        # Customer interactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_email TEXT,
                interaction_type TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT
            )
        ''')
        print("✅ Created customer_interactions table")
        
        # Performance metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_type TEXT,
                metric_value REAL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                details TEXT
            )
        ''')
        print("✅ Created performance_metrics table")
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_email TEXT,
                title TEXT,
                message TEXT,
                type TEXT,
                status TEXT DEFAULT 'unread',
                priority TEXT DEFAULT 'normal',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                read_at TEXT
            )
        ''')
        print("✅ Created notifications table")
        
        # System settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE,
                value TEXT,
                description TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_by TEXT
            )
        ''')
        print("✅ Created system_settings table")
        
        print("\n⚙️  Inserting default settings...")
        
        # Insert default settings
        default_settings = [
            ('smtp_host', 'smtp.gmail.com', 'SMTP server host'),
            ('smtp_port', '587', 'SMTP server port'),
            ('smtp_username', '', 'SMTP username'),
            ('smtp_password', '', 'SMTP password'),
            ('payment_gateway', 'stripe', 'Payment gateway provider'),
            ('tax_rate', '0.18', 'Tax rate percentage'),
            ('delivery_charge', '50', 'Delivery charge amount'),
            ('min_order_amount', '100', 'Minimum order amount'),
            ('loyalty_points_rate', '0.1', 'Loyalty points per rupee spent'),
            ('auto_reorder_threshold', '10', 'Automatic reorder threshold'),
            ('business_hours_start', '08:00', 'Business hours start time'),
            ('business_hours_end', '22:00', 'Business hours end time')
        ]
        
        for key, value, description in default_settings:
            cursor.execute('''
                INSERT OR IGNORE INTO system_settings (key, value, description)
                VALUES (?, ?, ?)
            ''', (key, value, description))
        
        print(f"✅ Inserted {len(default_settings)} default settings")
        
        # Add some sample data for demo
        print("\n📝 Adding sample enterprise data...")
        
        # Sample supplier
        cursor.execute('''
            INSERT OR IGNORE INTO suppliers (name, contact_person, email, phone, address, payment_terms, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('Fresh Foods Pvt Ltd', 'Rajesh Kumar', 'rajesh@freshfoods.com', '+91-9876543210', 
              'Mumbai, Maharashtra', '30 days', 4.5))
        
        # Sample financial record
        cursor.execute('''
            INSERT OR IGNORE INTO financial_records (transaction_type, amount, description, category, created_by)
            VALUES (?, ?, ?, ?, ?)
        ''', ('expense', 15000, 'Monthly ingredients purchase', 'inventory', 'admin@college.edu'))
        
        print("✅ Added sample enterprise data")
        
        conn.commit()
        print("\n🎉 Database migration completed successfully!")
        print("\n📋 Migration Summary:")
        print("   ✅ Enhanced users table with security features")
        print("   ✅ Enhanced menu table with advanced inventory")
        print("   ✅ Enhanced orders table with detailed tracking")
        print("   ✅ Added 8 new enterprise tables")
        print("   ✅ Inserted default system settings")
        print("   ✅ Added sample enterprise data")
        print("\n🚀 Your database is now ready for enterprise features!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()