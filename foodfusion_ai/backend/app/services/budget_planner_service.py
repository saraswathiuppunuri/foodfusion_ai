from typing import List
from sqlalchemy.orm import Session
from app.models.entities import Dish, Restaurant
from app.schemas.schemas import (
    BudgetPlannerRequest, BudgetPlannerResponse, BudgetPlannerCombo, DishOut
)

def plan_budget_meals(req: BudgetPlannerRequest, db: Session) -> BudgetPlannerResponse:
    """
    Generates exact constraint-satisfying meal combos that do not exceed the customer's budget,
    accounting for food prices, 5% GST, and delivery fees.
    """
    max_budget = req.max_budget
    query = db.query(Dish).filter(Dish.is_available == True)
    if req.is_veg_only:
        query = query.filter(Dish.is_veg == True)
    if req.spice_preference:
        query = query.filter(Dish.spice_level == req.spice_preference)
    
    all_dishes = query.all()
    if not all_dishes:
        return BudgetPlannerResponse(
            status="no_dishes",
            max_budget=max_budget,
            combos=[],
            message="No active dishes found matching the specified dietary filters."
        )

    DELIVERY_FEE = 40.0
    TAX_RATE = 0.05
    combos: List[BudgetPlannerCombo] = []

    # 1. Single Dish + Delivery Combos
    for dish in all_dishes:
        subtotal = dish.price
        tax = round(subtotal * TAX_RATE, 2)
        grand_total = round(subtotal + tax + DELIVERY_FEE, 2)
        if grand_total <= max_budget:
            remaining = round(max_budget - grand_total, 2)
            r_name = dish.restaurant.name if dish.restaurant else "Local Kitchen"
            combos.append(BudgetPlannerCombo(
                items=[DishOut.model_validate(dish)],
                item_subtotal=subtotal,
                estimated_tax=tax,
                estimated_delivery=DELIVERY_FEE,
                grand_total=grand_total,
                remaining_budget=remaining,
                restaurant_name=r_name,
                reason=f"Complete solo meal ({dish.calories} kcal, {dish.protein_g}g protein) delivered to your door with ₹{remaining:.2f} to spare."
            ))

    # 2. Multi-dish Combos from same restaurant (Main + Bread/Drink)
    # Group by restaurant
    by_rest = {}
    for d in all_dishes:
        by_rest.setdefault(d.restaurant_id, []).append(d)

    for rest_id, r_dishes in by_rest.items():
        if len(r_dishes) >= 2:
            for i in range(len(r_dishes)):
                for j in range(i + 1, len(r_dishes)):
                    d1, d2 = r_dishes[i], r_dishes[j]
                    subtotal = d1.price + d2.price
                    tax = round(subtotal * TAX_RATE, 2)
                    grand_total = round(subtotal + tax + DELIVERY_FEE, 2)
                    if grand_total <= max_budget:
                        remaining = round(max_budget - grand_total, 2)
                        r_name = d1.restaurant.name if d1.restaurant else "Local Kitchen"
                        combos.append(BudgetPlannerCombo(
                            items=[DishOut.model_validate(d1), DishOut.model_validate(d2)],
                            item_subtotal=subtotal,
                            estimated_tax=tax,
                            estimated_delivery=DELIVERY_FEE,
                            grand_total=grand_total,
                            remaining_budget=remaining,
                            restaurant_name=r_name,
                            reason=f"2-item pairing combining {d1.name} and {d2.name} from {r_name} staying ₹{remaining:.2f} under budget."
                        ))

    # Sort combos by best value (closest to budget without exceeding, and highest protein)
    combos.sort(key=lambda c: (sum(it.protein_g for it in c.items), -c.remaining_budget), reverse=True)

    if combos:
        return BudgetPlannerResponse(
            status="success",
            max_budget=max_budget,
            combos=combos[:5],
            message=f"Found {len(combos)} delicious meal combinations strictly under your ₹{max_budget:.0f} budget (including taxes & delivery)!"
        )

    # If no delivery combination was possible under the tight budget (e.g. ₹150)
    # Offer Pickup/Takeaway options (₹0 delivery fee) or closest alternative
    pickup_combos = []
    for dish in all_dishes:
        subtotal = dish.price
        tax = round(subtotal * TAX_RATE, 2)
        pickup_total = round(subtotal + tax, 2)
        if pickup_total <= max_budget:
            remaining = round(max_budget - pickup_total, 2)
            r_name = dish.restaurant.name if dish.restaurant else "Local Kitchen"
            pickup_combos.append(BudgetPlannerCombo(
                items=[DishOut.model_validate(dish)],
                item_subtotal=subtotal,
                estimated_tax=tax,
                estimated_delivery=0.0,
                grand_total=pickup_total,
                remaining_budget=remaining,
                restaurant_name=r_name,
                reason=f"Pickup / Takeaway Option: ₹0 delivery fee allows {dish.name} to comfortably fit your ₹{max_budget:.0f} budget!"
            ))

    if pickup_combos:
        return BudgetPlannerResponse(
            status="pickup_alternative",
            max_budget=max_budget,
            combos=pickup_combos[:4],
            message=(
                f"Standard home delivery includes a ₹40 fee + 5% GST, which exceeds ₹{max_budget:.0f} for delivered meals. "
                f"However, we found {len(pickup_combos)} delicious Takeaway/Pickup meals that fit your budget with zero delivery fees!"
            )
        )

    # Total fallback: closest available meal
    cheapest = min(all_dishes, key=lambda d: d.price)
    min_subtotal = cheapest.price
    min_tax = round(min_subtotal * TAX_RATE, 2)
    min_total = round(min_subtotal + min_tax + DELIVERY_FEE, 2)
    r_name = cheapest.restaurant.name if cheapest.restaurant else "Local Kitchen"

    return BudgetPlannerResponse(
        status="budget_exceeded",
        max_budget=max_budget,
        combos=[BudgetPlannerCombo(
            items=[DishOut.model_validate(cheapest)],
            item_subtotal=min_subtotal,
            estimated_tax=min_tax,
            estimated_delivery=DELIVERY_FEE,
            grand_total=min_total,
            remaining_budget=round(max_budget - min_total, 2),
            restaurant_name=r_name,
            reason=f"Lowest-priced available dish on the platform is {cheapest.name} (Total: ₹{min_total:.2f})."
        )],
        message=(
            f"The lowest-cost delivered meal on the platform is ₹{min_total:.2f} (Food: ₹{min_subtotal} + Tax: ₹{min_tax} + Delivery: ₹{DELIVERY_FEE}). "
            f"To place an order, please increase your budget by ₹{round(min_total - max_budget, 2)} or choose Takeaway pickup."
        )
    )
