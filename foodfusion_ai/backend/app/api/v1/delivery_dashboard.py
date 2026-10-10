from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.permissions import require_delivery_partner
from app.models.entities import User, DeliveryAssignment, Order
from app.schemas.schemas import OrderOut
from app.api.v1.orders import format_order_out
from app.services.order_service import transition_order_status

router = APIRouter(prefix="/delivery-partner", tags=["Delivery Partner Dashboard"])

@router.get("/assignments")
def get_my_assignments(
    current_user: User = Depends(require_delivery_partner),
    db: Session = Depends(get_db)
):
    """Retrieves delivery assignments assigned to the current rider."""
    assignments = db.query(DeliveryAssignment).filter(
        DeliveryAssignment.delivery_partner_id == current_user.id
    ).order_by(DeliveryAssignment.id.desc()).all()

    result = []
    for a in assignments:
        o = a.order
        r = o.restaurant
        result.append({
            "assignment_id": a.id,
            "order_id": o.id,
            "status": a.status,
            "order_status": o.status,
            "earnings": a.earnings,
            "restaurant_name": r.name if r else "",
            "pickup_address": r.address if r else "",
            "delivery_address": o.delivery_address,
            "delivery_instructions": o.delivery_instructions,
            "assigned_at": a.assigned_at,
            "delivered_at": a.delivered_at
        })
    return result

@router.put("/assignments/{assignment_id}/status")
def update_delivery_progress(
    assignment_id: int,
    action: str, # accept, picked_up, delivered
    current_user: User = Depends(require_delivery_partner),
    db: Session = Depends(get_db)
):
    """Transitions delivery status along the order timeline."""
    assignment = db.query(DeliveryAssignment).filter(
        DeliveryAssignment.id == assignment_id,
        DeliveryAssignment.delivery_partner_id == current_user.id
    ).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    order = assignment.order
    if action == "accept":
        assignment.status = "accepted"
    elif action == "picked_up":
        assignment.status = "picked_up"
        transition_order_status(order.id, "picked_up", None, db)
    elif action == "delivered":
        assignment.status = "delivered"
        transition_order_status(order.id, "delivered", None, db)
    else:
        raise HTTPException(status_code=400, detail="Invalid action")

    db.commit()
    return {"status": "success", "message": f"Delivery updated to {action}", "order_status": order.status}

@router.get("/earnings")
def get_earnings_summary(
    current_user: User = Depends(require_delivery_partner),
    db: Session = Depends(get_db)
):
    """Calculates total deliveries and earnings for the partner."""
    delivered = db.query(DeliveryAssignment).filter(
        DeliveryAssignment.delivery_partner_id == current_user.id,
        DeliveryAssignment.status == "delivered"
    ).all()

    total_earnings = sum(d.earnings for d in delivered)
    return {
        "completed_deliveries": len(delivered),
        "total_earnings_inr": round(total_earnings, 2),
        "rating": 4.9,
        "active_incentives": "₹150 peak-hour bonus active"
    }
