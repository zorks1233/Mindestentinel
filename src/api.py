# Safer src/api.py
# This API module only attempts to import modules from the src.api package (not the whole src package),
# and does so with try/except to avoid crashes when optional or heavy dependencies are missing.
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import os, pkgutil, importlib

app = FastAPI(title="Mindestentinel API (safe loader)")

def try_include(module_name: str):
    try:
        mod = importlib.import_module(module_name)
    except Exception as e:
        # import failed; skip this module but log to stdout for debugging.
        try:
            print(f"Skipping {module_name}: import failed: {e}")
        except Exception:
            pass
        return False
    # Look for common router names and include if present
    for attr in ("router", "api_router", "routes", "router_instance", "api"):
        obj = getattr(mod, attr, None)
        if obj is not None:
            try:
                app.include_router(obj)
                print(f"Included router from {module_name}.{attr}")
                return True
            except Exception:
                pass
    return False

# Discover modules inside the src.api package directory only
try:
    import src.api as _api_pkg
    pkg_path = getattr(_api_pkg, "__path__", None)
    if pkg_path:
        for finder, modname, ispkg in pkgutil.iter_modules(path=pkg_path):
            fullname = f"src.api.{modname}"
            try_include(fullname)
except Exception:
    # If src.api package doesn't exist or discovery fails, ignore silently
    pass

@app.get("/", response_class=PlainTextResponse)
def root():
    return "Mindestentinel API - OK (safe loader)"
