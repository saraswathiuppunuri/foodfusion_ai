# FoodFusion AI — Architecture Specification & Engineering Design

This document details the software architecture, data models, AI recommendation pipelines, optimization algorithms, and security paradigms powering **FoodFusion AI — Smart Food Ordering & Sustainable Delivery**.

---

## 1. System Architecture Overview

FoodFusion AI is architected as an end-to-end decoupled system comprising a high-performance **Flutter** mobile client (Dart 3.x), a robust **FastAPI** backend (Python 3.14+), an **Explainable Scikit-Learn AI Engine**, a **Constraint-Based Knapsack Optimizer**, and a relational database (SQLite for local demo, with SQLAlchemy ORM abstraction enabling instant migration to PostgreSQL).

```mermaid
flowchart TD
    subgraph Client["Flutter Mobile Client (Android / Cross-Platform)"]
        UI["Material 3 UI (Warm Cream / Navy / Orange)"]
        Nav["GoRouter (StatefulShellRoute + Nested Stacks)"]
        State["Riverpod 2.x State Management"]
        DioClient["Dio HTTP Client (Auto JWT Interceptors)"]
        UI --> Nav
        Nav --> State
        State --> DioClient
    end

    subgraph Gateway["FastAPI REST API Gateway"]
        AuthMid["JWT Auth Middleware & Security Guards"]
        RBAC["Role-Based Access Control (4 Roles)"]
        Router["V1 API Endpoints"]
        AuthMid --> RBAC
        RBAC --> Router
    end

    subgraph AI["AI & Optimization Engines"]
        RecEngine["Explainable TF-IDF & Cosine Similarity Engine"]
        Knapsack["0/1 Dynamic Knapsack Budget Meal Optimizer"]
        ChatNLP["Intent & Slot-Extraction Natural Language Grounding"]
    end

    subgraph DataLayer["Persistence & Database Layer"]
        ORM["SQLAlchemy ORM Models"]
        DB[(SQLite / PostgreSQL Engine)]
        ORM --> DB
    end

    DioClient -- REST Requests (Bearer Token) --> AuthMid
    Router --> RecEngine
    Router --> Knapsack
    Router --> ChatNLP
    Router --> ORM
    RecEngine --> ORM
    Knapsack --> ORM
    ChatNLP --> ORM
```

---

## 2. Entity-Relationship Data Model

The schema uses foreign key constraints, normalized structures, and status audit timelines.

```mermaid
erDiagram
    USER ||--o{ RESTAURANT : "owns"
    USER ||--o{ ORDER : "places"
    USER ||--o{ CART : "possesses"
    USER ||--o{ REVIEW : "writes"
    USER ||--o{ FAVORITE : "bookmarks"
    USER ||--o{ DELIVERY_ASSIGNMENT : "handles"
    USER ||--o{ GROUP_ORDER_PARTICIPANT : "participates"

    RESTAURANT ||--o{ DISH : "serves"
    RESTAURANT ||--o{ ORDER : "fulfills"
    RESTAURANT ||--o{ SURPLUS_OFFER : "publishes"

    CATEGORY ||--o{ DISH : "categorizes"

    CART ||--o{ CART_ITEM : "contains"
    DISH ||--o{ CART_ITEM : "referenced_in"

    ORDER ||--o{ ORDER_ITEM : "comprises"
    ORDER ||--o{ ORDER_TIMELINE : "audits"
    ORDER ||--o| DELIVERY_ASSIGNMENT : "assigned_to"
    DISH ||--o{ ORDER_ITEM : "ordered_as"

    GROUP_ORDER_SESSION ||--o{ GROUP_ORDER_PARTICIPANT : "includes"
    GROUP_ORDER_PARTICIPANT ||--o{ GROUP_ORDER_ITEM : "adds"

    USER {
        int id PK
        string email UK
        string hashed_password
        string role "customer | restaurant_owner | delivery_partner | admin"
        string dietary_preference
        string spice_preference
        float avg_budget
        bool is_active
    }

    RESTAURANT {
        int id PK
        int owner_id FK
        string name
        string cuisine
        float rating
        int avg_prep_time_min
        string address
        bool is_verified
    }

    DISH {
        int id PK
        int restaurant_id FK
        string name
        float price
        bool is_veg
        string spice_level
        int calories
        int protein_g
        int prep_time_min
        bool is_available
        int stock_count
    }

    SURPLUS_OFFER {
        int id PK
        int restaurant_id FK
        int dish_id FK
        float original_price
        float discounted_price
        int discount_percentage
        int quantity_available
        float waste_saved_kg
        float co2_saved_kg
        datetime offer_expires_at
    }

    ORDER {
        int id PK
        int customer_id FK
        int restaurant_id FK
        string status "placed | accepted | preparing | ready_for_pickup | picked_up | delivered"
        float item_subtotal
        float delivery_fee
        float tax_gst
        float discount_amount
        float grand_total
        string payment_method
        string payment_status
    }
```

