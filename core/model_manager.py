# src/core/model_manager.py
"""
ModelManager - Verwaltung & Lifecycle für Modelle in Mindestentinel.

Features:
- Registrierung / Deregistrierung von Modellen (in-memory + persistente Registry)
- Unterstützung für:
    * External plugin model objects (must implement `generate` async or `generate_sync`)
    * Hugging Face local models (if transformers & torch available) via register_local_hf_model
    * Generic Python callables wrapped via LocalCallableModel
- Start/Stop lifecycle delegation (if model implements .start()/ .stop())
- Thread-safe operations
- Persistente Registry in JSON at data/models/external_registry.json
- Lazy-loading: registry metadata persisted, model objects kept in memory and can be reloaded on init (if possible)
- Methods:
    register_model(name, model_obj, meta)
    register_local_hf_model(name, hf_name_or_path, device=None, trust_remote_code=False)
    register_external_plugin(name, plugin_instance, meta)
    deregister_model(name)
    get_model(name)
    list_models()
    start_model(name)
    stop_model(name)
"""

from __future__ import annotations
import json
import threading
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List, Callable
import asyncio

_LOGGER = logging.getLogger("mindestentinel.model_manager")
_LOGGER.addHandler(logging.NullHandler())

REGISTRY_PATH_DEFAULT = Path("data") / "models" / "external_registry.json"
REGISTRY_PATH_DEFAULT.parent.mkdir(parents=True, exist_ok=True)

# Optional heavy deps
_HAS_TRANSFORMERS = False
_HAS_TORCH = False
try:
    import transformers  # type: ignore
    _HAS_TRANSFORMERS = True
except Exception:
    _HAS_TRANSFORMERS = False

try:
    import torch  # type: ignore
    _HAS_TORCH = True
except Exception:
    _HAS_TORCH = False


class LocalCallableModel:
    """
    Wrapper for simple Python callables that implement a sync `call(prompt, **kwargs)` or `generate_sync`.
    The wrapper exposes:
      - async def generate(prompt)
      - def generate_sync(prompt)
    """
    def __init__(self, name: str, callable_obj: Callable[..., Any]):
        if not callable(callable_obj):
            raise TypeError("callable_obj must be callable")
        self.name = name
        self._call = callable_obj

    async def generate(self, prompt: str, **kwargs) -> str:
        # run in thread to avoid blocking event loop
        return await asyncio.to_thread(self.generate_sync, prompt, **kwargs)

    def generate_sync(self, prompt: str, **kwargs) -> str:
        # call user-provided callable; expect string return
        return str(self._call(prompt, **kwargs))


