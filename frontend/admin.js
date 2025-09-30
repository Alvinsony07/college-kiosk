// Admin Panel JavaScript - College Canteen Management System
// Backend: Flask app running on localhost:5000
// All endpoints use /api prefix

// ========== Configuration ==========
const CONFIG = {
    API_BASE: 'http://localhost:5000/api',
    IMAGE_BASE: 'http://localhost:5000/static/images',
    POLLING_INTERVAL: 8000, // 8 seconds
    LOW_STOCK_THRESHOLD: 10
};

// ========== State Management ==========
const state = {
    admin: null,
    pollingEnabled: true,
    pollingInterval: null,
    currentPage: 'dashboard',
    orders: [],
    menu: [],
    users: [],
    pendingUsers: [],
    settings: {
        lowStockThreshold: 10
    }
};

// ========== Utility Functions ==========
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

function formatCurrency(amount) {
    return `₹${parseFloat(amount).toFixed(2)}`;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
}

function confirmAction(message) {
    return confirm(message);
}

// ========== API Functions ==========
async function apiCall(endpoint, method = 'GET', body = null, isFormData = false) {
    try {
        const options = {
            method,
            headers: {}
        };

        if (body && !isFormData) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(body);
        } else if (body && isFormData) {
            options.body = body;
        }

        const response = await fetch(`${CONFIG.API_BASE}${endpoint}`, options);
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// ========== Authentication ==========
function checkAuth() {
    const admin = sessionStorage.getItem('admin');
    if (!admin) {
        showLoginPage();
        return false;
    }
    state.admin = JSON.parse(admin);
    return true;
}

function showLoginPage() {
    document.getElementById('loginPage').style.display = 'flex';
    document.getElementById('adminPanel').style.display = 'none';
}

function showAdminPanel() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('adminPanel').style.display = 'flex';
    document.getElementById('adminEmail').textContent = state.admin.email;
    loadPage('dashboard');
    startPolling();
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const errorEl = document.getElementById('loginError');

    try {
        const data = await apiCall('/login', 'POST', { email, password });
        
        if (data.role !== 'admin') {
            errorEl.textContent = 'Unauthorized: Admin access required';
            errorEl.classList.add('show');
            return;
        }

        state.admin = data;
        sessionStorage.setItem('admin', JSON.stringify(data));
        showAdminPanel();
    } catch (error) {
        errorEl.textContent = error.message || 'Login failed';
        errorEl.classList.add('show');
    }
}

function handleLogout() {
    if (confirmAction('Are you sure you want to logout?')) {
        sessionStorage.removeItem('admin');
        state.admin = null;
        stopPolling();
        showLoginPage();
    }
}

// ========== Polling ==========
function startPolling() {
    if (state.pollingEnabled && !state.pollingInterval) {
        state.pollingInterval = setInterval(() => {
            if (state.currentPage === 'dashboard') {
                loadDashboard();
            } else if (state.currentPage === 'orders') {
                loadOrders();
            }
            updateLastRefresh();
        }, CONFIG.POLLING_INTERVAL);
    }
}

function stopPolling() {
    if (state.pollingInterval) {
        clearInterval(state.pollingInterval);
        state.pollingInterval = null;
    }
}

function togglePolling() {
    state.pollingEnabled = !state.pollingEnabled;
    if (state.pollingEnabled) {
        startPolling();
    } else {
        stopPolling();
    }
}

function updateLastRefresh() {
    const now = new Date();
    document.getElementById('lastRefresh').textContent = 
        `Last refresh: ${now.toLocaleTimeString()}`;
}

