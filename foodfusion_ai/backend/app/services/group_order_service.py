import random
import string
from typing import Dict, Any, List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.entities import (
    GroupOrderSession, GroupOrderParticipant, GroupOrderItem, 
    Restaurant, Dish, Order, OrderItem, OrderTimeline, OrderStatus, User
)
from app.schemas.schemas import GroupOrderOut, GroupParticipantShare

def generate_join_code() -> str:
    digits = ''.join(random.choices(string.digits, k=4))
    return f"FOOD-{digits}"

def create_group_session(host_user: User, restaurant_id: int, total_budget: float, db: Session) -> GroupOrderSession:
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")

    code = generate_join_code()
    session = GroupOrderSession(
        join_code=code,
        host_user_id=host_user.id,
        restaurant_id=restaurant_id,
        total_budget=total_budget,
        status="open"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Automatically add host as participant #1
    host_participant = GroupOrderParticipant(
        session_id=session.id,
        user_name=f"{host_user.name} (Host)",
        user_id=host_user.id,
        personal_budget=300.0,
        diet_pref=host_user.dietary_preference or "any"
    )
    db.add(host_participant)
    db.commit()
    return session

def join_group_session(join_code: str, user_name: str, personal_budget: float, diet_pref: str, db: Session, user: User = None) -> GroupOrderParticipant:
    session = db.query(GroupOrderSession).filter(GroupOrderSession.join_code == join_code.upper()).first()
    if not session:
        raise HTTPException(status_code=404, detail="Group order session not found with this join code")
    if session.status != "open":
        raise HTTPException(status_code=400, detail="This group order session is locked or already placed")

    participant = GroupOrderParticipant(
        session_id=session.id,
        user_name=user_name,
        user_id=user.id if user else None,
        personal_budget=personal_budget,
        diet_pref=diet_pref
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant

def add_dish_to_participant(participant_id: int, dish_id: int, quantity: int, db: Session):
    participant = db.query(GroupOrderParticipant).filter(GroupOrderParticipant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    if participant.session.status != "open":
        raise HTTPException(status_code=400, detail="Session is locked")

    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish or dish.restaurant_id != participant.session.restaurant_id:
        raise HTTPException(status_code=400, detail="Dish must belong to the selected group restaurant")

    existing_item = db.query(GroupOrderItem).filter(
        GroupOrderItem.participant_id == participant_id,
        GroupOrderItem.dish_id == dish_id
    ).first()

    if existing_item:
        existing_item.quantity += quantity
    else:
        new_item = GroupOrderItem(
            participant_id=participant_id,
            dish_id=dish_id,
            quantity=quantity
        )
        db.add(new_item)
    db.commit()

def calculate_group_order_summary(session_id: int, db: Session) -> GroupOrderOut:
    session = db.query(GroupOrderSession).filter(GroupOrderSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    participants = session.participants
    participant_count = len(participants) or 1
    total_food = 0.0

    raw_shares = []
    for p in participants:
        p_items = []
        p_subtotal = 0.0
        for it in p.items:
            dish = it.dish
            cost = dish.price * it.quantity
            p_subtotal += cost
            p_items.append({
                "dish_id": dish.id,
                "dish_name": dish.name,
                "price": dish.price,
                "quantity": it.quantity,
                "subtotal": cost,
                "is_veg": dish.is_veg
            })
        total_food += p_subtotal
        raw_shares.append((p, p_items, p_subtotal))

    # Shared costs: 5% GST + fixed ₹40 delivery fee
    total_tax = round(total_food * 0.05, 2)
    total_delivery = 40.0 if total_food > 0 else 0.0
    shared_delivery_per_person = round(total_delivery / participant_count, 2)
    grand_total = round(total_food + total_tax + total_delivery, 2)

    participant_shares = []
    for p, items, subtotal in raw_shares:
        tax_share = round(subtotal * 0.05, 2)
        final_payable = round(subtotal + tax_share + shared_delivery_per_person, 2)
        is_ok = final_payable <= p.personal_budget

        participant_shares.append(GroupParticipantShare(
            participant_name=p.user_name,
            items=items,
            food_subtotal=subtotal,
            tax_share=tax_share,
            delivery_share=shared_delivery_per_person,
            final_share=final_payable,
            personal_budget=p.personal_budget,
            is_within_budget=is_ok
        ))

    is_group_ok = grand_total <= session.total_budget
    summary = (
        f"Group order contains {len(participant_shares)} participants. "
        f"Food Total: ₹{total_food:.2f} + GST: ₹{total_tax:.2f} + Delivery: ₹{total_delivery:.2f} = Grand Total: ₹{grand_total:.2f}. "
        f"Group is ₹{abs(session.total_budget - grand_total):.2f} {'under' if is_group_ok else 'over'} total budget."
    )

    r_name = session.restaurant.name if session.restaurant else "Group Restaurant"
    return GroupOrderOut(
        session_id=session.id,
        join_code=session.join_code,
        restaurant_name=r_name,
        status=session.status,
        total_budget=session.total_budget,
        combined_grand_total=grand_total,
        combined_food_total=total_food,
        total_tax=total_tax,
        total_delivery=total_delivery,
        participants=participant_shares,
        is_group_within_budget=is_group_ok,
        summary=summary
    )

def place_group_order(session_id: int, host_user: User, delivery_address: str, db: Session) -> Order:
    session = db.query(GroupOrderSession).filter(GroupOrderSession.id == session_id).with_for_update().first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.host_user_id != host_user.id:
        raise HTTPException(status_code=403, detail="Only the host organizer can lock and place this group order")
    if session.status == "placed":
        raise HTTPException(status_code=400, detail="This group order was already submitted")

    summary = calculate_group_order_summary(session_id, db)
    if summary.combined_food_total <= 0:
        raise HTTPException(status_code=400, detail="Cannot place an empty group order")

    # Lock session to prevent duplicate submissions
    session.status = "placed"

    # Create Order
    new_order = Order(
        user_id=host_user.id,
        restaurant_id=session.restaurant_id,
        order_type="group",
        status=OrderStatus.PLACED.value,
        item_subtotal=summary.combined_food_total,
        delivery_fee=summary.total_delivery,
        tax_gst=summary.total_tax,
        discount_amount=0.0,
        grand_total=summary.combined_grand_total,
        delivery_address=delivery_address,
        payment_method="demo_upi",
        payment_status="paid",
        estimated_prep_min=25,
        estimated_delivery_min=18
    )
    db.add(new_order)
    db.commit()

    # Add items
    for p in summary.participants:
        for it in p.items:
            oi = OrderItem(
                order_id=new_order.id,
                dish_id=it["dish_id"],
                dish_name=f"[{p.participant_name}] {it['dish_name']}",
                unit_price=it["price"],
                quantity=it["quantity"],
                subtotal=it["subtotal"]
            )
            db.add(oi)

    t = OrderTimeline(
        order_id=new_order.id,
        status="placed",
        message=f"Group order placed by {host_user.name} for {len(summary.participants)} members."
    )
    db.add(t)
    db.commit()
    db.refresh(new_order)
    return new_order
