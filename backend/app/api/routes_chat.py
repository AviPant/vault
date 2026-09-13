# Chat and Streaming Endpoints
# pyrefly: ignore [missing-import]
from typing import Optional, List
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException
# pyrefly: ignore [missing-import]
from fastapi.responses import StreamingResponse
# pyrefly: ignore [missing-import]
from pydantic import BaseModel

from app.core.model_router import model_router
from app.core.ollama_client import ollama_client
from app.agents.orchestrator import orchestrator
from app.tools.vision_ocr import clean_base64_image

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str
    images: Optional[List[str]] = None

class ChatRequest(BaseModel):
    prompt: Optional[str] = None
    messages: Optional[List[ChatMessage]] = None
    has_images: Optional[bool] = False
    images: Optional[List[str]] = None
    file_types: Optional[List[str]] = None
    stream: Optional[bool] = False
    model: Optional[str] = None
    temperature: Optional[float] = 0.2
    system_prompt: Optional[str] = None
    use_agent: Optional[bool] = True
    high_precision: Optional[bool] = False

@router.post("/chat")
@router.post("/chat/")
async def chat(request: ChatRequest):
    try:
        # Extract prompt and images from messages if top-level prompt is missing
        effective_prompt = request.prompt
        effective_images = request.images or []

        if not effective_prompt and request.messages:
            for msg in reversed(request.messages):
                if msg.role == "user":
                    effective_prompt = msg.content
                    if msg.images:
                        effective_images.extend(msg.images)
                    break

        if not effective_prompt and not effective_images:
            raise HTTPException(status_code=400, detail="Either a prompt or an image is required.")
            
        if not effective_prompt and effective_images:
            effective_prompt = "Analyze the attached image."

        # Set vision precision mode if specified
        if request.high_precision is not None:
            model_router.set_vision_mode(precision=request.high_precision)

        has_imgs = request.has_images or bool(effective_images)

        # ── Agent Mode: Multi-step orchestration ──
        if request.use_agent:
            if request.stream:
                def agent_stream():
                    try:
                        for chunk in orchestrator.run_stream(
                            prompt=effective_prompt,
                            images=effective_images,
                            file_types=request.file_types
                        ):
                            yield chunk
                    except Exception as e:
                        import json
                        yield f"data: {json.dumps({'error': str(e)})}\n\n"
                return StreamingResponse(agent_stream(), media_type="text/event-stream")
            else:
                result = orchestrator.run(
                    prompt=effective_prompt,
                    images=effective_images,
                    file_types=request.file_types
                )
                return result

        # ── Direct Mode: Single-model inference ──
        target_model = request.model or model_router.route_task(
            prompt=effective_prompt,
            has_images=has_imgs,
            file_types=request.file_types
        )
        model_router.switch_model_if_needed(target_model)

        # Normalize images before passing to direct generation
        cleaned_images = []
        try:
            for img in effective_images:
                cleaned_images.append(clean_base64_image(img))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        if request.stream:
            def event_generator():
                try:
                    generator = ollama_client.generate(
                        model=target_model,
                        prompt=effective_prompt,
                        system_prompt=request.system_prompt,
                        images=cleaned_images,
                        stream=True,
                        temperature=request.temperature or 0.2
                    )
                    for chunk in generator:
                        import json
                        yield f"data: {json.dumps({'token': chunk})}\n\n"
                except Exception as e:
                    import json
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
            return StreamingResponse(event_generator(), media_type="text/event-stream")

        else:
            response_data = ollama_client.generate(
                model=target_model,
                prompt=effective_prompt,
                system_prompt=request.system_prompt,
                images=cleaned_images,
                stream=False,
                temperature=request.temperature or 0.2
            )
            return {
                "model": target_model,
                "response": response_data.get("response", ""),
                "done": response_data.get("done", True)
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))