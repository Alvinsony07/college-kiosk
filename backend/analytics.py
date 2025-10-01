"""
Advanced Analytics and Reporting System
Features: Custom reports, PDF generation, predictive analytics, scheduled reports
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import sqlite3
import json
import base64
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import os
from collections import defaultdict
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
import warnings
warnings.filterwarnings('ignore')

class AdvancedAnalytics:
    def __init__(self, db_path):
        self.db_path = db_path
        plt.style.use('seaborn-v0_8-darkgrid')
        
    def get_data_frame(self, query, params=None):
        """Execute SQL query and return pandas DataFrame"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def generate_comprehensive_analytics(self, date_range=30):
        """Generate comprehensive analytics data"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range)
        
        analytics = {
            'summary': self.get_business_summary(start_date, end_date),
            'sales_trends': self.get_sales_trends(start_date, end_date),
            'customer_insights': self.get_customer_insights(start_date, end_date),
            'inventory_analysis': self.get_inventory_analysis(),
            'financial_metrics': self.get_financial_metrics(start_date, end_date),
            'predictive_analytics': self.get_predictive_analytics(),
            'performance_metrics': self.get_performance_metrics(start_date, end_date)
        }
        
        return analytics
    
    def get_business_summary(self, start_date, end_date):
        """Get business summary metrics"""
        # Revenue metrics
        revenue_query = """
            SELECT 
                COUNT(*) as total_orders,
                SUM(total_price) as total_revenue,
                AVG(total_price) as avg_order_value,
                DATE(created_at) as order_date
            FROM orders 
            WHERE created_at BETWEEN ? AND ?
            GROUP BY DATE(created_at)
            ORDER BY order_date
        """
        
        revenue_df = self.get_data_frame(revenue_query, [start_date.isoformat(), end_date.isoformat()])
        
        # Customer metrics
        customer_query = """
            SELECT 
                COUNT(DISTINCT customer_email) as unique_customers,
                COUNT(*) as total_orders,
                DATE(created_at) as order_date
            FROM orders 
            WHERE created_at BETWEEN ? AND ?
            GROUP BY DATE(created_at)
        """
        
        customer_df = self.get_data_frame(customer_query, [start_date.isoformat(), end_date.isoformat()])
        
        return {
            'total_revenue': float(revenue_df['total_revenue'].sum()) if not revenue_df.empty else 0,
            'total_orders': int(revenue_df['total_orders'].sum()) if not revenue_df.empty else 0,
            'avg_order_value': float(revenue_df['avg_order_value'].mean()) if not revenue_df.empty else 0,
            'unique_customers': int(customer_df['unique_customers'].sum()) if not customer_df.empty else 0,
            'daily_revenue': revenue_df.to_dict('records') if not revenue_df.empty else [],
            'customer_acquisition': customer_df.to_dict('records') if not customer_df.empty else []
        }
    
    def get_sales_trends(self, start_date, end_date):
        """Analyze sales trends"""
        # Hourly sales pattern
        hourly_query = """
            SELECT 
                strftime('%H', created_at) as hour,
                COUNT(*) as order_count,
                SUM(total_price) as revenue
            FROM orders 
            WHERE created_at BETWEEN ? AND ?
            GROUP BY strftime('%H', created_at)
            ORDER BY hour
        """
        
        hourly_df = self.get_data_frame(hourly_query, [start_date.isoformat(), end_date.isoformat()])
        
        # Weekly trends
        weekly_query = """
            SELECT 
                strftime('%w', created_at) as day_of_week,
                COUNT(*) as order_count,
                SUM(total_price) as revenue
            FROM orders 
            WHERE created_at BETWEEN ? AND ?
            GROUP BY strftime('%w', created_at)
        """
        
        weekly_df = self.get_data_frame(weekly_query, [start_date.isoformat(), end_date.isoformat()])
        
        # Category performance
        category_query = """
            SELECT 
                m.category,
                COUNT(*) as orders,
                SUM(json_extract(o.items, '$[*].qty')) as items_sold,
                SUM(m.price * json_extract(o.items, '$[*].qty')) as revenue
            FROM orders o
            JOIN menu m ON json_extract(o.items, '$[*].id') = m.id
            WHERE o.created_at BETWEEN ? AND ?
            GROUP BY m.category
            ORDER BY revenue DESC
        """
        
        # This is a simplified version - in practice, you'd need to properly parse the JSON items
        category_df = pd.DataFrame()  # Placeholder
        
        return {
            'hourly_pattern': hourly_df.to_dict('records') if not hourly_df.empty else [],
            'weekly_pattern': weekly_df.to_dict('records') if not weekly_df.empty else [],
            'category_performance': category_df.to_dict('records') if not category_df.empty else []
        }
    
    def get_customer_insights(self, start_date, end_date):
        """Analyze customer behavior"""
        # Customer frequency
        frequency_query = """
            SELECT 
                customer_email,
                COUNT(*) as order_frequency,
                SUM(total_price) as lifetime_value,
                MIN(created_at) as first_order,
                MAX(created_at) as last_order
            FROM orders 
            WHERE created_at BETWEEN ? AND ?
            GROUP BY customer_email
        """
        
        frequency_df = self.get_data_frame(frequency_query, [start_date.isoformat(), end_date.isoformat()])
        
        if frequency_df.empty:
            return {'customer_segments': [], 'retention_metrics': {}}
        
        # Customer segmentation
        frequency_df['segment'] = pd.cut(
            frequency_df['order_frequency'], 
            bins=[0, 1, 3, 5, float('inf')], 
            labels=['One-time', 'Occasional', 'Regular', 'VIP']
        )
        
        segments = frequency_df.groupby('segment').agg({
            'customer_email': 'count',
            'lifetime_value': 'mean',
            'order_frequency': 'mean'
        }).reset_index()
        
        # Retention analysis
        retention_metrics = {
            'repeat_customer_rate': len(frequency_df[frequency_df['order_frequency'] > 1]) / len(frequency_df) * 100,
            'avg_lifetime_value': float(frequency_df['lifetime_value'].mean()),
            'avg_order_frequency': float(frequency_df['order_frequency'].mean())
        }
        
        return {
            'customer_segments': segments.to_dict('records'),
            'retention_metrics': retention_metrics
        }
    
    def get_inventory_analysis(self):
        """Analyze inventory performance"""
        inventory_query = """
            SELECT 
                id, name, category, price, stock, available,
                CASE 
                    WHEN stock = 0 THEN 'Out of Stock'
                    WHEN stock <= 5 THEN 'Low Stock'
                    WHEN stock <= 20 THEN 'Normal'
                    ELSE 'Well Stocked'
                END as stock_status
            FROM menu
        """
        
        inventory_df = self.get_data_frame(inventory_query)
        
        if inventory_df.empty:
            return {'stock_levels': [], 'stock_alerts': []}
        
        # Stock analysis
        stock_summary = inventory_df['stock_status'].value_counts().to_dict()
        
        # Items needing attention
        alerts = inventory_df[inventory_df['stock'] <= 5].to_dict('records')
        
        return {
            'stock_levels': stock_summary,
            'stock_alerts': alerts,
            'category_stock': inventory_df.groupby('category')['stock'].sum().to_dict()
        }
    
    def get_financial_metrics(self, start_date, end_date):
        """Calculate financial KPIs"""
        # Revenue by payment method, profit margins, etc.
        financial_query = """
            SELECT 
                DATE(created_at) as date,
                SUM(total_price) as daily_revenue,
                COUNT(*) as daily_orders,
                AVG(total_price) as avg_order_value
            FROM orders 
            WHERE created_at BETWEEN ? AND ?
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        
        financial_df = self.get_data_frame(financial_query, [start_date.isoformat(), end_date.isoformat()])
        
        if financial_df.empty:
            return {'growth_rate': 0, 'revenue_trend': []}
        
        # Calculate growth rate
        if len(financial_df) > 1:
            recent_avg = financial_df.tail(7)['daily_revenue'].mean()
            previous_avg = financial_df.head(7)['daily_revenue'].mean()
            growth_rate = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
        else:
            growth_rate = 0
        
        return {
            'growth_rate': float(growth_rate),
            'revenue_trend': financial_df.to_dict('records'),
            'total_revenue': float(financial_df['daily_revenue'].sum()),
            'avg_daily_revenue': float(financial_df['daily_revenue'].mean())
        }
    
    def get_predictive_analytics(self):
        """Generate predictive insights"""
        # Get historical data for prediction
        prediction_query = """
            SELECT 
                DATE(created_at) as date,
                SUM(total_price) as revenue,
                COUNT(*) as orders
            FROM orders 
            WHERE created_at >= date('now', '-90 days')
            GROUP BY DATE(created_at)
            ORDER BY date
        """
        
        pred_df = self.get_data_frame(prediction_query)
        
        if len(pred_df) < 10:  # Need minimum data for prediction
            return {
                'revenue_forecast': [],
                'demand_forecast': [],
                'confidence': 'low'
            }
        
        # Simple linear regression for revenue prediction
        pred_df['date_numeric'] = pd.to_datetime(pred_df['date']).map(pd.Timestamp.timestamp)
        
        X = pred_df['date_numeric'].values.reshape(-1, 1)
        y_revenue = pred_df['revenue'].values
        y_orders = pred_df['orders'].values
        
        # Revenue prediction
        revenue_model = LinearRegression()
        revenue_model.fit(X, y_revenue)
        
        # Order prediction
        order_model = LinearRegression()
        order_model.fit(X, y_orders)
        
        # Predict next 30 days
        future_dates = pd.date_range(start=pred_df['date'].max(), periods=31)[1:]
        future_numeric = future_dates.map(pd.Timestamp.timestamp).values.reshape(-1, 1)
        
        revenue_pred = revenue_model.predict(future_numeric)
        order_pred = order_model.predict(future_numeric)
        
        # Calculate R² score for confidence
        from sklearn.metrics import r2_score
        revenue_r2 = r2_score(y_revenue, revenue_model.predict(X))
        
        confidence = 'high' if revenue_r2 > 0.7 else 'medium' if revenue_r2 > 0.4 else 'low'
        
        forecast_data = {
            'revenue_forecast': [
                {
                    'date': date.strftime('%Y-%m-%d'),
                    'predicted_revenue': float(rev),
                    'predicted_orders': int(ord)
                }
                for date, rev, ord in zip(future_dates, revenue_pred, order_pred)
            ],
            'confidence': confidence,
            'model_accuracy': float(revenue_r2)
        }
        
        return forecast_data
    
    def get_performance_metrics(self, start_date, end_date):
        """Calculate performance KPIs"""
        # Menu item performance
        performance_query = """
            SELECT 
                m.name,
                m.category,
                m.price,
                m.stock,
                COUNT(o.id) as times_ordered
            FROM menu m
            LEFT JOIN orders o ON 1=1  -- This would need proper JSON parsing in real implementation
            GROUP BY m.id, m.name, m.category, m.price, m.stock
            ORDER BY times_ordered DESC
        """
        
        # This is simplified - in practice, you'd need to properly parse the JSON items in orders
        performance_df = self.get_data_frame("SELECT * FROM menu LIMIT 10")  # Placeholder
        
        return {
            'top_performers': performance_df.to_dict('records') if not performance_df.empty else [],
            'underperformers': []
        }
    
    def create_chart(self, data, chart_type, title, x_label, y_label, figsize=(10, 6)):
        """Create a chart and return as base64 encoded image"""
        plt.figure(figsize=figsize)
        
        if chart_type == 'line':
            plt.plot(data['x'], data['y'])
        elif chart_type == 'bar':
            plt.bar(data['x'], data['y'])
        elif chart_type == 'pie':
            plt.pie(data['values'], labels=data['labels'], autopct='%1.1f%%')
        
        plt.title(title)
        if chart_type != 'pie':
            plt.xlabel(x_label)
            plt.ylabel(y_label)
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f"data:image/png;base64,{image_base64}"
    
    def generate_pdf_report(self, analytics_data, report_title="Analytics Report"):
        """Generate PDF report from analytics data"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#FF5722')
        )
        story.append(Paragraph(report_title, title_style))
        story.append(Spacer(1, 12))
        
        # Summary section
        story.append(Paragraph("Executive Summary", styles['Heading2']))
        summary = analytics_data.get('summary', {})
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Revenue', f"₹{summary.get('total_revenue', 0):,.2f}"],
            ['Total Orders', f"{summary.get('total_orders', 0):,}"],
            ['Average Order Value', f"₹{summary.get('avg_order_value', 0):.2f}"],
            ['Unique Customers', f"{summary.get('unique_customers', 0):,}"]
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF5722')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 20))
        
        # Financial metrics
        if 'financial_metrics' in analytics_data:
            story.append(Paragraph("Financial Performance", styles['Heading2']))
            financial = analytics_data['financial_metrics']
            
            financial_text = f"""
            <para>
            <b>Growth Rate:</b> {financial.get('growth_rate', 0):.1f}%<br/>
            <b>Average Daily Revenue:</b> ₹{financial.get('avg_daily_revenue', 0):,.2f}<br/>
            <b>Total Revenue (Period):</b> ₹{financial.get('total_revenue', 0):,.2f}
            </para>
            """
            story.append(Paragraph(financial_text, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Customer insights
        if 'customer_insights' in analytics_data:
            story.append(Paragraph("Customer Analysis", styles['Heading2']))
            customer = analytics_data['customer_insights']
            retention = customer.get('retention_metrics', {})
            
            customer_text = f"""
            <para>
            <b>Repeat Customer Rate:</b> {retention.get('repeat_customer_rate', 0):.1f}%<br/>
            <b>Average Lifetime Value:</b> ₹{retention.get('avg_lifetime_value', 0):,.2f}<br/>
            <b>Average Order Frequency:</b> {retention.get('avg_order_frequency', 0):.1f}
            </para>
            """
            story.append(Paragraph(customer_text, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_custom_report(self, report_config):
        """Generate custom report based on configuration"""
        report_type = report_config.get('type', 'summary')
        date_range = report_config.get('date_range', 30)
        filters = report_config.get('filters', {})
        
        # Build query based on configuration
        if report_type == 'sales':
            return self.generate_sales_report(date_range, filters)
        elif report_type == 'inventory':
            return self.generate_inventory_report(filters)
        elif report_type == 'customer':
            return self.generate_customer_report(date_range, filters)
        else:
            return self.generate_comprehensive_analytics(date_range)
    
    def generate_sales_report(self, date_range, filters):
        """Generate detailed sales report"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range)
        
        # Base query
        query = """
            SELECT 
                o.id,
                o.customer_name,
                o.customer_email,
                o.total_price,
                o.status,
                o.created_at,
                o.items
            FROM orders o
            WHERE o.created_at BETWEEN ? AND ?
        """
        
        params = [start_date.isoformat(), end_date.isoformat()]
        
        # Apply filters
        if filters.get('status'):
            query += " AND o.status = ?"
            params.append(filters['status'])
        
        if filters.get('min_amount'):
            query += " AND o.total_price >= ?"
            params.append(filters['min_amount'])
        
        query += " ORDER BY o.created_at DESC"
        
        sales_df = self.get_data_frame(query, params)
        
        return {
            'data': sales_df.to_dict('records') if not sales_df.empty else [],
            'summary': {
                'total_sales': float(sales_df['total_price'].sum()) if not sales_df.empty else 0,
                'order_count': len(sales_df),
                'avg_order_value': float(sales_df['total_price'].mean()) if not sales_df.empty else 0
            }
        }
    
    def generate_inventory_report(self, filters):
        """Generate inventory report"""
        query = "SELECT * FROM menu"
        params = []
        
        if filters.get('category'):
            query += " WHERE category = ?"
            params.append(filters['category'])
        
        if filters.get('low_stock_only'):
            query += " WHERE stock <= 5" if not params else " AND stock <= 5"
        
        inventory_df = self.get_data_frame(query, params)
        
        return {
            'data': inventory_df.to_dict('records') if not inventory_df.empty else [],
            'summary': {
                'total_items': len(inventory_df),
                'low_stock_items': len(inventory_df[inventory_df['stock'] <= 5]) if not inventory_df.empty else 0,
                'out_of_stock_items': len(inventory_df[inventory_df['stock'] == 0]) if not inventory_df.empty else 0
            }
        }
    
    def generate_customer_report(self, date_range, filters):
        """Generate customer analysis report"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=date_range)
        
        query = """
            SELECT 
                customer_email,
                customer_name,
                COUNT(*) as order_count,
                SUM(total_price) as total_spent,
                AVG(total_price) as avg_order_value,
                MIN(created_at) as first_order,
                MAX(created_at) as last_order
            FROM orders
            WHERE created_at BETWEEN ? AND ?
            GROUP BY customer_email, customer_name
        """
        
        params = [start_date.isoformat(), end_date.isoformat()]
        
        if filters.get('min_orders'):
            query += " HAVING order_count >= ?"
            params.append(filters['min_orders'])
        
        query += " ORDER BY total_spent DESC"
        
        customer_df = self.get_data_frame(query, params)
        
        return {
            'data': customer_df.to_dict('records') if not customer_df.empty else [],
            'summary': {
                'total_customers': len(customer_df),
                'avg_customer_value': float(customer_df['total_spent'].mean()) if not customer_df.empty else 0,
                'top_customer_value': float(customer_df['total_spent'].max()) if not customer_df.empty else 0
            }
        }

class ReportScheduler:
    def __init__(self, db_path):
        self.db_path = db_path
        self.analytics = AdvancedAnalytics(db_path)
        self.init_scheduler_tables()
    
    def init_scheduler_tables(self):
        """Initialize report scheduler tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scheduled_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                report_type TEXT NOT NULL,
                schedule_frequency TEXT NOT NULL, -- daily, weekly, monthly
                schedule_time TEXT, -- HH:MM format
                recipients TEXT, -- JSON array of email addresses
                report_config TEXT, -- JSON configuration
                is_active INTEGER DEFAULT 1,
                last_run TEXT,
                next_run TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheduled_report_id INTEGER,
                generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                status TEXT, -- success, failed
                file_path TEXT,
                recipients TEXT,
                error_message TEXT,
                FOREIGN KEY (scheduled_report_id) REFERENCES scheduled_reports (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_scheduled_report(self, name, report_type, frequency, schedule_time, recipients, config):
        """Create a new scheduled report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Calculate next run time
        from datetime import datetime, time
        next_run = self.calculate_next_run(frequency, schedule_time)
        
        cursor.execute('''
            INSERT INTO scheduled_reports 
            (name, report_type, schedule_frequency, schedule_time, recipients, report_config, next_run)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, report_type, frequency, schedule_time,
            json.dumps(recipients), json.dumps(config), next_run.isoformat()
        ))
        
        conn.commit()
        report_id = cursor.lastrowid
        conn.close()
        
        return report_id
    
    def calculate_next_run(self, frequency, schedule_time):
        """Calculate next run time based on frequency and time"""
        from datetime import datetime, time, timedelta
        
        now = datetime.now()
        hour, minute = map(int, schedule_time.split(':'))
        
        if frequency == 'daily':
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
        elif frequency == 'weekly':
            # Run every Monday at specified time
            days_ahead = 0 - now.weekday()  # Monday is 0
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_run = (now + timedelta(days=days_ahead)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        elif frequency == 'monthly':
            # Run on the 1st of each month
            if now.day == 1 and now.hour < hour:
                next_run = now.replace(day=1, hour=hour, minute=minute, second=0, microsecond=0)
            else:
                # Next month
                if now.month == 12:
                    next_run = now.replace(year=now.year + 1, month=1, day=1, hour=hour, minute=minute, second=0, microsecond=0)
                else:
                    next_run = now.replace(month=now.month + 1, day=1, hour=hour, minute=minute, second=0, microsecond=0)
        
        return next_run
    
    def get_due_reports(self):
        """Get reports that are due to run"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute('''
            SELECT * FROM scheduled_reports 
            WHERE is_active = 1 AND next_run <= ?
        ''', (now,))
        
        reports = cursor.fetchall()
        conn.close()
        
        return reports
    
    def run_scheduled_report(self, report_id):
        """Run a scheduled report"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM scheduled_reports WHERE id = ?", (report_id,))
        report = cursor.fetchone()
        
        if not report:
            return False
        
        try:
            # Generate report
            config = json.loads(report[7]) if report[7] else {}
            report_data = self.analytics.generate_custom_report(config)
            
            # Generate PDF
            pdf_buffer = self.analytics.generate_pdf_report(report_data, report[1])
            
            # Save PDF file
            reports_dir = os.path.join(os.path.dirname(self.db_path), 'reports')
            os.makedirs(reports_dir, exist_ok=True)
            
            filename = f"report_{report_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            filepath = os.path.join(reports_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(pdf_buffer.getvalue())
            
            # Update last run and calculate next run
            next_run = self.calculate_next_run(report[3], report[4])
            cursor.execute('''
                UPDATE scheduled_reports 
                SET last_run = CURRENT_TIMESTAMP, next_run = ?
                WHERE id = ?
            ''', (next_run.isoformat(), report_id))
            
            # Log success
            cursor.execute('''
                INSERT INTO report_history 
                (scheduled_report_id, status, file_path, recipients)
                VALUES (?, ?, ?, ?)
            ''', (report_id, 'success', filepath, report[5]))
            
            conn.commit()
            return True
            
        except Exception as e:
            # Log error
            cursor.execute('''
                INSERT INTO report_history 
                (scheduled_report_id, status, error_message)
                VALUES (?, ?, ?)
            ''', (report_id, 'failed', str(e)))
            conn.commit()
            return False
        
        finally:
            conn.close()