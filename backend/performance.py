"""
System Performance & Monitoring Module
Features: Database optimization, caching, monitoring, backup, alerts
"""

import sqlite3
import json
import time
import threading
import schedule
import logging
from datetime import datetime, timedelta
import psutil
import os
import shutil
import zipfile
import hashlib
from collections import defaultdict, deque
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart

# Redis caching (optional)
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class PerformanceMonitor:
    def __init__(self, db_path, redis_host='localhost', redis_port=6379):
        self.db_path = db_path
        self.metrics = defaultdict(deque)
        self.alerts = []
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('system_performance.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Redis setup
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
                self.redis_client.ping()
                self.logger.info("Redis cache connected successfully")
            except Exception as e:
                self.logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None
        
        # Performance thresholds
        self.thresholds = {
            'cpu_usage': 80,          # CPU usage percentage
            'memory_usage': 85,       # Memory usage percentage
            'disk_usage': 90,         # Disk usage percentage
            'response_time': 2000,    # Response time in milliseconds
            'error_rate': 5,          # Error rate percentage
            'db_connections': 10,     # Maximum database connections
        }
        
        self.init_monitoring_tables()
    
    def init_monitoring_tables(self):
        """Initialize monitoring tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # System metrics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                metric_type TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                threshold_exceeded INTEGER DEFAULT 0
            )
        ''')
        
        # Performance logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                endpoint TEXT,
                method TEXT,
                response_time REAL,
                status_code INTEGER,
                user_id INTEGER,
                ip_address TEXT,
                user_agent TEXT
            )
        ''')
        
        # Error logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                error_type TEXT NOT NULL,
                error_message TEXT,
                stack_trace TEXT,
                endpoint TEXT,
                user_id INTEGER,
                ip_address TEXT,
                resolved INTEGER DEFAULT 0
            )
        ''')
        
        # System alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                alert_type TEXT NOT NULL,
                severity TEXT DEFAULT 'medium', -- low, medium, high, critical
                title TEXT NOT NULL,
                message TEXT,
                triggered_by TEXT,
                acknowledged INTEGER DEFAULT 0,
                acknowledged_by INTEGER,
                acknowledged_at TEXT,
                resolved INTEGER DEFAULT 0,
                resolved_at TEXT
            )
        ''')
        
        # Database maintenance logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                operation_type TEXT NOT NULL, -- backup, vacuum, reindex, optimize
                status TEXT DEFAULT 'running', -- running, completed, failed
                start_time TEXT,
                end_time TEXT,
                duration_seconds REAL,
                details TEXT,
                error_message TEXT
            )
        ''')
        
        # Cache statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                cache_type TEXT NOT NULL, -- redis, memory, disk
                hit_count INTEGER DEFAULT 0,
                miss_count INTEGER DEFAULT 0,
                hit_rate REAL DEFAULT 0.0,
                memory_usage REAL DEFAULT 0.0,
                key_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def start_monitoring(self):
        """Start system monitoring"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitor_thread.start()
        
        # Schedule maintenance tasks
        schedule.every().day.at("02:00").do(self.perform_database_maintenance)
        schedule.every().hour.do(self.collect_system_metrics)
        schedule.every(5).minutes.do(self.check_system_health)
        
        self.logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.logger.info("System monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
    
    def collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.record_metric('system', 'cpu_usage', cpu_percent, '%')
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric('system', 'memory_usage', memory.percent, '%')
            self.record_metric('system', 'memory_available', memory.available / (1024**3), 'GB')
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            self.record_metric('system', 'disk_usage', disk_percent, '%')
            self.record_metric('system', 'disk_free', disk.free / (1024**3), 'GB')
            
            # Database size
            db_size = os.path.getsize(self.db_path) / (1024**2)  # MB
            self.record_metric('database', 'db_size', db_size, 'MB')
            
            # Network I/O
            net_io = psutil.net_io_counters()
            self.record_metric('network', 'bytes_sent', net_io.bytes_sent / (1024**2), 'MB')
            self.record_metric('network', 'bytes_recv', net_io.bytes_recv / (1024**2), 'MB')
            
            # Process count
            process_count = len(psutil.pids())
            self.record_metric('system', 'process_count', process_count, 'count')
            
            # Cache statistics if Redis is available
            if self.redis_client:
                self.collect_cache_metrics()
            
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
    
    def collect_cache_metrics(self):
        """Collect cache performance metrics"""
        try:
            info = self.redis_client.info()
            
            # Redis memory usage
            memory_used = info.get('used_memory', 0) / (1024**2)  # MB
            self.record_metric('cache', 'redis_memory', memory_used, 'MB')
            
            # Key count
            key_count = info.get('db0', {}).get('keys', 0) if 'db0' in info else 0
            self.record_metric('cache', 'redis_keys', key_count, 'count')
            
            # Hit rate calculation (if stats available)
            hits = info.get('keyspace_hits', 0)
            misses = info.get('keyspace_misses', 0)
            total = hits + misses
            hit_rate = (hits / total * 100) if total > 0 else 0
            
            # Store cache stats
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO cache_stats 
                (cache_type, hit_count, miss_count, hit_rate, memory_usage, key_count)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('redis', hits, misses, hit_rate, memory_used, key_count))
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error collecting cache metrics: {e}")
    
    def record_metric(self, metric_type, metric_name, value, unit, threshold_check=True):
        """Record a system metric"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        threshold_exceeded = 0
        if threshold_check and metric_name in self.thresholds:
            if value > self.thresholds[metric_name]:
                threshold_exceeded = 1
                self.create_alert(
                    'performance', 
                    'high',
                    f'{metric_name.title()} Threshold Exceeded',
                    f'{metric_name} is at {value}{unit}, exceeding threshold of {self.thresholds[metric_name]}{unit}',
                    'system_monitor'
                )
        
        cursor.execute('''
            INSERT INTO system_metrics 
            (metric_type, metric_name, value, unit, threshold_exceeded)
            VALUES (?, ?, ?, ?, ?)
        ''', (metric_type, metric_name, value, unit, threshold_exceeded))
        
        conn.commit()
        conn.close()
        
        # Keep in-memory metrics for quick access
        self.metrics[metric_name].append({
            'timestamp': datetime.now(),
            'value': value,
            'unit': unit
        })
        
        # Keep only last 100 readings in memory
        if len(self.metrics[metric_name]) > 100:
            self.metrics[metric_name].popleft()
    
    def log_performance(self, endpoint, method, response_time, status_code, user_id=None, ip_address=None, user_agent=None):
        """Log API performance"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO performance_logs 
            (endpoint, method, response_time, status_code, user_id, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (endpoint, method, response_time, status_code, user_id, ip_address, user_agent))
        
        conn.commit()
        conn.close()
        
        # Check response time threshold
        if response_time > self.thresholds['response_time']:
            self.create_alert(
                'performance',
                'medium',
                'Slow Response Time',
                f'Endpoint {endpoint} took {response_time}ms to respond',
                'performance_monitor'
            )
    
    def log_error(self, error_type, error_message, stack_trace=None, endpoint=None, user_id=None, ip_address=None):
        """Log system error"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO error_logs 
            (error_type, error_message, stack_trace, endpoint, user_id, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (error_type, error_message, stack_trace, endpoint, user_id, ip_address))
        
        conn.commit()
        conn.close()
        
        # Create alert for critical errors
        if error_type in ['DatabaseError', 'ConnectionError', 'SecurityError']:
            self.create_alert(
                'error',
                'critical',
                f'{error_type} Occurred',
                error_message,
                'error_monitor'
            )
        
        self.logger.error(f"{error_type}: {error_message}")
    
    def create_alert(self, alert_type, severity, title, message, triggered_by):
        """Create system alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO system_alerts 
            (alert_type, severity, title, message, triggered_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (alert_type, severity, title, message, triggered_by))
        
        alert_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        alert = {
            'id': alert_id,
            'type': alert_type,
            'severity': severity,
            'title': title,
            'message': message,
            'timestamp': datetime.now()
        }
        
        self.alerts.append(alert)
        self.logger.warning(f"Alert created: {title} - {message}")
        
        # Send email notification for critical alerts
        if severity == 'critical':
            self.send_alert_notification(alert)
        
        return alert_id
    
    def acknowledge_alert(self, alert_id, user_id):
        """Acknowledge an alert"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE system_alerts 
            SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (user_id, alert_id))
        
        conn.commit()
        conn.close()
    
    def check_system_health(self):
        """Perform system health checks"""
        health_score = 100
        issues = []
        
        # Check recent metrics
        current_time = datetime.now()
        five_minutes_ago = current_time - timedelta(minutes=5)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check for recent threshold violations
        cursor.execute('''
            SELECT metric_name, COUNT(*) 
            FROM system_metrics 
            WHERE threshold_exceeded = 1 AND timestamp > ?
            GROUP BY metric_name
        ''', (five_minutes_ago.isoformat(),))
        
        violations = cursor.fetchall()
        for metric, count in violations:
            health_score -= min(count * 5, 20)  # Max 20 points per metric
            issues.append(f"{metric} exceeded threshold {count} times")
        
        # Check for recent errors
        cursor.execute('''
            SELECT COUNT(*) FROM error_logs 
            WHERE timestamp > ? AND resolved = 0
        ''', (five_minutes_ago.isoformat(),))
        
        recent_errors = cursor.fetchone()[0]
        if recent_errors > 0:
            health_score -= min(recent_errors * 10, 30)
            issues.append(f"{recent_errors} unresolved errors")
        
        # Check database health
        try:
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            if integrity != 'ok':
                health_score -= 25
                issues.append("Database integrity issues detected")
        except Exception as e:
            health_score -= 25
            issues.append(f"Database health check failed: {e}")
        
        conn.close()
        
        # Record health score
        self.record_metric('system', 'health_score', max(health_score, 0), 'score', False)
        
        # Create alert if health is poor
        if health_score < 70:
            self.create_alert(
                'health',
                'high' if health_score < 50 else 'medium',
                'System Health Warning',
                f'System health score: {health_score}/100. Issues: {", ".join(issues)}',
                'health_monitor'
            )
    
    def perform_database_maintenance(self):
        """Perform database maintenance operations"""
        operations = [
            ('vacuum', self._vacuum_database),
            ('reindex', self._reindex_database),
            ('analyze', self._analyze_database),
            ('cleanup', self._cleanup_old_data)
        ]
        
        for operation, func in operations:
            self._log_maintenance_start(operation)
            start_time = time.time()
            
            try:
                func()
                duration = time.time() - start_time
                self._log_maintenance_complete(operation, duration)
                self.logger.info(f"Database {operation} completed in {duration:.2f} seconds")
            except Exception as e:
                duration = time.time() - start_time
                self._log_maintenance_failed(operation, duration, str(e))
                self.logger.error(f"Database {operation} failed: {e}")
    
    def _vacuum_database(self):
        """Vacuum database to reclaim space"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('VACUUM')
        conn.close()
    
    def _reindex_database(self):
        """Reindex database for better performance"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('REINDEX')
        conn.close()
    
    def _analyze_database(self):
        """Analyze database for query optimization"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('ANALYZE')
        conn.close()
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        cutoff_date = (datetime.now() - timedelta(days=30)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clean old metrics (keep last 30 days)
        cursor.execute('DELETE FROM system_metrics WHERE timestamp < ?', (cutoff_date,))
        
        # Clean old performance logs (keep last 30 days)
        cursor.execute('DELETE FROM performance_logs WHERE timestamp < ?', (cutoff_date,))
        
        # Clean resolved alerts older than 7 days
        alert_cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute('DELETE FROM system_alerts WHERE resolved = 1 AND resolved_at < ?', (alert_cutoff,))
        
        conn.commit()
        conn.close()
    
    def _log_maintenance_start(self, operation):
        """Log maintenance operation start"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO maintenance_logs (operation_type, status, start_time)
            VALUES (?, ?, ?)
        ''', (operation, 'running', datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def _log_maintenance_complete(self, operation, duration):
        """Log maintenance operation completion"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE maintenance_logs 
            SET status = ?, end_time = ?, duration_seconds = ?
            WHERE operation_type = ? AND status = 'running'
            ORDER BY timestamp DESC LIMIT 1
        ''', ('completed', datetime.now().isoformat(), duration, operation))
        conn.commit()
        conn.close()
    
    def _log_maintenance_failed(self, operation, duration, error):
        """Log maintenance operation failure"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE maintenance_logs 
            SET status = ?, end_time = ?, duration_seconds = ?, error_message = ?
            WHERE operation_type = ? AND status = 'running'
            ORDER BY timestamp DESC LIMIT 1
        ''', ('failed', datetime.now().isoformat(), duration, error, operation))
        conn.commit()
        conn.close()
    
    def create_backup(self, backup_path=None):
        """Create database backup"""
        if not backup_path:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"backup_{timestamp}.zip"
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add database file
                zipf.write(self.db_path, os.path.basename(self.db_path))
                
                # Add static files if they exist
                static_dirs = ['static', 'frontend/static', 'backend/static']
                for static_dir in static_dirs:
                    if os.path.exists(static_dir):
                        for root, dirs, files in os.walk(static_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path)
                                zipf.write(file_path, arcname)
            
            # Calculate backup hash for integrity
            with open(backup_path, 'rb') as f:
                backup_hash = hashlib.sha256(f.read()).hexdigest()
            
            self.logger.info(f"Backup created: {backup_path} (SHA256: {backup_hash})")
            return {'backup_path': backup_path, 'hash': backup_hash}
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {e}")
            raise
    
    def send_alert_notification(self, alert):
        """Send email notification for critical alerts"""
        # This would need email configuration
        # Placeholder implementation
        self.logger.critical(f"CRITICAL ALERT: {alert['title']} - {alert['message']}")
    
    def get_system_status(self):
        """Get current system status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Latest metrics
        cursor.execute('''
            SELECT metric_name, value, unit, timestamp
            FROM system_metrics
            WHERE timestamp > datetime('now', '-5 minutes')
            ORDER BY timestamp DESC
        ''')
        recent_metrics = cursor.fetchall()
        
        # Active alerts
        cursor.execute('''
            SELECT id, alert_type, severity, title, message, timestamp
            FROM system_alerts
            WHERE acknowledged = 0
            ORDER BY timestamp DESC
            LIMIT 10
        ''')
        active_alerts = cursor.fetchall()
        
        # System health score
        cursor.execute('''
            SELECT value FROM system_metrics
            WHERE metric_name = 'health_score'
            ORDER BY timestamp DESC
            LIMIT 1
        ''')
        health_result = cursor.fetchone()
        health_score = health_result[0] if health_result else 100
        
        conn.close()
        
        return {
            'health_score': health_score,
            'status': 'healthy' if health_score > 80 else 'warning' if health_score > 60 else 'critical',
            'recent_metrics': [
                {
                    'name': metric[0],
                    'value': metric[1],
                    'unit': metric[2],
                    'timestamp': metric[3]
                }
                for metric in recent_metrics
            ],
            'active_alerts': [
                {
                    'id': alert[0],
                    'type': alert[1],
                    'severity': alert[2],
                    'title': alert[3],
                    'message': alert[4],
                    'timestamp': alert[5]
                }
                for alert in active_alerts
            ]
        }
    
    def get_performance_report(self, hours=24):
        """Get performance report for specified hours"""
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Average response times by endpoint
        cursor.execute('''
            SELECT endpoint, AVG(response_time) as avg_response, COUNT(*) as request_count
            FROM performance_logs
            WHERE timestamp > ?
            GROUP BY endpoint
            ORDER BY avg_response DESC
        ''', (cutoff_time,))
        endpoint_performance = cursor.fetchall()
        
        # Error rate
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN status_code >= 400 THEN 1 END) * 100.0 / COUNT(*) as error_rate
            FROM performance_logs
            WHERE timestamp > ?
        ''', (cutoff_time,))
        error_rate = cursor.fetchone()[0] or 0
        
        # System metrics averages
        cursor.execute('''
            SELECT metric_name, AVG(value) as avg_value, MAX(value) as max_value
            FROM system_metrics
            WHERE timestamp > ? AND metric_type = 'system'
            GROUP BY metric_name
        ''', (cutoff_time,))
        system_averages = cursor.fetchall()
        
        conn.close()
        
        return {
            'period_hours': hours,
            'error_rate': round(error_rate, 2),
            'endpoint_performance': [
                {
                    'endpoint': ep[0],
                    'avg_response_time': round(ep[1], 2),
                    'request_count': ep[2]
                }
                for ep in endpoint_performance
            ],
            'system_averages': [
                {
                    'metric': avg[0],
                    'average': round(avg[1], 2),
                    'maximum': round(avg[2], 2)
                }
                for avg in system_averages
            ]
        }


class CacheManager:
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.memory_cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0}
    
    def get(self, key):
        """Get value from cache"""
        # Try Redis first
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    self.cache_stats['hits'] += 1
                    return json.loads(value)
            except Exception:
                pass
        
        # Try memory cache
        if key in self.memory_cache:
            self.cache_stats['hits'] += 1
            return self.memory_cache[key]
        
        self.cache_stats['misses'] += 1
        return None
    
    def set(self, key, value, expire=3600):
        """Set value in cache"""
        # Set in Redis
        if self.redis_client:
            try:
                self.redis_client.setex(key, expire, json.dumps(value))
            except Exception:
                pass
        
        # Set in memory cache
        self.memory_cache[key] = value
        
        # Simple memory cache size limit
        if len(self.memory_cache) > 1000:
            # Remove oldest entries (simplified LRU)
            keys_to_remove = list(self.memory_cache.keys())[:100]
            for k in keys_to_remove:
                del self.memory_cache[k]
    
    def delete(self, key):
        """Delete value from cache"""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception:
                pass
        
        if key in self.memory_cache:
            del self.memory_cache[key]
    
    def clear(self):
        """Clear all cache"""
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception:
                pass
        
        self.memory_cache.clear()
    
    def get_stats(self):
        """Get cache statistics"""
        total = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'hit_rate': round(hit_rate, 2),
            'memory_keys': len(self.memory_cache)
        }