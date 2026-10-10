import os
import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, 
    DateTime, ForeignKey, Text, Numeric
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from config import Config

Base = declarative_base()

class Restaurant(Base):
    __tablename__ = 'restaurants'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    cuisine = Column(String(100), nullable=False)
    rating = Column(Float, default=4.2)
    avg_prep_time = Column(Integer, default=20)
    address = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    phone = Column(String(30))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    dishes = relationship("Dish", back_populates="restaurant", cascade="all, delete-orphan")
    surplus_deals = relationship("SurplusDeal", back_populates="restaurant", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "cuisine": self.cuisine,
            "rating": self.rating,
            "avg_prep_time": self.avg_prep_time,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "phone": self.phone,
            "is_active": self.is_active
        }

class Dish(Base):
    __tablename__ = 'dishes'
    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String(50), nullable=False)
    is_veg = Column(Boolean, default=True)
    spice_level = Column(String(20), default='medium')
    calories = Column(Integer, default=350)
    protein_g = Column(Integer, default=12)
    image_url = Column(String(255))
    tags = Column(String(255))
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="dishes")
    surplus_deal = relationship("SurplusDeal", back_populates="dish", uselist=False)

    def to_dict(self):
        return {
            "id": self.id,
            "restaurant_id": self.restaurant_id,
            "restaurant_name": self.restaurant.name if self.restaurant else "",
            "name": self.name,
            "description": self.description,
            "price": float(self.price),
            "category": self.category,
            "is_veg": self.is_veg,
            "spice_level": self.spice_level,
            "calories": self.calories,
            "protein_g": self.protein_g,
            "image_url": self.image_url,
            "tags": self.tags,
            "is_available": self.is_available
        }

class SurplusDeal(Base):
    __tablename__ = 'surplus_deals'
    id = Column(Integer, primary_key=True)
    dish_id = Column(Integer, ForeignKey('dishes.id'), nullable=False)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id'), nullable=False)
    original_price = Column(Float, nullable=False)
    discounted_price = Column(Float, nullable=False)
    quantity_available = Column(Integer, nullable=False)
    waste_saved_kg = Column(Float, default=0.5)
    co2_saved_kg = Column(Float, default=1.2)
    expiry_time = Column(DateTime, nullable=False)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    dish = relationship("Dish", back_populates="surplus_deal")
    restaurant = relationship("Restaurant", back_populates="surplus_deals")

    def to_dict(self):
        now = datetime.datetime.utcnow()
        remaining_minutes = max(0, int((self.expiry_time - now).total_seconds() / 60))
        discount_percent = int(((self.original_price - self.discounted_price) / self.original_price) * 100) if self.original_price else 0
        return {
            "id": self.id,
            "dish_id": self.dish_id,
            "dish_name": self.dish.name if self.dish else "Surplus Meal",
            "restaurant_id": self.restaurant_id,
            "restaurant_name": self.restaurant.name if self.restaurant else "",
            "restaurant_address": self.restaurant.address if self.restaurant else "",
            "original_price": float(self.original_price),
            "discounted_price": float(self.discounted_price),
            "discount_percent": discount_percent,
            "quantity_available": self.quantity_available,
            "waste_saved_kg": float(self.waste_saved_kg),
            "co2_saved_kg": float(self.co2_saved_kg),
            "expiry_time": self.expiry_time.strftime("%Y-%m-%d %H:%M:%S"),
            "remaining_minutes": remaining_minutes,
            "status": self.status,
            "is_veg": self.dish.is_veg if self.dish else True,
            "image_url": self.dish.image_url if self.dish else ""
        }

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    customer_name = Column(String(100), nullable=False)
    customer_phone = Column(String(30))
    delivery_address = Column(Text)
    total_amount = Column(Float, nullable=False)
    order_type = Column(String(30), default='regular')
    status = Column(String(30), default='placed')
    predicted_prep_min = Column(Integer, default=20)
    actual_prep_min = Column(Integer, nullable=True)
    predicted_delivery_min = Column(Integer, default=15)
    delay_flag = Column(Boolean, default=False)
    delay_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "customer_name": self.customer_name,
            "total_amount": float(self.total_amount),
            "order_type": self.order_type,
            "status": self.status,
            "predicted_prep_min": self.predicted_prep_min,
            "predicted_delivery_min": self.predicted_delivery_min,
            "total_eta_min": self.predicted_prep_min + self.predicted_delivery_min,
            "delay_flag": self.delay_flag,
            "delay_reason": self.delay_reason,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "items": [item.to_dict() for item in self.items]
        }

