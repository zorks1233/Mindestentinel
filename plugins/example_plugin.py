# example plugin 
# plugins/example_plugin.py
class ExamplePlugin:
    """Ein einfacher Plugin-Stub, der einen Satz zurückliefert."""

    def __init__(self, name: str = "example"):
        self.name = name

    def process(self, data: str) -> str:
        return f"[{self.name}] {data}"
