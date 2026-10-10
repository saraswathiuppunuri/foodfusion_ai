# Online Food Ordering System — Powered by AI

A next-generation, AI-driven food ordering platform that transforms standard menu browsing into an intelligent, constraint-aware, and socially collaborative experience. The system optimizes individual & group orders, recommends affordable and nutritious meals, slashes restaurant food waste, and introduces a unique **Fridge-to-Plate Vision AI with "Cook at Home vs. Order Delivery" comparison**.

---

## 🌟 The 5 Core Features + Unique Innovation Twist

### 1. ⚡ AI Natural-Language Ordering & Explainable Cart Builder
* **User Input:** *“I need dinner for three people under ₹500, two vegetarian meals and one spicy meal.”*
* **AI Mechanism:** Multi-constraint natural language parser + Knapsack constraint satisfaction solver.
* **Output:** Automatically selects dishes matching budget and dietary constraints from single or coordinated restaurants, minimizing extra delivery fees and explaining the exact reasoning behind the choices.

### 2. 🌱 Smart Surplus Food Marketplace (Zero-Waste Engine)
* **Goal:** Eradicate avoidable restaurant food waste while helping consumers access affordable meals.
* **Mechanism:** Restaurants list fresh end-of-batch surplus dishes 60–90 minutes before closing at **40–65% off**.
* **Impact Tracking:** Live environmental analytics calculating kilograms of food rescued and grams of $CO_2$ prevented.

### 3. 👥 AI Group Order Optimizer & Fair-Split Calculator
* **Goal:** Eliminate group chat debates and awkward manual math when friends or colleagues order together.
* **Mechanism:** Friends input individual budgets, dietary constraints (veg, non-veg), and spice preferences. The AI generates a Pareto-optimal shared order and calculates the **exact itemized bill share** per person (including fair-split GST and delivery).

### 4. 🎯 Explainable Food Recommendations (Scikit-Learn TF-IDF)
* **Goal:** Personalized discovery with 100% transparent reasoning.
* **Mechanism:** Uses `scikit-learn`'s `TfidfVectorizer` and `cosine_similarity` to analyze dish flavor vectors, calories, protein macros, and user order history.
* **Explainability:** Transparent reasons provided for each recommendation (e.g., *"74% match because this dish stays under your target budget (₹210 vs ₹400), matches previous 5★ orders, and delivers 36g protein"*).

### 5. 📊 Predictive Order Management & Kitchen Analytics Dashboard
* **Goal:** Accurate delivery estimates, proactive bottleneck alerts, and partner kitchen analytics.
* **Mechanism:** Predictive models estimate prep time ($T_{prep}$) based on dish complexity, station queue lengths, and rush-hour volume. Flagging rules alert kitchens to impending delays before they affect customers.
* **Visualization:** Modern interactive **Chart.js** dashboard featuring hourly peak trends, waste reduction, recovered surplus revenue, and punctuality rates.

### 🍳 Unique Twist: "Fridge-to-Plate Vision AI" (Cook at Home vs. Order Delivery)
* **Goal:** Help users decide between home cooking and ordering out based on current pantry ingredients.
* **Mechanism:** Users take/upload a photo of their refrigerator or pantry. OpenCV Computer Vision identifies ingredients (e.g. tomatoes, paneer, capsicum, eggs).
* **Side-by-Side Comparison:**
  * **Cook at Home:** Required prep & cooking time (38 mins), missing ingredients to buy (₹75), dishwashing & clean-up time (25 mins / 3 pans).
  * **Order Delivery:** Fast kitchen prep & transit (32 mins to doorstep), delivered price (₹185), zero pots/cleaning effort, 4.6★ chef quality.
  * **AI Verdict:** Calculates exact time saved vs. financial difference to make an informed recommendation!

---

## 🎨 Attractive Left Sidebar UI

The user interface features a dedicated, responsive **Left Sidebar Navigation**:
* **Brand Identity & AI Core Pulse:** Glowing pulse indicator verifying active AI recommendation engine status.
* **Navigation Links with Badges:** 1-click access to all 5 features + unique twist + live tracking.
* **Live Sidebar Eco-Impact Widget:** Shows food rescued ($kg$) and $CO_2$ prevented ($kg$).
* **Daily Budget Compass:** Visual progress bar tracking spending vs. daily meal allowance (e.g., ₹240 / ₹500 remaining).
* **Active Kitchen Order Tracker:** Displays cooking status, live progress dots, and 14-minute countdown for in-flight orders.
* **User Profile & Preferences:** Quick modal to retrain Scikit-learn dietary and budget models.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3.3, FontAwesome 6 |
| **Backend** | Python 3 + Flask |
| **Database** | MySQL (with seamless automatic fallback to local SQLite `hackathon.db`) |
| **Machine Learning / AI** | Python, `scikit-learn` (TF-IDF & Cosine Similarity) |
| **Computer Vision** | `opencv-python` (OpenCV), `Pillow` (PIL) |
| **Maps & Location** | OpenStreetMap + Leaflet.js (Live route polyline & animated rider GPS) |
| **Charts & Analytics** | Chart.js 4.4+ |
| **Version Control** | Git & GitHub |

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.10+ installed
* Pip package manager

