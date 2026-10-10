# FoodFusion AI — Smart Food Ordering & Sustainable Delivery

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?style=flat&logo=flutter)](https://flutter.dev)
[![Python](https://img.shields.io/badge/Python-3.11%20|%203.14-3776AB?style=flat&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**FoodFusion AI** is an advanced food ordering and sustainable delivery mobile application and backend platform. It combines cutting-edge AI technologies—explainable recommendation engines, knapsack budget optimizers, conversational AI assistants, and surplus food marketplaces—to reduce avoidable food waste, respect user dietary needs, and provide transparent billing.

---

## 🌟 The 5 Differentiating Features

1. **Explainable AI Food Recommendations**: Uses Scikit-Learn TF-IDF vectorization and cosine similarity over menu ingredients, cuisine, and user preferences. Every recommendation includes an explicit human-readable justification (e.g. *"Recommended because you prefer spicy vegetarian food and this fits your ₹300 budget"*).
2. **Smart Budget Meal Planner**: A mathematical 0/1 Knapsack optimizer that solves for high-protein, nutritionally balanced meal combos strictly under a customer's entered ceiling (e.g., ₹150) inclusive of taxes and delivery fees.
3. **Sustainable Surplus Food Marketplace ("Save Food, Save Money")**: A zero-waste marketplace where restaurants list surplus fresh meals at 40%–65% off before shift closing. Tracks environmental impact in kilograms of food saved and CO₂ emissions averted.
4. **Group Ordering & Smart Bill Split**: Real-time collaborative ordering with 6-digit join codes, shared carts, and automated itemized tax and delivery fee split calculation per participant.
5. **Conversational AI Food Assistant**: A natural language assistant grounded in the live menu database. Users can ask questions like *"Find vegetarian food under ₹120"* and receive conversational replies with interactive dish cards ready to add to the cart.

---

## 🎨 Design System & Palette

Crafted to deliver a warm, appetizing, and sustainable brand identity:

- **Warm Cream Background**: `#FDFBF7` — Soft, welcoming, and food-friendly
- **Deep Navy Text**: `#0F172A` — Crisp, professional readability
- **Vibrant Orange Primary**: `#F97316` — Energetic culinary accent
- **Emerald Green**: `#10B981` — Sustainability, vegetarian tags, and zero-waste savings
- **Muted Navy / Subtles**: `#64748B`, `#E2E8F0` — Clean typography hierarchy

---

## 👥 Role-Based Access Control (RBAC)

The system enforces strict permission gates at the backend API layer across four roles:

1. **Customer**: Browse menus, filter dishes, AI recommendations, budget planning, surplus ordering, group orders, persistent cart, and order tracking.
2. **Restaurant Owner**: Manage dishes, menu availability, kitchen order transitions (`placed` $\rightarrow$ `accepted` $\rightarrow$ `preparing` $\rightarrow$ `ready_for_pickup`), list surplus deals, and inspect revenue analytics.
3. **Delivery Partner**: View assigned delivery dispatches, accept routes, advance delivery timeline (`picked_up` $\rightarrow$ `delivered`), and track earnings.
4. **Administrator**: Platform health analytics (GMV, total orders, waste prevented kg), user activation/suspension toggles, and partner restaurant verification.

### Demo Credentials

| Role | Email | Password |
| :--- | :--- | :--- |
| **Customer** | `customer@foodfusion.ai` | `Customer@123` |
| **Restaurant Owner** | `owner@spicevilla.com` | `Owner@123` |
| **Delivery Partner** | `rider@foodfusion.ai` | `Rider@123` |
| **Administrator** | `admin@foodfusion.ai` | `Admin@123` |

---

## 🏗️ Project Architecture

```
foodfusion_ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Modular REST API endpoints (Auth, Restaurants, Orders, etc.)
│   │   ├── core/            # Config, JWT Security, RBAC Guards
│   │   ├── models/          # Normalized SQLAlchemy DB entities
│   │   ├── schemas/         # Pydantic v2 validation models
│   │   └── services/        # AI engines, knapsack solver, seed data, analytics
│   ├── tests/               # Pytest suite with 100% core coverage
│   ├── main.py              # FastAPI application entrypoint
│   └── requirements.txt     # Backend dependencies
│
├── mobile/
│   ├── android/             # Complete Android Gradle & Manifest scaffolding
│   ├── lib/
│   │   ├── app/             # Themes, Typography & GoRouter navigation
│   │   ├── core/            # Network Dio client & reusable UI widgets
│   │   ├── features/        # Feature screens (Auth, Home, Search, Cart, Dashboards, AI)
│   │   ├── models/          # Type-safe Dart entity models
│   │   ├── providers/       # Riverpod state notifiers
│   │   └── main.dart        # Flutter entrypoint
│   ├── test/                # Unit & widget tests
│   └── pubspec.yaml         # Flutter dependencies
│
└── docs/
    ├── ARCHITECTURE.md      # Detailed system diagrams & algorithm formulas
    └── DEMO_SCRIPT.md       # Step-by-step hackathon live presentation guide
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.11+** (Python 3.14 compatible)
- **Flutter 3.x & Dart 3.x**
- **Android SDK** (for APK generation)

### 2. Backend Setup & Run

```bash
cd backend

# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the FastAPI server (auto-seeds database on startup)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- API Docs (Swagger): `http://localhost:8000/docs`
- Redoc Documentation: `http://localhost:8000/redoc`

### 3. Run Backend Test Suite

```bash
cd backend
pytest tests/test_backend.py -v
```
*(All 9/9 integration & unit tests pass, covering authentication, role-based access, knapsack budget calculations, TF-IDF AI recommendations, and checkout).*

### 4. Mobile App Setup & Compilation

```bash
cd mobile

# 1. Fetch dependencies
flutter pub get

# 2. Run mobile unit & widget tests
flutter test

# 3. Run on connected Android device / emulator
flutter run

# 4. Build release Android APK
flutter build apk --release
```
The compiled APK will be output to `mobile/build/app/outputs/flutter-apk/app-release.apk`.

---

## 🔒 Security & Data Integrity Highlights

- **Server-Side Price Calculation**: Grand totals, delivery fees, taxes, and coupon discounts are recalculate exclusively on the server. Client-submitted prices are rejected.
- **Atomic Surplus Stock Controls**: Inventory decrements use atomic database locks, preventing overselling past available quantity.
- **Secure Password Hashing**: Utilizes industry-standard bcrypt with salted rounds and signed JWT Bearer authentication tokens.
- **Role Permission Enforcement**: Every administrative and partner endpoint validates user claims via FastAPI dependency injection guards before processing requests.
