# SOP Knowledge Base Retriever
from typing import List, Dict, Any
from app.rag.vector_store import vector_store


def search_knowledge_base(query: str, n_results: int = 3) -> List[Dict[str, Any]]:
    """
    Search the local ChromaDB knowledge base for relevant SOPs,
    manuals, and engineering documents.

    Args:
        query: Natural language search query.
        n_results: Number of results to return (default 3).

    Returns:
        List of dicts, each with 'content', 'metadata', 'distance'.
        Empty list if the knowledge base has no documents.
    """
    return vector_store.query(query_text=query, n_results=n_results)


def format_context_for_llm(results: List[Dict[str, Any]]) -> str:
    """
    Format RAG search results into a text block suitable for
    injection into an LLM prompt as retrieved context.
    """
    if not results:
        return "[No relevant documents found in the knowledge base.]"

    parts = []
    for i, result in enumerate(results, 1):
        source = result.get("metadata", {}).get("source", "Unknown")
        content = result.get("content", "")
        distance = result.get("distance", 0)
        parts.append(
            f"--- Reference {i} (Source: {source}, Relevance: {1 - distance:.2%}) ---\n"
            f"{content}\n"
        )
    return "\n".join(parts)
