# src/core/container.py
class ServiceContainer:
    def __init__(self):
        self._factories = {}
        self._singletons = {}

    def register_factory(self, name, factory):
        self._factories[name] = factory

    def register(self, name, instance):
        self._singletons[name] = instance

    def resolve(self, name):
        if name in self._singletons:
            return self._singletons[name]
        if name in self._factories:
            inst = self._factories[name](self)
            self._singletons[name] = inst
            return inst
        raise KeyError(f"Service {name} not registered")
