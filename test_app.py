import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from app import app

def run_tests():
    client = app.test_client()

    print("[*] Testing Web Template Pages...")
    routes = ['/', '/surplus', '/group', '/fridge', '/analytics', '/map']
    for route in routes:
        res = client.get(route)
        if res.status_code != 200:
            print(f"[FAIL] Route {route} returned {res.status_code}")
            sys.exit(1)
        print(f"  [OK] {route} -> 200 OK")

    print("\n[*] Testing Feature 1: AI Natural-Language Ordering...")
    prompt = "I need dinner for three people under ₹500, two vegetarian meals and one spicy meal."
    nl_res = client.post('/api/nl-order', json={'prompt': prompt})
    assert nl_res.status_code == 200
    nl_data = nl_res.get_json()
    assert nl_data['status'] == 'success'
    print(f"  [OK] Cart Items Chosen: {[it['name'] for it in nl_data['items']]}")
    print(f"  [OK] Total Price: ₹{nl_data['total_price']} (Budget: ₹{nl_data['budget']})")
    print(f"  [OK] AI Explanation: {nl_data['explanation']}")

    print("\n[*] Testing Feature 2: Smart Surplus Food Marketplace...")
    surplus_res = client.get('/api/surplus')
    assert surplus_res.status_code == 200
    deals = surplus_res.get_json()['deals']
    print(f"  [OK] Active Surplus Deals Found: {len(deals)}")

    print("\n[*] Testing Feature 3: AI Group Order Optimizer...")
    grp_res = client.post('/api/group-optimize', json={'members': [
        {'name': 'Rahul', 'budget': 200, 'diet_preference': 'veg', 'spice_preference': 'mild'},
        {'name': 'Priya', 'budget': 250, 'diet_preference': 'non-veg', 'spice_preference': 'spicy'},
        {'name': 'Amit', 'budget': 180, 'diet_preference': 'veg', 'spice_preference': 'medium'}
    ]})
    assert grp_res.status_code == 200
    grp_data = grp_res.get_json()
    print(f"  [OK] Group Grand Total: ₹{grp_data['grand_total']}")
    print(f"  [OK] Split Summary: {grp_data['summary']}")

    print("\n[*] Testing Feature 4: Scikit-learn Explainable Recommendations...")
    rec_res = client.get('/api/recommendations')
    assert rec_res.status_code == 200
    recs = rec_res.get_json()['recommendations']
    print(f"  [OK] Recommended {len(recs)} meals via TF-IDF + Cosine Similarity.")
    print(f"  [OK] Top Pick: {recs[0]['name']} ({recs[0]['match_score']}% Match)")
    print(f"  [OK] Reasoning: {recs[0]['explanation']}")

    print("\n[*] Testing Feature 5: Predictive Kitchen & Waste Analytics...")
    ana_res = client.get('/api/analytics')
    assert ana_res.status_code == 200
    ana_data = ana_res.get_json()['data']
    print(f"  [OK] Total Waste Rescued: {ana_data['total_waste_saved_kg']} kg")
    print(f"  [OK] Revenue Recovered: ₹{ana_data['total_revenue_recovered_inr']}")

    print("\n[*] Testing Unique Twist: Fridge Vision & Cook vs. Order Comparison...")
    fv_res = client.post('/api/fridge-vision', json={'sample': 'default'})
    assert fv_res.status_code == 200
    fv_data = fv_res.get_json()
    print(f"  [OK] Detected Ingredients: {[i['name'] for i in fv_data['detected_ingredients']]}")
    print(f"  [OK] Cook Home: {fv_data['comparison']['cook_at_home']['total_time_min']} mins (₹{fv_data['comparison']['cook_at_home']['total_estimated_cost']})")
    print(f"  [OK] Order Delivery: {fv_data['comparison']['order_delivery']['total_time_min']} mins (₹{fv_data['comparison']['order_delivery']['total_cost_inr']})")
    print(f"  [OK] Verdict: {fv_data['comparison']['verdict']}")

    print("\n============================================================")
    print(" ⭐ ALL SUITES PASSED! READY FOR HACKATHON DEMO & EVALUATION")
    print("============================================================")

if __name__ == '__main__':
    run_tests()
