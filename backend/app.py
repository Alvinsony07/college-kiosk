from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sqlite3
import hashlib
import random
import string
import json
import re
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# ---------------------- Paths ---------------------- #
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'college.db'))
UPLOAD_FOLDER = os.path.join(FRONTEND_DIR, 'static', 'images')

# Create directories
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


# ---------------------- Context Manager for DB ---------------------- #
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """Context manager for database connections to ensure proper cleanup."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        raise
    finally:
        conn.close()


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

    # Notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient_email TEXT,
            title TEXT,
            message TEXT,
            type TEXT,
            priority TEXT DEFAULT 'normal',
            read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Activity Log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_email TEXT,
            action TEXT,
            details TEXT,
            ip_address TEXT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
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

# ---------------------- Validation Functions ---------------------- #
def validate_email(email):
    """Validate email format."""
    if not email or not isinstance(email, str):
        return False
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_password(password):
    """
    Validate password strength.
    Requirements: At least 8 characters, one uppercase, one lowercase, one digit, one special char.
    """
    if not password or not isinstance(password, str):
        return False, "Password is required"
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Valid"

def validate_positive_number(value, field_name="Value"):
    """Validate that a value is a positive number."""
    try:
        num = float(value)
        if num <= 0:
            return False, f"{field_name} must be positive"
        return True, num
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"

def validate_non_negative_integer(value, field_name="Value"):
    """Validate that a value is a non-negative integer."""
    try:
        num = int(value)
        if num < 0:
            return False, f"{field_name} must be non-negative"
        return True, num
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid integer"

def validate_file_upload(file):
    """Validate uploaded file type and size."""
    if not file or file.filename == '':
        return False, "No file provided"
    
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    filename = file.filename.lower()
    if not any(filename.endswith(f'.{ext}') for ext in allowed_extensions):
        return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
    
    # Check file size (already enforced by Flask config, but double-check)
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)  # Reset file pointer
    
    if file_size > 16 * 1024 * 1024:  # 16MB
        return False, "File size must be under 16MB"
    
    return True, "Valid"

def validate_required_fields(data, required_fields):
    """Check if all required fields are present and non-empty."""
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, "Valid"

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

    # Validate required fields
    is_valid, message = validate_required_fields(data, ['name', 'email', 'password'])
    if not is_valid:
        return jsonify({'error': message}), 400

    # Validate email format
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400

    # Validate password strength
    is_valid, message = validate_password(password)
    if not is_valid:
        return jsonify({'error': message}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                           (name, email, hashed_password))
            conn.commit()
        return jsonify({'message': 'Registered successfully. Awaiting admin approval.'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Email already registered'}), 409
    except Exception as e:
        print(f"Error during registration: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Validate required fields
    is_valid, message = validate_required_fields(data, ['email', 'password'])
    if not is_valid:
        return jsonify({'error': message}), 400

    # Validate email format
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, email, role, status FROM users WHERE email = ? AND password = ?",
                           (email, hashed_password))
            user = cursor.fetchone()

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
    except Exception as e:
        print(f"Error during login: {e}")
        return jsonify({'error': 'Login failed'}), 500

# ---------------------- Admin APIs ---------------------- #
@app.route('/api/users/pending', methods=['GET'])
def get_pending_users():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, email FROM users WHERE status = 'pending'")
            users = cursor.fetchall()
        return jsonify(users), 200
    except Exception as e:
        print(f"Error fetching pending users: {e}")
        return jsonify({'error': 'Failed to fetch pending users'}), 500

@app.route('/api/users/approve', methods=['POST'])
def approve_user():
    data = request.get_json()
    email = data.get('email')
    role = data.get('role', 'user')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    # Validate email format
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate role
    valid_roles = ['user', 'staff', 'admin']
    if role not in valid_roles:
        return jsonify({'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'}), 400
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email=?", (email,))
            if not cursor.fetchone():
                return jsonify({'error': 'User not found'}), 404
            
            cursor.execute("UPDATE users SET status='approved', role=? WHERE email=?", (role, email))
            conn.commit()
        return jsonify({'message': f'User {email} approved with role {role}'}), 200
    except Exception as e:
        print(f"Error approving user: {e}")
        return jsonify({'error': 'Failed to approve user'}), 500

@app.route('/api/users/assign-role', methods=['POST'])
def assign_role():
    data = request.get_json()
    email = data.get('email')
    role = data.get('role')
    
    if not email or not role:
        return jsonify({'error': 'Email and role are required'}), 400
    
    # Validate email format
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate role
    valid_roles = ['user', 'staff', 'admin']
    if role not in valid_roles:
        return jsonify({'error': f'Invalid role. Must be one of: {", ".join(valid_roles)}'}), 400
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email=? AND status='approved'", (email,))
            if not cursor.fetchone():
                return jsonify({'error': 'User not found or not approved'}), 404
            
            cursor.execute("UPDATE users SET role=? WHERE email=? AND status='approved'", (role, email))
            conn.commit()
        return jsonify({'message': f'Role {role} assigned to {email}'}), 200
    except Exception as e:
        print(f"Error assigning role: {e}")
        return jsonify({'error': 'Failed to assign role'}), 500

@app.route('/api/users/delete', methods=['POST'])
def delete_user():
    data = request.get_json()
    email = data.get('email')
    
    if not email:
        return jsonify({'error': 'Email is required'}), 400
    
    # Validate email format
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Prevent deleting admin account
    if email == 'kioskadmin@saintgits.org':
        return jsonify({'error': 'Cannot delete default admin account'}), 403
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check if user exists
            cursor.execute("SELECT id FROM users WHERE email=?", (email,))
            if not cursor.fetchone():
                return jsonify({'error': 'User not found'}), 404
            
            cursor.execute("DELETE FROM users WHERE email=?", (email,))
            conn.commit()
        return jsonify({'message': f'User {email} deleted'}), 200
    except Exception as e:
        print(f"Error deleting user: {e}")
        return jsonify({'error': 'Failed to delete user'}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, email, role, status FROM users")
            users = [{'name': name, 'email': email, 'role': role, 'status': status} 
                    for (name, email, role, status) in cursor.fetchall()]
        return jsonify(users), 200
    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({'error': 'Failed to fetch users'}), 500

# ---------------------- Menu APIs ---------------------- #
@app.route('/api/menu', methods=['GET'])
def get_menu():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM menu")
            menu = cursor.fetchall()
        
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
        ]), 200
    except Exception as e:
        print(f"Error fetching menu: {e}")
        return jsonify({'error': 'Failed to fetch menu'}), 500

@app.route('/api/menu', methods=['POST'])
def add_menu_item():
    name = request.form.get('name')
    price = request.form.get('price')
    category = request.form.get('category')
    stock = request.form.get('stock', 0)
    deliverable = request.form.get('deliverable', 0)
    image = request.files.get('image')

    # Validate required fields
    if not all([name, price, category, image]):
        return jsonify({'error': 'Missing required fields: name, price, category, image'}), 400

    # Validate price
    is_valid, result = validate_positive_number(price, "Price")
    if not is_valid:
        return jsonify({'error': result}), 400
    price = result

    # Validate stock
    is_valid, result = validate_non_negative_integer(stock, "Stock")
    if not is_valid:
        return jsonify({'error': result}), 400
    stock = result

    # Validate deliverable
    is_valid, result = validate_non_negative_integer(deliverable, "Deliverable")
    if not is_valid:
        return jsonify({'error': result}), 400
    deliverable = result

    # Validate image file
    is_valid, message = validate_file_upload(image)
    if not is_valid:
        return jsonify({'error': message}), 400

    try:
        filename = secure_filename(image.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image.save(filepath)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO menu (name, price, category, image, stock, deliverable) VALUES (?,?,?,?,?,?)",
                           (name, price, category, filename, stock, deliverable))
            conn.commit()
        return jsonify({'message': 'Menu item added successfully'}), 201
    except Exception as e:
        print(f"Error adding menu item: {e}")
        return jsonify({'error': 'Failed to add menu item'}), 500

@app.route('/api/menu/<int:item_id>', methods=['PUT'])
def update_or_toggle_menu_item(item_id):
    try:
        if request.content_type and request.content_type.startswith('multipart/form-data'):
            name = request.form.get('name')
            price = request.form.get('price')
            category = request.form.get('category')
            stock = request.form.get('stock')
            deliverable = request.form.get('deliverable')
            image = request.files.get('image')

            sets, vals = [], []
            if name: 
                sets.append("name=?")
                vals.append(name)
            
            if price:
                is_valid, result = validate_positive_number(price, "Price")
                if not is_valid:
                    return jsonify({'error': result}), 400
                sets.append("price=?")
                vals.append(result)
            
            if category: 
                sets.append("category=?")
                vals.append(category)
            
            if stock:
                is_valid, result = validate_non_negative_integer(stock, "Stock")
                if not is_valid:
                    return jsonify({'error': result}), 400
                sets.append("stock=?")
                vals.append(result)
            
            if deliverable is not None:
                is_valid, result = validate_non_negative_integer(deliverable, "Deliverable")
                if not is_valid:
                    return jsonify({'error': result}), 400
                sets.append("deliverable=?")
                vals.append(result)
            
            if image:
                is_valid, message = validate_file_upload(image)
                if not is_valid:
                    return jsonify({'error': message}), 400
                filename = secure_filename(image.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(filepath)
                sets.append("image=?")
                vals.append(filename)

            if not sets:
                return jsonify({'error': 'No fields to update'}), 400

            vals.append(item_id)
            with get_db_connection() as conn:
                cursor = conn.cursor()
                query = "UPDATE menu SET " + ", ".join(sets) + " WHERE id=?"
                cursor.execute(query, vals)
                conn.commit()
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
            if name is not None: 
                sets.append("name=?")
                vals.append(name)
            
            if price is not None:
                is_valid, result = validate_positive_number(price, "Price")
                if not is_valid:
                    return jsonify({'error': result}), 400
                sets.append("price=?")
                vals.append(result)
            
            if available is not None: 
                sets.append("available=?")
                vals.append(1 if bool(available) else 0)
            
            if category is not None: 
                sets.append("category=?")
                vals.append(category)
            
            if stock is not None:
                is_valid, result = validate_non_negative_integer(stock, "Stock")
                if not is_valid:
                    return jsonify({'error': result}), 400
                sets.append("stock=?")
                vals.append(result)
            
            if deliverable is not None:
                is_valid, result = validate_non_negative_integer(deliverable, "Deliverable")
                if not is_valid:
                    return jsonify({'error': result}), 400
                sets.append("deliverable=?")
                vals.append(result)

            if not sets:
                return jsonify({'error': 'No fields to update'}), 400

            vals.append(item_id)
            with get_db_connection() as conn:
                cursor = conn.cursor()
                query = "UPDATE menu SET " + ", ".join(sets) + " WHERE id=?"
                cursor.execute(query, vals)
                conn.commit()
            return jsonify({'message': 'Menu item updated'}), 200
        
        else:
            # Toggle availability
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT available FROM menu WHERE id=?", (item_id,))
                row = cursor.fetchone()
                if not row:
                    return jsonify({'error': 'Item not found'}), 404
                new_status = 0 if row[0] == 1 else 1
                cursor.execute("UPDATE menu SET available=? WHERE id=?", (new_status, item_id))
                conn.commit()
            return jsonify({'message': 'Availability toggled', 'available': bool(new_status)}), 200
    
    except Exception as e:
        return jsonify({'error': 'Failed to update menu item'}), 500

@app.route('/api/menu/<int:item_id>', methods=['DELETE'])
def delete_menu_item(item_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check if item exists
            cursor.execute("SELECT id FROM menu WHERE id=?", (item_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Menu item not found'}), 404
            
            cursor.execute("DELETE FROM menu WHERE id=?", (item_id,))
            conn.commit()
        return jsonify({'message': 'Menu item deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting menu item: {e}")
        return jsonify({'error': 'Failed to delete menu item'}), 500

# ---------------------- Orders APIs ---------------------- #
@app.route('/api/orders', methods=['GET'])
def get_orders():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, customer_name, customer_email, items, total_price, otp, status, created_at FROM orders ORDER BY id DESC")
            rows = cursor.fetchall()
            
            orders = []
            for r in rows:
                # Parse items safely using json.loads instead of eval
                try:
                    order_data = json.loads(r[3]) if isinstance(r[3], str) else r[3]
                except (json.JSONDecodeError, TypeError):
                    # If JSON parsing fails, try to handle old eval format
                    try:
                        order_data = eval(r[3]) if isinstance(r[3], str) else r[3]
                    except:
                        order_data = {"items": []}

                detailed_items = []
                for i in order_data.get("items", []):
                    try:
                        cur = conn.cursor()
                        cur.execute("SELECT name, price, category FROM menu WHERE id=?", (i["id"],))
                        m = cur.fetchone()
                        item_name = m[0] if m else f"ID:{i['id']}"
                        item_price = m[1] if m else 0
                        item_category = m[2] if m else "Other"
                    except Exception:
                        item_name = f"ID:{i['id']}"
                        item_price = 0
                        item_category = "Other"

                    detailed_items.append({
                        "id": i["id"],
                        "name": item_name,
                        "qty": i["qty"],
                        "price": item_price,
                        "category": item_category
                    })

                orders.append({
                    "id": r[0],
                    "customer_name": r[1],
                    "customer_email": r[2],
                    "items": detailed_items,
                    "total_price": r[4],
                    "otp": r[5],
                    "status": r[6],
                    "created_at": r[7]
                })
            
        return jsonify(orders), 200
    except Exception as e:
        print(f"Error fetching orders: {e}")
        return jsonify({'error': 'Failed to fetch orders'}), 500

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

    # Validate required fields
    is_valid, message = validate_required_fields(data, ['customer_name', 'customer_email', 'items', 'total_price'])
    if not is_valid:
        return jsonify({'error': message}), 400

    # Validate email
    if not validate_email(email):
        return jsonify({'error': 'Invalid email format'}), 400

    # Validate items
    if not isinstance(items, list) or len(items) == 0:
        return jsonify({'error': 'Items must be a non-empty list'}), 400

    # Validate total_price
    is_valid, result = validate_positive_number(total_price, "Total price")
    if not is_valid:
        return jsonify({'error': result}), 400
    total_price = result

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Check stock
            for item in items:
                if not isinstance(item, dict) or 'id' not in item or 'qty' not in item:
                    return jsonify({'error': 'Invalid item format'}), 400
                
                is_valid, qty = validate_positive_number(item['qty'], "Quantity")
                if not is_valid:
                    return jsonify({'error': f"Invalid quantity for item {item.get('id')}: {qty}"}), 400
                
                cursor.execute("SELECT stock FROM menu WHERE id=?", (item['id'],))
                row = cursor.fetchone()
                if not row or row[0] < item['qty']:
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
                (name, email, json.dumps(order_payload), total_price, otp, current_timestamp)
            )

            conn.commit()
        return jsonify({'message': 'Order created successfully', 'otp': otp, 'final_price': total_price}), 201
    except Exception as e:
        print(f"Error creating order: {e}")
        return jsonify({'error': 'Failed to create order'}), 500

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    data = request.get_json()
    status = data.get('status')
    
    if not status:
        return jsonify({'error': 'Status is required'}), 400
    
    # Validate status
    valid_statuses = ['Order Received', 'Preparing', 'Ready for Pickup', 'Completed', 'Cancelled']
    if status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check if order exists
            cursor.execute("SELECT id FROM orders WHERE id=?", (order_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'Order not found'}), 404
            
            cursor.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
            conn.commit()
        return jsonify({'message': 'Order status updated successfully'}), 200
    except Exception as e:
        print(f"Error updating order status: {e}")
        return jsonify({'error': 'Failed to update order status'}), 500

# ---------------------- Notification Endpoints ---------------------- #
@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    email = request.args.get('email', 'admin@saintgits.org')
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, title, message, type, priority, read, created_at 
                FROM notifications 
                WHERE recipient_email = ? 
                ORDER BY created_at DESC 
                LIMIT 50
            ''', (email,))
            notifications = cursor.fetchall()
        
        return jsonify([{
            'id': n[0],
            'title': n[1],
            'message': n[2],
            'type': n[3],
            'priority': n[4],
            'read': bool(n[5]),
            'created_at': n[6]
        } for n in notifications]), 200
    except Exception as e:
        print(f"Error getting notifications: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications', methods=['POST'])
def create_notification():
    data = request.get_json()
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notifications (recipient_email, title, message, type, priority)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data.get('recipient_email', 'admin@saintgits.org'),
                data.get('title'),
                data.get('message'),
                data.get('type'),
                data.get('priority', 'normal')
            ))
            conn.commit()
        return jsonify({'message': 'Notification created'}), 201
    except Exception as e:
        print(f"Error creating notification: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/<int:id>/read', methods=['PUT'])
def mark_notification_read(id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE notifications SET read = 1 WHERE id = ?', (id,))
            conn.commit()
        return jsonify({'message': 'Marked as read'}), 200
    except Exception as e:
        print(f"Error marking notification as read: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/notifications/mark-all-read', methods=['PUT'])
def mark_all_read():
    email = request.get_json().get('email', 'admin@saintgits.org')
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE notifications SET read = 1 WHERE recipient_email = ?', (email,))
            conn.commit()
        return jsonify({'message': 'All marked as read'}), 200
    except Exception as e:
        print(f"Error marking all as read: {e}")
        return jsonify({'error': str(e)}), 500

# ---------------------- Staff Statistics Endpoints ---------------------- #
@app.route('/api/staff/stats', methods=['GET'])
def get_staff_stats():
    """Get statistics for staff dashboard"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Total menu items
            cursor.execute("SELECT COUNT(*) FROM menu")
            total_items = cursor.fetchone()[0]
            
            # Total orders
            cursor.execute("SELECT COUNT(*) FROM orders")
            total_orders = cursor.fetchone()[0]
            
            # Pending orders
            cursor.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Order Received', 'Preparing')")
            pending_orders = cursor.fetchone()[0]
            
            # Total users
            cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'approved'")
            total_users = cursor.fetchone()[0]
            
            # Pending user requests
            cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'pending'")
            pending_users = cursor.fetchone()[0]
            
            # Today's revenue
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("SELECT COALESCE(SUM(total_price), 0) FROM orders WHERE DATE(created_at) = ?", (today,))
            today_revenue = cursor.fetchone()[0]
            
            return jsonify({
                'total_items': total_items,
                'total_orders': total_orders,
                'pending_orders': pending_orders,
                'total_users': total_users,
                'pending_users': pending_users,
                'today_revenue': today_revenue
            }), 200
    except Exception as e:
        print(f"Error fetching staff stats: {e}")
        return jsonify({'error': 'Failed to fetch statistics'}), 500

