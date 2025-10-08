// ==================== Configuration ====================
const API_BASE = 'http://localhost:5000/api';
let autoRefreshInterval = null;
let charts = {};

// ==================== Initialize ====================
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

function initializeApp() {
    setupEventListeners();
    setupThemeToggle();
    setupSidebarNavigation();
    updateDateTime();
    setInterval(updateDateTime, 1000);
    
    // Load initial data
    loadDashboardData();
    
    // Setup auto-refresh
    startAutoRefresh();
}

// ==================== Event Listeners ====================
function setupEventListeners() {
    // Sidebar toggle for mobile
    document.getElementById('menuToggle')?.addEventListener('click', () => {
        document.getElementById('sidebar').classList.add('active');
    });
    
    document.getElementById('closeSidebar')?.addEventListener('click', () => {
        document.getElementById('sidebar').classList.remove('active');
    });
    
    // Refresh button
    document.getElementById('refreshBtn')?.addEventListener('click', () => {
        loadDashboardData();
        showToast('Data refreshed successfully', 'success');
    });
    
    // Logout button
    document.getElementById('logoutBtn')?.addEventListener('click', () => {
        Swal.fire({
            title: 'Logout',
            text: 'Are you sure you want to logout?',
            icon: 'question',
            showCancelButton: true,
            confirmButtonText: 'Yes, logout',
            cancelButtonText: 'Cancel'
        }).then((result) => {
            if (result.isConfirmed) {
                window.location.href = '/';
            }
        });
    });
    
    // Add menu item button
    document.getElementById('addMenuItemBtn')?.addEventListener('click', () => {
        const modal = new bootstrap.Modal(document.getElementById('addMenuModal'));
        modal.show();
    });
    
    // Submit menu item
    document.getElementById('submitMenuBtn')?.addEventListener('click', submitMenuItem);
    
    // Update menu item
    document.getElementById('updateMenuBtn')?.addEventListener('click', updateMenuItem);
    
    // Update user
    document.getElementById('updateUserBtn')?.addEventListener('click', updateUser);
    
    // Image preview
    document.getElementById('menuImage')?.addEventListener('change', previewImage);
    document.getElementById('editMenuImage')?.addEventListener('change', previewEditImage);
    
    // User filters
    document.getElementById('userSearch')?.addEventListener('input', filterUsers);
    document.getElementById('roleFilter')?.addEventListener('change', filterUsers);
    document.getElementById('statusFilter')?.addEventListener('change', filterUsers);
    
    // Category tabs
    document.querySelectorAll('#categoryTabs .nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const category = e.target.dataset.category;
            filterMenuByCategory(category);
            
            // Update active tab
            document.querySelectorAll('#categoryTabs .nav-link').forEach(l => l.classList.remove('active'));
            e.target.classList.add('active');
        });
    });
    
    // Order status filter
    document.getElementById('orderStatusFilter')?.addEventListener('change', filterOrders);
    
    // Date range filter for revenue
    document.getElementById('applyDateFilter')?.addEventListener('click', loadRevenueData);
    
    // Export stock button
    document.getElementById('exportStockBtn')?.addEventListener('click', () => downloadReport('stock'));
    
    // Backup database
    document.getElementById('backupDbBtn')?.addEventListener('click', backupDatabase);
    
    // Save settings
    document.getElementById('saveSettingsBtn')?.addEventListener('click', saveSettings);
    
    // Auto-refresh toggle
    document.getElementById('autoRefresh')?.addEventListener('change', (e) => {
        if (e.target.checked) {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    });
}

// ==================== Theme Toggle ====================
function setupThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        themeToggle.checked = true;
        themeIcon.classList.replace('bi-moon-stars', 'bi-sun');
    }
    
    themeToggle?.addEventListener('change', (e) => {
        if (e.target.checked) {
            document.body.classList.add('dark-mode');
            themeIcon.classList.replace('bi-moon-stars', 'bi-sun');
            localStorage.setItem('theme', 'dark');
        } else {
            document.body.classList.remove('dark-mode');
            themeIcon.classList.replace('bi-sun', 'bi-moon-stars');
            localStorage.setItem('theme', 'light');
        }
        
        // Refresh charts with new theme
        updateChartTheme();
    });
}

// ==================== Sidebar Navigation ====================
function setupSidebarNavigation() {
    const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            const sectionId = link.dataset.section + 'Section';
            
            // Update active nav link
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
            
            // Show corresponding section
            document.querySelectorAll('.content-section').forEach(section => {
                section.classList.remove('active');
            });
            
            document.getElementById(sectionId)?.classList.add('active');
            
            // Update page title
            const pageTitle = link.querySelector('span').textContent;
            document.getElementById('pageTitle').textContent = pageTitle;
            
            // Load section-specific data
            loadSectionData(link.dataset.section);
            
            // Close sidebar on mobile
            if (window.innerWidth < 768) {
                document.getElementById('sidebar').classList.remove('active');
            }
        });
    });
}

// ==================== Load Section Data ====================
function loadSectionData(section) {
    switch(section) {
        case 'dashboard':
            loadDashboardData();
            break;
        case 'users':
            loadUsers();
            break;
        case 'menu':
            loadMenuItems();
            break;
        case 'inventory':
            loadInventory();
            break;
        case 'orders':
            loadOrders();
            break;
        case 'revenue':
            loadRevenueData();
            break;
    }
}

// ==================== Dashboard Data ====================
async function loadDashboardData() {
    try {
        // Fetch all data in parallel
        const [orders, menu, users] = await Promise.all([
            fetch(`${API_BASE}/orders`).then(r => r.json()),
            fetch(`${API_BASE}/menu`).then(r => r.json()),
            fetch(`${API_BASE}/users`).then(r => r.json())
        ]);
        
        updateDashboardStats(orders, menu, users);
        updateCharts(orders, menu);
        updateRecentOrders(orders);
        updateAlerts(menu, users);
        generateSmartInsights(orders, menu);
        
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showToast('Error loading dashboard data', 'error');
    }
}

