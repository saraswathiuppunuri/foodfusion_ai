from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import Restaurant, Dish, Category
from app.schemas.schemas import RestaurantOut, DishOut, CategoryOut

router = APIRouter(tags=["Restaurants & Menus"])

@router.get("/categories", response_model=List[CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    """Returns all food categories."""
    return db.query(Category).all()

@router.get("/restaurants", response_model=List[RestaurantOut])
def list_restaurants(
    search: Optional[str] = Query(None, description="Search by name or cuisine"),
    cuisine: Optional[str] = Query(None),
    min_rating: Optional[float] = Query(None, ge=1.0, le=5.0),
    max_prep_time: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Lists restaurants with multi-criteria filtering."""
    query = db.query(Restaurant).filter(Restaurant.is_active == True)

    if search:
        query = query.filter(
            (Restaurant.name.ilike(f"%{search}%")) |
            (Restaurant.cuisine.ilike(f"%{search}%"))
        )
    if cuisine:
        query = query.filter(Restaurant.cuisine.ilike(f"%{cuisine}%"))
    if min_rating:
        query = query.filter(Restaurant.rating >= min_rating)
    if max_prep_time:
        query = query.filter(Restaurant.avg_prep_time_min <= max_prep_time)

    return query.all()

@router.get("/restaurants/{restaurant_id}", response_model=RestaurantOut)
def get_restaurant_details(restaurant_id: int, db: Session = Depends(get_db)):
    """Retrieves full restaurant profile and menu dishes."""
    rest = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not rest:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return rest

@router.get("/dishes", response_model=List[DishOut])
def search_dishes(
    search: Optional[str] = Query(None),
    is_veg: Optional[bool] = Query(None),
    spice_level: Optional[str] = Query(None),
    max_price: Optional[float] = Query(None),
    category_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """Searches menu items with dietary, spice, and price filters."""
    query = db.query(Dish).filter(Dish.is_available == True)

    if search:
        query = query.filter(
            (Dish.name.ilike(f"%{search}%")) |
            (Dish.description.ilike(f"%{search}%")) |
            (Dish.tags.ilike(f"%{search}%"))
        )
    if is_veg is not None:
        query = query.filter(Dish.is_veg == is_veg)
    if spice_level:
        query = query.filter(Dish.spice_level == spice_level)
    if max_price:
        query = query.filter(Dish.price <= max_price)
    if category_id:
        query = query.filter(Dish.category_id == category_id)

    return query.all()
