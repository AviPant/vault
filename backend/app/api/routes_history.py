# Chat History Persistence (SQLite) — Air-Gapped, Zero External Dependencies
import os
import json
import sqlite3
import uuid
from datetime import datetime
from typing import Optional, List
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
# pyrefly: ignore [missing-import]
from pydantic import BaseModel

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "chat_history.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def _get_db():
    """Get a SQLite connection with WAL mode for concurrency."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            image TEXT,
            steps TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    return conn


# ─── Pydantic Models ───

class ConversationCreate(BaseModel):
    title: Optional[str] = None

class MessageCreate(BaseModel):
    role: str
    content: str
    image: Optional[str] = None
    steps: Optional[list] = None


# ─── Routes ───

@router.get("/conversations")
async def list_conversations():
    """List all conversations, newest first."""
    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT id, title, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
        ).fetchall()
        conversations = []
        for row in rows:
            msg_count = conn.execute(
                "SELECT COUNT(*) as cnt FROM messages WHERE conversation_id = ?", (row["id"],)
            ).fetchone()["cnt"]
            conversations.append({
                "id": row["id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "message_count": msg_count,
            })
        return conversations
    finally:
        conn.close()


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a conversation with all its messages."""
    conn = _get_db()
    try:
        conv = conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = conn.execute(
            "SELECT role, content, image, steps, created_at FROM messages WHERE conversation_id = ? ORDER BY id ASC",
            (conversation_id,)
        ).fetchall()

        return {
            "id": conv["id"],
            "title": conv["title"],
            "created_at": conv["created_at"],
            "updated_at": conv["updated_at"],
            "messages": [
                {
                    "role": m["role"],
                    "content": m["content"],
                    "image": m["image"],
                    "steps": json.loads(m["steps"]) if m["steps"] else [],
                    "created_at": m["created_at"],
                }
                for m in messages
            ],
        }
    finally:
        conn.close()


@router.post("/conversations")
async def create_conversation(body: ConversationCreate):
    """Create a new conversation. Returns the new conversation ID."""
    conn = _get_db()
    try:
        conv_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        title = body.title or f"Chat {datetime.now().strftime('%b %d, %H:%M')}"
        conn.execute(
            "INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conv_id, title, now, now)
        )
        conn.commit()
        return {"id": conv_id, "title": title, "created_at": now}
    finally:
        conn.close()


@router.put("/conversations/{conversation_id}")
async def add_message(conversation_id: str, message: MessageCreate):
    """Append a message to an existing conversation."""
    conn = _get_db()
    try:
        conv = conn.execute(
            "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        now = datetime.now().isoformat()
        steps_json = json.dumps(message.steps) if message.steps else None

        conn.execute(
            "INSERT INTO messages (conversation_id, role, content, image, steps, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (conversation_id, message.role, message.content, message.image, steps_json, now)
        )

        # Auto-title: use first user message as title if it's still default
        if message.role == "user":
            current_title = conn.execute(
                "SELECT title FROM conversations WHERE id = ?", (conversation_id,)
            ).fetchone()["title"]
            if current_title.startswith("Chat "):
                short_title = message.content[:60].strip()
                if short_title:
                    conn.execute(
                        "UPDATE conversations SET title = ? WHERE id = ?",
                        (short_title, conversation_id)
                    )

        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, conversation_id)
        )
        conn.commit()
        return {"status": "ok", "conversation_id": conversation_id}
    finally:
        conn.close()


@router.patch("/conversations/{conversation_id}")
async def update_conversation_title(conversation_id: str, body: ConversationCreate):
    """Rename a conversation."""
    conn = _get_db()
    try:
        conv = conn.execute(
            "SELECT id FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if body.title:
            conn.execute(
                "UPDATE conversations SET title = ? WHERE id = ?",
                (body.title, conversation_id)
            )
            conn.commit()
        return {"status": "ok"}
    finally:
        conn.close()


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a conversation and all its messages."""
    conn = _get_db()
    try:
        conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        conn.commit()
        return {"status": "deleted", "id": conversation_id}
    finally:
        conn.close()
