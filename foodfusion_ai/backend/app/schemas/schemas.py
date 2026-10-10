from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

# -------------------------------------------------------------
# AUTH & USER SCHEMAS
# -------------------------------------------------------------
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    role: str = "customer" # customer, restaurant_owner, delivery_partner, admin
    phone: Optional[str] = None
    dietary_preference: Optional[str] = "none"
    spice_preference: Optional[str] = "medium"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    user_id: int
    name: str

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    dietary_preference: Optional[str] = None
    spice_preference: Optional[str] = None
    preferred_cuisines: Optional[str] = None
    avg_budget: Optional[float] = None

class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    phone: Optional[str] = None
    dietary_preference: str
    spice_preference: str
    preferred_cuisines: Optional[str] = None
    avg_budget: float
    is_active: bool

    class Config:
        from_attributes = True

# -------------------------------------------------------------
# RESTAURANT & DISH SCHEMAS
# -------------------------------------------------------------
class CategoryOut(BaseModel):
    id: int
    name: str
    icon_name: str
    image_url: Optional[str] = None

    class Config:
        from_attributes = True

class DishOut(BaseModel):
    id: int
    restaurant_id: int
    category_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float
    is_veg: bool
    spice_level: str
    calories: int
    protein_g: int
    prep_time_min: int
    image_url: Optional[str] = None
    tags: Optional[str] = None
    ingredients: Optional[str] = None
    allergens: Optional[str] = None
    is_available: bool
    stock_count: int

    class Config:
        from_attributes = True

class DishCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    is_veg: bool = True
    spice_level: str = "medium"
    category_id: Optional[int] = None
    calories: int = 350
    protein_g: int = 15
    prep_time_min: int = 15
    image_url: Optional[str] = None
    tags: Optional[str] = None
    ingredients: Optional[str] = None
    allergens: Optional[str] = "None declared"
    stock_count: int = 50

class RestaurantOut(BaseModel):
    id: int
    owner_id: int
    name: str
    description: Optional[str] = None
    cuisine: str
    rating: float
    review_count: int
    avg_prep_time_min: int
    address: str
    latitude: float
    longitude: float
    phone: Optional[str] = None
    image_url: Optional[str] = None
    is_verified: bool
    is_active: bool
    dishes: Optional[List[DishOut]] = []

    class Config:
        from_attributes = True

# -------------------------------------------------------------
# CART SCHEMAS
# -------------------------------------------------------------
class CartItemAdd(BaseModel):
    dish_id: int
    quantity: int = 1
    customization_notes: Optional[str] = ""

class CartItemOut(BaseModel):
    id: int
    dish_id: int
    dish_name: str
    unit_price: float
    quantity: int
    subtotal: float
    is_veg: bool
    image_url: Optional[str] = None

class CartOut(BaseModel):
    id: int
    restaurant_id: Optional[int] = None
    restaurant_name: Optional[str] = None
    items: List[CartItemOut] = []
    item_subtotal: float = 0.0
    delivery_fee: float = 40.0
    tax_gst: float = 0.0
    grand_total: float = 0.0

# -------------------------------------------------------------
# CHECKOUT & ORDER SCHEMAS
# -------------------------------------------------------------
class CheckoutRequest(BaseModel):
    delivery_address: str
    delivery_instructions: Optional[str] = ""
    coupon_code: Optional[str] = None
    payment_method: str = "demo_upi" # demo_upi, demo_card, cash_on_delivery

class OrderTimelineOut(BaseModel):
    status: str
    message: str
    timestamp: datetime

    class Config:
        from_attributes = True

class OrderItemOut(BaseModel):
    id: int
    dish_id: int
    dish_name: str
    unit_price: float
    quantity: int
    subtotal: float

    class Config:
        from_attributes = True