class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    dish_id = Column(Integer, ForeignKey('dishes.id'), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    dish = relationship("Dish")

    def to_dict(self):
        return {
            "dish_id": self.dish_id,
            "dish_name": self.dish.name if self.dish else "Dish",
            "quantity": self.quantity,
            "unit_price": float(self.unit_price),
            "subtotal": float(self.quantity * self.unit_price)
        }

class UserProfile(Base):
    __tablename__ = 'user_profiles'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    preferred_cuisines = Column(String(255), default="North Indian, South Indian, Mughlai")
    dietary_preference = Column(String(50), default="none")
    spice_preference = Column(String(30), default="medium")
    avg_budget = Column(Float, default=300.0)
    past_order_tags = Column(Text, default="paneer, biryani, spicy, curry, tandoori, high-protein")

    def to_dict(self):
        return {
            "username": self.username,
            "preferred_cuisines": self.preferred_cuisines,
            "dietary_preference": self.dietary_preference,
            "spice_preference": self.spice_preference,
            "avg_budget": float(self.avg_budget),
            "past_order_tags": self.past_order_tags
        }

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False)
    phone = Column(String(30), nullable=True)
    password_hash = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    role = Column(String(30), default='customer')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    def set_password(self, password):
        import hashlib
        self.password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    def check_password(self, password):
        import hashlib
        return self.password_hash == hashlib.sha256(password.encode('utf-8')).hexdigest()

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone or "",
            "address": self.address or "",
            "role": self.role or "customer",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else ""
        }


# Database engine & session setup with automatic SQLite fallback
engine = None
SessionLocal = None

def get_engine():
    global engine
    if engine is not None:
        return engine

    # First attempt MySQL if specified or default
    mysql_uri = Config.SQLALCHEMY_DATABASE_URI or Config.DEFAULT_MYSQL
    try:
        test_engine = create_engine(mysql_uri, pool_pre_ping=True, pool_recycle=3600)
        with test_engine.connect() as conn:
            pass
        print(f"[*] Connected successfully to MySQL database.")
        engine = test_engine
        return engine
    except Exception as e:
        print(f"[!] MySQL connection failed ({e}). Falling back to local SQLite database (hackathon.db)...")
        sqlite_path = os.path.join(Config.BASE_DIR, 'hackathon.db')
        engine = create_engine(f"sqlite:///{sqlite_path}", connect_args={"check_same_thread": False})
        return engine

def get_db():
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    db = SessionLocal()
    try:
        return db
    finally:
        pass

def init_db():
    eng = get_engine()
    Base.metadata.create_all(bind=eng)
    seed_initial_data()
    ensure_default_user()

def ensure_default_user():
    eng = get_engine()
    Base.metadata.create_all(bind=eng)
    db = get_db()
    try:
        if db.query(User).count() == 0:
            demo_user = User(
                name="Aman Gupta",
                email="aman@foodfusion.com",
                phone="+91 98450 11223",
                address="Flat 402, Green Glen Towers, Indiranagar, Bengaluru",
                role="customer"
            )
            demo_user.set_password("password123")
            db.add(demo_user)
            db.commit()
            print("[*] Default demo user created.")
    except Exception as e:
        print("[!] Error creating default user:", e)
    finally:
        db.close()


