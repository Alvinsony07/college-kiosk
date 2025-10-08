from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sqlite3
import hashlib
import random
import string
from datetime import datetime
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
            status TEXT DEFAULT 'pending'
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
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

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

@app.route('/admin')
def admin():
    return send_from_directory(FRONTEND_DIR, 'admin.html')

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

# Serve CSS and JS files
@app.route('/<path:filename>')
def serve_static(filename):
    if filename.endswith('.css') or filename.endswith('.js'):
        return send_from_directory(FRONTEND_DIR, filename)
    return send_from_directory(FRONTEND_DIR, filename)

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
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, customer_name, customer_email, items, total_price, otp, status, created_at FROM orders ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    orders = []
    for r in rows:
        # Parse items safely
        try:
            order_data = eval(r[3]) if isinstance(r[3], str) else r[3]
        except Exception:
            order_data = {"items": []}

        detailed_items = []
        for i in order_data.get("items", []):
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute("SELECT name, price FROM menu WHERE id=?", (i["id"],))
                m = cur.fetchone()
                conn.close()
                item_name = m[0] if m else f"ID:{i['id']}"
                item_price = m[1] if m else 0
            except Exception:
                item_name = f"ID:{i['id']}"
                item_price = 0

            detailed_items.append({
                "id": i["id"],
                "name": item_name,
                "qty": i["qty"],
                "price": item_price
            })

        orders.append({
            "id": r[0],
            "customer_name": r[1],
            "customer_email": r[2],
            "items": detailed_items,   # ✅ always array with name+qty
            "total_price": r[4],
            "otp": r[5],
            "status": r[6],
            "created_at": r[7]
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

    # Get current timestamp
    current_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    cursor.execute(
        "INSERT INTO orders (customer_name, customer_email, items, total_price, otp, created_at) VALUES (?,?,?,?,?,?)",
        (name, email, str(order_payload), total_price, otp, current_timestamp)
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

# ---------------------- Run Server ---------------------- #
if __name__ == '__main__':
    app.run(debug=True)