// ========== Page Navigation ==========
function loadPage(pageName) {
    state.currentPage = pageName;
    
    // Update nav active state
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === pageName) {
            item.classList.add('active');
        }
    });

    // Update page title
    document.querySelector('.page-title').textContent = 
        pageName.charAt(0).toUpperCase() + pageName.slice(1);

    // Load page content
    const content = document.getElementById('pageContent');
    
    switch(pageName) {
        case 'dashboard':
            loadDashboard();
            break;
        case 'orders':
            loadOrders();
            break;
        case 'menu':
            loadMenu();
            break;
        case 'inventory':
            loadInventory();
            break;
        case 'users':
            loadUsers();
            break;
        case 'reports':
            loadReports();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// ========== Dashboard Page ==========
async function loadDashboard() {
    const content = document.getElementById('pageContent');
    content.innerHTML = '<div class=\"loading\">Loading dashboard...</div>';

    try {
        // Fetch data
        const [orders, menu] = await Promise.all([
            apiCall('/orders'),
            apiCall('/menu')
        ]);

        state.orders = orders;
        state.menu = menu;

        // Calculate KPIs
        const totalOrders = orders.length;
        const totalRevenue = orders.reduce((sum, order) => sum + order.total_price, 0);
        const activeOrders = orders.filter(o => 
            o.status !== 'Completed' && o.status !== 'Cancelled'
        ).length;
        const lowStockItems = menu.filter(item => 
            item.stock <= state.settings.lowStockThreshold
        ).length;

        // Render dashboard
        content.innerHTML = `
            <div class=\"kpi-grid\">
                <div class=\"kpi-card\">
                    <div class=\"kpi-icon\">📦</div>
                    <div class=\"kpi-label\">Total Orders</div>
                    <div class=\"kpi-value\">${totalOrders}</div>
                </div>
                <div class=\"kpi-card\">
                    <div class=\"kpi-icon\">💰</div>
                    <div class=\"kpi-label\">Total Revenue</div>
                    <div class=\"kpi-value\">${formatCurrency(totalRevenue)}</div>
                </div>
                <div class=\"kpi-card\">
                    <div class=\"kpi-icon\">🔥</div>
                    <div class=\"kpi-label\">Active Orders</div>
                    <div class=\"kpi-value\">${activeOrders}</div>
                </div>
                <div class=\"kpi-card\">
                    <div class=\"kpi-icon\">⚠️</div>
                    <div class=\"kpi-label\">Low Stock Items</div>
                    <div class=\"kpi-value\">${lowStockItems}</div>
                </div>
            </div>

            <div class=\"charts-grid\">
                <div class=\"chart-card\">
                    <h3>Top Selling Items</h3>
                    <canvas id=\"topSellingChart\"></canvas>
                </div>
                <div class=\"chart-card\">
                    <h3>Category Distribution</h3>
                    <canvas id=\"categoryChart\"></canvas>
                </div>
            </div>
        `;

        // Render charts
        renderTopSellingChart(orders, menu);
        renderCategoryChart(menu);
        updateLastRefresh();

    } catch (error) {
        content.innerHTML = `<div class=\"error\">Error loading dashboard: ${error.message}</div>`;
    }
}

function renderTopSellingChart(orders, menu) {
    const itemSales = {};
    
    // Calculate sales per item
    orders.forEach(order => {
        if (order.items && Array.isArray(order.items)) {
            order.items.forEach(item => {
                if (!itemSales[item.id]) {
                    itemSales[item.id] = { qty: 0, name: item.name };
                }
                itemSales[item.id].qty += item.qty;
            });
        }
    });

    // Sort and get top 5
    const topItems = Object.values(itemSales)
        .sort((a, b) => b.qty - a.qty)
        .slice(0, 5);

    const ctx = document.getElementById('topSellingChart');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: topItems.map(item => item.name),
            datasets: [{
                label: 'Quantity Sold',
                data: topItems.map(item => item.qty),
                backgroundColor: 'rgba(16, 185, 129, 0.8)',
                borderColor: 'rgba(16, 185, 129, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function renderCategoryChart(menu) {
    const categories = {};
    
    menu.forEach(item => {
        categories[item.category] = (categories[item.category] || 0) + 1;
    });

    const ctx = document.getElementById('categoryChart');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(categories),
            datasets: [{
                data: Object.values(categories),
                backgroundColor: [
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(6, 182, 212, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(139, 92, 246, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true
        }
    });
}

// ========== Orders Page ==========
async function loadOrders() {
    const content = document.getElementById('pageContent');
    content.innerHTML = '<div class=\"loading\">Loading orders...</div>';

    try {
        const orders = await apiCall('/orders');
        state.orders = orders;

        content.innerHTML = `
            <div class=\"table-controls\">
                <input type=\"text\" id=\"orderSearch\" class=\"search-box\" placeholder=\"Search by email or ID...\">
                <div class=\"filter-group\">
                    <select id=\"statusFilter\" class=\"search-box\" style=\"min-width: 150px;\">
                        <option value=\"\">All Statuses</option>
                        <option value=\"Order Received\">Order Received</option>
                        <option value=\"Preparing\">Preparing</option>
                        <option value=\"Ready\">Ready</option>
                        <option value=\"Completed\">Completed</option>
                    </select>
                </div>
            </div>

            <div class=\"table-container\">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Customer</th>
                            <th>Items</th>
                            <th>Total</th>
                            <th>OTP</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id=\"ordersTableBody\">
                    </tbody>
                </table>
            </div>
        `;

        renderOrdersTable(orders);

        // Add event listeners
        document.getElementById('orderSearch').addEventListener('input', filterOrders);
        document.getElementById('statusFilter').addEventListener('change', filterOrders);

    } catch (error) {
        content.innerHTML = `<div class=\"error\">Error loading orders: ${error.message}</div>`;
    }
}

function renderOrdersTable(orders) {
    const tbody = document.getElementById('ordersTableBody');
    
    if (orders.length === 0) {
        tbody.innerHTML = '<tr><td colspan=\"7\" class=\"text-center\">No orders found</td></tr>';
        return;
    }

    tbody.innerHTML = orders.map(order => `
        <tr>
            <td>#${order.id}</td>
            <td>
                <div>${order.customer_name}</div>
                <div class=\"text-secondary\" style=\"font-size: 0.85rem;\">${order.customer_email}</div>
            </td>
            <td>${order.items.length} item(s)</td>
            <td>${formatCurrency(order.total_price)}</td>
            <td><strong>${order.otp}</strong></td>
            <td><span class=\"status-badge status-${order.status.toLowerCase().replace(' ', '-')}\">${order.status}</span></td>
            <td>
                <button class=\"btn-icon\" onclick=\"viewOrder(${order.id})\">👁️</button>
                <button class=\"btn-icon\" onclick=\"updateOrderStatus(${order.id})\">✏️</button>
            </td>
        </tr>
    `).join('');
}

function filterOrders() {
    const searchTerm = document.getElementById('orderSearch').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;

    const filtered = state.orders.filter(order => {
        const matchesSearch = !searchTerm || 
            order.customer_email.toLowerCase().includes(searchTerm) ||
            order.id.toString().includes(searchTerm);
        const matchesStatus = !statusFilter || order.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    renderOrdersTable(filtered);
}

function viewOrder(orderId) {
    const order = state.orders.find(o => o.id === orderId);
    if (!order) return;

    const itemsHtml = order.items.map(item => `
        <div style=\"display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; padding: 0.75rem; background: var(--bg-secondary); border-radius: 8px;\">
            <div style=\"flex: 1;\">
                <div style=\"font-weight: 600;\">${item.name}</div>
                <div class=\"text-secondary\">Quantity: ${item.qty}</div>
            </div>
        </div>
    `).join('');

    // Progress calculation
    const statusSteps = ['Order Received', 'Preparing', 'Ready', 'Completed'];
    const currentStep = statusSteps.indexOf(order.status);
    const progress = currentStep >= 0 ? ((currentStep + 1) / statusSteps.length) * 100 : 0;

    showModal('Order Details', `
        <div>
            <div class=\"mb-2\"><strong>Order ID:</strong> #${order.id}</div>
            <div class=\"mb-2\"><strong>Customer:</strong> ${order.customer_name}</div>
            <div class=\"mb-2\"><strong>Email:</strong> ${order.customer_email}</div>
            <div class=\"mb-2\"><strong>OTP:</strong> <strong style=\"font-size: 1.2rem;\">${order.otp}</strong></div>
            <div class=\"mb-2\"><strong>Total:</strong> ${formatCurrency(order.total_price)}</div>
            <div class=\"mb-3\">
                <strong>Status:</strong> 
                <span class=\"status-badge status-${order.status.toLowerCase().replace(' ', '-')}\">${order.status}</span>
                <div class=\"progress-bar\">
                    <div class=\"progress-fill\" style=\"width: ${progress}%\"></div>
                </div>
            </div>
            <h3 class=\"mb-2\">Items</h3>
            ${itemsHtml}
        </div>
    `);
}

function updateOrderStatus(orderId) {
    const order = state.orders.find(o => o.id === orderId);
    if (!order) return;

    showModal('Update Order Status', `
        <form id=\"updateStatusForm\">
            <div class=\"form-group\">
                <label>Current Status: <strong>${order.status}</strong></label>
            </div>
            <div class=\"form-group\">
                <label>New Status</label>
                <select id=\"newStatus\" class=\"form-group\" required>
                    <option value=\"Order Received\">Order Received</option>
                    <option value=\"Preparing\">Preparing</option>
                    <option value=\"Ready\">Ready</option>
                    <option value=\"Completed\">Completed</option>
                </select>
            </div>
        </form>
    `, async () => {
        const newStatus = document.getElementById('newStatus').value;
        try {
            await apiCall(`/orders/${orderId}/status`, 'PUT', { status: newStatus });
            showToast('Order status updated successfully');
            closeModal();
            loadOrders();
        } catch (error) {
            showToast('Failed to update order status: ' + error.message, 'error');
        }
    });
}

// ========== Menu Page ==========
async function loadMenu() {
    const content = document.getElementById('pageContent');
    content.innerHTML = '<div class=\"loading\">Loading menu...</div>';

    try {
        const menu = await apiCall('/menu');
        state.menu = menu;

        content.innerHTML = `
            <div class=\"table-controls\">
                <input type=\"text\" id=\"menuSearch\" class=\"search-box\" placeholder=\"Search menu items...\">
                <button class=\"btn btn-success\" onclick=\"addMenuItem()\">+ Add Menu Item</button>
            </div>

            <div id=\"menuGrid\" class=\"menu-grid\"></div>
        `;

        renderMenuGrid(menu);
        
        document.getElementById('menuSearch').addEventListener('input', filterMenu);

    } catch (error) {
        content.innerHTML = `<div class=\"error\">Error loading menu: ${error.message}</div>`;
    }
}

function renderMenuGrid(menu) {
    const grid = document.getElementById('menuGrid');
    
    if (menu.length === 0) {
        grid.innerHTML = '<div class=\"text-center\">No menu items found</div>';
        return;
    }

    grid.innerHTML = menu.map(item => `
        <div class=\"menu-item-card\">
            <img src=\"${CONFIG.IMAGE_BASE}/${item.image}\" alt=\"${item.name}\" class=\"menu-item-image\" onerror=\"this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22280%22 height=%22200%22%3E%3Crect fill=%22%23ddd%22 width=%22280%22 height=%22200%22/%3E%3Ctext fill=%22%23999%22 font-family=%22sans-serif%22 font-size=%2218%22 dy=%2210.5%22 font-weight=%22bold%22 x=%2250%25%22 y=%2250%25%22 text-anchor=%22middle%22%3ENo Image%3C/text%3E%3C/svg%3E'\">
            <div class=\"menu-item-content\">
                <div class=\"menu-item-header\">
                    <div class=\"menu-item-name\">${item.name}</div>
                    <div class=\"menu-item-price\">${formatCurrency(item.price)}</div>
                </div>
                <div class=\"menu-item-meta\">
                    <span class=\"badge badge-category\">${item.category}</span>
                    <span class=\"badge ${item.stock <= state.settings.lowStockThreshold ? 'badge-low-stock' : 'badge-stock'}\">
                        Stock: ${item.stock}
                    </span>
                    ${item.deliverable ? '<span class=\"badge badge-stock\">Deliverable</span>' : ''}
                </div>
                <div class=\"menu-item-actions\">
                    <button class=\"btn-icon\" onclick=\"toggleAvailability(${item.id})\" title=\"${item.available ? 'Mark Unavailable' : 'Mark Available'}\">
                        ${item.available ? '✅' : '❌'}
                    </button>
                    <button class=\"btn-icon\" onclick=\"editMenuItem(${item.id})\" title=\"Edit\">✏️</button>
                    <button class=\"btn-icon\" onclick=\"deleteMenuItem(${item.id})\" title=\"Delete\">🗑️</button>
                </div>
            </div>
        </div>
    `).join('');
}

function filterMenu() {
    const searchTerm = document.getElementById('menuSearch').value.toLowerCase();
    const filtered = state.menu.filter(item => 
        item.name.toLowerCase().includes(searchTerm) ||
        item.category.toLowerCase().includes(searchTerm)
    );
    renderMenuGrid(filtered);
}

function addMenuItem() {
    showModal('Add Menu Item', `
        <form id=\"addMenuForm\" enctype=\"multipart/form-data\">
            <div class=\"form-group\">
                <label>Item Name</label>
                <input type=\"text\" id=\"itemName\" required>
            </div>
            <div class=\"form-group\">
                <label>Price (₹)</label>
                <input type=\"number\" id=\"itemPrice\" step=\"0.01\" required>
            </div>
            <div class=\"form-group\">
                <label>Category</label>
                <select id=\"itemCategory\" required>
                    <option value=\"Snacks\">Snacks</option>
                    <option value=\"Beverages\">Beverages</option>
                    <option value=\"Main Course\">Main Course</option>
                    <option value=\"Desserts\">Desserts</option>
                    <option value=\"Fast Food\">Fast Food</option>
                </select>
            </div>
            <div class=\"form-group\">
                <label>Stock Quantity</label>
                <input type=\"number\" id=\"itemStock\" value=\"0\" required>
            </div>
            <div class=\"form-group\">
                <label>
                    <input type=\"checkbox\" id=\"itemDeliverable\" style=\"width: auto; margin-right: 0.5rem;\">
                    Deliverable
                </label>
            </div>
            <div class=\"form-group\">
                <label>Image</label>
                <input type=\"file\" id=\"itemImage\" accept=\"image/*\" required>
            </div>
        </form>
    `, async () => {
        const formData = new FormData();
        formData.append('name', document.getElementById('itemName').value);
        formData.append('price', document.getElementById('itemPrice').value);
        formData.append('category', document.getElementById('itemCategory').value);
        formData.append('stock', document.getElementById('itemStock').value);
        formData.append('deliverable', document.getElementById('itemDeliverable').checked ? 1 : 0);
        formData.append('image', document.getElementById('itemImage').files[0]);

        try {
            await apiCall('/menu', 'POST', formData, true);
            showToast('Menu item added successfully');
            closeModal();
            loadMenu();
        } catch (error) {
            showToast('Failed to add menu item: ' + error.message, 'error');
        }
    });
}

function editMenuItem(itemId) {
    const item = state.menu.find(m => m.id === itemId);
    if (!item) return;

    showModal('Edit Menu Item', `
        <form id=\"editMenuForm\">
            <div class=\"form-group\">
                <label>Item Name</label>
                <input type=\"text\" id=\"editItemName\" value=\"${item.name}\" required>
            </div>
            <div class=\"form-group\">
                <label>Price (₹)</label>
                <input type=\"number\" id=\"editItemPrice\" value=\"${item.price}\" step=\"0.01\" required>
            </div>
            <div class=\"form-group\">
                <label>Category</label>
                <select id=\"editItemCategory\" required>
                    <option value=\"Snacks\" ${item.category === 'Snacks' ? 'selected' : ''}>Snacks</option>
                    <option value=\"Beverages\" ${item.category === 'Beverages' ? 'selected' : ''}>Beverages</option>
                    <option value=\"Main Course\" ${item.category === 'Main Course' ? 'selected' : ''}>Main Course</option>
                    <option value=\"Desserts\" ${item.category === 'Desserts' ? 'selected' : ''}>Desserts</option>
                    <option value=\"Fast Food\" ${item.category === 'Fast Food' ? 'selected' : ''}>Fast Food</option>
                </select>
            </div>
            <div class=\"form-group\">
                <label>Stock Quantity</label>
                <input type=\"number\" id=\"editItemStock\" value=\"${item.stock}\" required>
            </div>
            <div class=\"form-group\">
                <label>
                    <input type=\"checkbox\" id=\"editItemDeliverable\" ${item.deliverable ? 'checked' : ''} style=\"width: auto; margin-right: 0.5rem;\">
                    Deliverable
                </label>
            </div>
            <div class=\"form-group\">
                <label>Update Image (optional)</label>
                <input type=\"file\" id=\"editItemImage\" accept=\"image/*\">
            </div>
        </form>
    `, async () => {
        const imageFile = document.getElementById('editItemImage').files[0];
        
        if (imageFile) {
            // Use FormData if image is being updated
            const formData = new FormData();
            formData.append('name', document.getElementById('editItemName').value);
            formData.append('price', document.getElementById('editItemPrice').value);
            formData.append('category', document.getElementById('editItemCategory').value);
            formData.append('stock', document.getElementById('editItemStock').value);
            formData.append('deliverable', document.getElementById('editItemDeliverable').checked ? 1 : 0);
            formData.append('image', imageFile);

            try {
                await apiCall(`/menu/${itemId}`, 'PUT', formData, true);
                showToast('Menu item updated successfully');
                closeModal();
                loadMenu();
            } catch (error) {
                showToast('Failed to update menu item: ' + error.message, 'error');
            }
        } else {
            // Use JSON if no image
            const updateData = {
                name: document.getElementById('editItemName').value,
                price: parseFloat(document.getElementById('editItemPrice').value),
                category: document.getElementById('editItemCategory').value,
                stock: parseInt(document.getElementById('editItemStock').value),
                deliverable: document.getElementById('editItemDeliverable').checked ? 1 : 0
            };

            try {
                await apiCall(`/menu/${itemId}`, 'PUT', updateData);
                showToast('Menu item updated successfully');
                closeModal();
                loadMenu();
            } catch (error) {
                showToast('Failed to update menu item: ' + error.message, 'error');
            }
        }
    });
}

async function toggleAvailability(itemId) {
    try {
        await apiCall(`/menu/${itemId}`, 'PUT', {});
        showToast('Availability toggled successfully');
        loadMenu();
    } catch (error) {
        showToast('Failed to toggle availability: ' + error.message, 'error');
    }
}

async function deleteMenuItem(itemId) {
    if (!confirmAction('Are you sure you want to delete this menu item?')) return;

    try {
        await apiCall(`/menu/${itemId}`, 'DELETE');
        showToast('Menu item deleted successfully');
        loadMenu();
    } catch (error) {
        showToast('Failed to delete menu item: ' + error.message, 'error');
    }
}

// ========== Inventory Page ==========
async function loadInventory() {
    const content = document.getElementById('pageContent');
    content.innerHTML = '<div class=\"loading\">Loading inventory...</div>';

    try {
        const menu = await apiCall('/menu');
        state.menu = menu;

        content.innerHTML = `
            <div class=\"table-container\">
                <table>
                    <thead>
                        <tr>
                            <th>Item</th>
                            <th>Category</th>
                            <th>Current Stock</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${menu.map(item => `
                            <tr>
                                <td>
                                    <strong>${item.name}</strong>
                                </td>
                                <td>${item.category}</td>
                                <td><strong>${item.stock}</strong></td>
                                <td>
                                    ${item.stock <= state.settings.lowStockThreshold 
                                        ? '<span class=\"badge badge-low-stock\">Low Stock</span>' 
                                        : '<span class=\"badge badge-stock\">In Stock</span>'}
                                </td>
                                <td>
                                    <button class=\"btn-icon\" onclick=\"adjustStock(${item.id}, -1)\" title=\"Decrease\">➖</button>
                                    <button class=\"btn-icon\" onclick=\"adjustStock(${item.id}, 1)\" title=\"Increase\">➕</button>
                                    <button class=\"btn-icon\" onclick=\"setStock(${item.id})\" title=\"Set Stock\">✏️</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

    } catch (error) {
        content.innerHTML = `<div class=\"error\">Error loading inventory: ${error.message}</div>`;
    }
}

async function adjustStock(itemId, delta) {
    const item = state.menu.find(m => m.id === itemId);
    if (!item) return;

    const newStock = Math.max(0, item.stock + delta);
    
    try {
        await apiCall(`/menu/${itemId}`, 'PUT', { stock: newStock });
        showToast(`Stock ${delta > 0 ? 'increased' : 'decreased'} successfully`);
        loadInventory();
    } catch (error) {
        showToast('Failed to adjust stock: ' + error.message, 'error');
    }
}

function setStock(itemId) {
    const item = state.menu.find(m => m.id === itemId);
    if (!item) return;

    showModal('Set Stock Level', `
        <form id=\"setStockForm\">
            <div class=\"form-group\">
                <label>Item: <strong>${item.name}</strong></label>
            </div>
            <div class=\"form-group\">
                <label>Current Stock: <strong>${item.stock}</strong></label>
            </div>
            <div class=\"form-group\">
                <label>New Stock Level</label>
                <input type=\"number\" id=\"newStock\" value=\"${item.stock}\" min=\"0\" required>
            </div>
        </form>
    `, async () => {
        const newStock = parseInt(document.getElementById('newStock').value);
        try {
            await apiCall(`/menu/${itemId}`, 'PUT', { stock: newStock });
            showToast('Stock level updated successfully');
            closeModal();
            loadInventory();
        } catch (error) {
            showToast('Failed to update stock: ' + error.message, 'error');
        }
    });
}

// ========== Users Page ==========
async function loadUsers() {
    const content = document.getElementById('pageContent');
    content.innerHTML = '<div class=\"loading\">Loading users...</div>';

    try {
        const [pendingUsers, allUsers] = await Promise.all([
            apiCall('/users/pending'),
            apiCall('/users')
        ]);

        // Normalize pending users (handle both array and object formats)
        state.pendingUsers = Array.isArray(pendingUsers[0]) 
            ? pendingUsers.map(u => ({ id: u[0], name: u[1], email: u[2] }))
            : pendingUsers;

        // Normalize all users
        state.users = Array.isArray(allUsers) ? allUsers : [];

        content.innerHTML = `
            <h2 class=\"mb-3\">Pending Approvals</h2>
            <div class=\"table-container mb-3\">
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${state.pendingUsers.length > 0 ? state.pendingUsers.map(user => `
                            <tr>
                                <td>${user.name || 'N/A'}</td>
                                <td>${user.email}</td>
                                <td>
                                    <button class=\"btn btn-success\" onclick=\"approveUser('${user.email}', 'user')\">Approve as User</button>
                                    <button class=\"btn btn-success\" onclick=\"approveUser('${user.email}', 'staff')\">Approve as Staff</button>
                                    <button class=\"btn btn-danger\" onclick=\"deleteUser('${user.email}')\">Reject</button>
                                </td>
                            </tr>
                        `).join('') : '<tr><td colspan=\"3\" class=\"text-center\">No pending approvals</td></tr>'}
                    </tbody>
                </table>
            </div>

            <h2 class=\"mb-3\">All Users</h2>
            <div class=\"table-container\">
                <table>
                    <thead>
                        <tr>
                            <th>Email</th>
                            <th>Role</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${state.users.map(user => `
                            <tr>
                                <td>${user.email}</td>
                                <td>${user.role}</td>
                                <td><span class=\"status-badge\">${user.status}</span></td>
                                <td>
                                    ${user.status === 'approved' ? `
                                        <button class=\"btn btn-secondary\" onclick=\"changeUserRole('${user.email}')\">Change Role</button>
                                    ` : ''}
                                    <button class=\"btn btn-danger\" onclick=\"deleteUser('${user.email}')\">Delete</button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

    } catch (error) {
        content.innerHTML = `<div class=\"error\">Error loading users: ${error.message}</div>`;
    }
}

async function approveUser(email, role) {
    try {
        await apiCall('/users/approve', 'POST', { email, role });
        showToast(`User approved as ${role}`);
        loadUsers();
    } catch (error) {
        showToast('Failed to approve user: ' + error.message, 'error');
    }
}

function changeUserRole(email) {
    showModal('Change User Role', `
        <form id=\"changeRoleForm\">
            <div class=\"form-group\">
                <label>User: <strong>${email}</strong></label>
            </div>
            <div class=\"form-group\">
                <label>New Role</label>
                <select id=\"newRole\" required>
                    <option value=\"user\">User</option>
                    <option value=\"staff\">Staff</option>
                    <option value=\"admin\">Admin</option>
                </select>
            </div>
        </form>
    `, async () => {
        const role = document.getElementById('newRole').value;
        try {
            await apiCall('/users/assign-role', 'POST', { email, role });
            showToast('User role updated successfully');
            closeModal();
            loadUsers();
        } catch (error) {
            showToast('Failed to update role: ' + error.message, 'error');
        }
    });
}

async function deleteUser(email) {
    if (!confirmAction(`Are you sure you want to delete user ${email}?`)) return;

    try {
        await apiCall('/users/delete', 'POST', { email });
        showToast('User deleted successfully');
        loadUsers();
    } catch (error) {
        showToast('Failed to delete user: ' + error.message, 'error');
    }
}

// ========== Reports Page ==========
async function loadReports() {
    const content = document.getElementById('pageContent');
    
    content.innerHTML = `
        <h2 class=\"mb-3\">Export Reports</h2>
        
        <div class=\"kpi-grid\">
            <div class=\"kpi-card\">
                <h3 class=\"mb-2\">Orders Report</h3>
                <p class=\"text-secondary mb-2\">Export all orders data</p>
                <button class=\"btn btn-success\" onclick=\"exportOrdersCSV()\">Download CSV</button>
            </div>
            
            <div class=\"kpi-card\">
                <h3 class=\"mb-2\">Top Sellers Report</h3>
                <p class=\"text-secondary mb-2\">Export top selling items</p>
                <button class=\"btn btn-success\" onclick=\"exportTopSellersCSV()\">Download CSV</button>
            </div>
            
            <div class=\"kpi-card\">
                <h3 class=\"mb-2\">Low Stock Report</h3>
                <p class=\"text-secondary mb-2\">Export items with low stock</p>
                <button class=\"btn btn-success\" onclick=\"exportLowStockCSV()\">Download CSV</button>
            </div>
        </div>

        <div class=\"mb-3 mt-3\">
            <h3>Note on Time-Series Analytics</h3>
            <p class=\"text-secondary\">
                For time-series sales charts and revenue trends over time, the database schema needs to include a <code>created_at</code> timestamp field in the orders table. 
                This enhancement would enable historical analysis and trend visualization.
            </p>
        </div>
    `;
}

function exportOrdersCSV() {
    const headers = ['Order ID', 'Customer Name', 'Customer Email', 'Items', 'Total Price', 'OTP', 'Status'];
    const rows = state.orders.map(order => [
        order.id,
        order.customer_name,
        order.customer_email,
        order.items.map(i => `${i.name} (${i.qty})`).join('; '),
        order.total_price,
        order.otp,
        order.status
    ]);

    downloadCSV('orders_report.csv', headers, rows);
    showToast('Orders report downloaded');
}

function exportTopSellersCSV() {
    const itemSales = {};
    
    state.orders.forEach(order => {
        if (order.items && Array.isArray(order.items)) {
            order.items.forEach(item => {
                if (!itemSales[item.id]) {
                    itemSales[item.id] = { id: item.id, name: item.name, qty: 0 };
                }
                itemSales[item.id].qty += item.qty;
            });
        }
    });

    const topItems = Object.values(itemSales).sort((a, b) => b.qty - a.qty);
    
    const headers = ['Item ID', 'Item Name', 'Total Quantity Sold'];
    const rows = topItems.map(item => [item.id, item.name, item.qty]);

    downloadCSV('top_sellers_report.csv', headers, rows);
    showToast('Top sellers report downloaded');
}

function exportLowStockCSV() {
    const lowStock = state.menu.filter(item => item.stock <= state.settings.lowStockThreshold);
    
    const headers = ['Item ID', 'Name', 'Category', 'Current Stock', 'Price'];
    const rows = lowStock.map(item => [item.id, item.name, item.category, item.stock, item.price]);

    downloadCSV('low_stock_report.csv', headers, rows);
    showToast('Low stock report downloaded');
}

function downloadCSV(filename, headers, rows) {
    let csv = headers.join(',') + '\n';
    rows.forEach(row => {
        csv += row.map(cell => `"${cell}"`).join(',') + '\n';
    });

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

// ========== Settings Page ==========
function loadSettings() {
    const content = document.getElementById('pageContent');
    
    content.innerHTML = `
        <h2 class=\"mb-3\">System Settings</h2>
        
        <div class=\"kpi-card\" style=\"max-width: 600px;\">
            <form id=\"settingsForm\">
                <div class=\"form-group\">
                    <label>Low Stock Threshold</label>
                    <input type=\"number\" id=\"lowStockThreshold\" value=\"${state.settings.lowStockThreshold}\" min=\"1\" required>
                    <small class=\"text-secondary\">Items with stock at or below this value will be marked as low stock</small>
                </div>
                
                <div class=\"form-group\">
                    <label>Polling Interval (seconds)</label>
                    <input type=\"number\" id=\"pollingInterval\" value=\"${CONFIG.POLLING_INTERVAL / 1000}\" min=\"5\" max=\"60\" required>
                    <small class=\"text-secondary\">How often the dashboard auto-refreshes (5-60 seconds)</small>
                </div>
                
                <button type=\"submit\" class=\"btn btn-success\">Save Settings</button>
            </form>
        </div>

        <div class=\"kpi-card mt-3\" style=\"max-width: 600px;\">
            <h3 class=\"mb-2\">About Real-time Updates</h3>
            <p class=\"text-secondary\">
                Currently using polling-based updates (every ${CONFIG.POLLING_INTERVAL / 1000}s). 
                For true real-time updates, consider implementing WebSocket support:
            </p>
            <ul class=\"text-secondary\">
                <li>Install Flask-SocketIO on the backend</li>
                <li>Emit events when orders/menu changes occur</li>
                <li>Replace polling with Socket.IO client connection</li>
                <li>Listen for 'order_update' and 'menu_update' events</li>
            </ul>
        </div>

        <div class=\"kpi-card mt-3\" style=\"max-width: 600px;\">
            <h3 class=\"mb-2\">Default Admin Credentials</h3>
            <p class=\"text-secondary\">
                <strong>Email:</strong> kioskadmin@saintgits.org<br>
                <strong>Password:</strong> QAZwsx1!<br>
                <br>
                ⚠️ <strong>Security Note:</strong> Change these credentials in production!
            </p>
        </div>
    `;

    document.getElementById('settingsForm').addEventListener('submit', (e) => {
        e.preventDefault();
        state.settings.lowStockThreshold = parseInt(document.getElementById('lowStockThreshold').value);
        const newInterval = parseInt(document.getElementById('pollingInterval').value) * 1000;
        
        if (newInterval !== CONFIG.POLLING_INTERVAL) {
            CONFIG.POLLING_INTERVAL = newInterval;
            stopPolling();
            startPolling();
        }
        
        showToast('Settings saved successfully');
    });
}

// ========== Modal Functions ==========
function showModal(title, bodyHtml, onSubmit = null) {
    const modal = `
        <div class=\"modal-overlay\" onclick=\"if(event.target === this) closeModal()\">
            <div class=\"modal\">
                <div class=\"modal-header\">
                    <h2>${title}</h2>
                    <button class=\"modal-close\" onclick=\"closeModal()\">✕</button>
                </div>
                <div class=\"modal-body\">
                    ${bodyHtml}
                </div>
                ${onSubmit ? `
                    <div class=\"modal-footer\">
                        <button class=\"btn btn-secondary\" onclick=\"closeModal()\">Cancel</button>
                        <button class=\"btn btn-success\" id=\"modalSubmitBtn\">Submit</button>
                    </div>
                ` : `
                    <div class=\"modal-footer\">
                        <button class=\"btn btn-secondary\" onclick=\"closeModal()\">Close</button>
                    </div>
                `}
            </div>
        </div>
    `;

    document.getElementById('modalContainer').innerHTML = modal;

    if (onSubmit) {
        document.getElementById('modalSubmitBtn').addEventListener('click', onSubmit);
    }
}

function closeModal() {
    document.getElementById('modalContainer').innerHTML = '';
}

// ========== Event Listeners ==========
document.addEventListener('DOMContentLoaded', () => {
    // Check authentication
    if (checkAuth()) {
        showAdminPanel();
    }

    // Login form
    document.getElementById('loginForm').addEventListener('submit', handleLogin);

    // Logout
    document.getElementById('logoutBtn').addEventListener('click', handleLogout);

    // Navigation
    document.querySelectorAll('.nav-item[data-page]').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            loadPage(item.dataset.page);
        });
    });

    // Polling toggle
    document.getElementById('pollingToggle').addEventListener('change', togglePolling);

    // Sidebar toggle
    document.getElementById('sidebarToggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('collapsed');
    });

    // Mobile sidebar
    document.getElementById('mobileSidebarToggle').addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('open');
    });
});

// Make functions globally accessible
window.viewOrder = viewOrder;
window.updateOrderStatus = updateOrderStatus;
window.addMenuItem = addMenuItem;
window.editMenuItem = editMenuItem;
window.deleteMenuItem = deleteMenuItem;
window.toggleAvailability = toggleAvailability;
window.adjustStock = adjustStock;
window.setStock = setStock;
window.approveUser = approveUser;
window.changeUserRole = changeUserRole;
window.deleteUser = deleteUser;
window.exportOrdersCSV = exportOrdersCSV;
window.exportTopSellersCSV = exportTopSellersCSV;
window.exportLowStockCSV = exportLowStockCSV;
window.closeModal = closeModal;