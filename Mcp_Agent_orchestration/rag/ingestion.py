import hashlib
from pathlib import Path

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from config import CHROMA_DIR, DOCUMENTS_DIR, PROJECT_ROOT
from rag.embeddings import embed_documents

COLLECTION_NAME = "knowledge_base"


def read_document(file_path: Path) -> str:
    """Read supported text and PDF documents."""
    if file_path.suffix.lower() == ".pdf":
        reader = PdfReader(str(file_path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    return file_path.read_text(encoding="utf-8", errors="ignore")


def build_index() -> int:
    """Chunk documents, generate local embeddings, and store them in Chroma."""
    files = [
        path
        for path in DOCUMENTS_DIR.rglob("*")
        if path.is_file() and path.suffix.lower() in {".txt", ".md", ".pdf"}
    ]

    if not files:
        raise RuntimeError("No supported documents were found in data/documents.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=120,
    )

    chunk_texts: list[str] = []
    chunk_metadata: list[dict] = []
    chunk_ids: list[str] = []

    for file_path in files:
        text = read_document(file_path).strip()

        if not text:
            continue

        source = str(file_path.relative_to(PROJECT_ROOT))

        for index, chunk in enumerate(splitter.split_text(text)):
            chunk_texts.append(chunk)
            chunk_metadata.append({"source": source, "chunk_index": index})
            chunk_ids.append(
                hashlib.sha256(f"{source}:{index}".encode()).hexdigest()
            )

    if not chunk_texts:
        raise RuntimeError("No readable document content was found.")

    vectors = embed_documents(chunk_texts)
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Rebuild the local index so it contains only the current document chunks.
    try:
        chroma_client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=None,
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=chunk_ids,
        documents=chunk_texts,
        embeddings=vectors,
        metadatas=chunk_metadata,
    )

    return len(chunk_texts)


if __name__ == "__main__":
    indexed_chunks = build_index()
    print(f"Indexed {indexed_chunks} chunks into {CHROMA_DIR}.")
