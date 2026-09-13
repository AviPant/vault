# ChromaDB Persistent Vector Store with Ollama Embeddings
import os
import requests
from typing import List, Dict, Any, Optional
# pyrefly: ignore [missing-import]
import chromadb

from app.config import OLLAMA_BASE_URL
EMBEDDING_MODEL = "nomic-embed-text:latest"
VECTOR_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "vector_db"
)
COLLECTION_NAME = "vault_knowledge_base"


def _get_ollama_embedding(text: str) -> List[float]:
    """Calls Ollama's local embedding endpoint. Fully air-gapped."""
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {"model": EMBEDDING_MODEL, "prompt": text, "keep_alive": 0}
    try:
        resp = requests.post(url, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["embedding"]
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Ollama is not reachable for embeddings. Ensure 'ollama serve' is running.")
    except Exception as e:
        raise RuntimeError(f"Embedding failed: {e}")


def _is_ollama_available() -> bool:
    """Quick check if Ollama is reachable."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return resp.status_code == 200
    except Exception:
        return False


class OllamaEmbeddingFunction(chromadb.EmbeddingFunction):
    """ChromaDB-compatible embedding function backed by local Ollama."""

    def __call__(self, input: List[str]) -> List[List[float]]:
        return [_get_ollama_embedding(text) for text in input]


class VectorStore:
    def __init__(self):
        os.makedirs(VECTOR_DB_PATH, exist_ok=True)
        self.client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
        self.embedding_fn = OllamaEmbeddingFunction()
        # Lazy: collection is created on first access, not at import time
        self._collection = None

    @property
    def collection(self):
        """Lazily initialize the collection to avoid crashing at import when Ollama is down."""
        if self._collection is None:
            self._collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=self.embedding_fn,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> int:
        """Add document chunks to the vector store. Returns count added."""
        if not documents:
            return 0
        if not _is_ollama_available():
            raise RuntimeError("Cannot ingest documents: Ollama is offline. Start 'ollama serve' first.")
        if ids is None:
            existing_count = self.collection.count()
            ids = [f"doc_{existing_count + i}" for i in range(len(documents))]
        if metadatas is None:
            metadatas = [{}] * len(documents)

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        return len(documents)

    def query(self, query_text: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Semantic search over the knowledge base.
        Returns a list of dicts with 'content', 'metadata', 'distance'.
        Returns empty list gracefully if Ollama is down or no documents exist.
        """
        if not _is_ollama_available():
            print("[VECTOR_STORE] Ollama offline — skipping RAG search")
            return []

        try:
            if self.collection.count() == 0:
                return []

            results = self.collection.query(
                query_texts=[query_text],
                n_results=min(n_results, self.collection.count())
            )

            formatted = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]

            for doc, meta, dist in zip(docs, metas, dists):
                formatted.append({
                    "content": doc,
                    "metadata": meta,
                    "distance": round(dist, 4)
                })
            return formatted
        except Exception as e:
            print(f"[VECTOR_STORE] Query failed: {e}")
            return []

    def count(self) -> int:
        try:
            return self.collection.count()
        except Exception:
            return 0

    def reset(self):
        """Wipe and recreate the collection."""
        self.client.delete_collection(COLLECTION_NAME)
        self._collection = None

    def delete_by_source(self, source: str) -> bool:
        """Delete all document chunks associated with a specific source filename."""
        if self._collection is None:
            return False
        try:
            self.collection.delete(where={"source": source})
            print(f"[VECTOR_STORE] Deleted chunks for source: {source}")
            return True
        except Exception as e:
            print(f"[VECTOR_STORE] Error deleting {source}: {e}")
            return False


vector_store = VectorStore()
