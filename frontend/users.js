// ==================== STATE MANAGEMENT ====================
const state = {
  user: null,
  menu: [],
  cart: [],
  favorites: new Set(),
  orders: [],
  currentPage: 'home',
  currentFilter: 'all',
  isInitialized: false
};

// ==================== THEME MANAGEMENT ====================
function initTheme() {
  // Load theme preference from localStorage
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  console.log('[THEME] Initialized theme:', savedTheme);
}

function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  const newTheme = currentTheme === 'light' ? 'dark' : 'light';
  
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('theme', newTheme);
  
  console.log('[THEME] Switched to:', newTheme);
  
  // Optional: Add a subtle animation effect
  document.body.style.transition = 'background-color 0.3s ease';
}

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', async () => {
  console.log('[INIT] Starting initialization...');
  
  // Initialize theme first
  initTheme();
  
  // Show loading immediately
  showLoading(true);
  
  // Check authentication first
  if (!checkAuth()) {
    showLoading(false);
    return;
  }
  
  console.log('[INIT] User authenticated:', state.user.email);
  
  // Initialize UI components
  initNavigation();
  initSearchFilter();
  
  // Load persistent data from localStorage
  loadCart();
  loadFavorites();
  updateCartBadge();
  updateFavoritesBadge();
  
  console.log('[INIT] Loaded from localStorage - Cart:', state.cart.length, 'Favorites:', state.favorites.size);
  
  // Load data from server sequentially to avoid race conditions
  try {
    console.log('[INIT] Loading menu...');
    await loadMenu();
    console.log('[INIT] Menu loaded:', state.menu.length, 'items');
    
    console.log('[INIT] Loading orders...');
    await loadOrders();
    console.log('[INIT] Orders loaded:', state.orders.length, 'orders');
    
    // Update stats after all data is loaded
    console.log('[INIT] Updating stats...');
    updateUserStats();
    
    // Mark as initialized
    state.isInitialized = true;
    console.log('[INIT] Initialization complete');
    
  } catch (error) {
    console.error('[ERROR] Failed to load initial data:', error);
    showToast('Failed to load some data. Please refresh the page.', 'error');
  } finally {
    // Hide loading overlay
    showLoading(false);
    
    // Initialize animations after everything is loaded
    setTimeout(() => {
      initAnimations();
    }, 100);
  }
});

// ==================== AUTHENTICATION ====================
function checkAuth() {
  const userStr = localStorage.getItem('user');
  if (!userStr) {
    window.location.href = '/';
    return false;
  }
  
  try {
    state.user = JSON.parse(userStr);
    updateUserDisplay();
    return true;
  } catch (e) {
    console.error('[ERROR] Invalid user data:', e);
    localStorage.removeItem('user');
    window.location.href = '/';
    return false;
  }
}

function updateUserDisplay() {
  if (!state.user) return;
  
  const userNameEl = document.getElementById('userName');
  const avatarEl = document.getElementById('userAvatar');
  
  if (userNameEl) {
    userNameEl.textContent = state.user.name;
  }
  
  if (avatarEl) {
    avatarEl.textContent = state.user.name.charAt(0).toUpperCase();
  }
}

function logout() {
  if (confirm('Are you sure you want to logout?')) {
    localStorage.clear();
    window.location.href = '/';
  }
}

// ==================== NAVIGATION ====================
function initNavigation() {
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const page = link.dataset.page;
      navigateTo(page);
    });
  });
  
  // Scroll effect for navbar
  let lastScroll = 0;
  window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    const currentScroll = window.pageYOffset;
    
    if (currentScroll > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
    
    lastScroll = currentScroll;
  });
}

function navigateTo(page) {
  console.log('[DEBUG] Navigating to:', page);
  state.currentPage = page;
  
  // Update nav links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.toggle('active', link.dataset.page === page);
  });
  
  // Show/hide sections
  document.querySelectorAll('.section').forEach(section => {
    section.classList.add('hidden');
  });
  
  const sectionMap = {
    'home': 'homeSection',
    'menu': 'menuSection',
    'favorites': 'favoritesSection',
    'cart': 'cartSection',
    'orders': 'ordersSection'
  };
  
  const sectionId = sectionMap[page];
  if (sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
      section.classList.remove('hidden');
    }
  }
  
  // Render page content
  renderCurrentPage();
  
  // Smooth scroll to top
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function renderCurrentPage() {
  // Only render if initialized
  if (!state.isInitialized) {
    console.log('[RENDER] Not initialized yet, skipping render for:', state.currentPage);
    return;
  }
  
  console.log('[RENDER] Rendering page:', state.currentPage);
  
  switch (state.currentPage) {
    case 'menu':
      renderMenu();
      break;
    case 'cart':
      renderCart();
      break;
    case 'favorites':
      renderFavorites();
      break;
    case 'orders':
      renderOrders();
      break;
    case 'home':
      // Home page is mostly static, stats are updated by updateUserStats
      console.log('[RENDER] Home page active');
      break;
  }
}

// ==================== MENU ====================
async function loadMenu() {
  try {
    console.log('[DEBUG] Loading menu...');
    const response = await fetch('/api/menu');
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    console.log('[DEBUG] Menu data received:', data.length, 'items');
    
    // Filter available items
    state.menu = data.filter(item => item.available);
    console.log('[DEBUG] Available items:', state.menu.length);
    
    return Promise.resolve();
  } catch (error) {
    console.error('[ERROR] Failed to load menu:', error);
    showToast('Failed to load menu', 'error');
    state.menu = [];
    return Promise.reject(error);
  }
}

