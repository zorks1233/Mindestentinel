# huggingface plugin 
# plugins/huggingface_plugin.py
"""
Local huggingface model loader wrapper for simple usage as a plugin.
Requires transformers (+ torch optional).
"""

from typing import Optional
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    _HAS_TF = True
except Exception:
    _HAS_TF = False

class HuggingFacePlugin:
    def __init__(self, model_name: str, device: Optional[str] = None):
        if not _HAS_TF:
            raise RuntimeError("transformers and torch required")
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name, device_map="auto" if torch.cuda.is_available() else None)

    def generate_sync(self, prompt: str, max_new_tokens: int = 128) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        if torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}
        with torch.no_grad():
            out = self.model.generate(**inputs, max_new_tokens=max_new_tokens)
        return self.tokenizer.decode(out[0], skip_special_tokens=True)

    async def generate(self, prompt: str, max_new_tokens: int = 128) -> str:
        import asyncio
        return await asyncio.to_thread(self.generate_sync, prompt, max_new_tokens)