function updateDashboardStats(orders, menu, users) {
    const today = new Date().toDateString();
    
    // Today's orders - filter by actual created_at timestamp
    const todayOrders = orders.filter(o => {
        if (o.created_at) {
            try {
                const orderDate = new Date(o.created_at);
                return orderDate.toDateString() === today;
            } catch (e) {
                console.error('Error parsing order date:', e);
                return false;
            }
        }
        return false;
    });
    
    document.getElementById('todayOrders').textContent = todayOrders.length;
    
    // Today's revenue
    const todayRevenue = todayOrders.reduce((sum, o) => sum + (o.total_price || 0), 0);
    document.getElementById('todayRevenue').textContent = todayRevenue.toFixed(2);
    
    // Active users
    const activeUsers = users.filter(u => u.status === 'approved').length;
    document.getElementById('activeUsers').textContent = activeUsers;
    
    // Pending users
    const pendingUsers = users.filter(u => u.status === 'pending').length;
    document.getElementById('usersChange').textContent = `${pendingUsers} pending`;
    document.getElementById('pendingUsersBadge').textContent = pendingUsers;
    
    // Out of stock
    const outOfStock = menu.filter(m => m.stock === 0).length;
    document.getElementById('outOfStock').textContent = outOfStock;
    
    // Low stock
    const lowStock = menu.filter(m => m.stock > 0 && m.stock <= 10).length;
    document.getElementById('stockChange').textContent = `${lowStock} low stock`;
    document.getElementById('lowStockBadge').textContent = lowStock;
}

function updateCharts(orders, menu) {
    createOrdersPerHourChart(orders);
    createOrderStatusChart(orders);
    createTopSellingChart(orders, menu);
    createRevenueTrendChart(orders);
}

// ==================== Charts ====================
function createOrdersPerHourChart(orders) {
    const ctx = document.getElementById('ordersPerHourChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (charts.ordersPerHour) {
        charts.ordersPerHour.destroy();
    }
    
    // Generate hours (0-23)
    const hours = Array.from({length: 24}, (_, i) => i);
    const orderCounts = new Array(24).fill(0);
    
    // Get today's date string for filtering
    const today = new Date().toDateString();
    
    // Count orders by hour from actual timestamps
    orders.forEach(order => {
        if (order.created_at) {
            try {
                const orderDate = new Date(order.created_at);
                // Only count today's orders
                if (orderDate.toDateString() === today) {
                    const hour = orderDate.getHours();
                    orderCounts[hour]++;
                }
            } catch (e) {
                console.error('Error parsing order timestamp:', e);
            }
        }
    });
    
    const isDark = document.body.classList.contains('dark-mode');
    
    charts.ordersPerHour = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours.map(h => `${h}:00`),
            datasets: [{
                label: 'Orders',
                data: orderCounts,
                borderColor: '#4f46e5',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: isDark ? '#f1f5f9' : '#0f172a'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: isDark ? '#94a3b8' : '#64748b',
                        stepSize: 1
                    },
                    grid: {
                        color: isDark ? '#334155' : '#e2e8f0'
                    }
                },
                x: {
                    ticks: {
                        color: isDark ? '#94a3b8' : '#64748b'
                    },
                    grid: {
                        color: isDark ? '#334155' : '#e2e8f0'
                    }
                }
            }
        }
    });
}

function createOrderStatusChart(orders) {
    const ctx = document.getElementById('orderStatusChart');
    if (!ctx) return;
    
    if (charts.orderStatus) {
        charts.orderStatus.destroy();
    }
    
    const statusCounts = {};
    orders.forEach(o => {
        const status = o.status || 'Order Received';
        statusCounts[status] = (statusCounts[status] || 0) + 1;
    });
    
    const isDark = document.body.classList.contains('dark-mode');
    
    charts.orderStatus = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(statusCounts),
            datasets: [{
                data: Object.values(statusCounts),
                backgroundColor: [
                    '#4f46e5',
                    '#10b981',
                    '#f59e0b',
                    '#ef4444',
                    '#3b82f6'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: isDark ? '#f1f5f9' : '#0f172a'
                    }
                }
            }
        }
    });
}

function createTopSellingChart(orders, menu) {
    const ctx = document.getElementById('topSellingChart');
    if (!ctx) return;
    
    if (charts.topSelling) {
        charts.topSelling.destroy();
    }
    
    // Count items sold
    const itemCounts = {};
    orders.forEach(order => {
        if (order.items && Array.isArray(order.items)) {
            order.items.forEach(item => {
                const itemName = item.name || `Item ${item.id}`;
                itemCounts[itemName] = (itemCounts[itemName] || 0) + (item.qty || 1);
            });
        }
    });
    
    // Get top 5
    const sorted = Object.entries(itemCounts)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5);
    
    const isDark = document.body.classList.contains('dark-mode');
    
    charts.topSelling = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: sorted.map(([name]) => name),
            datasets: [{
                label: 'Quantity Sold',
                data: sorted.map(([,count]) => count),
                backgroundColor: [
                    'rgba(79, 70, 229, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(59, 130, 246, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: isDark ? '#94a3b8' : '#64748b'
                    },
                    grid: {
                        color: isDark ? '#334155' : '#e2e8f0'
                    }
                },
                x: {
                    ticks: {
                        color: isDark ? '#94a3b8' : '#64748b'
                    },
                    grid: {
                        color: isDark ? '#334155' : '#e2e8f0'
                    }
                }
            }
        }
    });
}

function createRevenueTrendChart(orders) {
    const ctx = document.getElementById('revenueTrendChart');
    if (!ctx) return;
    
    if (charts.revenueTrend) {
        charts.revenueTrend.destroy();
    }
    
    // Generate last 7 days
    const days = [];
    const revenues = [];
    
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        const dateString = date.toDateString();
        days.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        
        // Calculate actual revenue for this date from orders
        const dayRevenue = orders.reduce((sum, order) => {
            if (order.created_at) {
                try {
                    const orderDate = new Date(order.created_at);
                    if (orderDate.toDateString() === dateString) {
                        return sum + (order.total_price || 0);
                    }
                } catch (e) {
                    console.error('Error parsing order date:', e);
                }
            }
            return sum;
        }, 0);
        
        revenues.push(dayRevenue);
    }
    
    const isDark = document.body.classList.contains('dark-mode');
    
    charts.revenueTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: days,
            datasets: [{
                label: 'Revenue (₹)',
                data: revenues,
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: isDark ? '#f1f5f9' : '#0f172a'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: isDark ? '#94a3b8' : '#64748b',
                        callback: (value) => '₹' + value.toFixed(0)
                    },
                    grid: {
                        color: isDark ? '#334155' : '#e2e8f0'
                    }
                },
                x: {
                    ticks: {
                        color: isDark ? '#94a3b8' : '#64748b'
                    },
                    grid: {
                        color: isDark ? '#334155' : '#e2e8f0'
                    }
                }
            }
        }
    });
}

