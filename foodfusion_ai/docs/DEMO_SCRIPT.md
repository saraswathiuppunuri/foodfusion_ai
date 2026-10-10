# FoodFusion AI — Hackathon Live Demo Script & Walkthrough

This demo guide walks judges and evaluators through all 5 unique differentiating AI features and the 4 user role workflows in **FoodFusion AI**.

---

## 1. Quick Access Credentials

For rapid evaluation, the login screen includes **1-Tap Demo Login Buttons** that instantly authenticate each role:

| Role | Email | Password | Primary Dashboard |
| :--- | :--- | :--- | :--- |
| **Customer** | `customer@foodfusion.ai` | `Customer@123` | Customer Home & Bottom Navigation |
| **Restaurant Owner** | `owner@spicevilla.com` | `Owner@123` | Kitchen Management & Analytics |
| **Delivery Partner** | `rider@foodfusion.ai` | `Rider@123` | Fleet Dispatch & Earnings |
| **Administrator** | `admin@foodfusion.ai` | `Admin@123` | Platform Health & Approvals |

---

## 2. Walkthrough: The 5 Unique Differentiating Features

### Feature 1: Explainable AI Food Recommendations
> *"Why did the AI choose this dish for me?"*

1. **Step**: On the Home screen, tap the purple **"AI Picks"** button or go to Discover.
2. **Action**: The app executes `GET /recommendations`.
3. **What to Observe**:
   - Every card displays an **AI Match Score Badge** (e.g., `96% MATCH`, `88% MATCH`).
   - Every card features an **Explainability Callout Box**:
     > *"Recommended because you prefer spicy vegetarian food and this meal fits your ₹300 budget."*
   - Change your profile preferences in Profile (`/profile`) from *Vegetarian* to *High Protein* or alter your spice preference, and tap **Save & Re-train AI Model**. Return to AI Picks to witness the recommendations and match scores update dynamically.

---

### Feature 2: Smart Budget Meal Planner (The ₹150 Guarantee)
> *"Can I get a full, nutritious meal delivered for under ₹150 with all taxes and delivery included?"*

1. **Step**: On the Home screen, tap the orange **"₹150 Combos"** button.
2. **Action**: Set the budget slider to **₹150** (or enter a custom value like ₹250 or ₹500). Toggle the **Vegetarian Only** switch. Tap **"Generate AI Combos"**.
3. **What to Observe**:
   - The backend runs a **0/1 Knapsack Constraint Solver**.
   - Meal combinations are produced with complete price transparency:
     - Food Subtotal: ₹110
     - GST (5%): ₹5.50
     - Eco-Delivery: ₹35.00
     - **Grand Total: ₹150.50 $\rightarrow$ rigorously bounded under the specified threshold**.
   - Tap **"Add Combo to Cart"** to immediately transfer the entire combo into your persistent cart.

---

### Feature 3: Sustainable Surplus Food Marketplace ("Save Food, Save Money")
> *"Rescue fresh unsold meals at 40%–65% off, preventing avoidable waste."*

1. **Step**: On the Home screen, scroll to the **"Save Food, Save Money"** carousel or tap **"Save Food"** (`/surplus-marketplace`).
2. **What to Observe**:
   - Live discount badges: `-56% OFF`, `-60% OFF`.
   - Environmental impact badges: `0.8 kg food waste saved`, `2.0 kg CO₂ emissions prevented`.
   - Real-time countdown timer showing minutes remaining before offer deadline.
   - Remaining stock counter (e.g., `4 portions left`).
3. **Action**: Tap **"Rescue Meal"**.
   - An atomic reservation transaction executes on the server.
   - The meal is placed into your cart at the discounted rate and stock is decremented immediately.

---

### Feature 4: Group Ordering & Smart Bill Split
> *"Order with friends, enforce individual budgets, and split delivery transparently."*

