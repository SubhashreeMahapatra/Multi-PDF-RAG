from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
import os
import shutil
import uuid

from app.db.database import get_db
from app.db.models import Document
from app.core.config import settings
from app.services.pdf_processor import pdf_processor
from app.services.vector_store import vector_store_service

router = APIRouter(prefix="/documents", tags=["documents"])


def process_pdf_background(document_id: str, file_path: str, db_url: str):
    """Background task to process PDF after upload."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create new DB session for background task
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return

        # Extract text
        extraction = pdf_processor.extract_text_from_pdf(file_path)

        # Create chunks
        chunks = pdf_processor.create_chunks(
            pages=extraction["pages"],
            document_id=document_id,
            filename=doc.original_name,
        )

        # Store in vector DB
        if chunks:
            vector_store_service.add_chunks(chunks)

        # Update document status
        doc.page_count = extraction["page_count"]
        doc.chunk_count = len(chunks)
        doc.status = "ready"
        db.commit()

    except Exception as e:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "error"
            doc.error_message = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/upload", response_model=dict)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a PDF document for processing."""
    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    # Validate file size
    content = await file.read()
    file_size = len(content)
    max_size = settings.MAX_PDF_SIZE_MB * 1024 * 1024

    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_PDF_SIZE_MB}MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    # Save file
    document_id = str(uuid.uuid4())
    safe_filename = f"{document_id}.pdf"
    file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Create DB record
    doc = Document(
        id=document_id,
        filename=safe_filename,
        original_name=file.filename,
        file_size=file_size,
        file_path=file_path,
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # Process in background
    background_tasks.add_task(
        process_pdf_background,
        document_id,
        file_path,
        settings.DATABASE_URL,
    )

    return {
        "id": doc.id,
        "filename": doc.original_name,
        "file_size": doc.file_size,
        "status": doc.status,
        "message": "PDF uploaded successfully. Processing in background...",
    }


@router.get("/", response_model=List[dict])
def list_documents(db: Session = Depends(get_db)):
    """List all uploaded documents."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "filename": d.original_name,
            "file_size": d.file_size,
            "page_count": d.page_count,
            "chunk_count": d.chunk_count,
            "status": d.status,
            "error_message": d.error_message,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in docs
    ]


@router.get("/{document_id}", response_model=dict)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get a specific document by ID."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": doc.id,
        "filename": doc.original_name,
        "file_size": doc.file_size,
        "page_count": doc.page_count,
        "chunk_count": doc.chunk_count,
        "status": doc.status,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
    }


@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and its vectors."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from vector store
    try:
        deleted_chunks = vector_store_service.delete_document(document_id)
    except Exception:
        deleted_chunks = 0

    # Delete file
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    # Delete from DB
    db.delete(doc)
    db.commit()

    return {"message": f"Document deleted. Removed {deleted_chunks} chunks from vector store."}