function updateChartTheme() {
    // Recreate all charts with new theme
    const sections = ['dashboard', 'revenue'];
    sections.forEach(section => loadSectionData(section));
}

// ==================== Recent Orders & Alerts ====================
function updateRecentOrders(orders) {
    const feed = document.getElementById('recentOrdersFeed');
    if (!feed) return;
    
    const recent = orders.slice(0, 5);
    
    if (recent.length === 0) {
        feed.innerHTML = '<p class="text-muted">No recent orders</p>';
        return;
    }
    
    feed.innerHTML = recent.map(order => `
        <div class="activity-item">
            <strong>${order.customer_name}</strong> placed order #${order.id}
            <br>
            <small>₹${order.total_price} • ${order.items?.length || 0} items</small>
            <span class="time">Just now</span>
        </div>
    `).join('');
}

function updateAlerts(menu, users) {
    const alerts = document.getElementById('liveAlerts');
    if (!alerts) return;
    
    const alertItems = [];
    
    // Low stock alerts
    menu.filter(m => m.stock > 0 && m.stock <= 5).forEach(item => {
        alertItems.push(`
            <div class="activity-item border-warning">
                <i class="bi bi-exclamation-triangle text-warning"></i>
                <strong>${item.name}</strong> is running low (${item.stock} left)
                <span class="time">Stock Alert</span>
            </div>
        `);
    });
    
    // Out of stock
    menu.filter(m => m.stock === 0).forEach(item => {
        alertItems.push(`
            <div class="activity-item border-danger">
                <i class="bi bi-x-circle text-danger"></i>
                <strong>${item.name}</strong> is out of stock
                <span class="time">Critical</span>
            </div>
        `);
    });
    
    // Pending users
    const pendingCount = users.filter(u => u.status === 'pending').length;
    if (pendingCount > 0) {
        alertItems.push(`
            <div class="activity-item border-info">
                <i class="bi bi-person-plus text-info"></i>
                <strong>${pendingCount} new user(s)</strong> awaiting approval
                <span class="time">User Management</span>
            </div>
        `);
    }
    
    if (alertItems.length === 0) {
        alerts.innerHTML = '<p class="text-muted">No alerts</p>';
    } else {
        alerts.innerHTML = alertItems.slice(0, 5).join('');
    }
}

