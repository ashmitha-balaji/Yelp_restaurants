from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database import get_db
from models.user import User
from services.ai_service import chat_with_assistant
from utils.auth import get_current_user

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []


class ChatResponse(BaseModel):
    message: str
    recommendations: List[Dict[str, Any]] = []


@router.post("/chat", response_model=ChatResponse)
def ai_chat(
    data: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = chat_with_assistant(
        db=db,
        user_id=current_user.id,
        message=data.message,
        conversation_history=data.conversation_history or [],
    )
    return ChatResponse(
        message=result.get("message", ""),
        recommendations=result.get("recommendations", []),
    )
