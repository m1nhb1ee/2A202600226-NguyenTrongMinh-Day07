from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=self._collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        # Embed the document content
        embedding = self._embedding_fn(doc.content)
        
        # Build and return a normalized record
        return {
            "doc_id": doc.id,
            "content": doc.content,
            "embedding": embedding,
            "metadata": doc.metadata,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        # Embed the query
        query_embedding = self._embedding_fn(query)
        
        # Compute similarity scores for each record
        scored_records = []
        for record in records:
            score = _dot(query_embedding, record["embedding"])
            scored_records.append({**record, "score": score})
        
        # Sort by score descending and return top_k
        scored_records.sort(key=lambda x: x["score"], reverse=True)
        return scored_records[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if self._use_chroma:
            # Use ChromaDB backend
            ids = []
            documents = []
            embeddings = []
            metadatas = []
            
            for doc in docs:
                record = self._make_record(doc)
                ids.append(str(self._next_index))
                documents.append(record["content"])
                embeddings.append(record["embedding"])
                metadatas.append(record["metadata"])
                self._next_index += 1
            
            self._collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
        else:
            # Use in-memory backend
            for doc in docs:
                record = self._make_record(doc)
                self._store.append(record)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma:
            # Use ChromaDB backend
            result = self._collection.query(query_texts=[query], n_results=top_k)
            output = []
            if result and result["documents"] and len(result["documents"]) > 0:
                for i, doc_text in enumerate(result["documents"][0]):
                    output.append({
                        "content": doc_text,
                        "score": result["distances"][0][i] if result["distances"] else 0,
                        "metadata": result["metadatas"][0][i] if result["metadatas"] else {}
                    })
            return output
        else:
            # Use in-memory backend
            return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma:
            return self._collection.count()
        else:
            return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if metadata_filter is None:
            # No filter - just do regular search
            return self.search(query, top_k)
        
        if self._use_chroma:
            # ChromaDB supports where clause filtering
            result = self._collection.query(query_texts=[query], n_results=top_k, where=metadata_filter)
            output = []
            if result and result["documents"] and len(result["documents"]) > 0:
                for i, doc_text in enumerate(result["documents"][0]):
                    output.append({
                        "content": doc_text,
                        "score": result["distances"][0][i] if result["distances"] else 0,
                        "metadata": result["metadatas"][0][i] if result["metadatas"] else {}
                    })
            return output
        else:
            # In-memory: filter first, then search among filtered records
            filtered_records = []
            for record in self._store:
                # Check if all filter conditions match
                matches = True
                for key, value in metadata_filter.items():
                    if record["metadata"].get(key) != value:
                        matches = False
                        break
                if matches:
                    filtered_records.append(record)
            
            # Search among filtered records
            return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma:
            # ChromaDB doesn't have direct delete by doc_id in basic API
            # For now, return False (optional: implement if needed)
            return False
        else:
            # In-memory: filter and remove
            initial_size = len(self._store)
            self._store = [r for r in self._store if r["doc_id"] != doc_id]
            return len(self._store) < initial_size
