try:
    from multiproc_custom import manager as _mgr
except Exception:
    _mgr = None

if _mgr is not None:
    Process = _mgr.Process
    Queue = _mgr.Queue
    Pool = _mgr.Pool
    ensure_manager = _mgr.ensure_manager
    shutdown_manager = _mgr.shutdown_manager
    freeze_support = getattr(_mgr, 'freeze_support', lambda: None)
    cpu_count = getattr(_mgr, 'cpu_count', lambda: 1)
    Event = getattr(_mgr, 'Event', None)
else:
    import threading as _threading, queue as _queue, os as _os
    class Event:
        def __init__(self): self._ev = _threading.Event()
        def set(self): self._ev.set()
        def clear(self): self._ev.clear()
        def is_set(self): return self._ev.is_set()
        def wait(self, timeout=None): return self._ev.wait(timeout)
    class Queue:
        def __init__(self): self._q = _queue.Queue()
        def put(self, item): return self._q.put(item)
        def get(self, timeout=None): return self._q.get(timeout)
    class Process:
        def __init__(self, target=None, args=(), kwargs=None, daemon=False, name=None):
            self._t = _threading.Thread(target=target, args=args, kwargs=kwargs or {}, daemon=daemon)
        def start(self): self._t.start()
        def join(self, timeout=None): self._t.join(timeout)
        def is_alive(self): return self._t.is_alive()
        def terminate(self): pass
    def ensure_manager(): return None
    def shutdown_manager(): return None
    def freeze_support(): return None
    def cpu_count(): return _os.cpu_count() or 1
    Pool = None
