import datetime
from typing import List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.entities import SurplusOffer, Dish, Restaurant, Order, OrderItem, OrderTimeline, OrderStatus, User
from app.schemas.schemas import SurplusOfferOut, SurplusOfferCreate

def get_active_surplus_offers(db: Session) -> List[SurplusOfferOut]:
    """Retrieves all active surplus food offers before deadline with positive stock."""
    now = datetime.datetime.utcnow()
    offers = db.query(SurplusOffer).filter(
        SurplusOffer.status == "active",
        SurplusOffer.quantity_available > 0,
        SurplusOffer.offer_expires_at > now
    ).all()

    result = []
    for off in offers:
        remaining_min = max(0, int((off.offer_expires_at - now).total_seconds() / 60))
        discount_pct = int(((off.original_price - off.discounted_price) / off.original_price) * 100) if off.original_price else 0
        r = off.restaurant
        d = off.dish
        result.append(SurplusOfferOut(
            id=off.id,
            restaurant_id=off.restaurant_id,
            restaurant_name=r.name if r else "Kitchen Partner",
            restaurant_address=r.address if r else "Bengaluru",
            dish_id=off.dish_id,
            dish_name=d.name if d else "Surplus Meal",
            dish_image_url=d.image_url if d else None,
            is_veg=d.is_veg if d else True,
            original_price=off.original_price,
            discounted_price=off.discounted_price,
            discount_percentage=discount_pct,
            quantity_available=off.quantity_available,
            waste_saved_kg=off.waste_saved_kg,
            co2_saved_kg=off.co2_saved_kg,
            offer_expires_at=off.offer_expires_at,
            remaining_minutes=remaining_min,
            status=off.status
        ))
    return result

def create_surplus_offer_by_owner(owner_user: User, data: SurplusOfferCreate, db: Session) -> SurplusOffer:
    """Allows restaurant owners to list freshly made end-of-batch surplus food at a discount."""
    dish = db.query(Dish).filter(Dish.id == data.dish_id).first()
    if not dish:
        raise HTTPException(status_code=404, detail="Dish not found")
    
    # Verify owner owns this restaurant (or is admin)
    if owner_user.role != "admin" and dish.restaurant.owner_id != owner_user.id:
        raise HTTPException(status_code=403, detail="You can only list surplus for your own restaurant")

    now = datetime.datetime.utcnow()
    expires_at = now + datetime.timedelta(hours=data.expiry_hours)
    waste_kg = round(data.quantity_available * 0.45, 2)
    co2_kg = round(data.quantity_available * 1.15, 2)

    new_offer = SurplusOffer(
        restaurant_id=dish.restaurant_id,
        dish_id=dish.id,
        original_price=dish.price,
        discounted_price=data.discounted_price,
        quantity_available=data.quantity_available,
        waste_saved_kg=waste_kg,
        co2_saved_kg=co2_kg,
        offer_expires_at=expires_at,
        status="active"
    )
    db.add(new_offer)
    db.commit()
    db.refresh(new_offer)
    return new_offer

def reserve_surplus_offer(user: User, offer_id: int, db: Session) -> Order:
    """Safely reserves a surplus meal, decrements inventory, and places an order."""
    now = datetime.datetime.utcnow()
    offer = db.query(SurplusOffer).filter(SurplusOffer.id == offer_id).with_for_update().first()
    if not offer:
        raise HTTPException(status_code=404, detail="Surplus offer not found")
    
    if offer.status != "active" or offer.quantity_available <= 0:
        raise HTTPException(status_code=400, detail="This surplus meal is already sold out.")

    if offer.offer_expires_at <= now:
        offer.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="This surplus offer has expired.")

    # Decrement stock safely
    offer.quantity_available -= 1
    if offer.quantity_available == 0:
        offer.status = "sold_out"

    # Create Order
    tax = round(offer.discounted_price * 0.05, 2)
    delivery_fee = 0.0 # Free delivery for surplus rescue deals
    grand_total = round(offer.discounted_price + tax + delivery_fee, 2)

    order = Order(
        user_id=user.id,
        restaurant_id=offer.restaurant_id,
        order_type="surplus",
        status=OrderStatus.PREPARING.value,
        item_subtotal=offer.discounted_price,
        delivery_fee=delivery_fee,
        tax_gst=tax,
        discount_amount=round(offer.original_price - offer.discounted_price, 2),
        grand_total=grand_total,
        delivery_address="Customer Doorstep (Rescue Delivery)",
        payment_method="demo_upi",
        payment_status="paid",
        estimated_prep_min=10,
        estimated_delivery_min=14
    )
    db.add(order)
    db.commit()

    # Order item & timeline
    oi = OrderItem(
        order_id=order.id,
        dish_id=offer.dish_id,
        dish_name=f"[Surplus Rescue] {offer.dish.name}",
        unit_price=offer.discounted_price,
        quantity=1,
        subtotal=offer.discounted_price
    )
    t = OrderTimeline(
        order_id=order.id,
        status="preparing",
        message=f"Surplus food rescued! You saved 0.45 kg of fresh food and ₹{round(offer.original_price - offer.discounted_price, 2)}."
    )
    db.add_all([oi, t])
    db.commit()
    db.refresh(order)
    return order