1. **Step**: On the Home screen, tap the blue **"Group Split"** button (`/group-order`).
2. **Action**:
   - Tap **"Start New Group Session"** with a target restaurant and ₹1000 group budget.
   - Note the generated 6-digit **Join Code** (e.g., `GRP-8241`).
   - Tap **"Simulate Friend (Aarav) Joining"** to demo multi-user real-time participation.
3. **What to Observe**:
   - Shared cart displays each participant's itemized picks.
   - Automated itemized breakdown shows each participant's exact share:
     - Dish Subtotal + Proportional GST Share + Proportional Delivery Fee.
   - A budget health indicator flags whether the group total and individual shares remain strictly within budget.

---

### Feature 5: Conversational AI Food Assistant
> *"Natural language queries grounded directly in live menu databases."*

1. **Step**: Tap the **"AI Chat"** tab in the bottom navigation bar (`/ai-assistant`).
2. **Action**: Tap one of the suggested query chips or type your own:
   - *"Find vegetarian food under ₹120"*
   - *"Suggest a high-protein meal"*
   - *"Show spicy dishes available near me"*
3. **What to Observe**:
   - The assistant replies in conversational natural language.
   - It attaches live interactive **Dish Cards** with photos, prices, protein counts, and a direct **"Add to Cart"** button.
   - The assistant never invents dummy restaurants or hallucinated prices.

---

## 3. Walkthrough: The 4 Role-Based Management Portals

### Role 1: Customer (Ordering & Tracking)
1. Add items to cart from any restaurant or combo.
2. Open the Cart (`/cart`). Notice server-side calculated totals, item subtotal, GST, and delivery.
3. Tap **"Proceed to Checkout"** (`/checkout`).
4. Apply demo coupon `SAVE50`, choose **Demo UPI**, and tap **"Confirm & Pay"**.
5. You are redirected to **Live Order Tracking** (`/order-tracking/:id`):
   - Interactive 6-stage timeline stepper:
     `Placed` $\rightarrow$ `Accepted` $\rightarrow$ `Preparing` $\rightarrow$ `Ready for Pickup` $\rightarrow$ `Picked Up` $\rightarrow$ `Delivered`.
   - Dynamic estimated preparation and delivery countdown.
   - Option to cancel order (permitted while status is `placed`).

---

### Role 2: Restaurant Owner Dashboard
1. Go to Profile $\rightarrow$ Tap **"Restaurant Owner Dashboard"** (or login via the Restaurant Owner demo button).
2. **What to Observe**:
   - Active orders kitchen tickets with customer address and dish lists.
   - Live status transition buttons: Tap **"Accept Order"**, then **"Start Kitchen Prep"**, then **"Mark Ready for Pickup"**.
   - Analytics tab showing real-time gross revenue, order volume, best-selling dishes, and low-stock alerts calculated from actual database records.

---

### Role 3: Delivery Partner Dashboard
1. Go to Profile $\rightarrow$ Tap **"Delivery Partner Dashboard"** (or login via Rider demo button).
2. **What to Observe**:
   - Assigned delivery tickets with restaurant pickup address and customer drop-off location.
   - Tap **"Accept Job"**.
   - Tap **"Confirm Food Picked Up"** $\rightarrow$ status advances to `picked_up`.
   - Tap **"Complete Delivery"** $\rightarrow$ status advances to `delivered`.
   - Daily earnings counter automatically credits delivery payouts (₹55 per trip).

---

### Role 4: Administrator Dashboard
1. Go to Profile $\rightarrow$ Tap **"Administrator Dashboard"** (or login via Admin demo button).
2. **What to Observe**:
   - **Analytics Tab**: Global Platform GMV, total orders, partner count, and platform-wide food waste prevented (kg).
   - **Users & Roles Tab**: Full registry of users with instant toggle buttons to suspend or activate accounts.
   - **Partners Tab**: Partner restaurant registry with one-tap toggle switches to approve and verify restaurants.
