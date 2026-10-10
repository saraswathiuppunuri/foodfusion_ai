from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.permissions import require_restaurant_owner
from app.models.entities import User, Restaurant, Dish, Order
from app.schemas.schemas import (
    RestaurantOut, DishOut, DishCreate, OrderOut, 
    OrderStatusUpdate, RestaurantAnalyticsOut
)
from app.api.v1.orders import format_order_out
from app.services.order_service import transition_order_status
from app.services.analytics_service import calculate_restaurant_analytics

router = APIRouter(prefix="/restaurant-owner", tags=["Restaurant Owner Dashboard"])

@router.get("/restaurants", response_model=List[RestaurantOut])
def get_my_restaurants(
    current_user: User = Depends(require_restaurant_owner),
    db: Session = Depends(get_db)
):
    """Retrieves restaurants owned by the current authenticated owner."""
    return db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).all()

@router.get("/orders", response_model=List[OrderOut])
def get_incoming_orders(
    current_user: User = Depends(require_restaurant_owner),
    db: Session = Depends(get_db)
):
    """Retrieves live incoming kitchen order tickets."""
    owned_rest_ids = [r.id for r in current_user.restaurants]
    orders = db.query(Order).filter(Order.restaurant_id.in_(owned_rest_ids)).order_by(Order.id.desc()).all()
    return [format_order_out(o) for o in orders]

@router.put("/orders/{order_id}/status", response_model=OrderOut)
def update_order_stage(
    order_id: int,
    status_in: OrderStatusUpdate,
    current_user: User = Depends(require_restaurant_owner),
    db: Session = Depends(get_db)
):
    """Updates order stage: accepted, preparing, ready_for_pickup, rejected."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if current_user.role != "admin" and order.restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    updated = transition_order_status(order_id, status_in.status, status_in.reason, db)
    return format_order_out(updated)

@router.post("/dishes", response_model=DishOut)
def add_menu_dish(
    dish_in: DishCreate,
    current_user: User = Depends(require_restaurant_owner),
    db: Session = Depends(get_db)
):
    """Adds a new dish to the restaurant's menu."""
    rest = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).first()
    if not rest:
        raise HTTPException(status_code=400, detail="Owner does not have an active restaurant")

    dish = Dish(
        restaurant_id=rest.id,
        category_id=dish_in.category_id,
        name=dish_in.name,
        description=dish_in.description,
        price=dish_in.price,
        is_veg=dish_in.is_veg,
        spice_level=dish_in.spice_level,
        calories=dish_in.calories,
        protein_g=dish_in.protein_g,
        prep_time_min=dish_in.prep_time_min,
        image_url=dish_in.image_url,
        tags=dish_in.tags or dish_in.name.lower(),
        ingredients=dish_in.ingredients,
        allergens=dish_in.allergens,
        stock_count=dish_in.stock_count,
        is_available=True
    )
    db.add(dish)
    db.commit()
    db.refresh(dish)
    return dish

@router.put("/dishes/{dish_id}/availability", response_model=DishOut)
def toggle_dish_availability(
    dish_id: int,
    is_available: bool,
    current_user: User = Depends(require_restaurant_owner),
    db: Session = Depends(get_db)
):
    """Toggles live stock availability of a menu item."""
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    if current_user.role != "admin" and dish.restaurant.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    dish.is_available = is_available
    db.commit()
    db.refresh(dish)
    return dish

@router.get("/analytics", response_model=RestaurantAnalyticsOut)
def get_kitchen_analytics(
    current_user: User = Depends(require_restaurant_owner),
    db: Session = Depends(get_db)
):
    """Calculates live analytics from database records for the owner's primary restaurant."""
    rest = db.query(Restaurant).filter(Restaurant.owner_id == current_user.id).first()
    if not rest:
        raise HTTPException(status_code=404, detail="No restaurant found for this owner")
    return calculate_restaurant_analytics(rest.id, db)
