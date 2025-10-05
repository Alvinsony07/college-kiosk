# ✅ Testing Guide - Admin Module

## 🎯 Complete Testing Checklist

This guide helps you verify that every feature of the admin module is working perfectly before your evaluation.

---

## 🚀 Pre-Testing Setup

### Step 1: Start the Server

```bash
cd backend
python app.py
```

✅ Verify you see: `* Running on http://127.0.0.1:5000`

### Step 2: Open Admin Dashboard

Open browser: `http://localhost:5000/admin`

✅ Dashboard should load without errors

### Step 3: Open Developer Tools

Press `F12` → Go to Console tab

✅ No red error messages

---

## 📊 Dashboard Module Testing

### Test 1: Summary Cards Display

**Expected:**

- 4 cards visible (Orders, Revenue, Users, Stock)
- Numbers displayed (even if 0)
- Icons showing
- Hover effects working

**How to Test:**

1. Observe top 4 cards
2. Hover over each card
3. Check for animation

✅ Pass Criteria: All cards visible with hover effects

---

### Test 2: Charts Rendering

**Expected:**

- 4 charts visible
- Data populated (or empty if no data)
- Interactive tooltips on hover
- Responsive sizing

**How to Test:**

1. Scroll to charts section
2. Hover over chart elements
3. Check tooltips appear

✅ Pass Criteria: All 4 charts display without errors

---

### Test 3: Live Feed Updates

**Expected:**

- Recent Orders section shows orders
- Live Alerts section shows alerts
- Styled activity items
- Timestamps visible

**How to Test:**

1. Check "Recent Orders" feed
2. Check "Live Alerts" section
3. Verify styling

✅ Pass Criteria: Both feeds display correctly

---

### Test 4: Smart Insights

**Expected:**

- Insight cards with gradient background
- Multiple insight items
- Icons and text
- Data-driven content

**How to Test:**

1. Scroll to Smart Insights section
2. Read insight messages
3. Verify gradient background

✅ Pass Criteria: Insights display with professional styling

---

## 👥 User Management Testing

### Test 5: User Table Display

**Expected:**

- Table loads with users
- Email, Role, Status columns visible
- Action buttons present
- Badges color-coded

**How to Test:**

1. Click "User Management" in sidebar
2. Wait for table to load
3. Verify all columns present

✅ Pass Criteria: User table displays with data

---

### Test 6: Search Functionality

**Expected:**

- Search box filters users in real-time
- Results update as you type
- Case-insensitive
- Works for email

**How to Test:**

1. Type in search box
2. Observe table filtering
3. Clear search
4. Table resets

✅ Pass Criteria: Search filters users instantly

---

### Test 7: Role Filter

**Expected:**

- Dropdown shows role options
- Selecting role filters table
- "All Roles" shows everyone
- Works with search

**How to Test:**

1. Select "Admin" from role filter
2. Only admins shown
3. Select "All Roles"
4. All users shown

✅ Pass Criteria: Role filter works correctly

---

### Test 8: Status Filter

**Expected:**

- Dropdown shows status options
- Filters by approved/pending
- Works with other filters
- Updates instantly

**How to Test:**

1. Select "Pending" from status filter
2. Only pending users shown
3. Select "All Status"
4. All users shown

✅ Pass Criteria: Status filter works correctly

---

### Test 9: Approve User

**Expected:**

- "Approve" button on pending users
- Click triggers confirmation
- Success notification appears
- Table updates
- Badge changes to "Approved"

**How to Test:**

1. Find pending user
2. Click "Approve" button
3. Check for toast notification
4. Verify badge changed

✅ Pass Criteria: User approved successfully

---

### Test 10: Edit User Role

**Expected:**

- "Edit" button opens modal
- Email shown (readonly)
- Role dropdown works
- Update saves changes
- Modal closes
- Table refreshes

**How to Test:**

1. Click "Edit" on any user
2. Modal opens
3. Change role
4. Click "Update Role"
5. Success notification
6. Modal closes

✅ Pass Criteria: Role updated successfully

---

### Test 11: Delete User

**Expected:**

- "Delete" button shows confirmation
- SweetAlert modal appears
- Cancel works
- Confirm deletes user
- Success notification
- Table refreshes

**How to Test:**

1. Click "Delete" on test user
2. SweetAlert appears
3. Click "Cancel" (nothing happens)
4. Click "Delete" again
5. Click "Yes, delete"
6. User removed

✅ Pass Criteria: User deleted with confirmation

---

## 🍔 Menu Management Testing

### Test 12: Menu Grid Display

**Expected:**