function generateSmartInsights(orders, menu) {
    const insights = document.getElementById('smartInsights');
    if (!insights) return;
    
    const insightItems = [];
    
    // Calculate comprehensive item sales data
    const itemStats = {};
    orders.forEach(order => {
        if (order.items && Array.isArray(order.items)) {
            order.items.forEach(item => {
                const itemName = item.name || `Item ${item.id}`;
                if (!itemStats[itemName]) {
                    itemStats[itemName] = { quantity: 0, revenue: 0 };
                }
                itemStats[itemName].quantity += (item.qty || 1);
                itemStats[itemName].revenue += (item.price || 0) * (item.qty || 1);
            });
        }
    });
    
    // 1. BEST SELLER INSIGHT - Most sold item by quantity
    if (Object.keys(itemStats).length > 0) {
        const topItem = Object.entries(itemStats)
            .sort(([,a], [,b]) => b.quantity - a.quantity)[0];
        const [itemName, stats] = topItem;
        const totalRevenue = stats.revenue.toFixed(2);
        
        insightItems.push(`
            <div class="insight-item">
                <i class="bi bi-fire text-danger"></i>
                <strong>Best Seller:</strong> ${itemName} - ${stats.quantity} units sold (₹${totalRevenue} revenue)
            </div>
        `);
    }
    
    // 2. REVENUE CHAMPION - Highest revenue generating item
    if (Object.keys(itemStats).length > 1) {
        const revenueChamp = Object.entries(itemStats)
            .sort(([,a], [,b]) => b.revenue - a.revenue)[0];
        const [itemName, stats] = revenueChamp;
        
        // Only show if different from best seller
        const bestSeller = Object.entries(itemStats)
            .sort(([,a], [,b]) => b.quantity - a.quantity)[0][0];
        
        if (itemName !== bestSeller) {
            insightItems.push(`
                <div class="insight-item">
                    <i class="bi bi-trophy text-warning"></i>
                    <strong>Revenue Champion:</strong> ${itemName} (₹${stats.revenue.toFixed(2)} total)
                </div>
            `);
        }
    }
    
    // 3. CRITICAL STOCK ALERT - Items that will run out based on sales velocity
    const criticalItems = menu.filter(item => {
        if (item.stock <= 0) return false;
        const itemName = item.name;
        const sold = itemStats[itemName]?.quantity || 0;
        
        // Calculate sales velocity: if sold > 5 and stock < 10, it's critical
        // Or if current stock < 20% of items sold, flag it
        if (sold > 0) {
            const velocityRatio = item.stock / sold;
            return velocityRatio < 2 && item.stock <= 10; // Will run out soon
        }
        return item.stock <= 3; // Very low stock regardless
    });
    
    if (criticalItems.length > 0) {
        const mostCritical = criticalItems[0];
        const soldQty = itemStats[mostCritical.name]?.quantity || 0;
        const hoursLeft = soldQty > 0 ? Math.floor((mostCritical.stock / soldQty) * 24) : 0;
        
        if (hoursLeft > 0 && hoursLeft < 48) {
            insightItems.push(`
                <div class="insight-item">
                    <i class="bi bi-exclamation-triangle text-danger"></i>
                    <strong>⚠️ Critical Alert:</strong> ${mostCritical.name} will run out in ~${hoursLeft}h at current sales rate!
                </div>
            `);
        } else {
            insightItems.push(`
                <div class="insight-item">
                    <i class="bi bi-exclamation-triangle text-warning"></i>
                    <strong>Low Stock Alert:</strong> ${mostCritical.name} (only ${mostCritical.stock} left)
                </div>
            `);
        }
    }
    
    // 4. SMART REVENUE INSIGHT - Average order value with trend
    const totalRevenue = orders.reduce((sum, o) => sum + (o.total_price || 0), 0);
    const avgOrder = orders.length > 0 ? (totalRevenue / orders.length) : 0;
    
    if (orders.length > 0) {
        let revenueInsight = '';
        if (avgOrder > 150) {
            revenueInsight = ' - Excellent! Above target ₹150';
        } else if (avgOrder > 100) {
            revenueInsight = ' - Good performance';
        } else if (avgOrder > 50) {
            revenueInsight = ' - Consider upselling combos';
        } else {
            revenueInsight = ' - Low value, promote higher items';
        }
        
        insightItems.push(`
            <div class="insight-item">
                <i class="bi bi-graph-up text-success"></i>
                <strong>Avg Order Value:</strong> ₹${avgOrder.toFixed(2)}${revenueInsight}
            </div>
        `);
    }
    
    // 5. PEAK PERFORMANCE - Order volume analysis
    if (orders.length >= 10) {
        const statusBreakdown = orders.reduce((acc, o) => {
            acc[o.status || 'Order Received'] = (acc[o.status || 'Order Received'] || 0) + 1;
            return acc;
        }, {});
        
        const completed = statusBreakdown['Delivered'] || 0;
        const completionRate = ((completed / orders.length) * 100).toFixed(1);
        
        insightItems.push(`
            <div class="insight-item">
                <i class="bi bi-speedometer text-primary"></i>
                <strong>Order Volume:</strong> ${orders.length} orders | ${completionRate}% completion rate
            </div>
        `);
    } else if (orders.length > 0) {
        insightItems.push(`
            <div class="insight-item">
                <i class="bi bi-info-circle text-info"></i>
                <strong>Order Status:</strong> ${orders.length} order${orders.length > 1 ? 's' : ''} processed today
            </div>
        `);
    }
    
    // 6. CATEGORY PERFORMANCE - Which category is selling most
    const categoryStats = {};
    menu.forEach(item => {
        const category = item.category || 'Other';
        const sold = itemStats[item.name]?.quantity || 0;
        if (!categoryStats[category]) {
            categoryStats[category] = { quantity: 0, revenue: 0 };
        }
        categoryStats[category].quantity += sold;
        categoryStats[category].revenue += itemStats[item.name]?.revenue || 0;
    });
    
    const topCategory = Object.entries(categoryStats)
        .filter(([,stats]) => stats.quantity > 0)
        .sort(([,a], [,b]) => b.quantity - a.quantity)[0];
    
    if (topCategory) {
        const [catName, stats] = topCategory;
        insightItems.push(`
            <div class="insight-item">
                <i class="bi bi-star text-warning"></i>
                <strong>Top Category:</strong> ${catName} (${stats.quantity} items sold)
            </div>
        `);
    }
    
    // 7. STOCK HEALTH - Overall inventory status
    const totalItems = menu.length;
    const outOfStock = menu.filter(m => m.stock === 0).length;
    const lowStock = menu.filter(m => m.stock > 0 && m.stock <= 5).length;
    const healthyStock = totalItems - outOfStock - lowStock;
    
    if (totalItems > 0) {
        const healthPercentage = ((healthyStock / totalItems) * 100).toFixed(0);
        let healthStatus = '';
        let healthIcon = '';
        
        if (healthPercentage >= 80) {
            healthStatus = 'Excellent inventory health';
            healthIcon = 'bi-check-circle text-success';
        } else if (healthPercentage >= 60) {
            healthStatus = 'Good - Minor restocking needed';
            healthIcon = 'bi-info-circle text-info';
        } else if (healthPercentage >= 40) {
            healthStatus = 'Fair - Restocking required';
            healthIcon = 'bi-exclamation-circle text-warning';
        } else {
            healthStatus = 'Critical - Urgent restocking!';
            healthIcon = 'bi-x-circle text-danger';
        }
        
        insightItems.push(`
            <div class="insight-item">
                <i class="bi ${healthIcon}"></i>
                <strong>Inventory Health:</strong> ${healthPercentage}% healthy (${healthyStock}/${totalItems} items) - ${healthStatus}
            </div>
        `);
    }
    
    // 8. NO DATA INSIGHT - Helpful message if no orders
    if (orders.length === 0 && menu.length > 0) {
        insightItems.push(`
            <div class="insight-item">
                <i class="bi bi-lightbulb text-info"></i>
                <strong>Getting Started:</strong> No orders yet. ${menu.length} menu items ready. Waiting for customer orders!
            </div>
        `);
    }
    
    // Display insights or show helpful message
    if (insightItems.length === 0) {
        insights.innerHTML = `
            <div class="insight-item">
                <i class="bi bi-info-circle text-muted"></i>
                <strong>Smart Insights:</strong> Add menu items and process orders to see AI-powered insights here.
            </div>
        `;
    } else {
        insights.innerHTML = insightItems.join('');
    }
}

// ==================== User Management ====================
async function loadUsers() {
    try {
        const response = await fetch(`${API_BASE}/users`);
        const users = await response.json();
        
        window.allUsers = users; // Store for filtering
        displayUsers(users);
        
    } catch (error) {
        console.error('Error loading users:', error);
        showToast('Error loading users', 'error');
    }
}

function displayUsers(users) {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody) return;
    
    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted">No users found</td></tr>';
        return;
    }
    
    tbody.innerHTML = users.map(user => `
        <tr>
            <td>${user.email}</td>
            <td><span class="badge bg-secondary">${user.role}</span></td>
            <td>
                ${user.status === 'approved' 
                    ? '<span class="badge bg-success">✓ Approved</span>' 
                    : '<span class="badge bg-warning">⏳ Pending</span>'}
            </td>
            <td>
                ${user.status === 'pending' ? `
                    <button class="btn btn-sm btn-success" onclick="approveUser('${user.email}')">
                        <i class="bi bi-check-circle"></i> Approve
                    </button>
                ` : ''}
                <button class="btn btn-sm btn-primary" onclick="editUser('${user.email}', '${user.role}')">
                    <i class="bi bi-pencil"></i> Edit
                </button>
                <button class="btn btn-sm btn-danger" onclick="deleteUser('${user.email}')">
                    <i class="bi bi-trash"></i> Delete
                </button>
            </td>
        </tr>
    `).join('');
}

