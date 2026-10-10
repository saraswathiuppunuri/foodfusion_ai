import os
import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
from config import Config
from database import init_db, get_db, Restaurant, Dish, SurplusDeal, Order, OrderItem, UserProfile
from ai_engine.nl_parser import build_smart_cart
from ai_engine.group_optimizer import optimize_group_order
from ai_engine.recommender import train_and_recommend
from ai_engine.predictive_kitchen import predict_order_timings, generate_analytics_data
from ai_engine.vision_fridge import analyze_fridge_image

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Initialize database on startup
with app.app_context():
    init_db()

# -------------------------------------------------------------
# WEB PAGES (Jinja2 Templates)
# -------------------------------------------------------------
@app.route('/')
def index():
    db = get_db()
    try:
        restaurants = [r.to_dict() for r in db.query(Restaurant).all()]
        dishes = [d.to_dict() for d in db.query(Dish).all()]
        surplus_deals = [s.to_dict() for s in db.query(SurplusDeal).filter_by(status='active').all()]
        recent_orders = [o.to_dict() for o in db.query(Order).order_by(Order.id.desc()).limit(5).all()]
        user = db.query(UserProfile).first()
        user_dict = user.to_dict() if user else {}
    finally:
        db.close()
    return render_template('index.html', 
                           restaurants=restaurants, 
                           dishes=dishes, 
                           surplus_deals=surplus_deals,
                           recent_orders=recent_orders,
                           user=user_dict)

@app.route('/surplus')
def surplus_marketplace():
    db = get_db()
    try:
        deals = [s.to_dict() for s in db.query(SurplusDeal).filter_by(status='active').all()]
        restaurants = [r.to_dict() for r in db.query(Restaurant).all()]
        dishes = [d.to_dict() for d in db.query(Dish).all()]
        total_waste_saved = sum(d['waste_saved_kg'] for d in deals)
        total_co2_saved = sum(d['co2_saved_kg'] for d in deals)
    finally:
        db.close()
    return render_template('surplus.html', deals=deals, restaurants=restaurants, dishes=dishes,
                           total_waste_saved=round(total_waste_saved, 1),
                           total_co2_saved=round(total_co2_saved, 1))

@app.route('/group')
def group_order():
    return render_template('group.html')

@app.route('/fridge')
def fridge_vision():
    return render_template('fridge.html')

@app.route('/analytics')
def analytics_dashboard():
    return render_template('analytics.html')

@app.route('/map')
def map_view():
    db = get_db()
    try:
        restaurants = [r.to_dict() for r in db.query(Restaurant).all()]
    finally:
        db.close()
    return render_template('map_view.html', restaurants=restaurants)

# -------------------------------------------------------------
# REST API ENDPOINTS
# -------------------------------------------------------------
@app.route('/api/dishes', methods=['GET'])
def get_all_dishes():
    db = get_db()
    try:
        dishes = [d.to_dict() for d in db.query(Dish).all()]
    finally:
        db.close()
    return jsonify({"status": "success", "dishes": dishes})

@app.route('/api/restaurants', methods=['GET'])
def get_restaurants():
    db = get_db()
    try:
        restaurants = [r.to_dict() for r in db.query(Restaurant).all()]
    finally:
        db.close()
    return jsonify({"status": "success", "restaurants": restaurants})

# Feature 1: Natural Language Ordering API
@app.route('/api/nl-order', methods=['POST'])
def process_nl_order():
    data = request.get_json() or {}
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({"status": "error", "message": "Please enter a valid request."}), 400

    db = get_db()
    try:
        all_dishes = [d.to_dict() for d in db.query(Dish).all()]
    finally:
        db.close()

    result = build_smart_cart(prompt, all_dishes)
    return jsonify(result)

# Feature 2: Surplus Food Marketplace APIs
@app.route('/api/surplus', methods=['GET'])
def get_surplus_deals():
    db = get_db()
    try:
        deals = [s.to_dict() for s in db.query(SurplusDeal).filter_by(status='active').all()]
    finally:
        db.close()
    return jsonify({"status": "success", "deals": deals})

@app.route('/api/surplus/add', methods=['POST'])
def add_surplus_deal():
    data = request.get_json() or {}
    dish_id = data.get('dish_id')
    restaurant_id = data.get('restaurant_id')
    original_price = float(data.get('original_price', 150))
    discounted_price = float(data.get('discounted_price', 75))
    quantity = int(data.get('quantity', 5))
    expire_minutes = int(data.get('expire_minutes', 90))

    expiry_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=expire_minutes)

    db = get_db()
    try:
        new_deal = SurplusDeal(
            dish_id=dish_id,
            restaurant_id=restaurant_id,
            original_price=original_price,
            discounted_price=discounted_price,
            quantity_available=quantity,
            waste_saved_kg=round(quantity * 0.45, 2),
            co2_saved_kg=round(quantity * 1.1, 2),
            expiry_time=expiry_time,
            status='active'
        )
        db.add(new_deal)
        db.commit()
        deal_dict = new_deal.to_dict()
    finally:
        db.close()

    return jsonify({"status": "success", "deal": deal_dict, "message": "Surplus deal listed successfully!"})

