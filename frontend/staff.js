// ===========================
// Staff Dashboard JavaScript
// ===========================

// API Base URL
const API_BASE = '';

// ===========================
// Utility Functions
// ===========================

// Show alert messages
function showAlert(message, type = 'success') {
  const container = document.getElementById('alert-container');
  const alert = document.createElement('div');
  alert.className = `alert alert-${type}`;
  
  const icon = type === 'success' ? 'fa-check-circle' : 
               type === 'error' ? 'fa-exclamation-circle' : 
               'fa-info-circle';
  
  alert.innerHTML = `
    <i class="fa-solid ${icon}"></i>
    <span>${message}</span>
  `;
  
  container.appendChild(alert);
  
  // Auto remove after 5 seconds
  setTimeout(() => {
    alert.remove();
  }, 5000);
}

// Format date
function formatDate(dateString) {
  const date = new Date(dateString);
  const options = { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric', 
    hour: '2-digit', 
    minute: '2-digit' 
  };
  return date.toLocaleDateString('en-IN', options);
}

// Format currency
function formatCurrency(amount) {
  return `₹${parseFloat(amount).toFixed(2)}`;
}

// ===========================
// Tab Navigation
// ===========================

// Tab switching functionality
document.querySelectorAll('.tab-button').forEach(button => {
  button.addEventListener('click', function() {
    const targetTab = this.getAttribute('data-tab');
    switchTab(targetTab);
  });
});

// Sidebar navigation
document.querySelectorAll('.nav-links a').forEach(link => {
  link.addEventListener('click', function(e) {
    e.preventDefault();
    const targetTab = this.getAttribute('data-tab');
    switchTab(targetTab);
    
    // Update active state in sidebar
    document.querySelectorAll('.nav-links a').forEach(l => l.classList.remove('active'));
    this.classList.add('active');
  });
});

function switchTab(tabName) {
  // Hide all tab contents
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
  });
  
  // Remove active class from all tab buttons
  document.querySelectorAll('.tab-button').forEach(button => {
    button.classList.remove('active');
  });
  
  // Show selected tab content
  const targetContent = document.getElementById(`${tabName}-content`);
  const targetButton = document.querySelector(`button[data-tab="${tabName}"]`);
  
  if (targetContent) targetContent.classList.add('active');
  if (targetButton) targetButton.classList.add('active');
  
  // Load data for the tab
  loadTabData(tabName);
}

function loadTabData(tabName) {
  switch(tabName) {
    case 'users':
      loadPendingUsers();
      loadAllUsers();
      break;
    case 'orders':
      loadOrders();
      break;
    case 'menu':
      loadMenu();
      break;
    case 'dashboard':
      // Dashboard is always loaded
      break;
  }
}

// ===========================
// Statistics Loading
// ===========================

async function loadStatistics() {
  try {
    const response = await fetch(`${API_BASE}/api/staff/stats`);
    const data = await response.json();
    
    if (response.ok) {
      document.getElementById('total-items').textContent = data.total_items || 0;
      document.getElementById('total-orders').textContent = data.total_orders || 0;
      document.getElementById('pending-orders').textContent = data.pending_orders || 0;
      document.getElementById('total-users').textContent = data.total_users || 0;
      document.getElementById('pending-users').textContent = data.pending_users || 0;
      document.getElementById('today-revenue').textContent = formatCurrency(data.today_revenue || 0);
    } else {
      console.error('Failed to load statistics:', data.error);
    }
  } catch (error) {
    console.error('Error loading statistics:', error);
  }
}

// ===========================
// User Management
// ===========================

async function loadPendingUsers() {
  const loadingEl = document.getElementById('pending-users-loading');
  const tableEl = document.getElementById('pending-users-table');
  const emptyEl = document.getElementById('no-pending-users');
  const tbody = document.getElementById('pending-users-list');
  
  loadingEl.style.display = 'block';
  tableEl.style.display = 'none';
  emptyEl.style.display = 'none';
  
  try {
    const response = await fetch(`${API_BASE}/api/staff/users/pending`);
    const users = await response.json();
    
    loadingEl.style.display = 'none';
    
    if (users.length === 0) {
      emptyEl.style.display = 'block';
      return;
    }
    
    tableEl.style.display = 'table';
    tbody.innerHTML = '';
    
    users.forEach(user => {
      const row = document.createElement('tr');
      row.innerHTML = `
        <td>${user.id}</td>
        <td>${user.name}</td>
        <td>${user.email}</td>
        <td><span class="badge pending">${user.status}</span></td>
        <td>
          <button class="btn approve-btn" onclick="approveUser(${user.id}, '${user.email}')">
            <i class="fa-solid fa-check"></i> Approve
          </button>
          <button class="btn reject-btn" onclick="rejectUser(${user.id}, '${user.email}')">
            <i class="fa-solid fa-times"></i> Reject
          </button>
        </td>
      `;
      tbody.appendChild(row);
    });
    
    // Update statistics
    loadStatistics();
  } catch (error) {
    loadingEl.style.display = 'none';
    showAlert('Failed to load pending users: ' + error.message, 'error');
  }
}