class ExternalPluginWrapper:
    """
    Adapter for plugin instances that expose `query(model, prompt, ...)` or `generate(prompt)` or `generate_sync`.
    We try to call in the following order:
      - async generate(prompt)
      - generate_sync(prompt)
      - plugin.query(...) (sync)
      - plugin.query_async(...) (async)
    """
    def __init__(self, name: str, plugin_instance: Any, default_model: Optional[str] = None):
        self.name = name
        self.plugin = plugin_instance
        self.default_model = default_model

    async def generate(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        # choose model if plugin requires explicit model name
        model_to_use = model or self.default_model
        # try async generate
        if hasattr(self.plugin, "generate") and asyncio.iscoroutinefunction(self.plugin.generate):
            return await self.plugin.generate(prompt, model=model_to_use, **kwargs)  # type: ignore
        # try generate_sync in thread
        if hasattr(self.plugin, "generate_sync"):
            return await asyncio.to_thread(self.plugin.generate_sync, prompt, model_to_use, **kwargs)
        # try query (sync)
        if hasattr(self.plugin, "query"):
            return await asyncio.to_thread(self.plugin.query, model_to_use, prompt, **kwargs)
        # try async query
        if hasattr(self.plugin, "query") and asyncio.iscoroutinefunction(self.plugin.query):
            return await self.plugin.query(model_to_use, prompt, **kwargs)  # type: ignore
        raise TypeError("Plugin object has no compatible generate/query methods")

    def generate_sync(self, prompt: str, model: Optional[str] = None, **kwargs) -> str:
        model_to_use = model or self.default_model
        if hasattr(self.plugin, "generate_sync"):
            return self.plugin.generate_sync(prompt, model_to_use, **kwargs)  # type: ignore
        if hasattr(self.plugin, "generate"):
            # if generate is sync
            gen = getattr(self.plugin, "generate")
            if not asyncio.iscoroutinefunction(gen):
                return gen(prompt, model_to_use, **kwargs)  # type: ignore
        if hasattr(self.plugin, "query"):
            return self.plugin.query(model_to_use, prompt, **kwargs)  # type: ignore
        raise TypeError("Plugin object has no compatible sync generate/query methods")


class HFModelWrapper:
    """
    HuggingFace model wrapper. Requires `transformers` (+ `torch`) to be installed.
    Loads model/tokenizer and exposes generate() async and generate_sync().
    """
    def __init__(self, name: str, model_name_or_path: str, device: Optional[str] = None, trust_remote_code: bool = False):
        if not _HAS_TRANSFORMERS:
            raise RuntimeError("transformers is required to use HFModelWrapper. pip install transformers")
        if not _HAS_TORCH:
            raise RuntimeError("torch is required to use HFModelWrapper. pip install torch")

        self.name = name
        self.model_name_or_path = model_name_or_path
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.trust_remote_code = trust_remote_code

        # Loading can be heavy; we perform it at init (explicit)
        _LOGGER.info("Lade HF-Model %s on device %s", model_name_or_path, self.device)
        # Use from_pretrained with device_map if available
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM  # type: ignore
            self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, trust_remote_code=self.trust_remote_code)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name_or_path,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=self.trust_remote_code,
            )
            # ensure model on specified device if no device_map
            if hasattr(self.model, "to") and not torch.cuda.is_available():
                self.model.to(self.device)
        except Exception as e:
            _LOGGER.exception("Fehler beim Laden des HF-Modells: %s", e)
            raise

    async def generate(self, prompt: str, max_new_tokens: int = 128, **kwargs) -> str:
        return await asyncio.to_thread(self.generate_sync, prompt, max_new_tokens=max_new_tokens, **kwargs)

    def generate_sync(self, prompt: str, max_new_tokens: int = 128, **kwargs) -> str:
        # Tokenize and generate
        inputs = self.tokenizer(prompt, return_tensors="pt")
        if _HAS_TORCH and torch.cuda.is_available():
            inputs = {k: v.to("cuda") for k, v in inputs.items()}
        with torch.no_grad():
            out = self.model.generate(**inputs, max_new_tokens=max_new_tokens, **kwargs)
        decoded = self.tokenizer.decode(out[0], skip_special_tokens=True)
        return decoded


