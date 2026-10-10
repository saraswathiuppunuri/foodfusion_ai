from datetime import datetime
from typing import Optional
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.entities import (
    Cart, CartItem, Dish, Order, OrderItem, OrderTimeline, 
    OrderStatus, Coupon, DeliveryAssignment, User, UserRole
)
from app.schemas.schemas import CartOut, CartItemOut, CheckoutRequest, OrderOut

def get_or_create_cart(user: User, db: Session) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    if not cart:
        cart = Cart(user_id=user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

def add_to_cart(user: User, dish_id: int, quantity: int, notes: str, db: Session) -> CartOut:
    cart = get_or_create_cart(user, db)
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish or not dish.is_available:
        raise HTTPException(status_code=400, detail="Dish is currently unavailable")

    # If cart already has items from a different restaurant, reset cart for single-restaurant delivery
    if cart.restaurant_id and cart.restaurant_id != dish.restaurant_id and cart.items:
        cart.items.clear()
    
    cart.restaurant_id = dish.restaurant_id

    existing = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.dish_id == dish_id).first()
    if existing:
        existing.quantity += quantity
        existing.customization_notes = notes or existing.customization_notes
    else:
        new_item = CartItem(cart_id=cart.id, dish_id=dish_id, quantity=quantity, customization_notes=notes)
        db.add(new_item)

    db.commit()
    return get_cart_view(user, db)

def get_cart_view(user: User, db: Session) -> CartOut:
    cart = get_or_create_cart(user, db)
    items_out = []
    subtotal = 0.0

    for item in cart.items:
        dish = item.dish
        item_tot = dish.price * item.quantity
        subtotal += item_tot
        items_out.append(CartItemOut(
            id=item.id,
            dish_id=dish.id,
            dish_name=dish.name,
            unit_price=dish.price,
            quantity=item.quantity,
            subtotal=item_tot,
            is_veg=dish.is_veg,
            image_url=dish.image_url
        ))

    tax = round(subtotal * 0.05, 2)
    delivery_fee = 40.0 if subtotal > 0 else 0.0
    grand = round(subtotal + tax + delivery_fee, 2)

    r_name = None
    if cart.restaurant_id:
        r = cart.items[0].dish.restaurant if cart.items else None
        r_name = r.name if r else None

    return CartOut(
        id=cart.id,
        restaurant_id=cart.restaurant_id,
        restaurant_name=r_name,
        items=items_out,
        item_subtotal=round(subtotal, 2),
        delivery_fee=delivery_fee,
        tax_gst=tax,
        grand_total=grand
    )

def checkout_cart(user: User, req: CheckoutRequest, db: Session) -> Order:
    cart = get_or_create_cart(user, db)
    if not cart.items:
        raise HTTPException(status_code=400, detail="Cannot checkout with an empty cart")

    # 1. Recalculate prices from database
    subtotal = 0.0
    for it in cart.items:
        dish = it.dish
        if not dish.is_available or dish.stock_count < it.quantity:
            raise HTTPException(status_code=400, detail=f"Item {dish.name} is no longer in stock")
        subtotal += dish.price * it.quantity
        # Decrement stock
        dish.stock_count = max(0, dish.stock_count - it.quantity)

    # 2. Check coupon
    discount = 0.0
    if req.coupon_code:
        coupon = db.query(Coupon).filter(
            Coupon.code == req.coupon_code.upper(),
            Coupon.is_active == True,
            Coupon.expires_at > datetime.utcnow()
        ).first()
        if coupon and subtotal >= coupon.min_order_amount:
            if coupon.discount_percentage > 0:
                raw_disc = subtotal * (coupon.discount_percentage / 100.0)
                discount = min(raw_disc, coupon.max_discount)
            elif coupon.flat_discount > 0:
                discount = coupon.flat_discount

    tax = round(subtotal * 0.05, 2)
    delivery_fee = 40.0
    grand_total = max(0.0, round(subtotal + tax + delivery_fee - discount, 2))

    # 3. Create Order
    order = Order(
        user_id=user.id,
        restaurant_id=cart.restaurant_id,
        order_type="regular",
        status=OrderStatus.PLACED.value,
        item_subtotal=round(subtotal, 2),
        delivery_fee=delivery_fee,
        tax_gst=tax,
        discount_amount=round(discount, 2),
        grand_total=grand_total,
        delivery_address=req.delivery_address,
        delivery_instructions=req.delivery_instructions,
        payment_method=req.payment_method,
        payment_status="paid" if req.payment_method != "cash_on_delivery" else "pending",
        estimated_prep_min=18,
        estimated_delivery_min=14
    )
    db.add(order)
    db.commit()

    # 4. Create OrderItems
    for it in cart.items:
        oi = OrderItem(
            order_id=order.id,
            dish_id=it.dish_id,
            dish_name=it.dish.name,
            unit_price=it.dish.price,
            quantity=it.quantity,
            subtotal=it.dish.price * it.quantity
        )
        db.add(oi)

    # 5. Timeline record
    t = OrderTimeline(
        order_id=order.id,
        status="placed",
        message=f"Order placed successfully! Payment verified via {req.payment_method}."
    )
    db.add(t)

    # 6. Assign simulated delivery rider
    rider = db.query(User).filter(User.role == UserRole.DELIVERY_PARTNER.value).first()
    if rider:
        da = DeliveryAssignment(order_id=order.id, delivery_partner_id=rider.id, status="assigned", earnings=45.0)
        db.add(da)

    # 7. Clear cart items
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    db.refresh(order)
    return order

VALID_TRANSITIONS = {
    "placed": ["accepted", "rejected", "cancelled"],
    "accepted": ["preparing", "cancelled"],
    "preparing": ["ready_for_pickup", "cancelled"],
    "ready_for_pickup": ["picked_up"],
    "picked_up": ["delivered"],
    "delivered": [],
    "cancelled": [],
    "rejected": []
}

def transition_order_status(order_id: int, new_status: str, reason: Optional[str], db: Session) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    cur = order.status.lower()
    nxt = new_status.lower()
    allowed = VALID_TRANSITIONS.get(cur, [])
    if nxt not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid status transition from '{cur}' to '{nxt}'")

    order.status = nxt
    if nxt == "cancelled":
        order.cancellation_reason = reason or "Cancelled by user"

    # Add timeline entry
    msg_map = {
        "accepted": "Restaurant accepted your order.",
        "preparing": "The chef is freshly preparing your dishes.",
        "ready_for_pickup": "Order packed and waiting for delivery partner pickup.",
        "picked_up": "Delivery partner picked up your order and is en route.",
        "delivered": "Order delivered to your doorstep. Bon appétit!",
        "cancelled": f"Order cancelled. Reason: {reason or 'Customer request'}",
        "rejected": f"Order rejected by restaurant. Reason: {reason or 'Kitchen closed'}"
    }
    t = OrderTimeline(order_id=order.id, status=nxt, message=msg_map.get(nxt, f"Status updated to {nxt}"))
    db.add(t)

    # Update delivery assignment if status is delivered
    if nxt == "delivered" and order.delivery_assignment:
        order.delivery_assignment.status = "delivered"
        order.delivery_assignment.delivered_at = datetime.utcnow()

    db.commit()
    db.refresh(order)
    return order
