from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def train_and_recommend(user_profile: Dict[str, Any], all_dishes: List[Dict[str, Any]], top_n: int = 6) -> List[Dict[str, Any]]:
    """
    Scikit-learn powered content-based recommendation system with TF-IDF Vectorization
    and Cosine Similarity, outputting transparent natural-language explanations.
    """
    if not all_dishes:
        return []

    # Prepare dish corpus combining tags, cuisine, category, and description
    dish_corpus = []
    for d in all_dishes:
        text_repr = f"{d.get('tags', '')} {d.get('category', '')} {d.get('spice_level', '')} {d.get('description', '')}"
        if d.get("is_veg"):
            text_repr += " vegetarian veg green plant-based"
        else:
            text_repr += " non-veg meat chicken mutton protein"
        dish_corpus.append(text_repr.lower())

    # Build user query representation
    user_cuisines = user_profile.get("preferred_cuisines", "North Indian, Biryani")
    user_diet = user_profile.get("dietary_preference", "none")
    user_spice = user_profile.get("spice_preference", "medium")
    user_past = user_profile.get("past_order_tags", "paneer, biryani, spicy, chicken")
    user_budget = float(user_profile.get("avg_budget", 350.0))

    user_text = f"{user_cuisines} {user_spice} {user_past}".lower()
    if user_diet in ["veg", "vegetarian"]:
        user_text += " vegetarian veg"
    elif user_diet in ["non-veg", "nonveg"]:
        user_text += " non-veg chicken meat"

    # Fit TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(dish_corpus + [user_text])
    
    dish_vectors = tfidf_matrix[:-1]
    user_vector = tfidf_matrix[-1:]

    # Compute cosine similarity
    similarity_scores = cosine_similarity(user_vector, dish_vectors)[0]

    recommendations = []
    for idx, dish in enumerate(all_dishes):
        base_sim = float(similarity_scores[idx])
        
        # Hard dietary filter
        if user_diet in ["veg", "vegetarian"] and not dish.get("is_veg"):
            continue

        # Price affordability bonus/penalty
        price = float(dish.get("price", 999))
        price_factor = 1.0 if price <= user_budget else max(0.5, 1.0 - (price - user_budget) / user_budget)
        
        final_score = base_sim * 0.7 + (price_factor * 0.3)
        match_percentage = int(min(99, max(50, final_score * 100 + 20)))

        # Generate Explainable AI reasoning
        reasons = []
        if dish.get("spice_level") == user_spice:
            reasons.append(f"matches your '{user_spice}' spice preference")
        if price <= user_budget:
            reasons.append(f"stays under your target budget (₹{price:.0f} vs ₹{user_budget:.0f})")
        if any(tag in dish.get("tags", "").lower() for tag in user_past.lower().split(',')):
            reasons.append("frequently matched ingredients from your previous 5★ orders")
        if dish.get("protein_g", 0) >= 20:
            reasons.append(f"high-protein meal ({dish.get('protein_g')}g protein)")

        explanation = f"{match_percentage}% match because this dish " + (", and ".join(reasons) if reasons else "aligns closely with your dietary habits") + "."

        rec_item = dict(dish)
        rec_item["match_score"] = match_percentage
        rec_item["explanation"] = explanation
        recommendations.append(rec_item)

    # Sort by match score descending
    recommendations.sort(key=lambda x: x["match_score"], reverse=True)
    return recommendations[:top_n]
