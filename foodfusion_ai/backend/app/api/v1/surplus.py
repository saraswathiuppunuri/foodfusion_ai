from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.permissions import get_current_user, require_restaurant_owner
from app.models.entities import User
from app.schemas.schemas import SurplusOfferOut, SurplusOfferCreate, OrderOut
from app.services.surplus_service import (
    get_active_surplus_offers, create_surplus_offer_by_owner, reserve_surplus_offer
)
from app.api.v1.orders import format_order_out

router = APIRouter(prefix="/surplus", tags=["Sustainable Surplus Food Marketplace"])

@router.get("", response_model=List[SurplusOfferOut])
def list_surplus_offers(db: Session = Depends(get_db)):
    """Retrieves all active surplus food offers before deadline with positive stock."""
    return get_active_surplus_offers(db)

@router.post("", response_model=SurplusOfferOut)
def list_new_surplus_deal(
    offer_in: SurplusOfferCreate,
    current_user: User = Depends(require_restaurant_owner),
    db: Session = Depends(get_db)
):
    """Allows restaurant owners to list freshly cooked end-of-batch meals at steep discounts."""
    offer = create_surplus_offer_by_owner(current_user, offer_in, db)
    # Re-fetch formatted view
    offers = get_active_surplus_offers(db)
    matched = next((o for o in offers if o.id == offer.id), None)
    return matched

@router.post("/reserve/{offer_id}", response_model=OrderOut)
def reserve_deal(
    offer_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reserves a surplus food meal, prevents waste, and places an order."""
    order = reserve_surplus_offer(current_user, offer_id, db)
    return format_order_out(order)
