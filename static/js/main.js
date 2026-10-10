/* ===================================================================
   FoodAI - Core Application JavaScript
   =================================================================== */

// Global state
let cart = JSON.parse(localStorage.getItem('foodai_cart') || '[]');

document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    updateCartUI();
    initNLPrompt();
});

// Sidebar Mobile Toggle
function initSidebar() {
    const sidebar = document.getElementById('appSidebar');
    const toggleBtn = document.getElementById('sidebarToggleBtn');
    const closeBtn = document.getElementById('sidebarCloseBtn');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
    }

    if (closeBtn && sidebar) {
        closeBtn.addEventListener('click', () => {
            sidebar.classList.remove('show');
        });
    }
}

// -------------------------------------------------------------------
// CART MANAGEMENT
// -------------------------------------------------------------------
function addToCart(dishId, name, price, restaurantName, imageUrl, isVeg) {
    const existing = cart.find(item => item.id === dishId);
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({
            id: dishId,
            name: name,
            price: parseFloat(price),
            restaurantName: restaurantName || "Partner Kitchen",
            imageUrl: imageUrl || "",
            isVeg: isVeg !== undefined ? isVeg : true,
            quantity: 1
        });
    }
    saveCart();
    showToast(`Added ${name} to Smart Cart!`, "success");
    
    // Automatically trigger offcanvas preview
    const cartOffcanvasEl = document.getElementById('cartOffcanvas');
    if (cartOffcanvasEl) {
        const bsOffcanvas = bootstrap.Offcanvas.getOrCreateInstance(cartOffcanvasEl);
        bsOffcanvas.show();
    }
}

function updateCartQuantity(dishId, delta) {
    const item = cart.find(it => it.id === dishId);
    if (!item) return;

    item.quantity += delta;
    if (item.quantity <= 0) {
        cart = cart.filter(it => it.id !== dishId);
    }
    saveCart();
}

function saveCart() {
    localStorage.setItem('foodai_cart', JSON.stringify(cart));
    updateCartUI();
}

