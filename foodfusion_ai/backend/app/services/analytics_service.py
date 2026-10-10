from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.entities import Order, OrderItem, Dish, Restaurant, SurplusOffer, User
from app.schemas.schemas import RestaurantAnalyticsOut, PlatformAnalyticsOut

def calculate_restaurant_analytics(restaurant_id: int, db: Session) -> RestaurantAnalyticsOut:
    """Calculates live analytics directly from database tables for a specific restaurant."""
    orders = db.query(Order).filter(Order.restaurant_id == restaurant_id).all()
    dishes = db.query(Dish).filter(Dish.restaurant_id == restaurant_id).all()
    surplus_offers = db.query(SurplusOffer).filter(SurplusOffer.restaurant_id == restaurant_id).all()
    rest = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    total_orders = len(orders)
    valid_orders = [o for o in orders if o.status not in ["cancelled", "rejected"]]
    total_revenue = sum(o.grand_total for o in valid_orders)

    # Surplus metrics
    surplus_orders = [o for o in valid_orders if o.order_type == "surplus"]
    surplus_rev = sum(o.grand_total for o in surplus_orders)
    surplus_kg = sum(s.waste_saved_kg for s in surplus_offers)

    # Best-selling dishes
    order_ids = [o.id for o in valid_orders]
    best_sellers = []
    if order_ids:
        item_counts = db.query(
            OrderItem.dish_name, func.sum(OrderItem.quantity).label("total_sold"), func.sum(OrderItem.subtotal).label("total_rev")
        ).filter(OrderItem.order_id.in_(order_ids)).group_by(OrderItem.dish_name).order_by(func.sum(OrderItem.quantity).desc()).limit(5).all()

        for name, sold, rev in item_counts:
            best_sellers.append({
                "dish_name": name,
                "units_sold": int(sold or 0),
                "revenue": float(rev or 0.0)
            })

    # Low-stock or unavailable items
    low_stock = []
    for d in dishes:
        if not d.is_available or d.stock_count <= 15:
            low_stock.append({
                "dish_id": d.id,
                "name": d.name,
                "stock_count": d.stock_count,
                "is_available": d.is_available
            })

    # Status distribution
    status_counts = dict(Counter(o.status for o in orders))

    # Hourly distribution
    hourly_counts = {f"{h:02d}:00": 0 for h in range(8, 24)}
    for o in orders:
        if o.created_at:
            h_str = f"{o.created_at.hour:02d}:00"
            if h_str in hourly_counts:
                hourly_counts[h_str] += 1

    return RestaurantAnalyticsOut(
        total_orders=total_orders,
        total_revenue=round(total_revenue, 2),
        surplus_saved_kg=round(surplus_kg, 1),
        surplus_revenue=round(surplus_rev, 2),
        avg_rating=rest.rating if rest else 4.5,
        best_selling_dishes=best_sellers,
        low_stock_dishes=low_stock,
        order_status_distribution=status_counts,
        hourly_trends=hourly_counts
    )

def calculate_platform_analytics(db: Session) -> PlatformAnalyticsOut:
    """Calculates platform-wide metrics for the Administrator dashboard."""
    users_count = db.query(User).count()
    restaurants_count = db.query(Restaurant).count()
    orders_count = db.query(Order).count()
    gmv = db.query(func.sum(Order.grand_total)).filter(Order.status != "cancelled").scalar() or 0.0
    waste_kg = db.query(func.sum(SurplusOffer.waste_saved_kg)).scalar() or 0.0
    active_surplus = db.query(SurplusOffer).filter(SurplusOffer.status == "active").count()
    active_deliveries = db.query(Order).filter(Order.status.in_(["preparing", "ready_for_pickup", "picked_up"])).count()

    return PlatformAnalyticsOut(
        total_users=users_count,
        total_restaurants=restaurants_count,
        total_orders=orders_count,
        gross_merchandise_value=round(float(gmv), 2),
        total_food_waste_prevented_kg=round(float(waste_kg), 1),
        active_surplus_deals=active_surplus,
        active_deliveries=active_deliveries
    )
