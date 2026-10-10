import datetime
from sqlalchemy.orm import Session
from app.core.security import hash_password
from app.core.config import settings
from app.models.entities import (
    User, UserRole, Category, Restaurant, Dish, SurplusOffer,
    Order, OrderItem, OrderTimeline, OrderStatus, Coupon, DeliveryAssignment
)

def seed_database(db: Session):
    """Seeds rich, realistic demo data across all roles and models."""
    if db.query(User).filter(User.email == settings.ADMIN_EMAIL).first():
        return # Already seeded

    print("[*] Seeding FoodFusion AI Database with realistic production-grade data...")

    # 1. USERS & ROLES
    admin_user = User(
        name="System Administrator",
        email=settings.ADMIN_EMAIL,
        hashed_password=hash_password(settings.ADMIN_PASSWORD),
        role=UserRole.ADMIN.value,
        phone="+91 99000 00001"
    )
    owner_user = User(
        name="Vikram Seth (Spice Villa)",
        email=settings.RESTAURANT_EMAIL,
        hashed_password=hash_password(settings.RESTAURANT_PASSWORD),
        role=UserRole.RESTAURANT_OWNER.value,
        phone="+91 99000 00002"
    )
    rider_user = User(
        name="Ramesh Kumar (Rider #402)",
        email=settings.DELIVERY_EMAIL,
        hashed_password=hash_password(settings.DELIVERY_PASSWORD),
        role=UserRole.DELIVERY_PARTNER.value,
        phone="+91 99000 00003"
    )
    customer_user = User(
        name="Aman Gupta",
        email=settings.CUSTOMER_EMAIL,
        hashed_password=hash_password(settings.CUSTOMER_PASSWORD),
        role=UserRole.CUSTOMER.value,
        phone="+91 98450 12345",
        dietary_preference="vegetarian",
        spice_preference="spicy",
        preferred_cuisines="North Indian, Biryani",
        avg_budget=350.0
    )

    db.add_all([admin_user, owner_user, rider_user, customer_user])
    db.commit()

    # 2. CATEGORIES
    c_biryani = Category(name="Biryani & Rice", icon_name="rice_bowl", image_url="https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=300")
    c_curry = Category(name="Curries & Gravies", icon_name="soup_kitchen", image_url="https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=300")
    c_healthy = Category(name="Healthy & Salads", icon_name="spa", image_url="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=300")
    c_south = Category(name="South Indian", icon_name="breakfast_dining", image_url="https://images.unsplash.com/photo-1668236543090-82eba5ee5976?w=300")
    c_asian = Category(name="Pan-Asian & Noodles", icon_name="ramen_dining", image_url="https://images.unsplash.com/photo-1585032226651-759b368d7246?w=300")

    db.add_all([c_biryani, c_curry, c_healthy, c_south, c_asian])
    db.commit()

    # 3. RESTAURANTS
    r1 = Restaurant(
        owner_id=owner_user.id,
        name="Spice Villa Artisanal Kitchen",
        description="Authentic royal North Indian curries and aromatic dum gravies.",
        cuisine="North Indian, Mughlai",
        rating=4.7,
        review_count=340,
        avg_prep_time_min=18,
        address="102 100ft Road, Indiranagar, Bengaluru",
        latitude=12.9716,
        longitude=77.6412,
        phone="+91 98450 11223",
        image_url="https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600"
    )
    r2 = Restaurant(
        owner_id=owner_user.id,
        name="Green Bowl Organics",
        description="Farm-to-table macro-balanced salads and plant-based protein bowls.",
        cuisine="Healthy, Vegan, Mediterranean",
        rating=4.6,
        review_count=195,
        avg_prep_time_min=14,
        address="45 4th Block, Koramangala, Bengaluru",
        latitude=12.9352,
        longitude=77.6245,
        phone="+91 98450 44556",
        image_url="https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=600"
    )
    r3 = Restaurant(
        owner_id=owner_user.id,
        name="Biryani Central & Kebabs",
        description="Authentic Hyderabadi dum biryani cooked in sealed handis.",
        cuisine="Hyderabadi, Biryani, Mughlai",
        rating=4.8,
        review_count=520,
        avg_prep_time_min=22,
        address="78 Sector 3, HSR Layout, Bengaluru",
        latitude=12.9121,
        longitude=77.6446,
        phone="+91 98450 77889",
        image_url="https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600"
    )

    db.add_all([r1, r2, r3])
    db.commit()

    # 4. DISHES
    dishes = [
        # Spice Villa Dishes
        Dish(
            restaurant_id=r1.id, category_id=c_curry.id,
            name="Paneer Butter Masala Mini Bowl",
            description="Tender cottage cheese cubes simmered in creamy makhani cashew gravy with 2 butter rotis.",
            price=160.0, is_veg=True, spice_level="mild",
            calories=440, protein_g=18, prep_time_min=16,
            image_url="https://images.unsplash.com/photo-1631452180519-c014fe946bc7?w=400",
            tags="paneer, curry, vegetarian, mild, creamy, north indian, dinner",
            ingredients="Paneer, Tomatoes, Cashews, Butter, Cream, Spices",
            allergens="Dairy, Cashews (Nuts)", stock_count=40
        ),
        Dish(
            restaurant_id=r1.id, category_id=c_curry.id,
            name="Andhra Fiery Chicken Curry",
            description="Tender country chicken simmered in stone-ground Guntur red chilli and curry leaf gravy.",
            price=175.0, is_veg=False, spice_level="spicy",
            calories=410, protein_g=34, prep_time_min=18,
            image_url="https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=400",
            tags="chicken, spicy, fiery, non-veg, andhra, high-protein",
            ingredients="Chicken, Guntur Chillies, Garlic, Onion, Spices",
            allergens="None", stock_count=35
        ),
        Dish(
            restaurant_id=r1.id, category_id=c_curry.id,
            name="Dal Tadka & Fragrant Jeera Rice",
            description="Yellow lentils tempered with aromatic cumin, garlic, and pure desi ghee.",
            price=135.0, is_veg=True, spice_level="mild",
            calories=380, protein_g=14, prep_time_min=12,
            image_url="https://images.unsplash.com/photo-1546833999-b9f581a1996d?w=400",
            tags="dal, lentils, jeera rice, vegetarian, budget, healthy, comfort",
            ingredients="Toor dal, Cumin, Ghee, Garlic, Basmati Rice",
            allergens="Dairy (Ghee)", stock_count=50
        ),
        Dish(
            restaurant_id=r1.id, category_id=c_curry.id,
            name="Garlic Butter Tandoori Naan (2 pcs)",
            description="Leavened oven-baked flatbread brushed with crushed garlic and butter.",
            price=55.0, is_veg=True, spice_level="mild",
            calories=240, protein_g=6, prep_time_min=8,
            image_url="https://images.unsplash.com/photo-1626074353765-517a681e40be?w=400",
            tags="naan, bread, garlic, vegetarian, sides",
            ingredients="Refined Flour, Garlic, Butter, Yeast",
            allergens="Gluten, Dairy", stock_count=60
        ),

        # Green Bowl Organics Dishes
        Dish(
            restaurant_id=r2.id, category_id=c_healthy.id,
            name="Tofu Avocado Quinoa Crunch Bowl",
            description="Grilled organic tofu, tri-color quinoa, charred corn, edamame and lime tahini dressing.",
            price=210.0, is_veg=True, spice_level="mild",
            calories=340, protein_g=22, prep_time_min=14,
            image_url="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400",
            tags="tofu, quinoa, avocado, vegan, salad, high-protein, clean eating",
            ingredients="Organic Tofu, Quinoa, Hass Avocado, Edamame, Tahini",
            allergens="Soy, Sesame", stock_count=30
        ),
        Dish(
            restaurant_id=r2.id, category_id=c_healthy.id,
            name="Spicy Peri-Peri Soya Wrap",
            description="Grilled textured soya protein tossed with crunchy bell peppers and peri-peri sauce in whole wheat wrap.",
            price=145.0, is_veg=True, spice_level="spicy",
            calories=310, protein_g=21, prep_time_min=12,
            image_url="https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=400",
            tags="soya, wrap, spicy, peri-peri, vegan, protein, budget",
            ingredients="Soya chunks, Whole wheat wrap, Bell peppers, Peri-peri dressing",
            allergens="Gluten, Soy", stock_count=25
        ),

        # Biryani Central Dishes
        Dish(
            restaurant_id=r3.id, category_id=c_biryani.id,
            name="Royal Nawabi Dum Chicken Biryani",
            description="Aged long-grain basmati layered with marinated chicken, saffron, and fried onions with mirchi salan.",
            price=220.0, is_veg=False, spice_level="medium",
            calories=560, protein_g=38, prep_time_min=20,
            image_url="https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=400",
            tags="biryani, chicken, hyderabadi, non-veg, high-protein, best-seller",
            ingredients="Basmati Rice, Marinated Chicken, Saffron, Fried Onions, Spices",
            allergens="Dairy (Curd/Ghee)", stock_count=45
        ),
        Dish(
            restaurant_id=r3.id, category_id=c_biryani.id,
            name="Hyderabadi Shahi Veg Dum Biryani",
            description="Seasonal vegetables, marinated paneer cubes, cashews, and saffron rice with mint raita.",
            price=175.0, is_veg=True, spice_level="medium",
            calories=460, protein_g=16, prep_time_min=18,
            image_url="https://images.unsplash.com/photo-1642821373181-696a54913e9a?w=400",
            tags="veg biryani, paneer, vegetarian, aromatic, saffron, dinner",
            ingredients="Basmati Rice, Paneer, Carrots, Beans, Mint, Cashews",
            allergens="Dairy, Cashews", stock_count=35
        ),
        Dish(
            restaurant_id=r3.id, category_id=c_biryani.id,
            name="Fiery Andhra Spicy Mutton Biryani",
            description="Tender mutton chunks marinated in fiery red chillies layered with fragrant basmati.",
            price=295.0, is_veg=False, spice_level="spicy",
            calories=640, protein_g=42, prep_time_min=24,
            image_url="https://images.unsplash.com/photo-1589302168068-964664d93dc0?w=400",
            tags="mutton, biryani, spicy, fiery, non-veg, high-protein",
            ingredients="Basmati Rice, Tender Mutton, Andhra Chillies, Spices",
            allergens="Dairy", stock_count=20
        )
    ]

    db.add_all(dishes)
    db.commit()

    # 5. SURPLUS OFFERS (Save Food, Save Money)
    now = datetime.datetime.utcnow()
    surplus_offers = [
        SurplusOffer(
            restaurant_id=r1.id, dish_id=dishes[0].id,
            original_price=160.0, discounted_price=79.0,
            quantity_available=6, waste_saved_kg=1.8, co2_saved_kg=4.2,
            offer_expires_at=now + datetime.timedelta(hours=2.5),
            status="active"
        ),
        SurplusOffer(
            restaurant_id=r3.id, dish_id=dishes[6].id,
            original_price=220.0, discounted_price=99.0,
            quantity_available=4, waste_saved_kg=2.4, co2_saved_kg=5.8,
            offer_expires_at=now + datetime.timedelta(hours=1.5),
            status="active"
        ),
        SurplusOffer(
            restaurant_id=r2.id, dish_id=dishes[4].id,
            original_price=210.0, discounted_price=105.0,
            quantity_available=5, waste_saved_kg=1.5, co2_saved_kg=3.1,
            offer_expires_at=now + datetime.timedelta(hours=3),
            status="active"
        )
    ]
    db.add_all(surplus_offers)

    # 6. COUPONS
    coupons = [
        Coupon(code="SAVE50", discount_percentage=50.0, max_discount=100.0, min_order_amount=150.0, expires_at=now + datetime.timedelta(days=30)),
        Coupon(code="ZEROCOL", flat_discount=40.0, min_order_amount=100.0, expires_at=now + datetime.timedelta(days=30)),
        Coupon(code="FOODAI", discount_percentage=20.0, max_discount=60.0, min_order_amount=120.0, expires_at=now + datetime.timedelta(days=30))
    ]
    db.add_all(coupons)

    # 7. HISTORICAL & ACTIVE ORDERS (For live tracking & real analytics)
    order1 = Order(
        user_id=customer_user.id,
        restaurant_id=r1.id,
        order_type="regular",
        status=OrderStatus.PREPARING.value,
        item_subtotal=335.0,
        delivery_fee=40.0,
        tax_gst=16.75,
        discount_amount=0.0,
        grand_total=391.75,
        delivery_address="Flat 402, Green Glen Layout, Bellandur, Bengaluru",
        delivery_instructions="Leave at the security gate if unreachable",
        payment_method="demo_upi",
        payment_status="paid",
        estimated_prep_min=18,
        estimated_delivery_min=14
    )
    db.add(order1)
    db.commit()

    # Add items to order1
    oi1 = OrderItem(order_id=order1.id, dish_id=dishes[0].id, dish_name=dishes[0].name, unit_price=160.0, quantity=1, subtotal=160.0)
    oi2 = OrderItem(order_id=order1.id, dish_id=dishes[1].id, dish_name=dishes[1].name, unit_price=175.0, quantity=1, subtotal=175.0)
    db.add_all([oi1, oi2])

    # Add timeline to order1
    t1 = OrderTimeline(order_id=order1.id, status="placed", message="Order placed and payment verified via Demo UPI")
    t2 = OrderTimeline(order_id=order1.id, status="accepted", message="Spice Villa accepted the order")
    t3 = OrderTimeline(order_id=order1.id, status="preparing", message="Chef is preparing your fresh meal")
    db.add_all([t1, t2, t3])

    # Delivery assignment
    da = DeliveryAssignment(order_id=order1.id, delivery_partner_id=rider_user.id, status="assigned", earnings=45.0)
    db.add(da)

    # Historical completed orders for analytics
    past_order = Order(
        user_id=customer_user.id,
        restaurant_id=r3.id,
        order_type="surplus",
        status=OrderStatus.DELIVERED.value,
        item_subtotal=220.0,
        delivery_fee=0.0,
        tax_gst=11.0,
        discount_amount=121.0, # 55% discount
        grand_total=110.0,
        delivery_address="Flat 402, Green Glen Layout, Bengaluru",
        payment_method="demo_card",
        payment_status="paid",
        created_at=now - datetime.timedelta(days=1)
    )
    db.add(past_order)
    db.commit()

    print("[*] Seed data generation complete! Demo accounts ready.")