function filterUsers() {
    const search = document.getElementById('userSearch')?.value.toLowerCase() || '';
    const roleFilter = document.getElementById('roleFilter')?.value || '';
    const statusFilter = document.getElementById('statusFilter')?.value || '';
    
    const filtered = (window.allUsers || []).filter(user => {
        const matchesSearch = user.email.toLowerCase().includes(search);
        const matchesRole = !roleFilter || user.role === roleFilter;
        const matchesStatus = !statusFilter || user.status === statusFilter;
        
        return matchesSearch && matchesRole && matchesStatus;
    });
    
    displayUsers(filtered);
}

async function approveUser(email) {
    try {
        const response = await fetch(`${API_BASE}/users/approve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, role: 'user' })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('User approved successfully', 'success');
            loadUsers();
            loadDashboardData();
        } else {
            showToast(data.error || 'Error approving user', 'error');
        }
    } catch (error) {
        console.error('Error approving user:', error);
        showToast('Error approving user', 'error');
    }
}

function editUser(email, currentRole) {
    document.getElementById('editUserEmail').value = email;
    document.getElementById('editUserEmailDisplay').value = email;
    document.getElementById('editUserRole').value = currentRole;
    
    const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
    modal.show();
}

async function updateUser() {
    const email = document.getElementById('editUserEmail').value;
    const role = document.getElementById('editUserRole').value;
    
    try {
        const response = await fetch(`${API_BASE}/users/assign-role`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, role })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('User role updated successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('editUserModal')).hide();
            loadUsers();
        } else {
            showToast(data.error || 'Error updating user', 'error');
        }
    } catch (error) {
        console.error('Error updating user:', error);
        showToast('Error updating user', 'error');
    }
}

async function deleteUser(email) {
    const result = await Swal.fire({
        title: 'Delete User',
        text: `Are you sure you want to delete ${email}?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, delete',
        confirmButtonColor: '#ef4444',
        cancelButtonText: 'Cancel'
    });
    
    if (!result.isConfirmed) return;
    
    try {
        const response = await fetch(`${API_BASE}/users/delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('User deleted successfully', 'success');
            loadUsers();
            loadDashboardData();
        } else {
            showToast(data.error || 'Error deleting user', 'error');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        showToast('Error deleting user', 'error');
    }
}

// ==================== Menu Management ====================
async function loadMenuItems() {
    try {
        const response = await fetch(`${API_BASE}/menu`);
        const menu = await response.json();
        
        window.allMenuItems = menu; // Store for filtering
        displayMenuItems(menu);
        
    } catch (error) {
        console.error('Error loading menu:', error);
        showToast('Error loading menu items', 'error');
    }
}

function displayMenuItems(items) {
    const grid = document.getElementById('menuItemsGrid');
    if (!grid) return;
    
    if (items.length === 0) {
        grid.innerHTML = '<div class="col-12 text-center text-muted"><p>No menu items found</p></div>';
        return;
    }
    
    grid.innerHTML = items.map(item => {
        const stockStatus = item.stock === 0 ? 'out-of-stock' : 
                           item.stock <= 10 ? 'low-stock' : 'in-stock';
        const stockText = item.stock === 0 ? 'Out of Stock' :
                         item.stock <= 10 ? `Low: ${item.stock}` : `${item.stock}`;
        const stockColor = item.stock === 0 ? 'danger' :
                          item.stock <= 10 ? 'warning' : 'success';
        
        return `
            <div class="col-md-4 col-lg-3">
                <div class="menu-item-card">
                    <span class="stock-badge text-${stockColor}">${stockText}</span>
                    <img src="/static/images/${item.image}" alt="${item.name}" onerror="this.src='https://via.placeholder.com/200x200?text=${item.name}'">
                    <div class="menu-item-body">
                        <div class="menu-item-header">
                            <h6>${item.name}</h6>
                            <span class="menu-item-price">₹${item.price}</span>
                        </div>
                        <p class="text-muted small mb-2">
                            <i class="bi bi-tag"></i> ${item.category}
                        </p>
                        <div class="menu-item-footer">
                            <div class="stock-indicator ${stockStatus}">
                                <i class="bi bi-circle-fill"></i>
                                Stock: ${item.stock}
                            </div>
                            <div class="menu-item-actions">
                                <button class="btn btn-sm btn-success" onclick="quickRestock(${item.id}, ${item.stock})" title="Add 10 stock">
                                    <i class="bi bi-plus-circle"></i>
                                </button>
                                <button class="btn btn-sm btn-primary" onclick="editMenuItem(${item.id})" title="Edit">
                                    <i class="bi bi-pencil"></i>
                                </button>
                                <button class="btn btn-sm btn-danger" onclick="deleteMenuItem(${item.id})" title="Delete">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function filterMenuByCategory(category) {
    const items = category === 'all' 
        ? window.allMenuItems 
        : window.allMenuItems.filter(item => item.category === category);
    
    displayMenuItems(items);
}

function previewImage(e) {
    const file = e.target.files[0];
    const preview = document.getElementById('imagePreview');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
        };
        reader.readAsDataURL(file);
    }
}

function previewEditImage(e) {
    const file = e.target.files[0];
    const preview = document.getElementById('editImagePreview');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            preview.innerHTML = `<img src="${e.target.result}" alt="Preview">`;
        };
        reader.readAsDataURL(file);
    }
}

async function submitMenuItem() {
    const formData = new FormData();
    formData.append('name', document.getElementById('menuName').value);
    formData.append('price', document.getElementById('menuPrice').value);
    formData.append('category', document.getElementById('menuCategory').value);
    formData.append('stock', document.getElementById('menuStock').value);
    formData.append('deliverable', document.getElementById('menuDeliverable').checked ? 1 : 0);
    formData.append('image', document.getElementById('menuImage').files[0]);
    
    try {
        const response = await fetch(`${API_BASE}/menu`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Menu item added successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('addMenuModal')).hide();
            document.getElementById('addMenuForm').reset();
            document.getElementById('imagePreview').innerHTML = '';
            loadMenuItems();
            loadDashboardData();
        } else {
            showToast(data.error || 'Error adding menu item', 'error');
        }
    } catch (error) {
        console.error('Error adding menu item:', error);
        showToast('Error adding menu item', 'error');
    }
}

