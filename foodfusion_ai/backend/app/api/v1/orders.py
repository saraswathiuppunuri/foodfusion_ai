from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.permissions import get_current_user
from app.models.entities import User, Order, OrderItem
from app.schemas.schemas import CheckoutRequest, OrderOut
from app.services.order_service import checkout_cart, transition_order_status, add_to_cart

router = APIRouter(prefix="/orders", tags=["Orders & Tracking"])

def format_order_out(order: Order) -> OrderOut:
    return OrderOut(
        id=order.id,
        restaurant_id=order.restaurant_id,
        restaurant_name=order.restaurant.name if order.restaurant else "Restaurant",
        order_type=order.order_type,
        status=order.status,
        item_subtotal=order.item_subtotal,
        delivery_fee=order.delivery_fee,
        tax_gst=order.tax_gst,
        discount_amount=order.discount_amount,
        grand_total=order.grand_total,
        delivery_address=order.delivery_address,
        delivery_instructions=order.delivery_instructions,
        payment_method=order.payment_method,
        payment_status=order.payment_status,
        estimated_prep_min=order.estimated_prep_min,
        estimated_delivery_min=order.estimated_delivery_min,
        total_eta_min=order.estimated_prep_min + order.estimated_delivery_min,
        created_at=order.created_at,
        items=[
            {
                "id": it.id,
                "dish_id": it.dish_id,
                "dish_name": it.dish_name,
                "unit_price": it.unit_price,
                "quantity": it.quantity,
                "subtotal": it.subtotal
            } for it in order.items
        ],
        timeline=[
            {
                "status": t.status,
                "message": t.message,
                "timestamp": t.timestamp
            } for t in order.timeline
        ]
    )

@router.post("/checkout", response_model=OrderOut)
def checkout(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Processes checkout from cart, validates prices server-side, and generates tracking timeline."""
    order = checkout_cart(current_user, req, db)
    return format_order_out(order)

@router.get("", response_model=List[OrderOut])
def list_my_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Retrieves order history for the authenticated customer."""
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.id.desc()).all()
    return [format_order_out(o) for o in orders]

@router.get("/{order_id}", response_model=OrderOut)
def get_order_details(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves real-time status and timeline updates for an order."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Security: Only order owner or admin/owner/rider can view
    if current_user.role == "customer" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    return format_order_out(order)

@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: int,
    reason: str = "Customer requested cancellation",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancels an order if it has not yet reached preparation stage."""
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status not in ["placed", "accepted"]:
        raise HTTPException(status_code=400, detail="Cannot cancel an order that is already being prepared or in transit")

    updated = transition_order_status(order_id, "cancelled", reason, db)
    return format_order_out(updated)

@router.post("/{order_id}/reorder")
def reorder_previous(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Copies dishes from a previous order directly into the customer's cart."""
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    added_count = 0
    for item in order.items:
        try:
            add_to_cart(current_user, item.dish_id, item.quantity, "", db)
            added_count += 1
        except Exception:
            pass

    return {"status": "success", "message": f"Added {added_count} items from Order #{order_id} to your cart!"}