---

## 3. Order Lifecycle & Status State Machine

Orders follow a strict linear progression with verification at each role boundary.

```mermaid
stateDiagram-v2
    [*] --> Placed : Customer Checkout (Server Recalculates Totals)
    Placed --> Accepted : Restaurant Owner Accepts Kitchen Ticket
    Placed --> Cancelled : Customer Cancels (Only while Placed)
    Placed --> Rejected : Restaurant Rejects / Out of Stock
    Accepted --> Preparing : Kitchen Starts Preparation
    Preparing --> ReadyForPickup : Food Cooked & Packaged
    ReadyForPickup --> PickedUp : Delivery Partner Verifies & Collects
    PickedUp --> Delivered : Delivered at Customer Location
    Delivered --> [*]
    Cancelled --> [*]
    Rejected --> [*]
```

---

## 4. AI & Optimization Algorithms

### A. Explainable Hybrid Recommendation Engine
Located in `app/services/recommendation_service.py`.

1. **Content Representation**:
   Each dish document $D_i$ is synthesized as a feature text containing:
   $$\text{Text}(D_i) = \text{Cuisine} + \text{DishName} + \text{Ingredients} + \text{DietaryTag} + \text{SpiceLevel}$$
2. **TF-IDF Vectorization**:
   Computes word importance weights across the active menu corpus:
   $$\text{TF-IDF}(t, d, D) = \text{TF}(t, d) \times \log \left( \frac{1 + |D|}{1 + \text{DF}(t, D)} \right) + 1$$
3. **Scoring Function**:
   Given user profile vector $U$ and dietary filter constraints:
   $$\text{Score}(D_i, U) = 0.45 \cdot \text{CosineSimilarity}(\vec{D}_i, \vec{U}) + 0.25 \cdot \text{DietaryMatch} + 0.15 \cdot \text{SpiceMatch} + 0.15 \cdot \text{RatingNormalized}$$
4. **Transparent Explainability**:
   Instead of black-box outputs, each suggestion emits a human-readable badge:
   `"Recommended because you prefer spicy vegetarian food and this meal fits your ₹300 budget."`

---

### B. Smart 0/1 Knapsack Budget Meal Optimizer
Located in `app/services/budget_planner_service.py`.

- **Strict Constraint**: $\text{GrandTotal}(\text{Items}) = \sum \text{Price} + \text{GST}(5\%) + \text{EcoDeliveryFee}(₹35) \le \text{MaxBudget}$
- Guaranteed mathematical bound: If a user enters ₹150, the algorithm solves for the most satisfying combination (maximizing protein, calorie balance, and rating) whose combined cost including all taxes and fees does **not exceed ₹150**.
- If no combination exists, it provides exact reasons and the lowest feasible budget threshold.

---

### C. Conversational AI Natural Language Assistant
Located in `app/services/ai_assistant_service.py`.

- Extracts user intents: `high_protein`, `budget_bound`, `spice_filter`, `diet_filter`, `surplus_deals`, `similar_last_order`.
- Queries the live menu database without hallucinating non-existent restaurants or prices.
- Returns structured JSON cards containing live dish models that users can add directly to their cart in 1 tap.

---

### D. Sustainable Surplus Food Marketplace
Located in `app/services/surplus_service.py`.

- Restaurants list surplus inventory near closing or shift change at 40%–65% discount.
- Enforces real-time stock decrements with atomic database transactions.
- Calculates and displays environmental impact:
  $$\text{CO}_2\text{ Saved (kg)} = \text{WasteSaved (kg)} \times 2.5$$
- Offers expire automatically based on deadline timestamps, preventing unsafe food claims.

---

## 5. Security & Role-Based Access Control (RBAC)

| User Role | Accessible Endpoints | Permission Enforcement |
| :--- | :--- | :--- |
| **Customer** | `/cart/*`, `/orders/checkout`, `/recommendations`, `/budget-planner`, `/surplus`, `/group-orders/*`, `/ai-assistant/chat` | Checked via JWT bearer token |
| **Restaurant Owner** | `/restaurant/orders`, `/restaurant/orders/{id}/status`, `/restaurant/menu/*`, `/restaurant/surplus`, `/restaurant/analytics` | Blocked if role $\ne$ `restaurant_owner` |
| **Delivery Partner**| `/delivery/assignments`, `/delivery/assignments/{id}/accept`, `/delivery/assignments/{id}/status`, `/delivery/earnings` | Blocked if role $\ne$ `delivery_partner` |
| **Administrator** | `/admin/users`, `/admin/users/{id}/status`, `/admin/restaurants`, `/admin/restaurants/{id}/verify`, `/admin/analytics` | Blocked if role $\ne$ `admin` |

- Passwords hashed using standard **bcrypt**.
- Prices and billing totals are strictly calculated and validated on the backend. Client-submitted prices are discarded.
