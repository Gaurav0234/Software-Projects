from functools import lru_cache

from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL


@lru_cache
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL, device="cpu")


def embed_documents(texts: list[str]) -> list[list[float]]:
    vectors = get_embedding_model().encode(
        texts,
        normalize_embeddings=True,
        show_progress_bar=True,
    )
    return vectors.tolist()


def embed_query(query: str) -> list[float]:
    vector = get_embedding_model().encode(
        query,
        normalize_embeddings=True,
    )
    return vector.tolist()