function renderMenu(filter = 'all', searchTerm = '') {
  const grid = document.getElementById('menuGrid');
  if (!grid) return;
  
  console.log('[DEBUG] Rendering menu, filter:', filter, 'search:', searchTerm);
  
  let filtered = filter === 'all' ? state.menu : state.menu.filter(item => item.category === filter);
  
  if (searchTerm) {
    filtered = filtered.filter(item =>
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.category.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }
  
  if (filtered.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
        <i class="fas fa-search" style="font-size: 3rem; color: var(--text-tertiary); margin-bottom: 1rem; opacity: 0.5;"></i>
        <h3 style="color: var(--text-secondary)">No items found</h3>
        <p style="color: var(--text-tertiary)">Try a different category or search term</p>
      </div>
    `;
    return;
  }
  
  grid.innerHTML = filtered.map(item => createMenuCard(item)).join('');
  // Animation removed for better UX
}

function createMenuCard(item) {
  const isOutOfStock = item.stock <= 0;
  const isFavorite = state.favorites.has(item.id);
  const imageUrl = item.image ? `/static/images/${item.image}` : `https://via.placeholder.com/400x250/1e1e2e/6366f1?text=${encodeURIComponent(item.name)}`;
  
  const badges = [];
  if (item.stock > 0 && item.stock < 5) badges.push('<span class="badge">Low Stock</span>');
  
  return `
    <div class="menu-card ${isOutOfStock ? 'out-of-stock' : ''}">
      <div class="menu-card-image">
        <img src="${imageUrl}" alt="${item.name}" loading="lazy" 
             onerror="this.src='https://via.placeholder.com/400x250/1e1e2e/6366f1?text=${encodeURIComponent(item.name)}'">
        <button class="favorite-btn ${isFavorite ? 'active' : ''}" onclick="toggleFavorite(${item.id})" 
                title="${isFavorite ? 'Remove from favorites' : 'Add to favorites'}">
          <i class="fas fa-heart"></i>
        </button>
        ${badges.length > 0 ? `<div class="menu-card-badges">${badges.join('')}</div>` : ''}
      </div>
      <div class="menu-card-content">
        <h3 class="menu-card-title">${item.name}</h3>
        <div class="menu-card-meta">
          <span><i class="fas fa-tag"></i> ${item.category}</span>
          <span><i class="fas fa-box"></i> Stock: ${item.stock}</span>
        </div>
        <div class="menu-card-footer">
          <div>
            <div class="menu-card-price">₹${item.price.toFixed(2)}</div>
            ${item.stock < 5 && item.stock > 0 ? `<div class="menu-card-stock low">Only ${item.stock} left!</div>` : ''}
          </div>
          <button class="add-to-cart-btn" onclick="addToCart(${item.id})" ${isOutOfStock ? 'disabled' : ''}>
            <i class="fas fa-${isOutOfStock ? 'ban' : 'plus'}"></i>
            ${isOutOfStock ? 'Out of Stock' : 'Add'}
          </button>
        </div>
      </div>
    </div>
  `;
}

// ==================== SEARCH & FILTER ====================
function initSearchFilter() {
  const searchInput = document.getElementById('menuSearch');
  if (searchInput) {
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
      clearTimeout(debounceTimer);
      debounceTimer = setTimeout(() => {
        renderMenu(state.currentFilter, e.target.value);
      }, 300);
    });
  }
  
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.currentFilter = btn.dataset.filter;
      const searchTerm = document.getElementById('menuSearch')?.value || '';
      renderMenu(state.currentFilter, searchTerm);
    });
  });
}

// ==================== FAVORITES ====================
function loadFavorites() {
  const favoritesStr = localStorage.getItem('favorites');
  if (favoritesStr) {
    try {
      const favArray = JSON.parse(favoritesStr);
      state.favorites = new Set(favArray);
      console.log('[DEBUG] Loaded favorites:', state.favorites.size, 'items');
    } catch (e) {
      console.error('[ERROR] Failed to parse favorites:', e);
      state.favorites = new Set();
    }
  }
  updateFavoritesBadge();
}

function saveFavorites() {
  localStorage.setItem('favorites', JSON.stringify([...state.favorites]));
  console.log('[DEBUG] Saved favorites:', state.favorites.size, 'items');
}

function toggleFavorite(itemId) {
  if (state.favorites.has(itemId)) {
    state.favorites.delete(itemId);
    showToast('Removed from favorites', 'success');
  } else {
    state.favorites.add(itemId);
    showToast('Added to favorites', 'success');
  }
  
  saveFavorites();
  updateFavoritesBadge();
  
  // Update UI with animation
  const btn = event.target.closest('.favorite-btn');
  if (btn) {
    btn.classList.toggle('active');
    // Add scale animation using CSS
    btn.style.animation = 'scaleUp 0.3s ease';
    setTimeout(() => {
      btn.style.animation = '';
    }, 300);
  }
  
  // Re-render favorites page if we're on it
  if (state.currentPage === 'favorites' && state.isInitialized) {
    renderFavorites();
  }
}

