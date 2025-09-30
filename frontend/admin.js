/**
 * Enhanced Admin Dashboard JavaScript
 * College Kiosk Management System
 * 
 * Features:
 * - Real-time data updates with live polling
 * - Advanced charts and analytics
 * - Comprehensive reporting with CSV/PDF export
 * - Audit logging system
 * - Bulk operations for all entities
 * - Low-stock alerts and notifications
 * - Search and filtering capabilities
 * - Responsive design with mobile support
 */

class EnhancedAdminApp {
    constructor() {
        this.currentPage = 'dashboard';
        this.charts = {};
        this.refreshInterval = null;
        this.currentAdmin = 'admin'; // This would come from login session
        this.lowStockThreshold = 5;
        this.selectedItems = new Set();
        this.currentReportData = null;
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.startClock();
        this.startServerStatusCheck();
        this.startDataRefresh();
        
        // Load initial data
        await this.loadDashboardData();
        this.showPage('dashboard');
        
        console.log('Enhanced Admin Dashboard initialized');
    }

    setupEventListeners() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.showPage(page);
            });
        });

        // Mobile menu toggle
        document.getElementById('mobileMenuBtn')?.addEventListener('click', () => {
            document.getElementById('sidebar').classList.toggle('mobile-open');
        });

        // Theme toggle
        document.getElementById('themeToggleBtn')?.addEventListener('click', () => {
            this.toggleTheme();
        });

        // Notifications
        document.getElementById('notificationBtn')?.addEventListener('click', () => {
            this.toggleNotificationCenter();
        });

        document.getElementById('closeNotifications')?.addEventListener('click', () => {
            this.hideNotificationCenter();
        });

        // Refresh button
        document.getElementById('refreshBtn')?.addEventListener('click', () => {
            this.refreshCurrentPage();
        });

        // Logout
        document.getElementById('logoutBtn')?.addEventListener('click', () => {
            this.handleLogout();
        });

        // Modal system
        document.getElementById('modalOverlay')?.addEventListener('click', (e) => {
            if (e.target.id === 'modalOverlay') {
                this.hideModal();
            }
        });

        // Setup page-specific event listeners
        this.setupOrdersEventListeners();
        this.setupMenuEventListeners();
        this.setupUsersEventListeners();
        this.setupReportsEventListeners();
        this.setupAuditLogsEventListeners();
    }

    setupOrdersEventListeners() {
        // Order search and filters
        document.getElementById('orderSearch')?.addEventListener('input', () => {
            this.filterOrders();
        });

        document.getElementById('orderStatusFilter')?.addEventListener('change', () => {
            this.filterOrders();
        });

        document.getElementById('orderDateFrom')?.addEventListener('change', () => {
            this.filterOrders();
        });

        document.getElementById('orderDateTo')?.addEventListener('change', () => {
            this.filterOrders();
        });

        document.getElementById('clearOrderFilters')?.addEventListener('click', () => {
            this.clearOrderFilters();
        });

        // Bulk operations
        document.getElementById('selectAllOrders')?.addEventListener('change', (e) => {
            this.toggleSelectAllOrders(e.target.checked);
        });

        document.getElementById('bulkOrderActionBtn')?.addEventListener('click', () => {
            this.showBulkOrderStatusModal();
        });

        document.getElementById('exportOrdersBtn')?.addEventListener('click', () => {
            this.exportOrders();
        });
    }

    setupMenuEventListeners() {
        // Menu search and filters
        document.getElementById('menuSearch')?.addEventListener('input', () => {
            this.filterMenu();
        });

        document.getElementById('menuCategoryFilter')?.addEventListener('change', () => {
            this.filterMenu();
        });

        document.getElementById('menuStockFilter')?.addEventListener('change', () => {
            this.filterMenu();
        });

        // Menu view toggle
        document.getElementById('toggleMenuViewBtn')?.addEventListener('click', () => {
            this.toggleMenuView();
        });

        // Bulk operations
        document.getElementById('selectAllMenu')?.addEventListener('change', (e) => {
            this.toggleSelectAllMenu(e.target.checked);
        });

        document.getElementById('bulkDeleteMenuBtn')?.addEventListener('click', () => {
            this.bulkDeleteMenuItems();
        });

        document.getElementById('addMenuItemBtn')?.addEventListener('click', () => {
            this.showAddMenuItemModal();
        });

        document.getElementById('exportMenuBtn')?.addEventListener('click', () => {
            this.exportMenu();
        });
    }

    setupUsersEventListeners() {
        // User search and filters
        document.getElementById('userSearch')?.addEventListener('input', () => {
            this.filterUsers();
        });

        document.getElementById('userRoleFilter')?.addEventListener('change', () => {
            this.filterUsers();
        });

        document.getElementById('userStatusFilter')?.addEventListener('change', () => {
            this.filterUsers();
        });

        // Bulk operations
        document.getElementById('selectAllUsers')?.addEventListener('change', (e) => {
            this.toggleSelectAllUsers(e.target.checked);
        });

        document.getElementById('bulkApproveBtn')?.addEventListener('click', () => {
            this.bulkApproveUsers();
        });

        document.getElementById('bulkDeleteUsersBtn')?.addEventListener('click', () => {
            this.bulkDeleteUsers();
        });

        document.getElementById('exportUsersBtn')?.addEventListener('click', () => {
            this.exportUsers();
        });

        // Chart export buttons
        document.getElementById('salesTrendExport')?.addEventListener('click', () => {
            this.exportChart('salesTrend', 'Sales Trend');
        });

        document.getElementById('orderStatusExport')?.addEventListener('click', () => {
            this.exportChart('orderStatus', 'Order Status Distribution');
        });

        document.getElementById('topItemsExport')?.addEventListener('click', () => {
            this.exportChart('topItems', 'Top Selling Items');
        });

        document.getElementById('categorySalesExport')?.addEventListener('click', () => {
            this.exportChart('categorySales', 'Category-wise Sales');
        });
    }

    setupReportsEventListeners() {
        document.getElementById('generateReportBtn')?.addEventListener('click', () => {
            this.generateReport();
        });

        document.getElementById('exportReportBtn')?.addEventListener('click', () => {
            this.exportCurrentReport();
        });

        document.getElementById('reportType')?.addEventListener('change', () => {
            this.clearReportData();
        });
    }

    setupAuditLogsEventListeners() {
        // Audit log search and filters
        document.getElementById('auditLogSearch')?.addEventListener('input', () => {
            this.filterAuditLogs();
        });

        document.getElementById('auditActionFilter')?.addEventListener('change', () => {
            this.filterAuditLogs();
        });

        document.getElementById('auditDateFrom')?.addEventListener('change', () => {
            this.filterAuditLogs();
        });

        document.getElementById('auditDateTo')?.addEventListener('change', () => {
            this.filterAuditLogs();
        });

        document.getElementById('exportAuditLogsBtn')?.addEventListener('click', () => {
            this.exportAuditLogs();
        });
    }

    // Navigation and Page Management
    async showPage(page) {
        // Hide all pages
        document.querySelectorAll('.page-content').forEach(p => p.classList.add('hidden'));
        
        // Show selected page
        const pageElement = document.getElementById(`${page}-page`);
        if (pageElement) {
            pageElement.classList.remove('hidden');
        }

        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.page === page) {
                item.classList.add('active');
            }
        });

        // Update page title
        const titles = {
            dashboard: 'Dashboard',
            orders: 'Order Management',
            menu: 'Menu Management',
            users: 'User Management',
            reports: 'Reports & Analytics',
            'audit-logs': 'Audit Logs'
        };
        
        document.getElementById('pageTitle').textContent = titles[page] || 'Admin Dashboard';
        this.currentPage = page;

        // Load page data
        await this.loadPageData(page);
    }

    async loadPageData(page) {
        try {
            switch (page) {
                case 'dashboard':
                    await this.loadDashboardData();
                    break;
                case 'orders':
                    await this.loadOrdersData();
                    break;
                case 'menu':
                    await this.loadMenuData();
                    break;
                case 'users':
                    await this.loadUsersData();
                    break;
                case 'audit-logs':
                    await this.loadAuditLogsData();
                    break;
            }
        } catch (error) {
            console.error(`Error loading ${page} data:`, error);
            this.showToast(`Error loading ${page} data`, 'error');
        }
    }

    // Dashboard Data Loading
    async loadDashboardData() {
        try {
            const response = await fetch('/api/dashboard/stats');
            const data = await response.json();

            if (response.ok) {
                this.updateKPICards(data.kpi);
                this.updateCharts(data.charts);
                await this.updateRecentOrders();
                this.updateNotificationBadges(data.kpi);
                
                // Show success feedback
                this.showToast('Dashboard data refreshed', 'success');
            } else {
                throw new Error(`HTTP ${response.status}: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Dashboard data error:', error);
            this.showToast('Failed to load dashboard data', 'error');
            
            // Set default values if data fails to load
            this.updateKPICards({
                total_orders: 0,
                total_revenue: 0,
                active_orders: 0,
                pending_approvals: 0,
                low_stock_items: 0
            });
        }
    }

    updateKPICards(kpi) {
        document.getElementById('totalOrders').textContent = kpi.total_orders || 0;
        document.getElementById('totalRevenue').textContent = `₹${kpi.total_revenue || 0}`;
        document.getElementById('activeOrders').textContent = kpi.active_orders || 0;
        document.getElementById('pendingApprovals').textContent = kpi.pending_approvals || 0;
        document.getElementById('lowStockCount').textContent = kpi.low_stock_items || 0;

        // Update badges in sidebar
        document.getElementById('activeOrdersBadge').textContent = kpi.active_orders || 0;
        document.getElementById('lowStockBadge').textContent = kpi.low_stock_items || 0;
        document.getElementById('pendingUsersBadge').textContent = kpi.pending_approvals || 0;
    }

    updateCharts(chartData) {
        // Store current chart data for theme switching
        this.currentChartData = chartData;
        
        // Sales Trend Chart
        this.createSalesTrendChart(chartData.sales_trend || []);
        
        // Order Status Distribution Chart
        this.createOrderStatusChart(chartData.status_distribution || {});
        
        // Top Items Chart
        this.createTopItemsChart(chartData.top_items || []);
        
        // Category Sales Chart (if available)
        if (chartData.category_sales) {
            this.createCategorySalesChart(chartData.category_sales);
        }
    }

    async updateRecentOrders() {
        try {
            const response = await fetch('/api/orders?limit=5');
            const orders = await response.json();
            
            const recentOrdersList = document.getElementById('recentOrdersList');
            if (!recentOrdersList) return;

            if (response.ok && orders.length > 0) {
                recentOrdersList.innerHTML = orders.map(order => `
                    <div class="recent-order-item">
                        <div class="order-info">
                            <div class="order-id">#${order.id}</div>
                            <div class="order-customer">${order.customer_name}</div>
                            <div class="order-total">₹${order.total_price}</div>
                        </div>
                        <div class="order-status">
                            <span class="status-badge ${this.getStatusClass(order.status)}">${order.status}</span>
                        </div>
                    </div>
                `).join('');
            } else {
                recentOrdersList.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-shopping-cart"></i>
                        <p>No recent orders</p>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Recent orders error:', error);
            const recentOrdersList = document.getElementById('recentOrdersList');
            if (recentOrdersList) {
                recentOrdersList.innerHTML = `
                    <div class="error-state">
                        <i class="fas fa-exclamation-triangle"></i>
                        <p>Failed to load recent orders</p>
                    </div>
                `;
            }
        }
    }

    createSalesTrendChart(salesData) {
        const ctx = document.getElementById('salesTrendChart');
        if (!ctx) return;

        if (this.charts.salesTrend) {
            this.charts.salesTrend.destroy();
        }

        // Handle empty data
        if (!salesData || salesData.length === 0) {
            const parentElement = ctx.parentElement;
            parentElement.innerHTML = `
                <div class="empty-chart-state">
                    <i class="fas fa-chart-line"></i>
                    <p>No sales data available</p>
                    <small>Sales data will appear here once orders are placed</small>
                </div>
            `;
            return;
        }

        const labels = salesData.map(item => new Date(item.date).toLocaleDateString());
        const orders = salesData.map(item => item.orders || 0);
        const revenue = salesData.map(item => item.revenue || 0);

        // Get CSS custom properties for theme-aware colors
        const computedStyle = getComputedStyle(document.documentElement);
        const primaryColor = computedStyle.getPropertyValue('--primary').trim();
        const successColor = computedStyle.getPropertyValue('--success').trim();
        const textColor = computedStyle.getPropertyValue('--text').trim();
        const borderColor = computedStyle.getPropertyValue('--border').trim();

        this.charts.salesTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Orders',
                        data: orders,
                        borderColor: primaryColor,
                        backgroundColor: primaryColor + '20',
                        tension: 0.4,
                        yAxisID: 'y',
                        fill: true
                    },
                    {
                        label: 'Revenue (₹)',
                        data: revenue,
                        borderColor: successColor,
                        backgroundColor: successColor + '20',
                        tension: 0.4,
                        yAxisID: 'y1',
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: {
                        labels: {
                            color: textColor
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: textColor
                        },
                        grid: {
                            color: borderColor
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        ticks: {
                            color: textColor
                        },
                        grid: {
                            color: borderColor
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        ticks: {
                            color: textColor
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    },
                }
            }
        });
    }

    createOrderStatusChart(statusData) {
        const ctx = document.getElementById('orderStatusChart');
        if (!ctx) return;

        if (this.charts.orderStatus) {
            this.charts.orderStatus.destroy();
        }

        // Handle empty data
        if (!statusData || Object.keys(statusData).length === 0) {
            const parentElement = ctx.parentElement;
            parentElement.innerHTML = `
                <div class="empty-chart-state">
                    <i class="fas fa-chart-pie"></i>
                    <p>No order status data</p>
                    <small>Order status distribution will appear here</small>
                </div>
            `;
            return;
        }

        const labels = Object.keys(statusData);
        const data = Object.values(statusData);
        
        // Get CSS custom properties for theme-aware colors
        const computedStyle = getComputedStyle(document.documentElement);
        const colors = [
            computedStyle.getPropertyValue('--warning').trim(),
            computedStyle.getPropertyValue('--info').trim(),
            computedStyle.getPropertyValue('--primary').trim(),
            computedStyle.getPropertyValue('--success').trim(),
            computedStyle.getPropertyValue('--danger').trim()
        ];
        const textColor = computedStyle.getPropertyValue('--text').trim();
        const surfaceColor = computedStyle.getPropertyValue('--surface').trim();

        this.charts.orderStatus = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderWidth: 3,
                    borderColor: surfaceColor,
                    hoverBorderWidth: 4,
                    hoverBorderColor: textColor
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: textColor,
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    tooltip: {
                        backgroundColor: surfaceColor,
                        titleColor: textColor,
                        bodyColor: textColor,
                        borderColor: colors[0],
                        borderWidth: 1
                    }
                }
            }
        });
    }

    createTopItemsChart(topItems) {
        const ctx = document.getElementById('topItemsChart');
        if (!ctx) return;

        if (this.charts.topItems) {
            this.charts.topItems.destroy();
        }

        // Handle empty data
        if (!topItems || topItems.length === 0) {
            const parentElement = ctx.parentElement;
            parentElement.innerHTML = `
                <div class="empty-chart-state">
                    <i class="fas fa-chart-bar"></i>
                    <p>No top selling items data</p>
                    <small>Popular items will appear here</small>
                </div>
            `;
            return;
        }

        const labels = topItems.map(item => item.name);
        const data = topItems.map(item => item.orders || 0);

        // Get CSS custom properties for theme-aware colors
        const computedStyle = getComputedStyle(document.documentElement);
        const primaryColor = computedStyle.getPropertyValue('--primary').trim();
        const textColor = computedStyle.getPropertyValue('--text').trim();
        const borderColor = computedStyle.getPropertyValue('--border').trim();

        this.charts.topItems = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Orders',
                    data: data,
                    backgroundColor: primaryColor + '40',
                    borderColor: primaryColor,
                    borderWidth: 2,
                    borderRadius: 4,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: computedStyle.getPropertyValue('--surface').trim(),
                        titleColor: textColor,
                        bodyColor: textColor,
                        borderColor: primaryColor,
                        borderWidth: 1
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: textColor
                        },
                        grid: {
                            color: borderColor
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: textColor
                        },
                        grid: {
                            color: borderColor
                        }
                    }
                }
            }
        });
    }

    // Orders Management
    async loadOrdersData() {
        try {
            const response = await fetch('/api/orders');
            const orders = await response.json();

            if (response.ok) {
                this.renderOrdersTable(orders);
            }
        } catch (error) {
            console.error('Orders data error:', error);
        }
    }

    renderOrdersTable(orders) {
        const tbody = document.getElementById('ordersTableBody');
        if (!tbody) return;

        if (orders.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="empty-state">
                        <i class="fas fa-shopping-cart"></i>
                        <p>No orders found</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = orders.map(order => {
            const items = this.parseOrderItems(order.items);
            const statusClass = this.getStatusClass(order.status);
            
            return `
                <tr data-order-id="${order.id}">
                    <td>
                        <input type="checkbox" class="order-checkbox" value="${order.id}">
                    </td>
                    <td><strong>#${order.id}</strong></td>
                    <td>
                        <div class="customer-info">
                            <div class="customer-name">${order.customer_name}</div>
                            <div class="customer-email">${order.customer_email}</div>
                        </div>
                    </td>
                    <td>
                        <div class="order-items">
                            ${items.slice(0, 2).map(item => `<span class="item-tag">${item.name} (${item.quantity})</span>`).join('')}
                            ${items.length > 2 ? `<span class="more-items">+${items.length - 2} more</span>` : ''}
                        </div>
                    </td>
                    <td><strong>₹${order.total_price}</strong></td>
                    <td>
                        <span class="status-badge ${statusClass}">${order.status}</span>
                    </td>
                    <td>
                        <div class="date-info">
                            <div>${this.formatDate(order.created_at)}</div>
                            <div class="text-muted">${this.formatTime(order.created_at)}</div>
                        </div>
                    </td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn btn-sm btn-outline" onclick="adminApp.showOrderDetails(${order.id})" title="View Details">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-primary" onclick="adminApp.updateOrderStatus(${order.id})" title="Update Status">
                                <i class="fas fa-edit"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        // Setup order checkboxes
        this.setupOrderCheckboxes();
    }

    parseOrderItems(itemsString) {
        try {
            const parsed = JSON.parse(itemsString);
            return parsed.items || [];
        } catch {
            return [];
        }
    }

    getStatusClass(status) {
        const statusClasses = {
            'Order Received': 'warning',
            'Preparing': 'info',
            'Ready for Pickup': 'primary',
            'Completed': 'success',
            'Cancelled': 'danger'
        };
        return statusClasses[status] || 'secondary';
    }

    setupOrderCheckboxes() {
        document.querySelectorAll('.order-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                if (checkbox.checked) {
                    this.selectedItems.add(checkbox.value);
                } else {
                    this.selectedItems.delete(checkbox.value);
                }
                this.updateBulkActionButtons();
            });
        });
    }

    updateBulkOrderButton() {
        const selectedOrders = document.querySelectorAll('.order-checkbox:checked');
        const bulkBtn = document.getElementById('bulkOrderActionBtn');
        
        if (bulkBtn) {
            bulkBtn.disabled = selectedOrders.length === 0;
        }
    }

    async updateOrderStatus(orderId) {
        const modal = this.showModal('Update Order Status', `
            <form id="updateOrderStatusForm">
                <div class="form-group">
                    <label class="form-label">New Status</label>
                    <select id="newOrderStatus" class="form-select" required>
                        <option value="Order Received">Order Received</option>
                        <option value="Preparing">Preparing</option>
                        <option value="Ready for Pickup">Ready for Pickup</option>
                        <option value="Completed">Completed</option>
                        <option value="Cancelled">Cancelled</option>
                    </select>
                </div>
                <div class="modal-actions">
                    <button type="button" class="btn btn-outline" onclick="adminApp.hideModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary">Update Status</button>
                </div>
            </form>
        `);

        document.getElementById('updateOrderStatusForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const newStatus = document.getElementById('newOrderStatus').value;
            
            try {
                const response = await fetch(`/api/orders/${orderId}/status`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        status: newStatus,
                        admin_email: this.currentAdmin
                    })
                });

                if (response.ok) {
                    this.showToast('Order status updated successfully', 'success');
                    this.hideModal();
                    await this.loadOrdersData();
                } else {
                    throw new Error('Failed to update order status');
                }
            } catch (error) {
                this.showToast('Error updating order status', 'error');
            }
        });
    }

    // Menu Management
    async loadMenuData() {
        try {
            const response = await fetch('/api/menu');
            const menuItems = await response.json();

            if (response.ok) {
                this.renderMenuItems(menuItems);
                this.populateMenuCategories(menuItems);
            }
        } catch (error) {
            console.error('Menu data error:', error);
        }
    }

    renderMenuItems(menuItems) {
        const isGridView = !document.getElementById('menuTableView').classList.contains('hidden');
        
        if (isGridView) {
            this.renderMenuGrid(menuItems);
        } else {
            this.renderMenuTable(menuItems);
        }
    }

    renderMenuGrid(menuItems) {
        const container = document.getElementById('menuGridView');
        if (!container) return;

        if (menuItems.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-utensils"></i>
                    <p>No menu items found</p>
                </div>
            `;
            return;
        }

        container.innerHTML = menuItems.map(item => {
            const lowStock = item.stock < this.lowStockThreshold;
            const stockClass = lowStock ? 'low-stock' : (item.stock === 0 ? 'out-of-stock' : '');
            
            return `
                <div class="menu-card ${stockClass}" data-item-id="${item.id}">
                    <div class="menu-card-header">
                        <input type="checkbox" class="menu-checkbox" value="${item.id}">
                        <div class="menu-card-image">
                            <img src="/static/images/${item.image}" alt="${item.name}" onerror="this.src='/static/images/placeholder.jpg'">
                        </div>
                    </div>
                    <div class="menu-card-body">
                        <h4 class="menu-card-title">${item.name}</h4>
                        <p class="menu-card-category">${item.category}</p>
                        <div class="menu-card-details">
                            <div class="price">₹${item.price}</div>
                            <div class="stock ${stockClass}">
                                <i class="fas fa-box"></i>
                                ${item.stock} in stock
                                ${lowStock ? '<i class="fas fa-exclamation-triangle warning-icon"></i>' : ''}
                            </div>
                        </div>
                        <div class="menu-card-status">
                            <span class="availability-badge ${item.available ? 'available' : 'unavailable'}">
                                ${item.available ? 'Available' : 'Unavailable'}
                            </span>
                            ${item.deliverable ? '<span class="deliverable-badge">Deliverable</span>' : ''}
                        </div>
                    </div>
                    <div class="menu-card-actions">
                        <button class="btn btn-sm btn-outline" onclick="adminApp.editMenuItem(${item.id})" title="Edit">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-sm btn-primary" onclick="adminApp.toggleMenuAvailability(${item.id})" title="Toggle Availability">
                            <i class="fas fa-power-off"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="adminApp.deleteMenuItem(${item.id})" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        this.setupMenuCheckboxes();
    }

    populateMenuCategories(menuItems) {
        const categoryFilter = document.getElementById('menuCategoryFilter');
        if (!categoryFilter) return;

        const categories = [...new Set(menuItems.map(item => item.category))];
        
        categoryFilter.innerHTML = '<option value="">All Categories</option>' +
            categories.map(cat => `<option value="${cat}">${cat}</option>`).join('');
    }

    setupMenuCheckboxes() {
        document.querySelectorAll('.menu-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateBulkMenuButtons();
            });
        });
    }

    updateBulkMenuButtons() {
        const selectedItems = document.querySelectorAll('.menu-checkbox:checked');
        const bulkDeleteBtn = document.getElementById('bulkDeleteMenuBtn');
        
        if (bulkDeleteBtn) {
            bulkDeleteBtn.disabled = selectedItems.length === 0;
        }
    }

    renderMenuTable(menuItems) {
        const tbody = document.getElementById('menuTableBody');
        if (!tbody) return;

        if (menuItems.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center">No menu items found</td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = menuItems.map(item => {
            const lowStock = item.stock < this.lowStockThreshold;
            const stockClass = lowStock ? 'low-stock' : (item.stock === 0 ? 'out-of-stock' : '');
            
            return `
                <tr data-item-id="${item.id}">
                    <td><input type="checkbox" class="menu-checkbox" value="${item.id}"></td>
                    <td>
                        <div class="menu-image">
                            <img src="/static/images/${item.image}" alt="${item.name}" onerror="this.src='/static/images/placeholder.jpg'">
                        </div>
                    </td>
                    <td>
                        <div class="menu-item-info">
                            <div class="item-name">${item.name}</div>
                            <div class="item-category text-muted">${item.category}</div>
                        </div>
                    </td>
                    <td>${item.category}</td>
                    <td><strong>₹${item.price}</strong></td>
                    <td>
                        <span class="stock-info ${stockClass}">
                            ${item.stock}
                            ${lowStock ? '<i class="fas fa-exclamation-triangle warning-icon"></i>' : ''}
                        </span>
                    </td>
                    <td>
                        <span class="availability-badge ${item.available ? 'available' : 'unavailable'}">
                            ${item.available ? 'Available' : 'Unavailable'}
                        </span>
                        ${item.deliverable ? '<span class="deliverable-badge">Deliverable</span>' : ''}
                    </td>
                    <td>
                        <div class="action-buttons">
                            <button class="btn btn-sm btn-outline" onclick="adminApp.editMenuItem(${item.id})" title="Edit">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-primary" onclick="adminApp.toggleMenuAvailability(${item.id})" title="Toggle Availability">
                                <i class="fas fa-power-off"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="adminApp.deleteMenuItem(${item.id})" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        this.setupMenuCheckboxes();
    }

    // User Management
    async loadUsersData() {
        try {
            const response = await fetch('/api/users');
            const users = await response.json();

            if (response.ok) {
                this.renderUsersTable(users);
            }
        } catch (error) {
            console.error('Users data error:', error);
        }
    }

    renderUsersTable(users) {
        const tbody = document.getElementById('usersTableBody');
        if (!tbody) return;

        if (users.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="empty-state">
                        <i class="fas fa-users"></i>
                        <p>No users found</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = users.map(user => {
            const statusClass = user.status === 'approved' ? 'success' : 'warning';
            const roleClass = user.role === 'admin' ? 'danger' : (user.role === 'staff' ? 'info' : 'secondary');
            
            return `
                <tr data-user-email="${user.email}">
                    <td>
                        <input type="checkbox" class="user-checkbox" value="${user.email}">
                    </td>
                    <td>${user.name || 'N/A'}</td>
                    <td>${user.email}</td>
                    <td>
                        <span class="role-badge ${roleClass}">${user.role}</span>
                    </td>
                    <td>
                        <span class="status-badge ${statusClass}">${user.status}</span>
                    </td>
                    <td>
                        ${this.formatDate(user.created_at)}
                    </td>
                    <td>
                        <div class="action-buttons">
                            ${user.status === 'pending' ? `
                                <button class="btn btn-sm btn-success" onclick="adminApp.approveUser('${user.email}')" title="Approve">
                                    <i class="fas fa-check"></i>
                                </button>
                            ` : ''}
                            <button class="btn btn-sm btn-info" onclick="adminApp.assignRole('${user.email}')" title="Assign Role">
                                <i class="fas fa-user-tag"></i>
                            </button>
                            <button class="btn btn-sm btn-danger" onclick="adminApp.deleteUser('${user.email}')" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');

        this.setupUserCheckboxes();
    }

    setupUserCheckboxes() {
        document.querySelectorAll('.user-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateBulkUserButtons();
            });
        });
    }

    updateBulkUserButtons() {
        const selectedUsers = document.querySelectorAll('.user-checkbox:checked');
        const bulkApproveBtn = document.getElementById('bulkApproveBtn');
        const bulkDeleteBtn = document.getElementById('bulkDeleteUsersBtn');
        
        if (bulkApproveBtn) {
            bulkApproveBtn.disabled = selectedUsers.length === 0;
        }
        if (bulkDeleteBtn) {
            bulkDeleteBtn.disabled = selectedUsers.length === 0;
        }
    }

    async approveUser(email) {
        try {
            const response = await fetch('/api/users/approve-audit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    email: email,
                    role: 'user',
                    admin_email: this.currentAdmin
                })
            });

            if (response.ok) {
                this.showToast('User approved successfully', 'success');
                await this.loadUsersData();
                await this.loadDashboardData(); // Update badges
            } else {
                throw new Error('Failed to approve user');
            }
        } catch (error) {
            this.showToast('Error approving user', 'error');
        }
    }

    // Reports Management
    async generateReport() {
        const reportType = document.getElementById('reportType').value;
        const fromDate = document.getElementById('reportFromDate').value;
        const toDate = document.getElementById('reportToDate').value;

        try {
            let url = `/api/reports/${reportType}`;
            const params = new URLSearchParams();
            
            if (fromDate) params.append('start_date', fromDate);
            if (toDate) params.append('end_date', toDate);
            
            if (params.toString()) {
                url += `?${params.toString()}`;
            }

            const response = await fetch(url);
            const data = await response.json();

            if (response.ok) {
                this.currentReportData = data;
                this.renderReportData(reportType, data);
                document.getElementById('exportReportBtn').disabled = false;
            } else {
                throw new Error('Failed to generate report');
            }
        } catch (error) {
            this.showToast('Error generating report', 'error');
        }
    }

    renderReportData(reportType, data) {
        const reportTitle = document.getElementById('reportTitle');
        const reportSummary = document.getElementById('reportSummary');
        const reportData = document.getElementById('reportData');

        // Update title
        const titles = {
            orders: 'Orders Report',
            users: 'Users Report',
            menu: 'Menu Report'
        };
        reportTitle.textContent = titles[reportType];

        // Render summary
        this.renderReportSummary(reportType, data.summary);

        // Render detailed data
        this.renderReportDetails(reportType, data);
    }

    renderReportSummary(reportType, summary) {
        const container = document.getElementById('reportSummary');
        
        let summaryCards = '';
        
        switch (reportType) {
            case 'orders':
                summaryCards = `
                    <div class="summary-card">
                        <div class="summary-value">${summary.total_orders}</div>
                        <div class="summary-label">Total Orders</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-value">₹${summary.total_revenue}</div>
                        <div class="summary-label">Total Revenue</div>
                    </div>
                    <div class="summary-card">
                        <div class="summary-value">₹${summary.avg_order_value}</div>
                        <div class="summary-label">Average Order Value</div>
                    </div>
                `;
                break;
            case 'users':
                summaryCards = `
                    <div class="summary-card">
                        <div class="summary-value">${summary.total_users}</div>
                        <div class="summary-label">Total Users</div>
                    </div>
                `;
                break;
            case 'menu':
                summaryCards = `
                    <div class="summary-card">
                        <div class="summary-value">${summary.total_items}</div>
                        <div class="summary-label">Total Items</div>
                    </div>
                    <div class="summary-card warning">
                        <div class="summary-value">${summary.low_stock_items}</div>
                        <div class="summary-label">Low Stock Items</div>
                    </div>
                `;
                break;
        }
        
        container.innerHTML = summaryCards;
    }

    // Audit Logs Management
    async loadAuditLogsData(page = 1) {
        try {
            const params = new URLSearchParams({ page: page.toString() });
            
            // Add filters
            const search = document.getElementById('auditLogSearch')?.value;
            const action = document.getElementById('auditActionFilter')?.value;
            const fromDate = document.getElementById('auditDateFrom')?.value;
            const toDate = document.getElementById('auditDateTo')?.value;
            
            if (search) params.append('search', search);
            if (action) params.append('action', action);
            if (fromDate) params.append('start_date', fromDate);
            if (toDate) params.append('end_date', toDate);

            const response = await fetch(`/api/audit-logs?${params.toString()}`);
            const data = await response.json();

            if (response.ok) {
                this.renderAuditLogsTable(data.logs);
                this.renderAuditLogsPagination(data.pagination);
            }
        } catch (error) {
            console.error('Audit logs error:', error);
        }
    }

    renderAuditLogsTable(logs) {
        const tbody = document.getElementById('auditLogsTableBody');
        if (!tbody) return;

        if (logs.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="empty-state">
                        <i class="fas fa-history"></i>
                        <p>No audit logs found</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = logs.map(log => `
            <tr>
                <td>
                    <div class="date-info">
                        <div>${new Date(log.timestamp).toLocaleDateString()}</div>
                        <div class="text-muted">${new Date(log.timestamp).toLocaleTimeString()}</div>
                    </div>
                </td>
                <td>${log.admin_email}</td>
                <td>
                    <span class="action-badge">${this.formatActionName(log.action)}</span>
                </td>
                <td>${log.target}</td>
                <td>${log.details}</td>
            </tr>
        `).join('');
    }

    formatActionName(action) {
        return action.replace(/_/g, ' ').toLowerCase()
            .replace(/\b\w/g, l => l.toUpperCase());
    }

    // Utility Methods
    async refreshCurrentPage() {
        const refreshBtn = document.getElementById('refreshBtn');
        const icon = refreshBtn?.querySelector('i');
        
        if (icon) {
            icon.classList.add('fa-spin');
        }

        try {
            await this.loadPageData(this.currentPage);
            this.showToast('Data refreshed successfully', 'success');
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showToast('Error refreshing data', 'error');
        } finally {
            if (icon) {
                icon.classList.remove('fa-spin');
            }
        }
    }

    async loadPageData(page) {
        switch (page) {
            case 'dashboard':
                await this.loadDashboardData();
                break;
            case 'orders':
                await this.loadOrdersData();
                break;
            case 'menu':
                await this.loadMenuData();
                break;
            case 'users':
                await this.loadUsersData();
                break;
            case 'reports':
                // Reports page doesn't need auto-refresh
                break;
            case 'audit-logs':
                await this.loadAuditLogsData();
                break;
            default:
                await this.loadDashboardData();
        }
    }

    startClock() {
        const updateClock = () => {
            const now = new Date();
            const timeStr = now.toLocaleTimeString();
            const dateStr = now.toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
            });
            
            document.getElementById('clockTime').textContent = timeStr;
            document.getElementById('clockDate').textContent = dateStr;
        };

        updateClock();
        setInterval(updateClock, 1000);
    }

    startServerStatusCheck() {
        const checkStatus = async () => {
            try {
                const response = await fetch('/api/dashboard/stats');
                const statusDot = document.getElementById('statusDot');
                const statusText = document.getElementById('statusText');
                
                if (response.ok) {
                    statusDot.className = 'status-dot online';
                    statusText.textContent = 'Online';
                } else {
                    statusDot.className = 'status-dot offline';
                    statusText.textContent = 'Issues';
                }
            } catch (error) {
                const statusDot = document.getElementById('statusDot');
                const statusText = document.getElementById('statusText');
                statusDot.className = 'status-dot offline';
                statusText.textContent = 'Offline';
            }
        };

        checkStatus();
        setInterval(checkStatus, 30000); // Check every 30 seconds
    }

    startDataRefresh() {
        // Auto-refresh every 60 seconds
        this.refreshInterval = setInterval(() => {
            if (this.currentPage === 'dashboard') {
                this.loadDashboardData();
            }
        }, 60000);
    }

    updateNotificationBadges(kpi) {
        const totalNotifications = (kpi.pending_approvals || 0) + (kpi.low_stock_items || 0) + (kpi.active_orders || 0);
        const badge = document.getElementById('notificationBadge');
        
        if (badge) {
            badge.textContent = totalNotifications;
            badge.style.display = totalNotifications > 0 ? 'flex' : 'none';
        }
    }

    showModal(title, content) {
        const overlay = document.getElementById('modalOverlay');
        const modalContent = document.getElementById('modalContent');
        
        modalContent.innerHTML = `
            <div class="modal-header">
                <h3 class="modal-title">${title}</h3>
                <button class="modal-close" onclick="adminApp.hideModal()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body">
                ${content}
            </div>
        `;
        
        overlay.classList.remove('hidden');
        return modalContent;
    }

    hideModal() {
        document.getElementById('modalOverlay').classList.add('hidden');
    }

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        const toastMessage = document.getElementById('toast-message');
        
        toastMessage.textContent = message;
        toast.className = `toast ${type}`;
        toast.classList.add('show');
        
        setTimeout(() => {
            toast.classList.remove('show');
        }, 3000);
    }

    toggleTheme() {
        document.body.classList.toggle('theme-dark');
        const icon = document.getElementById('themeToggleIcon');
        
        if (document.body.classList.contains('theme-dark')) {
            icon.className = 'fas fa-sun';
            localStorage.setItem('theme', 'dark');
        } else {
            icon.className = 'fas fa-moon';
            localStorage.setItem('theme', 'light');
        }
        
        // Re-render charts with new theme colors
        setTimeout(() => {
            this.updateCharts(this.currentChartData || {
                sales_trend: [],
                status_distribution: {},
                top_items: []
            });
        }, 100);
    }

    toggleNotificationCenter() {
        const notificationCenter = document.getElementById('notificationCenter');
        if (notificationCenter) {
            notificationCenter.classList.toggle('hidden');
            if (!notificationCenter.classList.contains('hidden')) {
                this.loadNotifications();
            }
        }
    }

    hideNotificationCenter() {
        const notificationCenter = document.getElementById('notificationCenter');
        if (notificationCenter) {
            notificationCenter.classList.add('hidden');
        }
    }

    async loadNotifications() {
        try {
            const response = await fetch('/api/notifications');
            const notifications = await response.json();
            
            if (response.ok) {
                this.renderNotifications(notifications);
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            this.renderNotifications([]);
        }
    }

    renderNotifications(notifications) {
        const notificationList = document.getElementById('notificationList');
        if (!notificationList) return;

        if (notifications.length === 0) {
            notificationList.innerHTML = `
                <div class="no-notifications">
                    <i class="fas fa-bell-slash"></i>
                    <p>No new notifications</p>
                </div>
            `;
            return;
        }

        notificationList.innerHTML = notifications.map(notification => `
            <div class="notification-item ${notification.type || 'info'}">
                <div class="notification-icon">
                    <i class="fas ${this.getNotificationIcon(notification.type)}"></i>
                </div>
                <div class="notification-content">
                    <div class="notification-title">${notification.title}</div>
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-time">${new Date(notification.timestamp).toLocaleString()}</div>
                </div>
                ${notification.action ? `
                    <div class="notification-action">
                        <button class="btn btn-sm btn-primary" onclick="adminApp.handleNotificationAction('${notification.action}', '${notification.id}')">
                            ${notification.actionText || 'View'}
                        </button>
                    </div>
                ` : ''}
            </div>
        `).join('');
    }

    getNotificationIcon(type) {
        const icons = {
            'warning': 'fa-exclamation-triangle',
            'danger': 'fa-exclamation-circle',
            'success': 'fa-check-circle',
            'info': 'fa-info-circle',
            'order': 'fa-shopping-cart',
            'user': 'fa-user',
            'stock': 'fa-box'
        };
        return icons[type] || 'fa-bell';
    }

    handleNotificationAction(action, notificationId) {
        switch(action) {
            case 'view_orders':
                this.showPage('orders');
                break;
            case 'view_users':
                this.showPage('users');
                break;
            case 'view_menu':
                this.showPage('menu');
                break;
            default:
                console.log('Unknown notification action:', action);
        }
        this.hideNotificationCenter();
    }

    // Utility functions for date formatting
    formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) {
                return 'Invalid Date';
            }
            return date.toLocaleDateString();
        } catch (error) {
            return 'Invalid Date';
        }
    }

    formatTime(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) {
                return 'Invalid Time';
            }
            return date.toLocaleTimeString();
        } catch (error) {
            return 'Invalid Time';
        }
    }

    formatDateTime(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            if (isNaN(date.getTime())) {
                return 'Invalid Date';
            }
            return date.toLocaleString();
        } catch (error) {
            return 'Invalid Date';
        }
    }

    // Filter Functions
    filterOrders() {
        const searchTerm = document.getElementById('orderSearch')?.value.toLowerCase() || '';
        const statusFilter = document.getElementById('orderStatusFilter')?.value || '';
        const dateFrom = document.getElementById('orderDateFrom')?.value || '';
        const dateTo = document.getElementById('orderDateTo')?.value || '';

        const rows = document.querySelectorAll('#ordersTableBody tr');
        
        rows.forEach(row => {
            const customerName = row.querySelector('.customer-name')?.textContent.toLowerCase() || '';
            const customerEmail = row.querySelector('.customer-email')?.textContent.toLowerCase() || '';
            const status = row.querySelector('.status-badge')?.textContent || '';
            const orderDate = row.querySelector('.date-info div')?.textContent || '';

            const matchesSearch = customerName.includes(searchTerm) || 
                                customerEmail.includes(searchTerm) ||
                                row.querySelector('td:nth-child(2)')?.textContent.toLowerCase().includes(searchTerm);
            
            const matchesStatus = !statusFilter || status === statusFilter;
            
            let matchesDate = true;
            if (dateFrom || dateTo) {
                const rowDate = new Date(orderDate);
                if (dateFrom && rowDate < new Date(dateFrom)) matchesDate = false;
                if (dateTo && rowDate > new Date(dateTo)) matchesDate = false;
            }

            row.style.display = (matchesSearch && matchesStatus && matchesDate) ? '' : 'none';
        });
    }

    filterMenu() {
        const searchTerm = document.getElementById('menuSearch')?.value.toLowerCase() || '';
        const categoryFilter = document.getElementById('menuCategoryFilter')?.value || '';
        const stockFilter = document.getElementById('menuStockFilter')?.value || '';

        const items = document.querySelectorAll('.menu-card, #menuTableBody tr');
        
        items.forEach(item => {
            const name = item.querySelector('.menu-card-title, .item-name')?.textContent.toLowerCase() || '';
            const category = item.querySelector('.menu-card-category, .item-category')?.textContent || '';
            const stockText = item.querySelector('.stock, .stock-info')?.textContent || '';
            const stock = parseInt(stockText.match(/\d+/)?.[0] || '0');

            const matchesSearch = name.includes(searchTerm) || category.toLowerCase().includes(searchTerm);
            const matchesCategory = !categoryFilter || category === categoryFilter;
            
            let matchesStock = true;
            if (stockFilter === 'low') matchesStock = stock < this.lowStockThreshold;
            else if (stockFilter === 'out') matchesStock = stock === 0;
            else if (stockFilter === 'available') matchesStock = stock > 0;

            item.style.display = (matchesSearch && matchesCategory && matchesStock) ? '' : 'none';
        });
    }

    filterUsers() {
        const searchTerm = document.getElementById('userSearch')?.value.toLowerCase() || '';
        const roleFilter = document.getElementById('userRoleFilter')?.value || '';
        const statusFilter = document.getElementById('userStatusFilter')?.value || '';

        const rows = document.querySelectorAll('#usersTableBody tr');
        
        rows.forEach(row => {
            const name = row.querySelector('.user-name')?.textContent.toLowerCase() || '';
            const email = row.querySelector('.user-email')?.textContent.toLowerCase() || '';
            const role = row.querySelector('.role-badge')?.textContent || '';
            const status = row.querySelector('.status-badge')?.textContent || '';

            const matchesSearch = name.includes(searchTerm) || email.includes(searchTerm);
            const matchesRole = !roleFilter || role === roleFilter;
            const matchesStatus = !statusFilter || status === statusFilter;

            row.style.display = (matchesSearch && matchesRole && matchesStatus) ? '' : 'none';
        });
    }

    clearOrderFilters() {
        document.getElementById('orderSearch').value = '';
        document.getElementById('orderStatusFilter').value = '';
        document.getElementById('orderDateFrom').value = '';
        document.getElementById('orderDateTo').value = '';
        this.filterOrders();
    }

    handleLogout() {
        if (confirm('Are you sure you want to logout?')) {
            // Clear any stored data
            localStorage.removeItem('adminSession');
            
            // Redirect to login or home page
            window.location.href = '/';
        }
    }

    // Bulk Operations
    toggleSelectAllOrders(checked) {
        const checkboxes = document.querySelectorAll('.order-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = checked;
        });
        
        this.selectedItems.clear();
        if (checked) {
            checkboxes.forEach(checkbox => {
                this.selectedItems.add(checkbox.value);
            });
        }
        
        this.updateBulkActionButtons();
    }

    updateBulkActionButtons() {
        const bulkBtn = document.getElementById('bulkOrderActionBtn');
        const selectedCount = this.selectedItems.size;
        
        if (bulkBtn) {
            bulkBtn.style.display = selectedCount > 0 ? 'block' : 'none';
            bulkBtn.textContent = `Bulk Update (${selectedCount} selected)`;
        }
    }

    showBulkOrderStatusModal() {
        if (this.selectedItems.size === 0) {
            this.showToast('No orders selected', 'warning');
            return;
        }

        const modalContent = `
            <div class="bulk-status-modal">
                <div class="modal-header">
                    <h3>Update Order Status</h3>
                    <p>Selected: ${this.selectedItems.size} orders</p>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label for="bulkStatusSelect">New Status:</label>
                        <select id="bulkStatusSelect" class="form-control">
                            <option value="Order Received">Order Received</option>
                            <option value="Preparing">Preparing</option>
                            <option value="Ready for Pickup">Ready for Pickup</option>
                            <option value="Completed">Completed</option>
                            <option value="Cancelled">Cancelled</option>
                        </select>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="adminApp.hideModal()">Cancel</button>
                    <button class="btn btn-primary" onclick="adminApp.executeBulkStatusUpdate()">Update Orders</button>
                </div>
            </div>
        `;

        this.showModal('Bulk Update Orders', modalContent);
    }

    async executeBulkStatusUpdate() {
        const status = document.getElementById('bulkStatusSelect').value;
        const orderIds = Array.from(this.selectedItems);

        try {
            const response = await fetch('/api/orders/bulk-update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    order_ids: orderIds,
                    status: status
                })
            });

            if (response.ok) {
                this.showToast(`${orderIds.length} orders updated successfully`, 'success');
                this.hideModal();
                this.selectedItems.clear();
                await this.loadOrdersData();
                this.updateBulkActionButtons();
            } else {
                throw new Error('Failed to update orders');
            }
        } catch (error) {
            console.error('Bulk update error:', error);
            this.showToast('Error updating orders', 'error');
        }
    }

    // Export Functions
    async exportOrders() {
        try {
            const fromDate = document.getElementById('orderDateFrom')?.value;
            const toDate = document.getElementById('orderDateTo')?.value;
            const status = document.getElementById('orderStatusFilter')?.value;
            
            const params = new URLSearchParams();
            if (fromDate) params.append('start_date', fromDate);
            if (toDate) params.append('end_date', toDate);
            if (status) params.append('status', status);
            
            const url = `/api/reports/orders/csv?${params.toString()}`;
            
            // Create download link
            const link = document.createElement('a');
            link.href = url;
            link.download = `orders_export_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showToast('Orders exported successfully', 'success');
        } catch (error) {
            this.showToast('Error exporting orders', 'error');
        }
    }

    async exportMenu() {
        try {
            const category = document.getElementById('menuCategoryFilter')?.value;
            const params = new URLSearchParams();
            if (category) params.append('category', category);
            
            const url = `/api/reports/menu/csv?${params.toString()}`;
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `menu_export_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showToast('Menu exported successfully', 'success');
        } catch (error) {
            this.showToast('Error exporting menu', 'error');
        }
    }

    async exportUsers() {
        try {
            const role = document.getElementById('userRoleFilter')?.value;
            const status = document.getElementById('userStatusFilter')?.value;
            
            const params = new URLSearchParams();
            if (role) params.append('role', role);
            if (status) params.append('status', status);
            
            const url = `/api/reports/users/csv?${params.toString()}`;
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `users_export_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showToast('Users exported successfully', 'success');
        } catch (error) {
            this.showToast('Error exporting users', 'error');
        }
    }

    async exportAuditLogs() {
        try {
            const search = document.getElementById('auditLogSearch')?.value;
            const action = document.getElementById('auditActionFilter')?.value;
            const fromDate = document.getElementById('auditDateFrom')?.value;
            const toDate = document.getElementById('auditDateTo')?.value;
            
            const params = new URLSearchParams();
            if (search) params.append('search', search);
            if (action) params.append('action', action);
            if (fromDate) params.append('start_date', fromDate);
            if (toDate) params.append('end_date', toDate);
            
            const url = `/api/audit-logs/csv?${params.toString()}`;
            
            const link = document.createElement('a');
            link.href = url;
            link.download = `audit_logs_export_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showToast('Audit logs exported successfully', 'success');
        } catch (error) {
            this.showToast('Error exporting audit logs', 'error');
        }
    }

    // Chart export functionality
    exportChart(chartType, chartName) {
        try {
            const chart = this.charts[chartType];
            if (!chart) {
                this.showToast(`${chartName} chart not available for export`, 'warning');
                return;
            }

            // Create a temporary canvas to render the chart
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Set canvas size
            canvas.width = 800;
            canvas.height = 600;
            
            // Fill with background color
            const computedStyle = getComputedStyle(document.documentElement);
            const bgColor = computedStyle.getPropertyValue('--surface').trim();
            ctx.fillStyle = bgColor || '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // Get chart image
            const chartCanvas = chart.canvas;
            const chartImage = chartCanvas.toDataURL('image/png');
            
            // Create download link
            const link = document.createElement('a');
            link.href = chartImage;
            link.download = `${chartName.toLowerCase().replace(/\s/g, '_')}_${new Date().toISOString().split('T')[0]}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            this.showToast(`${chartName} exported successfully`, 'success');
        } catch (error) {
            console.error('Chart export error:', error);
            this.showToast(`Error exporting ${chartName}`, 'error');
        }
    }
}

// Initialize the Enhanced Admin App
let adminApp;
document.addEventListener('DOMContentLoaded', () => {
    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.classList.add('theme-dark');
        document.getElementById('themeToggleIcon').className = 'fas fa-sun';
    }
    
    // Initialize the app
    adminApp = new EnhancedAdminApp();
});

// Global utility functions for onclick handlers
function navigateToPage(page) {
    if (adminApp) {
        adminApp.showPage(page);
    }
}

// Make adminApp globally available for inline event handlers
window.adminApp = null;
document.addEventListener('DOMContentLoaded', () => {
    window.adminApp = adminApp;
});