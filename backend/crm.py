"""
Customer Relationship Management (CRM) System
Features: Customer profiles, segmentation, loyalty programs, communication tools
"""

import sqlite3
import json
from datetime import datetime, timedelta
from flask import current_app
import hashlib
import random
import string
from collections import defaultdict
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import pandas as pd

class CRMManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_crm_tables()
    
    def init_crm_tables(self):
        """Initialize CRM-related tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Customer profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                email TEXT UNIQUE,
                first_name TEXT,
                last_name TEXT,
                phone TEXT,
                date_of_birth TEXT,
                gender TEXT,
                department TEXT,
                year_of_study TEXT,
                dietary_preferences TEXT, -- JSON array
                allergies TEXT, -- JSON array
                favorite_items TEXT, -- JSON array of menu item IDs
                notes TEXT,
                profile_image TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Customer segments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                criteria TEXT, -- JSON criteria for automatic segmentation
                color TEXT DEFAULT '#3B82F6',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Customer segment assignments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_segment_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                segment_id INTEGER,
                assigned_at TEXT DEFAULT CURRENT_TIMESTAMP,
                assigned_by INTEGER, -- user ID who assigned
                FOREIGN KEY (customer_id) REFERENCES customer_profiles (id),
                FOREIGN KEY (segment_id) REFERENCES customer_segments (id),
                FOREIGN KEY (assigned_by) REFERENCES users (id)
            )
        ''')
        
        # Loyalty program table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loyalty_program (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                points_per_rupee REAL DEFAULT 1.0,
                welcome_bonus INTEGER DEFAULT 0,
                birthday_bonus INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                terms_conditions TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Customer loyalty points
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_loyalty_points (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                current_points INTEGER DEFAULT 0,
                lifetime_points INTEGER DEFAULT 0,
                tier_level TEXT DEFAULT 'Bronze', -- Bronze, Silver, Gold, Platinum
                tier_benefits TEXT, -- JSON
                joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customer_profiles (id)
            )
        ''')
        
        # Points transactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS points_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                transaction_type TEXT, -- earned, redeemed, expired, adjusted
                points INTEGER,
                order_id INTEGER,
                description TEXT,
                reference_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customer_profiles (id),
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        
        # Customer feedback/reviews
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customer_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                order_id INTEGER,
                menu_item_id INTEGER,
                rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                review TEXT,
                feedback_type TEXT, -- order, item, service, general
                is_anonymous INTEGER DEFAULT 0,
                is_approved INTEGER DEFAULT 1,
                response TEXT, -- Admin response
                responded_by INTEGER,
                responded_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customer_profiles (id),
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (menu_item_id) REFERENCES menu (id),
                FOREIGN KEY (responded_by) REFERENCES users (id)
            )
        ''')
        
        # Support tickets
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS support_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                subject TEXT NOT NULL,
                description TEXT NOT NULL,
                priority TEXT DEFAULT 'medium', -- low, medium, high, urgent
                status TEXT DEFAULT 'open', -- open, in_progress, resolved, closed
                category TEXT, -- complaint, suggestion, question, refund
                order_id INTEGER,
                assigned_to INTEGER,
                resolution TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT,
                FOREIGN KEY (customer_id) REFERENCES customer_profiles (id),
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (assigned_to) REFERENCES users (id)
            )
        ''')
        
        # Communication logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS communication_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                communication_type TEXT, -- email, sms, push, in_app
                template_id INTEGER,
                subject TEXT,
                content TEXT,
                status TEXT DEFAULT 'sent', -- sent, delivered, failed, opened
                sent_by INTEGER,
                sent_at TEXT DEFAULT CURRENT_TIMESTAMP,
                delivered_at TEXT,
                opened_at TEXT,
                FOREIGN KEY (customer_id) REFERENCES customer_profiles (id),
                FOREIGN KEY (sent_by) REFERENCES users (id)
            )
        ''')
        
        # Email templates
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                subject TEXT NOT NULL,
                html_content TEXT NOT NULL,
                text_content TEXT,
                template_type TEXT, -- welcome, order_confirmation, marketing, etc.
                variables TEXT, -- JSON array of template variables
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Marketing campaigns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS marketing_campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                campaign_type TEXT, -- email, sms, push
                template_id INTEGER,
                target_segments TEXT, -- JSON array of segment IDs
                target_criteria TEXT, -- JSON criteria for targeting
                schedule_type TEXT DEFAULT 'immediate', -- immediate, scheduled, recurring
                scheduled_for TEXT,
                recurring_pattern TEXT, -- JSON for recurring campaigns
                status TEXT DEFAULT 'draft', -- draft, scheduled, running, completed, paused
                total_recipients INTEGER DEFAULT 0,
                sent_count INTEGER DEFAULT 0,
                delivered_count INTEGER DEFAULT 0,
                opened_count INTEGER DEFAULT 0,
                clicked_count INTEGER DEFAULT 0,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                launched_at TEXT,
                completed_at TEXT,
                FOREIGN KEY (template_id) REFERENCES email_templates (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Insert default data
        self.insert_default_crm_data()
    
    def insert_default_crm_data(self):
        """Insert default CRM data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Default customer segments
        default_segments = [
            ('New Customers', 'Recently registered customers', '{"orders_count": {"operator": "<=", "value": 1}}', '#10B981'),
            ('Regular Customers', 'Customers with 2-10 orders', '{"orders_count": {"operator": "between", "value": [2, 10]}}', '#3B82F6'),
            ('VIP Customers', 'High-value customers with 10+ orders', '{"orders_count": {"operator": ">", "value": 10}}', '#F59E0B'),
            ('Inactive Customers', 'No orders in last 30 days', '{"last_order_days": {"operator": ">", "value": 30}}', '#EF4444'),
            ('High Spenders', 'Customers with high average order value', '{"avg_order_value": {"operator": ">", "value": 500}}', '#8B5CF6'),
        ]
        
        for name, desc, criteria, color in default_segments:
            cursor.execute('''
                INSERT OR IGNORE INTO customer_segments (name, description, criteria, color)
                VALUES (?, ?, ?, ?)
            ''', (name, desc, criteria, color))
        
        # Default loyalty program
        cursor.execute('''
            INSERT OR IGNORE INTO loyalty_program 
            (name, description, points_per_rupee, welcome_bonus, birthday_bonus, terms_conditions)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            'College Kiosk Rewards',
            'Earn points on every purchase and redeem for discounts',
            1.0, 100, 50,
            'Points are earned on successful orders. 100 points = ₹10. Points expire after 1 year of inactivity.'
        ))
        
        # Default email templates
        default_templates = [
            ('Welcome Email', 'Welcome to College Kiosk!', 
             '''<h1>Welcome {{first_name}}!</h1>
                <p>Thank you for joining College Kiosk. We're excited to serve you delicious food!</p>
                <p>As a welcome bonus, you've earned {{welcome_bonus}} loyalty points.</p>''',
             'Welcome {{first_name}}! Thank you for joining College Kiosk. You earned {{welcome_bonus}} points!',
             'welcome', '["first_name", "welcome_bonus"]'),
            
            ('Order Confirmation', 'Your Order is Confirmed - #{{order_id}}',
             '''<h2>Order Confirmation</h2>
                <p>Hi {{customer_name}},</p>
                <p>Your order #{{order_id}} has been confirmed and is being prepared.</p>
                <p><strong>Total: ₹{{total_amount}}</strong></p>
                <p>Estimated ready time: {{ready_time}}</p>''',
             'Hi {{customer_name}}, your order #{{order_id}} is confirmed. Total: ₹{{total_amount}}',
             'order_confirmation', '["customer_name", "order_id", "total_amount", "ready_time"]'),
            
            ('Order Ready', 'Your Order is Ready for Pickup - #{{order_id}}',
             '''<h2>Order Ready!</h2>
                <p>Hi {{customer_name}},</p>
                <p>Your order #{{order_id}} is ready for pickup.</p>
                <p>Please collect it from the kiosk counter.</p>''',
             'Hi {{customer_name}}, your order #{{order_id}} is ready for pickup!',
             'order_ready', '["customer_name", "order_id"]'),
        ]
        
        for name, subject, html, text, template_type, variables in default_templates:
            cursor.execute('''
                INSERT OR IGNORE INTO email_templates 
                (name, subject, html_content, text_content, template_type, variables)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, subject, html, text, template_type, variables))
        
        conn.commit()
        conn.close()
    
    def create_customer_profile(self, user_data):
        """Create or update customer profile"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if profile exists
        cursor.execute("SELECT id FROM customer_profiles WHERE email = ?", (user_data['email'],))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing profile
            cursor.execute('''
                UPDATE customer_profiles SET
                first_name = ?, last_name = ?, phone = ?, date_of_birth = ?,
                gender = ?, department = ?, year_of_study = ?, updated_at = CURRENT_TIMESTAMP
                WHERE email = ?
            ''', (
                user_data.get('first_name'), user_data.get('last_name'),
                user_data.get('phone'), user_data.get('date_of_birth'),
                user_data.get('gender'), user_data.get('department'),
                user_data.get('year_of_study'), user_data['email']
            ))
            profile_id = existing[0]
        else:
            # Create new profile
            cursor.execute('''
                INSERT INTO customer_profiles 
                (user_id, email, first_name, last_name, phone, date_of_birth, gender, department, year_of_study)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_data.get('user_id'), user_data['email'], user_data.get('first_name'),
                user_data.get('last_name'), user_data.get('phone'), user_data.get('date_of_birth'),
                user_data.get('gender'), user_data.get('department'), user_data.get('year_of_study')
            ))
            profile_id = cursor.lastrowid
            
            # Initialize loyalty points
            cursor.execute('''
                INSERT INTO customer_loyalty_points (customer_id, current_points, lifetime_points)
                VALUES (?, ?, ?)
            ''', (profile_id, 100, 100))  # Welcome bonus
        
        conn.commit()
        conn.close()
        
        # Auto-assign to segments
        self.auto_assign_segments(profile_id)
        
        return profile_id
    
    def get_customer_profile(self, customer_id=None, email=None):
        """Get customer profile with analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if customer_id:
            where_clause = "cp.id = ?"
            param = customer_id
        else:
            where_clause = "cp.email = ?"
            param = email
        
        # Get profile with loyalty info
        cursor.execute(f'''
            SELECT 
                cp.*,
                clp.current_points, clp.lifetime_points, clp.tier_level,
                COUNT(o.id) as total_orders,
                IFNULL(SUM(o.total_price), 0) as total_spent,
                IFNULL(AVG(o.total_price), 0) as avg_order_value,
                MAX(o.created_at) as last_order_date
            FROM customer_profiles cp
            LEFT JOIN customer_loyalty_points clp ON cp.id = clp.customer_id
            LEFT JOIN orders o ON cp.email = o.customer_email
            WHERE {where_clause}
            GROUP BY cp.id
        ''', (param,))
        
        profile = cursor.fetchone()
        
        if not profile:
            conn.close()
            return None
        
        # Get segments
        cursor.execute('''
            SELECT cs.name, cs.color
            FROM customer_segment_assignments csa
            JOIN customer_segments cs ON csa.segment_id = cs.id
            WHERE csa.customer_id = ?
        ''', (profile[0],))
        segments = cursor.fetchall()
        
        # Get recent orders
        cursor.execute('''
            SELECT id, total_price, status, created_at
            FROM orders
            WHERE customer_email = ?
            ORDER BY created_at DESC
            LIMIT 10
        ''', (profile[2],))
        recent_orders = cursor.fetchall()
        
        # Get feedback/reviews
        cursor.execute('''
            SELECT cf.rating, cf.review, cf.created_at, m.name as item_name
            FROM customer_feedback cf
            LEFT JOIN menu m ON cf.menu_item_id = m.id
            WHERE cf.customer_id = ?
            ORDER BY cf.created_at DESC
            LIMIT 5
        ''', (profile[0],))
        reviews = cursor.fetchall()
        
        conn.close()
        
        return {
            'id': profile[0],
            'user_id': profile[1],
            'email': profile[2],
            'first_name': profile[3],
            'last_name': profile[4],
            'full_name': f"{profile[3] or ''} {profile[4] or ''}".strip(),
            'phone': profile[5],
            'date_of_birth': profile[6],
            'gender': profile[7],
            'department': profile[8],
            'year_of_study': profile[9],
            'dietary_preferences': json.loads(profile[10]) if profile[10] else [],
            'allergies': json.loads(profile[11]) if profile[11] else [],
            'favorite_items': json.loads(profile[12]) if profile[12] else [],
            'notes': profile[13],
            'profile_image': profile[14],
            'created_at': profile[15],
            'updated_at': profile[16],
            'loyalty': {
                'current_points': profile[17] or 0,
                'lifetime_points': profile[18] or 0,
                'tier_level': profile[19] or 'Bronze'
            },
            'analytics': {
                'total_orders': profile[20],
                'total_spent': float(profile[21]),
                'avg_order_value': float(profile[22]),
                'last_order_date': profile[23]
            },
            'segments': [{'name': s[0], 'color': s[1]} for s in segments],
            'recent_orders': [
                {
                    'id': r[0], 'total_price': r[1], 
                    'status': r[2], 'created_at': r[3]
                } for r in recent_orders
            ],
            'reviews': [
                {
                    'rating': r[0], 'review': r[1], 
                    'created_at': r[2], 'item_name': r[3]
                } for r in reviews
            ]
        }
    
    def auto_assign_segments(self, customer_id):
        """Automatically assign customer to segments based on criteria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get customer analytics
        cursor.execute('''
            SELECT 
                COUNT(o.id) as orders_count,
                IFNULL(AVG(o.total_price), 0) as avg_order_value,
                IFNULL(julianday('now') - julianday(MAX(o.created_at)), 9999) as days_since_last_order
            FROM customer_profiles cp
            LEFT JOIN orders o ON cp.email = o.customer_email
            WHERE cp.id = ?
        ''', (customer_id,))
        
        analytics = cursor.fetchone()
        if not analytics:
            conn.close()
            return
        
        orders_count, avg_order_value, days_since_last_order = analytics
        
        # Get all active segments with criteria
        cursor.execute("SELECT id, criteria FROM customer_segments WHERE is_active = 1")
        segments = cursor.fetchall()
        
        # Clear existing assignments
        cursor.execute("DELETE FROM customer_segment_assignments WHERE customer_id = ?", (customer_id,))
        
        # Check each segment
        for segment_id, criteria_json in segments:
            if not criteria_json:
                continue
            
            try:
                criteria = json.loads(criteria_json)
                matches = True
                
                for field, condition in criteria.items():
                    if field == 'orders_count':
                        matches = self._check_condition(orders_count, condition)
                    elif field == 'avg_order_value':
                        matches = self._check_condition(avg_order_value, condition)
                    elif field == 'last_order_days':
                        matches = self._check_condition(days_since_last_order, condition)
                    
                    if not matches:
                        break
                
                if matches:
                    cursor.execute('''
                        INSERT INTO customer_segment_assignments (customer_id, segment_id)
                        VALUES (?, ?)
                    ''', (customer_id, segment_id))
            
            except (json.JSONDecodeError, KeyError):
                continue
        
        conn.commit()
        conn.close()
    
    def _check_condition(self, value, condition):
        """Check if value meets condition criteria"""
        operator = condition.get('operator')
        expected = condition.get('value')
        
        if operator == '=':
            return value == expected
        elif operator == '>':
            return value > expected
        elif operator == '>=':
            return value >= expected
        elif operator == '<':
            return value < expected
        elif operator == '<=':
            return value <= expected
        elif operator == 'between':
            return expected[0] <= value <= expected[1]
        
        return False
    
    def award_loyalty_points(self, customer_email, points, transaction_type='earned', order_id=None, description=None):
        """Award loyalty points to customer"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get customer profile
        cursor.execute("SELECT id FROM customer_profiles WHERE email = ?", (customer_email,))
        customer = cursor.fetchone()
        
        if not customer:
            conn.close()
            return False
        
        customer_id = customer[0]
        
        # Update points
        cursor.execute('''
            UPDATE customer_loyalty_points 
            SET current_points = current_points + ?,
                lifetime_points = lifetime_points + ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE customer_id = ?
        ''', (points, points if transaction_type == 'earned' else 0, customer_id))
        
        # Log transaction
        cursor.execute('''
            INSERT INTO points_transactions 
            (customer_id, transaction_type, points, order_id, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (customer_id, transaction_type, points, order_id, description))
        
        # Update tier if needed
        cursor.execute("SELECT lifetime_points FROM customer_loyalty_points WHERE customer_id = ?", (customer_id,))
        lifetime_points = cursor.fetchone()[0]
        
        new_tier = self._calculate_tier(lifetime_points)
        cursor.execute(
            "UPDATE customer_loyalty_points SET tier_level = ? WHERE customer_id = ?",
            (new_tier, customer_id)
        )
        
        conn.commit()
        conn.close()
        
        return True
    
    def _calculate_tier(self, lifetime_points):
        """Calculate customer tier based on lifetime points"""
        if lifetime_points >= 5000:
            return 'Platinum'
        elif lifetime_points >= 2000:
            return 'Gold'
        elif lifetime_points >= 500:
            return 'Silver'
        else:
            return 'Bronze'
    
    def create_support_ticket(self, customer_id, subject, description, priority='medium', category='general', order_id=None):
        """Create a support ticket"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO support_tickets 
            (customer_id, subject, description, priority, category, order_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (customer_id, subject, description, priority, category, order_id))
        
        ticket_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return ticket_id
    
    def get_customer_segments_analysis(self):
        """Get analysis of customer segments"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                cs.name,
                cs.color,
                COUNT(csa.customer_id) as customer_count,
                IFNULL(AVG(
                    SELECT SUM(total_price) 
                    FROM orders o 
                    WHERE o.customer_email = cp.email
                ), 0) as avg_customer_value
            FROM customer_segments cs
            LEFT JOIN customer_segment_assignments csa ON cs.id = csa.segment_id
            LEFT JOIN customer_profiles cp ON csa.customer_id = cp.id
            WHERE cs.is_active = 1
            GROUP BY cs.id, cs.name, cs.color
            ORDER BY customer_count DESC
        ''')
        
        segments = cursor.fetchall()
        conn.close()
        
        return [
            {
                'name': s[0],
                'color': s[1],
                'customer_count': s[2],
                'avg_customer_value': float(s[3])
            }
            for s in segments
        ]
    
    def send_personalized_email(self, customer_id, template_id, additional_data=None):
        """Send personalized email to customer"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get customer profile
        cursor.execute("SELECT * FROM customer_profiles WHERE id = ?", (customer_id,))
        customer = cursor.fetchone()
        
        if not customer:
            conn.close()
            return False
        
        # Get email template
        cursor.execute("SELECT * FROM email_templates WHERE id = ?", (template_id,))
        template = cursor.fetchone()
        
        if not template:
            conn.close()
            return False
        
        # Prepare template variables
        template_vars = {
            'first_name': customer[3] or 'Valued Customer',
            'last_name': customer[4] or '',
            'full_name': f"{customer[3] or ''} {customer[4] or ''}".strip() or 'Valued Customer',
            'email': customer[2]
        }
        
        if additional_data:
            template_vars.update(additional_data)
        
        # Replace variables in template
        subject = template[2]
        html_content = template[3]
        
        for var, value in template_vars.items():
            subject = subject.replace(f'{{{{{var}}}}}', str(value))
            html_content = html_content.replace(f'{{{{{var}}}}}', str(value))
        
        # Log communication
        cursor.execute('''
            INSERT INTO communication_logs 
            (customer_id, communication_type, template_id, subject, content)
            VALUES (?, ?, ?, ?, ?)
        ''', (customer_id, 'email', template_id, subject, html_content))
        
        conn.commit()
        conn.close()
        
        # In a real implementation, you would send the actual email here
        # For now, we'll just return True to indicate success
        return True
    
    def get_customer_feedback_analysis(self):
        """Analyze customer feedback and ratings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Overall rating statistics
        cursor.execute('''
            SELECT 
                AVG(rating) as avg_rating,
                COUNT(*) as total_reviews,
                COUNT(CASE WHEN rating = 5 THEN 1 END) as five_star,
                COUNT(CASE WHEN rating = 4 THEN 1 END) as four_star,
                COUNT(CASE WHEN rating = 3 THEN 1 END) as three_star,
                COUNT(CASE WHEN rating = 2 THEN 1 END) as two_star,
                COUNT(CASE WHEN rating = 1 THEN 1 END) as one_star
            FROM customer_feedback
        ''')
        
        rating_stats = cursor.fetchone()
        
        # Top rated items
        cursor.execute('''
            SELECT 
                m.name,
                AVG(cf.rating) as avg_rating,
                COUNT(cf.id) as review_count
            FROM customer_feedback cf
            JOIN menu m ON cf.menu_item_id = m.id
            GROUP BY m.id, m.name
            HAVING review_count >= 5
            ORDER BY avg_rating DESC, review_count DESC
            LIMIT 10
        ''')
        
        top_items = cursor.fetchall()
        
        # Recent feedback
        cursor.execute('''
            SELECT 
                cf.rating,
                cf.review,
                cf.created_at,
                cp.first_name,
                m.name as item_name
            FROM customer_feedback cf
            JOIN customer_profiles cp ON cf.customer_id = cp.id
            LEFT JOIN menu m ON cf.menu_item_id = m.id
            ORDER BY cf.created_at DESC
            LIMIT 20
        ''')
        
        recent_feedback = cursor.fetchall()
        
        conn.close()
        
        return {
            'rating_stats': {
                'avg_rating': float(rating_stats[0]) if rating_stats[0] else 0,
                'total_reviews': rating_stats[1],
                'distribution': {
                    '5': rating_stats[2],
                    '4': rating_stats[3],
                    '3': rating_stats[4],
                    '2': rating_stats[5],
                    '1': rating_stats[6]
                }
            },
            'top_items': [
                {
                    'name': item[0],
                    'avg_rating': float(item[1]),
                    'review_count': item[2]
                }
                for item in top_items
            ],
            'recent_feedback': [
                {
                    'rating': fb[0],
                    'review': fb[1],
                    'created_at': fb[2],
                    'customer_name': fb[3],
                    'item_name': fb[4]
                }
                for fb in recent_feedback
            ]
        }

class LoyaltyManager:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def calculate_order_points(self, order_total):
        """Calculate points for an order"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT points_per_rupee FROM loyalty_program WHERE is_active = 1 LIMIT 1")
        result = cursor.fetchone()
        conn.close()
        
        points_per_rupee = result[0] if result else 1.0
        return int(order_total * points_per_rupee)
    
    def redeem_points(self, customer_email, points_to_redeem):
        """Redeem loyalty points for discount"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get customer points
        cursor.execute('''
            SELECT clp.customer_id, clp.current_points
            FROM customer_loyalty_points clp
            JOIN customer_profiles cp ON clp.customer_id = cp.id
            WHERE cp.email = ?
        ''', (customer_email,))
        
        result = cursor.fetchone()
        if not result or result[1] < points_to_redeem:
            conn.close()
            return False, "Insufficient points"
        
        customer_id, current_points = result
        
        # Deduct points
        cursor.execute('''
            UPDATE customer_loyalty_points 
            SET current_points = current_points - ?
            WHERE customer_id = ?
        ''', (points_to_redeem, customer_id))
        
        # Log transaction
        cursor.execute('''
            INSERT INTO points_transactions 
            (customer_id, transaction_type, points, description)
            VALUES (?, ?, ?, ?)
        ''', (customer_id, 'redeemed', -points_to_redeem, f'Redeemed {points_to_redeem} points'))
        
        conn.commit()
        conn.close()
        
        # Calculate discount (100 points = ₹10)
        discount_amount = points_to_redeem / 10
        return True, discount_amount
    
    def get_tier_benefits(self, tier_level):
        """Get benefits for a tier level"""
        benefits = {
            'Bronze': {
                'discount_percentage': 0,
                'free_delivery_threshold': 200,
                'birthday_bonus': 50,
                'special_offers': False
            },
            'Silver': {
                'discount_percentage': 2,
                'free_delivery_threshold': 150,
                'birthday_bonus': 100,
                'special_offers': True
            },
            'Gold': {
                'discount_percentage': 5,
                'free_delivery_threshold': 100,
                'birthday_bonus': 200,
                'special_offers': True
            },
            'Platinum': {
                'discount_percentage': 10,
                'free_delivery_threshold': 0,
                'birthday_bonus': 500,
                'special_offers': True
            }
        }
        
        return benefits.get(tier_level, benefits['Bronze'])