/* ===================================================================
   FoodAI - Core Application JavaScript
   =================================================================== */

// Global state
let cart = JSON.parse(localStorage.getItem('foodai_cart') || '[]');
let currentDiscount = 0;

document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    updateCartUI();
    initNLPrompt();
    initAuthUser();
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
    openCheckoutModal();
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

// -------------------------------------------------------------------
// ZOMATO-STYLE CHECKOUT, ADDRESS & ORDER PLACEMENT
// -------------------------------------------------------------------
function openCheckoutModal() {
    if (!cart || cart.length === 0) {
        showToast("Your cart is empty! Add delicious meals to order.", "warning");
        return;
    }

    const subtotal = cart.reduce((sum, it) => sum + (it.price * it.quantity), 0);
    const itemTotalEl = document.getElementById('modalItemTotal');
    if (itemTotalEl) itemTotalEl.textContent = `₹${subtotal.toFixed(2)}`;

    // Recompute coupon if one was active
    recalculateCheckoutBill();

    // Close offcanvas cart drawer
    const cartOffcanvasEl = document.getElementById('cartOffcanvas');
    if (cartOffcanvasEl) {
        const bsOffcanvas = bootstrap.Offcanvas.getInstance(cartOffcanvasEl);
        if (bsOffcanvas) bsOffcanvas.hide();
    }

    // Open checkout modal
    const checkoutModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('checkoutModal'));
    checkoutModal.show();
}

function recalculateCheckoutBill() {
    const subtotal = cart.reduce((sum, it) => sum + (it.price * it.quantity), 0);
    const taxes = 15.0;
    const discountRow = document.getElementById('modalDiscountRow');
    const discountAmountEl = document.getElementById('modalDiscountAmount');
    const grandTotalEl = document.getElementById('modalGrandTotal');

    if (currentDiscount > 0) {
        if (discountRow) discountRow.classList.remove('d-none');
        if (discountAmountEl) discountAmountEl.textContent = `-₹${currentDiscount.toFixed(2)}`;
    } else {
        if (discountRow) discountRow.classList.add('d-none');
    }

    const grandTotal = Math.max(0, subtotal + taxes - currentDiscount);
    if (grandTotalEl) grandTotalEl.textContent = `₹${grandTotal.toFixed(2)}`;
}

function toggleInstruction(btn, text) {
    btn.classList.toggle('active');
}

function setAndApplyCoupon(code) {
    const input = document.getElementById('couponCodeInput');
    if (input) input.value = code;
    applyCouponCode();
}

function applyCouponCode() {
    const input = document.getElementById('couponCodeInput');
    const statusMsg = document.getElementById('couponStatusMessage');
    const code = (input ? input.value : '').trim().toUpperCase();
    const subtotal = cart.reduce((sum, it) => sum + (it.price * it.quantity), 0);

    if (!code) {
        showToast("Please enter a coupon code", "warning");
        return;
    }

    if (code === 'SAVE50') {
        if (subtotal < 100) {
            showToast("SAVE50 requires a minimum order of ₹100", "warning");
            return;
        }
        currentDiscount = 50.0;
    } else if (code === 'WELCOME20') {
        currentDiscount = Math.round(subtotal * 0.20);
    } else if (code === 'ECOSAVE') {
        currentDiscount = Math.round(subtotal * 0.15);
    } else {
        showToast(`Coupon '${code}' is invalid or expired`, "danger");
        return;
    }

    recalculateCheckoutBill();

    if (statusMsg) {
        statusMsg.classList.remove('d-none');
        statusMsg.innerHTML = `<i class="fa-solid fa-circle-check me-1"></i> Coupon <strong>${code}</strong> applied! ₹${currentDiscount.toFixed(2)} saved.`;
    }

    showToast(`🎉 Coupon ${code} applied! Saved ₹${currentDiscount.toFixed(2)}`, "success");
}

