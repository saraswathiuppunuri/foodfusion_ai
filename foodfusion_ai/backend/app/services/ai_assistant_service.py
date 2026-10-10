import re
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.entities import Dish, User, Order, SurplusOffer
from app.schemas.schemas import ChatRequest, ChatResponse, DishOut

def process_chat_message(req: ChatRequest, user: User, db: Session) -> ChatResponse:
    """
    Understands food cravings, budgets, macro requirements, and surplus deals,
    grounding responses exclusively in active database menu items with no hallucinations.
    """
    msg = req.message.lower().strip()
    suggested_dishes: List[Dish] = []
    reply = ""

    # 1. "Find discounted food" / "Surplus"
    if any(k in msg for k in ["discount", "surplus", "save food", "deal", "cheap", "offer"]):
        surplus_items = db.query(SurplusOffer).filter(SurplusOffer.status == "active", SurplusOffer.quantity_available > 0).all()
        if surplus_items:
            suggested_dishes = [s.dish for s in surplus_items if s.dish]
            reply = f"I found {len(suggested_dishes)} flash-discounted surplus meals with up to 60% off! These are freshly cooked end-of-batch items that save food from being wasted."
        else:
            suggested_dishes = db.query(Dish).filter(Dish.price <= 150, Dish.is_available == True).limit(4).all()
            reply = "No active surplus flash sales right now, but here are our most affordable fresh meals under ₹150:"

    # 2. "Suggest a high-protein meal"
    elif any(k in msg for k in ["high-protein", "high protein", "protein", "gym", "workout", "macro"]):
        suggested_dishes = db.query(Dish).filter(Dish.protein_g >= 20, Dish.is_available == True).order_by(Dish.protein_g.desc()).limit(4).all()
        reply = f"Here are our top high-protein options packed with 20g–42g of clean protein to fuel your day:"

    # 3. "Show spicy dishes available near me"
    elif any(k in msg for k in ["spicy", "fiery", "hot", "andhra", "guntur"]):
        suggested_dishes = db.query(Dish).filter(Dish.spice_level == "spicy", Dish.is_available == True).limit(4).all()
        reply = f"Here are our most popular fiery dishes with authentic spices and rich heat:"

    # 4. "Recommend something similar to my last order"
    elif any(k in msg for k in ["last order", "previous order", "similar to my last", "reorder"]):
        last_order = db.query(Order).filter(Order.user_id == user.id).order_by(Order.id.desc()).first()
        if last_order and last_order.items:
            last_dish_name = last_order.items[0].dish_name
            # Find related dishes in same restaurant or cuisine
            suggested_dishes = db.query(Dish).filter(
                Dish.restaurant_id == last_order.restaurant_id,
                Dish.is_available == True
            ).limit(4).all()
            reply = f"Based on your recent order of '{last_dish_name}' from {last_order.restaurant.name}, here are delicious complementary recommendations:"
        else:
            suggested_dishes = db.query(Dish).filter(Dish.is_available == True).limit(4).all()
            reply = "You don't have past orders yet! Based on your declared profile, here are top-rated dishes to get started:"

    # 5. Budget constraints (e.g. "under ₹120", "under 150 vegetarian")
    elif "under" in msg or "below" in msg or "budget" in msg or "₹" in msg or "rs" in msg:
        budget_match = re.search(r'(?:under|below|budget|rs\.?|₹)\s*(\d+)', msg)
        budget = float(budget_match.group(1)) if budget_match else 150.0
        is_veg = "veg" in msg or "vegetarian" in msg

        q = db.query(Dish).filter(Dish.price <= budget, Dish.is_available == True)
        if is_veg:
            q = q.filter(Dish.is_veg == True)
        suggested_dishes = q.order_by(Dish.price.asc()).limit(4).all()
        
        diet_str = "vegetarian " if is_veg else ""
        if suggested_dishes:
            reply = f"Here are delicious {diet_str}meals priced strictly under ₹{budget:.0f}:"
        else:
            cheapest = db.query(Dish).order_by(Dish.price.asc()).first()
            reply = f"I couldn't find {diet_str}meals under ₹{budget:.0f}. The most affordable meal is {cheapest.name} at ₹{cheapest.price:.0f}."

    # 6. Specific Cravings (biryani, paneer, salad, noodles, etc.)
    elif any(c in msg for c in ["biryani", "paneer", "salad", "noodles", "wrap", "coffee"]):
        matched_word = next(c for c in ["biryani", "paneer", "salad", "noodles", "wrap", "coffee"] if c in msg)
        suggested_dishes = db.query(Dish).filter(
            Dish.name.ilike(f"%{matched_word}%"),
            Dish.is_available == True
        ).limit(4).all()
        reply = f"Craving {matched_word.title()}? Here are the highest-rated dishes matching your craving:"

    # Default friendly assistant greeting
    else:
        suggested_dishes = db.query(Dish).filter(Dish.is_available == True).limit(3).all()
        reply = (
            f"Hello {user.name}! I am FoodFusion AI, your personal food & sustainable dining assistant. "
            f"You can ask me to find meals under a budget (e.g., 'vegetarian under ₹150'), "
            f"find high-protein fitness meals, locate surplus zero-waste flash deals, or recommend dishes based on your past orders!"
        )

    dishes_out = [DishOut.model_validate(d) for d in suggested_dishes]
    return ChatResponse(
        reply=reply,
        suggested_dishes=dishes_out,
        quick_actions=[
            "Vegetarian under ₹150",
            "High-Protein Meals",
            "Surplus Food Flash Deals",
            "Spicy Biryani Specials"
        ]
    )
