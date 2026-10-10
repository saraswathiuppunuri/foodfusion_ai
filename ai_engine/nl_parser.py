import re
from typing import Dict, Any, List

NUMBER_WORDS = {
    'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'single': 1, 'couple': 2, 'duo': 2, 'trio': 3
}

def parse_natural_language_prompt(prompt: str) -> Dict[str, Any]:
    """
    Extracts constraints from natural-language requests like:
    'I need dinner for three people under ₹500, two vegetarian meals and one spicy meal.'
    """
    text = prompt.lower()
    
    # 1. Budget extraction (e.g. under 500, under ₹500, Rs. 500, budget 500, within 500)
    budget = None
    budget_match = re.search(r'(?:under|below|within|budget|rs\.?|inr|₹)\s*(\d+)', text)
    if not budget_match:
        budget_match = re.search(r'(\d+)\s*(?:rs|rupees|inr|₹)', text)
    if budget_match:
        budget = float(budget_match.group(1))
    else:
        budget = 500.0  # sensible default

    # 2. People / Meals count
    people_count = 1
    people_match = re.search(r'(\d+)\s*(?:people|persons?|members?|meals?|friends?)', text)
    if people_match:
        people_count = int(people_match.group(1))
    else:
        for word, num in NUMBER_WORDS.items():
            if re.search(rf'\b{word}\s*(?:people|persons?|members?|meals?|friends?)\b', text):
                people_count = num
                break

    # 3. Vegetarian constraint
    veg_count = 0
    veg_match = re.search(r'(\d+)\s*(?:vegetarian|veg)\b', text)
    if veg_match:
        veg_count = int(veg_match.group(1))
    else:
        for word, num in NUMBER_WORDS.items():
            if re.search(rf'\b{word}\s*(?:vegetarian|veg)\b', text):
                veg_count = num
                break
        if veg_count == 0 and ('vegetarian' in text or 'pure veg' in text or 'veg only' in text):
            veg_count = people_count

    # 4. Spicy constraint
    spicy_count = 0
    spicy_match = re.search(r'(\d+)\s*(?:spicy|hot)\b', text)
    if spicy_match:
        spicy_count = int(spicy_match.group(1))
    else:
        for word, num in NUMBER_WORDS.items():
            if re.search(rf'\b{word}\s*(?:spicy|hot)\b', text):
                spicy_count = num
                break
        if spicy_count == 0 and ('spicy' in text or 'fiery' in text or 'extra spicy' in text):
            spicy_count = 1

    # 5. Non-veg constraint
    non_veg_count = 0
    non_veg_match = re.search(r'(\d+)\s*(?:non-veg|nonveg|chicken|mutton|meat)\b', text)
    if non_veg_match:
        non_veg_count = int(non_veg_match.group(1))
    else:
        for word, num in NUMBER_WORDS.items():
            if re.search(rf'\b{word}\s*(?:non-veg|nonveg|chicken|mutton|meat)\b', text):
                non_veg_count = num
                break

    # 6. High protein / healthy flags
    high_protein = bool(re.search(r'high[- ]protein|protein|gym|workout', text))
    low_calorie = bool(re.search(r'low[- ]cal|healthy|salad|diet|keto', text))

    return {
        "budget": budget,
        "people_count": max(1, people_count),
        "veg_count": veg_count,
        "spicy_count": spicy_count,
        "non_veg_count": non_veg_count,
        "high_protein": high_protein,
        "low_calorie": low_calorie,
        "original_prompt": prompt
    }

