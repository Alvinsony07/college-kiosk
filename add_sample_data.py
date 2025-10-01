#!/usr/bin/env python3
"""
Sample Data Generator for College Kiosk Enterprise System
This script adds realistic sample data to demonstrate all enterprise features
"""

import sqlite3
import os
import random
import json
from datetime import datetime, timedelta

# Database path
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'college.db'))

def add_sample_data():
    """Add comprehensive sample data for enterprise features"""
    print("🚀 Adding Sample Data to College Kiosk Enterprise System...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("👥 Adding sample users...")
        
        # Sample users
        sample_users = [
            ('Admin User', 'admin@college.edu', 'admin123', '9876543210', 'admin', 'approved', 1000),
            ('John Doe', 'john@student.edu', 'password123', '9876543211', 'user', 'approved', 250),
            ('Jane Smith', 'jane@student.edu', 'password123', '9876543212', 'user', 'approved', 180),
            ('Bob Wilson', 'bob@student.edu', 'password123', '9876543213', 'user', 'approved', 320),
            ('Alice Johnson', 'alice@student.edu', 'password123', '9876543214', 'user', 'pending', 0),
            ('Mike Brown', 'mike@staff.edu', 'password123', '9876543215', 'staff', 'approved', 150),
            ('Sarah Davis', 'sarah@student.edu', 'password123', '9876543216', 'user', 'approved', 420),
            ('Tom Anderson', 'tom@student.edu', 'password123', '9876543217', 'user', 'approved', 90),
        ]
        
        for user in sample_users:
            hashed_password = user[2]  # In real app, this would be hashed
            cursor.execute('''
                INSERT OR IGNORE INTO users (name, email, password, phone, role, status, loyalty_points)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', user)
        
        print("🍕 Adding sample menu items...")
        
        # Sample menu items
        sample_menu = [
            ('Veg Sandwich', 45.0, 'Sandwiches', 'Sandwich_Photography_Styling.jpeg', 1, 25, 1, 'Fresh vegetable sandwich with cucumber, tomato, and lettuce', 'Bread, Cucumber, Tomato, Lettuce, Mayo', 'Calories: 280, Protein: 8g, Carbs: 35g', 'Gluten', 10, 8.5, 25.0, 44.4),
            ('Chocolate Coffee', 65.0, 'Beverages', 'chocolate-coffee-fill.jpeg', 1, 30, 0, 'Rich chocolate coffee blend', 'Coffee, Chocolate, Milk, Sugar', 'Calories: 180, Protein: 6g, Sugar: 20g', 'Dairy', 5, 9.2, 35.0, 46.2),
            ('Ginger Mint Tea', 35.0, 'Beverages', 'Ginger_Mint_Tea_with_Milk_Pudina_Adrak_Chai.png', 1, 40, 0, 'Refreshing ginger mint tea', 'Tea, Ginger, Mint, Milk', 'Calories: 80, Antioxidants, Vitamin C', 'Dairy', 3, 7.8, 15.0, 57.1),
            ('Avocado Smoothie', 85.0, 'Beverages', 'avocado-smoothie-recipe.jpg', 1, 15, 1, 'Healthy avocado smoothie', 'Avocado, Banana, Milk, Honey', 'Calories: 320, Protein: 8g, Healthy Fats', 'Dairy', 8, 9.5, 45.0, 47.1),
            ('Vada Pav', 25.0, 'Snacks', 'vada_pav.jpg.jpg', 1, 50, 1, 'Traditional Mumbai street food', 'Potato, Pav, Spices, Oil', 'Calories: 250, Carbs: 40g', 'Gluten', 12, 9.8, 12.0, 52.0),
            ('Masala Dosa', 75.0, 'Main Course', '', 1, 20, 0, 'South Indian crispy crepe with potato filling', 'Rice, Lentils, Potato, Spices', 'Calories: 350, Protein: 12g', 'None', 20, 8.9, 40.0, 49.3),
            ('Pani Puri', 30.0, 'Snacks', '', 1, 35, 0, 'Crispy hollow balls with spicy water', 'Flour, Tamarind, Spices, Water', 'Calories: 200, Carbs: 35g', 'Gluten', 8, 9.4, 15.0, 50.0),
            ('Bhel Puri', 40.0, 'Snacks', '', 1, 28, 0, 'Puffed rice snack with chutneys', 'Puffed Rice, Sev, Chutneys', 'Calories: 180, Fiber: 5g', 'None', 10, 8.7, 22.0, 45.0),
        ]
        
        for item in sample_menu:
            cursor.execute('''
                INSERT OR IGNORE INTO menu (
                    name, price, category, image, available, stock, deliverable,
                    description, ingredients, nutrition_info, allergens,
                    preparation_time, popularity_score, cost_price, profit_margin
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', item)
        
        print("📋 Adding sample orders...")
        
        # Sample orders
        sample_orders = [
            ('John Doe', 'john@student.edu', '[{"name": "Veg Sandwich", "quantity": 2, "price": 45}]', 90.0, 'completed', '123456', 15, 12, 5, 'Great taste!', 1),
            ('Jane Smith', 'jane@student.edu', '[{"name": "Chocolate Coffee", "quantity": 1, "price": 65}, {"name": "Vada Pav", "quantity": 2, "price": 25}]', 115.0, 'completed', '234567', 18, 20, 4, 'Good service', 1),
            ('Bob Wilson', 'bob@student.edu', '[{"name": "Avocado Smoothie", "quantity": 1, "price": 85}]', 85.0, 'preparing', '345678', 8, None, None, None, 1),
            ('Sarah Davis', 'sarah@student.edu', '[{"name": "Masala Dosa", "quantity": 1, "price": 75}, {"name": "Ginger Mint Tea", "quantity": 1, "price": 35}]', 110.0, 'Order Received', '456789', 25, None, None, None, 1),
            ('Tom Anderson', 'tom@student.edu', '[{"name": "Pani Puri", "quantity": 3, "price": 30}]', 90.0, 'completed', '567890', 12, 10, 5, 'Excellent!', 1),
        ]
        
        # Add orders with timestamps from the last 7 days
        for i, order in enumerate(sample_orders):
            order_date = (datetime.now() - timedelta(days=random.randint(0, 7))).isoformat()
            cursor.execute('''
                INSERT OR IGNORE INTO orders (
                    customer_name, customer_email, items, total_price, status, otp,
                    estimated_time, actual_time, rating, feedback, loyalty_points_earned,
                    created_at, payment_method, payment_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*order, order_date, 'cash', 'completed' if order[4] == 'completed' else 'pending'))
        
        print("💰 Adding financial records...")
        
        # Sample financial records
        financial_records = [
            ('expense', 15000, 'Monthly ingredients purchase', 'inventory', 'admin@college.edu'),
            ('expense', 5000, 'Kitchen equipment maintenance', 'maintenance', 'admin@college.edu'),
            ('income', 25000, 'Food sales revenue', 'sales', 'system'),
            ('expense', 3000, 'Staff salary', 'payroll', 'admin@college.edu'),
            ('expense', 2000, 'Utilities bill', 'utilities', 'admin@college.edu'),
            ('income', 1500, 'Catering service', 'catering', 'system'),
        ]
        
        for record in financial_records:
            record_date = (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
            cursor.execute('''
                INSERT OR IGNORE INTO financial_records (
                    transaction_type, amount, description, category, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (*record, record_date))
        
        print("📦 Adding inventory transactions...")
        
        # Sample inventory transactions
        inventory_transactions = [
            (1, 'purchase', 100, 25.0, 'Fresh Foods Pvt Ltd', 'Weekly vegetable stock'),
            (2, 'purchase', 50, 35.0, 'Coffee Suppliers Co', 'Premium coffee beans'),
            (3, 'purchase', 200, 15.0, 'Tea Garden Ltd', 'Organic tea leaves'),
            (4, 'purchase', 80, 45.0, 'Fruit Distributors', 'Fresh avocados'),
            (5, 'purchase', 150, 12.0, 'Snack Supplies Inc', 'Vada pav ingredients'),
        ]
        
        for transaction in inventory_transactions:
            trans_date = (datetime.now() - timedelta(days=random.randint(1, 15))).isoformat()
            cursor.execute('''
                INSERT OR IGNORE INTO inventory_transactions (
                    item_id, transaction_type, quantity, unit_price, supplier, notes, created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (*transaction, trans_date, 'admin@college.edu'))
        
        print("🏢 Adding more suppliers...")
        
        # Additional suppliers
        suppliers = [
            ('Coffee Suppliers Co', 'Rajesh Patel', 'rajesh@coffeesuppliers.com', '+91-9876543220', 'Mumbai, Maharashtra', '15 days', 4.2, 'active'),
            ('Tea Garden Ltd', 'Priya Sharma', 'priya@teagarden.com', '+91-9876543221', 'Darjeeling, West Bengal', '30 days', 4.7, 'active'),
            ('Fruit Distributors', 'Amit Kumar', 'amit@fruitdist.com', '+91-9876543222', 'Pune, Maharashtra', '7 days', 4.0, 'active'),
            ('Snack Supplies Inc', 'Neha Gupta', 'neha@snacksupplies.com', '+91-9876543223', 'Delhi, India', '21 days', 4.3, 'active'),
        ]
        
        for supplier in suppliers:
            cursor.execute('''
                INSERT OR IGNORE INTO suppliers (
                    name, contact_person, email, phone, address, payment_terms, rating, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', supplier)
        
        print("🎯 Adding performance metrics...")
        
        # Sample performance metrics
        for i in range(30):
            metric_date = (datetime.now() - timedelta(days=i)).isoformat()
            cursor.execute('''
                INSERT OR IGNORE INTO performance_metrics (
                    metric_type, metric_value, timestamp, details
                ) VALUES (?, ?, ?, ?)
            ''', ('daily_orders', random.randint(15, 45), metric_date, 'Daily order count'))
            
            cursor.execute('''
                INSERT OR IGNORE INTO performance_metrics (
                    metric_type, metric_value, timestamp, details
                ) VALUES (?, ?, ?, ?)
            ''', ('daily_revenue', random.uniform(800, 2500), metric_date, 'Daily revenue in INR'))
        
        print("📢 Adding sample notifications...")
        
        # Sample notifications
        notifications = [
            ('admin@college.edu', 'Low Stock Alert', 'Avocado Smoothie ingredients are running low', 'inventory', 'high'),
            ('admin@college.edu', 'New Order Received', 'Order #12345 received from John Doe', 'order', 'normal'),
            ('admin@college.edu', 'Weekly Report Ready', 'Your weekly sales report is ready for review', 'report', 'normal'),
            ('admin@college.edu', 'Payment Overdue', 'Payment to Fresh Foods Pvt Ltd is overdue', 'financial', 'high'),
            ('john@student.edu', 'Order Completed', 'Your order has been completed and ready for pickup', 'order', 'normal'),
        ]
        
        for notification in notifications:
            notif_date = (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat()
            cursor.execute('''
                INSERT OR IGNORE INTO notifications (
                    recipient_email, title, message, type, priority, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (*notification, notif_date))
        
        print("📊 Adding customer interactions...")
        
        # Sample customer interactions
        interactions = [
            ('john@student.edu', 'order_placed', 'Customer placed order for Veg Sandwich x2', 'system'),
            ('jane@student.edu', 'complaint', 'Customer complained about late delivery', 'admin@college.edu'),
            ('bob@student.edu', 'feedback', 'Customer provided positive feedback', 'system'),
            ('sarah@student.edu', 'inquiry', 'Customer inquired about nutritional information', 'staff@college.edu'),
        ]
        
        for interaction in interactions:
            inter_date = (datetime.now() - timedelta(days=random.randint(1, 10))).isoformat()
            cursor.execute('''
                INSERT OR IGNORE INTO customer_interactions (
                    customer_email, interaction_type, details, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?)
            ''', (*interaction, inter_date))
        
        conn.commit()
        print("\n🎉 Sample data added successfully!")
        print("\n📋 Data Summary:")
        
        # Show data counts
        tables = ['users', 'menu', 'orders', 'financial_records', 'inventory_transactions', 
                 'suppliers', 'notifications', 'customer_interactions', 'performance_metrics']
        
        for table in tables:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            print(f"   ✅ {table}: {count} records")
        
        print("\n🚀 Your enterprise system now has realistic data to explore!")
        print("   👤 Try logging in with: admin@college.edu / admin123")
        print("   🎯 Dashboard will now show real metrics and analytics")
        print("   📊 All enterprise features are populated with sample data")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error adding sample data: {str(e)}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    add_sample_data()