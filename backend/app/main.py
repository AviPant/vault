# FastAPI Entrypoint — V.A.U.L.T. Sovereign AI Engine
# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_chat import router as chat_router
from app.api.routes_system import router as system_router
from app.api.routes_history import router as history_router
from app.api.routes_files import router as files_router

app = FastAPI(
    title="Project V.A.U.L.T.",
    description="Sovereign On-Premise Agentic AI Workbench for Industrial Operations",
    version="1.0.0"
)

# Allow React Dev Server (Vite port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
        "http://localhost:5175", "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routes
app.include_router(chat_router, prefix="/api", tags=["Chat & Inference"])
app.include_router(system_router, prefix="/api/system", tags=["System & VRAM"])
app.include_router(history_router, prefix="/api/history", tags=["Chat History"])
app.include_router(files_router, prefix="/api/files", tags=["File Management"])

@app.get("/")
def health_check():
    return {"status": "online", "system": "V.A.U.L.T. Sovereign Engine"}