function editMenuItem(itemId) {
    const item = window.allMenuItems.find(m => m.id === itemId);
    if (!item) return;
    
    document.getElementById('editMenuId').value = item.id;
    document.getElementById('editMenuName').value = item.name;
    document.getElementById('editMenuPrice').value = item.price;
    document.getElementById('editMenuCategory').value = item.category;
    document.getElementById('editMenuStock').value = item.stock;
    document.getElementById('editMenuDeliverable').checked = item.deliverable;
    
    const modal = new bootstrap.Modal(document.getElementById('editMenuModal'));
    modal.show();
}

async function updateMenuItem() {
    const itemId = document.getElementById('editMenuId').value;
    const imageFile = document.getElementById('editMenuImage').files[0];
    
    const formData = new FormData();
    formData.append('name', document.getElementById('editMenuName').value);
    formData.append('price', document.getElementById('editMenuPrice').value);
    formData.append('category', document.getElementById('editMenuCategory').value);
    formData.append('stock', document.getElementById('editMenuStock').value);
    formData.append('deliverable', document.getElementById('editMenuDeliverable').checked ? 1 : 0);
    
    if (imageFile) {
        formData.append('image', imageFile);
    }
    
    try {
        const response = await fetch(`${API_BASE}/menu/${itemId}`, {
            method: 'PUT',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Menu item updated successfully', 'success');
            bootstrap.Modal.getInstance(document.getElementById('editMenuModal')).hide();
            loadMenuItems();
            loadDashboardData();
        } else {
            showToast(data.error || 'Error updating menu item', 'error');
        }
    } catch (error) {
        console.error('Error updating menu item:', error);
        showToast('Error updating menu item', 'error');
    }
}

async function deleteMenuItem(itemId) {
    const result = await Swal.fire({
        title: 'Delete Menu Item',
        text: 'Are you sure you want to delete this item?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, delete',
        confirmButtonColor: '#ef4444',
        cancelButtonText: 'Cancel'
    });
    
    if (!result.isConfirmed) return;
    
    try {
        const response = await fetch(`${API_BASE}/menu/${itemId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showToast('Menu item deleted successfully', 'success');
            loadMenuItems();
            loadDashboardData();
        } else {
            showToast('Error deleting menu item', 'error');
        }
    } catch (error) {
        console.error('Error deleting menu item:', error);
        showToast('Error deleting menu item', 'error');
    }
}

async function quickRestock(itemId, currentStock) {
    try {
        const response = await fetch(`${API_BASE}/menu/${itemId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stock: currentStock + 10 })
        });
        
        if (response.ok) {
            showToast('Stock updated: +10 items', 'success');
            loadMenuItems();
            loadInventory();
            loadDashboardData();
        } else {
            showToast('Error updating stock', 'error');
        }
    } catch (error) {
        console.error('Error updating stock:', error);
        showToast('Error updating stock', 'error');
    }
}

// ==================== Inventory Management ====================
async function loadInventory() {
    try {
        const response = await fetch(`${API_BASE}/menu`);
        const menu = await response.json();
        
        updateStockSummary(menu);
        displayInventoryTable(menu);
        
    } catch (error) {
        console.error('Error loading inventory:', error);
        showToast('Error loading inventory', 'error');
    }
}

function updateStockSummary(menu) {
    const outOfStock = menu.filter(m => m.stock === 0).length;
    const lowStock = menu.filter(m => m.stock > 0 && m.stock <= 10).length;
    const inStock = menu.filter(m => m.stock > 10).length;
    
    document.getElementById('outOfStockCount').textContent = outOfStock;
    document.getElementById('lowStockCount').textContent = lowStock;
    document.getElementById('inStockCount').textContent = inStock;
}