function renderFavorites() {
  const grid = document.getElementById('favoritesGrid');
  console.log('[FAVORITES] Render called');
  console.log('[FAVORITES] Initialized:', state.isInitialized);
  console.log('[FAVORITES] Menu length:', state.menu.length);
  console.log('[FAVORITES] Favorites size:', state.favorites.size);
  console.log('[FAVORITES] Favorites:', Array.from(state.favorites));
  
  if (!grid) {
    console.error('[ERROR] Favorites grid element not found');
    return;
  }
  
  // Wait for initialization
  if (!state.isInitialized || state.menu.length === 0) {
    console.log('[FAVORITES] Not ready yet, showing loading');
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
        <div class="spinner" style="margin: 0 auto 1rem;"></div>
        <p style="color: var(--text-tertiary)">Loading your favorites...</p>
      </div>
    `;
    return;
  }
  
  // Check if there are any favorites
  if (state.favorites.size === 0) {
    console.log('[FAVORITES] No favorites added yet');
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
        <i class="fas fa-heart" style="font-size: 3rem; color: var(--text-tertiary); margin-bottom: 1rem; opacity: 0.5;"></i>
        <h3 style="color: var(--text-secondary)">No favorites yet</h3>
        <p style="color: var(--text-tertiary)">Add items to your favorites for quick access</p>
        <button class="btn btn-primary" onclick="navigateTo('menu')" style="margin-top: 1rem;">
          <i class="fas fa-utensils"></i> Browse Menu
        </button>
      </div>
    `;
    return;
  }
  
  // Filter favorite items from menu
  const favoriteItems = state.menu.filter(item => state.favorites.has(item.id));
  console.log('[FAVORITES] Favorite items found:', favoriteItems.length);
  
  if (favoriteItems.length === 0) {
    console.log('[FAVORITES] Favorites exist but items not in menu (possibly unavailable)');
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 3rem;">
        <i class="fas fa-heart" style="font-size: 3rem; color: var(--text-tertiary); margin-bottom: 1rem; opacity: 0.5;"></i>
        <h3 style="color: var(--text-secondary)">Your favorite items are currently unavailable</h3>
        <p style="color: var(--text-tertiary)">They might be out of stock or removed from the menu</p>
        <button class="btn btn-primary" onclick="navigateTo('menu')" style="margin-top: 1rem;">
          <i class="fas fa-utensils"></i> Browse Menu
        </button>
      </div>
    `;
    return;
  }
  
  console.log('[FAVORITES] Rendering', favoriteItems.length, 'favorite cards');
  grid.innerHTML = favoriteItems.map(item => createMenuCard(item)).join('');
  // Animation removed for better UX
}

function updateFavoritesBadge() {
  const badge = document.getElementById('favoritesBadge');
  const count = state.favorites.size;
  
  if (badge) {
    badge.textContent = count;
    badge.classList.toggle('show', count > 0);
  }
  
  // Update stat on home page
  const statEl = document.getElementById('favoritesCountStat');
  if (statEl) {
    statEl.textContent = count;
  }
}

// ==================== CART ====================
function addToCart(itemId) {
  const item = state.menu.find(i => i.id === itemId);
  if (!item) {
    showToast('Item not found', 'error');
    return;
  }
  
  if (item.stock <= 0) {
    showToast('Sorry, this item is out of stock', 'error');
    return;
  }
  
  const existingItem = state.cart.find(i => i.id === itemId);
  if (existingItem) {
    if (existingItem.quantity >= item.stock) {
      showToast(`Only ${item.stock} available`, 'warning');
      return;
    }
    existingItem.quantity++;
  } else {
    state.cart.push({ ...item, quantity: 1 });
  }
  
  saveCart();
  updateCartBadge();
  showToast('Added to cart!', 'success');
  
  // Animate button with CSS
  const btn = event.target.closest('.add-to-cart-btn');
  if (btn) {
    btn.style.animation = 'pulse 0.4s ease';
    setTimeout(() => {
      btn.style.animation = '';
    }, 400);
  }
}

function removeFromCart(itemId) {
  state.cart = state.cart.filter(item => item.id !== itemId);
  saveCart();
  updateCartBadge();
  renderCart();
  showToast('Item removed', 'success');
}

function updateQuantity(itemId, change) {
  const item = state.cart.find(i => i.id === itemId);
  if (!item) return;
  
  const menuItem = state.menu.find(i => i.id === itemId);
  item.quantity += change;
  
  if (item.quantity <= 0) {
    removeFromCart(itemId);
  } else if (menuItem && item.quantity > menuItem.stock) {
    item.quantity = menuItem.stock;
    showToast(`Only ${menuItem.stock} available`, 'warning');
    saveCart();
    renderCart();
  } else {
    saveCart();
    updateCartBadge();
    renderCart();
  }
}

function saveCart() {
  localStorage.setItem('cart', JSON.stringify(state.cart));
}

function loadCart() {
  const cartStr = localStorage.getItem('cart');
  if (cartStr) {
    try {
      state.cart = JSON.parse(cartStr);
      console.log('[DEBUG] Loaded cart:', state.cart.length, 'items');
    } catch (e) {
      console.error('[ERROR] Failed to parse cart:', e);
      state.cart = [];
    }
  }
  updateCartBadge();
}

function updateCartBadge() {
  const badge = document.getElementById('cartBadge');
  const total = state.cart.reduce((sum, item) => sum + item.quantity, 0);
  
  if (badge) {
    badge.textContent = total;
    badge.classList.toggle('show', total > 0);
  }
}

function renderCart() {
  const container = document.getElementById('cartContent');
  if (!container) return;
  
  if (state.cart.length === 0) {
    container.innerHTML = `
      <div class="cart-empty">
        <i class="fas fa-shopping-cart"></i>
        <h3>Your cart is empty</h3>
        <p>Add some delicious items to get started!</p>
        <button class="btn btn-primary" onclick="navigateTo('menu')" style="padding: 0.75rem 1.5rem; font-size: 1rem;">
          <i class="fas fa-utensils"></i> Browse Menu
        </button>
      </div>
    `;
    return;
  }
  
  const subtotal = state.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const deliveryFee = 0; // Will be calculated at checkout
  const total = subtotal + deliveryFee;
  
  container.innerHTML = `
    <div class="cart-items">
      ${state.cart.map(item => `
        <div class="cart-item">
          <img src="/static/images/${item.image}" alt="${item.name}" class="cart-item-image"
               onerror="this.src='https://via.placeholder.com/100/1e1e2e/6366f1?text=${encodeURIComponent(item.name)}'">
          <div class="cart-item-details">
            <h3 class="cart-item-name">${item.name}</h3>
            <p class="cart-item-price">₹${item.price} × ${item.quantity} = ₹${(item.price * item.quantity).toFixed(2)}</p>
            <div class="cart-item-controls">
              <div class="quantity-control">
                <button class="quantity-btn" onclick="updateQuantity(${item.id}, -1)">
                  <i class="fas fa-minus"></i>
                </button>
                <span class="quantity-value">${item.quantity}</span>
                <button class="quantity-btn" onclick="updateQuantity(${item.id}, 1)">
                  <i class="fas fa-plus"></i>
                </button>
              </div>
              <button class="remove-btn" onclick="removeFromCart(${item.id})">
                <i class="fas fa-trash"></i> Remove
              </button>
            </div>
          </div>
        </div>
      `).join('')}
    </div>
    
    <div class="cart-summary">
      <div class="cart-summary-row">
        <span class="cart-summary-label">Subtotal</span>
        <span class="cart-summary-value">₹${subtotal.toFixed(2)}</span>
      </div>
      <div class="cart-summary-row">
        <span class="cart-summary-label">Delivery Fee</span>
        <span class="cart-summary-value">At checkout</span>
      </div>
      <div class="cart-summary-row">
        <span class="cart-summary-label">Total</span>
        <span class="cart-summary-value">₹${total.toFixed(2)}+</span>
      </div>
      <button class="checkout-btn" onclick="openCheckout()">
        <i class="fas fa-check-circle"></i> Proceed to Checkout
      </button>
    </div>
  `;
}

// ==================== CHECKOUT ====================
function openCheckout() {
  if (state.cart.length === 0) {
    showToast('Your cart is empty', 'error');
    return;
  }
  
  const modal = document.getElementById('checkoutModal');
  const body = document.getElementById('checkoutModalBody');
  
  const subtotal = state.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  
  body.innerHTML = `
    <form id="checkoutForm">
      <div class="form-group">
        <label for="customerName">Full Name *</label>
        <input type="text" id="customerName" required value="${state.user?.name || ''}">
        <span class="error-message">Please enter your name</span>
      </div>
      
      <div class="form-group">
        <label for="customerEmail">Email *</label>
        <input type="email" id="customerEmail" required value="${state.user?.email || ''}">
        <span class="error-message">Please enter a valid email</span>
      </div>
      
      <div class="form-group">
        <label for="customerPhone">Phone Number *</label>
        <input type="tel" id="customerPhone" required pattern="[0-9]{10}" maxlength="10">
        <span class="error-message">Please enter a valid 10-digit phone number</span>
      </div>
      
      <div class="form-group">
        <label>Order Type *</label>
        <div class="radio-group">
          <label class="radio-label">
            <input type="radio" name="orderType" value="pickup" checked onchange="updateCheckoutTotal()">
            <span>Pickup from Kiosk (Free)</span>
          </label>
          <label class="radio-label">
            <input type="radio" name="orderType" value="delivery" onchange="updateCheckoutTotal()">
            <span>Delivery (₹5 if &lt;5 items)</span>
          </label>
        </div>
      </div>
      
      <div id="deliveryFields" style="display: none;">
        <div class="form-group">
          <label for="classroom">Classroom *</label>
          <input type="text" id="classroom" placeholder="e.g., Room 301">
        </div>
        <div class="form-group">
          <label for="department">Department *</label>
          <input type="text" id="department" placeholder="e.g., Computer Science">
        </div>
        <div class="form-group">
          <label for="block">Block *</label>
          <input type="text" id="block" placeholder="e.g., Block A">
        </div>
      </div>
      
      <div class="form-group">
        <label>Payment Method *</label>
        <div class="radio-group">
          <label class="radio-label">
            <input type="radio" name="paymentMethod" value="upi" checked>
            <span>UPI</span>
          </label>
          <label class="radio-label">
            <input type="radio" name="paymentMethod" value="card">
            <span>Card</span>
          </label>
          <label class="radio-label">
            <input type="radio" name="paymentMethod" value="cod">
            <span>Cash</span>
          </label>
        </div>
      </div>
      
      <div style="padding: 1rem; background: var(--bg-elevated); border-radius: var(--radius); margin-top: 1rem;">
        <h4 style="margin-bottom: 0.5rem;">Order Summary</h4>
        <div style="display: flex; justify-content: space-between; padding: 0.5rem 0;">
          <span>Subtotal</span>
          <span>₹${subtotal.toFixed(2)}</span>
        </div>
        <div style="display: flex; justify-content: space-between; padding: 0.5rem 0;">
          <span>Delivery Fee</span>
          <span id="checkoutDeliveryFee">Free</span>
        </div>
        <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; border-top: 1px solid var(--border); margin-top: 0.5rem; font-weight: 700; font-size: 1.125rem;">
          <span>Total</span>
          <span id="checkoutTotal">₹${subtotal.toFixed(2)}</span>
        </div>
      </div>
      
      <button type="button" class="btn btn-primary" id="confirmOrderBtn" onclick="confirmOrder()" style="width: 100%; margin-top: 1rem; padding: 1rem;">
        <i class="fas fa-check-circle"></i> Place Order
      </button>
    </form>
  `;
  
  modal.classList.add('active');
  
  // Setup delivery fields toggle
  document.querySelectorAll('input[name="orderType"]').forEach(radio => {
    radio.addEventListener('change', () => {
      const deliveryFields = document.getElementById('deliveryFields');
      deliveryFields.style.display = radio.value === 'delivery' ? 'block' : 'none';
      updateCheckoutTotal();
    });
  });
}

function updateCheckoutTotal() {
  const orderType = document.querySelector('input[name="orderType"]:checked')?.value;
  const subtotal = state.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  
  // Calculate delivery fee based on quantity
  const totalQty = state.cart.reduce((sum, item) => sum + item.quantity, 0);
  const deliveryFee = (orderType === 'delivery' && totalQty < 5) ? 5 : 0;
  const total = subtotal + deliveryFee;
  
  const feeEl = document.getElementById('checkoutDeliveryFee');
  const totalEl = document.getElementById('checkoutTotal');
  
  if (feeEl && totalEl) {
    feeEl.textContent = deliveryFee > 0 ? `₹${deliveryFee.toFixed(2)}` : 'Free';
    totalEl.textContent = `₹${total.toFixed(2)}`;
  }
}

async function confirmOrder() {
  const form = document.getElementById('checkoutForm');
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }
  
  const name = document.getElementById('customerName').value.trim();
  const email = document.getElementById('customerEmail').value.trim();
  const phone = document.getElementById('customerPhone').value.trim();
  const orderType = document.querySelector('input[name="orderType"]:checked').value;
  const paymentMethod = document.querySelector('input[name="paymentMethod"]:checked').value;
  
  // Validate delivery details if delivery selected
  if (orderType === 'delivery') {
    const classroom = document.getElementById('classroom').value.trim();
    const department = document.getElementById('department').value.trim();
    const block = document.getElementById('block').value.trim();
    
    if (!classroom || !department || !block) {
      showToast('Please fill in all delivery details', 'error');
      return;
    }
  }
  
  const subtotal = state.cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  const totalQty = state.cart.reduce((sum, item) => sum + item.quantity, 0);
  const deliveryFee = (orderType === 'delivery' && totalQty < 5) ? 5 : 0;
  const totalPrice = subtotal + deliveryFee;
  
  const orderData = {
    customer_name: name,
    customer_email: email,
    customer_phone: phone,
    items: state.cart.map(item => ({ id: item.id, qty: item.quantity })),
    total_price: totalPrice,
    delivery_mode: orderType,
    payment_method: paymentMethod
  };
  
  if (orderType === 'delivery') {
    orderData.classroom = document.getElementById('classroom').value.trim();
    orderData.department = document.getElementById('department').value.trim();
    orderData.block = document.getElementById('block').value.trim();
  }
  
  const btn = document.getElementById('confirmOrderBtn');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner" style="width: 20px; height: 20px; border-width: 2px;"></div> Processing...';
  
  try {
    const response = await fetch('/api/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(orderData)
    });
    
    const data = await response.json();
    
    if (response.ok) {
      closeModal('checkoutModal');
      
      // Show success with OTP
      showToast(`Order placed! OTP: ${data.otp}`, 'success');
      alert(`✅ Order Placed Successfully!\n\n📦 Your OTP: ${data.otp}\n💰 Total: ₹${totalPrice.toFixed(2)}\n\n${orderType === 'delivery' ? '🚚 Will be delivered soon!' : '🏪 Show OTP at kiosk to collect'}\n\nThank you!`);
      
      // Clear cart
      state.cart = [];
      saveCart();
      updateCartBadge();
      
      // Reload menu and orders
      showLoading(true);
      try {
        await Promise.all([
          loadMenu(),
          loadOrders()
        ]);
        updateUserStats();
      } catch (error) {
        console.error('[ERROR] Failed to reload data after order:', error);
      } finally {
        showLoading(false);
      }
      
      // Navigate to orders
      navigateTo('orders');
    } else {
      showToast(data.error || 'Failed to place order', 'error');
    }
  } catch (error) {
    console.error('[ERROR] Order placement failed:', error);
    showToast('Failed to place order. Please try again.', 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fas fa-check-circle"></i> Place Order';
  }
}

// ==================== ORDERS ====================
async function loadOrders() {
  if (!state.user || !state.user.email) {
    console.error('[ORDERS] No user or email found, skipping order load');
    state.orders = [];
    return Promise.resolve();
  }
  
  console.log('[ORDERS] Loading orders for:', state.user.email);
  
  try {
    const url = `/api/orders/user/${encodeURIComponent(state.user.email)}`;
    console.log('[ORDERS] Fetching from URL:', url);
    
    const response = await fetch(url);
    console.log('[ORDERS] Response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('[ORDERS] Server returned error:', response.status, errorText);
      state.orders = [];
      return Promise.resolve();
    }
    
    const orders = await response.json();
    console.log('[ORDERS] Successfully received:', orders.length, 'orders');
    
    if (orders.length > 0) {
      console.log('[ORDERS] Sample order:', JSON.stringify(orders[0], null, 2));
    }
    
    state.orders = orders;
    return Promise.resolve();
    
  } catch (error) {
    console.error('[ERROR] Network error loading orders:', error);
    console.error('[ERROR] Error details:', error.message, error.stack);
    state.orders = [];
    return Promise.resolve(); // Don't reject, just set empty
  }
}

function renderOrders() {
  const container = document.getElementById('ordersContent');
  if (!container) return;
  
  console.log('[DEBUG] Rendering orders, count:', state.orders.length);
  console.log('[DEBUG] Menu items available:', state.menu.length);
  
  if (state.orders.length === 0) {
    container.innerHTML = `
      <div class="cart-empty">
        <i class="fas fa-receipt"></i>
        <h3>No orders yet</h3>
        <p>Place your first order to see it here!</p>
        <button class="btn btn-primary" onclick="navigateTo('menu')">
          <i class="fas fa-utensils"></i> Order Now
        </button>
      </div>
    `;
    return;
  }
  
  // Check if menu is loaded (needed to enrich order items)
  if (state.menu.length === 0) {
    container.innerHTML = `
      <div class="cart-empty">
        <div class="spinner" style="margin: 0 auto 1rem;"></div>
        <p style="color: var(--text-tertiary);">Loading order details...</p>
      </div>
    `;
    return;
  }
  
  container.innerHTML = state.orders.map(order => {
    // Parse items safely
    let itemsData;
    try {
      itemsData = typeof order.items === 'string' ? JSON.parse(order.items) : order.items;
    } catch (e) {
      console.error('[ERROR] Failed to parse order items:', e);
      itemsData = { items: [] };
    }
    
    const items = itemsData.items || [];
    console.log(`[DEBUG] Order #${order.id} - Raw items:`, items);
    
    // Enrich items with menu data
    const enrichedItems = items.map(item => {
      const menuItem = state.menu.find(m => m.id === item.id);
      if (!menuItem) {
        console.warn(`[WARN] Order #${order.id} - Item ID ${item.id} not found in menu`);
      }
      return {
        ...item,
        name: menuItem ? menuItem.name : 'Item',
        image: menuItem ? menuItem.image : null,
        price: menuItem ? menuItem.price : 0
      };
    });
    
    console.log(`[DEBUG] Order #${order.id} - Enriched items:`, enrichedItems);
    
    // Create items display with images - show message if no items
    let itemsDisplay = '';
    if (enrichedItems.length === 0) {
      itemsDisplay = '<div style="color: var(--text-tertiary); font-size: 0.875rem;">No item details available</div>';
    } else {
      itemsDisplay = enrichedItems.slice(0, 2).map(item => {
        const imageUrl = item.image ? `/static/images/${item.image}` : 'https://via.placeholder.com/60x60/1e1e2e/6366f1?text=Item';
        return `
          <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;">
            <img src="${imageUrl}" alt="${item.name}" 
                 style="width: 50px; height: 50px; border-radius: 8px; object-fit: cover;"
                 onerror="this.src='https://via.placeholder.com/60x60/1e1e2e/6366f1?text=Item'">
            <div style="flex: 1;">
              <div style="font-weight: 500; color: var(--text-primary);">${item.name}</div>
              <div style="font-size: 0.875rem; color: var(--text-tertiary);">Qty: ${item.qty}</div>
            </div>
          </div>
        `;
      }).join('');
    }
    
    const moreItemsCount = enrichedItems.length > 2 ? enrichedItems.length - 2 : 0;
    
    return `
      <div class="order-card" onclick="viewOrderDetails(${order.id})">
        <div class="order-header">
          <div>
            <div class="order-id">Order #${order.id}</div>
            <div style="color: var(--text-tertiary); font-size: 0.875rem; margin-top: 0.25rem;">
              ${new Date(order.created_at).toLocaleString()}
            </div>
          </div>
          <span class="order-status ${order.status.toLowerCase().replace(/\s+/g, '-')}">${order.status}</span>
        </div>
        <div class="order-items" style="padding: 1rem 0;">
          ${itemsDisplay}
          ${moreItemsCount > 0 ? `<div style="color: var(--text-tertiary); font-size: 0.875rem; margin-top: 0.5rem;">+${moreItemsCount} more item${moreItemsCount > 1 ? 's' : ''}</div>` : ''}
        </div>
        <div class="order-footer">
          <div class="order-total">₹${order.total_price.toFixed(2)}</div>
          <div class="order-actions">
            <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); reorder(${order.id})">
              <i class="fas fa-redo"></i> Reorder
            </button>
            <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); viewOrderDetails(${order.id})">
              <i class="fas fa-eye"></i> View
            </button>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function viewOrderDetails(orderId) {
  const order = state.orders.find(o => o.id === orderId);
  if (!order) return;
  
  const modal = document.getElementById('orderDetailsModal');
  const body = document.getElementById('orderDetailsModalBody');
  
  // Parse items safely
  let itemsData;
  try {
    itemsData = typeof order.items === 'string' ? JSON.parse(order.items) : order.items;
  } catch (e) {
    console.error('[ERROR] Failed to parse order items:', e);
    itemsData = { items: [] };
  }
  
  const items = itemsData.items || [];
  const deliveryMode = itemsData.delivery_mode || 'pickup';
  const classroom = itemsData.classroom || '';
  const department = itemsData.department || '';
  const block = itemsData.block || '';
  
  // Enrich items with menu data
  const enrichedItems = items.map(item => {
    const menuItem = state.menu.find(m => m.id === item.id);
    return {
      ...item,
      name: menuItem ? menuItem.name : 'Item',
      image: menuItem ? menuItem.image : null,
      price: menuItem ? menuItem.price : 0
    };
  });
  
  body.innerHTML = `
    <div style="margin-bottom: 1.5rem;">
      <h4 style="font-size: 1.25rem; margin-bottom: 0.5rem;">Order #${order.id}</h4>
      <p style="color: var(--text-tertiary);">${new Date(order.created_at).toLocaleString()}</p>
      <span class="order-status ${order.status.toLowerCase().replace(/\s+/g, '-')}" style="display: inline-block; margin-top: 0.5rem;">${order.status}</span>
    </div>
    
    ${deliveryMode === 'delivery' && (classroom || department || block) ? `
      <div style="margin-bottom: 1.5rem; padding: 1rem; background: var(--bg-elevated); border-radius: var(--radius);">
        <h4 style="margin-bottom: 0.75rem;">Delivery Details</h4>
        ${classroom ? `<div style="margin-bottom: 0.5rem;"><strong>Classroom:</strong> ${classroom}</div>` : ''}
        ${department ? `<div style="margin-bottom: 0.5rem;"><strong>Department:</strong> ${department}</div>` : ''}
        ${block ? `<div><strong>Block:</strong> ${block}</div>` : ''}
      </div>
    ` : ''}
    
    <div style="margin-bottom: 1.5rem;">
      <h4 style="margin-bottom: 0.75rem;">Items</h4>
      ${enrichedItems.length === 0 ? 
        '<div style="padding: 1rem; text-align: center; color: var(--text-tertiary);">No item details available for this order</div>' 
        : 
        enrichedItems.map(item => {
          const imageUrl = item.image ? `/static/images/${item.image}` : 'https://via.placeholder.com/80x80/1e1e2e/6366f1?text=Item';
          return `
            <div style="display: flex; gap: 1rem; padding: 1rem 0; border-bottom: 1px solid var(--border);">
              <img src="${imageUrl}" alt="${item.name}" 
                   style="width: 80px; height: 80px; border-radius: 12px; object-fit: cover; flex-shrink: 0;"
                   onerror="this.src='https://via.placeholder.com/80x80/1e1e2e/6366f1?text=Item'">
              <div style="flex: 1; display: flex; flex-direction: column; justify-content: center;">
                <div style="font-weight: 600; font-size: 1rem; margin-bottom: 0.25rem;">${item.name}</div>
                <div style="color: var(--text-tertiary); font-size: 0.875rem;">Quantity: ${item.qty}</div>
                <div style="color: var(--text-tertiary); font-size: 0.875rem;">Price: ₹${item.price.toFixed(2)} each</div>
              </div>
              <div style="text-align: right; display: flex; align-items: center;">
                <div style="font-weight: 700; font-size: 1.125rem; color: var(--primary);">₹${(item.price * item.qty).toFixed(2)}</div>
              </div>
            </div>
          `;
        }).join('')
      }
    </div>
    
    <div style="padding: 1rem; background: var(--bg-elevated); border-radius: var(--radius);">
      <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
        <span>Subtotal</span>
        <span>₹${order.total_price.toFixed(2)}</span>
      </div>
      <div style="display: flex; justify-content: space-between; padding-top: 0.5rem; border-top: 1px solid var(--border); font-weight: 700; font-size: 1.125rem;">
        <span>Total</span>
        <span>₹${order.total_price.toFixed(2)}</span>
      </div>
    </div>
    
    ${order.otp ? `
      <div style="margin-top: 1.5rem; padding: 1rem; background: rgba(99, 102, 241, 0.1); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: var(--radius); text-align: center;">
        <div style="font-weight: 600; margin-bottom: 0.5rem;">Your OTP</div>
        <div style="font-size: 2rem; font-weight: 800; letter-spacing: 0.25em; color: var(--primary);">${order.otp}</div>
        <div style="font-size: 0.875rem; color: var(--text-tertiary); margin-top: 0.5rem;">Show this at the kiosk to collect your order</div>
      </div>
    ` : ''}
  `;
  
  modal.classList.add('active');
}

async function reorder(orderId) {
  const order = state.orders.find(o => o.id === orderId);
  if (!order) return;
  
  // Parse items safely
  let itemsData;
  try {
    itemsData = typeof order.items === 'string' ? JSON.parse(order.items) : order.items;
  } catch (e) {
    console.error('[ERROR] Failed to parse order items:', e);
    showToast('Failed to load order items', 'error');
    return;
  }
  
  const items = itemsData.items || [];
  let addedCount = 0;
  
  for (const orderItem of items) {
    const menuItem = state.menu.find(m => m.id === orderItem.id);
    if (menuItem && menuItem.available && menuItem.stock > 0) {
      const existingItem = state.cart.find(i => i.id === orderItem.id);
      const qtyToAdd = Math.min(orderItem.qty, menuItem.stock);
      
      if (existingItem) {
        const newQty = Math.min(existingItem.quantity + qtyToAdd, menuItem.stock);
        existingItem.quantity = newQty;
      } else {
        state.cart.push({ ...menuItem, quantity: qtyToAdd });
      }
      addedCount++;
    }
  }
  
  if (addedCount > 0) {
    saveCart();
    updateCartBadge();
    showToast(`${addedCount} item(s) added to cart!`, 'success');
    navigateTo('cart');
  } else {
    showToast('No items available from this order', 'warning');
  }
}

function reorderLast() {
  if (state.orders.length === 0) {
    showToast('No previous orders', 'warning');
    navigateTo('menu');
    return;
  }
  
  reorder(state.orders[0].id);
}

// ==================== USER STATS ====================
function updateUserStats() {
  console.log('[STATS] Updating user stats...');
  console.log('[STATS] Orders:', state.orders.length);
  console.log('[STATS] Favorites:', state.favorites.size);
  
  const totalOrders = state.orders.length;
  const savedAmount = state.orders.reduce((sum, order) => sum + (order.total_price * 0.05), 0); // Assuming 5% savings
  
  console.log('[STATS] Calculated - Orders:', totalOrders, 'Saved:', savedAmount);
  
  // First, make stat cards visible with fade-in animation
  const statCards = document.querySelectorAll('[data-stat-card]');
  statCards.forEach((card, index) => {
    setTimeout(() => {
      card.style.transition = 'opacity 0.6s ease';
      card.style.opacity = '1';
    }, index * 150);
  });
  
  // Then animate the values after cards are visible (wait for first card to start appearing)
  setTimeout(() => {
    animateValue('totalOrdersStat', 0, totalOrders, 800);
    animateValue('savedAmountStat', 0, Math.floor(savedAmount), 800, '₹');
  }, 200);
}

function animateValue(elementId, start, end, duration, prefix = '') {
  const element = document.getElementById(elementId);
  if (!element) return;
  
  const range = end - start;
  const increment = range / (duration / 16); // 60fps
  let current = start;
  
  const timer = setInterval(() => {
    current += increment;
    if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
      current = end;
      clearInterval(timer);
    }
    element.textContent = prefix + Math.floor(current);
  }, 16);
}

// ==================== MODALS ====================
function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
  }
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('active');
  }
});

// ==================== UTILITIES ====================
function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  if (!container) return;
  
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const icons = {
    success: 'fa-check-circle',
    error: 'fa-exclamation-circle',
    warning: 'fa-exclamation-triangle'
  };
  
  toast.innerHTML = `
    <i class="fas ${icons[type] || icons.success}"></i>
    <span>${message}</span>
  `;
  
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function showLoading(show) {
  const overlay = document.getElementById('loadingOverlay');
  if (overlay) {
    overlay.classList.toggle('hidden', !show);
  }
}

// ==================== ANIMATIONS ====================
function initAnimations() {
  // Only animate if on home page
  if (state.currentPage !== 'home') return;
  
  // Add CSS animation classes to hero elements
  const animateElements = [
    { selector: '.hero-badge', delay: 200 },
    { selector: '.hero-title', delay: 400 },
    { selector: '.hero-subtitle', delay: 600 },
    { selector: '.hero-actions', delay: 800 }
  ];
  
  animateElements.forEach(({ selector, delay }) => {
    const element = document.querySelector(selector);
    if (element) {
      setTimeout(() => {
        element.style.animation = 'fadeInUp 0.6s ease forwards';
      }, delay);
    }
  });
  // Note: stat-card animations are handled by updateUserStats() function
}

function animateCards() {
  // Get all menu cards
  const cards = document.querySelectorAll('.menu-card');
  
  if (cards.length > 0) {
    // Only animate cards that haven't been animated yet
    cards.forEach((card, index) => {
      // Check if card already has been animated
      if (card.dataset.animated === 'true') {
        return; // Skip already animated cards
      }
      
      // Mark as animated
      card.dataset.animated = 'true';
      
      // Set initial state
      card.style.opacity = '0';
      card.style.transform = 'translateY(30px)';
      
      // Animate to final state
      setTimeout(() => {
        card.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
      }, index * 50);
    });
  }
}

// Make functions globally accessible
window.navigateTo = navigateTo;
window.toggleFavorite = toggleFavorite;
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.updateQuantity = updateQuantity;
window.openCheckout = openCheckout;
window.updateCheckoutTotal = updateCheckoutTotal;
window.confirmOrder = confirmOrder;
window.viewOrderDetails = viewOrderDetails;
window.reorder = reorder;
window.reorderLast = reorderLast;
window.closeModal = closeModal;
window.logout = logout;