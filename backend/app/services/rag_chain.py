from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import HumanMessage, SystemMessage
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.services.vector_store import vector_store_service


SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based on provided PDF documents.

Guidelines:
- Answer ONLY based on the provided document context
- If the answer is not in the context, say "I couldn't find information about that in the provided documents"
- Always cite your sources: mention the document name and page number
- Be concise but thorough
- Format responses clearly using markdown where helpful
"""

RAG_PROMPT_TEMPLATE = """Based on the following excerpts from PDF documents, answer the user's question.

CONTEXT FROM DOCUMENTS:
{context}

CHAT HISTORY:
{chat_history}

USER QUESTION: {question}

Answer based on the document context. Cite sources as [Document Name, Page X]."""


class RAGChainService:
    """Core RAG pipeline using FREE Google Gemini."""

    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_CHAT_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.1,
            convert_system_message_to_human=True,  # Gemini requirement
        )

    def format_context(self, chunks: List[Dict]) -> str:
        if not chunks:
            return "No relevant documents found."
        parts = []
        for i, chunk in enumerate(chunks, 1):
            meta = chunk["metadata"]
            parts.append(
                f"[{i}] Source: {meta.get('source', 'Unknown')} "
                f"(Relevance: {chunk.get('score', 0):.2f})\n{chunk['text']}"
            )
        return "\n---\n".join(parts)

    def format_chat_history(self, messages: List[Dict]) -> str:
        if not messages:
            return "No previous conversation."
        recent = messages[-6:]
        return "\n".join(
            f"{'Human' if m['role'] == 'user' else 'Assistant'}: {m['content'][:400]}"
            for m in recent
        )

    def answer_question(
        self,
        question: str,
        document_ids: Optional[List[str]] = None,
        chat_history: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        # 1. Retrieve relevant chunks
        retrieved = vector_store_service.similarity_search(
            query=question,
            document_ids=document_ids,
            k=settings.TOP_K_RESULTS,
        )

        # 2. Build prompt
        context = self.format_context(retrieved)
        history_str = self.format_chat_history(chat_history or [])
        prompt = RAG_PROMPT_TEMPLATE.format(
            context=context, chat_history=history_str, question=question
        )

        # 3. Call Gemini (FREE)
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = self.llm.invoke(messages)

        # 4. Return answer + sources
        return {
            "answer": response.content,
            "sources": self._extract_sources(retrieved),
            "chunks_used": len(retrieved),
            "tokens_used": None,  # Gemini free tier doesn't expose this
        }

    def _extract_sources(self, chunks: List[Dict]) -> List[Dict]:
        seen = set()
        sources = []
        for chunk in chunks:
            meta = chunk["metadata"]
            key = f"{meta.get('document_id')}_{meta.get('page_number')}"
            if key not in seen:
                seen.add(key)
                sources.append({
                    "document_id": meta.get("document_id"),
                    "filename": meta.get("filename"),
                    "page_number": meta.get("page_number"),
                    "source": meta.get("source"),
                    "relevance_score": chunk.get("score", 0),
                })
        return sources


rag_chain = RAGChainService()
