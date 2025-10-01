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
    this.lastChartData = null;
        
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

        // Update navigation and ARIA states
        document.querySelectorAll('.nav-item').forEach(item => {
            const isActive = item.dataset.page === page;
            item.classList.toggle('active', isActive);
            item.setAttribute('aria-pressed', isActive.toString());
            
            // Update aria-label for active page
            if (isActive) {
                const originalLabel = item.getAttribute('aria-label') || item.textContent.trim();
                if (!originalLabel.includes('Current page')) {
                    item.setAttribute('aria-label', `${originalLabel} - Current page`);
                }
            } else {
                // Remove "Current page" from aria-label
                const currentLabel = item.getAttribute('aria-label') || '';
                item.setAttribute('aria-label', currentLabel.replace(' - Current page', ''));
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
            console.log('Loading dashboard data...');
            const response = await fetch('/api/dashboard/stats');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Dashboard response:', data);
            
            this.updateKPICards(data.kpi || {});
            this.updateCharts(data.charts || {});
            this.updateNotificationBadges(data.kpi || {});
            
            // Load other dashboard components in parallel
            const [ordersResult, notificationsResult, chartsResult] = await Promise.allSettled([
                this.updateRecentOrders(),
                this.loadNotifications(),
                this.loadChartsData()
            ]);
            
            // Log any failures but don't stop execution
            if (ordersResult.status === 'rejected') {
                console.warn('Failed to load recent orders:', ordersResult.reason);
            }
            if (notificationsResult.status === 'rejected') {
                console.warn('Failed to load notifications:', notificationsResult.reason);
            }
            if (chartsResult.status === 'rejected') {
                console.warn('Failed to load charts:', chartsResult.reason);
            }
            
            console.log('Dashboard data loaded successfully');
            
        } catch (error) {
            console.error('Dashboard data error:', error);
            this.showToast('Failed to load dashboard data', 'error');
            this.loadFallbackDashboardData();
        }
    }

    loadFallbackDashboardData() {
        console.log('Loading fallback dashboard data...');
        // Set default KPI values
        this.updateKPICards({
            total_orders: 6,
            total_revenue: 395,
            active_orders: 5,
            pending_approvals: 0,
            low_stock_items: 1
        });
        
        // Set sample chart data
        this.updateCharts({
            sales_trend: [
                { date: '2025-09-25', orders: 1, revenue: 25 },
                { date: '2025-09-26', orders: 2, revenue: 65 },
                { date: '2025-09-27', orders: 0, revenue: 0 },
                { date: '2025-09-28', orders: 1, revenue: 320 },
                { date: '2025-09-29', orders: 1, revenue: 240 },
                { date: '2025-09-30', orders: 1, revenue: 395 },
                { date: '2025-10-01', orders: 0, revenue: 0 }
            ],
            status_distribution: {
                'Order Received': 3,
                'Preparing': 1,
                'Ready for Pickup': 1,
                'Completed': 1
            },
            top_items: [
                { name: 'Vada Pav', orders: 2 },
                { name: 'Samosa', orders: 1 },
                { name: 'Ginger Mint Tea', orders: 1 },
                { name: 'Chocolate Coffee', orders: 1 },
                { name: 'Sandwich', orders: 1 }
            ]
        });
    }

    updateKPICards(kpi) {
        document.getElementById('totalOrders').textContent = kpi.total_orders || 0;
        document.getElementById('totalRevenue').textContent = `₹${kpi.total_revenue || 0}`;
        document.getElementById('activeOrders').textContent = kpi.active_orders || 0;
        document.getElementById('pendingApprovals').textContent = kpi.pending_approvals || 0;
        document.getElementById('lowStockCount').textContent = kpi.low_stock_items || 0;

        // Update badges in sidebar
        this.updateSidebarBadges(kpi);
        this.updateInsightsPanel(kpi);
    }

    updateInsightsPanel(kpi = {}) {
        const list = document.getElementById('insightsList');
        const updatedAt = document.getElementById('insightsUpdatedAt');
        if (!list) return;

        const totalOrders = kpi.total_orders || 0;
        const totalRevenue = kpi.total_revenue || 0;
        const avgOrderValue = totalOrders ? totalRevenue / totalOrders : 0;

        const insights = [
            {
                icon: 'fa-indian-rupee-sign',
                title: 'Average Order Value',
                detail: totalOrders ? `₹${avgOrderValue.toFixed(2)} per order` : 'No orders recorded yet',
                meta: `${totalOrders} orders counted this term`
            },
            {
                icon: 'fa-clock',
                title: 'Orders In Progress',
                detail: `${kpi.active_orders || 0} active orders awaiting fulfilment`,
                meta: kpi.active_orders ? 'Keep the kitchen in sync with updates' : 'Great job! Everything is completed'
            },
            {
                icon: 'fa-box-open',
                title: 'Inventory Watchlist',
                detail: `${kpi.low_stock_items || 0} menu items need restocking soon`,
                meta: kpi.low_stock_items ? 'Review stock levels under Menu > Inventory' : 'Inventory levels look healthy'
            },
            {
                icon: 'fa-user-check',
                title: 'User Approvals',
                detail: `${kpi.pending_approvals || 0} registrations pending review`,
                meta: 'Approve or reject requests from the Users page'
            }
        ];

        list.innerHTML = insights.map(item => `
            <li class="insight-item">
                <div class="insight-icon">
                    <i class="fas ${item.icon}"></i>
                </div>
                <div class="insight-content">
                    <div class="insight-title">${item.title}</div>
                    <div class="insight-detail">${item.detail}</div>
                    <div class="insight-meta">${item.meta}</div>
                </div>
            </li>
        `).join('');

        if (updatedAt) {
            const now = new Date();
            updatedAt.textContent = `Updated ${now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
        }
    }

    updateSidebarBadges(kpi) {
        const badges = {
            'activeOrdersBadge': kpi.active_orders || 0,
            'lowStockBadge': kpi.low_stock_items || 0,
            'pendingUsersBadge': kpi.pending_approvals || 0
        };
        
        Object.entries(badges).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
                element.style.display = value > 0 ? 'inline' : 'none';
            }
        });
    }

    updateNotificationBadges(kpi) {
        this.updateSidebarBadges(kpi);
    }

    updateCharts(chartData) {
        if (!chartData) {
            return;
        }

        this.lastChartData = chartData;
        // Sales Trend Chart
        this.createSalesTrendChart(chartData.sales_trend);
        
        // Order Status Distribution Chart
        this.createOrderStatusChart(chartData.status_distribution);
        
        // Top Items Chart
        this.createTopItemsChart(chartData.top_items);
        
        // Category Sales Chart (if available)
        if (chartData.category_sales) {
            this.createCategorySalesChart(chartData.category_sales);
        }
    }

    refreshChartsTheme() {
        if (this.lastChartData) {
            this.updateCharts(this.lastChartData);
        }
    }

    async updateRecentOrders() {
        try {
            console.log('Loading recent orders...');
            const response = await fetch('/api/orders?limit=5');
            const orders = await response.json();
            
            if (response.ok && Array.isArray(orders)) {
                this.renderRecentOrders(orders.slice(0, 5));
            } else {
                console.error('Failed to load recent orders:', orders);
                this.renderRecentOrders([]);
            }
        } catch (error) {
            console.error('Error loading recent orders:', error);
            this.renderRecentOrders([]);
        }
    }

    renderRecentOrders(orders) {
        const container = document.getElementById('recentOrdersList');
        if (!container) {
            console.warn('Recent orders container not found');
            return;
        }

        if (orders.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-shopping-cart"></i>
                    <p>No recent orders</p>
                </div>
            `;
            return;
        }

        container.innerHTML = orders.map(order => {
            const statusClass = this.getStatusClass(order.status);
            const timeAgo = this.getTimeAgo(new Date(order.created_at));
            
            return `
                <div class="recent-order-item" onclick="adminApp.showOrderDetails(${order.id})">
                    <div class="order-info">
                        <div class="order-id">#${order.id}</div>
                        <div class="order-customer">${order.customer_name}</div>
                        <div class="order-time">${timeAgo}</div>
                    </div>
                    <div class="order-amount">₹${order.total_price}</div>
                    <div class="order-status">
                        <span class="status-badge ${statusClass}">${order.status}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    getChartTheme() {
        const styles = getComputedStyle(document.documentElement);
        const getVar = (name, fallback) => {
            const value = styles.getPropertyValue(name);
            return value ? value.trim() : fallback;
        };

        return {
            accent1: getVar('--chart-accent-1', '#2563eb'),
            accent2: getVar('--chart-accent-2', '#9333ea'),
            accent3: getVar('--chart-accent-3', '#16a34a'),
            accent4: getVar('--chart-accent-4', '#f97316'),
            neutral: getVar('--chart-neutral', '#64748b'),
            grid: getVar('--chart-grid', 'rgba(148, 163, 184, 0.25)'),
            tooltipBg: getVar('--chart-tooltip-bg', 'rgba(255, 255, 255, 0.95)'),
            tooltipText: getVar('--chart-tooltip-text', '#1f2937'),
            tooltipSubtle: getVar('--chart-tooltip-subtle', '#475569'),
            text: getVar('--text', '#1f2937'),
            textMuted: getVar('--text-muted', '#64748b'),
            surface: getVar('--surface', '#ffffff')
        };
    }

    hexToRgba(hex, alpha = 1) {
        if (!hex) return `rgba(0,0,0,${alpha})`;
        let normalized = hex.replace('#', '');
        if (normalized.length === 3) {
            normalized = normalized.split('').map(char => char + char).join('');
        }
        const bigint = parseInt(normalized, 16);
        const r = (bigint >> 16) & 255;
        const g = (bigint >> 8) & 255;
        const b = bigint & 255;
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    adjustColor(hex, amount) {
        if (!hex) return hex;
        let normalized = hex.replace('#', '');
        if (normalized.length === 3) {
            normalized = normalized.split('').map(char => char + char).join('');
        }
        const num = parseInt(normalized, 16);
        let r = (num >> 16) + amount;
        let g = ((num >> 8) & 0x00FF) + amount;
        let b = (num & 0x0000FF) + amount;

        r = Math.min(255, Math.max(0, r));
        g = Math.min(255, Math.max(0, g));
        b = Math.min(255, Math.max(0, b));

        return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
    }

    createChartGradient(ctx, color) {
        const gradient = ctx.createLinearGradient(0, 0, 0, ctx.canvas.height || 360);
        gradient.addColorStop(0, this.hexToRgba(color, 0.35));
        gradient.addColorStop(1, this.hexToRgba(color, 0.05));
        return gradient;
    }

    generateChartPalette(count) {
        const theme = this.getChartTheme();
        const base = [theme.accent1, theme.accent2, theme.accent3, theme.accent4, theme.neutral];
        const palette = [];

        for (let i = 0; i < count; i++) {
            const color = base[i % base.length];
            const variant = i < base.length ? color : this.adjustColor(color, (i - base.length + 1) * 12);
            palette.push(variant);
        }

        return palette;
    }

    createSalesTrendChart(salesData) {
        const canvas = document.getElementById('salesTrendChart');
        if (!canvas) {
            console.warn('Sales trend chart canvas not found');
            return;
        }

        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.warn('Unable to get 2D context for sales chart');
            return;
        }

        if (this.charts.salesTrend) {
            this.charts.salesTrend.destroy();
        }

        if (!salesData || salesData.length === 0) {
            console.warn('No sales data available for chart');
            return;
        }

        const labels = salesData.map(item => new Date(item.date).toLocaleDateString());
        const orders = salesData.map(item => item.orders);
        const revenue = salesData.map(item => item.revenue);

        const chartTheme = this.getChartTheme();
        const ordersGradient = this.createChartGradient(ctx, chartTheme.accent1);
        const revenueGradient = this.createChartGradient(ctx, chartTheme.accent3);

        this.charts.salesTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Orders',
                        data: orders,
                        borderColor: chartTheme.accent1,
                        backgroundColor: ordersGradient,
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: chartTheme.accent1,
                        pointBorderColor: chartTheme.surface,
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Revenue (₹)',
                        data: revenue,
                        borderColor: chartTheme.accent3,
                        backgroundColor: revenueGradient,
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: chartTheme.accent3,
                        pointBorderColor: chartTheme.surface,
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        yAxisID: 'y1'
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
                        display: true,
                        position: 'top',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle',
                            padding: 20,
                            color: chartTheme.text
                        }
                    },
                    tooltip: {
                        backgroundColor: chartTheme.tooltipBg,
                        titleColor: chartTheme.tooltipText,
                        bodyColor: chartTheme.tooltipSubtle,
                        borderColor: this.hexToRgba(chartTheme.tooltipText, 0.08),
                        borderWidth: 1,
                        cornerRadius: 8
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: chartTheme.grid,
                            drawBorder: false
                        },
                        ticks: {
                            color: chartTheme.textMuted
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        grid: {
                            color: chartTheme.grid,
                            drawBorder: false
                        },
                        ticks: {
                            color: chartTheme.textMuted
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        grid: {
                            drawOnChartArea: false,
                            color: chartTheme.grid,
                            drawBorder: false
                        },
                        ticks: {
                            color: chartTheme.textMuted
                        }
                    },
                }
            }
        });
    }

    createOrderStatusChart(statusData) {
        const canvas = document.getElementById('orderStatusChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.warn('Unable to get context for order status chart');
            return;
        }

        if (this.charts.orderStatus) {
            this.charts.orderStatus.destroy();
        }

        const labels = Object.keys(statusData);
        const data = Object.values(statusData);

        const chartTheme = this.getChartTheme();
        const palette = this.generateChartPalette(labels.length);
        const hoverPalette = palette.map(color => this.adjustColor(color, -18));

        this.charts.orderStatus = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: palette,
                    hoverBackgroundColor: hoverPalette,
                    borderWidth: 3,
                    borderColor: chartTheme.surface,
                    hoverBorderWidth: 4,
                    cutout: '65%',
                    borderRadius: 6,
                    spacing: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'rectRounded',
                            padding: 15,
                            color: chartTheme.text,
                            font: {
                                size: 12,
                                weight: '500'
                            }
                        }
                    },
                    tooltip: {
                        backgroundColor: chartTheme.tooltipBg,
                        titleColor: chartTheme.tooltipText,
                        bodyColor: chartTheme.tooltipSubtle,
                        borderColor: this.hexToRgba(chartTheme.tooltipText, 0.08),
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true,
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                },
                animation: {
                    animateRotate: true,
                    animateScale: true,
                    duration: 1000
                }
            }
        });
    }

    createTopItemsChart(topItems) {
        const canvas = document.getElementById('topItemsChart');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.warn('Unable to get context for top items chart');
            return;
        }

        if (this.charts.topItems) {
            this.charts.topItems.destroy();
        }

        const labels = topItems.map(item => item.name);
        const data = topItems.map(item => item.orders);

        const chartTheme = this.getChartTheme();
        const backgroundColors = this.generateChartPalette(labels.length);
        const borderColors = backgroundColors.map(color => this.adjustColor(color, -20));
        const hoverColors = backgroundColors.map(color => this.adjustColor(color, -10));

        this.charts.topItems = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Orders',
                    data: data,
                    backgroundColor: backgroundColors,
                    borderColor: borderColors,
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false,
                    hoverBackgroundColor: hoverColors,
                    hoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: chartTheme.textMuted,
                            maxRotation: 45
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: chartTheme.grid,
                            drawBorder: false
                        },
                        ticks: {
                            color: chartTheme.textMuted
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: chartTheme.tooltipBg,
                        titleColor: chartTheme.tooltipText,
                        bodyColor: chartTheme.tooltipSubtle,
                        borderColor: this.hexToRgba(chartTheme.tooltipText, 0.08),
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    createCategorySalesChart(categoryData) {
        const canvas = document.getElementById('categorySalesChart');
        if (!canvas) {
            console.warn('Category sales chart canvas not found');
            return;
        }

        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.warn('Unable to get context for category sales chart');
            return;
        }

        if (this.charts.categorySales) {
            this.charts.categorySales.destroy();
        }

        if (!categoryData || Object.keys(categoryData).length === 0) {
            console.warn('No category data available for chart');
            return;
        }

        const labels = Object.keys(categoryData);
        const data = Object.values(categoryData);

        const chartTheme = this.getChartTheme();
        const backgroundColors = this.generateChartPalette(labels.length);
        const borderColors = backgroundColors.map(color => this.adjustColor(color, -20));
        const hoverColors = backgroundColors.map(color => this.adjustColor(color, -10));

        this.charts.categorySales = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Sales',
                    data: data,
                    backgroundColor: backgroundColors,
                    borderColor: borderColors,
                    borderWidth: 2,
                    borderRadius: 6,
                    borderSkipped: false,
                    hoverBackgroundColor: hoverColors,
                    hoverBorderWidth: 3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: chartTheme.textMuted
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: chartTheme.grid,
                            drawBorder: false
                        },
                        ticks: {
                            color: chartTheme.textMuted
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: chartTheme.tooltipBg,
                        titleColor: chartTheme.tooltipText,
                        bodyColor: chartTheme.tooltipSubtle,
                        borderColor: this.hexToRgba(chartTheme.tooltipText, 0.08),
                        borderWidth: 1,
                        cornerRadius: 8,
                        displayColors: true
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
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
                            <div>${new Date(order.created_at).toLocaleDateString()}</div>
                            <div class="text-muted">${new Date(order.created_at).toLocaleTimeString()}</div>
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
        this.updateSelectAllState('orders');
    }

    parseOrderItems(rawItems) {
        if (!rawItems) {
            return [];
        }

        let items = [];

        if (Array.isArray(rawItems)) {
            items = rawItems;
        } else if (typeof rawItems === 'string') {
            try {
                const parsed = JSON.parse(rawItems);
                items = Array.isArray(parsed) ? parsed : parsed.items || [];
            } catch (error) {
                console.warn('Failed to parse order items string:', error);
                items = [];
            }
        } else if (typeof rawItems === 'object') {
            items = rawItems.items || [];
        }

        if (!Array.isArray(items)) {
            return [];
        }

        return items.map(item => {
            const quantity = item.quantity ?? item.qty ?? item.count ?? 0;
            const price = item.price ?? item.cost ?? null;
            const safePrice = typeof price === 'number' ? price : null;
            const subtotal = item.subtotal ?? (safePrice !== null ? safePrice * quantity : null);

            return {
                id: item.id ?? item.item_id ?? null,
                name: item.name ?? `Item ${item.id ?? ''}`.trim(),
                quantity,
                price: safePrice,
                subtotal
            };
        });
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
                this.updateBulkOrderButton();
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
            console.log('Loading menu data...');
            
            // Initialize view button state
            this.initializeMenuView();
            
            const response = await fetch('/api/menu');
            const menuItems = await response.json();

            console.log('Menu response:', response.ok, menuItems);
            if (response.ok) {
                this.renderMenuItems(menuItems);
                this.populateMenuCategories(menuItems);
            } else {
                console.error('Failed to load menu items:', menuItems);
                this.showToast('Failed to load menu items', 'error');
            }
        } catch (error) {
            console.error('Menu data error:', error);
            this.showToast('Error loading menu data', 'error');
        }
    }

    initializeMenuView() {
        const gridContainer = document.getElementById('menuGridView');
        const tableContainer = document.getElementById('menuTableView');
        const toggleBtn = document.getElementById('toggleMenuViewBtn');
        
        if (!gridContainer || !tableContainer || !toggleBtn) return;
        
        // Check current state and set button text accordingly
        const isGridView = !gridContainer.classList.contains('hidden');
        
        if (isGridView) {
            toggleBtn.innerHTML = '<i class="fas fa-list"></i> Table View';
            toggleBtn.title = 'Switch to Table View';
        } else {
            toggleBtn.innerHTML = '<i class="fas fa-th"></i> Grid View';
            toggleBtn.title = 'Switch to Grid View';
        }
    }

    renderMenuItems(menuItems) {
        console.log('Rendering menu items:', menuItems.length);
        
        // Check if grid view is active by checking container visibility
        const gridContainer = document.getElementById('menuGridView');
        const tableContainer = document.getElementById('menuTableView');
        
        // Default to grid view (as per HTML structure)
        let isGridView = true;
        
        if (gridContainer && tableContainer) {
            // Grid view is active if grid container is not hidden
            isGridView = !gridContainer.classList.contains('hidden');
        }
        
        console.log('View mode - Grid:', isGridView);
        
        if (isGridView) {
            // Hide table view and show grid view
            if (tableContainer) tableContainer.classList.add('hidden');
            if (gridContainer) gridContainer.classList.remove('hidden');
            this.renderMenuGrid(menuItems);
        } else {
            // Hide grid view and show table view
            if (gridContainer) gridContainer.classList.add('hidden');
            if (tableContainer) tableContainer.classList.remove('hidden');
            this.renderMenuTable(menuItems);
        }
    }

    renderMenuTable(menuItems) {
        const tbody = document.getElementById('menuTableBody');
        if (!tbody) {
            console.error('Menu table body not found');
            return;
        }

        if (menuItems.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="empty-state">
                        <i class="fas fa-utensils"></i>
                        <p>No menu items found</p>
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = menuItems.map(item => {
            const lowStock = item.stock < this.lowStockThreshold;
            const stockClass = lowStock ? 'low-stock' : (item.stock === 0 ? 'out-of-stock' : '');
            const statusClass = item.available ? 'available' : 'unavailable';
            
            return `
                <tr data-item-id="${item.id}" class="${stockClass}">
                    <td>
                        <input type="checkbox" class="menu-checkbox" value="${item.id}">
                    </td>
                    <td>
                        <div class="menu-item-image">
                            <img src="/static/images/${item.image}" alt="${item.name}" onerror="this.src='/static/images/placeholder.jpg'">
                        </div>
                    </td>
                    <td>
                        <div class="menu-item-info">
                            <div class="item-name">${item.name}</div>
                            <div class="item-category text-muted">${item.category}</div>
                        </div>
                    </td>
                    <td><strong>${item.category}</strong></td>
                    <td><strong>₹${item.price}</strong></td>
                    <td>
                        <div class="stock-info ${stockClass}">
                            <span class="stock-number">${item.stock}</span>
                            ${lowStock ? '<i class="fas fa-exclamation-triangle warning-icon" title="Low Stock"></i>' : ''}
                        </div>
                    </td>
                    <td>
                        <span class="status-badge ${statusClass}">${item.available ? 'Available' : 'Unavailable'}</span>
                        ${item.deliverable ? '<span class="status-badge deliverable">Deliverable</span>' : ''}
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
        this.updateSelectAllState('menu');
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
        this.updateSelectAllState('menu');
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
                this.updateSelectAllState('menu');
            });
        });
    }

    setupOrderCheckboxes() {
        document.querySelectorAll('.order-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateBulkOrderButtons();
                this.updateSelectAllState('orders');
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
                        ${user.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
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
        this.updateSelectAllState('users');
    }

    setupUserCheckboxes() {
        document.querySelectorAll('.user-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                this.updateBulkUserButtons();
                this.updateSelectAllState('users');
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

    // Select All Functions
    toggleSelectAllOrders(checked) {
        const orderCheckboxes = document.querySelectorAll('.order-checkbox');
        orderCheckboxes.forEach(checkbox => {
            checkbox.checked = checked;
        });
        this.updateBulkOrderButtons();
    }

    toggleSelectAllMenu(checked) {
        const menuCheckboxes = document.querySelectorAll('.menu-checkbox');
        menuCheckboxes.forEach(checkbox => {
            checkbox.checked = checked;
        });
        this.updateBulkMenuButtons();
    }

    toggleSelectAllUsers(checked) {
        const userCheckboxes = document.querySelectorAll('.user-checkbox');
        userCheckboxes.forEach(checkbox => {
            checkbox.checked = checked;
        });
        this.updateBulkUserButtons();
    }

    updateBulkOrderButtons() {
        const selectedOrders = document.querySelectorAll('.order-checkbox:checked');
        const bulkUpdateBtn = document.getElementById('bulkOrderActionBtn');
        
        if (bulkUpdateBtn) {
            bulkUpdateBtn.disabled = selectedOrders.length === 0;
        }
    }

    updateSelectAllState(type) {
        let selectAllId, checkboxClass;
        
        switch(type) {
            case 'orders':
                selectAllId = 'selectAllOrders';
                checkboxClass = '.order-checkbox';
                break;
            case 'menu':
                selectAllId = 'selectAllMenu';
                checkboxClass = '.menu-checkbox';
                break;
            case 'users':
                selectAllId = 'selectAllUsers';
                checkboxClass = '.user-checkbox';
                break;
            default:
                return;
        }

        const selectAllCheckbox = document.getElementById(selectAllId);
        if (!selectAllCheckbox) return;

        const allCheckboxes = document.querySelectorAll(checkboxClass);
        const checkedCheckboxes = document.querySelectorAll(`${checkboxClass}:checked`);
        
        if (checkedCheckboxes.length === 0) {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = false;
        } else if (checkedCheckboxes.length === allCheckboxes.length) {
            selectAllCheckbox.checked = true;
            selectAllCheckbox.indeterminate = false;
        } else {
            selectAllCheckbox.checked = false;
            selectAllCheckbox.indeterminate = true;
        }
    }

    toggleMenuView() {
        const gridContainer = document.getElementById('menuGridView');
        const tableContainer = document.getElementById('menuTableView');
        const toggleBtn = document.getElementById('toggleMenuViewBtn');
        
        if (!gridContainer || !tableContainer || !toggleBtn) return;
        
        const isGridView = !gridContainer.classList.contains('hidden');
        
        if (isGridView) {
            // Switch to table view
            gridContainer.classList.add('hidden');
            tableContainer.classList.remove('hidden');
            toggleBtn.innerHTML = '<i class="fas fa-th"></i> Grid View';
            toggleBtn.title = 'Switch to Grid View';
        } else {
            // Switch to grid view
            tableContainer.classList.add('hidden');
            gridContainer.classList.remove('hidden');
            toggleBtn.innerHTML = '<i class="fas fa-list"></i> Table View';
            toggleBtn.title = 'Switch to Table View';
        }
        
        // Re-render menu items in the new view
        this.loadMenuData();
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

    renderReportDetails(reportType, data) {
        const container = document.getElementById('reportData');
        
        if (!data.data || data.data.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-chart-bar"></i>
                    <p>No data available for the selected criteria</p>
                </div>
            `;
            return;
        }

        switch (reportType) {
            case 'orders':
                this.renderOrdersReport(container, data.data);
                break;
            case 'users':
                this.renderUsersReport(container, data.data);
                break;
            case 'menu':
                this.renderMenuReport(container, data.data);
                break;
        }
    }

    renderOrdersReport(container, orders) {
        const tableHTML = `
            <div class="report-table-container">
                <table class="report-table">
                    <thead>
                        <tr>
                            <th>Order ID</th>
                            <th>Customer</th>
                            <th>Items</th>
                            <th>Total</th>
                            <th>Status</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${orders.map(order => `
                            <tr>
                                <td>#${order.id}</td>
                                <td>
                                    <div class="customer-info">
                                        <div>${order.customer_name}</div>
                                        <div class="text-muted">${order.customer_email}</div>
                                    </div>
                                </td>
                                <td>
                                    <div class="order-items">
                                        ${this.parseOrderItems(order.items).map(item => 
                                            `<span class="item-tag">${item.name} (${item.quantity})</span>`
                                        ).slice(0, 2).join('')}
                                    </div>
                                </td>
                                <td><strong>₹${order.total_price}</strong></td>
                                <td><span class="status-badge ${this.getStatusClass(order.status)}">${order.status}</span></td>
                                <td>${new Date(order.created_at).toLocaleDateString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        container.innerHTML = tableHTML;
    }

    renderUsersReport(container, users) {
        const tableHTML = `
            <div class="report-table-container">
                <table class="report-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th>Joined</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${users.map(user => `
                            <tr>
                                <td>${user.name}</td>
                                <td>${user.email}</td>
                                <td><span class="role-badge ${user.role}">${user.role}</span></td>
                                <td><span class="status-badge ${user.status}">${user.status}</span></td>
                                <td>${new Date(user.created_at).toLocaleDateString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;
        container.innerHTML = tableHTML;
    }

    renderMenuReport(container, items) {
        const tableHTML = `
            <div class="report-table-container">
                <table class="report-table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Category</th>
                            <th>Price</th>
                            <th>Stock</th>
                            <th>Available</th>
                            <th>Deliverable</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${items.map(item => {
                            const lowStock = item.stock < this.lowStockThreshold;
                            const stockClass = lowStock ? 'low-stock' : (item.stock === 0 ? 'out-of-stock' : '');
                            
                            return `
                                <tr class="${stockClass}">
                                    <td>${item.name}</td>
                                    <td>${item.category}</td>
                                    <td>₹${item.price}</td>
                                    <td>
                                        <span class="stock-badge ${stockClass}">
                                            ${item.stock}
                                            ${lowStock ? '<i class="fas fa-exclamation-triangle"></i>' : ''}
                                        </span>
                                    </td>
                                    <td><span class="status-badge ${item.available ? 'available' : 'unavailable'}">${item.available ? 'Yes' : 'No'}</span></td>
                                    <td><span class="status-badge ${item.deliverable ? 'deliverable' : 'not-deliverable'}">${item.deliverable ? 'Yes' : 'No'}</span></td>
                                </tr>
                            `;
                        }).join('')}
                    </tbody>
                </table>
            </div>
        `;
        container.innerHTML = tableHTML;
    }

    async exportReport() {
        if (!this.currentReportData) {
            this.showToast('No report data to export', 'warning');
            return;
        }

        const reportType = document.getElementById('reportType').value;
        const fromDate = document.getElementById('reportFromDate').value;
        const toDate = document.getElementById('reportToDate').value;
        const exportFormat = document.getElementById('reportExportFormat').value;

        try {
            let url = `/api/reports/${reportType}`;
            
            if (exportFormat === 'csv') {
                url += '/csv';
            }
            
            const params = new URLSearchParams();
            if (fromDate) params.append('start_date', fromDate);
            if (toDate) params.append('end_date', toDate);
            
            if (params.toString()) {
                url += `?${params.toString()}`;
            }

            if (exportFormat === 'csv') {
                // Download CSV
                const link = document.createElement('a');
                link.href = url;
                link.download = `${reportType}_report_${new Date().toISOString().split('T')[0]}.csv`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                this.showToast('Report exported successfully', 'success');
            } else if (exportFormat === 'pdf') {
                // Generate PDF using jsPDF
                await this.exportReportAsPDF(reportType);
            }
        } catch (error) {
            console.error('Export error:', error);
            this.showToast('Error exporting report', 'error');
        }
    }

    async exportReportAsPDF(reportType) {
        try {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
            
            // Add title
            doc.setFontSize(20);
            doc.text(`${reportType.toUpperCase()} REPORT`, 20, 30);
            
            // Add date
            doc.setFontSize(12);
            doc.text(`Generated on: ${new Date().toLocaleDateString()}`, 20, 45);
            
            // Add report data
            let yPosition = 60;
            
            if (this.currentReportData.data && this.currentReportData.data.length > 0) {
                this.currentReportData.data.forEach((item, index) => {
                    if (yPosition > 250) {
                        doc.addPage();
                        yPosition = 30;
                    }
                    
                    let text = '';
                    switch (reportType) {
                        case 'orders':
                            text = `#${item.id} - ${item.customer_name} - ₹${item.total_price} - ${item.status}`;
                            break;
                        case 'users':
                            text = `${item.name} - ${item.email} - ${item.role} - ${item.status}`;
                            break;
                        case 'menu':
                            text = `${item.name} - ${item.category} - ₹${item.price} - Stock: ${item.stock}`;
                            break;
                    }
                    
                    doc.text(text, 20, yPosition);
                    yPosition += 10;
                });
            }
            
            // Save PDF
            doc.save(`${reportType}_report_${new Date().toISOString().split('T')[0]}.pdf`);
            this.showToast('Report exported as PDF successfully', 'success');
        } catch (error) {
            console.error('PDF export error:', error);
            this.showToast('Error exporting PDF', 'error');
        }
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

    renderAuditLogsPagination(pagination) {
        const paginationContainer = document.getElementById('auditLogsPagination');
        if (!paginationContainer || !pagination) return;

        const { page, pages, total } = pagination;
        
        if (pages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let paginationHTML = '<div class="pagination">';
        
        // Previous button
        if (page > 1) {
            paginationHTML += `<button class="btn btn-sm btn-outline" onclick="adminApp.loadAuditLogsData(${page - 1})">
                <i class="fas fa-chevron-left"></i>
            </button>`;
        }

        // Page numbers
        const startPage = Math.max(1, page - 2);
        const endPage = Math.min(pages, page + 2);

        if (startPage > 1) {
            paginationHTML += `<button class="btn btn-sm btn-outline" onclick="adminApp.loadAuditLogsData(1)">1</button>`;
            if (startPage > 2) {
                paginationHTML += '<span class="pagination-ellipsis">...</span>';
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            const activeClass = i === page ? 'btn-primary' : 'btn-outline';
            paginationHTML += `<button class="btn btn-sm ${activeClass}" onclick="adminApp.loadAuditLogsData(${i})">${i}</button>`;
        }

        if (endPage < pages) {
            if (endPage < pages - 1) {
                paginationHTML += '<span class="pagination-ellipsis">...</span>';
            }
            paginationHTML += `<button class="btn btn-sm btn-outline" onclick="adminApp.loadAuditLogsData(${pages})">${pages}</button>`;
        }

        // Next button
        if (page < pages) {
            paginationHTML += `<button class="btn btn-sm btn-outline" onclick="adminApp.loadAuditLogsData(${page + 1})">
                <i class="fas fa-chevron-right"></i>
            </button>`;
        }

        paginationHTML += '</div>';
        paginationHTML += `<div class="pagination-info">Showing ${((page - 1) * 50) + 1}-${Math.min(page * 50, total)} of ${total} logs</div>`;

        paginationContainer.innerHTML = paginationHTML;
    }

    async filterAuditLogs() {
        await this.loadAuditLogsData(1);
    }

    async clearAuditFilters() {
        document.getElementById('auditLogSearch').value = '';
        document.getElementById('auditActionFilter').value = '';
        document.getElementById('auditDateFrom').value = '';
        document.getElementById('auditDateTo').value = '';
        await this.loadAuditLogsData(1);
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
            this.showToast('Error refreshing data', 'error');
        } finally {
            if (icon) {
                icon.classList.remove('fa-spin');
            }
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
        let retryCount = 0;
        const maxRetries = 3;
        
        const checkStatus = async () => {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout
                
                const response = await fetch('/api/dashboard/stats', {
                    signal: controller.signal,
                    method: 'HEAD' // Use HEAD for lighter requests
                });
                
                clearTimeout(timeoutId);
                const statusDot = document.getElementById('statusDot');
                const statusText = document.getElementById('statusText');
                
                if (response.ok) {
                    statusDot.className = 'status-dot online';
                    statusText.textContent = 'Online';
                    retryCount = 0; // Reset retry count on success
                } else {
                    throw new Error(`HTTP ${response.status}`);
                }
            } catch (error) {
                retryCount++;
                const statusDot = document.getElementById('statusDot');
                const statusText = document.getElementById('statusText');
                
                if (retryCount >= maxRetries) {
                    statusDot.className = 'status-dot offline';
                    statusText.textContent = 'Offline';
                    statusDot.title = `Server Offline (${error.message})`;
                } else {
                    statusDot.className = 'status-dot warning';
                    statusText.textContent = 'Issues';
                    statusDot.title = `Connection issues (Retry ${retryCount}/${maxRetries})`;
                }
            }
        };
        
        // Initial check
        checkStatus();
        
        // Check every 30 seconds
        setInterval(checkStatus, 30000);
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

        this.refreshChartsTheme();
    }

    formatDateTime(value) {
        if (!value) return 'N/A';
        const date = value instanceof Date ? value : new Date(value);
        return Number.isNaN(date.getTime()) ? 'N/A' : date.toLocaleString();
    }

    buildDeliveryMeta(order) {
        if (!order) return '';
        const deliveryMode = order.delivery_mode || 'pickup';
        const isDelivery = deliveryMode === 'delivery';

        if (!isDelivery) {
            return `
                <div class="detail-item">
                    <strong>Fulfilment:</strong> Pickup
                </div>
            `;
        }

        const metaLines = [
            `<div class="detail-item"><strong>Fulfilment:</strong> Delivery</div>`
        ];

        if (order.block) {
            metaLines.push(`<div class="detail-item"><strong>Block:</strong> ${order.block}</div>`);
        }
        if (order.department) {
            metaLines.push(`<div class="detail-item"><strong>Department:</strong> ${order.department}</div>`);
        }
        if (order.classroom) {
            metaLines.push(`<div class="detail-item"><strong>Classroom:</strong> ${order.classroom}</div>`);
        }
        if (order.expected_time) {
            metaLines.push(`<div class="detail-item"><strong>Expected:</strong> ${this.formatDateTime(order.expected_time)}</div>`);
        }

        return metaLines.join('');
    }

    handleLogout() {
        if (confirm('Are you sure you want to logout?')) {
            // Clear any stored data
            localStorage.removeItem('adminSession');
            
            // Redirect to login or home page
            window.location.href = '/';
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

    // Order Management Functions
    async showOrderDetails(orderId) {
        try {
            const response = await fetch(`/api/orders/${orderId}`);
            const order = await response.json();

            if (!response.ok) {
                this.showToast(order?.error || 'Failed to load order details', 'error');
                return;
            }

            const items = this.parseOrderItems(order.items);
            const createdAt = this.formatDateTime(order.created_at);
            const updatedAt = this.formatDateTime(order.updated_at);
            const deliveryMeta = this.buildDeliveryMeta(order);

            this.showModal(`
                <div class="modal-header">
                    <h3><i class="fas fa-shopping-cart"></i> Order Details #${order.id}</h3>
                    <button class="btn btn-ghost" onclick="adminApp.hideModal()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="order-details-grid">
                        <div class="detail-section">
                            <h4>Customer Information</h4>
                            <div class="detail-item">
                                <strong>Name:</strong> ${order.customer_name || 'Unknown'}
                            </div>
                            <div class="detail-item">
                                <strong>Email:</strong> ${order.customer_email || 'N/A'}
                            </div>
                            ${deliveryMeta}
                        </div>
                        
                        <div class="detail-section">
                            <h4>Order Information</h4>
                            <div class="detail-item">
                                <strong>Status:</strong> 
                                <span class="status-badge ${this.getStatusClass(order.status)}">${order.status}</span>
                            </div>
                            <div class="detail-item">
                                <strong>Total:</strong> ₹${Number(order.total_price || 0).toFixed(2)}
                            </div>
                            <div class="detail-item">
                                <strong>OTP:</strong> ${order.otp || 'N/A'}
                            </div>
                            <div class="detail-item">
                                <strong>Created:</strong> ${createdAt}
                            </div>
                            <div class="detail-item">
                                <strong>Updated:</strong> ${updatedAt}
                            </div>
                        </div>
                    </div>
                    
                    <div class="detail-section">
                        <h4>Order Items</h4>
                        <div class="order-items-list">
                            ${items.length === 0 ? `
                                <div class="empty-state compact">
                                    <i class="fas fa-utensils"></i>
                                    <p>No items recorded</p>
                                </div>
                            ` : items.map(item => `
                                <div class="order-item">
                                    <div class="item-info">
                                        <strong>${item.name}</strong>
                                        <span class="item-quantity">Qty: ${item.quantity}</span>
                                    </div>
                                    <div class="item-price">
                                        ${item.price !== null ? `₹${item.price.toFixed(2)}` : '—'}
                                        ${item.subtotal !== null ? `<span class="item-subtotal">Subtotal: ₹${item.subtotal.toFixed(2)}</span>` : ''}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-primary" onclick="adminApp.updateOrderStatus(${orderId})">
                        <i class="fas fa-edit"></i> Update Status
                    </button>
                    <button class="btn btn-outline" onclick="adminApp.hideModal()">Close</button>
                </div>
            `);
        } catch (error) {
            console.error('Error loading order details:', error);
            this.showToast('Error loading order details', 'error');
        }
    }

    // Menu Management Functions
    async editMenuItem(itemId) {
        try {
            const response = await fetch(`/api/menu/${itemId}`);
            const item = await response.json();

            if (response.ok) {
                this.showModal(`
                    <div class="modal-header">
                        <h3><i class="fas fa-edit"></i> Edit Menu Item</h3>
                        <button class="btn btn-ghost" onclick="adminApp.hideModal()">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <form id="editMenuItemForm" class="modal-body">
                        <div class="form-group">
                            <label for="editItemName">Name</label>
                            <input type="text" id="editItemName" class="form-input" value="${item.name}" required>
                        </div>
                        <div class="form-group">
                            <label for="editItemPrice">Price (₹)</label>
                            <input type="number" id="editItemPrice" class="form-input" value="${item.price}" step="0.01" required>
                        </div>
                        <div class="form-group">
                            <label for="editItemCategory">Category</label>
                            <input type="text" id="editItemCategory" class="form-input" value="${item.category}" required>
                        </div>
                        <div class="form-group">
                            <label for="editItemStock">Stock</label>
                            <input type="number" id="editItemStock" class="form-input" value="${item.stock}" min="0">
                        </div>
                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" id="editItemAvailable" ${item.available ? 'checked' : ''}>
                                Available
                            </label>
                        </div>
                        <div class="form-group">
                            <label class="checkbox-label">
                                <input type="checkbox" id="editItemDeliverable" ${item.deliverable ? 'checked' : ''}>
                                Deliverable
                            </label>
                        </div>
                        <div class="form-group">
                            <label for="editItemImage">Update Image (optional)</label>
                            <input type="file" id="editItemImage" class="form-input" accept="image/*">
                        </div>
                    </form>
                    <div class="modal-footer">
                        <button type="submit" form="editMenuItemForm" class="btn btn-primary">
                            <i class="fas fa-save"></i> Save Changes
                        </button>
                        <button class="btn btn-outline" onclick="adminApp.hideModal()">Cancel</button>
                    </div>
                `);

                document.getElementById('editMenuItemForm').addEventListener('submit', async (e) => {
                    e.preventDefault();
                    await this.handleEditMenuItem(itemId);
                });
            } else {
                this.showToast('Failed to load menu item', 'error');
            }
        } catch (error) {
            console.error('Error loading menu item:', error);
            this.showToast('Error loading menu item', 'error');
        }
    }

    async handleEditMenuItem(itemId) {
        try {
            const formData = new FormData();
            formData.append('name', document.getElementById('editItemName').value);
            formData.append('price', document.getElementById('editItemPrice').value);
            formData.append('category', document.getElementById('editItemCategory').value);
            formData.append('stock', document.getElementById('editItemStock').value);
            formData.append('available', document.getElementById('editItemAvailable').checked ? '1' : '0');
            formData.append('deliverable', document.getElementById('editItemDeliverable').checked ? '1' : '0');
            
            const imageFile = document.getElementById('editItemImage').files[0];
            if (imageFile) {
                formData.append('image', imageFile);
            }

            const response = await fetch(`/api/menu/${itemId}`, {
                method: 'PUT',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                this.showToast('Menu item updated successfully', 'success');
                this.hideModal();
                await this.loadMenuData();
            } else {
                this.showToast(result.error || 'Failed to update menu item', 'error');
            }
        } catch (error) {
            console.error('Error updating menu item:', error);
            this.showToast('Error updating menu item', 'error');
        }
    }

    async toggleMenuAvailability(itemId) {
        try {
            const response = await fetch(`/api/menu/${itemId}/toggle`, {
                method: 'PUT'
            });

            const result = await response.json();

            if (response.ok) {
                this.showToast('Menu item availability updated', 'success');
                await this.loadMenuData();
            } else {
                this.showToast(result.error || 'Failed to update availability', 'error');
            }
        } catch (error) {
            console.error('Error toggling availability:', error);
            this.showToast('Error updating availability', 'error');
        }
    }

    // Filter Functions
    filterMenu() {
        const searchTerm = document.getElementById('menuSearch')?.value.toLowerCase() || '';
        const categoryFilter = document.getElementById('menuCategoryFilter')?.value || '';
        const stockFilter = document.getElementById('menuStockFilter')?.value || '';

        console.log('Filtering menu:', { searchTerm, categoryFilter, stockFilter });

        // Filter grid view items
        const gridItems = document.querySelectorAll('.menu-card');
        gridItems.forEach(item => {
            const name = item.querySelector('.menu-card-title')?.textContent.toLowerCase() || '';
            const category = item.querySelector('.menu-card-category')?.textContent || '';
            const stockText = item.querySelector('.stock')?.textContent || '';
            const stock = parseInt(stockText.match(/\d+/)?.[0] || '0');

            const matchesSearch = name.includes(searchTerm) || category.toLowerCase().includes(searchTerm);
            const matchesCategory = !categoryFilter || category === categoryFilter;
            
            let matchesStock = true;
            if (stockFilter === 'low') matchesStock = stock < this.lowStockThreshold;
            else if (stockFilter === 'out') matchesStock = stock === 0;
            else if (stockFilter === 'in') matchesStock = stock > 0;

            item.style.display = (matchesSearch && matchesCategory && matchesStock) ? '' : 'none';
        });

        // Filter table view items
        const tableRows = document.querySelectorAll('#menuTableBody tr');
        tableRows.forEach(row => {
            const name = row.querySelector('.item-name')?.textContent.toLowerCase() || '';
            const category = row.cells[3]?.textContent || ''; // Category is in 4th column
            const stockText = row.querySelector('.stock-number')?.textContent || '';
            const stock = parseInt(stockText || '0');

            const matchesSearch = name.includes(searchTerm) || category.toLowerCase().includes(searchTerm);
            const matchesCategory = !categoryFilter || category === categoryFilter;
            
            let matchesStock = true;
            if (stockFilter === 'low') matchesStock = stock < this.lowStockThreshold;
            else if (stockFilter === 'out') matchesStock = stock === 0;
            else if (stockFilter === 'in') matchesStock = stock > 0;

            row.style.display = (matchesSearch && matchesCategory && matchesStock) ? '' : 'none';
        });
    }

    filterOrders() {
        const searchTerm = document.getElementById('orderSearch')?.value.toLowerCase() || '';
        const statusFilter = document.getElementById('orderStatusFilter')?.value || '';
        const fromDate = document.getElementById('orderDateFrom')?.value || '';
        const toDate = document.getElementById('orderDateTo')?.value || '';

        console.log('Filtering orders:', { searchTerm, statusFilter, fromDate, toDate });

        const tableRows = document.querySelectorAll('#ordersTableBody tr');
        tableRows.forEach(row => {
            const orderId = row.cells[0]?.textContent.toLowerCase() || '';
            const customerName = row.cells[1]?.textContent.toLowerCase() || '';
            const status = row.cells[2]?.textContent || '';
            const orderDate = row.cells[4]?.textContent || '';

            const matchesSearch = orderId.includes(searchTerm) || customerName.includes(searchTerm);
            const matchesStatus = !statusFilter || status === statusFilter;
            
            let matchesDate = true;
            if (fromDate && toDate) {
                const orderDateObj = new Date(orderDate);
                const fromDateObj = new Date(fromDate);
                const toDateObj = new Date(toDate);
                matchesDate = orderDateObj >= fromDateObj && orderDateObj <= toDateObj;
            }

            row.style.display = (matchesSearch && matchesStatus && matchesDate) ? '' : 'none';
        });
    }

    filterUsers() {
        const searchTerm = document.getElementById('userSearch')?.value.toLowerCase() || '';
        const roleFilter = document.getElementById('userRoleFilter')?.value || '';
        const statusFilter = document.getElementById('userStatusFilter')?.value || '';

        console.log('Filtering users:', { searchTerm, roleFilter, statusFilter });

        const tableRows = document.querySelectorAll('#usersTableBody tr');
        tableRows.forEach(row => {
            const username = row.cells[1]?.textContent.toLowerCase() || '';
            const email = row.cells[2]?.textContent.toLowerCase() || '';
            const role = row.cells[3]?.textContent || '';
            const status = row.cells[4]?.textContent || '';

            const matchesSearch = username.includes(searchTerm) || email.includes(searchTerm);
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

    filterAuditLogs() {
        const searchTerm = document.getElementById('auditLogSearch')?.value.toLowerCase() || '';
        const actionFilter = document.getElementById('auditActionFilter')?.value || '';
        const fromDate = document.getElementById('auditDateFrom')?.value || '';
        const toDate = document.getElementById('auditDateTo')?.value || '';

        console.log('Filtering audit logs:', { searchTerm, actionFilter, fromDate, toDate });

        const tableRows = document.querySelectorAll('#auditLogsTableBody tr');
        tableRows.forEach(row => {
            const action = row.cells[1]?.textContent || '';
            const admin = row.cells[2]?.textContent.toLowerCase() || '';
            const details = row.cells[3]?.textContent.toLowerCase() || '';
            const timestamp = row.cells[4]?.textContent || '';

            const matchesSearch = admin.includes(searchTerm) || details.includes(searchTerm);
            const matchesAction = !actionFilter || action === actionFilter;
            
            let matchesDate = true;
            if (fromDate && toDate) {
                const logDate = new Date(timestamp);
                const fromDateObj = new Date(fromDate);
                const toDateObj = new Date(toDate);
                matchesDate = logDate >= fromDateObj && logDate <= toDateObj;
            }

            row.style.display = (matchesSearch && matchesAction && matchesDate) ? '' : 'none';
        });
    }

    clearReportData() {
        const reportResults = document.getElementById('reportResults');
        if (reportResults) {
            reportResults.innerHTML = '<div class="empty-state"><i class="fas fa-chart-bar"></i><h3>No Report Generated</h3><p>Select a report type and date range, then click Generate Report.</p></div>';
        }
        
        document.getElementById('exportReportBtn').disabled = true;
        this.currentReportData = null;
    }

    async deleteMenuItem(itemId) {
        if (!confirm('Are you sure you want to delete this menu item?')) {
            return;
        }

        try {
            const response = await fetch(`/api/menu/${itemId}`, {
                method: 'DELETE'
            });

            const result = await response.json();

            if (response.ok) {
                this.showToast('Menu item deleted successfully', 'success');
                await this.loadMenuData();
            } else {
                this.showToast(result.error || 'Failed to delete menu item', 'error');
            }
        } catch (error) {
            console.error('Error deleting menu item:', error);
            this.showToast('Error deleting menu item', 'error');
        }
    }

    // Bulk Operations for Menu
    toggleSelectAllMenu(checked) {
        const checkboxes = document.querySelectorAll('.menu-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = checked;
        });
        
        this.selectedItems.clear();
        if (checked) {
            checkboxes.forEach(checkbox => {
                this.selectedItems.add(checkbox.dataset.itemId);
            });
        }
        
        this.updateBulkActionButtons();
    }

    async bulkDeleteMenuItems() {
        if (this.selectedItems.size === 0) {
            this.showToast('No items selected', 'warning');
            return;
        }

        if (!confirm(`Are you sure you want to delete ${this.selectedItems.size} selected items?`)) {
            return;
        }

        try {
            const promises = Array.from(this.selectedItems).map(itemId => 
                fetch(`/api/menu/${itemId}`, { method: 'DELETE' })
            );
            
            await Promise.all(promises);
            this.showToast(`${this.selectedItems.size} items deleted successfully`, 'success');
            this.selectedItems.clear();
            await this.loadMenuData();
        } catch (error) {
            console.error('Error deleting menu items:', error);
            this.showToast('Error deleting menu items', 'error');
        }
    }

    async bulkToggleMenuAvailability() {
        if (this.selectedItems.size === 0) {
            this.showToast('No items selected', 'warning');
            return;
        }

        try {
            const promises = Array.from(this.selectedItems).map(itemId => 
                fetch(`/api/menu/${itemId}/toggle`, { method: 'PUT' })
            );
            
            await Promise.all(promises);
            this.showToast(`${this.selectedItems.size} items updated successfully`, 'success');
            this.selectedItems.clear();
            await this.loadMenuData();
        } catch (error) {
            console.error('Error updating menu items:', error);
            this.showToast('Error updating menu items', 'error');
        }
    }

    updateBulkActionButtons() {
        const selectedCount = this.selectedItems.size;
        const bulkActions = document.getElementById('bulkMenuActions');
        
        if (bulkActions) {
            bulkActions.style.display = selectedCount > 0 ? 'flex' : 'none';
            
            const countSpan = bulkActions.querySelector('.selected-count');
            if (countSpan) {
                countSpan.textContent = selectedCount;
            }
        }
    }

    // Bulk Operations for Menu
    toggleSelectAllMenu(checked) {
        const checkboxes = document.querySelectorAll('.menu-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = checked;
        });
        
        this.selectedItems.clear();
        if (checked) {
            checkboxes.forEach(checkbox => {
                this.selectedItems.add(checkbox.dataset.itemId);
            });
        }
        
        this.updateBulkActionButtons();
    }

    async bulkDeleteMenuItems() {
        if (this.selectedItems.size === 0) {
            this.showToast('No items selected', 'warning');
            return;
        }

        if (!confirm(`Are you sure you want to delete ${this.selectedItems.size} selected items?`)) {
            return;
        }

        try {
            const promises = Array.from(this.selectedItems).map(itemId => 
                fetch(`/api/menu/${itemId}`, { method: 'DELETE' })
            );
            
            await Promise.all(promises);
            this.showToast(`${this.selectedItems.size} items deleted successfully`, 'success');
            this.selectedItems.clear();
            await this.loadMenuData();
        } catch (error) {
            console.error('Error deleting menu items:', error);
            this.showToast('Error deleting menu items', 'error');
        }
    }

    async bulkToggleMenuAvailability() {
        if (this.selectedItems.size === 0) {
            this.showToast('No items selected', 'warning');
            return;
        }

        try {
            const promises = Array.from(this.selectedItems).map(itemId => 
                fetch(`/api/menu/${itemId}/toggle`, { method: 'PUT' })
            );
            
            await Promise.all(promises);
            this.showToast(`${this.selectedItems.size} items updated successfully`, 'success');
            this.selectedItems.clear();
            await this.loadMenuData();
        } catch (error) {
            console.error('Error updating menu items:', error);
            this.showToast('Error updating menu items', 'error');
        }
    }

    updateBulkActionButtons() {
        const selectedCount = this.selectedItems.size;
        const bulkActions = document.getElementById('bulkMenuActions');
        
        if (bulkActions) {
            bulkActions.style.display = selectedCount > 0 ? 'flex' : 'none';
            
            const countSpan = bulkActions.querySelector('.selected-count');
            if (countSpan) {
                countSpan.textContent = selectedCount;
            }
        }
    }

    // Modal Functions
    showModal(content) {
        const modalOverlay = document.getElementById('modalOverlay');
        const modalContent = document.getElementById('modalContent');
        
        if (modalOverlay && modalContent) {
            modalContent.innerHTML = content;
            modalOverlay.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    }

    hideModal() {
        const modalOverlay = document.getElementById('modalOverlay');
        if (modalOverlay) {
            modalOverlay.classList.add('hidden');
            document.body.style.overflow = '';
        }
    }

    // Notification Functions
    toggleNotificationCenter() {
        const notificationCenter = document.getElementById('notificationCenter');
        if (notificationCenter) {
            const isHidden = notificationCenter.classList.contains('hidden');
            if (isHidden) {
                this.showNotificationCenter();
            } else {
                this.hideNotificationCenter();
            }
        }
    }

    showNotificationCenter() {
        const notificationCenter = document.getElementById('notificationCenter');
        if (notificationCenter) {
            notificationCenter.classList.remove('hidden');
            this.loadNotifications();
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
            } else {
                // If no API endpoint exists, show sample notifications
                this.renderNotifications(this.getSampleNotifications());
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
            // Show sample notifications as fallback
            this.renderNotifications(this.getSampleNotifications());
        }
    }

    getSampleNotifications() {
        return [
            {
                id: 1,
                type: 'warning',
                title: 'Low Stock Alert',
                message: '1 item is running low on stock',
                timestamp: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
                read: false
            },
            {
                id: 2,
                type: 'info',
                title: 'New Order',
                message: 'Order #6 has been placed by sonu',
                timestamp: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
                read: false
            },
            {
                id: 3,
                type: 'success',
                title: 'Order Completed',
                message: 'Order #4 has been completed successfully',
                timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
                read: true
            },
            {
                id: 4,
                type: 'info',
                title: 'User Registration',
                message: 'New user registration pending approval',
                timestamp: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
                read: true
            }
        ];
    }

    renderNotifications(notifications) {
        const notificationList = document.getElementById('notificationList');
        if (!notificationList) return;

        if (notifications.length === 0) {
            notificationList.innerHTML = `
                <div class="empty-notification">
                    <i class="fas fa-bell-slash"></i>
                    <p>No notifications</p>
                </div>
            `;
            return;
        }

        notificationList.innerHTML = notifications.map(notification => {
            const timeAgo = this.getTimeAgo(new Date(notification.timestamp));
            const iconClass = this.getNotificationIcon(notification.type);
            
            return `
                <div class="notification-item ${notification.read ? 'read' : 'unread'}" 
                     data-id="${notification.id}" 
                     data-type="${notification.type}" 
                     data-title="${notification.title}" 
                     onclick="adminApp.handleNotificationClick('${notification.type}', '${notification.title}', ${notification.id})">
                    <div class="notification-icon ${notification.type}">
                        <i class="${iconClass}"></i>
                    </div>
                    <div class="notification-content">
                        <div class="notification-title">${notification.title}</div>
                        <div class="notification-message">${notification.message}</div>
                        <div class="notification-time">${timeAgo}</div>
                    </div>
                    ${!notification.read ? '<div class="notification-dot"></div>' : ''}
                </div>
            `;
        }).join('');

        // Update notification badge
        this.updateNotificationBadge(notifications);
    }

    getNotificationIcon(type) {
        const icons = {
            'success': 'fas fa-check-circle',
            'warning': 'fas fa-exclamation-triangle',
            'danger': 'fas fa-exclamation-circle',
            'info': 'fas fa-info-circle',
            'default': 'fas fa-bell'
        };
        return icons[type] || icons.default;
    }

    getTimeAgo(date) {
        const now = new Date();
        const diffMs = now - date;
        const diffMinutes = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffMinutes < 1) return 'Just now';
        if (diffMinutes < 60) return `${diffMinutes}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${diffDays}d ago`;
    }

    updateNotificationBadge(notifications) {
        const notificationBtn = document.getElementById('notificationBtn');
        const unreadCount = notifications.filter(n => !n.read).length;
        
        // Remove existing badge
        const existingBadge = notificationBtn.querySelector('.notification-badge');
        if (existingBadge) {
            existingBadge.remove();
        }

        // Add new badge if there are unread notifications
        if (unreadCount > 0) {
            const badge = document.createElement('span');
            badge.className = 'notification-badge';
            badge.textContent = unreadCount > 99 ? '99+' : unreadCount;
            notificationBtn.appendChild(badge);
        }
    }

    handleNotificationClick(type, title, notificationId) {
        // Mark notification as read
        this.markNotificationAsRead(notificationId);
        
        // Navigate based on notification type
        switch(type) {
            case 'warning':
                if (title.includes('Low Stock')) {
                    this.showPage('menu');
                    // Focus on low stock filter
                    setTimeout(() => {
                        const stockFilter = document.getElementById('menuStockFilter');
                        if (stockFilter) {
                            stockFilter.value = 'low';
                            stockFilter.dispatchEvent(new Event('change'));
                        }
                    }, 300);
                }
                break;
            
            case 'info':
                if (title.includes('New Order')) {
                    this.showPage('orders');
                    // Focus on recent orders
                    setTimeout(() => {
                        const statusFilter = document.getElementById('orderStatusFilter');
                        if (statusFilter) {
                            statusFilter.value = 'Order Received';
                            statusFilter.dispatchEvent(new Event('change'));
                        }
                    }, 300);
                } else if (title.includes('User Registration')) {
                    this.showPage('users');
                    // Focus on pending users
                    setTimeout(() => {
                        const statusFilter = document.getElementById('userStatusFilter');
                        if (statusFilter) {
                            statusFilter.value = 'pending';
                            statusFilter.dispatchEvent(new Event('change'));
                        }
                    }, 300);
                }
                break;
            
            case 'success':
                if (title.includes('Order Completed')) {
                    this.showPage('orders');
                    // Focus on completed orders
                    setTimeout(() => {
                        const statusFilter = document.getElementById('orderStatusFilter');
                        if (statusFilter) {
                            statusFilter.value = 'Completed';
                            statusFilter.dispatchEvent(new Event('change'));
                        }
                    }, 300);
                }
                break;
            
            default:
                // Default navigation to dashboard
                this.showPage('dashboard');
                break;
        }
        
        // Close notification center
        this.hideNotificationCenter();
        
        // Show toast for feedback
        this.showToast('Navigated to relevant section', 'info');
    }
    
    markNotificationAsRead(notificationId) {
        // Update the notification item visually
        const notificationItem = document.querySelector(`[data-id="${notificationId}"]`);
        if (notificationItem) {
            notificationItem.classList.remove('unread');
            notificationItem.classList.add('read');
            
            // Remove the notification dot
            const dot = notificationItem.querySelector('.notification-dot');
            if (dot) {
                dot.remove();
            }
        }
        
        // Update badge count
        const currentNotifications = this.getSampleNotifications();
        const updatedNotifications = currentNotifications.map(n => 
            n.id === notificationId ? { ...n, read: true } : n
        );
        this.updateNotificationBadge(updatedNotifications);
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