function updateCartUI() {
    const badge = document.getElementById('cartBadgeCount');
    const emptyState = document.getElementById('cartEmptyState');
    const itemsList = document.getElementById('cartItemsList');
    const footerArea = document.getElementById('cartFooterArea');
    const subtotalEl = document.getElementById('cartSubtotal');
    const grandTotalEl = document.getElementById('cartGrandTotal');

    const totalCount = cart.reduce((sum, it) => sum + it.quantity, 0);
    if (badge) badge.textContent = totalCount;

    if (cart.length === 0) {
        if (emptyState) emptyState.classList.remove('d-none');
        if (itemsList) itemsList.classList.add('d-none');
        if (footerArea) footerArea.classList.add('d-none');
        return;
    }

    if (emptyState) emptyState.classList.add('d-none');
    if (itemsList) itemsList.classList.remove('d-none');
    if (footerArea) footerArea.classList.remove('d-none');

    let subtotal = 0;
    if (itemsList) {
        itemsList.innerHTML = cart.map(item => {
            const itemTotal = item.price * item.quantity;
            subtotal += itemTotal;
            return `
                <div class="cart-item-row d-flex align-items-center justify-content-between p-2 mb-2 rounded bg-white border">
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge ${item.isVeg ? 'bg-success' : 'bg-danger'} rounded-circle p-1"></span>
                        <div>
                            <div class="fw-bold small text-truncate" style="max-width: 140px;">${item.name}</div>
                            <small class="text-muted">₹${item.price.toFixed(2)}</small>
                        </div>
                    </div>
                    <div class="d-flex align-items-center gap-2">
                        <button class="btn btn-sm btn-outline-secondary py-0 px-2" onclick="updateCartQuantity(${item.id}, -1)">-</button>
                        <span class="fw-bold small">${item.quantity}</span>
                        <button class="btn btn-sm btn-outline-secondary py-0 px-2" onclick="updateCartQuantity(${item.id}, 1)">+</button>
                        <span class="fw-bold small text-primary ms-2">₹${itemTotal.toFixed(2)}</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    const taxes = 15.0;
    const grandTotal = subtotal + taxes;

    if (subtotalEl) subtotalEl.textContent = `₹${subtotal.toFixed(2)}`;
    if (grandTotalEl) grandTotalEl.textContent = `₹${grandTotal.toFixed(2)}`;

    // Query predictive order timing
    fetchOrderPrediction(cart.length);
}

function fetchOrderPrediction(itemCount) {
    fetch('/api/predict-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ item_count: itemCount, distance_km: 3.2 })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            const p = data.prediction;
            const etaEl = document.getElementById('cartEtaDisplay');
            const delayEl = document.getElementById('cartDelayStatus');
            if (etaEl) etaEl.innerHTML = `<i class="fa-solid fa-clock text-primary me-1"></i>~${p.total_eta_min} mins (${p.predicted_prep_min}m prep + ${p.predicted_delivery_min}m transit)`;
            if (delayEl) {
                if (p.is_delayed) {
                    delayEl.className = "badge bg-warning-subtle text-warning-emphasis";
                    delayEl.textContent = "Delay Risk Flagged";
                } else {
                    delayEl.className = "badge bg-success-subtle text-success";
                    delayEl.textContent = "On Time Guarantee";
                }
            }
        }
    })
    .catch(err => console.error(err));
}

function handleCheckout() {
    if (cart.length === 0) return;

    const checkoutBtn = document.getElementById('checkoutBtn');
    if (checkoutBtn) {
        checkoutBtn.disabled = true;
        checkoutBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-2"></i>Optimizing Dispatch...`;
    }

    fetch('/api/place-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            items: cart,
            customer_name: "Aman Gupta",
            address: "102 Indiranagar 100ft Rd, Bengaluru",
            order_type: "ai_smart_cart"
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            cart = [];
            saveCart();
            const cartOffcanvasEl = document.getElementById('cartOffcanvas');
            const bsOffcanvas = bootstrap.Offcanvas.getInstance(cartOffcanvasEl);
            if (bsOffcanvas) bsOffcanvas.hide();

            showToast(`🎉 Order Placed Successfully! Order #${data.order.id}. ETA: ${data.order.total_eta_min} mins.`, "success");
            
            // Redirect to map to track delivery live after 1.2s
            setTimeout(() => {
                window.location.href = '/map';
            }, 1200);
        } else {
            showToast("Failed to place order: " + data.message, "danger");
        }
    })
    .catch(err => {
        console.error(err);
        showToast("Error communicating with server", "danger");
    })
    .finally(() => {
        if (checkoutBtn) {
            checkoutBtn.disabled = false;
            checkoutBtn.innerHTML = `<i class="fa-solid fa-lock me-2"></i>Place AI Order`;
        }
    });
}

// -------------------------------------------------------------------
// NATURAL LANGUAGE HERO BAR (Feature 1)
// -------------------------------------------------------------------
function initNLPrompt() {
    const nlBtn = document.getElementById('nlSubmitBtn');
    const nlInput = document.getElementById('nlPromptInput');

    if (nlBtn && nlInput) {
        nlBtn.addEventListener('click', () => runNLQuery(nlInput.value));
        nlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') runNLQuery(nlInput.value);
        });
    }
}

function setPresetPrompt(text) {
    const nlInput = document.getElementById('nlPromptInput');
    if (nlInput) {
        nlInput.value = text;
        runNLQuery(text);
    }
}

function runNLQuery(promptText) {
    if (!promptText || !promptText.trim()) {
        showToast("Please enter an order prompt!", "warning");
        return;
    }

    const btn = document.getElementById('nlSubmitBtn');
    const resultBox = document.getElementById('nlResultSection');
    
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-2"></i>AI Reasoning...`;
    }

    fetch('/api/nl-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: promptText })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success' || data.status === 'partial_match') {
            renderNLResult(data);
        } else {
            showToast(data.message || "Could not parse query", "warning");
        }
    })
    .catch(err => {
        console.error(err);
        showToast("AI query failed. Please try again.", "danger");
    })
    .finally(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-wand-magic-sparkles me-1"></i>Build Smart Cart`;
        }
    });
}

