from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.models.entities import User, Dish, Restaurant
from app.schemas.schemas import RecommendationOut, DishOut

def get_explainable_recommendations(user: User, db: Session, limit: int = 6) -> List[RecommendationOut]:
    """
    Computes personalized meal recommendations using Scikit-Learn TF-IDF vectorization
    and Cosine Similarity, generating human-readable explainability badges.
    """
    dishes = db.query(Dish).filter(Dish.is_available == True).all()
    if not dishes:
        return []

    # Prepare dish text corpus
    dish_corpus = []
    for d in dishes:
        text = f"{d.name} {d.tags or ''} {d.ingredients or ''} {d.spice_level} "
        if d.is_veg:
            text += "veg vegetarian plant-based green "
        else:
            text += "non-veg meat chicken protein "
        dish_corpus.append(text.lower())

    # Build user profile query string
    user_cuisines = user.preferred_cuisines or "North Indian, Biryani"
    user_spice = user.spice_preference or "medium"
    user_diet = user.dietary_preference or "none"
    user_budget = user.avg_budget or 300.0

    user_query = f"{user_cuisines} {user_spice} ".lower()
    if user_diet in ["veg", "vegetarian"]:
        user_query += "veg vegetarian plant-based "
    elif user_diet in ["non-veg", "nonveg"]:
        user_query += "non-veg chicken protein "

    # Vectorize using TF-IDF
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(dish_corpus + [user_query])
        dish_vectors = tfidf_matrix[:-1]
        user_vector = tfidf_matrix[-1:]
        similarity_scores = cosine_similarity(user_vector, dish_vectors)[0]
    except Exception:
        # Fallback to rating/budget heuristic if TF-IDF fails
        similarity_scores = [0.7] * len(dishes)

    recommendations = []
    for idx, dish in enumerate(dishes):
        # Hard dietary filter
        if user_diet in ["veg", "vegetarian"] and not dish.is_veg:
            continue

        base_sim = float(similarity_scores[idx])
        price_factor = 1.0 if dish.price <= user_budget else max(0.4, 1.0 - (dish.price - user_budget) / user_budget)
        combined_score = (base_sim * 0.65) + (price_factor * 0.35)
        match_percentage = int(min(99, max(52, combined_score * 100 + 15)))

        # Build transparent natural language explanation
        reasons = []
        if user_diet in ["veg", "vegetarian"] and dish.is_veg:
            reasons.append("matches your vegetarian dietary preference")
        if dish.spice_level == user_spice:
            reasons.append(f"satisfies your '{user_spice}' spice craving")
        if dish.price <= user_budget:
            reasons.append(f"comfortably fits your target budget of ₹{user_budget:.0f}")
        if dish.protein_g >= 20:
            reasons.append(f"provides high protein ({dish.protein_g}g)")

        explanation = "Recommended because " + (", and ".join(reasons) if reasons else "it aligns with your taste profile") + "."

        r_name = dish.restaurant.name if dish.restaurant else "Popular Kitchen"
        dish_out = DishOut.model_validate(dish)
        recommendations.append(RecommendationOut(
            dish=dish_out,
            restaurant_name=r_name,
            match_score=match_percentage,
            explanation=explanation
        ))

    # Sort descending by match score
    recommendations.sort(key=lambda x: x.match_score, reverse=True)
    return recommendations[:limit]
