# Document Parser & Embedding Ingester
import os
import hashlib
from typing import List, Dict, Any, Optional
# pyrefly: ignore [missing-import]
from pypdf import PdfReader


from app.rag.vector_store import vector_store


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks for embedding."""
    chunks = []
    start = 0
    text = text.strip()
    if not text:
        return []
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


def _generate_chunk_id(source: str, index: int) -> str:
    """Deterministic ID so re-ingestion doesn't duplicate."""
    raw = f"{source}::chunk_{index}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _read_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    text_parts = []
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text_parts.append(extracted)
    return "\n".join(text_parts)


def _read_docx(file_path: str) -> str:
    from docx import Document
    doc = Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())


def _read_xlsx(file_path: str) -> str:
    import pandas as pd
    xls = pd.ExcelFile(file_path)
    parts = []
    for sheet_name in xls.sheet_names:
        df = pd.read_excel(xls, sheet_name=sheet_name)
        parts.append(f"[Sheet: {sheet_name}]\n{df.to_string(index=False)}")
    return "\n\n".join(parts)


def _read_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


READERS = {
    ".pdf": _read_pdf,
    ".docx": _read_docx,
    ".xlsx": _read_xlsx,
    ".xls": _read_xlsx,
    ".txt": _read_txt,
    ".md": _read_txt,
    ".csv": _read_txt,
}


def ingest_file(
    file_path: str,
    chunk_size: int = 500,
    overlap: int = 50,
    extra_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Parse a document file, chunk it, and add to the vector store.
    Returns ingestion stats.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    reader = READERS.get(ext)
    if reader is None:
        raise ValueError(f"Unsupported file type: {ext}. Supported: {list(READERS.keys())}")

    raw_text = reader(file_path)
    if not raw_text.strip():
        return {"file": file_path, "chunks_added": 0, "message": "File was empty or unreadable."}

    chunks = _chunk_text(raw_text, chunk_size=chunk_size, overlap=overlap)

    filename = os.path.basename(file_path)
    ids = [_generate_chunk_id(filename, i) for i in range(len(chunks))]
    metadatas = [
        {
            "source": filename,
            "chunk_index": i,
            "file_type": ext,
            **(extra_metadata or {})
        }
        for i in range(len(chunks))
    ]

    added = vector_store.add_documents(documents=chunks, metadatas=metadatas, ids=ids)

    return {
        "file": filename,
        "chunks_added": added,
        "total_chars": len(raw_text),
        "total_store_docs": vector_store.count()
    }


def ingest_directory(
    dir_path: str,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[Dict[str, Any]]:
    """Ingest all supported files in a directory."""
    results = []
    for filename in os.listdir(dir_path):
        ext = os.path.splitext(filename)[1].lower()
        if ext in READERS:
            full_path = os.path.join(dir_path, filename)
            try:
                result = ingest_file(full_path, chunk_size=chunk_size, overlap=overlap)
                results.append(result)
                print(f"[INGEST] {filename}: {result['chunks_added']} chunks indexed")
            except Exception as e:
                results.append({"file": filename, "error": str(e)})
                print(f"[INGEST_ERROR] {filename}: {e}")
    return results
