# OCR & Multimodal Parsing Engine via Qwen2.5-VL
import os
import base64
import io
from PIL import Image
from typing import Optional

from app.core.ollama_client import ollama_client
from app.core.model_router import model_router, MODEL_VISION
from app.agents.prompt_templates import VISION_ANALYSIS_PROMPT


def _encode_image(image_path: str) -> str:
    """Read and base64-encode an image file for Ollama multimodal input."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_image(
    image_path: str,
    custom_prompt: Optional[str] = None
) -> str:
    """
    Analyze an industrial image using qwen2.5vl:3b via local Ollama.

    Handles VRAM swap automatically via model_router.

    Args:
        image_path: Absolute path to the image file.
        custom_prompt: Optional specific instruction (defaults to general analysis).

    Returns:
        Text analysis/description from the vision model.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # VRAM safety: evict current model if needed, load vision model
    model_router.switch_model_if_needed(MODEL_VISION)

    image_b64 = _encode_image(image_path)
    
    # Normalize via the shared cleaner (also downscales for VRAM safety)
    try:
        image_b64 = clean_base64_image(image_b64)
    except ValueError:
        pass  # If cleaning fails, try sending original anyway
    
    prompt = custom_prompt or "Analyze this industrial image in detail."

    response = ollama_client.generate(
        model=MODEL_VISION,
        prompt=prompt,
        system_prompt=VISION_ANALYSIS_PROMPT,
        images=[image_b64],
        stream=False,
        temperature=0.1
    )

    return response.get("response", "Vision analysis returned no output.")


def clean_base64_image(image_b64: str) -> str:
    """Robust Base64 Normalization (Defends against WEBP, PDF, bad padding)"""
    try:
        raw_data = base64.b64decode(image_b64)
        img = Image.open(io.BytesIO(raw_data))
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Downscale large images to prevent CUDA OOM on RTX 3050 (6GB VRAM)
        MAX_DIM = 1024
        if max(img.size) > MAX_DIM:
            img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
            print(f"[VISION_OCR] Image downscaled to {img.size} for VRAM safety")
        
        buffered = io.BytesIO()
        img.save(buffered, format="PNG", optimize=True)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        raise ValueError(f"Failed to process image. Ensure it is a valid PNG/JPG image. ({str(e)})")

def analyze_image_b64(
    image_b64: str,
    custom_prompt: Optional[str] = None
) -> str:
    """
    Analyze an image from a pre-encoded base64 string.
    Used when the image is already in memory (e.g., from an upload).
    """
    model_router.switch_model_if_needed(MODEL_VISION)

    try:
        clean_b64 = clean_base64_image(image_b64)
    except ValueError as e:
        return f"Error: {str(e)}"

    prompt = custom_prompt or "Analyze this industrial image in detail."
    response = ollama_client.generate(
        model=MODEL_VISION,
        prompt=prompt,
        system_prompt=VISION_ANALYSIS_PROMPT,
        images=[clean_b64],
        stream=False,
        temperature=0.1
    )

    return response.get("response", "Vision analysis returned no output.")
