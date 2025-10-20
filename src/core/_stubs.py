# Auto-generated stubs for optional heavy dependencies
class _MissingDependencyProxy:
    def __init__(self, name):
        self._name = name
    def __call__(self, *args, **kwargs):
        raise RuntimeError(f"Dependency '{self._name}' is not installed. Install it to use this functionality.")
    def __getattr__(self, item):
        raise RuntimeError(f"Dependency '{self._name}' is not installed. Install it to use this functionality.")

class AutoModelForCausalLM(_MissingDependencyProxy): pass
class AutoTokenizer(_MissingDependencyProxy): pass
AutoModelForCausalLM = _MissingDependencyProxy('transformers.AutoModelForCausalLM')
AutoTokenizer = _MissingDependencyProxy('transformers.AutoTokenizer')

class TensorPlaceholder(_MissingDependencyProxy): pass
Tensor = _MissingDependencyProxy('torch.Tensor')

def safe_load(*args, **kwargs):
    raise RuntimeError("PyYAML (yaml) is not installed. Install pyyaml to use YAML features.")

def load(*args, **kwargs):
    raise RuntimeError("PyYAML (yaml) is not installed. Install pyyaml to use YAML features.")

transformers = _MissingDependencyProxy('transformers')
torch = _MissingDependencyProxy('torch')
yaml = _MissingDependencyProxy('yaml')

# zstandard stub
class ZstdCompressor(_MissingDependencyProxy): pass
zstandard = _MissingDependencyProxy("zstandard")

# Transformers Trainer placeholders
class TrainingArguments(_MissingDependencyProxy): pass
class Trainer(_MissingDependencyProxy): pass
TrainingArguments = _MissingDependencyProxy('transformers.TrainingArguments')
Trainer = _MissingDependencyProxy('transformers.Trainer')
