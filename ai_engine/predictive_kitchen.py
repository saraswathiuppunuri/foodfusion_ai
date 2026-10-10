import random
import datetime
from typing import List, Dict, Any

def predict_order_timings(item_count: int, distance_km: float = 3.2, current_kitchen_queue: int = 4, is_peak_hour: bool = False) -> Dict[str, Any]:
    """
    Estimates preparation time, transit delivery time, and flags potential delay risks.
    """
    # 1. Base prep calculation
    base_prep = 12.0
    item_overhead = item_count * 2.5
    queue_overhead = current_kitchen_queue * 1.8
    peak_multiplier = 1.3 if is_peak_hour else 1.0

    predicted_prep = int(round((base_prep + item_overhead + queue_overhead) * peak_multiplier))
    
    # 2. Transit time calculation (avg speed 20km/h in city + 4 min parking/handover)
    transit_speed_kmh = 18.0 if is_peak_hour else 25.0
    transit_minutes = int(round((distance_km / transit_speed_kmh) * 60 + 4))
    
    total_eta = predicted_prep + transit_minutes

    # 3. Delay risk detection
    is_delayed = False
    delay_reason = None
    if current_kitchen_queue > 6:
        is_delayed = True
        delay_reason = f"High kitchen ticket load ({current_kitchen_queue} active orders in station queue)"
    elif is_peak_hour and distance_km > 5.0:
        is_delayed = True
        delay_reason = f"Heavy peak-hour road traffic on delivery corridor ({distance_km:.1f} km)"

    return {
        "predicted_prep_min": predicted_prep,
        "predicted_delivery_min": transit_minutes,
        "total_eta_min": total_eta,
        "distance_km": round(distance_km, 1),
        "is_delayed": is_delayed,
        "delay_reason": delay_reason,
        "kitchen_queue_load": "High" if current_kitchen_queue > 5 else ("Medium" if current_kitchen_queue > 2 else "Low")
    }

def generate_analytics_data() -> Dict[str, Any]:
    """
    Generates rich time-series and aggregate analytics data for Chart.js dashboard.
    """
    # 1. Hourly order distribution (10 AM to 11 PM)
    hours = ["10 AM", "12 PM", "2 PM", "4 PM", "6 PM", "8 PM", "10 PM"]
    regular_orders = [18, 54, 82, 28, 45, 96, 62]
    surplus_orders = [5, 14, 28, 12, 19, 42, 31]

    # 2. Food Waste Reduction Metrics (Past 7 days)
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    waste_saved_kg = [14.2, 18.5, 16.0, 22.4, 29.8, 38.5, 41.2]
    waste_discarded_kg = [4.1, 3.2, 2.8, 3.5, 2.1, 1.8, 1.4] # Drastic drop thanks to AI

    # 3. Financial Impact: Revenue Recovered via Surplus
    revenue_recovered = [2150, 2840, 2600, 3400, 4800, 6200, 6950]

    # 4. On-Time vs Delayed Delivery performance
    performance = {
        "on_time_pct": 92.4,
        "minor_delay_pct": 5.8,
        "critical_delay_pct": 1.8
    }

    # 5. Top Saved Surplus Categories
    categories = ["Biryani & Rice", "Breads & Naan", "Curries & Gravies", "Salads & Cold Bowls", "Bakery & Desserts"]
    category_kg = [52.4, 38.1, 46.2, 21.0, 18.5]

    return {
        "hourly_labels": hours,
        "hourly_regular": regular_orders,
        "hourly_surplus": surplus_orders,
        "days": days,
        "waste_saved_kg": waste_saved_kg,
        "waste_discarded_kg": waste_discarded_kg,
        "revenue_recovered": revenue_recovered,
        "total_waste_saved_kg": round(sum(waste_saved_kg), 1),
        "total_revenue_recovered_inr": sum(revenue_recovered),
        "total_co2_prevented_kg": round(sum(waste_saved_kg) * 2.5, 1),
        "performance": performance,
        "categories": categories,
        "category_kg": category_kg
    }
