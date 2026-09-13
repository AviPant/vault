# File Upload, Download, and Management Endpoints
import os
from datetime import datetime
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, UploadFile, File, HTTPException
# pyrefly: ignore [missing-import]
from fastapi.responses import FileResponse

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@router.post("/upload")
@router.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file and instantly vectorize it into ChromaDB."""
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        # 1. Save to disk
        with open(file_path, "wb") as buffer:
            import shutil
            shutil.copyfileobj(file.file, buffer)
            
        file_size = os.path.getsize(file_path)
        
        # 2. THE FIX: Instantly trigger ChromaDB ingestion
        try:
            # Adjust the import based on your actual function name in ingest.py
            from app.rag.ingest import ingest_file 
            ingest_file(file_path)
            print(f"[RAG MANAGER] Successfully vectorized: {file.filename}")
        except Exception as ve:
            print(f"[RAG MANAGER] Vectorization failed for {file.filename}. Error: {ve}")
        
        return {
            "filename": file.filename,
            "saved_path": file_path,
            "size_bytes": file_size,
            "status": "indexed"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/outputs")
async def list_outputs():
    """List all generated documents (docx, xlsx) in the outputs directory."""
    files = []
    if os.path.exists(OUTPUT_DIR):
        for filename in sorted(os.listdir(OUTPUT_DIR), reverse=True):
            if filename.startswith("."):
                continue
            filepath = os.path.join(OUTPUT_DIR, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                ext = os.path.splitext(filename)[1].lower()
                files.append({
                    "filename": filename,
                    "size_bytes": stat.st_size,
                    "type": ext,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                })
    return files


@router.delete("/outputs/{filename}")
async def delete_output(filename: str):
    """Delete a generated document."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        os.remove(filepath)
        return {"message": f"Successfully deleted {filename}", "deleted": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download a generated document by filename."""
    filepath = os.path.join(OUTPUT_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")

    # Determine media type
    ext = os.path.splitext(filename)[1].lower()
    media_types = {
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type=media_type
    )


@router.get("/uploads")
async def list_uploads():
    """List all uploaded files."""
    files = []
    if os.path.exists(UPLOAD_DIR):
        for filename in sorted(os.listdir(UPLOAD_DIR), reverse=True):
            if filename.startswith("."):
                continue
            filepath = os.path.join(UPLOAD_DIR, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                ext = os.path.splitext(filename)[1].lower()
                files.append({
                    "filename": filename,
                    "size_bytes": stat.st_size,
                    "type": ext,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                })
    return files


@router.delete("/uploads/{filename}")
async def delete_upload(filename: str):
    """Delete an uploaded file from disk and its chunks from the vector store."""
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        os.remove(filepath)
        
        # Also remove chunks from vector store
        try:
            from app.rag.vector_store import vector_store
            vector_store.delete_by_source(filename)
        except Exception as ve:
            print(f"Warning: Failed to delete vector store chunks for {filename}: {ve}")
            
        return {"message": f"Successfully deleted {filename}", "deleted": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