- Items shown in grid layout
- Images display
- Names and prices visible
- Stock badges showing
- Category labels
- Action buttons present

**How to Test:**

1. Click "Menu Management"
2. Observe grid of items
3. Check all information visible

✅ Pass Criteria: Menu items display in attractive grid

---

### Test 13: Category Tabs

**Expected:**

- Tabs for All, Snacks, Meals, Drinks, Desserts
- Active tab highlighted
- Clicking filters items
- Smooth transition
- Item count updates

**How to Test:**

1. Click each category tab
2. Items filter accordingly
3. Active tab highlighted
4. Click "All" to reset

✅ Pass Criteria: Category filtering works smoothly

---

### Test 14: Add Menu Item

**Expected:**

- "Add Menu Item" button opens modal
- Form fields present
- Image upload with preview
- Form validation works
- Success notification
- New item appears in grid

**How to Test:**

1. Click "Add Menu Item"
2. Fill all fields:
   - Name: "Test Burger"
   - Price: 99
   - Category: Snacks
   - Stock: 20
   - Upload any image
3. Check image preview appears
4. Click "Add Item"
5. Success toast shows
6. Modal closes
7. New item in grid

✅ Pass Criteria: Menu item added successfully

---

### Test 15: Image Preview

**Expected:**

- Upload image
- Preview appears below
- Correct image shown
- Reasonable size
- Works in both add and edit modals

**How to Test:**

1. Open add menu modal
2. Select image file
3. Preview appears instantly
4. Try different image
5. Preview updates

✅ Pass Criteria: Image preview works correctly

---

### Test 16: Edit Menu Item

**Expected:**

- "Edit" button opens modal
- Form pre-filled with current data
- Can change any field
- Image upload optional
- Update works
- Grid refreshes

**How to Test:**

1. Click "Edit" on an item
2. Modal opens with data
3. Change price to 150
4. Click "Update Item"
5. Success notification
6. Price updated in grid

✅ Pass Criteria: Menu item updated successfully

---

### Test 17: Delete Menu Item

**Expected:**

- "Delete" button shows confirmation
- SweetAlert appears
- Cancel works
- Confirm deletes item
- Success notification
- Grid refreshes

**How to Test:**

1. Click delete on test item
2. Confirmation appears
3. Click "Yes, delete"
4. Item removed from grid

✅ Pass Criteria: Menu item deleted successfully

---

### Test 18: Quick Restock (+10)

**Expected:**

- "+10" button visible
- Click adds 10 to stock
- Success notification
- Stock number updates
- Dashboard updates

**How to Test:**

1. Note current stock (e.g., 5)
2. Click "+10" button
3. Toast: "Stock updated: +10 items"
4. Stock now shows 15

✅ Pass Criteria: Stock increases by 10 instantly

---

### Test 19: Stock Indicators

**Expected:**

- 🟢 Green for stock > 10
- 🟡 Yellow for stock 1-10
- 🔴 Red for stock = 0
- Color badge on item card
- Correct text displayed

**How to Test:**

1. Find item with different stock levels
2. Verify colors match stock:
   - In Stock (green)
   - Low Stock (yellow)
   - Out of Stock (red)

✅ Pass Criteria: Stock indicators show correct colors

---

## 📦 Inventory Management Testing

### Test 20: Stock Summary Cards

**Expected:**

- 3 cards (Out of Stock, Low Stock, In Stock)
- Correct counts
- Color-coded borders
- Updates with data

**How to Test:**

1. Click "Inventory & Stock"
2. View 3 summary cards at top
3. Verify counts match table below

✅ Pass Criteria: Summary cards show correct counts

---

### Test 21: Inventory Table

**Expected:**

- All menu items listed
- Columns: Item, Category, Stock, Status, Price, Actions
- Stock status badges
- Sortable (if implemented)
- Action buttons work

**How to Test:**

1. Check all columns present
2. Verify status badges match stock levels
3. Test action buttons

✅ Pass Criteria: Inventory table complete and accurate

---

### Test 22: Export Stock Report

**Expected:**

- "Export CSV" button works
- CSV file downloads
- Contains all inventory data
- Proper format
- Opens in Excel

**How to Test:**

1. Click "Export CSV" button
2. File downloads automatically
3. Open file
4. Verify data present

✅ Pass Criteria: CSV file downloads with inventory data

---

## 📋 Orders Management Testing

### Test 23: Orders Table Display

**Expected:**

- All orders listed
- Columns complete
- Status badges color-coded
- OTP codes visible
- Customer info shown

**How to Test:**

1. Click "Orders" in sidebar
2. Table loads with orders
3. All columns visible
4. Status badges colored

✅ Pass Criteria: Orders table displays correctly