function displayInventoryTable(items) {
    const tbody = document.getElementById('inventoryTableBody');
    if (!tbody) return;
    
    if (items.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">No items found</td></tr>';
        return;
    }
    
    tbody.innerHTML = items.map(item => {
        const stockStatus = item.stock === 0 ? 'out-of-stock' : 
                           item.stock <= 10 ? 'low-stock' : 'in-stock';
        const stockText = item.stock === 0 ? 'Out of Stock' :
                         item.stock <= 10 ? 'Low Stock' : 'In Stock';
        
        return `
            <tr>
                <td><strong>${item.name}</strong></td>
                <td><span class="badge bg-secondary">${item.category}</span></td>
                <td><strong>${item.stock}</strong></td>
                <td>
                    <span class="stock-indicator ${stockStatus}">
                        <i class="bi bi-circle-fill"></i>
                        ${stockText}
                    </span>
                </td>
                <td>₹${item.price}</td>
                <td>
                    <button class="btn btn-sm btn-success" onclick="quickRestock(${item.id}, ${item.stock})">
                        <i class="bi bi-plus-circle"></i> +10
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="editMenuItem(${item.id})">
                        <i class="bi bi-pencil"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

// ==================== Orders Management ====================
async function loadOrders() {
    try {
        const response = await fetch(`${API_BASE}/orders`);
        const orders = await response.json();
        
        window.allOrders = orders;
        displayOrders(orders);
        
    } catch (error) {
        console.error('Error loading orders:', error);
        showToast('Error loading orders', 'error');
    }
}

function displayOrders(orders) {
    const tbody = document.getElementById('ordersTableBody');
    if (!tbody) return;
    
    if (orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No orders found</td></tr>';
        return;
    }
    
    tbody.innerHTML = orders.map(order => {
        const statusClass = {
            'Order Received': 'info',
            'Preparing': 'warning',
            'Ready': 'success',
            'Completed': 'secondary',
            'Cancelled': 'danger'
        }[order.status] || 'info';
        
        const itemsList = order.items && Array.isArray(order.items)
            ? order.items.map(i => `${i.name} (${i.qty})`).join(', ')
            : 'N/A';
        
        return `
            <tr>
                <td><strong>#${order.id}</strong></td>
                <td>${order.customer_name}<br><small class="text-muted">${order.customer_email}</small></td>
                <td><small>${itemsList}</small></td>
                <td><strong>₹${order.total_price}</strong></td>
                <td><code>${order.otp}</code></td>
                <td><span class="badge bg-${statusClass}">${order.status}</span></td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="viewOrderDetails(${order.id})">
                        <i class="bi bi-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

function filterOrders() {
    const statusFilter = document.getElementById('orderStatusFilter')?.value || '';
    
    const filtered = statusFilter === '' 
        ? window.allOrders 
        : window.allOrders.filter(order => order.status === statusFilter);
    
    displayOrders(filtered);
}

function viewOrderDetails(orderId) {
    const order = window.allOrders.find(o => o.id === orderId);
    if (!order) return;
    
    const itemsList = order.items && Array.isArray(order.items)
        ? order.items.map(i => `<li>${i.name} - Qty: ${i.qty}</li>`).join('')
        : '<li>No items</li>';
    
    Swal.fire({
        title: `Order #${order.id}`,
        html: `
            <div style="text-align: left;">
                <p><strong>Customer:</strong> ${order.customer_name}</p>
                <p><strong>Email:</strong> ${order.customer_email}</p>
                <p><strong>Status:</strong> ${order.status}</p>
                <p><strong>OTP:</strong> <code>${order.otp}</code></p>
                <p><strong>Total:</strong> ₹${order.total_price}</p>
                <p><strong>Items:</strong></p>
                <ul>${itemsList}</ul>
            </div>
        `,
        icon: 'info',
        confirmButtonText: 'Close'
    });
}

// ==================== Revenue & Analytics ====================
async function loadRevenueData() {
    try {
        const response = await fetch(`${API_BASE}/orders`);
        const orders = await response.json();
        
        const menuResponse = await fetch(`${API_BASE}/menu`);
        const menu = await menuResponse.json();
        
        calculateRevenueSummary(orders);
        createDailyRevenueChart(orders);
        createCategoryRevenueChart(orders, menu);
        displayTopItems(orders);
        
    } catch (error) {
        console.error('Error loading revenue data:', error);
        showToast('Error loading revenue data', 'error');
    }
}

function calculateRevenueSummary(orders) {
    const totalRevenue = orders.reduce((sum, o) => sum + (o.total_price || 0), 0);
    const avgOrderValue = orders.length > 0 ? (totalRevenue / orders.length) : 0;
    
    document.getElementById('totalRevenue').textContent = totalRevenue.toFixed(2);
    document.getElementById('avgOrderValue').textContent = avgOrderValue.toFixed(2);
    document.getElementById('totalOrdersCount').textContent = orders.length;
    
    // Calculate peak hour from actual order timestamps
    const hourCounts = new Array(24).fill(0);
    orders.forEach(order => {
        if (order.created_at) {
            try {
                const orderDate = new Date(order.created_at);
                const hour = orderDate.getHours();
                hourCounts[hour]++;
            } catch (e) {
                console.error('Error parsing order timestamp:', e);
            }
        }
    });
    
    const maxCount = Math.max(...hourCounts);
    const peakHour = maxCount > 0 ? hourCounts.indexOf(maxCount) : 0;
    document.getElementById('peakHour').textContent = `${peakHour}:00`;
}

function createDailyRevenueChart(orders) {
    const ctx = document.getElementById('dailyRevenueChart');
    if (!ctx) return;
    
    if (charts.dailyRevenue) {
        charts.dailyRevenue.destroy();
    }
    
    // Generate last 7 days
    const days = [];
    const revenues = [];
    
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        const dateString = date.toDateString();
        days.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
        
        // Calculate actual revenue for this date from orders
        const dayRevenue = orders.reduce((sum, order) => {
            if (order.created_at) {
                try {
                    const orderDate = new Date(order.created_at);
                    if (orderDate.toDateString() === dateString) {
                        return sum + (order.total_price || 0);
                    }
                } catch (e) {
                    console.error('Error parsing order date:', e);
                }
            }
            return sum;
        }, 0);
        
        revenues.push(dayRevenue);
    }
    
    const isDark = document.body.classList.contains('dark-mode');
    
    charts.dailyRevenue = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: days,
            datasets: [{
                label: 'Revenue (₹)',
                data: revenues,
                backgroundColor: 'rgba(79, 70, 229, 0.8)',
                borderColor: '#4f46e5',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: isDark ? '#f1f5f9' : '#0f172a'
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Revenue: ₹' + context.parsed.y.toFixed(2);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: isDark ? '#94a3b8' : '#64748b',
                        callback: (value) => '₹' + value.toFixed(0)
                    },
                    grid: {
                        color: isDark ? '#334155' : '#e2e8f0'
                    }
                },
                x: {
                    ticks: {
                        color: isDark ? '#94a3b8' : '#64748b'
                    },
                    grid: {
                        color: isDark ? '#334155' : '#e2e8f0'
                    }
                }
            }
        }
    });
}

function createCategoryRevenueChart(orders, menu) {
    const ctx = document.getElementById('categoryRevenueChart');
    if (!ctx) return;
    
    if (charts.categoryRevenue) {
        charts.categoryRevenue.destroy();
    }
    
    // Calculate revenue by category
    const categoryRevenue = {};
    orders.forEach(order => {
        if (order.items && Array.isArray(order.items)) {
            order.items.forEach(item => {
                const menuItem = menu.find(m => m.id === item.id);
                if (menuItem) {
                    const category = menuItem.category;
                    // Use price from item data (already includes price from backend)
                    const itemPrice = item.price || menuItem.price || 0;
                    categoryRevenue[category] = (categoryRevenue[category] || 0) + (itemPrice * item.qty);
                }
            });
        }
    });
    
    const isDark = document.body.classList.contains('dark-mode');
    
    charts.categoryRevenue = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(categoryRevenue),
            datasets: [{
                data: Object.values(categoryRevenue),
                backgroundColor: [
                    '#4f46e5',
                    '#10b981',
                    '#f59e0b',
                    '#ef4444',
                    '#3b82f6'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: isDark ? '#f1f5f9' : '#0f172a'
                    }
                }
            }
        }
    });
}