@app.route('/api/surplus/buy/<int:deal_id>', methods=['POST'])
def buy_surplus_deal(deal_id):
    db = get_db()
    try:
        deal = db.query(SurplusDeal).filter_by(id=deal_id).first()
        if not deal or deal.quantity_available <= 0:
            return jsonify({"status": "error", "message": "Deal is no longer available"}), 404
        
        deal.quantity_available -= 1
        if deal.quantity_available == 0:
            deal.status = 'sold_out'
        
        # Create an order
        order = Order(
            customer_name="Eco Hero Customer",
            delivery_address="Customer Doorstep",
            total_amount=deal.discounted_price,
            order_type="surplus",
            status="preparing",
            predicted_prep_min=10,
            predicted_delivery_min=14
        )
        db.add(order)
        db.commit()
        
        item = OrderItem(order_id=order.id, dish_id=deal.dish_id, quantity=1, unit_price=deal.discounted_price)
        db.add(item)
        db.commit()
        order_dict = order.to_dict()
    finally:
        db.close()

    return jsonify({
        "status": "success", 
        "message": f"Successfully purchased surplus meal! You prevented 0.45 kg of food waste.",
        "order": order_dict
    })

# Feature 3: Group Order Optimizer API
@app.route('/api/group-optimize', methods=['POST'])
def process_group_order():
    data = request.get_json() or {}
    members = data.get('members', [])
    if not members:
        return jsonify({"status": "error", "message": "Please provide members with preferences"}), 400

    db = get_db()
    try:
        all_dishes = [d.to_dict() for d in db.query(Dish).all()]
    finally:
        db.close()

    result = optimize_group_order(members, all_dishes)
    return jsonify(result)

# Feature 4: Scikit-learn Explainable Recommendations API
@app.route('/api/recommendations', methods=['GET', 'POST'])
def get_recommendations():
    db = get_db()
    try:
        user = db.query(UserProfile).first()
        user_profile = user.to_dict() if user else {}
        all_dishes = [d.to_dict() for d in db.query(Dish).all()]
    finally:
        db.close()

    if request.method == 'POST':
        custom_data = request.get_json() or {}
        if custom_data:
            user_profile.update(custom_data)

    recommendations = train_and_recommend(user_profile, all_dishes, top_n=6)
    return jsonify({
        "status": "success",
        "user_profile": user_profile,
        "recommendations": recommendations
    })

# Feature 5: Predictive Kitchen & Analytics APIs
@app.route('/api/predict-order', methods=['POST'])
def predict_order():
    data = request.get_json() or {}
    item_count = int(data.get('item_count', 2))
    distance_km = float(data.get('distance_km', 3.5))
    queue = int(data.get('kitchen_queue', 4))
    is_peak = bool(data.get('is_peak_hour', False))

    timings = predict_order_timings(item_count, distance_km, queue, is_peak)
    return jsonify({"status": "success", "prediction": timings})

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    data = generate_analytics_data()
    return jsonify({"status": "success", "data": data})

# Unique Twist: Fridge-to-Plate Vision AI API
@app.route('/api/fridge-vision', methods=['POST'])
def process_fridge_vision():
    db = get_db()
    try:
        all_dishes = [d.to_dict() for d in db.query(Dish).all()]
    finally:
        db.close()

    # Check if file uploaded
    image_path = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)
            image_path = save_path

    # If no file uploaded or using sample
    sample_key = request.form.get('sample') or (request.get_json() or {}).get('sample')
    if not image_path:
        # Create a sample synthetic fridge image if none exists
        sample_filename = "sample_fridge.jpg"
        sample_path = os.path.join(app.config['UPLOAD_FOLDER'], sample_filename)
        if not os.path.exists(sample_path):
            import numpy as np
            import cv2
            blank = np.zeros((300, 400, 3), dtype=np.uint8)
            # Add colored patches simulating tomatoes (red), paneer (white), capsicum (green)
            blank[40:140, 40:140] = [30, 40, 220] # Red tomatoes
            blank[40:140, 220:340] = [230, 240, 240] # White paneer
            blank[180:260, 60:180] = [40, 180, 50] # Green capsicum
            blank[180:260, 220:340] = [30, 180, 220] # Yellow cheese
            cv2.imwrite(sample_path, blank)
        image_path = sample_path

    result = analyze_fridge_image(image_path, all_dishes)
    return jsonify(result)

# Place Order API
@app.route('/api/place-order', methods=['POST'])
def place_order():
    data = request.get_json() or {}
    items = data.get('items', [])
    customer_name = data.get('customer_name', 'Rahul Sharma')
    address = data.get('address', '102 Indiranagar, Bengaluru')
    order_type = data.get('order_type', 'regular')

    if not items:
        return jsonify({"status": "error", "message": "Cart is empty"}), 400

    total_amount = sum(float(it.get('price', 0)) * int(it.get('quantity', 1)) for it in items)
    
    # Predict timing
    prediction = predict_order_timings(item_count=len(items), distance_km=3.2)

    db = get_db()
    try:
        new_order = Order(
            customer_name=customer_name,
            delivery_address=address,
            total_amount=round(total_amount, 2),
            order_type=order_type,
            status="preparing",
            predicted_prep_min=prediction["predicted_prep_min"],
            predicted_delivery_min=prediction["predicted_delivery_min"],
            delay_flag=prediction["is_delayed"],
            delay_reason=prediction["delay_reason"]
        )
        db.add(new_order)
        db.commit()

        for it in items:
            dish_id = it.get('dish_id') or it.get('id', 1)
            oi = OrderItem(
                order_id=new_order.id,
                dish_id=dish_id,
                quantity=int(it.get('quantity', 1)),
                unit_price=float(it.get('price', 0))
            )
            db.add(oi)
        db.commit()
        order_dict = new_order.to_dict()
    finally:
        db.close()

    return jsonify({
        "status": "success",
        "message": "Order placed successfully! Live delivery tracking active.",
        "order": order_dict
    })

if __name__ == '__main__':
    print("=====================================================================")
    print(" 🚀 Online Food Ordering System — Powered by AI")
    print(" Server starting on http://127.0.0.1:5000")
    print("=====================================================================")
    app.run(host='0.0.0.0', port=5000, debug=True)
