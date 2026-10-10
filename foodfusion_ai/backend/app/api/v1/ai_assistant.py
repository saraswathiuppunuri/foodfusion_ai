from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.permissions import get_current_user
from app.models.entities import User
from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.ai_assistant_service import process_chat_message

router = APIRouter(prefix="/ai-assistant", tags=["Conversational AI Food Assistant"])

@router.post("/chat", response_model=ChatResponse)
def chat_with_assistant(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Conversational food assistant that answers natural-language queries,
    grounding meal suggestions directly in live database menus.
    """
    return process_chat_message(req, current_user, db)
