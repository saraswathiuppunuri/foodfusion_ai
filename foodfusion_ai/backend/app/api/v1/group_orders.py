from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.permissions import get_current_user
from app.models.entities import User
from app.schemas.schemas import (
    GroupOrderCreate, GroupOrderJoin, GroupOrderItemAdd, 
    GroupOrderOut, OrderOut
)
from app.services.group_order_service import (
    create_group_session, join_group_session, add_dish_to_participant,
    calculate_group_order_summary, place_group_order
)
from app.api.v1.orders import format_order_out

router = APIRouter(prefix="/group-orders", tags=["Group Ordering & Split Bills"])

@router.post("", response_model=GroupOrderOut)
def create_session(
    data: GroupOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new group order session and returns a shareable join code."""
    session = create_group_session(current_user, data.restaurant_id, data.total_budget, db)
    return calculate_group_order_summary(session.id, db)

@router.post("/join")
def join_session(
    data: GroupOrderJoin,
    db: Session = Depends(get_db)
):
    """Allows a friend to join a group order using the 6-character shareable code."""
    participant = join_group_session(
        join_code=data.join_code,
        user_name=data.user_name,
        personal_budget=data.personal_budget,
        diet_pref=data.diet_pref,
        db=db
    )
    return {
        "status": "success",
        "participant_id": participant.id,
        "session_id": participant.session_id,
        "message": f"Successfully joined group order at {participant.session.restaurant.name}!"
    }

@router.post("/{session_id}/participants/{participant_id}/items", response_model=GroupOrderOut)
def add_item_to_group(
    session_id: int,
    participant_id: int,
    item_in: GroupOrderItemAdd,
    db: Session = Depends(get_db)
):
    """Adds a dish to a specific participant's sub-basket in the group order."""
    add_dish_to_participant(participant_id, item_in.dish_id, item_in.quantity, db)
    return calculate_group_order_summary(session_id, db)

@router.get("/{session_id}", response_model=GroupOrderOut)
def get_group_summary(
    session_id: int,
    db: Session = Depends(get_db)
):
    """Retrieves real-time group order status, individual subtotals, and fair-share bill split."""
    return calculate_group_order_summary(session_id, db)

@router.post("/{session_id}/place", response_model=OrderOut)
def place_order(
    session_id: int,
    delivery_address: str = "Host Meeting Location",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Organizer locks and confirms the entire group order, preventing duplicate submissions."""
    order = place_group_order(session_id, current_user, delivery_address, db)
    return format_order_out(order)
