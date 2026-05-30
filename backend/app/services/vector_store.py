import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from typing import List, Dict, Any, Optional
from app.core.config import settings


class VectorStoreService:
    """Manages ChromaDB vector store with free Google embeddings."""

    def __init__(self):
        # Free Google embeddings — text-embedding-004
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )

        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        self.vector_store = Chroma(
            client=self.chroma_client,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=self.embeddings,
        )

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        texts = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        ids = [
            f"{m['document_id']}_p{m['page_number']}_c{m['chunk_index']}"
            for m in metadatas
        ]
        self.vector_store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
        return len(chunks)

    def similarity_search(
        self,
        query: str,
        document_ids: Optional[List[str]] = None,
        k: int = None,
    ) -> List[Dict[str, Any]]:
        k = k or settings.TOP_K_RESULTS

        where_filter = None
        if document_ids:
            if len(document_ids) == 1:
                where_filter = {"document_id": document_ids[0]}
            else:
                where_filter = {"document_id": {"$in": document_ids}}

        results = self.vector_store.similarity_search_with_relevance_scores(
            query=query, k=k, filter=where_filter,
        )

        formatted = []
        for doc, score in results:
            if score >= settings.SIMILARITY_THRESHOLD:
                formatted.append({
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": round(score, 4),
                })
        return formatted

    def delete_document(self, document_id: str) -> int:
        collection = self.chroma_client.get_collection(settings.CHROMA_COLLECTION_NAME)
        results = collection.get(where={"document_id": document_id}, include=["metadatas"])
        if results["ids"]:
            collection.delete(ids=results["ids"])
        return len(results["ids"])

    def get_document_chunk_count(self, document_id: str) -> int:
        collection = self.chroma_client.get_collection(settings.CHROMA_COLLECTION_NAME)
        results = collection.get(where={"document_id": document_id}, include=[])
        return len(results["ids"])


vector_store_service = VectorStoreService()
