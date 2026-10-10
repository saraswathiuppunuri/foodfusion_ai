from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.permissions import require_admin
from app.models.entities import User, Restaurant, Coupon
from app.schemas.schemas import UserOut, RestaurantOut, PlatformAnalyticsOut
from app.services.analytics_service import calculate_platform_analytics

router = APIRouter(prefix="/admin", tags=["Administrator Dashboard"])

@router.get("/users", response_model=List[UserOut])
def list_all_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Lists registered users and roles across the platform."""
    return db.query(User).all()

@router.put("/users/{user_id}/status")
def toggle_user_active(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Suspends or activates a user account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = is_active
    db.commit()
    return {"status": "success", "message": f"User active status set to {is_active}"}

@router.get("/restaurants", response_model=List[RestaurantOut])
def list_restaurants_admin(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Lists all restaurants for administrative verification and audit."""
    return db.query(Restaurant).all()

@router.put("/restaurants/{restaurant_id}/verify")
def verify_restaurant(
    restaurant_id: int,
    is_verified: bool,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Approves or revokes restaurant verification on the platform."""
    rest = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not rest:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    rest.is_verified = is_verified
    db.commit()
    return {"status": "success", "message": f"Restaurant verification set to {is_verified}"}

@router.get("/analytics", response_model=PlatformAnalyticsOut)
def get_global_analytics(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Calculates platform-wide GMV, food waste saved, and system totals."""
    return calculate_platform_analytics(db)