---

### Test 24: Order Status Filter

**Expected:**

- Dropdown has all status options
- Selecting status filters orders
- "All Orders" shows everything
- Updates instantly

**How to Test:**

1. Select "Preparing" from filter
2. Only preparing orders shown
3. Select "All Orders"
4. All orders visible

✅ Pass Criteria: Order status filter works

---

### Test 25: View Order Details

**Expected:**

- Eye icon opens modal
- Shows complete order info
- Customer details
- Items list
- Total and OTP
- Modal styled correctly

**How to Test:**

1. Click eye icon on an order
2. Modal opens
3. All information displayed
4. Click "Close"
5. Modal closes

✅ Pass Criteria: Order details modal works

---

## 💰 Revenue & Analytics Testing

### Test 26: Revenue Summary Cards

**Expected:**

- 4 metric cards
- Total Revenue
- Avg Order Value
- Total Orders Count
- Peak Hour
- Values calculated correctly

**How to Test:**

1. Click "Revenue & Analytics"
2. View 4 summary cards
3. Verify numbers make sense

✅ Pass Criteria: Revenue metrics display

---

### Test 27: Daily Revenue Chart

**Expected:**

- Bar chart visible
- Shows last 7 days
- Bars colored correctly
- Tooltips work on hover
- Responsive

**How to Test:**

1. Observe revenue chart
2. Hover over bars
3. Tooltip shows value

✅ Pass Criteria: Revenue chart displays and is interactive

---

### Test 28: Category Revenue Chart

**Expected:**

- Pie chart visible
- Shows category breakdown
- Legend present
- Colors distinct
- Tooltips work

**How to Test:**

1. View category pie chart
2. Hover over segments
3. Check legend

✅ Pass Criteria: Category chart works

---

### Test 29: Top Items Table

**Expected:**

- Table shows top 10 items
- Rank, Name, Category, Qty, Revenue
- Sorted by quantity
- Data accurate

**How to Test:**

1. Scroll to top items table
2. Verify sorting (highest first)
3. Check all columns

✅ Pass Criteria: Top items table accurate

---

### Test 30: Date Range Filter

**Expected:**

- Start date picker works
- End date picker works
- Apply button filters data
- Charts update
- Metrics recalculate

**How to Test:**

1. Select start date
2. Select end date
3. Click "Apply Filter"
4. Data updates

✅ Pass Criteria: Date filter works (even if not fully implemented)

---

## 📊 Reports Testing

### Test 31: Sales Report Download

**Expected:**

- "Download CSV" button
- File downloads
- Contains order data
- Proper headers
- Opens in Excel

**How to Test:**

1. Click "Reports" in sidebar
2. Click "Download CSV" on Sales Report
3. File downloads
4. Open and verify

✅ Pass Criteria: Sales report downloads

---

### Test 32: Stock Report Download

**Expected:**

- Downloads inventory CSV
- All items included
- Stock levels shown
- Categories included

**How to Test:**

1. Click "Download CSV" on Stock Report
2. File downloads
3. Open and verify data

✅ Pass Criteria: Stock report downloads

---

### Test 33: User Activity Report

**Expected:**

- Downloads user CSV
- All users included
- Roles and status shown

**How to Test:**

1. Download User Activity report
2. Open file
3. Verify user list

✅ Pass Criteria: User report downloads

---

### Test 34: Database Backup

**Expected:**

- "Backup Now" button
- Shows confirmation dialog
- Explains backup process

**How to Test:**

1. Click "Backup Now"
2. SweetAlert appears
3. Read message
4. Click "Download Backup"

✅ Pass Criteria: Backup button shows dialog

---

## ⚙️ Settings Testing

### Test 35: Notification Toggles

**Expected:**

- 4 toggle switches
- Can toggle on/off
- Visual feedback
- Settings save

**How to Test:**

1. Click "Settings"
2. Toggle each switch
3. Switches respond
4. Click "Save Settings"
5. Success notification

✅ Pass Criteria: Notification toggles work

---

### Test 36: Auto-Refresh Settings

**Expected:**

- Interval input box
- Number between 5-60
- Enable/disable toggle
- Save button works
- Settings persist

**How to Test:**

1. Change interval to 15
2. Toggle auto-refresh off
3. Click "Save Settings"
4. Success notification
5. Reload page
6. Settings retained

✅ Pass Criteria: Auto-refresh settings work

---

### Test 37: Branding Configuration

**Expected:**

- College name input
- Batch info input
- Can edit text
- Save button works
- Project credit visible

**How to Test:**

1. Edit college name
2. Edit batch info
3. Click save (if available)
4. Check credit display

