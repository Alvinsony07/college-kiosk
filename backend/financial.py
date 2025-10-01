"""
Financial Management System
Features: Payment gateways, tax management, expense tracking, P&L reports, invoice generation
"""

import sqlite3
import json
from datetime import datetime, timedelta
import uuid
import hashlib
import hmac
import random
from decimal import Decimal, ROUND_HALF_UP
import pandas as pd
import io
import base64

# PDF generation imports (optional)
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

class FinancialManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_financial_tables()
    
    def init_financial_tables(self):
        """Initialize financial management tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Payment methods
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL, -- cash, card, upi, wallet, bank_transfer
                provider TEXT, -- razorpay, paytm, gpay, etc.
                is_active INTEGER DEFAULT 1,
                processing_fee_percentage REAL DEFAULT 0.0,
                processing_fee_fixed REAL DEFAULT 0.0,
                settlement_days INTEGER DEFAULT 0, -- T+0, T+1, etc.
                config TEXT, -- JSON configuration
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Payment transactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_id TEXT UNIQUE NOT NULL,
                order_id INTEGER,
                payment_method_id INTEGER,
                gateway_transaction_id TEXT,
                amount REAL NOT NULL,
                processing_fee REAL DEFAULT 0.0,
                net_amount REAL NOT NULL,
                currency TEXT DEFAULT 'INR',
                status TEXT DEFAULT 'pending', -- pending, success, failed, refunded
                payment_date TEXT DEFAULT CURRENT_TIMESTAMP,
                settlement_date TEXT,
                gateway_response TEXT, -- JSON response from payment gateway
                failure_reason TEXT,
                refund_amount REAL DEFAULT 0.0,
                refund_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (payment_method_id) REFERENCES payment_methods (id)
            )
        ''')
        
        # Tax configurations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tax_configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tax_name TEXT NOT NULL,
                tax_type TEXT NOT NULL, -- gst, service_tax, cess
                tax_rate REAL NOT NULL,
                applicable_categories TEXT, -- JSON array of categories
                is_active INTEGER DEFAULT 1,
                effective_from TEXT DEFAULT CURRENT_TIMESTAMP,
                effective_to TEXT,
                description TEXT
            )
        ''')
        
        # Expense categories
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expense_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES expense_categories (id)
            )
        ''')
        
        # Expenses
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_number TEXT UNIQUE,
                category_id INTEGER NOT NULL,
                supplier_id INTEGER,
                description TEXT NOT NULL,
                amount REAL NOT NULL,
                tax_amount REAL DEFAULT 0.0,
                total_amount REAL NOT NULL,
                expense_date TEXT DEFAULT CURRENT_TIMESTAMP,
                payment_method TEXT,
                receipt_image TEXT,
                notes TEXT,
                status TEXT DEFAULT 'pending', -- pending, approved, rejected, paid
                approved_by INTEGER,
                approved_at TEXT,
                paid_by INTEGER,
                paid_at TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES expense_categories (id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
                FOREIGN KEY (approved_by) REFERENCES users (id),
                FOREIGN KEY (paid_by) REFERENCES users (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Invoices
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                order_id INTEGER,
                customer_name TEXT,
                customer_email TEXT,
                customer_phone TEXT,
                customer_address TEXT,
                customer_gstin TEXT,
                subtotal REAL NOT NULL,
                tax_details TEXT, -- JSON with tax breakdown
                discount_amount REAL DEFAULT 0.0,
                total_amount REAL NOT NULL,
                invoice_date TEXT DEFAULT CURRENT_TIMESTAMP,
                due_date TEXT,
                status TEXT DEFAULT 'draft', -- draft, sent, paid, overdue, cancelled
                payment_terms TEXT,
                notes TEXT,
                generated_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders (id),
                FOREIGN KEY (generated_by) REFERENCES users (id)
            )
        ''')
        
        # Invoice items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                menu_item_id INTEGER,
                item_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                tax_rate REAL DEFAULT 0.0,
                tax_amount REAL DEFAULT 0.0,
                total_amount REAL NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id),
                FOREIGN KEY (menu_item_id) REFERENCES menu (id)
            )
        ''')
        
        # Discounts and coupons
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS discount_coupons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                discount_type TEXT NOT NULL, -- percentage, fixed, buy_x_get_y
                discount_value REAL NOT NULL,
                minimum_order_amount REAL DEFAULT 0.0,
                maximum_discount_amount REAL,
                applicable_categories TEXT, -- JSON array
                applicable_items TEXT, -- JSON array of menu item IDs
                usage_limit INTEGER,
                usage_limit_per_customer INTEGER DEFAULT 1,
                current_usage INTEGER DEFAULT 0,
                start_date TEXT DEFAULT CURRENT_TIMESTAMP,
                end_date TEXT,
                is_active INTEGER DEFAULT 1,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Coupon usage tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coupon_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                coupon_id INTEGER NOT NULL,
                order_id INTEGER NOT NULL,
                customer_email TEXT,
                discount_amount REAL NOT NULL,
                used_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (coupon_id) REFERENCES discount_coupons (id),
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        
        # Financial accounts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_name TEXT NOT NULL,
                account_type TEXT NOT NULL, -- asset, liability, equity, revenue, expense
                account_number TEXT,
                bank_name TEXT,
                ifsc_code TEXT,
                opening_balance REAL DEFAULT 0.0,
                current_balance REAL DEFAULT 0.0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Journal entries for double-entry bookkeeping
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_number TEXT UNIQUE NOT NULL,
                transaction_date TEXT DEFAULT CURRENT_TIMESTAMP,
                reference_type TEXT, -- sale, purchase, payment, expense
                reference_id INTEGER,
                description TEXT,
                total_amount REAL NOT NULL,
                created_by INTEGER,
                approved_by INTEGER,
                approved_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users (id),
                FOREIGN KEY (approved_by) REFERENCES users (id)
            )
        ''')
        
        # Journal entry lines
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS journal_entry_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_entry_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                debit_amount REAL DEFAULT 0.0,
                credit_amount REAL DEFAULT 0.0,
                description TEXT,
                FOREIGN KEY (journal_entry_id) REFERENCES journal_entries (id),
                FOREIGN KEY (account_id) REFERENCES financial_accounts (id)
            )
        ''')
        
        # Budget planning
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                budget_year INTEGER NOT NULL,
                budget_month INTEGER, -- NULL for annual budget
                category_id INTEGER,
                account_id INTEGER,
                budgeted_amount REAL NOT NULL,
                actual_amount REAL DEFAULT 0.0,
                variance REAL DEFAULT 0.0,
                notes TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES expense_categories (id),
                FOREIGN KEY (account_id) REFERENCES financial_accounts (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Insert default data
        self.insert_default_financial_data()
    
    def insert_default_financial_data(self):
        """Insert default financial data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Default payment methods
        default_payment_methods = [
            ('Cash', 'cash', '', 0.0, 0.0, 0),
            ('Credit Card', 'card', 'razorpay', 2.5, 0.0, 2),
            ('Debit Card', 'card', 'razorpay', 1.5, 0.0, 2),
            ('UPI', 'upi', 'razorpay', 1.0, 0.0, 1),
            ('PayTM Wallet', 'wallet', 'paytm', 2.0, 0.0, 1),
            ('Google Pay', 'upi', 'gpay', 0.0, 0.0, 0),
        ]
        
        for name, ptype, provider, fee_pct, fee_fixed, settlement in default_payment_methods:
            cursor.execute('''
                INSERT OR IGNORE INTO payment_methods 
                (name, type, provider, processing_fee_percentage, processing_fee_fixed, settlement_days)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (name, ptype, provider, fee_pct, fee_fixed, settlement))
        
        # Default tax configurations
        default_taxes = [
            ('CGST', 'gst', 9.0, '["all"]', 'Central Goods and Services Tax'),
            ('SGST', 'gst', 9.0, '["all"]', 'State Goods and Services Tax'),
            ('IGST', 'gst', 18.0, '["all"]', 'Integrated Goods and Services Tax'),
            ('Service Charge', 'service_tax', 10.0, '["food", "beverage"]', 'Service charge on food items'),
        ]
        
        for name, tax_type, rate, categories, desc in default_taxes:
            cursor.execute('''
                INSERT OR IGNORE INTO tax_configurations 
                (tax_name, tax_type, tax_rate, applicable_categories, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, tax_type, rate, categories, desc))
        
        # Default expense categories
        default_expense_categories = [
            ('Raw Materials', None, 'Food ingredients and supplies'),
            ('Utilities', None, 'Electricity, water, gas'),
            ('Staff Salaries', None, 'Employee compensation'),
            ('Marketing', None, 'Advertising and promotion'),
            ('Maintenance', None, 'Equipment and facility maintenance'),
            ('Rent', None, 'Property rent and lease'),
            ('Insurance', None, 'Business insurance premiums'),
            ('Professional Services', None, 'Legal, accounting, consulting'),
            ('Technology', None, 'Software, hardware, internet'),
            ('Miscellaneous', None, 'Other business expenses'),
        ]
        
        for name, parent_id, desc in default_expense_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO expense_categories (name, parent_id, description)
                VALUES (?, ?, ?)
            ''', (name, parent_id, desc))
        
        # Default financial accounts (Chart of Accounts)
        default_accounts = [
            # Assets
            ('Cash in Hand', 'asset', None, None, None, 10000.0),
            ('Bank Account - Current', 'asset', '1234567890', 'State Bank of India', 'SBIN0001234', 50000.0),
            ('Accounts Receivable', 'asset', None, None, None, 0.0),
            ('Inventory', 'asset', None, None, None, 25000.0),
            ('Equipment', 'asset', None, None, None, 100000.0),
            
            # Liabilities
            ('Accounts Payable', 'liability', None, None, None, 0.0),
            ('Accrued Expenses', 'liability', None, None, None, 0.0),
            ('Sales Tax Payable', 'liability', None, None, None, 0.0),
            
            # Equity
            ('Owner Equity', 'equity', None, None, None, 185000.0),
            
            # Revenue
            ('Food Sales', 'revenue', None, None, None, 0.0),
            ('Beverage Sales', 'revenue', None, None, None, 0.0),
            
            # Expenses
            ('Cost of Goods Sold', 'expense', None, None, None, 0.0),
            ('Staff Salaries', 'expense', None, None, None, 0.0),
            ('Rent Expense', 'expense', None, None, None, 0.0),
            ('Utilities Expense', 'expense', None, None, None, 0.0),
            ('Marketing Expense', 'expense', None, None, None, 0.0),
        ]
        
        for name, acc_type, number, bank, ifsc, balance in default_accounts:
            cursor.execute('''
                INSERT OR IGNORE INTO financial_accounts 
                (account_name, account_type, account_number, bank_name, ifsc_code, 
                 opening_balance, current_balance)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, acc_type, number, bank, ifsc, balance, balance))
        
        conn.commit()
        conn.close()
    
    def process_payment(self, payment_data):
        """Process a payment transaction"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate unique transaction ID
        transaction_id = f"TXN{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
        
        # Calculate processing fees
        cursor.execute("SELECT * FROM payment_methods WHERE id = ?", (payment_data['payment_method_id'],))
        payment_method = cursor.fetchone()
        
        amount = Decimal(str(payment_data['amount']))
        processing_fee = Decimal('0')
        
        if payment_method:
            fee_percentage = Decimal(str(payment_method[5]))  # processing_fee_percentage
            fee_fixed = Decimal(str(payment_method[6]))       # processing_fee_fixed
            processing_fee = (amount * fee_percentage / 100) + fee_fixed
        
        net_amount = amount - processing_fee
        
        # Insert payment transaction
        cursor.execute('''
            INSERT INTO payment_transactions 
            (transaction_id, order_id, payment_method_id, amount, processing_fee, 
             net_amount, status, gateway_transaction_id, gateway_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            transaction_id,
            payment_data.get('order_id'),
            payment_data['payment_method_id'],
            float(amount),
            float(processing_fee),
            float(net_amount),
            payment_data.get('status', 'pending'),
            payment_data.get('gateway_transaction_id'),
            json.dumps(payment_data.get('gateway_response', {}))
        ))
        
        payment_id = cursor.lastrowid
        
        # Create journal entry for successful payment
        if payment_data.get('status') == 'success':
            self.create_sale_journal_entry(cursor, payment_data.get('order_id'), float(amount))
        
        conn.commit()
        conn.close()
        
        return {
            'transaction_id': transaction_id,
            'payment_id': payment_id,
            'net_amount': float(net_amount),
            'processing_fee': float(processing_fee)
        }
    
    def create_sale_journal_entry(self, cursor, order_id, amount):
        """Create journal entry for a sale"""
        entry_number = f"JE{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Create journal entry
        cursor.execute('''
            INSERT INTO journal_entries 
            (entry_number, reference_type, reference_id, description, total_amount)
            VALUES (?, ?, ?, ?, ?)
        ''', (entry_number, 'sale', order_id, f'Sale for Order #{order_id}', amount))
        
        journal_id = cursor.lastrowid
        
        # Get account IDs
        cursor.execute("SELECT id FROM financial_accounts WHERE account_name = 'Cash in Hand'")
        cash_account = cursor.fetchone()[0]
        
        cursor.execute("SELECT id FROM financial_accounts WHERE account_name = 'Food Sales'")
        sales_account = cursor.fetchone()[0]
        
        # Debit Cash (Asset increases)
        cursor.execute('''
            INSERT INTO journal_entry_lines 
            (journal_entry_id, account_id, debit_amount, description)
            VALUES (?, ?, ?, ?)
        ''', (journal_id, cash_account, amount, 'Cash received from sale'))
        
        # Credit Sales (Revenue increases)
        cursor.execute('''
            INSERT INTO journal_entry_lines 
            (journal_entry_id, account_id, credit_amount, description)
            VALUES (?, ?, ?, ?)
        ''', (journal_id, sales_account, amount, 'Food sales revenue'))
        
        # Update account balances
        cursor.execute(
            "UPDATE financial_accounts SET current_balance = current_balance + ? WHERE id = ?",
            (amount, cash_account)
        )
    
    def apply_discount_coupon(self, coupon_code, order_data):
        """Apply discount coupon to order"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get coupon details
        cursor.execute('''
            SELECT * FROM discount_coupons 
            WHERE code = ? AND is_active = 1 
            AND start_date <= CURRENT_TIMESTAMP 
            AND (end_date IS NULL OR end_date >= CURRENT_TIMESTAMP)
        ''', (coupon_code,))
        
        coupon = cursor.fetchone()
        
        if not coupon:
            conn.close()
            return {'success': False, 'error': 'Invalid or expired coupon'}
        
        coupon_id = coupon[0]
        discount_type = coupon[4]
        discount_value = coupon[5]
        min_order_amount = coupon[6]
        max_discount = coupon[7]
        usage_limit = coupon[9]
        usage_limit_per_customer = coupon[10]
        current_usage = coupon[11]
        
        order_total = order_data['total_amount']
        customer_email = order_data.get('customer_email')
        
        # Check minimum order amount
        if order_total < min_order_amount:
            conn.close()
            return {
                'success': False, 
                'error': f'Minimum order amount is ₹{min_order_amount}'
            }
        
        # Check usage limits
        if usage_limit and current_usage >= usage_limit:
            conn.close()
            return {'success': False, 'error': 'Coupon usage limit exceeded'}
        
        if customer_email:
            cursor.execute(
                "SELECT COUNT(*) FROM coupon_usage WHERE coupon_id = ? AND customer_email = ?",
                (coupon_id, customer_email)
            )
            customer_usage = cursor.fetchone()[0]
            
            if customer_usage >= usage_limit_per_customer:
                conn.close()
                return {'success': False, 'error': 'Personal usage limit exceeded'}
        
        # Calculate discount
        discount_amount = 0
        
        if discount_type == 'percentage':
            discount_amount = order_total * (discount_value / 100)
        elif discount_type == 'fixed':
            discount_amount = discount_value
        
        # Apply maximum discount limit
        if max_discount and discount_amount > max_discount:
            discount_amount = max_discount
        
        # Ensure discount doesn't exceed order total
        discount_amount = min(discount_amount, order_total)
        
        conn.close()
        
        return {
            'success': True,
            'coupon_id': coupon_id,
            'discount_amount': discount_amount,
            'coupon_name': coupon[2]
        }
    
    def record_coupon_usage(self, coupon_id, order_id, customer_email, discount_amount):
        """Record coupon usage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO coupon_usage (coupon_id, order_id, customer_email, discount_amount)
            VALUES (?, ?, ?, ?)
        ''', (coupon_id, order_id, customer_email, discount_amount))
        
        # Update coupon usage count
        cursor.execute(
            "UPDATE discount_coupons SET current_usage = current_usage + 1 WHERE id = ?",
            (coupon_id,)
        )
        
        conn.commit()
        conn.close()
    
    def generate_invoice(self, order_data, customer_data=None):
        """Generate invoice for order"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate invoice number
        invoice_number = f"INV{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
        
        # Calculate taxes
        tax_details = self.calculate_taxes(order_data['items'])
        
        subtotal = sum(item['price'] * item['quantity'] for item in order_data['items'])
        total_tax = sum(tax['amount'] for tax in tax_details['taxes'])
        discount_amount = order_data.get('discount_amount', 0)
        total_amount = subtotal + total_tax - discount_amount
        
        # Create invoice
        cursor.execute('''
            INSERT INTO invoices 
            (invoice_number, order_id, customer_name, customer_email, customer_phone,
             customer_address, customer_gstin, subtotal, tax_details, discount_amount,
             total_amount, due_date, payment_terms, generated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            invoice_number,
            order_data.get('order_id'),
            customer_data.get('name') if customer_data else order_data.get('customer_name'),
            customer_data.get('email') if customer_data else order_data.get('customer_email'),
            customer_data.get('phone') if customer_data else None,
            customer_data.get('address') if customer_data else None,
            customer_data.get('gstin') if customer_data else None,
            subtotal,
            json.dumps(tax_details),
            discount_amount,
            total_amount,
            (datetime.now() + timedelta(days=30)).isoformat(),  # 30 days due date
            'Net 30 days',
            order_data.get('created_by')
        ))
        
        invoice_id = cursor.lastrowid
        
        # Add invoice items
        for item in order_data['items']:
            item_tax_rate = self.get_item_tax_rate(item.get('category', 'food'))
            item_tax_amount = item['price'] * item['quantity'] * (item_tax_rate / 100)
            item_total = (item['price'] * item['quantity']) + item_tax_amount
            
            cursor.execute('''
                INSERT INTO invoice_items 
                (invoice_id, menu_item_id, item_name, quantity, unit_price, 
                 tax_rate, tax_amount, total_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                invoice_id,
                item.get('id'),
                item['name'],
                item['quantity'],
                item['price'],
                item_tax_rate,
                item_tax_amount,
                item_total
            ))
        
        conn.commit()
        conn.close()
        
        return {
            'invoice_id': invoice_id,
            'invoice_number': invoice_number,
            'total_amount': total_amount
        }
    
    def calculate_taxes(self, order_items):
        """Calculate taxes for order items"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get active tax configurations
        cursor.execute("SELECT * FROM tax_configurations WHERE is_active = 1")
        tax_configs = cursor.fetchall()
        
        taxes = []
        total_tax_amount = 0
        
        for tax_config in tax_configs:
            tax_name = tax_config[1]
            tax_rate = tax_config[3]
            applicable_categories = json.loads(tax_config[4])
            
            tax_amount = 0
            
            for item in order_items:
                item_category = item.get('category', 'food')
                
                # Check if tax applies to this category
                if 'all' in applicable_categories or item_category in applicable_categories:
                    item_subtotal = item['price'] * item['quantity']
                    tax_amount += item_subtotal * (tax_rate / 100)
            
            if tax_amount > 0:
                taxes.append({
                    'name': tax_name,
                    'rate': tax_rate,
                    'amount': round(tax_amount, 2)
                })
                total_tax_amount += tax_amount
        
        conn.close()
        
        return {
            'taxes': taxes,
            'total_tax_amount': round(total_tax_amount, 2)
        }
    
    def get_item_tax_rate(self, category):
        """Get tax rate for item category"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT SUM(tax_rate) FROM tax_configurations 
            WHERE is_active = 1 AND (
                applicable_categories LIKE '%"all"%' OR 
                applicable_categories LIKE ?
            )
        ''', (f'%"{category}"%',))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result and result[0] else 0
    
    def record_expense(self, expense_data):
        """Record business expense"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate expense number
        expense_number = f"EXP{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
        
        # Calculate tax if applicable
        tax_amount = expense_data.get('tax_amount', 0)
        total_amount = expense_data['amount'] + tax_amount
        
        cursor.execute('''
            INSERT INTO expenses 
            (expense_number, category_id, supplier_id, description, amount, 
             tax_amount, total_amount, expense_date, payment_method, receipt_image, 
             notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            expense_number,
            expense_data['category_id'],
            expense_data.get('supplier_id'),
            expense_data['description'],
            expense_data['amount'],
            tax_amount,
            total_amount,
            expense_data.get('expense_date', datetime.now().isoformat()),
            expense_data.get('payment_method'),
            expense_data.get('receipt_image'),
            expense_data.get('notes'),
            expense_data.get('created_by')
        ))
        
        expense_id = cursor.lastrowid
        
        # Create journal entry
        self.create_expense_journal_entry(cursor, expense_id, expense_data)
        
        conn.commit()
        conn.close()
        
        return expense_id
    
    def create_expense_journal_entry(self, cursor, expense_id, expense_data):
        """Create journal entry for expense"""
        entry_number = f"JE{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor.execute('''
            INSERT INTO journal_entries 
            (entry_number, reference_type, reference_id, description, total_amount)
            VALUES (?, ?, ?, ?, ?)
        ''', (entry_number, 'expense', expense_id, expense_data['description'], expense_data['amount']))
        
        journal_id = cursor.lastrowid
        
        # Get expense category name for account mapping
        cursor.execute("SELECT name FROM expense_categories WHERE id = ?", (expense_data['category_id'],))
        category_name = cursor.fetchone()[0]
        
        # Get or create expense account
        cursor.execute("SELECT id FROM financial_accounts WHERE account_name LIKE ?", (f"%{category_name}%",))
        expense_account = cursor.fetchone()
        
        if not expense_account:
            # Create generic expense account
            cursor.execute("SELECT id FROM financial_accounts WHERE account_name = 'Miscellaneous Expense'")
            expense_account = cursor.fetchone()
            
            if not expense_account:
                cursor.execute('''
                    INSERT INTO financial_accounts (account_name, account_type)
                    VALUES (?, ?)
                ''', (f"{category_name} Expense", 'expense'))
                expense_account_id = cursor.lastrowid
            else:
                expense_account_id = expense_account[0]
        else:
            expense_account_id = expense_account[0]
        
        # Get cash account
        cursor.execute("SELECT id FROM financial_accounts WHERE account_name = 'Cash in Hand'")
        cash_account_id = cursor.fetchone()[0]
        
        # Debit Expense Account (Expense increases)
        cursor.execute('''
            INSERT INTO journal_entry_lines 
            (journal_entry_id, account_id, debit_amount, description)
            VALUES (?, ?, ?, ?)
        ''', (journal_id, expense_account_id, expense_data['amount'], expense_data['description']))
        
        # Credit Cash Account (Asset decreases)
        cursor.execute('''
            INSERT INTO journal_entry_lines 
            (journal_entry_id, account_id, credit_amount, description)
            VALUES (?, ?, ?, ?)
        ''', (journal_id, cash_account_id, expense_data['amount'], 'Cash paid for expense'))
        
        # Update cash balance
        cursor.execute(
            "UPDATE financial_accounts SET current_balance = current_balance - ? WHERE id = ?",
            (expense_data['amount'], cash_account_id)
        )
    
    def generate_profit_loss_report(self, start_date, end_date):
        """Generate Profit & Loss report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Revenue
        cursor.execute('''
            SELECT SUM(total_price) FROM orders 
            WHERE created_at BETWEEN ? AND ? AND status = 'Completed'
        ''', (start_date, end_date))
        
        total_revenue = cursor.fetchone()[0] or 0
        
        # Cost of Goods Sold (approximate from menu cost prices)
        cursor.execute('''
            SELECT SUM(m.price * 0.4) FROM orders o  -- Assuming 40% COGS
            JOIN menu m ON 1=1  -- This would need proper item parsing
            WHERE o.created_at BETWEEN ? AND ? AND o.status = 'Completed'
        ''', (start_date, end_date))
        
        cogs = cursor.fetchone()[0] or 0
        gross_profit = total_revenue - cogs
        
        # Operating Expenses
        cursor.execute('''
            SELECT 
                ec.name,
                SUM(e.total_amount) as total
            FROM expenses e
            JOIN expense_categories ec ON e.category_id = ec.id
            WHERE e.expense_date BETWEEN ? AND ? AND e.status = 'paid'
            GROUP BY ec.id, ec.name
        ''', (start_date, end_date))
        
        expense_categories = cursor.fetchall()
        total_expenses = sum(exp[1] for exp in expense_categories)
        
        # Net Income
        net_income = gross_profit - total_expenses
        
        # Calculate margins
        gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        net_margin = (net_income / total_revenue * 100) if total_revenue > 0 else 0
        
        conn.close()
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'revenue': {
                'total_revenue': float(total_revenue),
                'cost_of_goods_sold': float(cogs),
                'gross_profit': float(gross_profit),
                'gross_margin_percent': round(gross_margin, 2)
            },
            'expenses': [
                {
                    'category': exp[0],
                    'amount': float(exp[1])
                }
                for exp in expense_categories
            ],
            'total_expenses': float(total_expenses),
            'net_income': float(net_income),
            'net_margin_percent': round(net_margin, 2)
        }
    
    def generate_balance_sheet(self, as_of_date=None):
        """Generate Balance Sheet"""
        if not as_of_date:
            as_of_date = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Assets
        cursor.execute('''
            SELECT account_name, current_balance 
            FROM financial_accounts 
            WHERE account_type = 'asset' AND is_active = 1
            ORDER BY account_name
        ''')
        assets = cursor.fetchall()
        total_assets = sum(asset[1] for asset in assets)
        
        # Liabilities
        cursor.execute('''
            SELECT account_name, current_balance 
            FROM financial_accounts 
            WHERE account_type = 'liability' AND is_active = 1
            ORDER BY account_name
        ''')
        liabilities = cursor.fetchall()
        total_liabilities = sum(liability[1] for liability in liabilities)
        
        # Equity
        cursor.execute('''
            SELECT account_name, current_balance 
            FROM financial_accounts 
            WHERE account_type = 'equity' AND is_active = 1
            ORDER BY account_name
        ''')
        equity = cursor.fetchall()
        total_equity = sum(eq[1] for eq in equity)
        
        conn.close()
        
        return {
            'as_of_date': as_of_date,
            'assets': [
                {
                    'account': asset[0],
                    'balance': float(asset[1])
                }
                for asset in assets
            ],
            'total_assets': float(total_assets),
            'liabilities': [
                {
                    'account': liability[0],
                    'balance': float(liability[1])
                }
                for liability in liabilities
            ],
            'total_liabilities': float(total_liabilities),
            'equity': [
                {
                    'account': eq[0],
                    'balance': float(eq[1])
                }
                for eq in equity
            ],
            'total_equity': float(total_equity),
            'total_liabilities_and_equity': float(total_liabilities + total_equity)
        }
    
    def generate_cash_flow_statement(self, start_date, end_date):
        """Generate Cash Flow Statement"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Operating Activities
        # Cash from sales
        cursor.execute('''
            SELECT SUM(net_amount) FROM payment_transactions 
            WHERE payment_date BETWEEN ? AND ? AND status = 'success'
        ''', (start_date, end_date))
        
        cash_from_sales = cursor.fetchone()[0] or 0
        
        # Cash for expenses
        cursor.execute('''
            SELECT SUM(total_amount) FROM expenses 
            WHERE expense_date BETWEEN ? AND ? AND status = 'paid'
        ''', (start_date, end_date))
        
        cash_for_expenses = cursor.fetchone()[0] or 0
        
        net_operating_cash = cash_from_sales - cash_for_expenses
        
        # Get beginning and ending cash balances
        cursor.execute("SELECT current_balance FROM financial_accounts WHERE account_name = 'Cash in Hand'")
        ending_cash = cursor.fetchone()[0] or 0
        
        # Calculate beginning cash (simplified)
        beginning_cash = ending_cash - net_operating_cash
        
        conn.close()
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date
            },
            'operating_activities': {
                'cash_from_sales': float(cash_from_sales),
                'cash_for_expenses': float(-cash_for_expenses),
                'net_operating_cash_flow': float(net_operating_cash)
            },
            'investing_activities': {
                'equipment_purchases': 0.0,
                'net_investing_cash_flow': 0.0
            },
            'financing_activities': {
                'owner_contributions': 0.0,
                'loan_proceeds': 0.0,
                'net_financing_cash_flow': 0.0
            },
            'cash_summary': {
                'beginning_cash': float(beginning_cash),
                'net_change_in_cash': float(net_operating_cash),
                'ending_cash': float(ending_cash)
            }
        }
    
    def generate_invoice_pdf(self, invoice_id):
        """Generate PDF invoice"""
        if not PDF_AVAILABLE:
            return {'error': 'PDF generation not available. Install reportlab package.'}
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get invoice details
        cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
        invoice = cursor.fetchone()
        
        if not invoice:
            conn.close()
            return None
        
        # Get invoice items
        cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        items = cursor.fetchall()
        
        conn.close()
        
        # Create PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Header
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#FF5722'),
            spaceAfter=30
        )
        
        story.append(Paragraph("INVOICE", header_style))
        story.append(Spacer(1, 12))
        
        # Invoice details
        invoice_info = [
            ['Invoice Number:', invoice[1]],
            ['Invoice Date:', invoice[11]],
            ['Due Date:', invoice[12]],
            ['Customer:', invoice[3]],
            ['Email:', invoice[4]],
        ]
        
        info_table = Table(invoice_info, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 20))
        
        # Items table
        item_data = [['Item', 'Quantity', 'Unit Price', 'Tax', 'Total']]
        
        for item in items:
            item_data.append([
                item[3],  # item_name
                str(item[4]),  # quantity
                f"₹{item[5]:.2f}",  # unit_price
                f"₹{item[7]:.2f}",  # tax_amount
                f"₹{item[8]:.2f}"   # total_amount
            ])
        
        items_table = Table(item_data, colWidths=[2.5*inch, 1*inch, 1.5*inch, 1*inch, 1.5*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF5722')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ]))
        
        story.append(items_table)
        story.append(Spacer(1, 20))
        
        # Totals
        totals_data = [
            ['Subtotal:', f"₹{invoice[6]:.2f}"],
            ['Discount:', f"₹{invoice[8]:.2f}"],
            ['Total Amount:', f"₹{invoice[9]:.2f}"]
        ]
        
        totals_table = Table(totals_data, colWidths=[4*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(totals_table)
        
        # Terms
        if invoice[13]:  # payment_terms
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"<b>Payment Terms:</b> {invoice[13]}", styles['Normal']))
        
        if invoice[14]:  # notes
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<b>Notes:</b> {invoice[14]}", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_invoice_html(self, invoice_id):
        """Generate HTML invoice as fallback when PDF is not available"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get invoice details
        cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
        invoice = cursor.fetchone()
        
        if not invoice:
            conn.close()
            return None
        
        # Get invoice items
        cursor.execute("SELECT * FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        items = cursor.fetchall()
        
        conn.close()
        
        # Generate HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Invoice {invoice[1]}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ text-align: center; color: #FF5722; font-size: 24px; margin-bottom: 30px; }}
                .invoice-info {{ margin-bottom: 20px; }}
                .invoice-info table {{ width: 100%; }}
                .invoice-info td {{ padding: 5px; }}
                .items-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .items-table th {{ background-color: #FF5722; color: white; padding: 10px; }}
                .items-table td {{ border: 1px solid #ddd; padding: 8px; text-align: center; }}
                .totals {{ text-align: right; margin-top: 20px; }}
                .totals table {{ margin-left: auto; }}
                .totals td {{ padding: 5px; }}
                .total-amount {{ font-weight: bold; font-size: 16px; }}
            </style>
        </head>
        <body>
            <div class="header">INVOICE</div>
            
            <div class="invoice-info">
                <table>
                    <tr><td><strong>Invoice Number:</strong></td><td>{invoice[1]}</td></tr>
                    <tr><td><strong>Invoice Date:</strong></td><td>{invoice[11]}</td></tr>
                    <tr><td><strong>Due Date:</strong></td><td>{invoice[12]}</td></tr>
                    <tr><td><strong>Customer:</strong></td><td>{invoice[3] or 'N/A'}</td></tr>
                    <tr><td><strong>Email:</strong></td><td>{invoice[4] or 'N/A'}</td></tr>
                </table>
            </div>
            
            <table class="items-table">
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Quantity</th>
                        <th>Unit Price</th>
                        <th>Tax</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in items:
            html += f"""
                    <tr>
                        <td>{item[3]}</td>
                        <td>{item[4]}</td>
                        <td>₹{item[5]:.2f}</td>
                        <td>₹{item[7]:.2f}</td>
                        <td>₹{item[8]:.2f}</td>
                    </tr>
            """
        
        html += f"""
                </tbody>
            </table>
            
            <div class="totals">
                <table>
                    <tr><td>Subtotal:</td><td>₹{invoice[6]:.2f}</td></tr>
                    <tr><td>Discount:</td><td>₹{invoice[8]:.2f}</td></tr>
                    <tr class="total-amount"><td>Total Amount:</td><td>₹{invoice[9]:.2f}</td></tr>
                </table>
            </div>
        """
        
        if invoice[13]:  # payment_terms
            html += f"<p><strong>Payment Terms:</strong> {invoice[13]}</p>"
        
        if invoice[14]:  # notes
            html += f"<p><strong>Notes:</strong> {invoice[14]}</p>"
        
        html += """
        </body>
        </html>
        """
        
        return html