def seed_initial_data():
    db = get_db()
    if db.query(Restaurant).count() > 0:
        db.close()
        return

    print("[*] Seeding rich sample restaurants, dishes, surplus deals, and predictive orders...")
    
    # Realistic restaurants in tech hub / urban center
    r1 = Restaurant(name="Spice Villa", cuisine="North Indian, Mughlai", rating=4.6, avg_prep_time=18,
                    address="102 Indiranagar 100ft Rd, Bengaluru", latitude=12.9716, longitude=77.6412, phone="+91 98450 11223")
    r2 = Restaurant(name="Green Bowl Organics", cuisine="Healthy, Salads, Vegan", rating=4.5, avg_prep_time=15,
                    address="45 Koramangala 4th Block, Bengaluru", latitude=12.9352, longitude=77.6245, phone="+91 98450 44556")
    r3 = Restaurant(name="Biryani Central", cuisine="Hyderabadi, Biryani, Mughlai", rating=4.7, avg_prep_time=22,
                    address="78 HSR Layout Sector 3, Bengaluru", latitude=12.9121, longitude=77.6446, phone="+91 98450 77889")
    r4 = Restaurant(name="Dosa & Filter Coffee Express", cuisine="South Indian, Breakfast", rating=4.8, avg_prep_time=12,
                    address="12 MG Road Metro Station, Bengaluru", latitude=12.9756, longitude=77.6066, phone="+91 98450 99001")
    r5 = Restaurant(name="Wok & Roll Pan-Asian", cuisine="Chinese, Thai, Pan-Asian", rating=4.3, avg_prep_time=20,
                    address="33 Whitefield Main Rd, Bengaluru", latitude=12.9698, longitude=77.7500, phone="+91 98450 33221")

    db.add_all([r1, r2, r3, r4, r5])
    db.commit()

    # Dishes with rich tags for scikit-learn TF-IDF matching and calorie/protein specs
    dishes = [
        # Spice Villa
        Dish(restaurant_id=r1.id, name="Paneer Butter Masala Mini Bowl", description="Rich paneer in tomato cashew gravy with 2 butter rotis",
             price=160.0, category="Curry", is_veg=True, spice_level="mild", calories=450, protein_g=18,
             tags="paneer, north indian, curry, vegetarian, mild, creamy, gravies, dinner, comfort",
             image_url="https://images.unsplash.com/photo-1631452180519-c014fe946bc7?auto=format&fit=crop&w=400&q=80"),
        Dish(restaurant_id=r1.id, name="Andhra Spicy Chicken Curry", description="Fiery country chicken simmered with crushed Guntur chillies",
             price=170.0, category="Curry", is_veg=False, spice_level="spicy", calories=410, protein_g=32,
             tags="chicken, spicy, andhra, curry, fiery, non-veg, high-protein, dinner",
             image_url="https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=400&q=80"),
        Dish(restaurant_id=r1.id, name="Dal Tadka with Jeera Rice", description="Yellow lentils tempered with ghee, cumin and garlic served with fragrant basmati",
             price=140.0, category="Combo", is_veg=True, spice_level="mild", calories=380, protein_g=14,
             tags="dal, lentils, jeera rice, vegetarian, budget, healthy, comfort, light",
             image_url="https://images.unsplash.com/photo-1546833999-b9f581a1996d?auto=format&fit=crop&w=400&q=80"),
        Dish(restaurant_id=r1.id, name="Garlic Butter Naan (2 pcs)", description="Soft tandoor baked leavened bread brushed with garlic butter",
             price=60.0, category="Bread", is_veg=True, spice_level="mild", calories=260, protein_g=6,
             tags="naan, bread, garlic, tandoor, vegetarian, sides",
             image_url="https://images.unsplash.com/photo-1626074353765-517a681e40be?auto=format&fit=crop&w=400&q=80"),

        # Green Bowl Organics
        Dish(restaurant_id=r2.id, name="Tofu Avocado Quinoa Crunch", description="Organic edamame, tri-color quinoa, charred corn, avocado with lime tahini",
             price=220.0, category="Salad", is_veg=True, spice_level="mild", calories=340, protein_g=22,
             tags="tofu, vegan, quinoa, avocado, salad, healthy, low-calorie, organic, gluten-free",
             image_url="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=400&q=80"),
        Dish(restaurant_id=r2.id, name="High-Protein Chickpea Mediterranean Bowl", description="Herbed chickpeas, roasted peppers, cucumber, feta and sourdough crisps",
             price=180.0, category="Healthy Bowl", is_veg=True, spice_level="mild", calories=390, protein_g=24,
             tags="chickpea, protein, salad, mediterranean, vegetarian, fitness, clean eating",
             image_url="https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=400&q=80"),
        Dish(restaurant_id=r2.id, name="Spicy Sriracha Soya Wrap", description="Grilled soya granules tossed with crunchy bell peppers and fiery sriracha mayo",
             price=150.0, category="Wrap", is_veg=True, spice_level="spicy", calories=320, protein_g=20,
             tags="soya, wrap, spicy, sriracha, vegan, protein, budget, quick bite",
             image_url="https://images.unsplash.com/photo-1528735602780-2552fd46c7af?auto=format&fit=crop&w=400&q=80"),

        # Biryani Central
        Dish(restaurant_id=r3.id, name="Nawabi Dum Chicken Biryani", description="Slow cooked basmati rice with marinated chicken, saffron, and mirchi ka salan",
             price=210.0, category="Biryani", is_veg=False, spice_level="medium", calories=550, protein_g=36,
             tags="biryani, chicken, hyderabadi, mughlai, non-veg, aromatic, high-protein",
             image_url="https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?auto=format&fit=crop&w=400&q=80"),
        Dish(restaurant_id=r3.id, name="Spicy Guntur Mutton Biryani Box", description="Tender mutton chunks marinated in fiery red chillies and layered with aged rice",
             price=290.0, category="Biryani", is_veg=False, spice_level="spicy", calories=620, protein_g=42,
             tags="mutton, biryani, spicy, fiery, non-veg, weekend special, rich",
             image_url="https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&w=400&q=80"),
        Dish(restaurant_id=r3.id, name="Royal Shahi Veg Biryani", description="Seasonal veggies, fried onions, paneer cubes, cashews with raita",
             price=170.0, category="Biryani", is_veg=True, spice_level="medium", calories=440, protein_g=15,
             tags="veg biryani, paneer, vegetarian, royal, aromatic, lunch, dinner",
             image_url="https://images.unsplash.com/photo-1642821373181-696a54913e9a?auto=format&fit=crop&w=400&q=80"),

        # Dosa & Filter Coffee Express
        Dish(restaurant_id=r4.id, name="Crispy Ghee Podi Masala Dosa", description="Golden crisp fermented crepe smeared with aromatic spicy podi and potato masala",
             price=110.0, category="South Indian", is_veg=True, spice_level="medium", calories=320, protein_g=8,
             tags="dosa, podi, ghee, south indian, vegetarian, crispy, budget, all-day",
             image_url="https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&w=400&q=80"),
        Dish(restaurant_id=r4.id, name="Steamed Ghee Idli (4 pcs) with Sambar", description="Pillowy soft rice cakes with piping hot vegetable lentil stew and coconut chutney",
             price=75.0, category="South Indian", is_veg=True, spice_level="mild", calories=240, protein_g=10,
             tags="idli, sambar, healthy, south indian, vegetarian, breakfast, budget, steamed",
             image_url="https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=400&q=80"),
        Dish(restaurant_id=r4.id, name="Degree Filter Coffee (Thermal Flask)", description="Strong chicory-blended decoction with frothy hot milk",
             price=45.0, category="Beverage", is_veg=True, spice_level="mild", calories=90, protein_g=3,
             tags="coffee, filter coffee, beverage, hot, south indian",
             image_url="https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=400&q=80"),

        # Wok & Roll Pan-Asian
        Dish(restaurant_id=r5.id, name="Fiery Schezwan Chilli Garlic Noodles", description="Wok tossed noodles with scallions, capsicum and house-made pungent schezwan sauce",
             price=150.0, category="Asian", is_veg=True, spice_level="spicy", calories=430, protein_g=11,
             tags="noodles, schezwan, spicy, chinese, asian, street food, vegetarian",
             image_url="https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=400&q=80"),
        Dish(restaurant_id=r5.id, name="Crispy Kung Pao Chicken Bowl", description="Glazed chicken breast cubes, toasted peanuts, dry red chillies over egg fried rice",
             price=190.0, category="Asian", is_veg=False, spice_level="spicy", calories=510, protein_g=34,
             tags="kung pao, chicken, spicy, chinese, asian, non-veg, high-protein",
             image_url="https://images.unsplash.com/photo-1525755662778-989d0524087e?auto=format&fit=crop&w=400&q=80")
    ]

    db.add_all(dishes)
    db.commit()

    # Surplus Deals (Feature 2: Zero-Waste Smart Marketplace)
    # Pre-calculated 50-65% discounts on fresh end-of-batch items
    now = datetime.datetime.utcnow()
    surplus_items = [
        SurplusDeal(dish_id=dishes[0].id, restaurant_id=r1.id, original_price=160.0, discounted_price=79.0,
                    quantity_available=6, waste_saved_kg=1.8, co2_saved_kg=4.2,
                    expiry_time=now + datetime.timedelta(minutes=85), status="active"),
        SurplusDeal(dish_id=dishes[7].id, restaurant_id=r3.id, original_price=210.0, discounted_price=99.0,
                    quantity_available=4, waste_saved_kg=2.4, co2_saved_kg=5.8,
                    expiry_time=now + datetime.timedelta(minutes=45), status="active"),
        SurplusDeal(dish_id=dishes[4].id, restaurant_id=r2.id, original_price=220.0, discounted_price=110.0,
                    quantity_available=5, waste_saved_kg=1.5, co2_saved_kg=2.9,
                    expiry_time=now + datetime.timedelta(minutes=110), status="active"),
        SurplusDeal(dish_id=dishes[13].id, restaurant_id=r5.id, original_price=150.0, discounted_price=69.0,
                    quantity_available=8, waste_saved_kg=2.1, co2_saved_kg=4.5,
                    expiry_time=now + datetime.timedelta(minutes=60), status="active")
    ]
    db.add_all(surplus_items)

    # User Profile (Feature 4: Scikit-learn Personalization)
    user = UserProfile(username="Aman Gupta", preferred_cuisines="North Indian, Biryani",
                       dietary_preference="none", spice_preference="spicy", avg_budget=400.0,
                       past_order_tags="paneer, biryani, spicy, chicken, tandoori, high-protein")
    db.add(user)

    # Sample Orders for Feature 5 Predictive Tracking & Kitchen Analytics
    sample_orders = [
        Order(customer_name="Priya Sharma", customer_phone="+91 99881 22334",
              delivery_address="Flat 402, Green Glen Layout, Bellandur", total_amount=480.0,
              order_type="nl_ai", status="preparing", predicted_prep_min=18, predicted_delivery_min=14,
              delay_flag=False, delay_reason=None),
        Order(customer_name="Rohan Verma", customer_phone="+91 98452 77112",
              delivery_address="3rd Cross, Indiranagar, Bengaluru", total_amount=210.0,
              order_type="surplus", status="out_for_delivery", predicted_prep_min=10, predicted_delivery_min=12,
              delay_flag=False, delay_reason=None),
        Order(customer_name="Aditya Sen (Group)", customer_phone="+91 97412 88990",
              delivery_address="Innovate Tech Park, Koramangala", total_amount=750.0,
              order_type="group", status="preparing", predicted_prep_min=28, predicted_delivery_min=20,
              delay_flag=True, delay_reason="High kitchen order spike (8 simultaneous tandoor tickets)"),
        Order(customer_name="Sneha Rao", customer_phone="+91 91081 44552",
              delivery_address="14th Main, HSR Layout Sector 4", total_amount=320.0,
              order_type="regular", status="delivered", predicted_prep_min=15, actual_prep_min=14,
              predicted_delivery_min=15, delay_flag=False, delay_reason=None)
    ]
    db.add_all(sample_orders)
    db.commit()
    db.close()
    print("[*] Database seeded successfully.")