class ModelManager:
    def __init__(self, registry_path: Optional[Path] = None):
        self._lock = threading.RLock()
        self._models: Dict[str, Any] = {}   # name -> model_object (wrapper)
        self._meta: Dict[str, Dict[str, Any]] = {}  # name -> metadata
        self.registry_path: Path = registry_path or REGISTRY_PATH_DEFAULT
        self._load_registry_from_disk()

    # ---------------- registry persistence ----------------
    def _load_registry_from_disk(self) -> None:
        if not self.registry_path.exists():
            _LOGGER.debug("Registry file not found: %s", self.registry_path)
            return
        try:
            with self.registry_path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            if not isinstance(data, dict):
                _LOGGER.warning("Registry file malformed, expected dict.")
                return
            # restore metadata only; not model objects
            with self._lock:
                self._meta = data
            _LOGGER.info("Registry geladen (%d Einträge).", len(self._meta))
        except Exception as e:
            _LOGGER.exception("Fehler beim Laden der Registry: %s", e)

    def _persist_registry_to_disk(self) -> None:
        try:
            with self.registry_path.open("w", encoding="utf-8") as fh:
                json.dump(self._meta, fh, indent=2, ensure_ascii=False)
            _LOGGER.debug("Registry persistent gespeichert.")
        except Exception as e:
            _LOGGER.exception("Fehler beim Speichern der Registry: %s", e)

    # ---------------- registration / deregistration ----------------
    def register_model(self, name: str, model_obj: Any, meta: Optional[Dict[str, Any]] = None, persist: bool = True) -> None:
        """
        Register an arbitrary model object. The model_obj must expose either:
            - async def generate(prompt, **kwargs)
            - def generate_sync(prompt, **kwargs)
        'meta' is stored in the registry.json (but model_obj is kept in memory).
        """
        if not name or not isinstance(name, str):
            raise ValueError("Model name must be a non-empty string")
        with self._lock:
            if name in self._models:
                raise KeyError(f"Model '{name}' already registered")
            # Basic capability check
            if not (hasattr(model_obj, "generate") or hasattr(model_obj, "generate_sync") or callable(model_obj)):
                raise TypeError("model_obj must implement generate (async) or generate_sync (sync) or be callable")
            # Wrap callables into LocalCallableModel
            if callable(model_obj) and not hasattr(model_obj, "generate") and not hasattr(model_obj, "generate_sync"):
                model_obj = LocalCallableModel(name, model_obj)

            self._models[name] = model_obj
            self._meta[name] = meta or {"source": "memory", "registered_at": int(__import__("time").time())}
            if persist:
                self._persist_registry_to_disk()
            _LOGGER.info("Model registriert: %s", name)

    def register_external_plugin(self, name: str, plugin_instance: Any, default_model: Optional[str] = None, meta: Optional[Dict[str, Any]] = None, persist: bool = True) -> None:
        """
        Register a plugin object (ExternalModelPlugin etc.). The plugin_instance should
        expose query/generate methods. We wrap it in ExternalPluginWrapper.
        """
        wrapper = ExternalPluginWrapper(name=name, plugin_instance=plugin_instance, default_model=default_model)
        meta = meta or {"source": "external_plugin", "info": getattr(plugin_instance, "__class__", {}).__name__ if plugin_instance else "plugin"}
        self.register_model(name, wrapper, meta=meta, persist=persist)

    def register_local_hf_model(self, name: str, model_name_or_path: str, device: Optional[str] = None, trust_remote_code: bool = False, meta: Optional[Dict[str, Any]] = None, persist: bool = True) -> None:
        """
        Load a model from HuggingFace (transformers) into memory and register it.
        Requires transformers & torch installed.
        """
        if not _HAS_TRANSFORMERS or not _HAS_TORCH:
            raise RuntimeError("transformers and torch are required to register_local_hf_model. Install them first.")
        # instantiate wrapper (heavy op)
        wrapper = HFModelWrapper(name, model_name_or_path, device=device, trust_remote_code=trust_remote_code)
        meta = meta or {"source": "huggingface", "repo": model_name_or_path}
        self.register_model(name, wrapper, meta=meta, persist=persist)

    def deregister_model(self, name: str, remove_meta: bool = True) -> None:
        with self._lock:
            if name in self._models:
                # try to gracefully stop model if it has stop()
                model = self._models[name]
                try:
                    if hasattr(model, "stop"):
                        maybe = getattr(model, "stop")
                        if callable(maybe):
                            maybe()
                except Exception:
                    _LOGGER.exception("Fehler beim Stoppen von Modell %s", name)
                del self._models[name]
            if remove_meta and name in self._meta:
                del self._meta[name]
                self._persist_registry_to_disk()
            _LOGGER.info("Model deregistriert: %s", name)

    # ---------------- accessors / lifecycle ----------------
    def get_model(self, name: str) -> Optional[Any]:
        with self._lock:
            return self._models.get(name)

    def list_models(self) -> List[str]:
        with self._lock:
            # union of in-memory models and persisted meta keys
            names = set(self._models.keys()) | set(self._meta.keys())
            return sorted(list(names))

    def start_model(self, name: str) -> None:
        with self._lock:
            model = self._models.get(name)
            if not model:
                raise KeyError(f"Model '{name}' not loaded")
            if hasattr(model, "start") and callable(getattr(model, "start")):
                model.start()
                _LOGGER.info("Model %s gestartet", name)
            else:
                _LOGGER.debug("Model %s hat keine start()-Methode", name)

    def stop_model(self, name: str) -> None:
        with self._lock:
            model = self._models.get(name)
            if not model:
                raise KeyError(f"Model '{name}' not loaded")
            if hasattr(model, "stop") and callable(getattr(model, "stop")):
                model.stop()
                _LOGGER.info("Model %s gestoppt", name)
            else:
                _LOGGER.debug("Model %s hat keine stop()-Methode", name)

    # ---------------- utility: reload from registry metadata ----------------
    def reload_from_registry(self) -> None:
        """
        Versucht, Modelle anhand persisted metadata neu zu laden.
        Only supports 'huggingface' entries if transformers installed.
        """
        with self._lock:
            for name, meta in list(self._meta.items()):
                src = meta.get("source")
                if name in self._models:
                    continue
                try:
                    if src == "huggingface" and _HAS_TRANSFORMERS and _HAS_TORCH:
                        repo = meta.get("repo")
                        if repo:
                            _LOGGER.info("Auto-loading HF model %s from registry", name)
                            self.register_local_hf_model(name, repo, persist=False)
                except Exception:
                    _LOGGER.exception("Fehler beim Auto-Laden von %s aus Registry", name)

    # ---------------- small helper ----------------
    def info(self) -> Dict[str, Any]:
        with self._lock:
            return {"count_loaded": len(self._models), "registered_meta": dict(self._meta)}

