from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import ast
import os
import sqlite3
import hashlib
import random
import string
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# ---------------------- Paths ---------------------- #
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'college.db'))
IMAGE_DIR = os.path.join(FRONTEND_DIR, 'static', 'images')

# Create image directory if not exists
os.makedirs(IMAGE_DIR, exist_ok=True)

# Uploads
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
UPLOAD_FOLDER = os.path.join(FRONTEND_DIR, 'static', 'images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ---------------------- DB Setup ---------------------- #
def initialize_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            role TEXT DEFAULT 'user',
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Menu table (added deliverable column)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS menu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            category TEXT,
            image TEXT,
            available INTEGER DEFAULT 1,
            stock INTEGER DEFAULT 0,
            deliverable INTEGER DEFAULT 0
        )
    ''')

    # Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_email TEXT,
            items TEXT,
            total_price REAL,
            status TEXT DEFAULT 'Order Received',
            otp TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Audit logs table for tracking admin actions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_email TEXT,
            action TEXT,
            target TEXT,
            details TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    def ensure_column(table, column, definition, default_expression=None):
        cursor.execute(f"PRAGMA table_info({table})")
        existing = {row[1] for row in cursor.fetchall()}
        if column not in existing:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            if default_expression:
                cursor.execute(
                    f"UPDATE {table} SET {column} = COALESCE({column}, {default_expression})"
                )

    ensure_column('users', 'created_at', "TEXT", "CURRENT_TIMESTAMP")
    ensure_column('orders', 'created_at', "TEXT", "CURRENT_TIMESTAMP")
    ensure_column('orders', 'updated_at', "TEXT", "CURRENT_TIMESTAMP")
    ensure_column('menu', 'created_at', "TEXT", "CURRENT_TIMESTAMP")
    ensure_column('menu', 'updated_at', "TEXT", "CURRENT_TIMESTAMP")

    # Insert default admin if not exists
    cursor.execute("SELECT * FROM users WHERE email = ?", ('kioskadmin@saintgits.org',))
    if not cursor.fetchone():
        admin_password = hashlib.sha256("QAZwsx1!".encode()).hexdigest()
        cursor.execute('''
            INSERT INTO users (name, email, password, role, status)
            VALUES (?, ?, ?, ?, ?)
        ''', ('Admin', 'kioskadmin@saintgits.org', admin_password, 'admin', 'approved'))

    conn.commit()
    conn.close()

initialize_db()

# ---------------------- Helper ---------------------- #
def generate_otp():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# ---------------------- Serve Pages ---------------------- #
@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/index.html')
def index_html():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/admin')
def admin():
    return send_from_directory(FRONTEND_DIR, 'admin.html')

@app.route('/admin.css')
def admin_css():
    return send_from_directory(FRONTEND_DIR, 'admin.css')

@app.route('/admin.js')
def admin_js():
    return send_from_directory(FRONTEND_DIR, 'admin.js')

@app.route('/staff')
def staff():
    return send_from_directory(FRONTEND_DIR, 'staff.html')

@app.route('/users')
def users_page():
    return send_from_directory(FRONTEND_DIR, 'users.html')

@app.route('/register')
def register():
    return send_from_directory(FRONTEND_DIR, 'register.html')

@app.route('/static/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ---------------------- Auth APIs ---------------------- #
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not all([name, email, password]):
        return jsonify({'error': 'Missing required fields'}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                       (name, email, hashed_password))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Registered successfully. Awaiting admin approval.'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already registered'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'error': 'Email and password required'}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, role, status FROM users WHERE email = ? AND password = ?",
                   (email, hashed_password))
    user = cursor.fetchone()
    conn.close()

    if user:
        if user[4] != 'approved':
            return jsonify({'error': 'Account pending approval'}), 403
        return jsonify({
            'id': user[0],
            'name': user[1],
            'email': user[2],
            'role': user[3]
        }), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

# ---------------------- Admin APIs ---------------------- #
@app.route('/api/users/pending', methods=['GET'])
def get_pending_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users WHERE status = 'pending'")
    users = cursor.fetchall()
    conn.close()
    return jsonify(users), 200

@app.route('/api/users/approve', methods=['POST'])
def approve_user():
    data = request.get_json()
    email = data.get('email')
    role = data.get('role', 'user')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status='approved', role=? WHERE email=?", (role, email))
    conn.commit()
    conn.close()
    return jsonify({'message': f'User {email} approved with role {role}'}), 200

@app.route('/api/users/assign-role', methods=['POST'])
def assign_role():
    data = request.get_json()
    email = data.get('email')
    role = data.get('role')
    if not email or not role:
        return jsonify({'error': 'Email and role are required'}), 400
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET role=? WHERE email=? AND status='approved'", (role, email))
    conn.commit()
    conn.close()
    return jsonify({'message': f'Role {role} assigned to {email}'}), 200

@app.route('/api/users/delete', methods=['POST'])
def delete_user():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE email=?", (email,))
    conn.commit()
    conn.close()
    return jsonify({'message': f'User {email} deleted'}), 200

@app.route('/api/users', methods=['GET'])
def get_users():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT email, role, status FROM users")
    users = [{'email': email, 'role': role, 'status': status} for (email, role, status) in cursor.fetchall()]
    conn.close()
    return jsonify(users)

# ---------------------- Menu APIs ---------------------- #
@app.route('/api/menu', methods=['GET'])
def get_menu():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM menu")
    menu = cursor.fetchall()
    conn.close()
    # Convert to dicts
    return jsonify([
        {
            'id': row[0],
            'name': row[1],
            'price': row[2],
            'category': row[3],
            'image': row[4],
            'available': bool(row[5]),
            'stock': row[6],
            'deliverable': bool(row[7])
        }
        for row in menu
    ])

@app.route('/api/menu', methods=['POST'])
def add_menu_item():
    name = request.form.get('name')
    price = request.form.get('price')
    category = request.form.get('category')
    stock = request.form.get('stock', 0)  # default 0
    deliverable = int(request.form.get('deliverable', 0))
    image = request.files.get('image')

    if not all([name, price, category, image]):
        return jsonify({'error': 'Missing fields'}), 400

    filename = secure_filename(image.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    image.save(filepath)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO menu (name, price, category, image, stock, deliverable) VALUES (?,?,?,?,?,?)",
                   (name, price, category, filename, stock, deliverable))

    conn.commit()
    conn.close()
    return jsonify({'message': 'Menu item added successfully'}), 201

@app.route('/api/menu/<int:item_id>', methods=['PUT'])
def update_or_toggle_menu_item(item_id):
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        name = request.form.get('name')
        price = request.form.get('price')
        category = request.form.get('category')
        stock = request.form.get('stock')
        deliverable = request.form.get('deliverable')
        image = request.files.get('image')

        sets, vals = [], []
        if name: sets.append("name=?"); vals.append(name)
        if price: sets.append("price=?"); vals.append(float(price))
        if category: sets.append("category=?"); vals.append(category)
        if stock: sets.append("stock=?"); vals.append(int(stock))
        if deliverable is not None: sets.append("deliverable=?"); vals.append(int(deliverable))
        if image:
            filename = secure_filename(image.filename)
            filepath = os.path.join(IMAGE_DIR, filename)
            image.save(filepath)
            sets.append("image=?"); vals.append(filename)

        if not sets:
            return jsonify({'error': 'No fields to update'}), 400

        vals.append(item_id)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE menu SET {', '.join(sets)} WHERE id=?", vals)
        conn.commit()
        conn.close()
        return jsonify({'message': 'Menu item updated with form'}), 200

    elif request.data:
        data = request.get_json(force=True, silent=True) or {}
        name = data.get('name')
        price = data.get('price')
        available = data.get('available')
        category = data.get('category')
        stock = data.get('stock')
        deliverable = data.get('deliverable')

        sets, vals = [], []
        if name is not None: sets.append("name=?"); vals.append(name)
        if price is not None: sets.append("price=?"); vals.append(float(price))
        if available is not None: sets.append("available=?"); vals.append(1 if bool(available) else 0)
        if category is not None: sets.append("category=?"); vals.append(category)
        if stock is not None: sets.append("stock=?"); vals.append(int(stock))
        if deliverable is not None: sets.append("deliverable=?"); vals.append(int(deliverable))

        if not sets:
            return jsonify({'error': 'No fields to update'}), 400

        vals.append(item_id)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE menu SET {', '.join(sets)} WHERE id=?", vals)
        conn.commit()
        conn.close()
        return jsonify({'message': 'Menu item updated'}), 200
    else:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT available FROM menu WHERE id=?", (item_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return jsonify({'error': 'Item not found'}), 404
        new_status = 0 if row[0] == 1 else 1
        cursor.execute("UPDATE menu SET available=? WHERE id=?", (new_status, item_id))
        conn.commit()
        conn.close()
        return jsonify({'message': 'Availability toggled', 'available': bool(new_status)}), 200

@app.route('/api/menu/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM menu WHERE id=?", (item_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Menu item deleted successfully'}), 200

# ---------------------- Orders APIs ---------------------- #
@app.route('/api/orders', methods=['GET'])
def get_orders():
    limit = request.args.get('limit', type=int)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT id, customer_name, customer_email, items, total_price, otp, status, created_at FROM orders ORDER BY id DESC"
    if limit:
        query += " LIMIT ?"
        cursor.execute(query, (limit,))
    else:
        cursor.execute(query)
    
    rows = cursor.fetchall()
    conn.close()

    orders = []
    for r in rows:
        # Parse items safely
        try:
            order_data = ast.literal_eval(r[3]) if isinstance(r[3], str) else (r[3] or {})
        except (ValueError, SyntaxError):
            order_data = {"items": []}

        detailed_items = []
        for i in order_data.get("items", []):
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("SELECT name FROM menu WHERE id=?", (i["id"],))
                m = cur.fetchone()
                conn.close()
                item_name = m[0] if m else f"ID:{i['id']}"
            except Exception:
                item_name = f"ID:{i['id']}"

            detailed_items.append({
                "id": i["id"],
                "name": item_name,
                "qty": i["qty"]
            })

        orders.append({
            "id": r[0],
            "customer_name": r[1],
            "customer_email": r[2],
            "items": detailed_items,   # ✅ always array with name+qty
            "total_price": r[4],
            "otp": r[5],
            "status": r[6],
            "created_at": r[7] if len(r) > 7 else None,
            "delivery_mode": order_data.get("delivery_mode", "pickup"),
            "department": order_data.get("department"),
            "classroom": order_data.get("classroom"),
            "block": order_data.get("block"),
            "expected_time": order_data.get("expected_time")
        })
    return jsonify(orders)

@app.route('/api/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    name = data.get('customer_name')
    email = data.get('customer_email')
    items = data.get('items')
    total_price = data.get('total_price')
    delivery_mode = data.get('delivery_mode', 'pickup')

    # Delivery details (only if delivery selected)
    classroom = data.get('classroom')
    department = data.get('department')
    block = data.get('block')
    expected_time = data.get('expected_time')

    if not all([name, email, items, total_price]):
        return jsonify({'error': 'Missing fields'}), 400

    if not isinstance(items, list):
        return jsonify({'error': 'Items must be a list'}), 400

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check stock
    for item in items:
        cursor.execute("SELECT stock FROM menu WHERE id=?", (item['id'],))
        row = cursor.fetchone()
        if not row or row[0] < item['qty']:
            conn.close()
            return jsonify({'error': f"Not enough stock for item {item['id']}"}), 400

    # Delivery charge logic (by quantity not rupees)
    if delivery_mode == 'delivery':
        deliverable_items = []
        total_qty = 0
        for i in items:
            cursor.execute("SELECT deliverable FROM menu WHERE id=?", (i['id'],))
            r = cursor.fetchone()
            if r and r[0] == 1:
                deliverable_items.append(i)
            total_qty += i['qty']
        if deliverable_items and total_qty < 5:
            total_price += 5

    # Deduct stock
    for item in items:
        cursor.execute("UPDATE menu SET stock = stock - ? WHERE id=?", (item['qty'], item['id']))

    otp = generate_otp()

    # Save items + delivery details together as JSON string
    order_payload = {
        "items": items,
        "classroom": classroom,
        "department": department,
        "block": block,
        "expected_time": expected_time,
        "delivery_mode": delivery_mode
    }

    cursor.execute(
        "INSERT INTO orders (customer_name, customer_email, items, total_price, otp) VALUES (?,?,?,?,?)",
        (name, email, str(order_payload), total_price, otp)
    )

    conn.commit()
    conn.close()
    return jsonify({'message': 'Order created successfully', 'otp': otp, 'final_price': total_price}), 201

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.get_json()
    status = data.get('status')
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Order status updated successfully'}), 200

# ---------------------- Analytics API ---------------------- #
@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Basic metrics
        cursor.execute("SELECT COUNT(*) FROM users WHERE role='user'")
        total_users = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM orders")
        total_orders = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(total_price) FROM orders WHERE status='Completed'")
        total_revenue = cursor.fetchone()[0] or 0

        cursor.execute("SELECT AVG(total_price) FROM orders")
        avg_order_value = cursor.fetchone()[0] or 0

        conversion_rate = (total_orders / total_users * 100) if total_users else 0

        cursor.execute("SELECT customer_email FROM orders")
        customer_emails = [row[0] for row in cursor.fetchall() if row[0]]
        email_counter = Counter(customer_emails)
        returning_customers = sum(1 for count in email_counter.values() if count > 1)
        customer_retention = (returning_customers / total_users * 100) if total_users else 0

        cursor.execute("SELECT created_at FROM orders")
        raw_order_dates = [row[0] for row in cursor.fetchall() if row[0]]

        def parse_ts(value):
            if not value:
                return None
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            return None

        order_datetimes = [parse_ts(ts) for ts in raw_order_dates]
        order_datetimes = [dt for dt in order_datetimes if dt]

        now = datetime.utcnow()
        recent_start = now - timedelta(days=30)
        previous_start = now - timedelta(days=60)
        last_week_start = now - timedelta(days=6)

        recent_orders = sum(1 for dt in order_datetimes if dt >= recent_start)
        previous_orders = sum(1 for dt in order_datetimes if previous_start <= dt < recent_start)
        if previous_orders == 0:
            monthly_growth = 0 if recent_orders == 0 else 100
        else:
            monthly_growth = ((recent_orders - previous_orders) / previous_orders) * 100

        cursor.execute("SELECT created_at FROM users WHERE role='user'")
        raw_user_dates = [parse_ts(row[0]) for row in cursor.fetchall() if row[0]]
        user_month_counts = Counter((dt.year, dt.month) for dt in raw_user_dates if dt)

        def month_offset(base, offset):
            year = base.year
            month = base.month - offset
            while month <= 0:
                month += 12
                year -= 1
            return year, month

        user_growth_labels = []
        user_growth_values = []
        for i in range(5, -1, -1):
            year, month = month_offset(now, i)
            month_date = datetime(year, month, 1)
            user_growth_labels.append(month_date.strftime('%b'))
            user_growth_values.append(user_month_counts.get((year, month), 0))

        new_customers = sum(1 for dt in raw_user_dates if dt and dt >= recent_start)
        avg_orders_per_customer = (total_orders / total_users) if total_users else 0

        cursor.execute("SELECT id, name, category, price FROM menu")
        menu_rows = cursor.fetchall()
        menu_by_id = {
            row[0]: {
                'name': row[1],
                'category': row[2] or 'Uncategorised',
                'price': row[3] or 0.0
            }
            for row in menu_rows
        }

        cursor.execute("SELECT items, total_price, status, created_at FROM orders")
        order_rows = cursor.fetchall()

        category_revenue = defaultdict(float)
        top_items_map = defaultdict(lambda: {'orders': 0, 'revenue': 0.0, 'category': 'Uncategorised'})
        order_pattern_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        order_pattern_counts = {label: 0 for label in order_pattern_labels}

        for items_str, order_total, status, created_at in order_rows:
            payload = {}
            if items_str:
                try:
                    payload = ast.literal_eval(items_str)
                except (ValueError, SyntaxError):
                    payload = {}

            items = payload.get('items', []) if isinstance(payload, dict) else []
            order_dt = parse_ts(created_at)

            for item in items:
                item_id = item.get('id')
                qty = item.get('qty', 0)
                menu_item = menu_by_id.get(item_id)
                if not menu_item or qty <= 0:
                    continue

                revenue = menu_item['price'] * qty
                if status == 'Completed':
                    category_revenue[menu_item['category']] += revenue

                top_entry = top_items_map[menu_item['name']]
                top_entry['orders'] += qty
                top_entry['revenue'] += revenue
                top_entry['category'] = menu_item['category']

            if order_dt and order_dt >= last_week_start:
                day_label = order_pattern_labels[order_dt.weekday()]
                order_pattern_counts[day_label] += 1

        if category_revenue:
            revenue_items = sorted(category_revenue.items(), key=lambda x: x[1], reverse=True)
            revenue_labels = [item[0] for item in revenue_items]
            revenue_values = [round(item[1], 2) for item in revenue_items]
        else:
            revenue_labels = ['No Data']
            revenue_values = [0]

        top_items = [
            {
                'name': name,
                'category': data['category'],
                'orders': data['orders'],
                'revenue': round(data['revenue'], 2),
                'rating': None
            }
            for name, data in top_items_map.items()
            if data['orders'] > 0
        ]
        top_items.sort(key=lambda x: x['orders'], reverse=True)
        top_items = top_items[:5]

        order_pattern_values = [order_pattern_counts[label] for label in order_pattern_labels]

        analytics_data = {
            'conversionRate': round(conversion_rate, 1),
            'avgOrderValue': round(avg_order_value, 2),
            'customerRetention': round(customer_retention, 1),
            'monthlyGrowth': round(monthly_growth, 1),
            'newCustomers': new_customers,
            'returningCustomers': returning_customers,
            'avgOrdersPerCustomer': round(avg_orders_per_customer, 1),
            'userGrowth': {
                'labels': user_growth_labels,
                'values': user_growth_values
            },
            'revenueByCategory': {
                'labels': revenue_labels,
                'values': revenue_values
            },
            'orderPatterns': {
                'labels': order_pattern_labels,
                'values': order_pattern_values
            },
            'topItems': top_items
        }

        return jsonify(analytics_data), 200

    except Exception as e:
        print(f"Analytics error: {e}")
        return jsonify({'error': 'Failed to compute analytics'}), 500
    
    finally:
        conn.close()

# ---------------------- Helper Functions ---------------------- #
def log_audit_action(admin_email, action, target, details=""):
    """Log admin actions for audit trail"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (admin_email, action, target, details)
            VALUES (?, ?, ?, ?)
        """, (admin_email, action, target, details))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Audit log error: {e}")

# ---------------------- Enhanced Admin APIs ---------------------- #

# Order Status Update with Audit Log
@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status_enhanced(order_id):
    data = request.get_json()
    new_status = data.get('status')
    admin_email = data.get('admin_email', 'admin')
    
    if not new_status:
        return jsonify({'error': 'Status is required'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get current order details for audit
    cursor.execute("SELECT status, customer_name FROM orders WHERE id = ?", (order_id,))
    order = cursor.fetchone()
    
    if not order:
        conn.close()
        return jsonify({'error': 'Order not found'}), 404
    
    old_status = order[0]
    customer_name = order[1]
    
    # Update order status and updated_at
    cursor.execute("""
        UPDATE orders 
        SET status = ?, updated_at = CURRENT_TIMESTAMP 
        WHERE id = ?
    """, (new_status, order_id))
    
    conn.commit()
    conn.close()
    
    # Log audit action
    log_audit_action(admin_email, 'UPDATE_ORDER_STATUS', 
                    f'Order #{order_id} ({customer_name})', 
                    f'Changed from {old_status} to {new_status}')
    
    return jsonify({'message': 'Order status updated successfully'}), 200

# Bulk Order Status Update
@app.route('/api/orders/bulk-status', methods=['PUT'])
def bulk_update_order_status():
    data = request.get_json()
    order_ids = data.get('order_ids', [])
    new_status = data.get('status')
    admin_email = data.get('admin_email', 'admin')
    
    if not order_ids or not new_status:
        return jsonify({'error': 'Order IDs and status are required'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updated_count = 0
    for order_id in order_ids:
        cursor.execute("SELECT customer_name FROM orders WHERE id = ?", (order_id,))
        order = cursor.fetchone()
        if order:
            cursor.execute("""
                UPDATE orders 
                SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (new_status, order_id))
            updated_count += 1
            
            # Log audit action
            log_audit_action(admin_email, 'BULK_UPDATE_ORDER_STATUS', 
                            f'Order #{order_id} ({order[0]})', 
                            f'Updated to {new_status}')
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': f'{updated_count} orders updated successfully'}), 200

# Enhanced Menu APIs with Audit Logging
@app.route('/api/menu/<int:item_id>/audit', methods=['PUT'])
def update_menu_item_with_audit(item_id):
    admin_email = request.form.get('admin_email') or request.json.get('admin_email', 'admin')
    
    # Get original item for audit
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM menu WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    
    if not item:
        conn.close()
        return jsonify({'error': 'Menu item not found'}), 404
    
    item_name = item[0]
    conn.close()
    
    # Use existing update logic
    result = update_or_toggle_menu_item(item_id)
    
    # Log audit action if successful
    if result[1] == 200:
        log_audit_action(admin_email, 'UPDATE_MENU_ITEM', item_name, 'Menu item updated')
    
    return result

@app.route('/api/menu/<int:item_id>/delete-audit', methods=['DELETE'])
def delete_menu_item_with_audit(item_id):
    data = request.get_json() or {}
    admin_email = data.get('admin_email', 'admin')
    
    # Get item name for audit
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM menu WHERE id = ?", (item_id,))
    item = cursor.fetchone()
    
    if not item:
        conn.close()
        return jsonify({'error': 'Menu item not found'}), 404
    
    item_name = item[0]
    
    # Delete the item
    cursor.execute("DELETE FROM menu WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    
    # Log audit action
    log_audit_action(admin_email, 'DELETE_MENU_ITEM', item_name, 'Menu item deleted')
    
    return jsonify({'message': 'Menu item deleted successfully'}), 200

# Bulk Menu Operations
@app.route('/api/menu/bulk-delete', methods=['DELETE'])
def bulk_delete_menu_items():
    data = request.get_json()
    item_ids = data.get('item_ids', [])
    admin_email = data.get('admin_email', 'admin')
    
    if not item_ids:
        return jsonify({'error': 'Item IDs are required'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    deleted_items = []
    for item_id in item_ids:
        cursor.execute("SELECT name FROM menu WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        if item:
            cursor.execute("DELETE FROM menu WHERE id = ?", (item_id,))
            deleted_items.append(item[0])
            log_audit_action(admin_email, 'BULK_DELETE_MENU_ITEM', item[0], 'Bulk deletion')
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': f'{len(deleted_items)} items deleted successfully'}), 200

@app.route('/api/menu/bulk-toggle', methods=['PUT'])
def bulk_toggle_menu_availability():
    data = request.get_json()
    item_ids = data.get('item_ids', [])
    available = data.get('available', True)
    admin_email = data.get('admin_email', 'admin')
    
    if not item_ids:
        return jsonify({'error': 'Item IDs are required'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updated_items = []
    for item_id in item_ids:
        cursor.execute("SELECT name FROM menu WHERE id = ?", (item_id,))
        item = cursor.fetchone()
        if item:
            cursor.execute("UPDATE menu SET available = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                          (1 if available else 0, item_id))
            updated_items.append(item[0])
            log_audit_action(admin_email, 'BULK_TOGGLE_MENU_AVAILABILITY', item[0], 
                           f'Set availability to {available}')
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': f'{len(updated_items)} items updated successfully'}), 200

# Enhanced User Management with Audit Logging
@app.route('/api/users/approve-audit', methods=['POST'])
def approve_user_with_audit():
    data = request.get_json()
    email = data.get('email')
    role = data.get('role', 'user')
    admin_email = data.get('admin_email', 'admin')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET status='approved', role=? WHERE email=?", (role, email))
    conn.commit()
    conn.close()
    
    # Log audit action
    log_audit_action(admin_email, 'APPROVE_USER', email, f'Approved with role: {role}')
    
    return jsonify({'message': f'User {email} approved with role {role}'}), 200

@app.route('/api/users/delete-audit', methods=['POST'])
def delete_user_with_audit():
    data = request.get_json()
    email = data.get('email')
    admin_email = data.get('admin_email', 'admin')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE email=?", (email,))
    conn.commit()
    conn.close()
    
    # Log audit action
    log_audit_action(admin_email, 'DELETE_USER', email, 'User account deleted')
    
    return jsonify({'message': f'User {email} deleted'}), 200

# Bulk User Operations
@app.route('/api/users/bulk-approve', methods=['POST'])
def bulk_approve_users():
    data = request.get_json()
    emails = data.get('emails', [])
    role = data.get('role', 'user')
    admin_email = data.get('admin_email', 'admin')
    
    if not emails:
        return jsonify({'error': 'Email list is required'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    approved_count = 0
    for email in emails:
        cursor.execute("UPDATE users SET status='approved', role=? WHERE email=?", (role, email))
        if cursor.rowcount > 0:
            approved_count += 1
            log_audit_action(admin_email, 'BULK_APPROVE_USER', email, f'Bulk approved with role: {role}')
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': f'{approved_count} users approved successfully'}), 200

@app.route('/api/users/bulk-delete', methods=['POST'])
def bulk_delete_users():
    data = request.get_json()
    emails = data.get('emails', [])
    admin_email = data.get('admin_email', 'admin')
    
    if not emails:
        return jsonify({'error': 'Email list is required'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    deleted_count = 0
    for email in emails:
        cursor.execute("DELETE FROM users WHERE email=?", (email,))
        if cursor.rowcount > 0:
            deleted_count += 1
            log_audit_action(admin_email, 'BULK_DELETE_USER', email, 'Bulk deletion')
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': f'{deleted_count} users deleted successfully'}), 200

# ---------------------- Reports APIs ---------------------- #

@app.route('/api/reports/orders', methods=['GET'])
def orders_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status_filter = request.args.get('status')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT * FROM orders WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND date(created_at) >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND date(created_at) <= ?"
        params.append(end_date)
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    orders = cursor.fetchall()
    
    # Calculate summary statistics
    total_orders = len(orders)
    total_revenue = sum(order[4] for order in orders if order[4])  # total_price is index 4
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Status distribution
    status_counts = {}
    for order in orders:
        status = order[5]  # status is index 5
        status_counts[status] = status_counts.get(status, 0) + 1
    
    conn.close()
    
    return jsonify({
        'orders': [
            {
                'id': order[0],
                'customer_name': order[1],
                'customer_email': order[2],
                'items': order[3],
                'total_price': order[4],
                'status': order[5],
                'otp': order[6],
                'created_at': order[7],
                'updated_at': order[8] if len(order) > 8 else None
            }
            for order in orders
        ],
        'summary': {
            'total_orders': total_orders,
            'total_revenue': round(total_revenue, 2),
            'avg_order_value': round(avg_order_value, 2),
            'status_distribution': status_counts
        }
    }), 200

@app.route('/api/reports/users', methods=['GET'])
def users_report():
    role_filter = request.args.get('role')
    status_filter = request.args.get('status')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT * FROM users WHERE 1=1"
    params = []
    
    if role_filter:
        query += " AND role = ?"
        params.append(role_filter)
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    users = cursor.fetchall()
    
    # Calculate summary statistics
    total_users = len(users)
    role_counts = {}
    status_counts = {}
    
    for user in users:
        role = user[4]  # role is index 4
        status = user[5]  # status is index 5
        role_counts[role] = role_counts.get(role, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1
    
    conn.close()
    
    return jsonify({
        'users': [
            {
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'role': user[4],
                'status': user[5],
                'created_at': user[6] if len(user) > 6 else None
            }
            for user in users
        ],
        'summary': {
            'total_users': total_users,
            'role_distribution': role_counts,
            'status_distribution': status_counts
        }
    }), 200

@app.route('/api/reports/menu', methods=['GET'])
def menu_report():
    category_filter = request.args.get('category')
    low_stock_threshold = int(request.args.get('low_stock_threshold', 5))
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT * FROM menu WHERE 1=1"
    params = []
    
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)
    
    query += " ORDER BY category, name"
    
    cursor.execute(query, params)
    menu_items = cursor.fetchall()
    
    # Calculate summary statistics
    total_items = len(menu_items)
    available_items = sum(1 for item in menu_items if item[5])  # available is index 5
    low_stock_items = sum(1 for item in menu_items if item[6] < low_stock_threshold)  # stock is index 6
    
    category_counts = {}
    for item in menu_items:
        category = item[3]  # category is index 3
        category_counts[category] = category_counts.get(category, 0) + 1
    
    conn.close()
    
    return jsonify({
        'menu_items': [
            {
                'id': item[0],
                'name': item[1],
                'price': item[2],
                'category': item[3],
                'image': item[4],
                'available': bool(item[5]),
                'stock': item[6],
                'deliverable': bool(item[7]),
                'low_stock': item[6] < low_stock_threshold
            }
            for item in menu_items
        ],
        'summary': {
            'total_items': total_items,
            'available_items': available_items,
            'low_stock_items': low_stock_items,
            'category_distribution': category_counts,
            'low_stock_threshold': low_stock_threshold
        }
    }), 200

# ---------------------- CSV Export APIs ---------------------- #
import csv
from io import StringIO

@app.route('/api/reports/orders/csv', methods=['GET'])
def export_orders_csv():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status_filter = request.args.get('status')
    
    # Get orders data using the same logic as orders_report
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT * FROM orders WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND date(created_at) >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND date(created_at) <= ?"
        params.append(end_date)
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    orders = cursor.fetchall()
    conn.close()
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Order ID', 'Customer Name', 'Customer Email', 'Items', 'Total Price', 'Status', 'OTP', 'Created At', 'Updated At'])
    
    # Write data
    for order in orders:
        writer.writerow([
            order[0],  # id
            order[1],  # customer_name
            order[2],  # customer_email
            order[3],  # items
            order[4],  # total_price
            order[5],  # status
            order[6],  # otp
            order[7],  # created_at
            order[8] if len(order) > 8 else ''  # updated_at
        ])
    
    # Prepare response
    from flask import Response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=orders_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

@app.route('/api/reports/users/csv', methods=['GET'])
def export_users_csv():
    role_filter = request.args.get('role')
    status_filter = request.args.get('status')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT * FROM users WHERE 1=1"
    params = []
    
    if role_filter:
        query += " AND role = ?"
        params.append(role_filter)
    
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    
    query += " ORDER BY created_at DESC"
    
    cursor.execute(query, params)
    users = cursor.fetchall()
    conn.close()
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['User ID', 'Name', 'Email', 'Role', 'Status', 'Created At'])
    
    # Write data
    for user in users:
        writer.writerow([
            user[0],  # id
            user[1],  # name
            user[2],  # email
            user[4],  # role
            user[5],  # status
            user[6] if len(user) > 6 else ''  # created_at
        ])
    
    # Prepare response
    from flask import Response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=users_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

@app.route('/api/reports/menu/csv', methods=['GET'])
def export_menu_csv():
    category_filter = request.args.get('category')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = "SELECT * FROM menu WHERE 1=1"
    params = []
    
    if category_filter:
        query += " AND category = ?"
        params.append(category_filter)
    
    query += " ORDER BY category, name"
    
    cursor.execute(query, params)
    menu_items = cursor.fetchall()
    conn.close()
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Item ID', 'Name', 'Price', 'Category', 'Image', 'Available', 'Stock', 'Deliverable'])
    
    # Write data
    for item in menu_items:
        writer.writerow([
            item[0],  # id
            item[1],  # name
            item[2],  # price
            item[3],  # category
            item[4],  # image
            'Yes' if item[5] else 'No',  # available
            item[6],  # stock
            'Yes' if item[7] else 'No'   # deliverable
        ])
    
    # Prepare response
    from flask import Response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=menu_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

# ---------------------- Audit Logs APIs ---------------------- #

@app.route('/api/audit-logs', methods=['GET'])
def get_audit_logs():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    search = request.args.get('search', '')
    action_filter = request.args.get('action')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Build query
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []
    
    if search:
        query += " AND (admin_email LIKE ? OR action LIKE ? OR target LIKE ? OR details LIKE ?)"
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param, search_param])
    
    if action_filter:
        query += " AND action = ?"
        params.append(action_filter)
    
    if start_date:
        query += " AND date(timestamp) >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND date(timestamp) <= ?"
        params.append(end_date)
    
    query += " ORDER BY timestamp DESC"
    
    # Get total count
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]
    
    # Add pagination
    offset = (page - 1) * per_page
    query += f" LIMIT {per_page} OFFSET {offset}"
    
    cursor.execute(query, params)
    logs = cursor.fetchall()
    conn.close()
    
    return jsonify({
        'logs': [
            {
                'id': log[0],
                'admin_email': log[1],
                'action': log[2],
                'target': log[3],
                'details': log[4],
                'timestamp': log[5]
            }
            for log in logs
        ],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total_count,
            'pages': (total_count + per_page - 1) // per_page
        }
    }), 200

@app.route('/api/audit-logs/csv', methods=['GET'])
def export_audit_logs_csv():
    search = request.args.get('search', '')
    action_filter = request.args.get('action')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Build query (similar to get_audit_logs but without pagination)
    query = "SELECT * FROM audit_logs WHERE 1=1"
    params = []
    
    if search:
        query += " AND (admin_email LIKE ? OR action LIKE ? OR target LIKE ? OR details LIKE ?)"
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param, search_param])
    
    if action_filter:
        query += " AND action = ?"
        params.append(action_filter)
    
    if start_date:
        query += " AND date(timestamp) >= ?"
        params.append(start_date)
    
    if end_date:
        query += " AND date(timestamp) <= ?"
        params.append(end_date)
    
    query += " ORDER BY timestamp DESC"
    
    cursor.execute(query, params)
    logs = cursor.fetchall()
    conn.close()
    
    # Create CSV content
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Log ID', 'Admin Email', 'Action', 'Target', 'Details', 'Timestamp'])
    
    # Write data
    for log in logs:
        writer.writerow([
            log[0],  # id
            log[1],  # admin_email
            log[2],  # action
            log[3],  # target
            log[4],  # details
            log[5]   # timestamp
        ])
    
    # Prepare response
    from flask import Response
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=audit_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

# ---------------------- Dashboard Statistics API ---------------------- #

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get counts
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status NOT IN ('Completed', 'Cancelled')")
    active_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'pending'")
    pending_approvals = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM menu WHERE stock < 5")
    low_stock_items = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(total_price) FROM orders WHERE status = 'Completed'")
    total_revenue = cursor.fetchone()[0] or 0
    
    # Get recent orders for chart data
    cursor.execute("""
        SELECT status, COUNT(*) 
        FROM orders 
        GROUP BY status
    """)
    status_distribution = dict(cursor.fetchall())
    
    # Get sales trend (last 7 days)
    cursor.execute("""
        SELECT date(created_at) as order_date, COUNT(*) as order_count, SUM(total_price) as daily_revenue
        FROM orders 
        WHERE created_at >= date('now', '-7 days')
        GROUP BY date(created_at)
        ORDER BY order_date
    """)
    sales_trend = cursor.fetchall()
    
    # Get top selling items
    cursor.execute("""
        SELECT m.name, m.category, COUNT(*) as order_count
        FROM orders o
        JOIN menu m ON o.items LIKE '%' || m.name || '%'
        WHERE o.status = 'Completed'
        GROUP BY m.name, m.category
        ORDER BY order_count DESC
        LIMIT 5
    """)
    top_items = cursor.fetchall()
    
    conn.close()
    
    return jsonify({
        'kpi': {
            'total_users': total_users,
            'total_orders': total_orders,
            'active_orders': active_orders,
            'pending_approvals': pending_approvals,
            'low_stock_items': low_stock_items,
            'total_revenue': round(total_revenue, 2)
        },
        'charts': {
            'status_distribution': status_distribution,
            'sales_trend': [
                {
                    'date': row[0],
                    'orders': row[1],
                    'revenue': row[2] or 0
                }
                for row in sales_trend
            ],
            'top_items': [
                {
                    'name': row[0],
                    'category': row[1],
                    'orders': row[2]
                }
                for row in top_items
            ]
        }
    }), 200

# ---------------------- Bulk Operations API ---------------------- #
@app.route('/api/orders/bulk-update', methods=['POST'])
def bulk_update_orders():
    try:
        data = request.get_json()
        order_ids = data.get('order_ids', [])
        status = data.get('status')
        
        if not order_ids or not status:
            return jsonify({'error': 'Missing order_ids or status'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Update orders
        placeholders = ','.join(['?' for _ in order_ids])
        cursor.execute(f"""
            UPDATE orders 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders})
        """, [status] + order_ids)
        
        updated_count = cursor.rowcount
        
        # Log the bulk update action
        cursor.execute("""
            INSERT INTO audit_logs (admin_email, action, target, details)
            VALUES (?, ?, ?, ?)
        """, ('admin', 'BULK_UPDATE_ORDERS', f"{updated_count} orders", f"Status changed to {status}"))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': f'{updated_count} orders updated successfully',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------------------- Notifications API ---------------------- #
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        notifications = []
        
        # Check for pending user approvals
        cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'pending'")
        pending_users = cursor.fetchone()[0]
        if pending_users > 0:
            notifications.append({
                'id': 'pending_users',
                'type': 'warning',
                'title': 'Pending User Approvals',
                'message': f'{pending_users} users waiting for approval',
                'timestamp': datetime.now().isoformat(),
                'action': 'view_users',
                'actionText': 'Review'
            })
        
        # Check for low stock items
        cursor.execute("SELECT COUNT(*) FROM menu WHERE stock < 5 AND available = 1")
        low_stock = cursor.fetchone()[0]
        if low_stock > 0:
            notifications.append({
                'id': 'low_stock',
                'type': 'warning',
                'title': 'Low Stock Alert',
                'message': f'{low_stock} items running low on stock',
                'timestamp': datetime.now().isoformat(),
                'action': 'view_menu',
                'actionText': 'Restock'
            })
        
        # Check for active orders
        cursor.execute("SELECT COUNT(*) FROM orders WHERE status NOT IN ('Completed', 'Cancelled')")
        active_orders = cursor.fetchone()[0]
        if active_orders > 0:
            notifications.append({
                'id': 'active_orders',
                'type': 'info',
                'title': 'Active Orders',
                'message': f'{active_orders} orders need attention',
                'timestamp': datetime.now().isoformat(),
                'action': 'view_orders',
                'actionText': 'Manage'
            })
        
        conn.close()
        return jsonify(notifications), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------------------- Run Server ---------------------- #
if __name__ == '__main__':
    app.run(debug=True)
