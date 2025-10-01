"""
API Documentation System
Features: Interactive API documentation, testing interface, code examples, authentication
"""

from flask import Flask, render_template_string, request, jsonify, Blueprint
import sqlite3
import json
import inspect
from datetime import datetime, timedelta
import os
from functools import wraps

try:
    from flask_restx import Api, Resource, fields, Namespace
    FLASK_RESTX_AVAILABLE = True
except ImportError:
    FLASK_RESTX_AVAILABLE = False
    print("Warning: flask-restx not available. API documentation will use basic Flask blueprint.")

class APIDocumentationManager:
    def __init__(self, app, db_path, api_title="College Kiosk API", api_version="2.0"):
        self.app = app
        self.db_path = db_path
        self.api_title = api_title
        self.api_version = api_version
        
        # Create API documentation blueprint
        self.doc_blueprint = Blueprint('api_docs', __name__, url_prefix='/docs')
        
        # Initialize Flask-RESTX
        self.api = Api(
            self.doc_blueprint,
            title=api_title,
            version=api_version,
            description="Comprehensive API documentation for College Kiosk Management System",
            doc='/swagger/',
            prefix='/api/v2'
        )
        
        # Register blueprint
        app.register_blueprint(self.doc_blueprint)
        
        # Initialize documentation tables
        self.init_documentation_tables()
        
        # Setup API namespaces
        self.setup_api_namespaces()
        
        # Generate documentation
        self.generate_api_documentation()
    
    def init_documentation_tables(self):
        """Initialize API documentation tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # API endpoints documentation
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_endpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_path TEXT NOT NULL,
                method TEXT NOT NULL,
                summary TEXT,
                description TEXT,
                parameters TEXT, -- JSON
                request_body TEXT, -- JSON schema
                responses TEXT, -- JSON responses
                examples TEXT, -- JSON examples
                tags TEXT, -- JSON array
                deprecated INTEGER DEFAULT 0,
                version TEXT DEFAULT '2.0',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # API usage statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint_path TEXT NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER,
                response_time REAL,
                user_agent TEXT,
                ip_address TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # API keys for documentation testing
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_test_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_name TEXT NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                description TEXT,
                permissions TEXT, -- JSON array
                expires_at TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_api_namespaces(self):
        """Setup API namespaces for documentation"""
        
        # Authentication namespace
        auth_ns = self.api.namespace('auth', description='Authentication operations')
        
        # User management namespace
        users_ns = self.api.namespace('users', description='User management operations')
        
        # Menu management namespace
        menu_ns = self.api.namespace('menu', description='Menu management operations')
        
        # Order management namespace  
        orders_ns = self.api.namespace('orders', description='Order management operations')
        
        # Inventory namespace
        inventory_ns = self.api.namespace('inventory', description='Inventory management operations')
        
        # Analytics namespace
        analytics_ns = self.api.namespace('analytics', description='Analytics and reporting operations')
        
        # Real-time namespace
        realtime_ns = self.api.namespace('realtime', description='Real-time features and WebSocket operations')
        
        # Admin namespace
        admin_ns = self.api.namespace('admin', description='Administrative operations')
        
        # Store namespaces
        self.namespaces = {
            'auth': auth_ns,
            'users': users_ns,
            'menu': menu_ns,
            'orders': orders_ns,
            'inventory': inventory_ns,
            'analytics': analytics_ns,
            'realtime': realtime_ns,
            'admin': admin_ns
        }
        
        # Setup models for each namespace
        self.setup_api_models()
        
        # Setup endpoints for each namespace
        self.setup_api_endpoints()
    
    def setup_api_models(self):
        """Setup API models for documentation"""
        
        # Authentication models
        auth_ns = self.namespaces['auth']
        
        self.login_model = auth_ns.model('Login', {
            'email': fields.String(required=True, description='User email'),
            'password': fields.String(required=True, description='User password'),
            'device_info': fields.Raw(description='Device information for mobile apps')
        })
        
        self.token_response = auth_ns.model('TokenResponse', {
            'access_token': fields.String(description='JWT access token'),
            'refresh_token': fields.String(description='JWT refresh token'),
            'expires_in': fields.Integer(description='Token expiration time in seconds'),
            'user': fields.Raw(description='User information')
        })
        
        # User models
        users_ns = self.namespaces['users']
        
        self.user_model = users_ns.model('User', {
            'id': fields.Integer(description='User ID'),
            'username': fields.String(required=True, description='Username'),
            'email': fields.String(required=True, description='Email address'),
            'full_name': fields.String(description='Full name'),
            'phone': fields.String(description='Phone number'),
            'role': fields.String(description='User role', enum=['customer', 'staff', 'admin']),
            'is_active': fields.Boolean(description='Account status'),
            'created_at': fields.DateTime(description='Account creation date')
        })
        
        # Menu models
        menu_ns = self.namespaces['menu']
        
        self.menu_item_model = menu_ns.model('MenuItem', {
            'id': fields.Integer(description='Menu item ID'),
            'name': fields.String(required=True, description='Item name'),
            'description': fields.String(description='Item description'),
            'price': fields.Float(required=True, description='Item price'),
            'category': fields.String(description='Item category'),
            'image_url': fields.String(description='Item image URL'),
            'is_available': fields.Boolean(description='Availability status'),
            'ingredients': fields.List(fields.String, description='List of ingredients'),
            'nutrition_info': fields.Raw(description='Nutritional information'),
            'allergens': fields.List(fields.String, description='Allergen information')
        })
        
        # Order models
        orders_ns = self.namespaces['orders']
        
        self.order_item_model = orders_ns.model('OrderItem', {
            'menu_item_id': fields.Integer(required=True, description='Menu item ID'),
            'quantity': fields.Integer(required=True, description='Quantity ordered'),
            'special_instructions': fields.String(description='Special instructions'),
            'price': fields.Float(description='Item price at time of order')
        })
        
        self.order_model = orders_ns.model('Order', {
            'id': fields.Integer(description='Order ID'),
            'customer_name': fields.String(description='Customer name'),
            'customer_email': fields.String(description='Customer email'),
            'items': fields.List(fields.Nested(self.order_item_model), description='Order items'),
            'total_price': fields.Float(description='Total order amount'),
            'status': fields.String(description='Order status', enum=['Pending', 'Confirmed', 'Preparing', 'Ready', 'Completed', 'Cancelled']),
            'payment_method': fields.String(description='Payment method'),
            'delivery_type': fields.String(description='Delivery type', enum=['pickup', 'delivery']),
            'created_at': fields.DateTime(description='Order creation time'),
            'estimated_completion': fields.DateTime(description='Estimated completion time')
        })
        
        # Analytics models
        analytics_ns = self.namespaces['analytics']
        
        self.analytics_report_model = analytics_ns.model('AnalyticsReport', {
            'report_type': fields.String(description='Type of report'),
            'date_range': fields.Raw(description='Date range for the report'),
            'data': fields.Raw(description='Report data'),
            'generated_at': fields.DateTime(description='Report generation time'),
            'total_records': fields.Integer(description='Total records in report')
        })
        
        # Error models (shared across namespaces)
        self.error_model = self.api.model('Error', {
            'error': fields.String(description='Error message'),
            'code': fields.Integer(description='Error code'),
            'details': fields.Raw(description='Additional error details')
        })
    
    def setup_api_endpoints(self):
        """Setup documented API endpoints"""
        
        # Authentication endpoints
        auth_ns = self.namespaces['auth']
        
        @auth_ns.route('/login')
        class LoginResource(Resource):
            @auth_ns.expect(self.login_model)
            @auth_ns.marshal_with(self.token_response, code=200)
            @auth_ns.response(401, 'Invalid credentials', self.error_model)
            def post(self):
                """Authenticate user and return access token"""
                return {'message': 'Login endpoint - implementation in main app.py'}
        
        @auth_ns.route('/refresh')
        class RefreshResource(Resource):
            @auth_ns.header('Authorization', 'Bearer token', required=True)
            @auth_ns.marshal_with(self.token_response, code=200)
            @auth_ns.response(401, 'Invalid token', self.error_model)
            def post(self):
                """Refresh access token"""
                return {'message': 'Token refresh endpoint'}
        
        @auth_ns.route('/logout')
        class LogoutResource(Resource):
            @auth_ns.header('Authorization', 'Bearer token', required=True)
            @auth_ns.response(200, 'Successfully logged out')
            def post(self):
                """Logout user and invalidate token"""
                return {'message': 'Logout successful'}
        
        # User management endpoints
        users_ns = self.namespaces['users']
        
        @users_ns.route('/')
        class UsersResource(Resource):
            @users_ns.marshal_list_with(self.user_model)
            @users_ns.param('page', 'Page number', type=int, default=1)
            @users_ns.param('limit', 'Items per page', type=int, default=20)
            @users_ns.param('role', 'Filter by role', type=str)
            def get(self):
                """Get list of users"""
                return {'message': 'Users list endpoint'}
            
            @users_ns.expect(self.user_model)
            @users_ns.marshal_with(self.user_model, code=201)
            @users_ns.response(400, 'Validation error', self.error_model)
            def post(self):
                """Create new user"""
                return {'message': 'User creation endpoint'}
        
        @users_ns.route('/<int:user_id>')
        class UserResource(Resource):
            @users_ns.marshal_with(self.user_model)
            @users_ns.response(404, 'User not found', self.error_model)
            def get(self, user_id):
                """Get user by ID"""
                return {'message': f'Get user {user_id}'}
            
            @users_ns.expect(self.user_model)
            @users_ns.marshal_with(self.user_model)
            def put(self, user_id):
                """Update user"""
                return {'message': f'Update user {user_id}'}
            
            @users_ns.response(204, 'User deleted')
            @users_ns.response(404, 'User not found', self.error_model)
            def delete(self, user_id):
                """Delete user"""
                return {'message': f'Delete user {user_id}'}
        
        # Menu endpoints
        menu_ns = self.namespaces['menu']
        
        @menu_ns.route('/')
        class MenuResource(Resource):
            @menu_ns.marshal_list_with(self.menu_item_model)
            @menu_ns.param('category', 'Filter by category', type=str)
            @menu_ns.param('available_only', 'Show only available items', type=bool, default=True)
            def get(self):
                """Get menu items"""
                return {'message': 'Menu items endpoint'}
            
            @menu_ns.expect(self.menu_item_model)
            @menu_ns.marshal_with(self.menu_item_model, code=201)
            def post(self):
                """Create new menu item"""
                return {'message': 'Menu item creation endpoint'}
        
        @menu_ns.route('/<int:item_id>')
        class MenuItemResource(Resource):
            @menu_ns.marshal_with(self.menu_item_model)
            @menu_ns.response(404, 'Menu item not found', self.error_model)
            def get(self, item_id):
                """Get menu item by ID"""
                return {'message': f'Get menu item {item_id}'}
            
            @menu_ns.expect(self.menu_item_model)
            @menu_ns.marshal_with(self.menu_item_model)
            def put(self, item_id):
                """Update menu item"""
                return {'message': f'Update menu item {item_id}'}
            
            @menu_ns.response(204, 'Menu item deleted')
            def delete(self, item_id):
                """Delete menu item"""
                return {'message': f'Delete menu item {item_id}'}
        
        # Order endpoints
        orders_ns = self.namespaces['orders']
        
        @orders_ns.route('/')
        class OrdersResource(Resource):
            @orders_ns.marshal_list_with(self.order_model)
            @orders_ns.param('status', 'Filter by status', type=str)
            @orders_ns.param('customer_email', 'Filter by customer email', type=str)
            @orders_ns.param('date_from', 'Filter from date (YYYY-MM-DD)', type=str)
            @orders_ns.param('date_to', 'Filter to date (YYYY-MM-DD)', type=str)
            def get(self):
                """Get orders"""
                return {'message': 'Orders endpoint'}
            
            @orders_ns.expect(self.order_model)
            @orders_ns.marshal_with(self.order_model, code=201)
            def post(self):
                """Create new order"""
                return {'message': 'Order creation endpoint'}
        
        @orders_ns.route('/<int:order_id>')
        class OrderResource(Resource):
            @orders_ns.marshal_with(self.order_model)
            @orders_ns.response(404, 'Order not found', self.error_model)
            def get(self, order_id):
                """Get order by ID"""
                return {'message': f'Get order {order_id}'}
            
            @orders_ns.param('status', 'New order status', required=True)
            @orders_ns.marshal_with(self.order_model)
            def patch(self, order_id):
                """Update order status"""
                return {'message': f'Update order {order_id} status'}
        
        # Analytics endpoints
        analytics_ns = self.namespaces['analytics']
        
        @analytics_ns.route('/sales')
        class SalesAnalyticsResource(Resource):
            @analytics_ns.marshal_with(self.analytics_report_model)
            @analytics_ns.param('period', 'Time period', enum=['day', 'week', 'month', 'year'], default='day')
            @analytics_ns.param('date_from', 'Start date (YYYY-MM-DD)', type=str)
            @analytics_ns.param('date_to', 'End date (YYYY-MM-DD)', type=str)
            def get(self):
                """Get sales analytics"""
                return {'message': 'Sales analytics endpoint'}
        
        @analytics_ns.route('/customers')
        class CustomerAnalyticsResource(Resource):
            @analytics_ns.marshal_with(self.analytics_report_model)
            def get(self):
                """Get customer analytics"""
                return {'message': 'Customer analytics endpoint'}
        
        @analytics_ns.route('/menu')
        class MenuAnalyticsResource(Resource):
            @analytics_ns.marshal_with(self.analytics_report_model)
            def get(self):
                """Get menu item analytics"""
                return {'message': 'Menu analytics endpoint'}
    
    def generate_api_documentation(self):
        """Generate comprehensive API documentation"""
        
        # Create custom documentation page
        @self.doc_blueprint.route('/')
        def api_documentation():
            """Main API documentation page"""
            return render_template_string(self.get_documentation_template())
        
        @self.doc_blueprint.route('/postman')
        def postman_collection():
            """Generate Postman collection"""
            collection = self.generate_postman_collection()
            return jsonify(collection)
        
        @self.doc_blueprint.route('/openapi.json')
        def openapi_spec():
            """OpenAPI specification"""
            return jsonify(self.api.__schema__)
        
        @self.doc_blueprint.route('/test-key')
        def get_test_key():
            """Get API test key for documentation"""
            test_key = self.generate_test_api_key()
            return jsonify({'api_key': test_key, 'expires_in': 3600})
    
    def get_documentation_template(self):
        """Get HTML template for documentation"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ api_title }} - API Documentation</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.5/swagger-ui-bundle.css" rel="stylesheet">
    <style>
        body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
        .header { background: #FF5722; color: white; padding: 20px; margin: -20px -20px 20px -20px; }
        .header h1 { margin: 0; }
        .nav { margin: 20px 0; }
        .nav a { margin-right: 20px; color: #FF5722; text-decoration: none; font-weight: bold; }
        .nav a:hover { text-decoration: underline; }
        .section { margin: 30px 0; }
        .code-block { background: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .endpoint { background: #fff; border: 1px solid #ddd; border-radius: 5px; margin: 10px 0; padding: 15px; }
        .method { display: inline-block; padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; margin-right: 10px; }
        .method.get { background: #4CAF50; }
        .method.post { background: #FF9800; }
        .method.put { background: #2196F3; }
        .method.delete { background: #f44336; }
        .method.patch { background: #9C27B0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>College Kiosk API Documentation</h1>
        <p>Version 2.0 - Enterprise Food Service Management System</p>
    </div>
    
    <div class="nav">
        <a href="#overview">Overview</a>
        <a href="#authentication">Authentication</a>
        <a href="#endpoints">Endpoints</a>
        <a href="#examples">Examples</a>
        <a href="#testing">Testing</a>
        <a href="/docs/swagger/">Interactive API Explorer</a>
        <a href="/docs/postman">Postman Collection</a>
    </div>
    
    <div id="overview" class="section">
        <h2>API Overview</h2>
        <p>The College Kiosk API provides comprehensive access to all food service management features including:</p>
        <ul>
            <li><strong>Authentication:</strong> JWT-based authentication with refresh tokens</li>
            <li><strong>User Management:</strong> Create, read, update, and delete users</li>
            <li><strong>Menu Management:</strong> Manage menu items, categories, and availability</li>
            <li><strong>Order Processing:</strong> Complete order lifecycle management</li>
            <li><strong>Inventory Management:</strong> Track stock levels, suppliers, and purchases</li>
            <li><strong>Analytics:</strong> Comprehensive reporting and business intelligence</li>
            <li><strong>Real-time Features:</strong> WebSocket-based live updates</li>
            <li><strong>Administrative Tools:</strong> Role-based access control and system management</li>
        </ul>
        
        <h3>Base URL</h3>
        <div class="code-block">https://your-domain.com/api/v2</div>
        
        <h3>Response Format</h3>
        <p>All API responses use JSON format with consistent structure:</p>
        <div class="code-block">
{
    "data": {}, // Response data
    "message": "Success message",
    "timestamp": "2025-10-01T12:00:00Z",
    "request_id": "unique-request-id"
}
        </div>
    </div>
    
    <div id="authentication" class="section">
        <h2>Authentication</h2>
        <p>The API uses JWT (JSON Web Token) authentication. Include the token in the Authorization header:</p>
        <div class="code-block">Authorization: Bearer YOUR_ACCESS_TOKEN</div>
        
        <h3>Getting an Access Token</h3>
        <p>Send a POST request to <code>/api/v2/auth/login</code> with your credentials:</p>
        <div class="code-block">
POST /api/v2/auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "your_password"
}
        </div>
        
        <h3>Token Refresh</h3>
        <p>Access tokens expire after 24 hours. Use the refresh token to get a new access token:</p>
        <div class="code-block">
POST /api/v2/auth/refresh
Authorization: Bearer YOUR_REFRESH_TOKEN
        </div>
    </div>
    
    <div id="endpoints" class="section">
        <h2>API Endpoints</h2>
        
        <h3>Authentication Endpoints</h3>
        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v2/auth/login</strong>
            <p>Authenticate user and return access token</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v2/auth/refresh</strong>
            <p>Refresh access token using refresh token</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v2/auth/logout</strong>
            <p>Logout user and invalidate tokens</p>
        </div>
        
        <h3>User Management</h3>
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v2/users/</strong>
            <p>Get list of users with pagination and filtering</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v2/users/</strong>
            <p>Create new user account</p>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v2/users/{user_id}</strong>
            <p>Get specific user details</p>
        </div>
        
        <div class="endpoint">
            <span class="method put">PUT</span>
            <strong>/api/v2/users/{user_id}</strong>
            <p>Update user information</p>
        </div>
        
        <h3>Menu Management</h3>
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v2/menu/</strong>
            <p>Get menu items with category filtering</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v2/menu/</strong>
            <p>Create new menu item</p>
        </div>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v2/menu/{item_id}</strong>
            <p>Get specific menu item details</p>
        </div>
        
        <h3>Order Management</h3>
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/v2/orders/</strong>
            <p>Get orders with status and date filtering</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/v2/orders/</strong>
            <p>Create new order</p>
        </div>
        
        <div class="endpoint">
            <span class="method patch">PATCH</span>
            <strong>/api/v2/orders/{order_id}</strong>
            <p>Update order status</p>
        </div>
    </div>
    
    <div id="examples" class="section">
        <h2>Code Examples</h2>
        
        <h3>JavaScript (Fetch API)</h3>
        <div class="code-block">
// Login
const response = await fetch('/api/v2/auth/login', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'password123'
    })
});

const data = await response.json();
const accessToken = data.access_token;

// Make authenticated request
const ordersResponse = await fetch('/api/v2/orders/', {
    headers: {
        'Authorization': `Bearer ${accessToken}`
    }
});

const orders = await ordersResponse.json();
        </div>
        
        <h3>Python (requests)</h3>
        <div class="code-block">
import requests

# Login
login_response = requests.post('/api/v2/auth/login', json={
    'email': 'user@example.com',
    'password': 'password123'
})

access_token = login_response.json()['access_token']

# Make authenticated request
headers = {'Authorization': f'Bearer {access_token}'}
orders_response = requests.get('/api/v2/orders/', headers=headers)
orders = orders_response.json()
        </div>
        
        <h3>cURL</h3>
        <div class="code-block">
# Login
curl -X POST /api/v2/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"email":"user@example.com","password":"password123"}'

# Make authenticated request  
curl -X GET /api/v2/orders/ \\
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
        </div>
    </div>
    
    <div id="testing" class="section">
        <h2>API Testing</h2>
        <p>Test the API using these tools:</p>
        <ul>
            <li><strong><a href="/docs/swagger/">Interactive API Explorer</a></strong> - Test endpoints directly in your browser</li>
            <li><strong><a href="/docs/postman">Postman Collection</a></strong> - Import into Postman for comprehensive testing</li>
            <li><strong>Test API Key:</strong> <button onclick="getTestKey()">Generate Test Key</button> <span id="test-key"></span></li>
        </ul>
        
        <h3>Rate Limiting</h3>
        <p>API requests are rate limited to prevent abuse:</p>
        <ul>
            <li>Authenticated users: 1000 requests/hour</li>
            <li>Anonymous users: 100 requests/hour</li>
            <li>Admin users: 5000 requests/hour</li>
        </ul>
        
        <h3>Error Codes</h3>
        <table border="1" style="width: 100%; border-collapse: collapse;">
            <tr style="background: #f5f5f5;">
                <th style="padding: 10px;">Code</th>
                <th style="padding: 10px;">Description</th>
                <th style="padding: 10px;">Common Causes</th>
            </tr>
            <tr>
                <td style="padding: 10px;">400</td>
                <td style="padding: 10px;">Bad Request</td>
                <td style="padding: 10px;">Invalid request parameters or body</td>
            </tr>
            <tr>
                <td style="padding: 10px;">401</td>
                <td style="padding: 10px;">Unauthorized</td>
                <td style="padding: 10px;">Missing or invalid authentication token</td>
            </tr>
            <tr>
                <td style="padding: 10px;">403</td>
                <td style="padding: 10px;">Forbidden</td>
                <td style="padding: 10px;">Insufficient permissions for the requested resource</td>
            </tr>
            <tr>
                <td style="padding: 10px;">404</td>
                <td style="padding: 10px;">Not Found</td>
                <td style="padding: 10px;">Resource does not exist</td>
            </tr>
            <tr>
                <td style="padding: 10px;">429</td>
                <td style="padding: 10px;">Too Many Requests</td>
                <td style="padding: 10px;">Rate limit exceeded</td>
            </tr>
            <tr>
                <td style="padding: 10px;">500</td>
                <td style="padding: 10px;">Internal Server Error</td>
                <td style="padding: 10px;">Server-side error</td>
            </tr>
        </table>
    </div>
    
    <script>
    async function getTestKey() {
        try {
            const response = await fetch('/docs/test-key');
            const data = await response.json();
            document.getElementById('test-key').textContent = data.api_key;
        } catch (error) {
            document.getElementById('test-key').textContent = 'Error generating test key';
        }
    }
    </script>
</body>
</html>
        '''
    
    def generate_postman_collection(self):
        """Generate Postman collection for API testing"""
        collection = {
            "info": {
                "name": f"{self.api_title} API Collection",
                "description": "Complete API collection for College Kiosk Management System",
                "version": self.api_version,
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{access_token}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": "{{base_url}}/api/v2",
                    "type": "string"
                },
                {
                    "key": "access_token",
                    "value": "",
                    "type": "string"
                }
            ],
            "item": [
                {
                    "name": "Authentication",
                    "item": [
                        {
                            "name": "Login",
                            "request": {
                                "method": "POST",
                                "header": [
                                    {
                                        "key": "Content-Type",
                                        "value": "application/json"
                                    }
                                ],
                                "body": {
                                    "mode": "raw",
                                    "raw": json.dumps({
                                        "email": "admin@collegekiosk.com",
                                        "password": "admin123"
                                    }, indent=2)
                                },
                                "url": {
                                    "raw": "{{base_url}}/auth/login",
                                    "host": ["{{base_url}}"],
                                    "path": ["auth", "login"]
                                }
                            },
                            "event": [
                                {
                                    "listen": "test",
                                    "script": {
                                        "exec": [
                                            "if (pm.response.status === 'OK') {",
                                            "    const response = pm.response.json();",
                                            "    pm.collectionVariables.set('access_token', response.access_token);",
                                            "}"
                                        ]
                                    }
                                }
                            ]
                        },
                        {
                            "name": "Refresh Token",
                            "request": {
                                "method": "POST",
                                "header": [],
                                "url": {
                                    "raw": "{{base_url}}/auth/refresh",
                                    "host": ["{{base_url}}"],
                                    "path": ["auth", "refresh"]
                                }
                            }
                        }
                    ]
                },
                {
                    "name": "Users",
                    "item": [
                        {
                            "name": "Get Users",
                            "request": {
                                "method": "GET",
                                "header": [],
                                "url": {
                                    "raw": "{{base_url}}/users/?page=1&limit=20",
                                    "host": ["{{base_url}}"],
                                    "path": ["users"],
                                    "query": [
                                        {"key": "page", "value": "1"},
                                        {"key": "limit", "value": "20"}
                                    ]
                                }
                            }
                        },
                        {
                            "name": "Create User",
                            "request": {
                                "method": "POST",
                                "header": [
                                    {
                                        "key": "Content-Type",
                                        "value": "application/json"
                                    }
                                ],
                                "body": {
                                    "mode": "raw",
                                    "raw": json.dumps({
                                        "username": "newuser",
                                        "email": "newuser@example.com",
                                        "password": "password123",
                                        "full_name": "New User",
                                        "role": "customer"
                                    }, indent=2)
                                },
                                "url": {
                                    "raw": "{{base_url}}/users/",
                                    "host": ["{{base_url}}"],
                                    "path": ["users"]
                                }
                            }
                        }
                    ]
                },
                {
                    "name": "Menu",
                    "item": [
                        {
                            "name": "Get Menu",
                            "request": {
                                "method": "GET",
                                "header": [],
                                "url": {
                                    "raw": "{{base_url}}/menu/?available_only=true",
                                    "host": ["{{base_url}}"],
                                    "path": ["menu"],
                                    "query": [
                                        {"key": "available_only", "value": "true"}
                                    ]
                                }
                            }
                        },
                        {
                            "name": "Create Menu Item",
                            "request": {
                                "method": "POST",
                                "header": [
                                    {
                                        "key": "Content-Type",
                                        "value": "application/json"
                                    }
                                ],
                                "body": {
                                    "mode": "raw",
                                    "raw": json.dumps({
                                        "name": "New Menu Item",
                                        "description": "Delicious new item",
                                        "price": 199.99,
                                        "category": "main_course",
                                        "is_available": True
                                    }, indent=2)
                                },
                                "url": {
                                    "raw": "{{base_url}}/menu/",
                                    "host": ["{{base_url}}"],
                                    "path": ["menu"]
                                }
                            }
                        }
                    ]
                },
                {
                    "name": "Orders",
                    "item": [
                        {
                            "name": "Get Orders",
                            "request": {
                                "method": "GET",
                                "header": [],
                                "url": {
                                    "raw": "{{base_url}}/orders/?status=Pending",
                                    "host": ["{{base_url}}"],
                                    "path": ["orders"],
                                    "query": [
                                        {"key": "status", "value": "Pending"}
                                    ]
                                }
                            }
                        },
                        {
                            "name": "Create Order",
                            "request": {
                                "method": "POST",
                                "header": [
                                    {
                                        "key": "Content-Type",
                                        "value": "application/json"
                                    }
                                ],
                                "body": {
                                    "mode": "raw",
                                    "raw": json.dumps({
                                        "customer_name": "John Doe",
                                        "customer_email": "john@example.com",
                                        "items": [
                                            {
                                                "menu_item_id": 1,
                                                "quantity": 2,
                                                "special_instructions": "Extra spicy"
                                            }
                                        ],
                                        "payment_method": "card",
                                        "delivery_type": "pickup"
                                    }, indent=2)
                                },
                                "url": {
                                    "raw": "{{base_url}}/orders/",
                                    "host": ["{{base_url}}"],
                                    "path": ["orders"]
                                }
                            }
                        }
                    ]
                }
            ]
        }
        
        return collection
    
    def generate_test_api_key(self):
        """Generate temporary API key for testing"""
        import secrets
        test_key = f"test_{secrets.token_urlsafe(32)}"
        
        # Store in database with 1 hour expiration
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
        
        cursor.execute('''
            INSERT INTO api_test_keys (key_name, api_key, description, expires_at)
            VALUES (?, ?, ?, ?)
        ''', ("Documentation Test", test_key, "Generated for API documentation testing", expires_at))
        
        conn.commit()
        conn.close()
        
        return test_key
    
    def document_endpoint(self, path, method, summary, description=None, 
                         parameters=None, request_body=None, responses=None, 
                         examples=None, tags=None):
        """Document an API endpoint"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO api_endpoints 
            (endpoint_path, method, summary, description, parameters, 
             request_body, responses, examples, tags, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            path, method.upper(), summary, description,
            json.dumps(parameters) if parameters else None,
            json.dumps(request_body) if request_body else None,
            json.dumps(responses) if responses else None,
            json.dumps(examples) if examples else None,
            json.dumps(tags) if tags else None,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def log_api_usage(self, endpoint_path, method, status_code, response_time, 
                     user_agent=None, ip_address=None):
        """Log API usage for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO api_usage_stats 
            (endpoint_path, method, status_code, response_time, user_agent, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (endpoint_path, method, status_code, response_time, user_agent, ip_address))
        
        conn.commit()
        conn.close()
    
    def get_api_usage_stats(self, days=7):
        """Get API usage statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Most used endpoints
        cursor.execute('''
            SELECT endpoint_path, method, COUNT(*) as usage_count,
                   AVG(response_time) as avg_response_time
            FROM api_usage_stats
            WHERE timestamp > ?
            GROUP BY endpoint_path, method
            ORDER BY usage_count DESC
            LIMIT 20
        ''', (start_date,))
        
        top_endpoints = cursor.fetchall()
        
        # Status code distribution
        cursor.execute('''
            SELECT status_code, COUNT(*) as count
            FROM api_usage_stats
            WHERE timestamp > ?
            GROUP BY status_code
            ORDER BY count DESC
        ''', (start_date,))
        
        status_distribution = cursor.fetchall()
        
        # Daily usage
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as requests
            FROM api_usage_stats
            WHERE timestamp > ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (start_date,))
        
        daily_usage = cursor.fetchall()
        
        conn.close()
        
        return {
            'period_days': days,
            'top_endpoints': [
                {
                    'endpoint': ep[0],
                    'method': ep[1],
                    'usage_count': ep[2],
                    'avg_response_time': round(ep[3], 2) if ep[3] else 0
                }
                for ep in top_endpoints
            ],
            'status_distribution': [
                {'status_code': status[0], 'count': status[1]}
                for status in status_distribution
            ],
            'daily_usage': [
                {'date': day[0], 'requests': day[1]}
                for day in daily_usage
            ]
        }