✅ Pass Criteria: Branding settings work

---

## 🎨 UI/UX Testing

### Test 38: Theme Toggle (Dark/Light)

**Expected:**

- Toggle switch in header
- Clicking changes theme instantly
- All elements adapt
- Charts recolor
- Theme persists on reload

**How to Test:**

1. Click theme toggle
2. Page switches to dark mode
3. Check all sections change
4. Reload page
5. Theme remembered

✅ Pass Criteria: Theme toggle works perfectly

---

### Test 39: Sidebar Navigation

**Expected:**

- All menu items clickable
- Active item highlighted
- Content switches smoothly
- Badges update
- Smooth animation

**How to Test:**

1. Click each sidebar item
2. Content changes
3. Active highlight moves
4. No page reload

✅ Pass Criteria: Navigation smooth and correct

---

### Test 40: Mobile Responsive (Sidebar)

**Expected:**

- Sidebar hidden on mobile
- Hamburger menu appears
- Click opens sidebar
- Click outside closes
- Touch-friendly

**How to Test:**

1. Resize browser to < 768px
2. Sidebar disappears
3. Hamburger icon appears
4. Click hamburger
5. Sidebar slides in
6. Click X to close

✅ Pass Criteria: Mobile sidebar works

---

### Test 41: Responsive Cards

**Expected:**

- Cards stack on mobile
- 4 columns → 2 → 1
- Readable on all sizes
- No horizontal scroll
- Touch targets adequate

**How to Test:**

1. Resize browser window
2. Watch cards reflow
3. Check readability

✅ Pass Criteria: Cards responsive

---

### Test 42: Toast Notifications

**Expected:**

- Appear on success/error
- Top-right corner
- Auto-dismiss in 3 seconds
- Colored by type
- Non-blocking

**How to Test:**

1. Perform any action (add item)
2. Toast appears
3. Disappears after 3 seconds
4. Correct color (green for success)

✅ Pass Criteria: Toast notifications work

---

### Test 43: Modal Animations

**Expected:**

- Smooth fade-in
- Backdrop darkens
- Close on ESC key
- Close on backdrop click
- Close button works

**How to Test:**

1. Open any modal
2. Press ESC → closes
3. Open again
4. Click backdrop → closes
5. Open again
6. Click X button → closes

✅ Pass Criteria: Modals animate and close properly

---

### Test 44: Hover Effects

**Expected:**

- Cards lift on hover
- Buttons change color
- Smooth transitions
- Cursor changes to pointer
- No jumps or glitches

**How to Test:**

1. Hover over dashboard cards
2. Hover over buttons
3. Hover over menu items
4. Check smoothness

✅ Pass Criteria: Hover effects smooth

---

### Test 45: Loading States

**Expected:**

- "Loading..." text initially
- Spinners (if implemented)
- Smooth data population
- No flash of empty content

**How to Test:**

1. Reload page
2. Watch data load
3. Check for loading indicators

✅ Pass Criteria: Loading states present

---

## 🎭 Demo Mode Testing

### Test 46: Enable Demo Mode

**Expected:**

- Toggle switch in header
- Clicking enables demo
- Sample data loads instantly
- All sections populated
- Toast notification

**How to Test:**

1. Toggle "Demo Mode" ON
2. Toast: "Demo Mode Enabled"
3. Dashboard fills with data
4. Charts populate

✅ Pass Criteria: Demo mode loads sample data

---

### Test 47: Demo Data Quality

**Expected:**

- 20 sample orders
- 5 sample menu items
- 10 sample users
- Realistic values
- Varied statuses
- Mixed stock levels

**How to Test:**

1. Enable demo mode
2. Visit each section
3. Check data looks realistic
4. Verify variety

✅ Pass Criteria: Demo data appears realistic

---

### Test 48: Disable Demo Mode

**Expected:**

- Toggle OFF
- Returns to real data
- Charts update
- Toast notification
- Smooth transition

**How to Test:**

1. Toggle "Demo Mode" OFF
2. Toast: "Demo Mode Disabled"
3. Real data restored

✅ Pass Criteria: Demo mode toggles cleanly

---

## 🔄 Real-Time Features Testing

### Test 49: Auto-Refresh

**Expected:**

- Dashboard refreshes every 10s (or set interval)
- No page reload
- Smooth update
- Can be disabled

**How to Test:**

1. Enable auto-refresh
2. Watch dashboard
3. Data updates after interval
4. No noticeable flicker

✅ Pass Criteria: Auto-refresh works (even if subtle)

---

### Test 50: Manual Refresh

**Expected:**

- Refresh button in header
- Clicking reloads data
- Toast notification
- All sections update

