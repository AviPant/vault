# Local Ollama Connector with keep_alive eviction
import requests
import json
from typing import Generator, Dict, Any, Optional

from app.config import OLLAMA_BASE_URL


class OllamaClient:
    def __init__(self, base_url: str = OLLAMA_BASE_URL):
        self.base_url = base_url
        self._available: Optional[bool] = None

    def is_available(self) -> bool:
        """Ping Ollama to check if the service is reachable."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            self._available = resp.status_code == 200
        except Exception:
            self._available = False
        return self._available

    def get_running_models(self) -> list:
        """Return list of models currently loaded in Ollama."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                return resp.json().get("models", [])
        except Exception:
            pass
        return []

    def unload_model(self, model_name: str) -> bool:
        """Forces Ollama to immediately purge the model from RTX 3050 VRAM."""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {"model": model_name, "keep_alive": 0}
            response = requests.post(url, json=payload, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"[VRAM_WARNING] Failed to unload {model_name}: {e}")
            return False

    def generate(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        images: Optional[list] = None,
        stream: bool = False,
        temperature: float = 0.2,
        format: Optional[str] = None
    ) -> Dict[str, Any] | Generator[str, None, None]:
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                "num_ctx": 4096  # Cap context to prevent VRAM overflow on RTX 3050
            },
            "keep_alive": 0      # Unload immediately after generating
        }

        if system_prompt:
            payload["system"] = system_prompt
        if images:
            # Only send images to known vision models to prevent Ollama 400 Bad Request errors
            is_vision = any(kw in model.lower() for kw in ["vl", "vision", "llava", "pixtral", "minicpm"])
            if is_vision:
                payload["images"] = images
            else:
                print(f"[OllamaClient] Stripping images. Model '{model}' is not a vision model.")
        if format:
            payload["format"] = format

        try:
            if stream:
                return self._stream_response(url, payload)
            else:
                resp = requests.post(url, json=payload, timeout=120)
                if resp.status_code == 404:
                    raise RuntimeError(f"Model '{model}' is not downloaded in Ollama. Run: ollama pull {model}")
                if resp.status_code >= 400:
                    raise RuntimeError(f"{resp.status_code} Client Error: {resp.text} for url: {url}")
                resp.raise_for_status()
                return resp.json()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Ollama service is not reachable. Start it with 'ollama serve' and try again."
            )

    def _stream_response(self, url: str, payload: dict) -> Generator[str, None, None]:
        try:
            with requests.post(url, json=payload, stream=True, timeout=120) as response:
                if response.status_code == 404:
                    yield f"\n[Error: Model '{payload['model']}' not found in Ollama. Run 'ollama pull {payload['model']}']\n"
                    return
                if response.status_code >= 400:
                    yield f"\n[Inference Error: {response.status_code} Client Error: {response.text} for url: {url}]\n"
                    return
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode("utf-8"))
                        yield data.get("response", "")
                        if data.get("done", False):
                            break
        except requests.exceptions.ConnectionError:
            yield "\n[Error: Ollama service is not reachable. Start it with 'ollama serve'.]\n"
        except Exception as e:
            yield f"\n[Inference Error: {str(e)}]\n"


ollama_client = OllamaClient()