function displayTopItems(orders) {
    const tbody = document.getElementById('topItemsTableBody');
    if (!tbody) return;
    
    // Count items and revenue
    const itemStats = {};
    orders.forEach(order => {
        if (order.items && Array.isArray(order.items)) {
            order.items.forEach(item => {
                if (!itemStats[item.name]) {
                    itemStats[item.name] = { qty: 0, revenue: 0 };
                }
                itemStats[item.name].qty += item.qty || 1;
                // Use actual price from order item data
                itemStats[item.name].revenue += (item.price || 0) * (item.qty || 1);
            });
        }
    });
    
    const sorted = Object.entries(itemStats)
        .sort(([,a], [,b]) => b.qty - a.qty)
        .slice(0, 10);
    
    if (sorted.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">No data available</td></tr>';
        return;
    }
    
    tbody.innerHTML = sorted.map(([name, stats], index) => `
        <tr>
            <td><strong>${index + 1}</strong></td>
            <td>${name}</td>
            <td><span class="badge bg-secondary">Category</span></td>
            <td><strong>${stats.qty}</strong></td>
            <td><strong>₹${stats.revenue.toFixed(2)}</strong></td>
        </tr>
    `).join('');
}

// ==================== Export & Download ====================
function downloadReport(type) {
    showToast(`Generating ${type} report...`, 'info');
    
    // Simulate CSV generation
    setTimeout(() => {
        let csvContent = '';
        let filename = '';
        
        switch(type) {
            case 'sales':
                csvContent = 'Order ID,Customer,Email,Items,Total,Status\n';
                if (window.allOrders) {
                    window.allOrders.forEach(order => {
                        const items = order.items?.map(i => i.name).join('; ') || 'N/A';
                        csvContent += `${order.id},${order.customer_name},${order.customer_email},"${items}",${order.total_price},${order.status}\n`;
                    });
                }
                filename = 'sales_report.csv';
                break;
                
            case 'stock':
                csvContent = 'Item Name,Category,Stock,Price,Status\n';
                if (window.allMenuItems) {
                    window.allMenuItems.forEach(item => {
                        const status = item.stock === 0 ? 'Out of Stock' : item.stock <= 10 ? 'Low Stock' : 'In Stock';
                        csvContent += `${item.name},${item.category},${item.stock},${item.price},${status}\n`;
                    });
                }
                filename = 'stock_report.csv';
                break;
                
            case 'users':
                csvContent = 'Email,Role,Status\n';
                if (window.allUsers) {
                    window.allUsers.forEach(user => {
                        csvContent += `${user.email},${user.role},${user.status}\n`;
                    });
                }
                filename = 'users_report.csv';
                break;
                
            case 'analytics':
                csvContent = 'Metric,Value\n';
                csvContent += `Total Orders,${window.allOrders?.length || 0}\n`;
                csvContent += `Total Revenue,₹${window.allOrders?.reduce((sum, o) => sum + o.total_price, 0).toFixed(2) || 0}\n`;
                csvContent += `Active Users,${window.allUsers?.filter(u => u.status === 'approved').length || 0}\n`;
                csvContent += `Menu Items,${window.allMenuItems?.length || 0}\n`;
                filename = 'analytics_report.csv';
                break;
                
            case 'audit':
                csvContent = 'Timestamp,Action,User,Details\n';
                csvContent += `${new Date().toISOString()},System Check,Admin,Report generated\n`;
                filename = 'audit_log.csv';
                break;
        }
        
        // Create download link
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
        
        showToast(`${type} report downloaded successfully`, 'success');
    }, 1000);
}

function backupDatabase() {
    Swal.fire({
        title: 'Database Backup',
        text: 'This will download the college.db file',
        icon: 'info',
        showCancelButton: true,
        confirmButtonText: 'Download Backup',
        cancelButtonText: 'Cancel'
    }).then((result) => {
        if (result.isConfirmed) {
            showToast('Backup feature requires server-side implementation', 'info');
            // In production, implement server endpoint to download database
        }
    });
}

// ==================== Settings ====================
function saveSettings() {
    const refreshInterval = document.getElementById('refreshInterval')?.value || 10;
    localStorage.setItem('refreshInterval', refreshInterval);
    
    const collegeName = document.getElementById('collegeName')?.value || '';
    const batchInfo = document.getElementById('batchInfo')?.value || '';
    localStorage.setItem('collegeName', collegeName);
    localStorage.setItem('batchInfo', batchInfo);
    
    showToast('Settings saved successfully', 'success');
    
    // Restart auto-refresh with new interval
    if (document.getElementById('autoRefresh')?.checked) {
        startAutoRefresh();
    }
}

// ==================== Auto Refresh ====================
function startAutoRefresh() {
    stopAutoRefresh();
    
    const interval = parseInt(document.getElementById('refreshInterval')?.value || 10) * 1000;
    
    autoRefreshInterval = setInterval(() => {
        const activeSection = document.querySelector('.nav-link.active')?.dataset.section;
        if (activeSection === 'dashboard') {
            loadDashboardData();
        }
    }, interval);
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

// ==================== Utility Functions ====================
function updateDateTime() {
    const now = new Date();
    const options = {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    };
    
    document.getElementById('currentDateTime').textContent = now.toLocaleDateString('en-US', options);
}

function showToast(message, type = 'info') {
    const bgColors = {
        success: 'linear-gradient(to right, #10b981, #059669)',
        error: 'linear-gradient(to right, #ef4444, #dc2626)',
        warning: 'linear-gradient(to right, #f59e0b, #d97706)',
        info: 'linear-gradient(to right, #3b82f6, #2563eb)'
    };
    
    Toastify({
        text: message,
        duration: 3000,
        gravity: 'top',
        position: 'right',
        style: {
            background: bgColors[type] || bgColors.info
        }
    }).showToast();
}

// Make functions globally available
window.approveUser = approveUser;
window.editUser = editUser;
window.deleteUser = deleteUser;
window.editMenuItem = editMenuItem;
window.deleteMenuItem = deleteMenuItem;
window.quickRestock = quickRestock;
window.viewOrderDetails = viewOrderDetails;
window.downloadReport = downloadReport;
