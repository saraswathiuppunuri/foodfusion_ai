import enum
import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship
from app.database import Base

class UserRole(str, enum.Enum):
    CUSTOMER = "customer"
    RESTAURANT_OWNER = "restaurant_owner"
    DELIVERY_PARTNER = "delivery_partner"
    ADMIN = "admin"

class OrderStatus(str, enum.Enum):
    PLACED = "placed"
    ACCEPTED = "accepted"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKED_UP = "picked_up"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), default=UserRole.CUSTOMER.value, index=True, nullable=False)
    phone = Column(String(30))
    dietary_preference = Column(String(50), default="none") # none, vegetarian, vegan, halal
    spice_preference = Column(String(30), default="medium") # mild, medium, spicy
    preferred_cuisines = Column(String(255), default="North Indian, Biryani, Asian")
    avg_budget = Column(Float, default=300.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    restaurants = relationship("Restaurant", back_populates="owner")
    orders = relationship("Order", back_populates="customer")
    cart = relationship("Cart", back_populates="user", uselist=False)

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    icon_name = Column(String(50), default="restaurant")
    image_url = Column(String(255))

    dishes = relationship("Dish", back_populates="category")

class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    cuisine = Column(String(100), nullable=False)
    rating = Column(Float, default=4.5)
    review_count = Column(Integer, default=120)
    avg_prep_time_min = Column(Integer, default=20)
    address = Column(String(255), nullable=False)
    latitude = Column(Float, default=12.9716)
    longitude = Column(Float, default=77.6412)
    phone = Column(String(30))
    image_url = Column(String(255))
    is_verified = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="restaurants")
    dishes = relationship("Dish", back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="restaurant")
    surplus_offers = relationship("SurplusOffer", back_populates="restaurant", cascade="all, delete-orphan")

class Dish(Base):
    __tablename__ = "dishes"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    is_veg = Column(Boolean, default=True)
    spice_level = Column(String(20), default="medium") # mild, medium, spicy
    calories = Column(Integer, default=350)
    protein_g = Column(Integer, default=14)
    prep_time_min = Column(Integer, default=15)
    image_url = Column(String(255))
    tags = Column(String(255)) # For TF-IDF Scikit-Learn
    ingredients = Column(Text) # Comma-separated
    allergens = Column(String(255), default="None declared")
    is_available = Column(Boolean, default=True)
    stock_count = Column(Integer, default=50)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="dishes")
    category = relationship("Category", back_populates="dishes")
    surplus_offer = relationship("SurplusOffer", back_populates="dish", uselist=False)

class Cart(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("User", back_populates="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True, index=True)
    cart_id = Column(Integer, ForeignKey("carts.id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    customization_notes = Column(String(255), default="")

    cart = relationship("Cart", back_populates="items")
    dish = relationship("Dish")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    order_type = Column(String(30), default="regular") # regular, surplus, group, ai_smart
    status = Column(String(30), default=OrderStatus.PLACED.value, index=True, nullable=False)
    item_subtotal = Column(Float, nullable=False)
    delivery_fee = Column(Float, default=40.0)
    tax_gst = Column(Float, default=15.0)
    discount_amount = Column(Float, default=0.0)
    grand_total = Column(Float, nullable=False)
    delivery_address = Column(String(255), nullable=False)
    delivery_instructions = Column(String(255), default="")
    payment_method = Column(String(50), default="demo_upi") # demo_upi, demo_card, cash_on_delivery
    payment_status = Column(String(30), default="paid") # paid, pending
    estimated_prep_min = Column(Integer, default=20)
    estimated_delivery_min = Column(Integer, default=15)
    cancellation_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    customer = relationship("User", back_populates="orders")
    restaurant = relationship("Restaurant", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    timeline = relationship("OrderTimeline", back_populates="order", cascade="all, delete-orphan")
    delivery_assignment = relationship("DeliveryAssignment", back_populates="order", uselist=False)

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    dish_name = Column(String(150), nullable=False)
    unit_price = Column(Float, nullable=False)
    quantity = Column(Integer, default=1)
    subtotal = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    dish = relationship("Dish")

class OrderTimeline(Base):
    __tablename__ = "order_timelines"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    status = Column(String(30), nullable=False)
    message = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    order = relationship("Order", back_populates="timeline")

class SurplusOffer(Base):
    __tablename__ = "surplus_offers"
    id = Column(Integer, primary_key=True, index=True)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    original_price = Column(Float, nullable=False)
    discounted_price = Column(Float, nullable=False)
    quantity_available = Column(Integer, nullable=False)
    waste_saved_kg = Column(Float, default=0.5)
    co2_saved_kg = Column(Float, default=1.2)
    offer_expires_at = Column(DateTime, nullable=False)
    status = Column(String(20), default="active") # active, sold_out, expired
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="surplus_offers")
    dish = relationship("Dish", back_populates="surplus_offer")

class GroupOrderSession(Base):
    __tablename__ = "group_order_sessions"
    id = Column(Integer, primary_key=True, index=True)
    join_code = Column(String(20), unique=True, index=True, nullable=False)
    host_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    status = Column(String(30), default="open") # open, locked, placed
    total_budget = Column(Float, default=1000.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    host = relationship("User")
    restaurant = relationship("Restaurant")
    participants = relationship("GroupOrderParticipant", back_populates="session", cascade="all, delete-orphan")

class GroupOrderParticipant(Base):
    __tablename__ = "group_order_participants"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("group_order_sessions.id"), nullable=False)
    user_name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    personal_budget = Column(Float, default=250.0)
    diet_pref = Column(String(50), default="any")
    spice_pref = Column(String(30), default="medium")

    session = relationship("GroupOrderSession", back_populates="participants")
    items = relationship("GroupOrderItem", back_populates="participant", cascade="all, delete-orphan")

class GroupOrderItem(Base):
    __tablename__ = "group_order_items"
    id = Column(Integer, primary_key=True, index=True)
    participant_id = Column(Integer, ForeignKey("group_order_participants.id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=False)
    quantity = Column(Integer, default=1)

    participant = relationship("GroupOrderParticipant", back_populates="items")
    dish = relationship("Dish")

class DeliveryAssignment(Base):
    __tablename__ = "delivery_assignments"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)
    delivery_partner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(30), default="assigned") # assigned, accepted, picked_up, delivered, rejected
    earnings = Column(Float, default=45.0)
    assigned_at = Column(DateTime, default=datetime.datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

    order = relationship("Order", back_populates="delivery_assignment")
    partner = relationship("User")

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=False)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=True)
    rating = Column(Float, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User")
    restaurant = relationship("Restaurant")
    dish = relationship("Dish")

class Coupon(Base):
    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    discount_percentage = Column(Float, default=0.0)
    flat_discount = Column(Float, default=0.0)
    min_order_amount = Column(Float, default=200.0)
    max_discount = Column(Float, default=100.0)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)

class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(Integer, ForeignKey("restaurants.id"), nullable=True)
    dish_id = Column(Integer, ForeignKey("dishes.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
