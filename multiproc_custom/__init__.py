
"""
multiproc_custom - a multiprocessing-like system using subprocesses + TCP broker.
Features:
  - Process(target=..., args=(), kwargs={}) where target can be:
     * a string "module:function" (recommended for cross-platform)
     * a picklable callable (will be pickled to a temp file)
  - Queue(name=None) - broker-mediated queue; use same name across processes.
  - Pool(n) - simple pool.map implementation (blocking).
Limitations:
  - Not a full drop-in replacement for stdlib multiprocessing but covers common patterns.
  - For best compatibility, use target as "module:function".
"""
from .manager import MultiprocManager, Process, Queue, Pool, ensure_manager, shutdown_manager

__all__ = ["MultiprocManager", "Process", "Queue", "Pool", "ensure_manager", "shutdown_manager"]
