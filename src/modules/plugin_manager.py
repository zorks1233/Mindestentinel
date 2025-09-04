# src/modules/plugin_manager.py
"""
PluginManager
- Lädt Plugin-Module aus dem 'plugins' Verzeichnis
- Führt plugin method calls in separaten Prozessen aus, um Abstürze/Sicherheit zu isolieren
- API:
    load_plugins_from_dir(directory)
    register_plugin(name, module_or_instance)
    unregister_plugin(name)
    call_plugin(name, method, *args, timeout=10, **kwargs)
"""

from __future__ import annotations
import importlib
import inspect
import multiprocessing
import os
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import Any, Dict, Optional, Callable

# ensure plugins package is in path
ROOT = Path.cwd()
PLUGINS_DIR = ROOT / "plugins"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def _plugin_worker(module_name: str, attr_name: Optional[str], method: str, args: tuple, kwargs: dict, conn):
    """
    Worker-Funktion, läuft im Kindprozess.
    Lädt das Modul, extrahiert Klasse/Funktion und ruft die Methode auf.
    Sendet (True, result) bei Erfolg, oder (False, error_str) bei Fehler über conn.
    """
    try:
        mod = importlib.import_module(module_name)
        target = None
        if attr_name:
            target = getattr(mod, attr_name)
        else:
            # if module-level provide default 'Plugin' class or 'process' function
            if hasattr(mod, "Plugin"):
                target = getattr(mod, "Plugin")
            else:
                # fallback: pick first callable in module
                for k, v in mod.__dict__.items():
                    if callable(v) and not k.startswith("_"):
                        target = v
                        break
        # instantiate or call directly
        instance = None
        if inspect.isclass(target):
            instance = target()
            if not hasattr(instance, method):
                raise AttributeError(f"Target has no method '{method}'")
            fn = getattr(instance, method)
            if inspect.iscoroutinefunction(fn):
                # no event loop here, run sync
                import asyncio
                res = asyncio.run(fn(*args, **kwargs))
            else:
                res = fn(*args, **kwargs)
        elif callable(target):
            # target is function, call it directly
            res = target(*args, **kwargs)
        else:
            raise TypeError("No callable target found in plugin module")

        conn.send(("ok", res))
    except Exception:
        tb = traceback.format_exc()
        try:
            conn.send(("error", tb))
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass

class PluginManager:
    def __init__(self, plugins_dir: Optional[str] = None):
        self.plugins_dir = Path(plugins_dir) if plugins_dir else PLUGINS_DIR
        self._lock = threading.RLock()
        self._registry: Dict[str, Dict[str, Any]] = {}  # name -> {module, instance, meta}
        # ensure directory is importable by package name 'plugins'
        if str(self.plugins_dir.parent) not in sys.path:
            sys.path.insert(0, str(self.plugins_dir.parent))

    def load_plugins_from_dir(self) -> int:
        """Findet Python-Dateien im plugins-Dir und lädt sie als Module."""
        count = 0
        if not self.plugins_dir.exists():
            return 0
        for p in self.plugins_dir.glob("*.py"):
            name = p.stem
            if name == "__init__":
                continue
            try:
                module_name = f"plugins.{name}"
                self.register_plugin_from_module(module_name)
                count += 1
            except Exception:
                # skip faulty plugin but keep processing
                continue
        return count

    def register_plugin_from_module(self, module_name: str, attr_name: Optional[str] = None, meta: Optional[dict] = None) -> None:
        """
        Lädt ein Plugin-Modul und registriert es unter dem Modulname (oder meta['name']).
        """
        with self._lock:
            if module_name in self._registry:
                raise KeyError(f"Plugin {module_name} bereits registriert")
            mod = importlib.import_module(module_name)
            # determine public name
            name = meta.get("name") if meta and "name" in meta else module_name
            self._registry[name] = {"module": module_name, "attr": attr_name, "instance": None, "meta": meta or {}}

    def register_plugin_instance(self, name: str, instance: Any, meta: Optional[dict] = None) -> None:
        """Direkte Registrierung einer Instanz (bereits importiert)."""
        with self._lock:
            if name in self._registry:
                raise KeyError(f"Plugin {name} bereits registriert")
            self._registry[name] = {"module": getattr(instance, "__module__", None), "attr": getattr(instance, "__class__", None).__name__, "instance": instance, "meta": meta or {}}

    def unregister_plugin(self, name: str) -> None:
        with self._lock:
            if name in self._registry:
                del self._registry[name]
            else:
                raise KeyError(f"Plugin {name} nicht registriert")

    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {k: v["meta"] for k, v in self._registry.items()}

    def call_plugin(self, name: str, method: str, *args, timeout: float = 10.0, **kwargs) -> Any:
        """
        Führt method auf Plugin name in einem separaten Prozess aus.
        Timeout in Sekunden. Liefert Ergebnis oder wirft Exception.
        """
        with self._lock:
            if name not in self._registry:
                raise KeyError(f"Plugin {name} nicht registriert")
            entry = self._registry[name]
            module_name = entry["module"]
            attr = entry.get("attr")
            # create a multiprocessing connection
            parent_conn, child_conn = multiprocessing.Pipe()
            p = multiprocessing.Process(target=_plugin_worker, args=(module_name, attr, method, args, kwargs, child_conn), daemon=True)
            p.start()
            start = time.time()
            result = None
            try:
                # wait for data up to timeout
                if parent_conn.poll(timeout):
                    status, payload = parent_conn.recv()
                    if status == "ok":
                        result = payload
                    else:
                        raise RuntimeError(f"Plugin error: {payload}")
                else:
                    # timeout - ensure process terminated
                    p.terminate()
                    raise TimeoutError(f"Plugin call timeout after {timeout}s")
            finally:
                try:
                    parent_conn.close()
                except Exception:
                    pass
                if p.is_alive():
                    p.terminate()
                p.join(timeout=1.0)
            return result