function submitZomatoOrder() {
    if (!cart || cart.length === 0) {
        showToast("Your cart is empty!", "warning");
        return;
    }

    const nameInput = document.getElementById('checkoutName');
    const phoneInput = document.getElementById('checkoutPhone');
    const flatInput = document.getElementById('checkoutFlat');
    const areaInput = document.getElementById('checkoutArea');
    const addrType = document.querySelector('input[name="addrType"]:checked')?.value || 'Home';
    const paymentOption = document.querySelector('input[name="paymentOption"]:checked')?.value || 'upi';

    const name = nameInput ? nameInput.value.trim() : '';
    const phone = phoneInput ? phoneInput.value.trim() : '';
    const flat = flatInput ? flatInput.value.trim() : '';
    const area = areaInput ? areaInput.value.trim() : '';

    if (!name || !phone || !flat || !area) {
        showToast("Please fill in Name, Phone, and Address fields!", "danger");
        return;
    }

    // Collect active delivery instructions
    const activeInstructions = Array.from(document.querySelectorAll('.instruction-pill.active'))
        .map(b => b.innerText.trim())
        .join(', ');

    const fullAddress = `[${addrType}] ${flat}, ${area}`;

    const confirmBtn = document.getElementById('confirmOrderBtn');
    if (confirmBtn) {
        confirmBtn.disabled = true;
        confirmBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin me-2"></i>Placing Order...`;
    }

    fetch('/api/place-order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            items: cart,
            customer_name: name,
            customer_phone: phone,
            address: fullAddress,
            delivery_instructions: activeInstructions,
            order_type: 'zomato_checkout',
            discount_amount: currentDiscount
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            const order = data.order || {};
            const orderIdEl = document.getElementById('successOrderId');
            const etaEl = document.getElementById('successOrderEta');
            const addrEl = document.getElementById('successOrderAddress');

            if (orderIdEl) orderIdEl.textContent = '#' + (order.id || Math.floor(100 + Math.random() * 900));
            if (etaEl) etaEl.textContent = `~${order.total_eta_min || 25} mins`;
            if (addrEl) addrEl.textContent = fullAddress;

            // Clear cart
            cart = [];
            saveCart();
            currentDiscount = 0;

            // Hide checkout modal
            const checkoutModalEl = document.getElementById('checkoutModal');
            if (checkoutModalEl) {
                const bsCheckout = bootstrap.Modal.getInstance(checkoutModalEl);
                if (bsCheckout) bsCheckout.hide();
            }

            // Open Order Success Modal
            const successModal = bootstrap.Modal.getOrCreateInstance(document.getElementById('orderSuccessModal'));
            successModal.show();
            showToast("🎉 Order placed successfully! Kitchen has started preparing.", "success");
        } else {
            showToast("Failed to place order: " + (data.message || 'Error occurred'), "danger");
        }
    })
    .catch(err => {
        console.error(err);
        showToast("Network error while placing order", "danger");
    })
    .finally(() => {
        if (confirmBtn) {
            confirmBtn.disabled = false;
            confirmBtn.innerHTML = `<i class="fa-solid fa-lock me-2"></i>Pay & Place Order`;
        }
    });
}

function resetCartUI() {
    const successModalEl = document.getElementById('orderSuccessModal');
    if (successModalEl) {
        const bsModal = bootstrap.Modal.getInstance(successModalEl);
        if (bsModal) bsModal.hide();
    }
    updateCartUI();
}

// -------------------------------------------------------------------
// USER AUTHENTICATION & QUICK DEMO ROLES (ZOMATO STYLE)
// -------------------------------------------------------------------
function initAuthUser() {
    const savedUser = localStorage.getItem('foodfusion_user');
    if (savedUser) {
        try {
            const user = JSON.parse(savedUser);
            renderUserNav(user);
            populateCheckoutUser(user);
        } catch (e) {
            console.error(e);
        }
    }
}