### 2. Installation
Clone or open this repository, then install the dependencies:
```bash
pip install -r requirements.txt
```

### 3. Database Configuration (MySQL or SQLite)
* **Instant Out-of-the-Box (SQLite):** Simply launch the application. If MySQL is not detected, the system automatically initializes `hackathon.db` with sample restaurants, dishes, surplus flash deals, and mock orders.
* **To use MySQL Server:**
  1. Create the MySQL database and tables:
     ```bash
     mysql -u root -p < schema.sql
     ```
  2. Set environment variables (optional, defaults to `root` on `localhost:3306`):
     ```bash
     export MYSQL_USER="root"
     export MYSQL_PASSWORD="your_password"
     export MYSQL_DB="food_ordering_ai"
     ```

### 4. Running the Application
Start the Flask web server:
```bash
python app.py
```
Open your browser and navigate to:
```
http://127.0.0.1:5000
```

### 5. Running the Automated Test Suite
Verify all 6 web pages and 6 AI API endpoints:
```bash
python test_app.py
```

---

## 📂 Project Architecture

```
hackathon/
├── app.py                     # Main Flask application and REST API controllers
├── config.py                  # MySQL & SQLite database configuration
├── database.py                # SQLAlchemy ORM models and automatic seed logic
├── schema.sql                 # Complete MySQL DDL schema and seed data
├── requirements.txt           # Python backend & AI package dependencies
├── test_app.py                # Automated end-to-end test suite
├── ai_engine/
│   ├── __init__.py
│   ├── nl_parser.py           # Feature 1: Natural-Language Cart Builder & Knapsack Solver
│   ├── group_optimizer.py     # Feature 3: Multi-person Group Consensus & Fair Bill Split
│   ├── recommender.py         # Feature 4: Scikit-learn TF-IDF & Cosine Similarity
│   ├── predictive_kitchen.py  # Feature 5: Prep & delivery time estimation & delay flags
│   └── vision_fridge.py       # Twist: OpenCV Fridge Ingredient Recognition & Cook vs Order
├── static/
│   ├── css/
│   │   └── style.css          # Theme styling, animations, and attractive left sidebar
│   ├── js/
│   │   └── main.js            # Sidebar drawer, cart state, checkout, and AI prompts
│   └── uploads/               # Upload directory for fridge vision photos
└── templates/
    ├── base.html              # Base layout with Attractive Left Sidebar & Modals
    ├── index.html             # Main dashboard (Feature 1 NL order hero & full catalog)
    ├── surplus.html           # Feature 2: Dedicated Zero-Waste Surplus Marketplace
    ├── group.html             # Feature 3: Dedicated Group Order Optimizer & Split Room
    ├── fridge.html            # Unique Twist: Fridge Vision & Cook vs. Order Battle
    ├── analytics.html         # Feature 5: Predictive Kitchen & Chart.js Dashboard
    └── map_view.html          # Maps: OpenStreetMap Leaflet delivery route & animated rider
```

---

## 🏆 Hackathon Demo Script (How to Present)

1. **Start on Home (`/`):** Point to the **Attractive Left Sidebar** with the live AI pulse, Eco-Impact counter (18.5 kg food saved), and daily budget tracker.
2. **Demonstrate Feature 1:** Click the preset chip: *“Dinner for 3 under ₹500, 2 veg, 1 spicy”*. Watch the AI instantly parse the constraints, display the solution, explain its choices, and populate the cart.
3. **Demonstrate Feature 2:** Navigate to **Surplus Food Rescue (`/surplus`)**. Show how restaurants list end-of-batch items at 60% off to prevent waste. Click *"List Restaurant Surplus"* to show the partner portal.
4. **Demonstrate Feature 3:** Go to **Group Order Optimizer (`/group`)**. Show 3 friends with different budgets and dietary preferences. Click *"Run AI Group Optimization"* to generate the fair bill breakdown with shared delivery/tax splits.
5. **Demonstrate Unique Twist:** Open **Fridge Vision AI (`/fridge`)**. Click *"Sample: Tomatoes & Paneer"*. Point out the OpenCV ingredient confidence scores and the side-by-side **Cook at Home (63 mins, 3 dirty pots, ₹95) vs. Order Delivery (32 mins, zero pots, ₹185)** comparison.
6. **Demonstrate Feature 5:** Open **Predictive Analytics (`/analytics`)**. Showcase the Chart.js visual charts (Rush hours, Food rescued vs. discarded, Revenue recovered, and Delay flags).
7. **Demonstrate Maps (`/map`):** Open **Live Map & ETA**. Show OpenStreetMap with the animated delivery rider navigating from Spice Villa to the customer doorstep.
