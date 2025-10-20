# src/core/plugin_manager.py
import importlib
import os
import sys
from types import ModuleType
from typing import Dict

class PluginManager:
    def __init__(self, plugin_dir: str = None):
        self.plugin_dir = plugin_dir
        self._plugins: Dict[str, ModuleType] = {}

    def discover(self):
        if not self.plugin_dir:
            return []
        candidates = []
        for entry in os.listdir(self.plugin_dir):
            if entry.endswith('.py') and not entry.startswith('_'):
                candidates.append(entry[:-3])
        return candidates

    def load(self, name: str):
        if name in self._plugins:
            return self._plugins[name]
        # load by importlib using package-style import if available, else file spec
        try:
            mod = importlib.import_module(name)
        except Exception:
            # try by path import
            path = os.path.join(self.plugin_dir, name + '.py') if self.plugin_dir else None
            if path and os.path.exists(path):
                import importlib.util
                spec = importlib.util.spec_from_file_location(name, path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
            else:
                raise
        self._plugins[name] = mod
        return mod