async function approveUser(userId, userEmail) {
  if (!confirm(`Approve user: ${userEmail}?`)) return;
  
  try {
    const response = await fetch(`${API_BASE}/api/staff/users/${userId}/approve`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' }
    });
    
    const data = await response.json();
    
    if (response.ok) {
      showAlert(`User ${userEmail} approved successfully!`, 'success');
      loadPendingUsers();
      loadAllUsers();
      loadStatistics();
    } else {
      showAlert(data.error || 'Failed to approve user', 'error');
    }
  } catch (error) {
    showAlert('Error approving user: ' + error.message, 'error');
  }
}

async function rejectUser(userId, userEmail) {
  if (!confirm(`Reject and delete user: ${userEmail}? This action cannot be undone.`)) return;
  
  try {
    const response = await fetch(`${API_BASE}/api/staff/users/${userId}/reject`, {
      method: 'DELETE'
    });
    
    const data = await response.json();
    
    if (response.ok) {
      showAlert(`User ${userEmail} rejected successfully`, 'success');
      loadPendingUsers();
      loadStatistics();
    } else {
      showAlert(data.error || 'Failed to reject user', 'error');
    }
  } catch (error) {
    showAlert('Error rejecting user: ' + error.message, 'error');
  }
}

async function loadAllUsers() {
  const loadingEl = document.getElementById('all-users-loading');
  const tableEl = document.getElementById('all-users-table');
  const tbody = document.getElementById('all-users-list');
  
  loadingEl.style.display = 'block';
  tableEl.style.display = 'none';
  
  try {
    const response = await fetch(`${API_BASE}/api/users`);
    const users = await response.json();
    
    loadingEl.style.display = 'none';
    tableEl.style.display = 'table';
    tbody.innerHTML = '';
    
    users.forEach(user => {
      const row = document.createElement('tr');
      const statusClass = user.status === 'approved' ? 'approved' : 'pending';
      row.innerHTML = `
        <td>${user.name}</td>
        <td>${user.email}</td>
        <td><span class="badge">${user.role}</span></td>
        <td><span class="badge ${statusClass}">${user.status}</span></td>
      `;
      tbody.appendChild(row);
    });
  } catch (error) {
    loadingEl.style.display = 'none';
    showAlert('Failed to load users: ' + error.message, 'error');
  }
}

// ===========================
// Order Management
// ===========================

async function loadOrders() {
  const loadingEl = document.getElementById('orders-loading');
  const tableEl = document.getElementById('orders-table');
  const emptyEl = document.getElementById('no-orders');
  const tbody = document.getElementById('orders-list');
  
  loadingEl.style.display = 'block';
  tableEl.style.display = 'none';
  emptyEl.style.display = 'none';
  
  try {
    const response = await fetch(`${API_BASE}/api/staff/orders/recent?limit=50`);
    const orders = await response.json();
    
    loadingEl.style.display = 'none';
    
    if (orders.length === 0) {
      emptyEl.style.display = 'block';
      return;
    }
    
    tableEl.style.display = 'table';
    tbody.innerHTML = '';
    
    orders.forEach(order => {
      const row = document.createElement('tr');
      
      // Build items list
      const itemsList = order.items.map(item => 
        `${item.name} (x${item.qty})`
      ).join(', ');
      
      // Status badge class
      let statusClass = 'pending';
      if (order.status === 'Completed') statusClass = 'completed';
      else if (order.status === 'Preparing') statusClass = 'preparing';
      else if (order.status === 'Ready for Pickup') statusClass = 'ready';
      else if (order.status === 'Cancelled') statusClass = 'cancelled';
      
      row.innerHTML = `
        <td><strong>#${order.id}</strong></td>
        <td>${order.customer_name}</td>
        <td>${order.customer_email}</td>
        <td>
          <div class="order-items-list">
            ${order.items.map(item => `<div>• ${item.name} × ${item.qty}</div>`).join('')}
          </div>
        </td>
        <td><strong>${formatCurrency(order.total_price)}</strong></td>
        <td><code style="background: #374151; padding: 4px 8px; border-radius: 4px;">${order.otp}</code></td>
        <td><span class="badge ${statusClass}">${order.status}</span></td>
        <td style="font-size: 0.85rem; color: #9ca3af;">${formatDate(order.created_at)}</td>
        <td>
          <select onchange="updateOrderStatus(${order.id}, this.value)" class="btn update-status-btn" style="padding: 8px;">
            <option value="">Change Status</option>
            <option value="Order Received" ${order.status === 'Order Received' ? 'selected' : ''}>Order Received</option>
            <option value="Preparing" ${order.status === 'Preparing' ? 'selected' : ''}>Preparing</option>
            <option value="Ready for Pickup" ${order.status === 'Ready for Pickup' ? 'selected' : ''}>Ready for Pickup</option>
            <option value="Completed" ${order.status === 'Completed' ? 'selected' : ''}>Completed</option>
            <option value="Cancelled" ${order.status === 'Cancelled' ? 'selected' : ''}>Cancelled</option>
          </select>
        </td>
      `;
      tbody.appendChild(row);
    });
    
    // Update statistics
    loadStatistics();
  } catch (error) {
    loadingEl.style.display = 'none';
    showAlert('Failed to load orders: ' + error.message, 'error');
  }
}

