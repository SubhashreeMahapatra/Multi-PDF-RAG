from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json

from app.db.database import get_db
from app.db.models import ChatSession, Message, Document
from app.services.rag_chain import rag_chain

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: str
    message: str
    document_ids: Optional[List[str]] = None  # If None, search all documents


class ChatResponse(BaseModel):
    message_id: str
    answer: str
    sources: List[dict]
    chunks_used: int
    tokens_used: Optional[int] = None


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Send a message and get an AI response based on your PDFs."""
    # Verify session exists
    session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # Validate document IDs if provided
    if request.document_ids:
        docs = db.query(Document).filter(
            Document.id.in_(request.document_ids),
            Document.status == "ready",
        ).all()
        if not docs:
            raise HTTPException(
                status_code=400,
                detail="No ready documents found with the provided IDs"
            )

    # Get recent chat history for context
    history = db.query(Message).filter(
        Message.session_id == request.session_id
    ).order_by(Message.created_at.desc()).limit(10).all()

    history_list = [
        {"role": m.role, "content": m.content}
        for m in reversed(history)
    ]

    # Save user message
    user_msg = Message(
        session_id=request.session_id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)
    db.flush()

    # Run RAG pipeline
    try:
        result = rag_chain.answer_question(
            question=request.message,
            document_ids=request.document_ids,
            chat_history=history_list,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"AI generation failed: {str(e)}")

    # Save assistant message
    assistant_msg = Message(
        session_id=request.session_id,
        role="assistant",
        content=result["answer"],
        sources=json.dumps(result["sources"]),
        tokens_used=result.get("tokens_used"),
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return ChatResponse(
        message_id=assistant_msg.id,
        answer=result["answer"],
        sources=result["sources"],
        chunks_used=result["chunks_used"],
        tokens_used=result.get("tokens_used"),
    )


@router.get("/{session_id}/history")
def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """Get all messages in a session."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = db.query(Message).filter(
        Message.session_id == session_id
    ).order_by(Message.created_at.asc()).all()

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "sources": json.loads(m.sources) if m.sources else [],
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in messages
    ]