function renderUserNav(user) {
    const container = document.getElementById('authNavContainer');
    if (!container) return;

    const initials = user.name ? user.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() : 'U';

    container.innerHTML = `
        <div class="dropdown">
            <button class="btn btn-sm btn-light border rounded-pill d-flex align-items-center gap-2 px-2 py-1" data-bs-toggle="dropdown">
                <span class="user-avatar" style="width: 26px; height: 26px; font-size: 0.72rem; background: #e23744;">${initials}</span>
                <span class="fw-bold small text-dark d-none d-sm-inline">${user.name}</span>
                <i class="fa-solid fa-chevron-down text-muted" style="font-size: 10px;"></i>
            </button>
            <ul class="dropdown-menu dropdown-menu-end shadow border-0 rounded-3 p-2">
                <li class="px-3 py-2 border-bottom mb-1">
                    <div class="fw-bold small text-dark">${user.name}</div>
                    <small class="text-muted text-capitalize">${user.role || 'Customer'} • ${user.phone || ''}</small>
                </li>
                <li><a class="dropdown-item rounded-2 py-2 small" href="#checkoutModal" onclick="openCheckoutModal()"><i class="fa-solid fa-bag-shopping me-2 text-danger"></i>My Cart & Checkout</a></li>
                <li><a class="dropdown-item rounded-2 py-2 small" href="/analytics"><i class="fa-solid fa-chart-line me-2 text-primary"></i>Orders & Analytics</a></li>
                <li><hr class="dropdown-divider"></li>
                <li><button class="dropdown-item rounded-2 py-2 small text-danger" onclick="logoutUser()"><i class="fa-solid fa-right-from-bracket me-2"></i>Log out</button></li>
            </ul>
        </div>
    `;
}

function populateCheckoutUser(user) {
    const nameInput = document.getElementById('checkoutName');
    const phoneInput = document.getElementById('checkoutPhone');
    const flatInput = document.getElementById('checkoutFlat');
    const areaInput = document.getElementById('checkoutArea');

    if (nameInput && user.name) nameInput.value = user.name;
    if (phoneInput && user.phone) phoneInput.value = user.phone;
    if (user.address) {
        if (flatInput) flatInput.value = user.address.split(',')[0] || user.address;
        if (areaInput) areaInput.value = user.address.split(',').slice(1).join(',').trim() || 'Indiranagar, Bengaluru';
    }
}

function quickLoginRole(role, name, phone, address) {
    const user = { role, name, phone, address };
    localStorage.setItem('foodfusion_user', JSON.stringify(user));
    renderUserNav(user);
    populateCheckoutUser(user);

    const loginModalEl = document.getElementById('loginModal');
    if (loginModalEl) {
        const bsModal = bootstrap.Modal.getInstance(loginModalEl);
        if (bsModal) bsModal.hide();
    }

    showToast(`Logged in as ${name} (${role.toUpperCase()})`, "success");
}

function handlePhoneLogin() {
    const phoneInput = document.getElementById('loginPhoneInput');
    const rawPhone = phoneInput ? phoneInput.value.trim() : '';

    if (!rawPhone || rawPhone.length < 10) {
        showToast("Please enter a valid 10-digit mobile number", "warning");
        return;
    }

    const phone = '+91 ' + rawPhone.replace(/\\D/g, '').slice(-10);
    const user = {
        role: 'customer',
        name: 'Aman Gupta',
        phone: phone,
        address: 'Flat 402, Green Glen Towers, Indiranagar'
    };

    localStorage.setItem('foodfusion_user', JSON.stringify(user));
    renderUserNav(user);
    populateCheckoutUser(user);

    const loginModalEl = document.getElementById('loginModal');
    if (loginModalEl) {
        const bsModal = bootstrap.Modal.getInstance(loginModalEl);
        if (bsModal) bsModal.hide();
    }

    showToast(`Welcome! Logged in with ${phone}`, "success");
}

function logoutUser() {
    localStorage.removeItem('foodfusion_user');
    const container = document.getElementById('authNavContainer');
    if (container) {
        container.innerHTML = `
            <button class="btn btn-outline-danger btn-sm fw-bold px-3 py-1 rounded-pill" data-bs-toggle="modal" data-bs-target="#loginModal" id="loginNavBtn">
                <i class="fa-solid fa-user me-1"></i>Log in
            </button>
        `;
    }
    showToast("Logged out successfully", "info");
}

function selectQuickLocation(areaName, flatDetail) {
    const navAddr = document.getElementById('navAddressDisplay');
    const areaInput = document.getElementById('checkoutArea');
    const flatInput = document.getElementById('checkoutFlat');

    if (navAddr) navAddr.textContent = areaName;
    if (areaInput) areaInput.value = areaName + ', Bengaluru';
    if (flatInput && flatDetail) flatInput.value = flatDetail;

    const modalEl = document.getElementById('addressPickerModal');
    if (modalEl) {
        const bsModal = bootstrap.Modal.getInstance(modalEl);
        if (bsModal) bsModal.hide();
    }

    showToast(`Delivery location set to ${areaName}`, "success");
}