async function updateOrderStatus(orderId, newStatus) {
  if (!newStatus) return;
  
  try {
    const response = await fetch(`${API_BASE}/api/orders/${orderId}/status`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      showAlert(`Order #${orderId} status updated to: ${newStatus}`, 'success');
      loadOrders();
      loadStatistics();
    } else {
      showAlert(data.error || 'Failed to update order status', 'error');
    }
  } catch (error) {
    showAlert('Error updating order status: ' + error.message, 'error');
  }
}

// ===========================
// Menu Management
// ===========================

async function loadMenu() {
  const loadingEl = document.getElementById('menu-loading');
  const tableEl = document.getElementById('menu-table');
  const tbody = document.getElementById('menu-list');
  
  loadingEl.style.display = 'block';
  tableEl.style.display = 'none';
  
  try {
    const response = await fetch(`${API_BASE}/api/menu`);
    const menu = await response.json();
    
    loadingEl.style.display = 'none';
    tableEl.style.display = 'table';
    tbody.innerHTML = '';
    
    menu.forEach(item => {
      const row = document.createElement('tr');
      row.id = `menu-row-${item.id}`;
      
      const availabilityClass = item.available ? 'active' : 'inactive';
      const availabilityText = item.available ? 'Available' : 'Unavailable';
      
      row.innerHTML = `
        <td><img src="/static/images/${item.image}" alt="${item.name}" class="menu-img"></td>
        <td><strong>${item.name}</strong></td>
        <td>${formatCurrency(item.price)}</td>
        <td><span class="badge">${item.category}</span></td>
        <td>${item.stock}</td>
        <td><span class="status ${availabilityClass}">${availabilityText}</span></td>
        <td>
          <button class="btn toggle-btn" onclick="toggleAvailability(${item.id}, ${item.available})">
            <i class="fa-solid fa-toggle-${item.available ? 'on' : 'off'}"></i> Toggle
          </button>
          <button class="btn edit-btn" onclick="editMenuItem(${item.id})">
            <i class="fa-solid fa-pen"></i>
          </button>
          <button class="btn delete-btn" onclick="deleteMenuItem(${item.id}, '${item.name}')">
            <i class="fa-solid fa-trash"></i>
          </button>
        </td>
      `;
      tbody.appendChild(row);
    });
    
    // Update statistics
    loadStatistics();
  } catch (error) {
    loadingEl.style.display = 'none';
    showAlert('Failed to load menu: ' + error.message, 'error');
  }
}

