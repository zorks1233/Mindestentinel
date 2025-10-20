# src/api package __init__.py - safe app creation and router inclusion
from fastapi import FastAPI
import pkgutil, importlib

app = FastAPI(title="Mindestentinel API (package init)")

def _try_include(module_name: str):
    try:
        mod = importlib.import_module(module_name)
    except Exception as e:
        try:
            print(f"Skipping {module_name}: import failed: {e}")
        except Exception:
            pass
        return False
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

# Discover and include routers from submodules of this package (src.api.*)
try:
    pkg_path = __path__
    for finder, name, ispkg in pkgutil.iter_modules(path=pkg_path):
        fullname = __name__ + "." + name
        _try_include(fullname)
except Exception:
    pass

# expose a simple root if nothing else
@app.get("/")
def _root():
    return {"status": "ok", "source": "src.api.__init__"}
