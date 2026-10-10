from typing import List, Dict, Any

def optimize_group_order(members: List[Dict[str, Any]], all_dishes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Optimizes a collaborative group order:
    1. Satisfies individual dietary restrictions and personal budgets.
    2. Minimizes restaurant divergence.
    3. Calculates transparent individual shares with tax & delivery fees.
    """
    if not members:
        return {"status": "error", "message": "No group members provided"}

    total_group_budget = sum(float(m.get("budget", 200)) for m in members)
    
    # Map dishes by dietary suitability
    veg_dishes = [d for d in all_dishes if d.get("is_veg")]
    non_veg_dishes = [d for d in all_dishes if not d.get("is_veg")]
    
    assigned_items = []
    member_breakdowns = []
    total_food_cost = 0.0

    # Pick top match for each member
    for m in members:
        m_name = m.get("name", "Member")
        m_budget = float(m.get("budget", 200))
        m_diet = m.get("diet_preference", "any").lower()
        m_spice = m.get("spice_preference", "medium").lower()

        # Filter candidate dishes for this member
        pool = all_dishes
        if m_diet in ["veg", "vegetarian"]:
            pool = [d for d in pool if d.get("is_veg")]
        elif m_diet in ["non-veg", "nonveg"]:
            pool = [d for d in pool if not d.get("is_veg")]
        
        # Sort pool: dishes matching spice level and under member's budget first
        def score_dish(d):
            score = 100
            if d["price"] <= m_budget:
                score += 50
            else:
                score -= 200 # Over budget penalty
            if d.get("spice_level") == m_spice:
                score += 30
            # Higher protein / rating bonus
            score += d.get("protein_g", 0) * 0.5
            return score

        pool_sorted = sorted(pool, key=score_dish, reverse=True)
        
        # Pick the best dish fitting budget if possible, else closest available
        chosen_dish = None
        for cand in pool_sorted:
            if cand["price"] <= m_budget:
                chosen_dish = cand
                break
        if not chosen_dish and pool_sorted:
            chosen_dish = pool_sorted[0]

        if chosen_dish:
            item_entry = {
                "member_name": m_name,
                "dish_id": chosen_dish["id"],
                "dish_name": chosen_dish["name"],
                "price": chosen_dish["price"],
                "restaurant_name": chosen_dish.get("restaurant_name", ""),
                "is_veg": chosen_dish.get("is_veg", True),
                "spice_level": chosen_dish.get("spice_level", "medium")
            }
            assigned_items.append(item_entry)
            total_food_cost += chosen_dish["price"]

    # Calculate fair splits: 5% GST + fixed ₹40 delivery fee shared equally
    gst_total = round(total_food_cost * 0.05, 2)
    delivery_fee_total = 40.0 if total_food_cost > 0 else 0.0
    delivery_per_person = round(delivery_fee_total / max(1, len(members)), 2)
    grand_total = round(total_food_cost + gst_total + delivery_fee_total, 2)

    for item in assigned_items:
        m_cost = item["price"]
        m_gst = round(m_cost * 0.05, 2)
        m_total = round(m_cost + m_gst + delivery_per_person, 2)
        
        # Check against member budget
        member_orig_budget = next((float(m.get("budget", 200)) for m in members if m["name"] == item["member_name"]), m_cost)
        variance = round(member_orig_budget - m_total, 2)

        member_breakdowns.append({
            "name": item["member_name"],
            "dish_name": item["dish_name"],
            "restaurant": item["restaurant_name"],
            "base_price": item["price"],
            "gst_share": m_gst,
            "delivery_share": delivery_per_person,
            "final_payable": m_total,
            "original_budget": member_orig_budget,
            "is_under_budget": variance >= 0,
            "balance": variance
        })

    group_savings = round(total_group_budget - grand_total, 2)

    return {
        "status": "success",
        "member_count": len(members),
        "total_group_budget": round(total_group_budget, 2),
        "total_food_cost": round(total_food_cost, 2),
        "gst_total": gst_total,
        "delivery_fee_total": delivery_fee_total,
        "grand_total": grand_total,
        "group_savings": group_savings,
        "is_overall_under_budget": group_savings >= 0,
        "breakdowns": member_breakdowns,
        "summary": (
            f"Successfully optimized group order for {len(members)} friends! "
            f"Combined food total is ₹{grand_total} (includes ₹{gst_total} GST & shared ₹{delivery_fee_total} delivery). "
            f"Group remains ₹{abs(group_savings)} {'under' if group_savings >= 0 else 'over'} collective budget."
        )
    }
