import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.config import settings
from app.database import engine, Base, SessionLocal
from app.services.seed_data import seed_database

# Explicitly ensure tables and seeds exist for test runner
Base.metadata.create_all(bind=engine)
db = SessionLocal()
seed_database(db)
db.close()

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_login_and_roles():
    # Customer login
    res_customer = client.post("/api/v1/auth/login", json={
        "email": settings.CUSTOMER_EMAIL,
        "password": settings.CUSTOMER_PASSWORD
    })
    assert res_customer.status_code == 200
    data = res_customer.json()
    assert "access_token" in data
    assert data["role"] == "customer"

    # Restaurant owner login
    res_owner = client.post("/api/v1/auth/login", json={
        "email": settings.RESTAURANT_EMAIL,
        "password": settings.RESTAURANT_PASSWORD
    })
    assert res_owner.status_code == 200
    assert res_owner.json()["role"] == "restaurant_owner"

def test_restaurants_and_menu():
    res = client.get("/api/v1/restaurants")
    assert res.status_code == 200
    restaurants = res.json()
    assert len(restaurants) >= 3
    assert restaurants[0]["name"] is not None

def test_budget_planner():
    # Budget Planner under ₹150
    res = client.post("/api/v1/budget-planner", json={
        "max_budget": 150.0,
        "people_count": 1,
        "is_veg_only": False
    })
    assert res.status_code == 200
    data = res.json()
    assert "combos" in data
    assert len(data["combos"]) > 0
    # Verify no combo exceeds entered budget
    for combo in data["combos"]:
        assert combo["grand_total"] <= 150.0

def test_explainable_recommendations():
    # Login as customer
    login_res = client.post("/api/v1/auth/login", json={
        "email": settings.CUSTOMER_EMAIL,
        "password": settings.CUSTOMER_PASSWORD
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    rec_res = client.get("/api/v1/recommendations", headers=headers)
    assert rec_res.status_code == 200
    recs = rec_res.json()
    assert len(recs) > 0
    assert "explanation" in recs[0]
    assert "match_score" in recs[0]

def test_surplus_marketplace():
    res = client.get("/api/v1/surplus")
    assert res.status_code == 200
    deals = res.json()
    assert len(deals) > 0
    first_deal = deals[0]
    assert first_deal["discount_percentage"] > 0
    assert first_deal["waste_saved_kg"] > 0

def test_conversational_ai_assistant():
    login_res = client.post("/api/v1/auth/login", json={
        "email": settings.CUSTOMER_EMAIL,
        "password": settings.CUSTOMER_PASSWORD
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    chat_res = client.post("/api/v1/ai-assistant/chat", headers=headers, json={
        "message": "Find high-protein meals"
    })
    assert chat_res.status_code == 200
    data = chat_res.json()
    assert "reply" in data
    assert len(data["suggested_dishes"]) > 0

def test_cart_and_checkout_flow():
    # Login
    login_res = client.post("/api/v1/auth/login", json={
        "email": settings.CUSTOMER_EMAIL,
        "password": settings.CUSTOMER_PASSWORD
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Clear cart first
    client.delete("/api/v1/cart", headers=headers)

    # Get a dish
    dishes = client.get("/api/v1/dishes").json()
    dish = dishes[0]

    # Add to cart
    add_res = client.post("/api/v1/cart/items", headers=headers, json={
        "dish_id": dish["id"],
        "quantity": 2
    })
    assert add_res.status_code == 200
    cart_data = add_res.json()
    assert cart_data["item_subtotal"] == dish["price"] * 2

    # Checkout
    order_res = client.post("/api/v1/orders/checkout", headers=headers, json={
        "delivery_address": "Test Flat 101, Bengaluru",
        "payment_method": "demo_upi",
        "coupon_code": "SAVE50"
    })
    assert order_res.status_code == 200
    order_data = order_res.json()
    assert order_data["status"] == "placed"
    assert order_data["grand_total"] > 0
    assert len(order_data["timeline"]) > 0

def test_rbac_security_enforcement():
    # Customer trying to access owner endpoints must get 403 Forbidden
    login_res = client.post("/api/v1/auth/login", json={
        "email": settings.CUSTOMER_EMAIL,
        "password": settings.CUSTOMER_PASSWORD
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    forbidden_res = client.get("/api/v1/restaurant-owner/orders", headers=headers)
    assert forbidden_res.status_code == 403