function renderNLResult(data) {
    const container = document.getElementById('nlResultSection');
    if (!container) return;

    const c = data.constraints_parsed;
    let itemsHtml = data.items.map(dish => `
        <div class="col-md-4 mb-3">
            <div class="card h-100 shadow-sm border-0 rounded-3">
                <img src="${dish.image_url}" class="card-img-top" style="height: 120px; object-fit: cover;" alt="${dish.name}">
                <div class="card-body p-3">
                    <div class="d-flex justify-content-between align-items-center mb-1">
                        <span class="badge ${dish.is_veg ? 'bg-success' : 'bg-danger'}">${dish.is_veg ? 'Veg' : 'Non-Veg'}</span>
                        <span class="badge bg-light text-dark">${dish.spice_level.toUpperCase()}</span>
                    </div>
                    <h6 class="fw-bold mb-1">${dish.name}</h6>
                    <div class="text-primary fw-bold">₹${dish.price.toFixed(2)}</div>
                </div>
            </div>
        </div>
    `).join('');

    container.innerHTML = `
        <div class="card border-0 shadow-lg rounded-4 p-4 mb-4 bg-white">
            <div class="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-3">
                <div class="d-flex align-items-center gap-2">
                    <span class="badge bg-primary fs-6 px-3 py-2"><i class="fa-solid fa-brain me-2"></i>AI Solution Found</span>
                    <span class="badge bg-success-subtle text-success fw-bold px-3 py-2">Total: ₹${data.total_price.toFixed(2)} / Budget: ₹${data.budget}</span>
                </div>
                <button class="btn btn-primary fw-bold px-4" onclick='applyNLToCart(${JSON.stringify(data.items)})'>
                    <i class="fa-solid fa-cart-plus me-2"></i>Add All ${data.items.length} Items to Cart
                </button>
            </div>

            <!-- Transparent Explanation Box -->
            <div class="alert alert-info border-0 rounded-3 d-flex align-items-start gap-3 mb-4">
                <i class="fa-solid fa-circle-info fa-lg mt-1 text-primary"></i>
                <div>
                    <h6 class="fw-bold mb-1 text-dark">Why AI Chose This Cart:</h6>
                    <p class="mb-0 small text-secondary">${data.explanation}</p>
                </div>
            </div>

            <!-- Extracted Constraints Badges -->
            <div class="d-flex gap-2 mb-3 flex-wrap">
                <span class="badge bg-secondary-subtle text-dark">Budget: ₹${c.budget}</span>
                <span class="badge bg-secondary-subtle text-dark">Servings: ${c.people_count} People</span>
                <span class="badge bg-secondary-subtle text-dark">Veg Meals: ${c.veg_count}</span>
                <span class="badge bg-secondary-subtle text-dark">Spicy Meals: ${c.spicy_count}</span>
                <span class="badge bg-success-subtle text-success">Saved: ₹${data.savings.toFixed(2)}</span>
            </div>

            <div class="row">
                ${itemsHtml}
            </div>
        </div>
    `;

    container.scrollIntoView({ behavior: 'smooth' });
}

function applyNLToCart(items) {
    items.forEach(dish => {
        addToCart(dish.id, dish.name, dish.price, dish.restaurant_name, dish.image_url, dish.is_veg);
    });
    showToast(`Successfully added all ${items.length} AI selected meals to your cart!`, "success");
}

// -------------------------------------------------------------------
// TOAST NOTIFICATIONS
// -------------------------------------------------------------------
function showToast(message, type = "info") {
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        toastContainer.style.zIndex = '1090';
        document.body.appendChild(toastContainer);
    }

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : (type === 'danger' ? 'danger' : 'primary')} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');

    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body fw-medium">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toastEl);
    const bsToast = new bootstrap.Toast(toastEl, { delay: 4000 });
    bsToast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}