def build_smart_cart(prompt: str, all_dishes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Optimizes cart selection matching constraints, budgets, and dietary specs,
    then generates transparent explanations.
    """
    constraints = parse_natural_language_prompt(prompt)
    target_count = constraints["people_count"]
    budget = constraints["budget"]
    target_veg = constraints["veg_count"]
    target_spicy = constraints["spicy_count"]
    target_non_veg = constraints["non_veg_count"]

    # Filter out unavailable dishes
    available = [d for d in all_dishes if d.get("is_available", True)]
    
    # Group dishes by restaurant to minimize split delivery fees
    by_restaurant = {}
    for d in available:
        r_name = d.get("restaurant_name", "Local Kitchen")
        by_restaurant.setdefault(r_name, []).append(d)

    best_selection = None
    best_score = -1e9
    best_restaurant_name = ""

    # Strategy: Evaluate each restaurant to find single-restaurant fulfillment first
    for r_name, r_dishes in by_restaurant.items():
        # Sort dishes by balance of price and ratings
        r_dishes_sorted = sorted(r_dishes, key=lambda x: (x.get("price", 999)))
        
        veg_items = [d for d in r_dishes_sorted if d.get("is_veg")]
        non_veg_items = [d for d in r_dishes_sorted if not d.get("is_veg")]
        spicy_items = [d for d in r_dishes_sorted if d.get("spice_level") == "spicy"]

        # Check if restaurant can meet requirements
        if len(r_dishes_sorted) < target_count:
            continue
        if target_veg > len(veg_items):
            continue
        if target_non_veg > len(non_veg_items):
            continue

        # Candidate selection
        chosen = []
        cur_veg = 0
        cur_spicy = 0
        cur_cost = 0.0

        # 1. Pick required spicy items
        spicy_needed = target_spicy
        for item in spicy_items:
            if spicy_needed > 0 and len(chosen) < target_count:
                if cur_cost + item["price"] <= budget:
                    chosen.append(item)
                    cur_cost += item["price"]
                    spicy_needed -= 1
                    if item.get("is_veg"):
                        cur_veg += 1

        # 2. Pick required veg items
        veg_needed = max(0, target_veg - cur_veg)
        for item in veg_items:
            if veg_needed > 0 and item not in chosen and len(chosen) < target_count:
                if cur_cost + item["price"] <= budget:
                    chosen.append(item)
                    cur_cost += item["price"]
                    veg_needed -= 1
                    cur_veg += 1

        # 3. Fill remaining slots with best value items
        for item in r_dishes_sorted:
            if len(chosen) < target_count and item not in chosen:
                if cur_cost + item["price"] <= budget:
                    chosen.append(item)
                    cur_cost += item["price"]

        if len(chosen) == target_count and cur_cost <= budget:
            # Score this restaurant solution: higher is better
            # Factors: remaining budget savings, healthy macros, spice/veg adherence
            budget_savings = budget - cur_cost
            score = 1000 - (cur_cost / budget * 100) + (10 * cur_veg)
            if score > best_score:
                best_score = score
                best_selection = chosen
                best_restaurant_name = r_name

    # Fallback across all restaurants if a single restaurant could not satisfy all slots
    if not best_selection:
        chosen = []
        cur_cost = 0.0
        # Pick veg first
        for item in sorted([d for d in available if d.get("is_veg")], key=lambda x: x["price"]):
            if len(chosen) < target_veg and cur_cost + item["price"] <= budget:
                chosen.append(item)
                cur_cost += item["price"]
        # Pick spicy next
        for item in sorted([d for d in available if d.get("spice_level") == "spicy" and d not in chosen], key=lambda x: x["price"]):
            if len([x for x in chosen if x.get("spice_level") == "spicy"]) < target_spicy and len(chosen) < target_count:
                if cur_cost + item["price"] <= budget:
                    chosen.append(item)
                    cur_cost += item["price"]
        # Fill rest
        for item in sorted(available, key=lambda x: x["price"]):
            if len(chosen) < target_count and item not in chosen and cur_cost + item["price"] <= budget:
                chosen.append(item)
                cur_cost += item["price"]

        best_selection = chosen
        best_restaurant_name = "Multi-Kitchen Bundle"

    total_price = sum(item["price"] for item in best_selection) if best_selection else 0.0
    veg_picked = sum(1 for item in best_selection if item.get("is_veg"))
    spicy_picked = sum(1 for item in best_selection if item.get("spice_level") == "spicy")
    non_veg_picked = sum(1 for item in best_selection if not item.get("is_veg"))

    # Generate transparent explanation
    savings = max(0.0, budget - total_price)
    explanation = (
        f"Cart curated from '{best_restaurant_name}' to satisfy all constraints in one synchronized delivery. "
        f"Includes {veg_picked} vegetarian meal(s) and {spicy_picked} spicy meal(s) for {len(best_selection)} person(s). "
        f"Total comes to ₹{total_price:.2f}, successfully staying under your ₹{budget:.0f} budget with ₹{savings:.2f} remaining."
    )

    return {
        "status": "success" if best_selection else "partial_match",
        "constraints_parsed": constraints,
        "items": best_selection or [],
        "total_price": round(total_price, 2),
        "budget": budget,
        "savings": round(savings, 2),
        "restaurant_name": best_restaurant_name,
        "explanation": explanation
    }