@app.route('/api/staff/users/pending', methods=['GET'])
def get_staff_pending_users():
    """Get pending user requests for staff"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, email, status FROM users WHERE status = 'pending' ORDER BY id DESC")
            users = cursor.fetchall()
        return jsonify([{
            'id': u[0],
            'name': u[1],
            'email': u[2],
            'status': u[3]
        } for u in users]), 200
    except Exception as e:
        print(f"Error fetching pending users: {e}")
        return jsonify({'error': 'Failed to fetch pending users'}), 500

@app.route('/api/staff/users/<int:user_id>/approve', methods=['PUT'])
def staff_approve_user(user_id):
    """Approve a user by staff"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'User not found'}), 404
            
            cursor.execute("UPDATE users SET status = 'approved', role = 'user' WHERE id = ?", (user_id,))
            conn.commit()
        return jsonify({'message': 'User approved successfully'}), 200
    except Exception as e:
        print(f"Error approving user: {e}")
        return jsonify({'error': 'Failed to approve user'}), 500

@app.route('/api/staff/users/<int:user_id>/reject', methods=['DELETE'])
def staff_reject_user(user_id):
    """Reject/delete a user by staff"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
            if not cursor.fetchone():
                return jsonify({'error': 'User not found'}), 404
            
            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
        return jsonify({'message': 'User rejected successfully'}), 200
    except Exception as e:
        print(f"Error rejecting user: {e}")
        return jsonify({'error': 'Failed to reject user'}), 500

@app.route('/api/staff/orders/recent', methods=['GET'])
def get_recent_orders():
    """Get recent orders for staff"""
    limit = request.args.get('limit', 20, type=int)
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, customer_name, customer_email, items, total_price, otp, status, created_at 
                FROM orders 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            
            orders = []
            for r in rows:
                try:
                    order_data = json.loads(r[3]) if isinstance(r[3], str) else r[3]
                except (json.JSONDecodeError, TypeError):
                    try:
                        order_data = eval(r[3]) if isinstance(r[3], str) else r[3]
                    except:
                        order_data = {"items": []}

                detailed_items = []
                for i in order_data.get("items", []):
                    try:
                        cur = conn.cursor()
                        cur.execute("SELECT name, price, category FROM menu WHERE id=?", (i["id"],))
                        m = cur.fetchone()
                        item_name = m[0] if m else f"ID:{i['id']}"
                        item_price = m[1] if m else 0
                        item_category = m[2] if m else "Other"
                    except Exception:
                        item_name = f"ID:{i['id']}"
                        item_price = 0
                        item_category = "Other"

                    detailed_items.append({
                        "id": i["id"],
                        "name": item_name,
                        "qty": i["qty"],
                        "price": item_price,
                        "category": item_category
                    })

                orders.append({
                    "id": r[0],
                    "customer_name": r[1],
                    "customer_email": r[2],
                    "items": detailed_items,
                    "total_price": r[4],
                    "otp": r[5],
                    "status": r[6],
                    "created_at": r[7],
                    "delivery_mode": order_data.get("delivery_mode", "pickup"),
                    "classroom": order_data.get("classroom", ""),
                    "department": order_data.get("department", ""),
                    "block": order_data.get("block", "")
                })
            
        return jsonify(orders), 200
    except Exception as e:
        print(f"Error fetching recent orders: {e}")
        return jsonify({'error': 'Failed to fetch recent orders'}), 500

# ---------------------- Activity Log Endpoints ---------------------- #
@app.route('/api/admin/log-activity', methods=['POST'])
def log_activity():
    data = request.get_json()
    admin_email = data.get('admin_email')
    action = data.get('action')
    details = data.get('details')
    ip_address = request.remote_addr
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO activity_log (admin_email, action, details, ip_address)
                VALUES (?, ?, ?, ?)
            ''', (admin_email, action, details, ip_address))
            conn.commit()
        return jsonify({'message': 'Activity logged'}), 201
    except Exception as e:
        print(f"Error logging activity: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/activity-log', methods=['GET'])
def get_activity_log():
    limit = request.args.get('limit', 100, type=int)
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT admin_email, action, details, ip_address, timestamp 
                FROM activity_log 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (limit,))
            logs = cursor.fetchall()
        
        return jsonify([{
            'admin': log[0],
            'action': log[1],
            'details': log[2],
            'ip_address': log[3],
            'timestamp': log[4]
        } for log in logs]), 200
    except Exception as e:
        print(f"Error getting activity log: {e}")
        return jsonify({'error': str(e)}), 500

# ---------------------- Run Server ---------------------- #
if __name__ == '__main__':
    app.run(debug=True)
