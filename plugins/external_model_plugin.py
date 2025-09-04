# external model plugin 
# plugins/external_model_plugin.py
import requests
from typing import Dict, Any, Optional

class ExternalModelPlugin:
    """
    Adapter to external LLM HTTP endpoints (e.g., Ollama or any custom endpoint).
    Expect endpoint to accept JSON {model, prompt} and reply with {response: "..."}.
    """

    def __init__(self, endpoint: str, api_key: Optional[str] = None, timeout: float = 30.0):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.timeout = float(timeout)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def query(self, model: str, prompt: str, steps: int = 128) -> str:
        payload = {"model": model, "prompt": prompt, "steps": steps}
        resp = requests.post(self.endpoint, json=payload, headers=self._headers(), timeout=self.timeout)
        resp.raise_for_status()
        j = resp.json()
        # support multiple response shapes
        if isinstance(j, dict) and "response" in j:
            return j["response"]
        if isinstance(j, dict) and "result" in j:
            return j["result"]
        return str(j)