class OrderOut(BaseModel):
    id: int
    restaurant_id: int
    restaurant_name: Optional[str] = None
    order_type: str
    status: str
    item_subtotal: float
    delivery_fee: float
    tax_gst: float
    discount_amount: float
    grand_total: float
    delivery_address: str
    delivery_instructions: Optional[str] = None
    payment_method: str
    payment_status: str
    estimated_prep_min: int
    estimated_delivery_min: int
    total_eta_min: int
    created_at: datetime
    items: List[OrderItemOut] = []
    timeline: List[OrderTimelineOut] = []

    class Config:
        from_attributes = True

class OrderStatusUpdate(BaseModel):
    status: str # accepted, preparing, ready_for_pickup, picked_up, delivered, cancelled, rejected
    reason: Optional[str] = None

# -------------------------------------------------------------
# ADVANCED FEATURE SCHEMAS
# -------------------------------------------------------------
# Feature A: Explainable Recommendations
class RecommendationOut(BaseModel):
    dish: DishOut
    restaurant_name: str
    match_score: int
    explanation: str

# Feature B: Budget Planner
class BudgetPlannerRequest(BaseModel):
    max_budget: float = Field(gt=0, description="Target budget in INR")
    people_count: int = 1
    is_veg_only: bool = False
    spice_preference: Optional[str] = None # mild, medium, spicy

class BudgetPlannerCombo(BaseModel):
    items: List[DishOut]
    item_subtotal: float
    estimated_tax: float
    estimated_delivery: float
    grand_total: float
    remaining_budget: float
    restaurant_name: str
    reason: str

class BudgetPlannerResponse(BaseModel):
    status: str
    max_budget: float
    combos: List[BudgetPlannerCombo]
    message: str

# Feature C: Surplus Food Marketplace
class SurplusOfferOut(BaseModel):
    id: int
    restaurant_id: int
    restaurant_name: str
    restaurant_address: str
    dish_id: int
    dish_name: str
    dish_image_url: Optional[str] = None
    is_veg: bool
    original_price: float
    discounted_price: float
    discount_percentage: int
    quantity_available: int
    waste_saved_kg: float
    co2_saved_kg: float
    offer_expires_at: datetime
    remaining_minutes: int
    status: str

    class Config:
        from_attributes = True

class SurplusOfferCreate(BaseModel):
    dish_id: int
    discounted_price: float
    quantity_available: int
    expiry_hours: float = 2.0

# Feature D: Group Orders
class GroupOrderCreate(BaseModel):
    restaurant_id: int
    total_budget: float = 1000.0

class GroupOrderJoin(BaseModel):
    join_code: str
    user_name: str
    personal_budget: float = 250.0
    diet_pref: str = "any"

class GroupOrderItemAdd(BaseModel):
    dish_id: int
    quantity: int = 1

class GroupParticipantShare(BaseModel):
    participant_name: str
    items: List[Dict[str, Any]]
    food_subtotal: float
    tax_share: float
    delivery_share: float
    final_share: float
    personal_budget: float
    is_within_budget: bool

class GroupOrderOut(BaseModel):
    session_id: int
    join_code: str
    restaurant_name: str
    status: str
    total_budget: float
    combined_grand_total: float
    combined_food_total: float
    total_tax: float
    total_delivery: float
    participants: List[GroupParticipantShare]
    is_group_within_budget: bool
    summary: str

# Feature E: AI Conversational Assistant
class ChatMessage(BaseModel):
    role: str # user, assistant
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    reply: str
    suggested_dishes: List[DishOut] = []
    quick_actions: List[str] = []

# Dashboards & Analytics
class RestaurantAnalyticsOut(BaseModel):
    total_orders: int
    total_revenue: float
    surplus_saved_kg: float
    surplus_revenue: float
    avg_rating: float
    best_selling_dishes: List[Dict[str, Any]]
    low_stock_dishes: List[Dict[str, Any]]
    order_status_distribution: Dict[str, int]
    hourly_trends: Dict[str, int]

class PlatformAnalyticsOut(BaseModel):
    total_users: int
    total_restaurants: int
    total_orders: int
    gross_merchandise_value: float
    total_food_waste_prevented_kg: float
    active_surplus_deals: int
    active_deliveries: int