async function toggleAvailability(itemId, currentStatus) {
  try {
    const response = await fetch(`${API_BASE}/api/menu/${itemId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ available: !currentStatus })
    });
    
    const data = await response.json();
    
    if (response.ok) {
      showAlert('Availability updated successfully', 'success');
      loadMenu();
    } else {
      showAlert(data.error || 'Failed to update availability', 'error');
    }
  } catch (error) {
    showAlert('Error updating availability: ' + error.message, 'error');
  }
}

async function editMenuItem(itemId) {
  const row = document.getElementById(`menu-row-${itemId}`);
  
  // Get current values
  const cells = row.querySelectorAll('td');
  const currentName = cells[1].querySelector('strong').textContent;
  const currentPrice = cells[2].textContent.replace('₹', '').replace(',', '');
  const currentCategory = cells[3].querySelector('.badge').textContent;
  const currentStock = cells[4].textContent;
  const currentImage = cells[0].querySelector('img').src.split('/').pop();
  
  // Replace row with edit form
  row.innerHTML = `
    <td>
      <img src="/static/images/${currentImage}" alt="${currentName}" class="menu-img">
      <input type="file" id="edit-image-${itemId}" accept="image/*" style="display: block; margin-top: 8px; font-size: 0.8rem;">
    </td>
    <td><input type="text" id="edit-name-${itemId}" value="${currentName}" style="width: 150px;"></td>
    <td><input type="number" id="edit-price-${itemId}" value="${currentPrice}" step="5" style="width: 100px;"></td>
    <td>
      <select id="edit-category-${itemId}" style="width: 120px;">
        <option value="Veg" ${currentCategory === 'Veg' ? 'selected' : ''}>Veg</option>
        <option value="Non-Veg" ${currentCategory === 'Non-Veg' ? 'selected' : ''}>Non-Veg</option>
        <option value="Beverages" ${currentCategory === 'Beverages' ? 'selected' : ''}>Beverages</option>
        <option value="Snacks" ${currentCategory === 'Snacks' ? 'selected' : ''}>Snacks</option>
      </select>
    </td>
    <td><input type="number" id="edit-stock-${itemId}" value="${currentStock}" style="width: 80px;"></td>
    <td colspan="2">
      <button class="btn save-btn" onclick="saveMenuItem(${itemId})">
        <i class="fa-solid fa-check"></i> Save
      </button>
      <button class="btn cancel-btn" onclick="loadMenu()">
        <i class="fa-solid fa-times"></i> Cancel
      </button>
    </td>
  `;
}

async function saveMenuItem(itemId) {
  const formData = new FormData();
  formData.append('name', document.getElementById(`edit-name-${itemId}`).value);
  formData.append('price', document.getElementById(`edit-price-${itemId}`).value);
  formData.append('category', document.getElementById(`edit-category-${itemId}`).value);
  formData.append('stock', document.getElementById(`edit-stock-${itemId}`).value);
  
  const imageFile = document.getElementById(`edit-image-${itemId}`).files[0];
  if (imageFile) {
    formData.append('image', imageFile);
  }
  
  try {
    const response = await fetch(`${API_BASE}/api/menu/${itemId}`, {
      method: 'PUT',
      body: formData
    });
    
    const data = await response.json();
    
    if (response.ok) {
      showAlert('Menu item updated successfully', 'success');
      loadMenu();
    } else {
      showAlert(data.error || 'Failed to update menu item', 'error');
    }
  } catch (error) {
    showAlert('Error updating menu item: ' + error.message, 'error');
  }
}

async function deleteMenuItem(itemId, itemName) {
  if (!confirm(`Are you sure you want to delete "${itemName}"? This action cannot be undone.`)) return;
  
  try {
    const response = await fetch(`${API_BASE}/api/menu/${itemId}`, {
      method: 'DELETE'
    });
    
    const data = await response.json();
    
    if (response.ok) {
      showAlert(`Menu item "${itemName}" deleted successfully`, 'success');
      loadMenu();
      loadStatistics();
    } else {
      showAlert(data.error || 'Failed to delete menu item', 'error');
    }
  } catch (error) {
    showAlert('Error deleting menu item: ' + error.message, 'error');
  }
}

// Handle add menu item form submission
document.getElementById('add-item-form').addEventListener('submit', async function(e) {
  e.preventDefault();
  
  const formData = new FormData(this);
  
  try {
    const response = await fetch(`${API_BASE}/api/menu`, {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    
    if (response.ok) {
      showAlert('Menu item added successfully', 'success');
      this.reset();
      loadMenu();
      loadStatistics();
    } else {
      showAlert(data.error || 'Failed to add menu item', 'error');
    }
  } catch (error) {
    showAlert('Error adding menu item: ' + error.message, 'error');
  }
});

// ===========================
// Refresh Data
// ===========================

function refreshData() {
  showAlert('Refreshing data...', 'info');
  loadStatistics();
  
  // Reload current tab data
  const activeTab = document.querySelector('.tab-content.active');
  if (activeTab) {
    const tabId = activeTab.id.replace('-content', '');
    loadTabData(tabId);
  }
}

// ===========================
// Initialize on Page Load
// ===========================

document.addEventListener('DOMContentLoaded', function() {
  // Load statistics on page load
  loadStatistics();
  
  // Load initial tab data (menu by default)
  loadMenu();
  
  // Auto-refresh statistics every 30 seconds
  setInterval(loadStatistics, 30000);
});
