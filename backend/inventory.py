"""
Advanced Inventory Management System
Features: Supplier management, purchase orders, barcode support, batch tracking, cost management
"""

import sqlite3
import json
from datetime import datetime, timedelta
import uuid
import io
import base64
from collections import defaultdict
import pandas as pd
import numpy as np
from reportlab.graphics.barcode import qr
from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

class InventoryManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_inventory_tables()
    
    def init_inventory_tables(self):
        """Initialize advanced inventory management tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Suppliers/Vendors table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                contact_person TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                gstin TEXT,
                payment_terms TEXT, -- JSON: net_days, discount_terms
                rating REAL DEFAULT 0.0,
                is_active INTEGER DEFAULT 1,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Product categories with hierarchical structure
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS product_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                parent_id INTEGER,
                description TEXT,
                markup_percentage REAL DEFAULT 0.0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES product_categories (id)
            )
        ''')
        
        # Enhanced menu items with inventory details
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                menu_id INTEGER,
                sku TEXT UNIQUE,
                barcode TEXT,
                qr_code TEXT,
                category_id INTEGER,
                supplier_id INTEGER,
                unit_of_measure TEXT DEFAULT 'pieces', -- pieces, kg, liters, etc.
                cost_price REAL DEFAULT 0.0,
                selling_price REAL DEFAULT 0.0,
                markup_percentage REAL DEFAULT 0.0,
                minimum_stock_level INTEGER DEFAULT 0,
                maximum_stock_level INTEGER DEFAULT 0,
                reorder_level INTEGER DEFAULT 0,
                reorder_quantity INTEGER DEFAULT 0,
                shelf_life_days INTEGER,
                storage_requirements TEXT, -- JSON: temperature, humidity, etc.
                is_perishable INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (menu_id) REFERENCES menu (id),
                FOREIGN KEY (category_id) REFERENCES product_categories (id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
            )
        ''')
        
        # Stock batches/lots for expiry tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_item_id INTEGER NOT NULL,
                batch_number TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                remaining_quantity INTEGER NOT NULL,
                cost_per_unit REAL DEFAULT 0.0,
                manufacturing_date TEXT,
                expiry_date TEXT,
                received_date TEXT DEFAULT CURRENT_TIMESTAMP,
                supplier_id INTEGER,
                purchase_order_id INTEGER,
                status TEXT DEFAULT 'active', -- active, expired, consumed, damaged
                notes TEXT,
                FOREIGN KEY (inventory_item_id) REFERENCES inventory_items (id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
                FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders (id)
            )
        ''')
        
        # Purchase orders
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                po_number TEXT UNIQUE NOT NULL,
                supplier_id INTEGER NOT NULL,
                status TEXT DEFAULT 'draft', -- draft, sent, confirmed, received, cancelled
                order_date TEXT DEFAULT CURRENT_TIMESTAMP,
                expected_delivery_date TEXT,
                actual_delivery_date TEXT,
                subtotal REAL DEFAULT 0.0,
                tax_amount REAL DEFAULT 0.0,
                total_amount REAL DEFAULT 0.0,
                payment_status TEXT DEFAULT 'pending', -- pending, partial, paid
                notes TEXT,
                created_by INTEGER,
                approved_by INTEGER,
                received_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
                FOREIGN KEY (created_by) REFERENCES users (id),
                FOREIGN KEY (approved_by) REFERENCES users (id),
                FOREIGN KEY (received_by) REFERENCES users (id)
            )
        ''')
        
        # Purchase order items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchase_order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_order_id INTEGER NOT NULL,
                inventory_item_id INTEGER NOT NULL,
                quantity_ordered INTEGER NOT NULL,
                quantity_received INTEGER DEFAULT 0,
                unit_cost REAL NOT NULL,
                total_cost REAL NOT NULL,
                notes TEXT,
                FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders (id),
                FOREIGN KEY (inventory_item_id) REFERENCES inventory_items (id)
            )
        ''')
        
        # Stock movements/transactions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_item_id INTEGER NOT NULL,
                batch_id INTEGER,
                movement_type TEXT NOT NULL, -- in, out, adjustment, transfer, waste
                quantity INTEGER NOT NULL, -- positive for in, negative for out
                reference_type TEXT, -- order, purchase, adjustment, waste
                reference_id INTEGER,
                cost_per_unit REAL DEFAULT 0.0,
                reason TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inventory_item_id) REFERENCES inventory_items (id),
                FOREIGN KEY (batch_id) REFERENCES stock_batches (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # Waste tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS waste_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_item_id INTEGER NOT NULL,
                batch_id INTEGER,
                quantity_wasted INTEGER NOT NULL,
                waste_reason TEXT, -- expired, damaged, spoiled, overproduction
                waste_cost REAL DEFAULT 0.0,
                disposal_method TEXT,
                reported_by INTEGER,
                reported_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inventory_item_id) REFERENCES inventory_items (id),
                FOREIGN KEY (batch_id) REFERENCES stock_batches (id),
                FOREIGN KEY (reported_by) REFERENCES users (id)
            )
        ''')
        
        # Supplier evaluations
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS supplier_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                evaluation_date TEXT DEFAULT CURRENT_TIMESTAMP,
                quality_rating INTEGER CHECK(quality_rating >= 1 AND quality_rating <= 5),
                delivery_rating INTEGER CHECK(delivery_rating >= 1 AND delivery_rating <= 5),
                price_rating INTEGER CHECK(price_rating >= 1 AND price_rating <= 5),
                service_rating INTEGER CHECK(service_rating >= 1 AND service_rating <= 5),
                overall_rating REAL,
                comments TEXT,
                evaluated_by INTEGER,
                FOREIGN KEY (supplier_id) REFERENCES suppliers (id),
                FOREIGN KEY (evaluated_by) REFERENCES users (id)
            )
        ''')
        
        # Inventory alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inventory_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_item_id INTEGER NOT NULL,
                alert_type TEXT NOT NULL, -- low_stock, out_of_stock, expiring_soon, expired
                priority TEXT DEFAULT 'medium', -- low, medium, high, critical
                message TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                is_acknowledged INTEGER DEFAULT 0,
                acknowledged_by INTEGER,
                acknowledged_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inventory_item_id) REFERENCES inventory_items (id),
                FOREIGN KEY (acknowledged_by) REFERENCES users (id)
            )
        ''')
        
        # Recipe/BOM (Bill of Materials) for prepared items
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipe_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                menu_item_id INTEGER NOT NULL,
                ingredient_item_id INTEGER NOT NULL,
                quantity_required REAL NOT NULL,
                unit TEXT NOT NULL,
                cost_per_unit REAL DEFAULT 0.0,
                notes TEXT,
                FOREIGN KEY (menu_item_id) REFERENCES menu (id),
                FOREIGN KEY (ingredient_item_id) REFERENCES inventory_items (id)
            )
        ''')
        
        # Stock taking/cycle counts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                count_date TEXT DEFAULT CURRENT_TIMESTAMP,
                count_type TEXT DEFAULT 'full', -- full, partial, cycle
                status TEXT DEFAULT 'in_progress', -- in_progress, completed, approved
                counted_by INTEGER,
                approved_by INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (counted_by) REFERENCES users (id),
                FOREIGN KEY (approved_by) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_count_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_count_id INTEGER NOT NULL,
                inventory_item_id INTEGER NOT NULL,
                system_quantity INTEGER NOT NULL,
                counted_quantity INTEGER NOT NULL,
                variance INTEGER NOT NULL, -- counted - system
                variance_cost REAL DEFAULT 0.0,
                notes TEXT,
                FOREIGN KEY (stock_count_id) REFERENCES stock_counts (id),
                FOREIGN KEY (inventory_item_id) REFERENCES inventory_items (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Insert default data
        self.insert_default_inventory_data()
    
    def insert_default_inventory_data(self):
        """Insert default inventory data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Default product categories
        default_categories = [
            ('Food Items', None, 'All food items', 25.0),
            ('Beverages', None, 'All beverages', 30.0),
            ('Snacks', None, 'Light refreshments', 35.0),
            ('Raw Materials', None, 'Cooking ingredients', 15.0),
            ('Packaging', None, 'Containers and wrapping', 20.0),
        ]
        
        for name, parent_id, desc, markup in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO product_categories (name, parent_id, description, markup_percentage)
                VALUES (?, ?, ?, ?)
            ''', (name, parent_id, desc, markup))
        
        # Default suppliers
        default_suppliers = [
            ('Local Vegetable Vendor', 'Ravi Kumar', 'ravi@localveggies.com', '+91-9876543210', 'Market Street, Local Market', None, '{"net_days": 7}', 4.0),
            ('Dairy Products Co.', 'Priya Sharma', 'orders@dairyco.com', '+91-9876543211', 'Dairy Complex, Industrial Area', '22ABCDE1234F1Z5', '{"net_days": 15, "early_discount": 2}', 4.5),
            ('Beverage Distributors', 'Amit Singh', 'amit@beverages.com', '+91-9876543212', 'Warehouse District', '22FGHIJ5678K1L9', '{"net_days": 30}', 4.2),
        ]
        
        for name, contact, email, phone, address, gstin, terms, rating in default_suppliers:
            cursor.execute('''
                INSERT OR IGNORE INTO suppliers 
                (name, contact_person, email, phone, address, gstin, payment_terms, rating)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, contact, email, phone, address, gstin, terms, rating))
        
        conn.commit()
        conn.close()
    
    def generate_sku(self, category_prefix='ITM'):
        """Generate unique SKU"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_suffix = str(uuid.uuid4())[:6].upper()
        return f"{category_prefix}{timestamp}{random_suffix}"
    
    def generate_barcode(self, sku):
        """Generate barcode for item"""
        # In a real implementation, you would use a proper barcode library
        # For now, we'll just return the SKU as barcode
        return sku
    
    def generate_qr_code(self, item_data):
        """Generate QR code for item"""
        qr_data = json.dumps({
            'sku': item_data.get('sku'),
            'name': item_data.get('name'),
            'category': item_data.get('category'),
            'price': item_data.get('price')
        })
        
        # Generate QR code and return as base64
        qr_code = qr.QrCodeWidget(qr_data)
        bounds = qr_code.getBounds()
        width = bounds[2] - bounds[0]
        height = bounds[3] - bounds[1]
        
        from reportlab.graphics.shapes import Drawing
        d = Drawing(width, height, transform=[1, 0, 0, 1, -bounds[0], -bounds[1]])
        d.add(qr_code)
        
        # Convert to base64
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            from reportlab.graphics import renderPM
            renderPM.drawToFile(d, f.name, fmt='PNG')
            with open(f.name, 'rb') as img_file:
                qr_base64 = base64.b64encode(img_file.read()).decode()
        
        return f"data:image/png;base64,{qr_base64}"
    
    def create_inventory_item(self, item_data):
        """Create new inventory item"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate SKU if not provided
        sku = item_data.get('sku') or self.generate_sku()
        barcode = item_data.get('barcode') or self.generate_barcode(sku)
        
        cursor.execute('''
            INSERT INTO inventory_items 
            (menu_id, sku, barcode, category_id, supplier_id, unit_of_measure, 
             cost_price, selling_price, markup_percentage, minimum_stock_level, 
             maximum_stock_level, reorder_level, reorder_quantity, shelf_life_days, 
             storage_requirements, is_perishable)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item_data.get('menu_id'),
            sku,
            barcode,
            item_data.get('category_id'),
            item_data.get('supplier_id'),
            item_data.get('unit_of_measure', 'pieces'),
            item_data.get('cost_price', 0.0),
            item_data.get('selling_price', 0.0),
            item_data.get('markup_percentage', 0.0),
            item_data.get('minimum_stock_level', 0),
            item_data.get('maximum_stock_level', 0),
            item_data.get('reorder_level', 0),
            item_data.get('reorder_quantity', 0),
            item_data.get('shelf_life_days'),
            json.dumps(item_data.get('storage_requirements', {})),
            item_data.get('is_perishable', 0)
        ))
        
        item_id = cursor.lastrowid
        
        # Generate QR code if requested
        if item_data.get('generate_qr_code'):
            qr_code_data = self.generate_qr_code({
                'sku': sku,
                'name': item_data.get('name', ''),
                'category': item_data.get('category', ''),
                'price': item_data.get('selling_price', 0.0)
            })
            
            cursor.execute(
                "UPDATE inventory_items SET qr_code = ? WHERE id = ?",
                (qr_code_data, item_id)
            )
        
        conn.commit()
        conn.close()
        
        return item_id
    
    def create_purchase_order(self, po_data):
        """Create new purchase order"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Generate PO number
        po_number = f"PO{datetime.now().strftime('%Y%m%d')}{random.randint(1000, 9999)}"
        
        cursor.execute('''
            INSERT INTO purchase_orders 
            (po_number, supplier_id, expected_delivery_date, subtotal, tax_amount, 
             total_amount, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            po_number,
            po_data['supplier_id'],
            po_data.get('expected_delivery_date'),
            po_data.get('subtotal', 0.0),
            po_data.get('tax_amount', 0.0),
            po_data.get('total_amount', 0.0),
            po_data.get('notes'),
            po_data.get('created_by')
        ))
        
        po_id = cursor.lastrowid
        
        # Add PO items
        for item in po_data.get('items', []):
            cursor.execute('''
                INSERT INTO purchase_order_items 
                (purchase_order_id, inventory_item_id, quantity_ordered, unit_cost, total_cost, notes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                po_id,
                item['inventory_item_id'],
                item['quantity_ordered'],
                item['unit_cost'],
                item['quantity_ordered'] * item['unit_cost'],
                item.get('notes')
            ))
        
        conn.commit()
        conn.close()
        
        return po_id
    
    def receive_purchase_order(self, po_id, received_items, received_by):
        """Receive purchase order and update stock"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update PO status
        cursor.execute('''
            UPDATE purchase_orders 
            SET status = 'received', actual_delivery_date = CURRENT_TIMESTAMP, received_by = ?
            WHERE id = ?
        ''', (received_by, po_id))
        
        # Process received items
        for item in received_items:
            item_id = item['inventory_item_id']
            quantity_received = item['quantity_received']
            cost_per_unit = item.get('cost_per_unit', 0.0)
            batch_number = item.get('batch_number', f"B{datetime.now().strftime('%Y%m%d%H%M%S')}")
            expiry_date = item.get('expiry_date')
            
            # Update PO item
            cursor.execute('''
                UPDATE purchase_order_items 
                SET quantity_received = quantity_received + ?
                WHERE purchase_order_id = ? AND inventory_item_id = ?
            ''', (quantity_received, po_id, item_id))
            
            # Create stock batch
            cursor.execute('''
                INSERT INTO stock_batches 
                (inventory_item_id, batch_number, quantity, remaining_quantity, 
                 cost_per_unit, expiry_date, supplier_id, purchase_order_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id, batch_number, quantity_received, quantity_received,
                cost_per_unit, expiry_date, 
                item.get('supplier_id'), po_id
            ))
            
            batch_id = cursor.lastrowid
            
            # Record stock movement
            cursor.execute('''
                INSERT INTO stock_movements 
                (inventory_item_id, batch_id, movement_type, quantity, 
                 reference_type, reference_id, cost_per_unit, reason, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id, batch_id, 'in', quantity_received,
                'purchase', po_id, cost_per_unit, 'Purchase order received', received_by
            ))
            
            # Update menu stock
            cursor.execute('''
                UPDATE menu 
                SET stock = stock + ?
                WHERE id = (SELECT menu_id FROM inventory_items WHERE id = ?)
            ''', (quantity_received, item_id))
        
        conn.commit()
        conn.close()
        
        # Check if reorder alerts can be cleared
        self.check_and_update_alerts()
    
    def consume_stock(self, order_id, order_items, consumed_by):
        """Consume stock for order using FIFO"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in order_items:
            menu_item_id = item['id']
            quantity_needed = item['qty']
            
            # Get inventory item
            cursor.execute(
                "SELECT id FROM inventory_items WHERE menu_id = ?",
                (menu_item_id,)
            )
            inventory_item = cursor.fetchone()
            
            if not inventory_item:
                continue
            
            inventory_item_id = inventory_item[0]
            
            # Get available batches (FIFO - oldest first)
            cursor.execute('''
                SELECT id, remaining_quantity, cost_per_unit, expiry_date
                FROM stock_batches 
                WHERE inventory_item_id = ? AND remaining_quantity > 0 AND status = 'active'
                ORDER BY CASE 
                    WHEN expiry_date IS NOT NULL THEN expiry_date 
                    ELSE '9999-12-31' 
                END ASC, received_date ASC
            ''', (inventory_item_id,))
            
            available_batches = cursor.fetchall()
            remaining_needed = quantity_needed
            
            for batch_id, batch_qty, cost_per_unit, expiry_date in available_batches:
                if remaining_needed <= 0:
                    break
                
                # Check if batch is expired
                if expiry_date and datetime.now() > datetime.fromisoformat(expiry_date):
                    continue
                
                consume_from_batch = min(remaining_needed, batch_qty)
                
                # Update batch quantity
                cursor.execute('''
                    UPDATE stock_batches 
                    SET remaining_quantity = remaining_quantity - ?
                    WHERE id = ?
                ''', (consume_from_batch, batch_id))
                
                # Record stock movement
                cursor.execute('''
                    INSERT INTO stock_movements 
                    (inventory_item_id, batch_id, movement_type, quantity, 
                     reference_type, reference_id, cost_per_unit, reason, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    inventory_item_id, batch_id, 'out', -consume_from_batch,
                    'order', order_id, cost_per_unit, f'Order #{order_id}', consumed_by
                ))
                
                remaining_needed -= consume_from_batch
            
            # Update menu stock
            actual_consumed = quantity_needed - remaining_needed
            cursor.execute(
                "UPDATE menu SET stock = stock - ? WHERE id = ?",
                (actual_consumed, menu_item_id)
            )
        
        conn.commit()
        conn.close()
        
        # Check for low stock alerts
        self.check_and_update_alerts()
    
    def check_and_update_alerts(self):
        """Check inventory levels and create alerts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear old alerts
        cursor.execute("DELETE FROM inventory_alerts WHERE is_active = 1")
        
        # Check low stock
        cursor.execute('''
            SELECT ii.id, m.name, SUM(sb.remaining_quantity) as current_stock, ii.reorder_level, ii.minimum_stock_level
            FROM inventory_items ii
            JOIN menu m ON ii.menu_id = m.id
            LEFT JOIN stock_batches sb ON ii.id = sb.inventory_item_id AND sb.status = 'active'
            GROUP BY ii.id, m.name, ii.reorder_level, ii.minimum_stock_level
            HAVING current_stock <= ii.reorder_level
        ''')
        
        low_stock_items = cursor.fetchall()
        
        for item_id, name, current_stock, reorder_level, min_level in low_stock_items:
            current_stock = current_stock or 0
            
            if current_stock == 0:
                alert_type = 'out_of_stock'
                priority = 'critical'
                message = f'{name} is out of stock'
            elif current_stock <= min_level:
                alert_type = 'low_stock'
                priority = 'high'
                message = f'{name} is critically low (Current: {current_stock})'
            else:
                alert_type = 'low_stock'
                priority = 'medium'
                message = f'{name} is below reorder level (Current: {current_stock}, Reorder: {reorder_level})'
            
            cursor.execute('''
                INSERT INTO inventory_alerts 
                (inventory_item_id, alert_type, priority, message)
                VALUES (?, ?, ?, ?)
            ''', (item_id, alert_type, priority, message))
        
        # Check expiring items
        expiry_threshold = (datetime.now() + timedelta(days=7)).isoformat()
        cursor.execute('''
            SELECT sb.inventory_item_id, m.name, sb.remaining_quantity, sb.expiry_date
            FROM stock_batches sb
            JOIN inventory_items ii ON sb.inventory_item_id = ii.id
            JOIN menu m ON ii.menu_id = m.id
            WHERE sb.expiry_date IS NOT NULL 
            AND sb.expiry_date <= ?
            AND sb.remaining_quantity > 0
            AND sb.status = 'active'
        ''', (expiry_threshold,))
        
        expiring_items = cursor.fetchall()
        
        for item_id, name, quantity, expiry_date in expiring_items:
            expiry_dt = datetime.fromisoformat(expiry_date)
            days_to_expiry = (expiry_dt - datetime.now()).days
            
            if days_to_expiry <= 0:
                alert_type = 'expired'
                priority = 'critical'
                message = f'{name} has expired ({quantity} units)'
            elif days_to_expiry <= 3:
                alert_type = 'expiring_soon'
                priority = 'high'
                message = f'{name} expires in {days_to_expiry} days ({quantity} units)'
            else:
                alert_type = 'expiring_soon'
                priority = 'medium'
                message = f'{name} expires in {days_to_expiry} days ({quantity} units)'
            
            cursor.execute('''
                INSERT INTO inventory_alerts 
                (inventory_item_id, alert_type, priority, message)
                VALUES (?, ?, ?, ?)
            ''', (item_id, alert_type, priority, message))
        
        conn.commit()
        conn.close()
    
    def get_inventory_dashboard(self):
        """Get comprehensive inventory dashboard data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Stock summary
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT ii.id) as total_items,
                SUM(sb.remaining_quantity) as total_stock,
                SUM(sb.remaining_quantity * sb.cost_per_unit) as total_value,
                COUNT(CASE WHEN SUM(sb.remaining_quantity) <= ii.reorder_level THEN 1 END) as low_stock_count
            FROM inventory_items ii
            LEFT JOIN stock_batches sb ON ii.id = sb.inventory_item_id AND sb.status = 'active'
            GROUP BY ii.id
        ''')
        
        summary = cursor.fetchone()
        
        # Alerts summary
        cursor.execute('''
            SELECT priority, COUNT(*) as count
            FROM inventory_alerts 
            WHERE is_active = 1
            GROUP BY priority
        ''')
        
        alerts = dict(cursor.fetchall())
        
        # Top moving items (last 30 days)
        cursor.execute('''
            SELECT 
                m.name,
                SUM(ABS(sm.quantity)) as total_movement,
                ii.id
            FROM stock_movements sm
            JOIN inventory_items ii ON sm.inventory_item_id = ii.id
            JOIN menu m ON ii.menu_id = m.id
            WHERE sm.created_at >= date('now', '-30 days')
            AND sm.movement_type = 'out'
            GROUP BY ii.id, m.name
            ORDER BY total_movement DESC
            LIMIT 10
        ''')
        
        top_movers = cursor.fetchall()
        
        # Expiring items (next 7 days)
        expiry_threshold = (datetime.now() + timedelta(days=7)).isoformat()
        cursor.execute('''
            SELECT 
                m.name,
                sb.remaining_quantity,
                sb.expiry_date,
                sb.batch_number
            FROM stock_batches sb
            JOIN inventory_items ii ON sb.inventory_item_id = ii.id
            JOIN menu m ON ii.menu_id = m.id
            WHERE sb.expiry_date IS NOT NULL 
            AND sb.expiry_date <= ?
            AND sb.remaining_quantity > 0
            AND sb.status = 'active'
            ORDER BY sb.expiry_date ASC
        ''', (expiry_threshold,))
        
        expiring_items = cursor.fetchall()
        
        # Purchase orders summary
        cursor.execute('''
            SELECT 
                status,
                COUNT(*) as count,
                SUM(total_amount) as total_value
            FROM purchase_orders
            WHERE order_date >= date('now', '-30 days')
            GROUP BY status
        ''')
        
        po_summary = cursor.fetchall()
        
        conn.close()
        
        return {
            'summary': {
                'total_items': summary[0] if summary else 0,
                'total_stock': summary[1] if summary else 0,
                'total_value': float(summary[2]) if summary and summary[2] else 0,
                'low_stock_count': summary[3] if summary else 0
            },
            'alerts': {
                'critical': alerts.get('critical', 0),
                'high': alerts.get('high', 0),
                'medium': alerts.get('medium', 0),
                'low': alerts.get('low', 0)
            },
            'top_movers': [
                {
                    'name': item[0],
                    'movement': item[1],
                    'item_id': item[2]
                }
                for item in top_movers
            ],
            'expiring_items': [
                {
                    'name': item[0],
                    'quantity': item[1],
                    'expiry_date': item[2],
                    'batch_number': item[3],
                    'days_to_expiry': (datetime.fromisoformat(item[2]) - datetime.now()).days
                }
                for item in expiring_items
            ],
            'purchase_orders': [
                {
                    'status': po[0],
                    'count': po[1],
                    'total_value': float(po[2])
                }
                for po in po_summary
            ]
        }
    
    def generate_reorder_suggestions(self):
        """Generate automatic reorder suggestions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get items below reorder level
        cursor.execute('''
            SELECT 
                ii.id,
                m.name,
                ii.sku,
                SUM(sb.remaining_quantity) as current_stock,
                ii.reorder_level,
                ii.reorder_quantity,
                ii.supplier_id,
                s.name as supplier_name,
                ii.cost_price,
                -- Calculate average consumption (last 30 days)
                IFNULL((
                    SELECT AVG(ABS(quantity)) 
                    FROM stock_movements sm 
                    WHERE sm.inventory_item_id = ii.id 
                    AND sm.movement_type = 'out'
                    AND sm.created_at >= date('now', '-30 days')
                ), 0) as avg_daily_consumption
            FROM inventory_items ii
            JOIN menu m ON ii.menu_id = m.id
            LEFT JOIN stock_batches sb ON ii.id = sb.inventory_item_id AND sb.status = 'active'
            LEFT JOIN suppliers s ON ii.supplier_id = s.id
            GROUP BY ii.id, m.name, ii.sku, ii.reorder_level, ii.reorder_quantity, 
                     ii.supplier_id, s.name, ii.cost_price
            HAVING current_stock <= ii.reorder_level
            ORDER BY current_stock ASC
        ''')
        
        reorder_items = cursor.fetchall()
        
        suggestions = []
        for item in reorder_items:
            (item_id, name, sku, current_stock, reorder_level, reorder_qty, 
             supplier_id, supplier_name, cost_price, avg_consumption) = item
            
            current_stock = current_stock or 0
            
            # Calculate suggested quantity based on consumption
            days_of_stock = (current_stock / avg_consumption) if avg_consumption > 0 else 0
            
            # Suggest quantity for 30 days + safety stock
            suggested_qty = max(reorder_qty, int(avg_consumption * 30 + reorder_level))
            
            suggestions.append({
                'item_id': item_id,
                'name': name,
                'sku': sku,
                'current_stock': current_stock,
                'reorder_level': reorder_level,
                'suggested_quantity': suggested_qty,
                'supplier_id': supplier_id,
                'supplier_name': supplier_name,
                'estimated_cost': suggested_qty * cost_price,
                'days_of_stock_remaining': round(days_of_stock, 1),
                'priority': 'critical' if current_stock == 0 else 'high' if days_of_stock < 3 else 'medium'
            })
        
        conn.close()
        return suggestions
    
    def perform_stock_count(self, count_data):
        """Perform stock count and identify variances"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create stock count record
        cursor.execute('''
            INSERT INTO stock_counts 
            (count_type, counted_by, notes)
            VALUES (?, ?, ?)
        ''', (
            count_data.get('count_type', 'full'),
            count_data.get('counted_by'),
            count_data.get('notes')
        ))
        
        count_id = cursor.lastrowid
        
        # Process counted items
        total_variance_cost = 0
        
        for item in count_data.get('items', []):
            item_id = item['inventory_item_id']
            counted_qty = item['counted_quantity']
            
            # Get system quantity
            cursor.execute('''
                SELECT SUM(remaining_quantity), AVG(cost_per_unit)
                FROM stock_batches 
                WHERE inventory_item_id = ? AND status = 'active'
            ''', (item_id,))
            
            result = cursor.fetchone()
            system_qty = result[0] or 0
            avg_cost = result[1] or 0
            
            variance = counted_qty - system_qty
            variance_cost = variance * avg_cost
            total_variance_cost += variance_cost
            
            # Record count item
            cursor.execute('''
                INSERT INTO stock_count_items 
                (stock_count_id, inventory_item_id, system_quantity, 
                 counted_quantity, variance, variance_cost, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                count_id, item_id, system_qty, counted_qty, 
                variance, variance_cost, item.get('notes')
            ))
            
            # If there's a variance, create adjustment
            if variance != 0:
                # Create stock movement for adjustment
                cursor.execute('''
                    INSERT INTO stock_movements 
                    (inventory_item_id, movement_type, quantity, 
                     reference_type, reference_id, cost_per_unit, 
                     reason, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item_id, 'adjustment', variance, 'stock_count', count_id,
                    avg_cost, f'Stock count adjustment: {variance:+d}', 
                    count_data.get('counted_by')
                ))
                
                # Update menu stock
                cursor.execute('''
                    UPDATE menu 
                    SET stock = stock + ?
                    WHERE id = (SELECT menu_id FROM inventory_items WHERE id = ?)
                ''', (variance, item_id))
        
        # Update stock count status
        cursor.execute(
            "UPDATE stock_counts SET status = 'completed' WHERE id = ?",
            (count_id,)
        )
        
        conn.commit()
        conn.close()
        
        return {
            'count_id': count_id,
            'total_variance_cost': total_variance_cost,
            'items_counted': len(count_data.get('items', []))
        }

class WasteManager:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def record_waste(self, waste_data):
        """Record waste/spoilage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        item_id = waste_data['inventory_item_id']
        quantity = waste_data['quantity_wasted']
        reason = waste_data.get('waste_reason', 'unknown')
        
        # Get cost per unit from latest batch
        cursor.execute('''
            SELECT cost_per_unit FROM stock_batches 
            WHERE inventory_item_id = ? AND remaining_quantity > 0
            ORDER BY received_date DESC LIMIT 1
        ''', (item_id,))
        
        result = cursor.fetchone()
        cost_per_unit = result[0] if result else 0
        waste_cost = quantity * cost_per_unit
        
        # Record waste
        cursor.execute('''
            INSERT INTO waste_tracking 
            (inventory_item_id, batch_id, quantity_wasted, waste_reason, 
             waste_cost, disposal_method, reported_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            item_id, waste_data.get('batch_id'), quantity, reason,
            waste_cost, waste_data.get('disposal_method'), 
            waste_data.get('reported_by')
        ))
        
        # Create stock movement
        cursor.execute('''
            INSERT INTO stock_movements 
            (inventory_item_id, batch_id, movement_type, quantity, 
             reference_type, reference_id, cost_per_unit, reason, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            item_id, waste_data.get('batch_id'), 'waste', -quantity,
            'waste', cursor.lastrowid, cost_per_unit, 
            f'Waste: {reason}', waste_data.get('reported_by')
        ))
        
        # Update batch and menu stock
        if waste_data.get('batch_id'):
            cursor.execute('''
                UPDATE stock_batches 
                SET remaining_quantity = remaining_quantity - ?
                WHERE id = ?
            ''', (quantity, waste_data['batch_id']))
        
        cursor.execute('''
            UPDATE menu 
            SET stock = stock - ?
            WHERE id = (SELECT menu_id FROM inventory_items WHERE id = ?)
        ''', (quantity, item_id))
        
        conn.commit()
        conn.close()
        
        return waste_cost
    
    def get_waste_analysis(self, period_days=30):
        """Get waste analysis for specified period"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=period_days)).isoformat()
        
        # Waste by reason
        cursor.execute('''
            SELECT 
                waste_reason,
                SUM(quantity_wasted) as total_quantity,
                SUM(waste_cost) as total_cost,
                COUNT(*) as incidents
            FROM waste_tracking 
            WHERE reported_at >= ?
            GROUP BY waste_reason
            ORDER BY total_cost DESC
        ''', (start_date,))
        
        waste_by_reason = cursor.fetchall()
        
        # Waste by item
        cursor.execute('''
            SELECT 
                m.name,
                SUM(wt.quantity_wasted) as total_quantity,
                SUM(wt.waste_cost) as total_cost
            FROM waste_tracking wt
            JOIN inventory_items ii ON wt.inventory_item_id = ii.id
            JOIN menu m ON ii.menu_id = m.id
            WHERE wt.reported_at >= ?
            GROUP BY ii.id, m.name
            ORDER BY total_cost DESC
            LIMIT 10
        ''', (start_date,))
        
        waste_by_item = cursor.fetchall()
        
        # Daily waste trend
        cursor.execute('''
            SELECT 
                DATE(reported_at) as waste_date,
                SUM(quantity_wasted) as daily_quantity,
                SUM(waste_cost) as daily_cost
            FROM waste_tracking 
            WHERE reported_at >= ?
            GROUP BY DATE(reported_at)
            ORDER BY waste_date
        ''', (start_date,))
        
        daily_trend = cursor.fetchall()
        
        conn.close()
        
        return {
            'waste_by_reason': [
                {
                    'reason': item[0],
                    'quantity': item[1],
                    'cost': float(item[2]),
                    'incidents': item[3]
                }
                for item in waste_by_reason
            ],
            'waste_by_item': [
                {
                    'item': item[0],
                    'quantity': item[1],
                    'cost': float(item[2])
                }
                for item in waste_by_item
            ],
            'daily_trend': [
                {
                    'date': item[0],
                    'quantity': item[1],
                    'cost': float(item[2])
                }
                for item in daily_trend
            ],
            'total_waste_cost': sum(item[2] for item in waste_by_reason),
            'total_waste_quantity': sum(item[1] for item in waste_by_reason)
        }