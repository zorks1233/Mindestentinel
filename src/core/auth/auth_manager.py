# src/core/auth/auth_manager.py
class AuthManager:
    """Konsolidierter AuthManager - stub für Token/Password/Strategy-Migration."""
    def __init__(self):
        self._strategies = {}

    def register_strategy(self, name, callable):
        self._strategies[name] = callable

    def authenticate(self, name, *args, **kwargs):
        if name not in self._strategies:
            raise KeyError(f"No auth strategy {name}")
        return self._strategies[name](*args, **kwargs)
