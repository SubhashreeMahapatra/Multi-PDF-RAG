from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Document(Base):
    """Represents an uploaded PDF document."""
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)       # bytes
    page_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    status = Column(String(50), default="processing")  # processing, ready, error
    error_message = Column(Text, nullable=True)
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    session_documents = relationship("SessionDocument", back_populates="document")


class ChatSession(Base):
    """A chat session that can reference multiple documents."""
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(255), default="New Chat")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    session_documents = relationship("SessionDocument", back_populates="session")


class SessionDocument(Base):
    """Many-to-many: sessions ↔ documents."""
    __tablename__ = "session_documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="session_documents")
    document = relationship("Document", back_populates="session_documents")


class Message(Base):
    """Individual chat messages."""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)          # user | assistant
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)              # JSON string of source citations
    tokens_used = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")
