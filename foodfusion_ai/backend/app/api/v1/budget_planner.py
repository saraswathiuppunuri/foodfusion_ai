from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.schemas import BudgetPlannerRequest, BudgetPlannerResponse
from app.services.budget_planner_service import plan_budget_meals

router = APIRouter(prefix="/budget-planner", tags=["Smart Budget Meal Planner"])

@router.post("", response_model=BudgetPlannerResponse)
def plan_meals(
    req: BudgetPlannerRequest,
    db: Session = Depends(get_db)
):
    """
    Computes exact constraint-satisfying meal combinations using Knapsack optimization
    that strictly do not exceed the target budget, including taxes and delivery fees.
    """
    return plan_budget_meals(req, db)
