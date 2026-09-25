import chromadb

from config import CHROMA_DIR
from rag.embeddings import embed_query

COLLECTION_NAME = "knowledge_base"


def search_knowledge_base(query: str, max_results: int = 3) -> dict:
    """Retrieve the most relevant indexed document chunks for a query."""
    if not query.strip():
        return {
            "success": False,
            "error": "The knowledge-base query cannot be empty.",
        }

    try:
        chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        collection = chroma_client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=None,
        )

        document_count = collection.count()
        if document_count == 0:
            return {
                "success": False,
                "error": "The knowledge base is empty. Run document ingestion first.",
            }

        result_count = min(max(1, max_results), document_count)
        query_vector = embed_query(query)

        search_results = collection.query(
            query_embeddings=[query_vector],
            n_results=result_count,
            include=["documents", "metadatas", "distances"],
        )

        results = []
        for content, metadata, distance in zip(
            search_results["documents"][0],
            search_results["metadatas"][0],
            search_results["distances"][0],
        ):
            results.append(
                {
                    "content": content,
                    "source": metadata["source"],
                    "score": round(max(0, 1 - float(distance)), 3),
                }
            )

        return {
            "success": True,
            "query": query,
            "results": results,
        }

    except Exception:
        return {
            "success": False,
            "error": (
                "The knowledge base is unavailable. "
                "Run document ingestion before using RAG search."
            ),
        }
