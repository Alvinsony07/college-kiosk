# 🔧 Troubleshooting & FAQ - Admin Module

## 📋 Table of Contents

1. [Common Issues](#common-issues)
2. [Installation Problems](#installation-problems)
3. [Runtime Errors](#runtime-errors)
4. [UI/Display Issues](#uidisplay-issues)
5. [Data & API Issues](#data--api-issues)
6. [Browser Compatibility](#browser-compatibility)
7. [Performance Issues](#performance-issues)
8. [FAQ](#frequently-asked-questions)

---

## 🚨 Common Issues

### Issue 1: Dashboard Shows "Loading..." Forever

**Symptoms:**

- Dashboard cards show loading text
- Charts don't appear
- Tables show "Loading data..."

**Possible Causes:**

1. Flask server not running
2. Wrong API endpoint URL
3. CORS errors
4. No data in database

**Solutions:**

**A. Check Flask Server**

```bash
# Navigate to backend folder
cd backend

# Run server
python app.py

# Should see:
# * Running on http://127.0.0.1:5000
```

**B. Verify API URL**
Open `admin.js` and check line 2:

```javascript
const API_BASE = "http://localhost:5000/api";
```

**C. Check Browser Console**

- Press F12
- Go to Console tab
- Look for error messages
- Common errors:
  - "Failed to fetch" → Server not running
  - "CORS error" → CORS not enabled
  - "404 Not Found" → Wrong endpoint

**D. Enable Demo Mode**

- Toggle "Demo Mode" in header
- Should populate with sample data
- If demo works, backend issue confirmed

---

### Issue 2: Images Not Displaying

**Symptoms:**

- Menu item images show placeholder
- Broken image icons
- 404 errors for images

**Solutions:**

**A. Check Directory Structure**
Ensure this folder exists:

```
frontend/
  static/
    images/
```

**B. Verify Image Path**
Images should be in:

```
frontend/static/images/yourimage.jpg
```

**C. Check app.py Route**
Verify this route exists in app.py:

```python
@app.route('/static/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
```

**D. File Permissions**
Ensure directory has write permissions:

```bash
# Windows
icacls "frontend\static\images" /grant Users:F

# Linux/Mac
chmod 755 frontend/static/images
```

---

### Issue 3: Charts Not Showing

**Symptoms:**

- Empty chart containers
- Charts show for a second then disappear
- Console error: "Chart is not defined"

**Solutions:**

**A. Check CDN Loading**
Open browser Network tab (F12), verify Chart.js loads:

```
chart.umd.min.js - Status: 200 OK
```

**B. Check Script Order**
In `admin.html`, Chart.js must load BEFORE admin.js:

```html
<!-- Chart.js FIRST -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

<!-- admin.js AFTER -->
<script src="admin.js"></script>
```

**C. Canvas Elements Present**
Check if canvas elements exist in HTML:

```html
<canvas id="ordersPerHourChart"></canvas>
<canvas id="orderStatusChart"></canvas>
<canvas id="topSellingChart"></canvas>
<canvas id="revenueTrendChart"></canvas>
```

**D. Enable Demo Mode**
Demo mode generates chart data automatically.

---

### Issue 4: Theme Toggle Not Working

**Symptoms:**

- Clicking theme toggle does nothing
- Theme doesn't persist on reload
- Wrong theme loaded

**Solutions:**

**A. Clear Browser Storage**

```javascript
// Open Console (F12) and run:
localStorage.clear();
location.reload();
```

**B. Check Toggle Event**
Verify this in browser console:

```javascript
document.getElementById("themeToggle").checked;
// Should return true or false
```

**C. Verify CSS Classes**
Dark mode should add this class to body:

```html
<body class="dark-mode"></body>
```

**D. Check CSS Variables**
In `admin.css`, ensure dark mode variables exist:

```css
body.dark-mode {
  --bg-primary: #1e293b;
  --text-primary: #f1f5f9;
  /* etc... */
}
```

---

### Issue 5: Modal Not Opening

**Symptoms:**

- Click "Add Menu Item" → nothing happens
- Click "Edit" → modal doesn't appear
- Console shows Bootstrap errors

**Solutions:**

**A. Check Bootstrap JS**
Verify Bootstrap JS loads in Network tab:

```
bootstrap.bundle.min.js - Status: 200 OK
```

**B. Script Load Order**
Bootstrap must load before admin.js:

```html
<!-- Bootstrap JS FIRST -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>

<!-- admin.js AFTER -->
<script src="admin.js"></script>
```

**C. Modal HTML Present**
Check if modal exists in HTML:

```html
<div class="modal fade" id="addMenuModal" tabindex="-1">
  <!-- Modal content -->
</div>
```

**D. Manual Modal Trigger**
Test in console:

```javascript
new bootstrap.Modal(document.getElementById("addMenuModal")).show();
```

---

### Issue 6: Auto-Refresh Not Working

**Symptoms:**

- Dashboard doesn't update automatically
- Manual refresh works fine
- Setting changes don't take effect

**Solutions:**

**A. Check Toggle Setting**
Ensure auto-refresh is enabled:

```javascript
document.getElementById("autoRefresh").checked;
// Should return true
```

**B. Verify Interval**
Check refresh interval setting:

```javascript
localStorage.getItem("refreshInterval");
// Should return a number (5-60)
```

**C. Check Console for Errors**
Auto-refresh might fail silently if API errors occur.

**D. Test Manually**

```javascript
loadDashboardData(); // Should trigger refresh
```

---

## 🔌 Installation Problems

### Problem: "pip command not found"

**Solution:**

```bash
# Install Python from python.org
# Add Python to PATH during installation
# Or use:
python -m pip install -r requirements.txt
```

---

### Problem: "Module not found: Flask"

**Solution:**

```bash
pip install flask
pip install flask-cors
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

---

### Problem: "Port 5000 already in use"

**Solution:**

**A. Kill Process Using Port**

```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

**B. Change Port**
In `app.py`:

```python
if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Changed to 5001
```

Then update `admin.js`:

```javascript
const API_BASE = "http://localhost:5001/api";
```

---

## 🐛 Runtime Errors

### Error: "CORS policy blocked"

**Cause:** Frontend and backend on different origins

**Solution:**

In `app.py`, ensure CORS is imported and enabled:

```python
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS
```

If issue persists:

```python
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

---

### Error: "Failed to fetch"

**Causes:**

1. Server not running
2. Wrong URL
3. Network issue

**Solutions:**

**A. Verify Server**

```bash
curl http://localhost:5000/api/menu
# Should return JSON data
```

**B. Check API_BASE**
In `admin.js`:

```javascript
console.log(API_BASE); // Should print: http://localhost:5000/api
```

**C. Test in Browser**
Open: `http://localhost:5000/api/menu`
Should see JSON response.

---

### Error: "Cannot read property of undefined"

**Cause:** Trying to access data before it loads

**Solution:**

Use optional chaining:

```javascript
// Instead of:
orders.items.length;

// Use:
orders.items?.length || 0;
```

Or check existence:

```javascript
if (orders && orders.items) {
  // Safe to access
}
```

---

## 🎨 UI/Display Issues

### Issue: Layout Broken on Mobile

**Solutions:**

**A. Check Viewport Meta Tag**
In `admin.html` <head>:

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
```

**B. Test Responsive**

- Open DevTools (F12)
- Click device toggle (Ctrl+Shift+M)
- Select mobile device
- Check layout

**C. Verify Media Queries**
In `admin.css`, ensure breakpoints exist:

```css
@media (max-width: 768px) {
  /* Mobile styles */
}
```

---

### Issue: Text Unreadable in Dark Mode

**Solution:**

Check color contrast in `admin.css`:

```css
body.dark-mode {
  --text-primary: #f1f5f9; /* Light text */
  --bg-primary: #1e293b; /* Dark background */
}
```

Text should have sufficient contrast (4.5:1 ratio minimum).

---

### Issue: Icons Not Showing

**Solution:**

**A. Check Bootstrap Icons CDN**
In `admin.html`:

```html
<link
  rel="stylesheet"
  href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css"
/>
```

**B. Verify Icon Classes**

```html
<i class="bi bi-house"></i>
<!-- Correct -->
<i class="bi-house"></i>
<!-- Wrong - missing 'bi' class -->
```

**C. Test Single Icon**

```html
<i class="bi bi-heart-fill" style="font-size: 50px;"></i>
```

Should show a heart icon.

---

## 📊 Data & API Issues

### Issue: Orders Not Showing Items

**Cause:** Items stored as string, not parsed

**Solution:**

In backend (`app.py`), ensure proper JSON:

```python
# When fetching:
order_data = eval(row[3]) if isinstance(row[3], str) else row[3]
```

In frontend:

```javascript
if (order.items && Array.isArray(order.items)) {
  // Safe to use
}
```

---

### Issue: Stock Not Updating

**Solutions:**

**A. Check API Endpoint**

```javascript
// In admin.js
fetch(`${API_BASE}/menu/${itemId}`, {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ stock: newStock }),
});
```

**B. Verify Backend Route**
In `app.py`:

```python
@app.route('/api/menu/<int:item_id>', methods=['PUT'])
def update_menu_item(item_id):
    # Should handle JSON updates
```

**C. Check Database**

```bash
sqlite3 college.db
SELECT id, name, stock FROM menu;
```

---

### Issue: Users Not Approving

**Solutions:**

**A. Check API Call**

```javascript
fetch(`${API_BASE}/users/approve`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, role: "user" }),
});
```

**B. Verify Backend**

```python
@app.route('/api/users/approve', methods=['POST'])
def approve_user():
    # Should update status to 'approved'
```

**C. Check Database**

```bash
sqlite3 college.db
SELECT email, status FROM users;
```

---

## 🌐 Browser Compatibility

### Chrome/Edge

✅ Fully supported - recommended

### Firefox

✅ Fully supported

### Safari

⚠️ Mostly supported

- May need `-webkit-` prefixes for some CSS
- Check scrollbar styling

### Internet Explorer

❌ Not supported - Use Edge instead

---

## ⚡ Performance Issues

### Issue: Slow Dashboard Loading

**Solutions:**

**A. Reduce Auto-Refresh Interval**

- Go to Settings
- Increase refresh interval to 30-60 seconds

**B. Limit Chart Data**
In `admin.js`, limit data points:

```javascript
const recentOrders = orders.slice(0, 20); // Only last 20
```

**C. Lazy Load Charts**
Only create charts when section is visible.

**D. Optimize Images**

- Compress uploaded images
- Use WebP format
- Set max dimensions

---

### Issue: Memory Leak

**Symptoms:**

- Browser becomes slow over time
- High memory usage
- Tab crashes

**Solutions:**

**A. Destroy Charts Before Recreating**

```javascript
if (charts.ordersPerHour) {
  charts.ordersPerHour.destroy();
}
// Then create new chart
```

**B. Clear Intervals**

```javascript
// Before setting new interval:
if (autoRefreshInterval) {
  clearInterval(autoRefreshInterval);
}
```

**C. Refresh Page**
As temporary fix, refresh browser tab.

---

## ❓ Frequently Asked Questions

### Q1: How do I add a default admin user?

**A:** Default admin already created in `app.py`:

```
Email: kioskadmin@saintgits.org
Password: QAZwsx1!
```

To add another:

```python
# In app.py, after initialize_db():
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
password = hashlib.sha256("YourPassword".encode()).hexdigest()
cursor.execute('''
    INSERT INTO users (name, email, password, role, status)
    VALUES (?, ?, ?, ?, ?)
''', ('Admin2', 'admin2@college.edu', password, 'admin', 'approved'))
conn.commit()
conn.close()
```

---

### Q2: Can I change the college name and branding?

**A:** Yes! Two ways:

**Method 1: Via Settings UI**

1. Go to Settings section
2. Update "College Name" and "Batch Info"
3. Click "Save Settings"

**Method 2: Via HTML**
Edit `admin.html`:

```html
<div class="sidebar-brand">
  <p class="text-muted small mb-0">Your College Name</p>
  <p class="text-muted small">Your Batch Info</p>
</div>
```

---

### Q3: How do I export data to Excel?

**A:** CSV files open in Excel:

1. Go to Reports section
2. Click "Download CSV" for any report
3. Open downloaded .csv file in Excel
4. Excel will format automatically

Or import:

1. Open Excel
2. Data → From Text/CSV
3. Select downloaded file
4. Click Import

---

### Q4: Can I add more categories?

**A:** Yes! Edit both files:

**In admin.html:**

```html
<ul class="nav nav-tabs" id="categoryTabs">
  <li class="nav-item">
    <a class="nav-link" data-category="YourCategory" href="#">Your Category</a>
  </li>
</ul>
```

**In admin.js:**

```javascript
// In add/edit modals:
<option value="YourCategory">Your Category</option>
```

---

### Q5: How do I backup the database?

**A:** Three methods:

**Method 1: Via UI**

1. Go to Reports section
2. Click "Backup Now" on Database Backup card

**Method 2: Manual Copy**

```bash
# Copy college.db file
cp college.db college_backup_2025-10-05.db
```

**Method 3: Automated (Add to app.py)**

```python
import shutil
from datetime import datetime

def backup_database():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    shutil.copy('college.db', f'backup_college_{timestamp}.db')
```

---

### Q6: Demo mode vs real data - which to use?

**A:**

**Use Demo Mode When:**

- ✅ Project presentation/evaluation
- ✅ Feature demonstration
- ✅ Testing UI without affecting data
- ✅ Training new users
- ✅ Screenshots for documentation

**Use Real Data When:**

- ✅ Actual canteen operations
- ✅ Production environment
- ✅ Real user testing
- ✅ Data analysis
- ✅ Performance testing

**Toggle easily:** Just flip the switch in header!

---

### Q7: How to customize colors?

**A:** Edit CSS variables in `admin.css`:

```css
:root {
  --primary: #4f46e5; /* Main color */
  --success: #10b981; /* Success/green */
  --danger: #ef4444; /* Error/red */
  --warning: #f59e0b; /* Warning/yellow */
  --info: #3b82f6; /* Info/blue */
}
```

Changes apply instantly after refresh!

---

### Q8: Can I add more charts?

**A:** Yes! Follow this pattern:

**1. Add canvas in HTML:**

```html
<canvas id="yourChartName"></canvas>
```

**2. Create chart in JS:**

```javascript
function createYourChart(data) {
  const ctx = document.getElementById("yourChartName");
  const chart = new Chart(ctx, {
    type: "bar", // or 'line', 'pie', etc.
    data: {
      labels: ["Label1", "Label2"],
      datasets: [
        {
          label: "Your Data",
          data: [10, 20],
        },
      ],
    },
  });
}
```

---

### Q9: How to add email notifications?

**A:** Backend implementation needed:

```python
# Install: pip install flask-mail

from flask_mail import Mail, Message

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'your@email.com'
app.config['MAIL_PASSWORD'] = 'yourpassword'

mail = Mail(app)

def send_approval_email(user_email):
    msg = Message('Account Approved',
                  sender='canteen@college.edu',
                  recipients=[user_email])
    msg.body = 'Your account has been approved!'
    mail.send(msg)
```

---

### Q10: Is this production-ready?

**A:** For academic project: **Yes! ✅**

For production deployment, consider:

- [ ] Add authentication middleware
- [ ] Implement JWT tokens
- [ ] Add rate limiting
- [ ] Set up HTTPS
- [ ] Use production database (PostgreSQL)
- [ ] Add logging
- [ ] Set up monitoring
- [ ] Configure backups
- [ ] Load testing
- [ ] Security audit

Current version is **perfect for evaluation** and **college use**!

---

## 🆘 Still Having Issues?

### Debug Checklist:

1. ✅ Flask server running?
2. ✅ Browser console clear of errors?
3. ✅ API endpoints responding?
4. ✅ Database file exists?
5. ✅ All CDN resources loaded?
6. ✅ Correct file paths?
7. ✅ Internet connection working?

### Get More Help:

**Check Console (F12):**

- Console tab for JS errors
- Network tab for failed requests
- Elements tab for HTML structure

**Test APIs Directly:**

```bash
curl http://localhost:5000/api/menu
curl http://localhost:5000/api/users
curl http://localhost:5000/api/orders
```

**Enable Verbose Logging:**
In `admin.js`, add:

```javascript
console.log("API Response:", data);
console.log("Current State:", state);
```

---

## ✅ Success Indicators

Your admin module is working correctly if:

1. ✅ Dashboard loads with metrics
2. ✅ Charts display data
3. ✅ Users table shows users
4. ✅ Menu items display with images
5. ✅ Orders table populated
6. ✅ Theme toggle works
7. ✅ Demo mode loads sample data
8. ✅ Reports download
9. ✅ No console errors
10. ✅ Responsive on mobile

---

## 🎓 Best Practices

### Development:

- Always check console for errors
- Test on multiple browsers
- Use demo mode for testing
- Keep backups of database
- Comment your code changes

### Evaluation Day:

- Enable demo mode
- Test all features beforehand
- Have backup plan if internet fails
- Know your code well
- Be ready to explain design decisions

### Maintenance:

- Regular database backups
- Monitor error logs
- Update dependencies
- Test after changes
- Document customizations

---

## 🎉 You've Got This!

Most issues have simple solutions. Follow this guide and you'll be running smoothly!

**Remember:**

- 🔍 Check console first
- 🔄 Try refresh
- 🎭 Test with demo mode
- 📖 Read error messages
- ✅ Follow checklist

---

_Last Updated: October 5, 2025_  
_Admin Module v1.0.0_

**Need more help?** Check:

- ADMIN_MODULE_README.md
- QUICK_START.md
- FEATURES_CHECKLIST.md

**Good luck! 🚀**
