from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.permissions import get_current_user
from app.models.entities import User
from app.schemas.schemas import RecommendationOut
from app.services.recommendation_service import get_explainable_recommendations

router = APIRouter(prefix="/recommendations", tags=["Explainable AI Recommendations"])

@router.get("", response_model=List[RecommendationOut])
def get_recommendations(
    limit: int = 6,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns personalized meal recommendations using Scikit-Learn TF-IDF vectorization
    and Cosine Similarity, complete with human-readable reasoning explanations.
    """
    return get_explainable_recommendations(current_user, db, limit=limit)
