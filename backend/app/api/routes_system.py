# VRAM & Model Management Endpoints
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
from app.core.model_router import model_router, DEFAULT_MODELS
from app.core.ollama_client import ollama_client
from app.rag.vector_store import vector_store

router = APIRouter()

@router.get("/status")
async def get_system_status():
    ollama_online = ollama_client.is_available()
    models = ollama_client.get_running_models() if ollama_online else []

    try:
        kb_doc_count = vector_store.count() if ollama_online else 0
    except Exception:
        kb_doc_count = 0

    return {
        "active_model": model_router.current_loaded_model or "None (VRAM Free)",
        "air_gapped": True,
        "vram_limit_gb": 6.0,
        "vision_mode": "precision" if model_router.use_precision_vision else "fast",
        "model_roster": DEFAULT_MODELS,
        "ollama_status": "online" if ollama_online else "offline",
        "available_models": [m.get("name", "") for m in models],
        "knowledge_base_docs": kb_doc_count,
    }

@router.post("/unload")
async def purge_vram():
    if not ollama_client.is_available():
        return {"status": "skipped", "message": "Ollama is offline"}
    active = model_router.current_loaded_model
    if active:
        ollama_client.unload_model(active)
        model_router.current_loaded_model = None
        return {"status": "success", "unloaded": active}
    return {"status": "success", "message": "No model loaded"}

@router.post("/vision-mode")
async def set_vision_mode(precision: bool = False):
    """Toggle between fast (3b) and precision (7b) vision models."""
    model_router.set_vision_mode(precision=precision)
    active_vision = DEFAULT_MODELS["vision_precision"] if precision else DEFAULT_MODELS["vision"]
    return {
        "status": "success",
        "vision_mode": "precision" if precision else "fast",
        "vision_model": active_vision
    }