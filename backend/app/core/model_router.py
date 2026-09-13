# app/core/model_router.py
from typing import Optional, List
import requests
import time
from app.core.ollama_client import ollama_client

# Model Roster tailored for RTX VRAM Constraints
DEFAULT_MODELS = {
    "orchestrator": "llama3.1:8b",
    "coder": "qwen2.5-coder:7b",
    "vision": "qwen2.5vl:3b",          # Fast, reliable default
    "vision_precision": "qwen2.5vl:7b"  # Deep inspection toggle
}

# Convenience aliases for direct import
MODEL_ORCHESTRATOR = DEFAULT_MODELS["orchestrator"]
MODEL_CODER = DEFAULT_MODELS["coder"]
MODEL_VISION = DEFAULT_MODELS["vision"]
MODEL_VISION_PRECISION = DEFAULT_MODELS["vision_precision"]


class ModelRouter:
    def __init__(self):
        self.current_loaded_model: Optional[str] = None
        self.use_precision_vision: bool = False

    def route_task(self, prompt: str, has_images: bool = False, file_types: Optional[List[str]] = None) -> str:
        """
        Classifies task type and returns the best model identifier.
        """
        file_types = file_types or []
        
        # 1. Vision Route (P&ID drawings, scanned logs, image attachments)
        if has_images or any(ext in file_types for ext in [".png", ".jpg", ".jpeg", ".pdf"]):
            return MODEL_VISION_PRECISION if self.use_precision_vision else MODEL_VISION

        # 2. Coding / Calculation Route
        code_keywords = [
            "calculate", "python", "script", "code", "run", 
            "formula", "math", "parse data", "dataframe", "excel"
        ]
        if any(kw in prompt.lower() for kw in code_keywords):
            return MODEL_CODER

        # 3. Default Orchestrator / Document Drafter
        return MODEL_ORCHESTRATOR

    def set_vision_mode(self, precision: bool = False):
        """Toggle between fast and precision vision models."""
        self.use_precision_vision = precision
        mode = "PRECISION (7b)" if precision else "FAST (3b)"
        print(f"[MODEL_ROUTER] Vision mode set to: {mode}")

    def switch_model_if_needed(self, target_model: str):
        """
        Safely swaps models in VRAM if the target model differs from the active one.
        Queries the actual Ollama daemon to see what is loaded and forcefully unloads
        everything except the target model to ensure VRAM constraints are respected.
        """
        if self.current_loaded_model == target_model:
            return  # Target is already loaded, do nothing
            
        print(f"[VRAM_MANAGER] Target model is {target_model}. Auditing GPU memory...")
        
        try:
            # 1. Query Ollama to see what is ACTUALLY loaded in memory right now
            response = requests.get("http://127.0.0.1:11434/api/ps", timeout=5)
            if response.status_code == 200:
                loaded_models = response.json().get("models", [])
                
                # 2. Iterate through running models and kill anything that isn't the target
                for model_info in loaded_models:
                    running_name = model_info.get("name")
                    if running_name != target_model:
                        print(f"[VRAM_MANAGER] Evicting active model: {running_name}...")
                        requests.post(
                            "http://127.0.0.1:11434/api/generate",
                            json={"model": running_name, "keep_alive": 0},
                            timeout=5
                        )
                        # Brief sleep allows PCIe bus to physically flush the VRAM
                        time.sleep(1.0) 
            
        except requests.exceptions.RequestException as e:
            print(f"[VRAM_MANAGER] Warning: Could not reach Ollama API to check memory: {e}")
            
        self.current_loaded_model = target_model
        print(f"[VRAM_MANAGER] Active model set to: {self.current_loaded_model}")

# IMPORTANT: This instantiation must be at the module level (outside the class)
# so that routes_chat.py can import it!
model_router = ModelRouter()