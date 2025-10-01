"""
Advanced UI/UX Enhancement System
Features: Modern responsive design, dark/light themes, PWA, accessibility, animations
"""

import json
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template_string, request, jsonify, send_from_directory
import sqlite3

class UIUXManager:
    def __init__(self, app, db_path):
        self.app = app
        self.db_path = db_path
        
        # Create UI/UX blueprint
        self.uiux_blueprint = Blueprint('uiux', __name__, url_prefix='/uiux')
        app.register_blueprint(self.uiux_blueprint)
        
        # Initialize UI/UX tables
        self.init_uiux_tables()
        
        # Setup routes
        self.setup_routes()
        
        # Generate UI components
        self.generate_ui_components()
    
    def init_uiux_tables(self):
        """Initialize UI/UX enhancement tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # User preferences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                theme TEXT DEFAULT 'light',
                language TEXT DEFAULT 'en',
                accessibility_mode INTEGER DEFAULT 0,
                font_size TEXT DEFAULT 'medium',
                high_contrast INTEGER DEFAULT 0,
                motion_reduced INTEGER DEFAULT 0,
                notifications_enabled INTEGER DEFAULT 1,
                layout_preference TEXT DEFAULT 'default',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # UI analytics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ui_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                page_path TEXT,
                component_name TEXT,
                action TEXT,
                session_id TEXT,
                device_type TEXT,
                browser_info TEXT,
                screen_resolution TEXT,
                interaction_time REAL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # UI feedback
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ui_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                component_name TEXT,
                feedback_type TEXT,
                rating INTEGER,
                comment TEXT,
                screenshot_path TEXT,
                user_agent TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_routes(self):
        """Setup UI/UX routes"""
        
        @self.uiux_blueprint.route('/themes')
        def get_themes():
            """Get available themes"""
            return jsonify({
                'themes': [
                    {
                        'id': 'light',
                        'name': 'Light Theme',
                        'description': 'Clean and bright interface',
                        'primary_color': '#FF5722',
                        'secondary_color': '#2196F3',
                        'background_color': '#FFFFFF',
                        'text_color': '#333333'
                    },
                    {
                        'id': 'dark',
                        'name': 'Dark Theme',
                        'description': 'Easy on the eyes for low-light environments',
                        'primary_color': '#FF7043',
                        'secondary_color': '#42A5F5',
                        'background_color': '#121212',
                        'text_color': '#FFFFFF'
                    },
                    {
                        'id': 'blue',
                        'name': 'Blue Theme',
                        'description': 'Professional blue color scheme',
                        'primary_color': '#1976D2',
                        'secondary_color': '#FFC107',
                        'background_color': '#FAFAFA',
                        'text_color': '#212121'
                    },
                    {
                        'id': 'high_contrast',
                        'name': 'High Contrast',
                        'description': 'Maximum contrast for accessibility',
                        'primary_color': '#000000',
                        'secondary_color': '#FFFF00',
                        'background_color': '#FFFFFF',
                        'text_color': '#000000'
                    }
                ]
            })
        
        @self.uiux_blueprint.route('/preferences/<int:user_id>')
        def get_user_preferences(user_id):
            """Get user UI preferences"""
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM user_preferences WHERE user_id = ?
            ''', (user_id,))
            
            preferences = cursor.fetchone()
            conn.close()
            
            if preferences:
                return jsonify({
                    'theme': preferences[2],
                    'language': preferences[3],
                    'accessibility_mode': bool(preferences[4]),
                    'font_size': preferences[5],
                    'high_contrast': bool(preferences[6]),
                    'motion_reduced': bool(preferences[7]),
                    'notifications_enabled': bool(preferences[8]),
                    'layout_preference': preferences[9]
                })
            else:
                # Return default preferences
                return jsonify({
                    'theme': 'light',
                    'language': 'en',
                    'accessibility_mode': False,
                    'font_size': 'medium',
                    'high_contrast': False,
                    'motion_reduced': False,
                    'notifications_enabled': True,
                    'layout_preference': 'default'
                })
        
        @self.uiux_blueprint.route('/preferences/<int:user_id>', methods=['POST'])
        def update_user_preferences(user_id):
            """Update user UI preferences"""
            data = request.json
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences 
                (user_id, theme, language, accessibility_mode, font_size, 
                 high_contrast, motion_reduced, notifications_enabled, 
                 layout_preference, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                data.get('theme', 'light'),
                data.get('language', 'en'),
                1 if data.get('accessibility_mode', False) else 0,
                data.get('font_size', 'medium'),
                1 if data.get('high_contrast', False) else 0,
                1 if data.get('motion_reduced', False) else 0,
                1 if data.get('notifications_enabled', True) else 0,
                data.get('layout_preference', 'default'),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Preferences updated successfully'})
        
        @self.uiux_blueprint.route('/feedback', methods=['POST'])
        def submit_feedback():
            """Submit UI/UX feedback"""
            data = request.json
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO ui_feedback 
                (user_id, component_name, feedback_type, rating, comment, user_agent)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                data.get('user_id'),
                data.get('component_name'),
                data.get('feedback_type'),
                data.get('rating'),
                data.get('comment'),
                request.headers.get('User-Agent')
            ))
            
            conn.commit()
            conn.close()
            
            return jsonify({'message': 'Feedback submitted successfully'})
        
        @self.uiux_blueprint.route('/components')
        def get_ui_components():
            """Get UI component library"""
            return jsonify({
                'components': [
                    {
                        'name': 'Button',
                        'variants': ['primary', 'secondary', 'outline', 'ghost'],
                        'sizes': ['small', 'medium', 'large'],
                        'states': ['default', 'hover', 'active', 'disabled', 'loading']
                    },
                    {
                        'name': 'Card',
                        'variants': ['default', 'elevated', 'outlined'],
                        'sizes': ['compact', 'standard', 'expanded'],
                        'features': ['shadow', 'border', 'hover_effect']
                    },
                    {
                        'name': 'Form',
                        'variants': ['standard', 'floating', 'outlined'],
                        'validation': ['real_time', 'on_submit', 'on_blur'],
                        'accessibility': ['screen_reader', 'keyboard_navigation']
                    },
                    {
                        'name': 'Navigation',
                        'types': ['horizontal', 'vertical', 'breadcrumb', 'tabs'],
                        'responsive': ['mobile_menu', 'collapsible', 'sticky'],
                        'indicators': ['active_state', 'progress', 'notifications']
                    },
                    {
                        'name': 'Modal',
                        'sizes': ['small', 'medium', 'large', 'fullscreen'],
                        'animations': ['slide', 'fade', 'zoom', 'bounce'],
                        'features': ['backdrop_blur', 'esc_close', 'click_outside_close']
                    }
                ]
            })
        
        @self.uiux_blueprint.route('/pwa-manifest.json')
        def pwa_manifest():
            """Progressive Web App manifest"""
            return jsonify({
                "name": "College Kiosk Management System",
                "short_name": "College Kiosk",
                "description": "Enterprise food service management system",
                "start_url": "/",
                "display": "standalone",
                "background_color": "#FF5722",
                "theme_color": "#FF5722",
                "orientation": "portrait-primary",
                "categories": ["food", "business", "productivity"],
                "lang": "en",
                "icons": [
                    {
                        "src": "/static/images/icon-72x72.png",
                        "sizes": "72x72",
                        "type": "image/png",
                        "purpose": "maskable any"
                    },
                    {
                        "src": "/static/images/icon-96x96.png",
                        "sizes": "96x96",
                        "type": "image/png",
                        "purpose": "maskable any"
                    },
                    {
                        "src": "/static/images/icon-128x128.png",
                        "sizes": "128x128",
                        "type": "image/png",
                        "purpose": "maskable any"
                    },
                    {
                        "src": "/static/images/icon-144x144.png",
                        "sizes": "144x144",
                        "type": "image/png",
                        "purpose": "maskable any"
                    },
                    {
                        "src": "/static/images/icon-152x152.png",
                        "sizes": "152x152",
                        "type": "image/png",
                        "purpose": "maskable any"
                    },
                    {
                        "src": "/static/images/icon-192x192.png",
                        "sizes": "192x192",
                        "type": "image/png",
                        "purpose": "maskable any"
                    },
                    {
                        "src": "/static/images/icon-384x384.png",
                        "sizes": "384x384",
                        "type": "image/png",
                        "purpose": "maskable any"
                    },
                    {
                        "src": "/static/images/icon-512x512.png",
                        "sizes": "512x512",
                        "type": "image/png",
                        "purpose": "maskable any"
                    }
                ],
                "screenshots": [
                    {
                        "src": "/static/images/screenshot-desktop.png",
                        "sizes": "1280x720",
                        "type": "image/png",
                        "form_factor": "wide"
                    },
                    {
                        "src": "/static/images/screenshot-mobile.png",
                        "sizes": "390x844",
                        "type": "image/png"
                    }
                ],
                "shortcuts": [
                    {
                        "name": "New Order",
                        "short_name": "Order",
                        "description": "Create a new order",
                        "url": "/order",
                        "icons": [
                            {
                                "src": "/static/images/shortcut-order.png",
                                "sizes": "96x96"
                            }
                        ]
                    },
                    {
                        "name": "Menu",
                        "short_name": "Menu",
                        "description": "View menu items",
                        "url": "/menu",
                        "icons": [
                            {
                                "src": "/static/images/shortcut-menu.png",
                                "sizes": "96x96"
                            }
                        ]
                    }
                ]
            })
        
        @self.uiux_blueprint.route('/service-worker.js')
        def service_worker():
            """Service worker for PWA functionality"""
            return render_template_string(self.get_service_worker_template())
    
    def generate_ui_components(self):
        """Generate modern UI component CSS and JavaScript"""
        
        # Modern CSS with themes
        modern_css = self.get_modern_css()
        
        # Advanced JavaScript for interactions
        advanced_js = self.get_advanced_javascript()
        
        # Save to static files
        static_dir = os.path.join(os.path.dirname(self.app.instance_path), 'frontend', 'static')
        os.makedirs(os.path.join(static_dir, 'css'), exist_ok=True)
        os.makedirs(os.path.join(static_dir, 'js'), exist_ok=True)
        
        with open(os.path.join(static_dir, 'css', 'modern-ui.css'), 'w') as f:
            f.write(modern_css)
        
        with open(os.path.join(static_dir, 'js', 'ui-enhancements.js'), 'w') as f:
            f.write(advanced_js)
    
    def get_modern_css(self):
        """Get modern CSS for advanced UI"""
        return '''
/* Modern UI Enhancement CSS */
:root {
  /* Light Theme Colors */
  --primary-color: #FF5722;
  --primary-dark: #D84315;
  --primary-light: #FF8A65;
  --secondary-color: #2196F3;
  --secondary-dark: #1976D2;
  --secondary-light: #64B5F6;
  --accent-color: #FFC107;
  --background-color: #FFFFFF;
  --surface-color: #FAFAFA;
  --error-color: #F44336;
  --warning-color: #FF9800;
  --success-color: #4CAF50;
  --info-color: #00BCD4;
  --text-primary: #212121;
  --text-secondary: #757575;
  --text-disabled: #BDBDBD;
  --divider-color: #E0E0E0;
  
  /* Spacing */
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-xxl: 48px;
  
  /* Typography */
  --font-family-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-family-mono: 'JetBrains Mono', Monaco, 'Cascadia Code', monospace;
  --font-size-xs: 12px;
  --font-size-sm: 14px;
  --font-size-md: 16px;
  --font-size-lg: 18px;
  --font-size-xl: 20px;
  --font-size-xxl: 24px;
  --font-size-display: 32px;
  
  /* Borders and Shadows */
  --border-radius-sm: 4px;
  --border-radius-md: 8px;
  --border-radius-lg: 12px;
  --border-radius-xl: 16px;
  --border-radius-full: 9999px;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  
  /* Animations */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);
}

/* Dark Theme */
[data-theme="dark"] {
  --primary-color: #FF7043;
  --primary-dark: #D84315;
  --primary-light: #FFAB91;
  --secondary-color: #42A5F5;
  --secondary-dark: #1976D2;
  --secondary-light: #90CAF9;
  --accent-color: #FFD54F;
  --background-color: #121212;
  --surface-color: #1E1E1E;
  --error-color: #CF6679;
  --warning-color: #FFB74D;
  --success-color: #81C784;
  --info-color: #4DD0E1;
  --text-primary: #FFFFFF;
  --text-secondary: #B3B3B3;
  --text-disabled: #666666;
  --divider-color: #333333;
}

/* High Contrast Theme */
[data-theme="high-contrast"] {
  --primary-color: #000000;
  --secondary-color: #FFFF00;
  --background-color: #FFFFFF;
  --surface-color: #FFFFFF;
  --text-primary: #000000;
  --text-secondary: #000000;
  --divider-color: #000000;
}

/* Base Styles */
* {
  box-sizing: border-box;
}

body {
  font-family: var(--font-family-primary);
  font-size: var(--font-size-md);
  line-height: 1.6;
  color: var(--text-primary);
  background-color: var(--background-color);
  margin: 0;
  padding: 0;
  transition: background-color var(--transition-normal), color var(--transition-normal);
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
  margin: 0 0 var(--spacing-md) 0;
  font-weight: 600;
  line-height: 1.2;
}

h1 { font-size: var(--font-size-display); }
h2 { font-size: var(--font-size-xxl); }
h3 { font-size: var(--font-size-xl); }
h4 { font-size: var(--font-size-lg); }
h5 { font-size: var(--font-size-md); }
h6 { font-size: var(--font-size-sm); }

/* Modern Button Component */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  font-family: inherit;
  font-size: var(--font-size-sm);
  font-weight: 500;
  text-decoration: none;
  border: none;
  border-radius: var(--border-radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
  overflow: hidden;
  user-select: none;
  white-space: nowrap;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  pointer-events: none;
}

.btn-primary {
  background-color: var(--primary-color);
  color: white;
}

.btn-primary:hover {
  background-color: var(--primary-dark);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-secondary {
  background-color: var(--secondary-color);
  color: white;
}

.btn-secondary:hover {
  background-color: var(--secondary-dark);
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-outline {
  background-color: transparent;
  color: var(--primary-color);
  border: 2px solid var(--primary-color);
}

.btn-outline:hover {
  background-color: var(--primary-color);
  color: white;
}

.btn-ghost {
  background-color: transparent;
  color: var(--text-primary);
}

.btn-ghost:hover {
  background-color: var(--surface-color);
}

/* Button Sizes */
.btn-sm {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: var(--font-size-xs);
}

.btn-lg {
  padding: var(--spacing-md) var(--spacing-lg);
  font-size: var(--font-size-lg);
}

/* Modern Card Component */
.card {
  background-color: var(--surface-color);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-normal);
  overflow: hidden;
}

.card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.card-elevated {
  box-shadow: var(--shadow-lg);
}

.card-elevated:hover {
  box-shadow: var(--shadow-xl);
}

.card-outlined {
  border: 1px solid var(--divider-color);
  box-shadow: none;
}

.card-header {
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--divider-color);
}

.card-body {
  padding: var(--spacing-lg);
}

.card-footer {
  padding: var(--spacing-lg);
  border-top: 1px solid var(--divider-color);
  background-color: var(--background-color);
}

/* Modern Form Components */
.form-group {
  margin-bottom: var(--spacing-lg);
}

.form-label {
  display: block;
  margin-bottom: var(--spacing-xs);
  font-weight: 500;
  color: var(--text-primary);
}

.form-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  font-family: inherit;
  font-size: var(--font-size-md);
  border: 2px solid var(--divider-color);
  border-radius: var(--border-radius-md);
  background-color: var(--surface-color);
  color: var(--text-primary);
  transition: all var(--transition-fast);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(255, 87, 34, 0.1);
}

.form-input:invalid {
  border-color: var(--error-color);
}

.form-input:invalid:focus {
  box-shadow: 0 0 0 3px rgba(244, 67, 54, 0.1);
}

/* Floating Label */
.form-floating {
  position: relative;
}

.form-floating .form-input {
  padding: var(--spacing-lg) var(--spacing-md) var(--spacing-sm);
}

.form-floating .form-label {
  position: absolute;
  top: var(--spacing-lg);
  left: var(--spacing-md);
  font-size: var(--font-size-md);
  color: var(--text-secondary);
  pointer-events: none;
  transition: all var(--transition-fast);
  background-color: var(--surface-color);
  padding: 0 var(--spacing-xs);
}

.form-floating .form-input:focus + .form-label,
.form-floating .form-input:not(:placeholder-shown) + .form-label {
  top: 0;
  font-size: var(--font-size-xs);
  color: var(--primary-color);
}

/* Modern Navigation */
.navbar {
  background-color: var(--surface-color);
  border-bottom: 1px solid var(--divider-color);
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.navbar-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-lg);
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
}

.navbar-brand {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--primary-color);
  text-decoration: none;
}

.navbar-nav {
  display: flex;
  gap: var(--spacing-md);
  list-style: none;
  margin: 0;
  padding: 0;
}

.navbar-nav a {
  color: var(--text-primary);
  text-decoration: none;
  padding: var(--spacing-sm) var(--spacing-md);
  border-radius: var(--border-radius-md);
  transition: all var(--transition-fast);
}

.navbar-nav a:hover,
.navbar-nav a.active {
  background-color: var(--primary-color);
  color: white;
}

/* Modern Modal */
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  opacity: 0;
  visibility: hidden;
  transition: all var(--transition-normal);
  backdrop-filter: blur(4px);
}

.modal.show {
  opacity: 1;
  visibility: visible;
}

.modal-dialog {
  background-color: var(--surface-color);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-xl);
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
  transform: scale(0.9) translateY(-20px);
  transition: transform var(--transition-normal);
}

.modal.show .modal-dialog {
  transform: scale(1) translateY(0);
}

.modal-header {
  padding: var(--spacing-lg);
  border-bottom: 1px solid var(--divider-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.modal-title {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  font-size: var(--font-size-xl);
  cursor: pointer;
  padding: var(--spacing-sm);
  border-radius: var(--border-radius-full);
  transition: background-color var(--transition-fast);
}

.modal-close:hover {
  background-color: var(--divider-color);
}

.modal-body {
  padding: var(--spacing-lg);
}

.modal-footer {
  padding: var(--spacing-lg);
  border-top: 1px solid var(--divider-color);
  display: flex;
  gap: var(--spacing-md);
  justify-content: flex-end;
}

/* Loading States */
.loading {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid transparent;
  border-top: 2px solid currentColor;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Accessibility */
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Focus Management */
:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

/* Reduced Motion */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}

/* Responsive Design */
@media (max-width: 768px) {
  :root {
    --spacing-md: 12px;
    --spacing-lg: 16px;
    --spacing-xl: 24px;
  }
  
  .navbar-nav {
    display: none;
  }
  
  .card-body {
    padding: var(--spacing-md);
  }
  
  .modal-dialog {
    margin: var(--spacing-md);
    width: calc(100% - var(--spacing-lg));
  }
}

/* Print Styles */
@media print {
  .navbar,
  .modal,
  .btn {
    display: none !important;
  }
  
  .card {
    box-shadow: none;
    border: 1px solid #000;
  }
}
'''
    
    def get_advanced_javascript(self):
        """Get advanced JavaScript for UI enhancements"""
        return '''
// Advanced UI Enhancement JavaScript
class UIManager {
    constructor() {
        this.theme = localStorage.getItem('theme') || 'light';
        this.accessibility = JSON.parse(localStorage.getItem('accessibility')) || {};
        this.animations = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        this.init();
        this.setupThemeToggle();
        this.setupAccessibility();
        this.setupInteractionTracking();
        this.setupPWA();
    }
    
    init() {
        document.documentElement.setAttribute('data-theme', this.theme);
        this.applyAccessibilitySettings();
        this.setupKeyboardNavigation();
        this.setupIntersectionObserver();
        this.setupFormValidation();
    }
    
    // Theme Management
    setupThemeToggle() {
        const themeToggle = document.querySelector('[data-theme-toggle]');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }
        
        // System theme detection
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addListener((e) => {
                if (this.theme === 'auto') {
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }
    
    toggleTheme() {
        const themes = ['light', 'dark', 'blue', 'high-contrast'];
        const currentIndex = themes.indexOf(this.theme);
        const nextIndex = (currentIndex + 1) % themes.length;
        this.setTheme(themes[nextIndex]);
    }
    
    setTheme(theme) {
        this.theme = theme;
        localStorage.setItem('theme', theme);
        document.documentElement.setAttribute('data-theme', theme);
        
        // Notify other components
        window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }));
    }
    
    // Accessibility Features
    setupAccessibility() {
        const accessibilityToggle = document.querySelector('[data-accessibility-toggle]');
        if (accessibilityToggle) {
            accessibilityToggle.addEventListener('click', () => {
                this.toggleAccessibilityMode();
            });
        }
    }
    
    applyAccessibilitySettings() {
        if (this.accessibility.highContrast) {
            document.documentElement.classList.add('high-contrast');
        }
        
        if (this.accessibility.largeText) {
            document.documentElement.style.fontSize = '120%';
        }
        
        if (this.accessibility.reducedMotion) {
            document.documentElement.style.setProperty('--transition-fast', '0ms');
            document.documentElement.style.setProperty('--transition-normal', '0ms');
            document.documentElement.style.setProperty('--transition-slow', '0ms');
        }
    }
    
    toggleAccessibilityMode() {
        this.accessibility.enabled = !this.accessibility.enabled;
        localStorage.setItem('accessibility', JSON.stringify(this.accessibility));
        this.applyAccessibilitySettings();
    }
    
    // Keyboard Navigation
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Tab navigation enhancement
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
            
            // Escape key handling
            if (e.key === 'Escape') {
                this.closeActiveModal();
                this.closeActiveDropdown();
            }
            
            // Arrow key navigation for lists
            if (['ArrowUp', 'ArrowDown'].includes(e.key)) {
                this.handleArrowNavigation(e);
            }
        });
        
        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });
    }
    
    handleArrowNavigation(e) {
        const focusableElements = document.querySelectorAll('[data-keyboard-nav]');
        const currentIndex = Array.from(focusableElements).indexOf(document.activeElement);
        
        if (currentIndex === -1) return;
        
        let nextIndex;
        if (e.key === 'ArrowUp') {
            nextIndex = currentIndex > 0 ? currentIndex - 1 : focusableElements.length - 1;
        } else {
            nextIndex = currentIndex < focusableElements.length - 1 ? currentIndex + 1 : 0;
        }
        
        focusableElements[nextIndex].focus();
        e.preventDefault();
    }
    
    // Animation and Interaction Tracking
    setupInteractionTracking() {
        // Track user interactions for analytics
        document.addEventListener('click', (e) => {
            this.trackInteraction('click', e.target);
        });
        
        document.addEventListener('focus', (e) => {
            this.trackInteraction('focus', e.target);
        }, true);
        
        // Performance monitoring
        this.setupPerformanceMonitoring();
    }
    
    trackInteraction(type, element) {
        const data = {
            type,
            element: element.tagName,
            className: element.className,
            id: element.id,
            timestamp: new Date().toISOString(),
            url: window.location.href
        };
        
        // Send to analytics endpoint
        fetch('/uiux/analytics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        }).catch(() => {
            // Store locally if network fails
            const stored = JSON.parse(localStorage.getItem('ui-analytics') || '[]');
            stored.push(data);
            localStorage.setItem('ui-analytics', JSON.stringify(stored.slice(-100)));
        });
    }
    
    // Intersection Observer for Animations
    setupIntersectionObserver() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        
        document.querySelectorAll('[data-animate]').forEach(el => {
            observer.observe(el);
        });
    }
    
    // Form Validation Enhancement
    setupFormValidation() {
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });
            
            // Real-time validation
            form.querySelectorAll('input, textarea, select').forEach(field => {
                field.addEventListener('blur', () => {
                    this.validateField(field);
                });
                
                field.addEventListener('input', () => {
                    if (field.classList.contains('invalid')) {
                        this.validateField(field);
                    }
                });
            });
        });
    }
    
    validateForm(form) {
        let isValid = true;
        form.querySelectorAll('input, textarea, select').forEach(field => {
            if (!this.validateField(field)) {
                isValid = false;
            }
        });
        return isValid;
    }
    
    validateField(field) {
        const rules = field.dataset.validation?.split('|') || [];
        let isValid = true;
        let errorMessage = '';
        
        // Required validation
        if (rules.includes('required') && !field.value.trim()) {
            isValid = false;
            errorMessage = 'This field is required.';
        }
        
        // Email validation
        if (rules.includes('email') && field.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(field.value)) {
                isValid = false;
                errorMessage = 'Please enter a valid email address.';
            }
        }
        
        // Length validation
        const minLength = rules.find(rule => rule.startsWith('min:'));
        if (minLength && field.value.length < parseInt(minLength.split(':')[1])) {
            isValid = false;
            errorMessage = `Minimum length is ${minLength.split(':')[1]} characters.`;
        }
        
        this.showFieldValidation(field, isValid, errorMessage);
        return isValid;
    }
    
    showFieldValidation(field, isValid, message) {
        field.classList.toggle('invalid', !isValid);
        field.classList.toggle('valid', isValid);
        
        let errorElement = field.parentNode.querySelector('.field-error');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'field-error';
            field.parentNode.appendChild(errorElement);
        }
        
        errorElement.textContent = isValid ? '' : message;
        errorElement.style.display = isValid ? 'none' : 'block';
    }
    
    // Modal Management
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('show');
            document.body.style.overflow = 'hidden';
            
            // Focus management
            const firstFocusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (firstFocusable) {
                firstFocusable.focus();
            }
        }
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }
    
    closeActiveModal() {
        const activeModal = document.querySelector('.modal.show');
        if (activeModal) {
            activeModal.classList.remove('show');
            document.body.style.overflow = '';
        }
    }
    
    closeActiveDropdown() {
        document.querySelectorAll('.dropdown.show').forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    }
    
    // Progressive Web App Features
    setupPWA() {
        // Service Worker Registration
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/uiux/service-worker.js')
                .then(registration => console.log('SW registered:', registration))
                .catch(error => console.log('SW registration failed:', error));
        }
        
        // Install Prompt
        let deferredPrompt;
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            this.showInstallButton();
        });
        
        // App Install Button
        const installButton = document.querySelector('[data-install-app]');
        if (installButton) {
            installButton.addEventListener('click', async () => {
                if (deferredPrompt) {
                    deferredPrompt.prompt();
                    const { outcome } = await deferredPrompt.userChoice;
                    console.log(`User response to install prompt: ${outcome}`);
                    deferredPrompt = null;
                    this.hideInstallButton();
                }
            });
        }
    }
    
    showInstallButton() {
        const installButton = document.querySelector('[data-install-app]');
        if (installButton) {
            installButton.style.display = 'block';
        }
    }
    
    hideInstallButton() {
        const installButton = document.querySelector('[data-install-app]');
        if (installButton) {
            installButton.style.display = 'none';
        }
    }
    
    // Performance Monitoring
    setupPerformanceMonitoring() {
        // Monitor page load performance
        window.addEventListener('load', () => {
            if (performance.getEntriesByType) {
                const perfData = performance.getEntriesByType('navigation')[0];
                this.trackPerformance({
                    loadTime: perfData.loadEventEnd - perfData.fetchStart,
                    domContentLoaded: perfData.domContentLoadedEventEnd - perfData.fetchStart,
                    firstPaint: performance.getEntriesByType('paint')[0]?.startTime || 0
                });
            }
        });
        
        // Monitor long tasks
        if ('PerformanceObserver' in window) {
            const observer = new PerformanceObserver((list) => {
                list.getEntries().forEach((entry) => {
                    if (entry.duration > 50) {
                        this.trackPerformance({
                            type: 'long-task',
                            duration: entry.duration,
                            startTime: entry.startTime
                        });
                    }
                });
            });
            observer.observe({ entryTypes: ['longtask'] });
        }
    }
    
    trackPerformance(data) {
        fetch('/uiux/performance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ...data,
                timestamp: new Date().toISOString(),
                url: window.location.href,
                userAgent: navigator.userAgent
            })
        }).catch(() => {
            // Store locally if network fails
            const stored = JSON.parse(localStorage.getItem('performance-data') || '[]');
            stored.push(data);
            localStorage.setItem('performance-data', JSON.stringify(stored.slice(-50)));
        });
    }
    
    // Utility Methods
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    throttle(func, limit) {
        let inThrottle;
        return function executedFunction(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
}

// Component Classes
class ModernButton {
    constructor(element) {
        this.element = element;
        this.init();
    }
    
    init() {
        this.element.addEventListener('click', (e) => {
            this.createRippleEffect(e);
        });
    }
    
    createRippleEffect(e) {
        const button = e.currentTarget;
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        const ripple = document.createElement('span');
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.5);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        `;
        
        button.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
    }
}

class Toast {
    static show(message, type = 'info', duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-message">${message}</span>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Add to container or create one
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        container.appendChild(toast);
        
        // Auto remove
        setTimeout(() => {
            toast.remove();
        }, duration);
    }
}

// Initialize UI Manager
document.addEventListener('DOMContentLoaded', () => {
    window.uiManager = new UIManager();
    
    // Initialize modern buttons
    document.querySelectorAll('.btn').forEach(btn => {
        new ModernButton(btn);
    });
    
    // Setup modal triggers
    document.querySelectorAll('[data-modal-trigger]').forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            const modalId = trigger.dataset.modalTrigger;
            window.uiManager.openModal(modalId);
        });
    });
    
    // Setup modal close buttons
    document.querySelectorAll('.modal-close, [data-modal-close]').forEach(closeBtn => {
        closeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const modal = closeBtn.closest('.modal');
            if (modal) {
                window.uiManager.closeModal(modal.id);
            }
        });
    });
    
    // Close modal on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                window.uiManager.closeModal(modal.id);
            }
        });
    });
});

// Add CSS for animations
const animationCSS = `
@keyframes ripple {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

.animate-in {
    animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(30px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 3000;
    pointer-events: none;
}

.toast {
    background: var(--surface-color);
    border-radius: var(--border-radius-md);
    box-shadow: var(--shadow-lg);
    margin-bottom: 10px;
    max-width: 400px;
    opacity: 0;
    transform: translateX(100%);
    animation: slideIn 0.3s ease-out forwards;
    pointer-events: auto;
}

.toast-info { border-left: 4px solid var(--info-color); }
.toast-success { border-left: 4px solid var(--success-color); }
.toast-warning { border-left: 4px solid var(--warning-color); }
.toast-error { border-left: 4px solid var(--error-color); }

.toast-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-md);
}

.toast-close {
    background: none;
    border: none;
    font-size: 18px;
    cursor: pointer;
    margin-left: var(--spacing-md);
}

@keyframes slideIn {
    to {
        opacity: 1;
        transform: translateX(0);
    }
}
`;

// Inject animation CSS
const style = document.createElement('style');
style.textContent = animationCSS;
document.head.appendChild(style);
'''
    
    def get_service_worker_template(self):
        """Get service worker template for PWA"""
        return '''
// Service Worker for PWA functionality
const CACHE_NAME = 'college-kiosk-v2.0';
const urlsToCache = [
    '/',
    '/static/css/modern-ui.css',
    '/static/js/ui-enhancements.js',
    '/static/images/icon-192x192.png',
    '/static/images/icon-512x512.png',
    '/offline.html'
];

// Install event
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => cache.addAll(urlsToCache))
    );
});

// Fetch event
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Return cached version or fetch from network
                return response || fetch(event.request);
            })
            .catch(() => {
                // If both cache and network fail, show offline page
                if (event.request.destination === 'document') {
                    return caches.match('/offline.html');
                }
            })
    );
});

// Activate event
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Background sync
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync') {
        event.waitUntil(doBackgroundSync());
    }
});

async function doBackgroundSync() {
    // Sync offline data when connection is restored
    const cache = await caches.open(CACHE_NAME);
    const offlineData = await cache.match('/offline-data');
    
    if (offlineData) {
        const data = await offlineData.json();
        
        // Send offline data to server
        try {
            await fetch('/api/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            // Remove offline data after successful sync
            await cache.delete('/offline-data');
        } catch (error) {
            console.log('Background sync failed:', error);
        }
    }
}

// Push notifications
self.addEventListener('push', (event) => {
    const options = {
        body: event.data ? event.data.text() : 'New notification',
        icon: '/static/images/icon-192x192.png',
        badge: '/static/images/badge-72x72.png',
        tag: 'college-kiosk',
        actions: [
            {
                action: 'view',
                title: 'View',
                icon: '/static/images/action-view.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss',
                icon: '/static/images/action-dismiss.png'
            }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('College Kiosk', options)
    );
});

// Notification click
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});
'''
    
    def track_ui_interaction(self, user_id, page_path, component_name, action, session_id=None):
        """Track UI interaction for analytics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO ui_analytics 
            (user_id, page_path, component_name, action, session_id, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, page_path, component_name, action, session_id, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_ui_analytics(self, days=7):
        """Get UI analytics data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Most interacted components
        cursor.execute('''
            SELECT component_name, action, COUNT(*) as interaction_count
            FROM ui_analytics
            WHERE timestamp > ?
            GROUP BY component_name, action
            ORDER BY interaction_count DESC
            LIMIT 20
        ''', (start_date,))
        
        top_interactions = cursor.fetchall()
        
        # Page views
        cursor.execute('''
            SELECT page_path, COUNT(*) as views
            FROM ui_analytics
            WHERE timestamp > ?
            GROUP BY page_path
            ORDER BY views DESC
        ''', (start_date,))
        
        page_views = cursor.fetchall()
        
        conn.close()
        
        return {
            'period_days': days,
            'top_interactions': [
                {
                    'component': interaction[0],
                    'action': interaction[1],
                    'count': interaction[2]
                }
                for interaction in top_interactions
            ],
            'page_views': [
                {'page': view[0], 'views': view[1]}
                for view in page_views
            ]
        }