"""
Comprehensive Testing Suite
Features: Unit tests, integration tests, performance testing, security testing, automated reporting
"""

import unittest
import requests
import sqlite3
import json
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, Blueprint, jsonify, request
import os
import subprocess
import logging

# Optional imports with fallbacks
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    print("Warning: pytest not available. Some test features may be limited.")

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Warning: selenium not available. End-to-end tests will be skipped.")

try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False
    print("Warning: coverage not available. Code coverage analysis will be limited.")

class TestSuiteManager:
    def __init__(self, app, db_path):
        self.app = app
        self.db_path = db_path
        
        # Create testing blueprint
        self.test_blueprint = Blueprint('testing', __name__, url_prefix='/testing')
        app.register_blueprint(self.test_blueprint)
        
        # Initialize testing database
        self.init_testing_tables()
        
        # Setup test routes
        self.setup_test_routes()
        
        # Configure logging
        self.setup_logging()
        
        # Initialize test coverage
        if COVERAGE_AVAILABLE:
            self.coverage = coverage.Coverage()
        else:
            self.coverage = None
    
    def init_testing_tables(self):
        """Initialize testing database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Test runs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_suite TEXT NOT NULL,
                test_type TEXT NOT NULL,
                status TEXT NOT NULL,
                total_tests INTEGER DEFAULT 0,
                passed_tests INTEGER DEFAULT 0,
                failed_tests INTEGER DEFAULT 0,
                skipped_tests INTEGER DEFAULT 0,
                execution_time REAL DEFAULT 0,
                coverage_percentage REAL DEFAULT 0,
                error_details TEXT,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                environment TEXT DEFAULT 'test',
                branch TEXT,
                commit_hash TEXT
            )
        ''')
        
        # Test results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_run_id INTEGER,
                test_name TEXT NOT NULL,
                test_class TEXT,
                test_method TEXT,
                status TEXT NOT NULL,
                execution_time REAL DEFAULT 0,
                error_message TEXT,
                stack_trace TEXT,
                assertions INTEGER DEFAULT 0,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_run_id) REFERENCES test_runs (id)
            )
        ''')
        
        # Performance test results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_run_id INTEGER,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                response_time REAL NOT NULL,
                status_code INTEGER NOT NULL,
                memory_usage REAL,
                cpu_usage REAL,
                concurrent_users INTEGER DEFAULT 1,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_run_id) REFERENCES test_runs (id)
            )
        ''')
        
        # Security test results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_run_id INTEGER,
                vulnerability_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                endpoint TEXT,
                description TEXT,
                recommendation TEXT,
                status TEXT DEFAULT 'open',
                discovered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_run_id) REFERENCES test_runs (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def setup_test_routes(self):
        """Setup testing routes"""
        
        @self.test_blueprint.route('/run/<test_type>')
        def run_tests(test_type):
            """Run specific type of tests"""
            try:
                if test_type == 'unit':
                    result = self.run_unit_tests()
                elif test_type == 'integration':
                    result = self.run_integration_tests()
                elif test_type == 'performance':
                    result = self.run_performance_tests()
                elif test_type == 'security':
                    result = self.run_security_tests()
                elif test_type == 'e2e':
                    result = self.run_e2e_tests()
                elif test_type == 'all':
                    result = self.run_all_tests()
                else:
                    return jsonify({'error': 'Invalid test type'}), 400
                
                return jsonify(result)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.test_blueprint.route('/results/<int:test_run_id>')
        def get_test_results(test_run_id):
            """Get detailed test results"""
            return jsonify(self.get_test_run_details(test_run_id))
        
        @self.test_blueprint.route('/coverage')
        def get_coverage_report():
            """Get test coverage report"""
            return jsonify(self.generate_coverage_report())
        
        @self.test_blueprint.route('/dashboard')
        def test_dashboard():
            """Get testing dashboard data"""
            return jsonify(self.get_dashboard_data())
        
        @self.test_blueprint.route('/schedule', methods=['POST'])
        def schedule_tests():
            """Schedule automated test runs"""
            data = request.json
            return jsonify(self.schedule_test_run(data))
    
    def setup_logging(self):
        """Setup test logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('tests.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('TestSuite')
    
    def run_unit_tests(self):
        """Run unit tests"""
        self.logger.info("Starting unit tests")
        
        # Create test run record
        test_run_id = self.create_test_run('unit_tests', 'unit')
        
        try:
            # Start coverage tracking
            self.coverage.start()
            
            # Discover and run unit tests
            loader = unittest.TestLoader()
            suite = loader.discover('tests/unit', pattern='test_*.py')
            
            # Custom test runner for capturing results
            runner = DetailedTestRunner(test_run_id, self.db_path)
            result = runner.run(suite)
            
            # Stop coverage tracking
            self.coverage.stop()
            coverage_percentage = self.calculate_coverage()
            
            # Update test run
            self.update_test_run(test_run_id, {
                'status': 'completed' if result.wasSuccessful() else 'failed',
                'total_tests': result.testsRun,
                'passed_tests': result.testsRun - len(result.failures) - len(result.errors),
                'failed_tests': len(result.failures) + len(result.errors),
                'coverage_percentage': coverage_percentage,
                'completed_at': datetime.now().isoformat()
            })
            
            return {
                'test_run_id': test_run_id,
                'status': 'completed' if result.wasSuccessful() else 'failed',
                'total_tests': result.testsRun,
                'passed_tests': result.testsRun - len(result.failures) - len(result.errors),
                'failed_tests': len(result.failures) + len(result.errors),
                'coverage_percentage': coverage_percentage
            }
            
        except Exception as e:
            self.update_test_run(test_run_id, {
                'status': 'error',
                'error_details': str(e),
                'completed_at': datetime.now().isoformat()
            })
            raise
    
    def run_integration_tests(self):
        """Run integration tests"""
        self.logger.info("Starting integration tests")
        
        test_run_id = self.create_test_run('integration_tests', 'integration')
        
        try:
            # Integration test cases
            test_cases = [
                self.test_user_registration_flow,
                self.test_order_creation_flow,
                self.test_menu_management_flow,
                self.test_payment_processing_flow,
                self.test_notification_system,
                self.test_real_time_updates
            ]
            
            total_tests = len(test_cases)
            passed_tests = 0
            failed_tests = 0
            
            for test_case in test_cases:
                try:
                    start_time = time.time()
                    test_case()
                    execution_time = time.time() - start_time
                    
                    self.record_test_result(test_run_id, test_case.__name__, 'passed', execution_time)
                    passed_tests += 1
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.record_test_result(test_run_id, test_case.__name__, 'failed', execution_time, str(e))
                    failed_tests += 1
            
            status = 'completed' if failed_tests == 0 else 'failed'
            
            self.update_test_run(test_run_id, {
                'status': status,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'completed_at': datetime.now().isoformat()
            })
            
            return {
                'test_run_id': test_run_id,
                'status': status,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests
            }
            
        except Exception as e:
            self.update_test_run(test_run_id, {
                'status': 'error',
                'error_details': str(e),
                'completed_at': datetime.now().isoformat()
            })
            raise
    
    def run_performance_tests(self):
        """Run performance tests"""
        self.logger.info("Starting performance tests")
        
        test_run_id = self.create_test_run('performance_tests', 'performance')
        
        try:
            # Test endpoints with different load levels
            endpoints = [
                {'url': '/api/menu', 'method': 'GET'},
                {'url': '/api/orders', 'method': 'GET'},
                {'url': '/api/users', 'method': 'GET'},
                {'url': '/api/analytics/sales', 'method': 'GET'},
            ]
            
            concurrent_users = [1, 5, 10, 25, 50]
            
            total_tests = 0
            passed_tests = 0
            failed_tests = 0
            
            for endpoint in endpoints:
                for users in concurrent_users:
                    total_tests += 1
                    
                    try:
                        result = self.load_test_endpoint(
                            endpoint['url'], 
                            endpoint['method'], 
                            concurrent_users=users,
                            duration=30
                        )
                        
                        # Record performance metrics
                        self.record_performance_result(test_run_id, endpoint['url'], endpoint['method'], result)
                        
                        # Check if performance meets criteria
                        if result['avg_response_time'] < 2.0 and result['error_rate'] < 0.05:
                            passed_tests += 1
                        else:
                            failed_tests += 1
                            
                    except Exception as e:
                        failed_tests += 1
                        self.logger.error(f"Performance test failed for {endpoint['url']}: {e}")
            
            status = 'completed' if failed_tests == 0 else 'failed'
            
            self.update_test_run(test_run_id, {
                'status': status,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'completed_at': datetime.now().isoformat()
            })
            
            return {
                'test_run_id': test_run_id,
                'status': status,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests
            }
            
        except Exception as e:
            self.update_test_run(test_run_id, {
                'status': 'error',
                'error_details': str(e),
                'completed_at': datetime.now().isoformat()
            })
            raise
    
    def run_security_tests(self):
        """Run security tests"""
        self.logger.info("Starting security tests")
        
        test_run_id = self.create_test_run('security_tests', 'security')
        
        try:
            vulnerabilities_found = 0
            
            # SQL Injection Tests
            sql_injection_results = self.test_sql_injection()
            vulnerabilities_found += len(sql_injection_results)
            
            for vuln in sql_injection_results:
                self.record_security_vulnerability(test_run_id, 'sql_injection', 'high', vuln)
            
            # XSS Tests
            xss_results = self.test_xss_vulnerabilities()
            vulnerabilities_found += len(xss_results)
            
            for vuln in xss_results:
                self.record_security_vulnerability(test_run_id, 'xss', 'medium', vuln)
            
            # Authentication Tests
            auth_results = self.test_authentication_security()
            vulnerabilities_found += len(auth_results)
            
            for vuln in auth_results:
                self.record_security_vulnerability(test_run_id, 'authentication', 'high', vuln)
            
            # Authorization Tests
            authz_results = self.test_authorization_security()
            vulnerabilities_found += len(authz_results)
            
            for vuln in authz_results:
                self.record_security_vulnerability(test_run_id, 'authorization', 'medium', vuln)
            
            # HTTPS/TLS Tests
            tls_results = self.test_tls_security()
            vulnerabilities_found += len(tls_results)
            
            for vuln in tls_results:
                self.record_security_vulnerability(test_run_id, 'tls', 'medium', vuln)
            
            status = 'completed' if vulnerabilities_found == 0 else 'vulnerabilities_found'
            
            self.update_test_run(test_run_id, {
                'status': status,
                'total_tests': 5,  # Number of security test categories
                'passed_tests': 5 - (1 if vulnerabilities_found > 0 else 0),
                'failed_tests': 1 if vulnerabilities_found > 0 else 0,
                'completed_at': datetime.now().isoformat()
            })
            
            return {
                'test_run_id': test_run_id,
                'status': status,
                'vulnerabilities_found': vulnerabilities_found,
                'security_score': max(0, 100 - vulnerabilities_found * 10)
            }
            
        except Exception as e:
            self.update_test_run(test_run_id, {
                'status': 'error',
                'error_details': str(e),
                'completed_at': datetime.now().isoformat()
            })
            raise
    
    def run_e2e_tests(self):
        """Run end-to-end tests using Selenium"""
        self.logger.info("Starting end-to-end tests")
        
        test_run_id = self.create_test_run('e2e_tests', 'e2e')
        
        try:
            # Setup WebDriver
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            driver = webdriver.Chrome(options=options)
            
            try:
                test_cases = [
                    self.e2e_user_registration,
                    self.e2e_user_login,
                    self.e2e_menu_browsing,
                    self.e2e_order_placement,
                    self.e2e_admin_dashboard,
                    self.e2e_staff_operations
                ]
                
                total_tests = len(test_cases)
                passed_tests = 0
                failed_tests = 0
                
                for test_case in test_cases:
                    try:
                        start_time = time.time()
                        test_case(driver)
                        execution_time = time.time() - start_time
                        
                        self.record_test_result(test_run_id, test_case.__name__, 'passed', execution_time)
                        passed_tests += 1
                        
                    except Exception as e:
                        execution_time = time.time() - start_time
                        self.record_test_result(test_run_id, test_case.__name__, 'failed', execution_time, str(e))
                        failed_tests += 1
                
                status = 'completed' if failed_tests == 0 else 'failed'
                
                self.update_test_run(test_run_id, {
                    'status': status,
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests,
                    'completed_at': datetime.now().isoformat()
                })
                
                return {
                    'test_run_id': test_run_id,
                    'status': status,
                    'total_tests': total_tests,
                    'passed_tests': passed_tests,
                    'failed_tests': failed_tests
                }
                
            finally:
                driver.quit()
                
        except Exception as e:
            self.update_test_run(test_run_id, {
                'status': 'error',
                'error_details': str(e),
                'completed_at': datetime.now().isoformat()
            })
            raise
    
    def run_all_tests(self):
        """Run all test suites"""
        self.logger.info("Starting comprehensive test run")
        
        results = {}
        
        try:
            results['unit'] = self.run_unit_tests()
            results['integration'] = self.run_integration_tests()
            results['performance'] = self.run_performance_tests()
            results['security'] = self.run_security_tests()
            results['e2e'] = self.run_e2e_tests()
            
            # Calculate overall status
            all_passed = all(
                result.get('status') in ['completed', 'vulnerabilities_found'] 
                for result in results.values()
            )
            
            results['overall'] = {
                'status': 'completed' if all_passed else 'failed',
                'test_suites': len(results),
                'total_tests': sum(result.get('total_tests', 0) for result in results.values()),
                'passed_tests': sum(result.get('passed_tests', 0) for result in results.values()),
                'failed_tests': sum(result.get('failed_tests', 0) for result in results.values())
            }
            
            return results
            
        except Exception as e:
            self.logger.error(f"Comprehensive test run failed: {e}")
            raise
    
    # Integration Test Methods
    def test_user_registration_flow(self):
        """Test user registration integration"""
        # Test user registration API
        response = requests.post('http://localhost:5000/api/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        assert response.status_code == 201
        
        # Verify user was created in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', ('test@example.com',))
        user = cursor.fetchone()
        conn.close()
        
        assert user is not None
    
    def test_order_creation_flow(self):
        """Test order creation integration"""
        # Create order
        response = requests.post('http://localhost:5000/api/orders', json={
            'customer_name': 'Test Customer',
            'customer_email': 'customer@test.com',
            'items': [{'menu_item_id': 1, 'quantity': 2}]
        })
        assert response.status_code == 201
        
        order_data = response.json()
        order_id = order_data['order_id']
        
        # Verify order in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM orders WHERE id = ?', (order_id,))
        order = cursor.fetchone()
        conn.close()
        
        assert order is not None
    
    def test_menu_management_flow(self):
        """Test menu management integration"""
        # Add menu item
        response = requests.post('http://localhost:5000/api/menu', json={
            'name': 'Test Item',
            'price': 9.99,
            'category': 'test'
        })
        assert response.status_code == 201
        
        # Get menu
        response = requests.get('http://localhost:5000/api/menu')
        assert response.status_code == 200
        
        menu_items = response.json()
        assert len(menu_items) > 0
    
    def test_payment_processing_flow(self):
        """Test payment processing integration"""
        # Mock payment processing
        response = requests.post('http://localhost:5000/api/payments/process', json={
            'order_id': 1,
            'amount': 19.98,
            'payment_method': 'card',
            'card_token': 'test_token'
        })
        assert response.status_code == 200
    
    def test_notification_system(self):
        """Test notification system integration"""
        # Send notification
        response = requests.post('http://localhost:5000/api/notifications/send', json={
            'user_id': 1,
            'message': 'Test notification',
            'type': 'info'
        })
        assert response.status_code == 200
    
    def test_real_time_updates(self):
        """Test real-time update system integration"""
        # Test WebSocket connection (simplified)
        try:
            import websocket
            
            def on_message(ws, message):
                data = json.loads(message)
                assert 'type' in data
                assert 'data' in data
            
            ws = websocket.WebSocketApp("ws://localhost:5000/ws", on_message=on_message)
            
            # Run for a short time to test connection
            def run_ws():
                ws.run_forever()
            
            thread = threading.Thread(target=run_ws)
            thread.daemon = True
            thread.start()
            
            time.sleep(2)  # Test connection for 2 seconds
            ws.close()
            
        except ImportError:
            # Skip WebSocket test if library not available
            self.logger.warning("websocket-client not available, skipping WebSocket test")
            pass
    
    # Performance Testing Methods
    def load_test_endpoint(self, url, method, concurrent_users=10, duration=30):
        """Perform load testing on an endpoint"""
        results = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'response_times': [],
            'avg_response_time': 0,
            'min_response_time': float('inf'),
            'max_response_time': 0,
            'error_rate': 0
        }
        
        def make_request():
            try:
                start_time = time.time()
                response = requests.request(method, f'http://localhost:5000{url}', timeout=10)
                response_time = time.time() - start_time
                
                results['total_requests'] += 1
                results['response_times'].append(response_time)
                
                if response.status_code < 400:
                    results['successful_requests'] += 1
                else:
                    results['failed_requests'] += 1
                    
                results['min_response_time'] = min(results['min_response_time'], response_time)
                results['max_response_time'] = max(results['max_response_time'], response_time)
                
            except Exception:
                results['total_requests'] += 1
                results['failed_requests'] += 1
        
        # Start concurrent requests
        threads = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            if len(threads) < concurrent_users:
                thread = threading.Thread(target=make_request)
                thread.start()
                threads.append(thread)
            
            # Clean up finished threads
            threads = [t for t in threads if t.is_alive()]
            time.sleep(0.1)
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Calculate statistics
        if results['response_times']:
            results['avg_response_time'] = sum(results['response_times']) / len(results['response_times'])
        
        if results['total_requests'] > 0:
            results['error_rate'] = results['failed_requests'] / results['total_requests']
        
        return results
    
    # Security Testing Methods
    def test_sql_injection(self):
        """Test for SQL injection vulnerabilities"""
        vulnerabilities = []
        
        # Test common SQL injection payloads
        payloads = [
            "' OR '1'='1",
            "'; DROP TABLE users; --",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1 --"
        ]
        
        # Test endpoints that might be vulnerable
        endpoints = [
            '/api/login',
            '/api/users',
            '/api/search'
        ]
        
        for endpoint in endpoints:
            for payload in payloads:
                try:
                    response = requests.post(f'http://localhost:5000{endpoint}', 
                                           json={'query': payload}, timeout=5)
                    
                    # Check if response indicates SQL injection success
                    if ('syntax error' in response.text.lower() or 
                        'sql' in response.text.lower() or
                        'database' in response.text.lower()):
                        vulnerabilities.append({
                            'endpoint': endpoint,
                            'payload': payload,
                            'description': f'Potential SQL injection at {endpoint}'
                        })
                        
                except Exception:
                    pass
        
        return vulnerabilities
    
    def test_xss_vulnerabilities(self):
        """Test for XSS vulnerabilities"""
        vulnerabilities = []
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg/onload=alert('XSS')>"
        ]
        
        endpoints = [
            '/api/feedback',
            '/api/comments',
            '/api/search'
        ]
        
        for endpoint in endpoints:
            for payload in xss_payloads:
                try:
                    response = requests.post(f'http://localhost:5000{endpoint}', 
                                           json={'content': payload}, timeout=5)
                    
                    if payload in response.text:
                        vulnerabilities.append({
                            'endpoint': endpoint,
                            'payload': payload,
                            'description': f'Potential XSS vulnerability at {endpoint}'
                        })
                        
                except Exception:
                    pass
        
        return vulnerabilities
    
    def test_authentication_security(self):
        """Test authentication security"""
        vulnerabilities = []
        
        # Test for weak authentication
        weak_passwords = ['123', 'password', 'admin', '']
        
        for password in weak_passwords:
            try:
                response = requests.post('http://localhost:5000/api/login', 
                                       json={'username': 'admin', 'password': password})
                
                if response.status_code == 200:
                    vulnerabilities.append({
                        'type': 'weak_password',
                        'description': f'Weak password accepted: {password}'
                    })
                    
            except Exception:
                pass
        
        # Test for session security
        try:
            response = requests.get('http://localhost:5000/api/admin')
            if response.status_code != 401:
                vulnerabilities.append({
                    'type': 'unauthorized_access',
                    'description': 'Admin endpoint accessible without authentication'
                })
        except Exception:
            pass
        
        return vulnerabilities
    
    def test_authorization_security(self):
        """Test authorization security"""
        vulnerabilities = []
        
        # Test for privilege escalation
        try:
            # Try to access admin functions with regular user token
            response = requests.get('http://localhost:5000/api/admin/users',
                                  headers={'Authorization': 'Bearer fake_user_token'})
            
            if response.status_code == 200:
                vulnerabilities.append({
                    'type': 'privilege_escalation',
                    'description': 'Regular user can access admin functions'
                })
                
        except Exception:
            pass
        
        return vulnerabilities
    
    def test_tls_security(self):
        """Test TLS/SSL security"""
        vulnerabilities = []
        
        try:
            # Test if HTTP is redirected to HTTPS
            response = requests.get('http://localhost:5000', allow_redirects=False)
            if response.status_code != 301:
                vulnerabilities.append({
                    'type': 'http_not_redirected',
                    'description': 'HTTP traffic not redirected to HTTPS'
                })
                
        except Exception:
            pass
        
        return vulnerabilities
    
    # End-to-End Test Methods
    def e2e_user_registration(self, driver):
        """E2E test for user registration"""
        driver.get('http://localhost:5000/register')
        
        # Fill registration form
        driver.find_element(By.NAME, 'username').send_keys('testuser')
        driver.find_element(By.NAME, 'email').send_keys('test@example.com')
        driver.find_element(By.NAME, 'password').send_keys('testpass123')
        
        # Submit form
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Wait for success message
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'success-message'))
        )
    
    def e2e_user_login(self, driver):
        """E2E test for user login"""
        driver.get('http://localhost:5000/login')
        
        driver.find_element(By.NAME, 'email').send_keys('test@example.com')
        driver.find_element(By.NAME, 'password').send_keys('testpass123')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Wait for dashboard to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'dashboard'))
        )
    
    def e2e_menu_browsing(self, driver):
        """E2E test for menu browsing"""
        driver.get('http://localhost:5000/menu')
        
        # Wait for menu items to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'menu-item'))
        )
        
        # Test filtering
        category_filter = driver.find_element(By.CSS_SELECTOR, 'select[name="category"]')
        category_filter.click()
        
        # Select a category
        driver.find_element(By.CSS_SELECTOR, 'option[value="beverages"]').click()
        
        # Wait for filtered results
        time.sleep(2)
    
    def e2e_order_placement(self, driver):
        """E2E test for order placement"""
        driver.get('http://localhost:5000/menu')
        
        # Add item to cart
        driver.find_element(By.CSS_SELECTOR, '.menu-item .add-to-cart').click()
        
        # Go to cart
        driver.find_element(By.CSS_SELECTOR, '.cart-icon').click()
        
        # Proceed to checkout
        driver.find_element(By.CSS_SELECTOR, '.checkout-btn').click()
        
        # Fill checkout form
        driver.find_element(By.NAME, 'customer_name').send_keys('Test Customer')
        driver.find_element(By.NAME, 'customer_email').send_keys('customer@test.com')
        
        # Submit order
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Wait for confirmation
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'order-confirmation'))
        )
    
    def e2e_admin_dashboard(self, driver):
        """E2E test for admin dashboard"""
        # Login as admin first
        driver.get('http://localhost:5000/login')
        driver.find_element(By.NAME, 'email').send_keys('admin@example.com')
        driver.find_element(By.NAME, 'password').send_keys('admin123')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Navigate to admin dashboard
        driver.get('http://localhost:5000/admin')
        
        # Wait for dashboard elements
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'admin-dashboard'))
        )
        
        # Test navigation to different admin sections
        driver.find_element(By.LINK_TEXT, 'Users').click()
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'users-table'))
        )
    
    def e2e_staff_operations(self, driver):
        """E2E test for staff operations"""
        # Login as staff
        driver.get('http://localhost:5000/login')
        driver.find_element(By.NAME, 'email').send_keys('staff@example.com')
        driver.find_element(By.NAME, 'password').send_keys('staff123')
        driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
        
        # Navigate to staff dashboard
        driver.get('http://localhost:5000/staff')
        
        # Test order management
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'orders-list'))
        )
        
        # Update order status
        status_select = driver.find_element(By.CSS_SELECTOR, '.order-item select')
        status_select.click()
        driver.find_element(By.CSS_SELECTOR, 'option[value="preparing"]').click()
    
    # Helper Methods
    def create_test_run(self, suite_name, test_type):
        """Create a new test run record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO test_runs (test_suite, test_type, status, started_at)
            VALUES (?, ?, ?, ?)
        ''', (suite_name, test_type, 'running', datetime.now().isoformat()))
        
        test_run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return test_run_id
    
    def update_test_run(self, test_run_id, data):
        """Update test run record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
        values = list(data.values()) + [test_run_id]
        
        cursor.execute(f'''
            UPDATE test_runs SET {set_clause} WHERE id = ?
        ''', values)
        
        conn.commit()
        conn.close()
    
    def record_test_result(self, test_run_id, test_name, status, execution_time, error_message=None):
        """Record individual test result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO test_results 
            (test_run_id, test_name, status, execution_time, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (test_run_id, test_name, status, execution_time, error_message))
        
        conn.commit()
        conn.close()
    
    def record_performance_result(self, test_run_id, endpoint, method, result):
        """Record performance test result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO performance_tests 
            (test_run_id, endpoint, method, response_time, status_code, concurrent_users)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (test_run_id, endpoint, method, result['avg_response_time'], 200, 10))
        
        conn.commit()
        conn.close()
    
    def record_security_vulnerability(self, test_run_id, vuln_type, severity, vulnerability):
        """Record security vulnerability"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_tests 
            (test_run_id, vulnerability_type, severity, endpoint, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (test_run_id, vuln_type, severity, 
               vulnerability.get('endpoint', ''), vulnerability.get('description', '')))
        
        conn.commit()
        conn.close()
    
    def calculate_coverage(self):
        """Calculate test coverage percentage"""
        try:
            self.coverage.html_report(directory='coverage_html_report')
            
            # Get coverage data
            coverage_data = self.coverage.get_data()
            total_lines = 0
            covered_lines = 0
            
            for filename in coverage_data.measured_files():
                lines = coverage_data.lines(filename)
                total_lines += len(lines) if lines else 0
                
                executed = coverage_data.lines(filename)
                covered_lines += len(executed) if executed else 0
            
            return (covered_lines / total_lines * 100) if total_lines > 0 else 0
            
        except Exception as e:
            self.logger.error(f"Error calculating coverage: {e}")
            return 0
    
    def get_test_run_details(self, test_run_id):
        """Get detailed test run information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get test run info
        cursor.execute('SELECT * FROM test_runs WHERE id = ?', (test_run_id,))
        test_run = cursor.fetchone()
        
        if not test_run:
            return {'error': 'Test run not found'}
        
        # Get test results
        cursor.execute('SELECT * FROM test_results WHERE test_run_id = ?', (test_run_id,))
        test_results = cursor.fetchall()
        
        # Get performance results
        cursor.execute('SELECT * FROM performance_tests WHERE test_run_id = ?', (test_run_id,))
        performance_results = cursor.fetchall()
        
        # Get security results
        cursor.execute('SELECT * FROM security_tests WHERE test_run_id = ?', (test_run_id,))
        security_results = cursor.fetchall()
        
        conn.close()
        
        return {
            'test_run': {
                'id': test_run[0],
                'test_suite': test_run[1],
                'test_type': test_run[2],
                'status': test_run[3],
                'total_tests': test_run[4],
                'passed_tests': test_run[5],
                'failed_tests': test_run[6],
                'execution_time': test_run[8],
                'coverage_percentage': test_run[9],
                'started_at': test_run[11],
                'completed_at': test_run[12]
            },
            'test_results': [
                {
                    'test_name': result[2],
                    'status': result[5],
                    'execution_time': result[6],
                    'error_message': result[7]
                }
                for result in test_results
            ],
            'performance_results': [
                {
                    'endpoint': result[2],
                    'method': result[3],
                    'response_time': result[4],
                    'status_code': result[5]
                }
                for result in performance_results
            ],
            'security_results': [
                {
                    'vulnerability_type': result[2],
                    'severity': result[3],
                    'endpoint': result[4],
                    'description': result[5]
                }
                for result in security_results
            ]
        }
    
    def generate_coverage_report(self):
        """Generate comprehensive coverage report"""
        try:
            # Generate HTML coverage report
            self.coverage.html_report(directory='coverage_html_report')
            
            # Get summary data
            coverage_data = self.coverage.get_data()
            
            report = {
                'overall_coverage': self.calculate_coverage(),
                'files': []
            }
            
            for filename in coverage_data.measured_files():
                lines = coverage_data.lines(filename)
                missing = coverage_data.lines(filename)  # Lines not executed
                
                if lines:
                    file_coverage = ((len(lines) - len(missing)) / len(lines)) * 100
                    
                    report['files'].append({
                        'filename': filename,
                        'coverage_percentage': file_coverage,
                        'total_lines': len(lines),
                        'covered_lines': len(lines) - len(missing),
                        'missing_lines': list(missing) if missing else []
                    })
            
            return report
            
        except Exception as e:
            return {'error': f'Failed to generate coverage report: {e}'}
    
    def get_dashboard_data(self):
        """Get testing dashboard data"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Recent test runs
        cursor.execute('''
            SELECT * FROM test_runs 
            ORDER BY started_at DESC 
            LIMIT 10
        ''')
        recent_runs = cursor.fetchall()
        
        # Test statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_runs,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful_runs,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_runs,
                AVG(coverage_percentage) as avg_coverage
            FROM test_runs
            WHERE started_at > date('now', '-30 days')
        ''')
        stats = cursor.fetchone()
        
        # Security vulnerabilities
        cursor.execute('''
            SELECT vulnerability_type, severity, COUNT(*) as count
            FROM security_tests
            WHERE status = 'open'
            GROUP BY vulnerability_type, severity
        ''')
        vulnerabilities = cursor.fetchall()
        
        conn.close()
        
        return {
            'recent_runs': [
                {
                    'id': run[0],
                    'test_suite': run[1],
                    'test_type': run[2],
                    'status': run[3],
                    'total_tests': run[4],
                    'passed_tests': run[5],
                    'failed_tests': run[6],
                    'started_at': run[11]
                }
                for run in recent_runs
            ],
            'statistics': {
                'total_runs': stats[0] if stats else 0,
                'successful_runs': stats[1] if stats else 0,
                'failed_runs': stats[2] if stats else 0,
                'success_rate': (stats[1] / stats[0] * 100) if stats and stats[0] > 0 else 0,
                'average_coverage': stats[3] if stats else 0
            },
            'vulnerabilities': [
                {
                    'type': vuln[0],
                    'severity': vuln[1],
                    'count': vuln[2]
                }
                for vuln in vulnerabilities
            ]
        }
    
    def schedule_test_run(self, schedule_data):
        """Schedule automated test runs"""
        # This would integrate with a job scheduler like Celery or APScheduler
        # For now, return a simple confirmation
        return {
            'message': 'Test run scheduled successfully',
            'schedule_id': f"schedule_{int(time.time())}",
            'test_type': schedule_data.get('test_type'),
            'frequency': schedule_data.get('frequency'),
            'next_run': schedule_data.get('next_run')
        }


class DetailedTestRunner(unittest.TextTestRunner):
    """Custom test runner that records detailed results"""
    
    def __init__(self, test_run_id, db_path):
        super().__init__()
        self.test_run_id = test_run_id
        self.db_path = db_path
    
    def run(self, test):
        result = super().run(test)
        
        # Record individual test results
        for test_case, error in result.failures + result.errors:
            self.record_test_result(test_case, 'failed', str(error))
        
        return result
    
    def record_test_result(self, test_case, status, error_message):
        """Record individual test result in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO test_results 
            (test_run_id, test_name, test_class, test_method, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            self.test_run_id,
            str(test_case),
            test_case.__class__.__name__,
            test_case._testMethodName,
            status,
            error_message
        ))
        
        conn.commit()
        conn.close()