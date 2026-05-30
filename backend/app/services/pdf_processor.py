import fitz  # PyMuPDF
import os
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.core.config import settings


class PDFProcessorService:
    """Handles PDF text extraction and chunking."""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def extract_text_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF with page-level metadata.
        Returns dict with full text, pages list, and page count.
        """
        doc = fitz.open(file_path)
        pages = []
        full_text = ""

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            text = self._clean_text(text)

            if text.strip():
                pages.append({
                    "page_number": page_num + 1,
                    "text": text,
                    "char_count": len(text),
                })
                full_text += f"\n\n--- Page {page_num + 1} ---\n\n{text}"

        doc.close()

        return {
            "full_text": full_text,
            "pages": pages,
            "page_count": len(doc),
            "total_chars": len(full_text),
        }

    def create_chunks(
        self,
        pages: List[Dict],
        document_id: str,
        filename: str,
    ) -> List[Dict[str, Any]]:
        """
        Split pages into chunks with metadata for vector storage.
        Each chunk knows which document and page it came from.
        """
        all_chunks = []

        for page_data in pages:
            page_num = page_data["page_number"]
            page_text = page_data["text"]

            if not page_text.strip():
                continue

            # Split page text into chunks
            chunks = self.text_splitter.split_text(page_text)

            for chunk_idx, chunk_text in enumerate(chunks):
                if not chunk_text.strip():
                    continue

                all_chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "document_id": document_id,
                        "filename": filename,
                        "page_number": page_num,
                        "chunk_index": chunk_idx,
                        "source": f"{filename} (Page {page_num})",
                    },
                })

                # Respect max chunks limit
                if len(all_chunks) >= settings.MAX_CHUNKS_PER_PDF:
                    return all_chunks

        return all_chunks

    def _clean_text(self, text: str) -> str:
        """Remove excessive whitespace and fix common PDF artifacts."""
        import re
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        # Remove form feed characters
        text = text.replace('\x0c', '\n')
        # Fix hyphenation at line breaks
        text = re.sub(r'(\w)-\n(\w)', r'\1\2', text)
        # Clean up spaces
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()

    def get_pdf_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract PDF metadata (title, author, etc.)."""
        doc = fitz.open(file_path)
        metadata = doc.metadata
        page_count = len(doc)
        doc.close()
        return {
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
            "page_count": page_count,
        }


pdf_processor = PDFProcessorService()