**How to Test:**

1. Click refresh button
2. Toast: "Data refreshed"
3. Data updates

✅ Pass Criteria: Manual refresh works

---

## 🔒 Security Testing

### Test 51: Form Validation

**Expected:**

- Required fields enforced
- Email format validated
- Number fields accept numbers only
- Min/max values respected
- Error messages shown

**How to Test:**

1. Try submitting empty form
2. Try invalid email format
3. Try negative price
4. Check error messages

✅ Pass Criteria: Form validation prevents invalid submissions

---

### Test 52: API Error Handling

**Expected:**

- Graceful error messages
- No console errors break UI
- User-friendly alerts
- Fallback content

**How to Test:**

1. Stop Flask server
2. Try any action
3. Should see friendly error
4. UI still functional

✅ Pass Criteria: Errors handled gracefully

---

## 🌐 Browser Testing

### Test 53: Chrome

**Expected:** All features work

**Test:** Run through all tests in Chrome

✅ Pass Criteria: Everything works

---

### Test 54: Firefox

**Expected:** All features work

**Test:** Open in Firefox, test key features

✅ Pass Criteria: Everything works

---

### Test 55: Edge

**Expected:** All features work

**Test:** Open in Edge, test key features

✅ Pass Criteria: Everything works

---

## 📱 Device Testing

### Test 56: Desktop (1920x1080)

**Expected:** Full layout visible

**Test:** View at full desktop resolution

✅ Pass Criteria: Looks professional

---

### Test 57: Laptop (1366x768)

**Expected:** Everything fits

**Test:** Resize to laptop size

✅ Pass Criteria: No scrolling issues

---

### Test 58: Tablet (768x1024)

**Expected:** Responsive layout

**Test:** Resize to tablet

✅ Pass Criteria: Touch-friendly

---

### Test 59: Mobile (375x667)

**Expected:** Mobile layout

**Test:** Resize to mobile

✅ Pass Criteria: Usable on small screen

---

## ✅ Final Evaluation Checklist

### Before Demo Day

#### Technical

- [ ] Flask server starts without errors
- [ ] No console errors in browser
- [ ] All APIs responding
- [ ] Database accessible
- [ ] Images loading

#### Functionality

- [ ] Dashboard displays metrics
- [ ] Charts rendering
- [ ] Users can be managed
- [ ] Menu CRUD works
- [ ] Orders display
- [ ] Reports download

#### Visual

- [ ] Theme toggle works
- [ ] Responsive on mobile
- [ ] Animations smooth
- [ ] No broken layouts
- [ ] Professional appearance

#### Demo Mode

- [ ] Toggle switch works
- [ ] Sample data loads
- [ ] All features visible
- [ ] Easy to enable/disable

#### Documentation

- [ ] README complete
- [ ] Quick start available
- [ ] Code commented
- [ ] Features documented

---

## 🎯 Quick Test (5 Minutes)

If short on time, test these critical features:

1. ✅ Dashboard loads with charts
2. ✅ Theme toggle (dark/light)
3. ✅ Add menu item
4. ✅ Approve a user
5. ✅ View order details
6. ✅ Download a report
7. ✅ Enable demo mode
8. ✅ Mobile responsive (resize)
9. ✅ No console errors
10. ✅ Toast notifications work

---

## 🎉 Test Completion

### Scoring

- **50/60 Pass:** Good - ready for evaluation
- **55/60 Pass:** Excellent - minor issues only
- **60/60 Pass:** Perfect - production ready!

### Common Issues

- Images not loading → Check folder permissions
- Charts not showing → Verify Chart.js loaded
- API errors → Ensure Flask running
- Theme issues → Clear localStorage

---

## 📝 Testing Log Template

```
Test Date: __________
Tester: __________
Browser: __________
Screen Size: __________

Dashboard: ✅/❌
User Management: ✅/❌
Menu Management: ✅/❌
Inventory: ✅/❌
Orders: ✅/❌
Revenue: ✅/❌
Reports: ✅/❌
Settings: ✅/❌
UI/UX: ✅/❌
Demo Mode: ✅/❌

Issues Found:
1. _______________
2. _______________

Overall Status: PASS/FAIL

Notes:
_______________
_______________
```

---

## 🚀 You're Ready!

If you've completed this testing guide, your admin module is **evaluation-ready**!

**Remember:**

- Enable demo mode for clean presentations
- Test in dark mode - looks more professional
- Have your code explanation ready
- Know how to navigate quickly
- Be confident - you built something amazing!

---

**Good luck with your evaluation! 🎓**

_Testing Guide v1.0 - MCA Batch 2025_
