
# Manager and public API for multiproc_custom
import os, sys, socket, threading, pickle, struct, time, subprocess, tempfile, uuid, traceback, types
from typing import Any, Callable, Optional, Dict, Tuple, List

# Message framing helpers (length-prefixed)
def _send_sock(sock: socket.socket, obj: Any):
    data = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
    sock.sendall(struct.pack(">I", len(data)) + data)

def _recv_sock(sock: socket.socket):
    hdr = sock.recv(4)
    if not hdr or len(hdr) < 4:
        raise EOFError("No header")
    (n,) = struct.unpack(">I", hdr)
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise EOFError("Premature EOF")
        buf.extend(chunk)
    return pickle.loads(bytes(buf))

class _BrokerServer(threading.Thread):
    def __init__(self, host="127.0.0.1", port=0):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self.port = self._sock.getsockname()[1]
        self._sock.listen(8)
        self._lock = threading.Lock()
        self._clients = {}  # client_id -> sock
        self._tasks = {}    # client_id -> (task_obj)
        self._queues = {}   # name -> list()
        self._results = {}  # client_id -> result/exception
        self._handlers = {}
        self._running = True

    def run(self):
        while self._running:
            try:
                conn, addr = self._sock.accept()
                t = threading.Thread(target=self._handle_client, args=(conn, addr), daemon=True)
                t.start()
            except Exception:
                break

    def _handle_client(self, conn: socket.socket, addr):
        try:
            # first message: handshake with client_id
            msg = _recv_sock(conn)
            client_id = msg.get("client_id")
            role = msg.get("role")
            # register
            with self._lock:
                self._clients[client_id] = conn
            # If a task is already assigned, send it
            while True:
                try:
                    cmd = _recv_sock(conn)
                except EOFError:
                    break
                if not isinstance(cmd, dict):
                    continue
                typ = cmd.get("type")
                if typ == "ready":
                    # send task if exists
                    task = None
                    with self._lock:
                        task = self._tasks.pop(client_id, None)
                    _send_sock(conn, {"type":"task", "task":task})
                elif typ == "result":
                    with self._lock:
                        self._results[client_id] = cmd.get("result")
                elif typ == "queue_put":
                    qn = cmd.get("queue")
                    item = cmd.get("item")
                    with self._lock:
                        self._queues.setdefault(qn, []).append(item)
                    # ack
                    _send_sock(conn, {"type":"ok"})
                elif typ == "queue_get":
                    qn = cmd.get("queue")
                    timeout = cmd.get("timeout", None)
                    start = time.time()
                    val = None
                    while True:
                        with self._lock:
                            q = self._queues.setdefault(qn, [])
                            if q:
                                val = q.pop(0)
                                break
                        if timeout is not None and (time.time() - start) > timeout:
                            break
                        time.sleep(0.05)
                    _send_sock(conn, {"type":"queue_item", "item": val})
                elif typ == "log":
                    # just print broker-side
                    print("[child log]", cmd.get("msg"))
                elif typ == "heartbeat":
                    _send_sock(conn, {"type":"pong"})
                else:
                    _send_sock(conn, {"type":"unknown"})
        except Exception as e:
            # print("client handler exception", e, traceback.format_exc())
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def assign_task(self, client_id, task_obj):
        with self._lock:
            self._tasks[client_id] = task_obj

    def get_result(self, client_id, timeout=None):
        start = time.time()
        while True:
            with self._lock:
                if client_id in self._results:
                    return self._results.pop(client_id)
            if timeout is not None and (time.time() - start) > timeout:
                return None
            time.sleep(0.05)

    def shutdown(self):
        self._running = False
        try:
            self._sock.close()
        except Exception:
            pass

_GLOBAL_BROKER = None

def ensure_manager():
    global _GLOBAL_BROKER
    if _GLOBAL_BROKER is None:
        srv = _BrokerServer(host="127.0.0.1", port=0)
        srv.start()
        _GLOBAL_BROKER = srv
    return _GLOBAL_BROKER

def shutdown_manager():
    global _GLOBAL_BROKER
    if _GLOBAL_BROKER is not None:
        _GLOBAL_BROKER.shutdown()
        _GLOBAL_BROKER = None

class Process:
    def __init__(self, target=None, args=(), kwargs=None, daemon=False, name=None):
        self.target = target
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.daemon = daemon
        self.name = name or ("proc-" + str(uuid.uuid4()))
        self._proc = None
        self._client_id = self.name
        self._pid = None
        self._exitcode = None

    def start(self):
        broker = ensure_manager()
        # Prepare task object
        task = {"target": None, "args": self.args, "kwargs": self.kwargs}
        if isinstance(self.target, str):
            # module:function form
            task["target"] = {"type":"importable", "spec": self.target}
        else:
            # pickle callable to a temp file for child to load
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pkl")
            pickle.dump(self.target, tf)
            tf.close()
            task["target"] = {"type":"pickle", "path": tf.name}
        # assign task for client id
        broker.assign_task(self._client_id, task)
        # start child process running worker pointing back to broker port and client id
        cmd = [sys.executable, os.path.join(os.path.dirname(__file__), "worker.py"),
               "--broker-host", broker.host, "--broker-port", str(broker.port), "--client-id", self._client_id]
        self._proc = subprocess.Popen(cmd)
        self._pid = self._proc.pid

    def join(self, timeout=None):
        if self._proc is not None:
            try:
                self._proc.wait(timeout=timeout)
                self._exitcode = self._proc.returncode
            except Exception:
                pass

    def is_alive(self):
        if self._proc is None:
            return False
        return self._proc.poll() is None

    def terminate(self):
        if self._proc is not None:
            try:
                self._proc.terminate()
            except Exception:
                pass

    @property
    def pid(self):
        return self._pid

    @property
    def exitcode(self):
        return self._exitcode

    def result(self, timeout=None):
        broker = ensure_manager()
        return broker.get_result(self._client_id, timeout=timeout)

class Queue:
    def __init__(self, name=None):
        self.name = name or "q-" + str(uuid.uuid4())

    def put(self, item):
        broker = ensure_manager()
        # connect and send queue_put
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((broker.host, broker.port))
        _send_sock(sock, {"client_id":"parent", "role":"parent"})
        _send_sock(sock, {"type":"queue_put", "queue": self.name, "item": item})
        # await ack
        try:
            resp = _recv_sock(sock)
        except Exception:
            resp = None
        try:
            sock.close()
        except Exception:
            pass
        return resp

    def get(self, timeout=None):
        broker = ensure_manager()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((broker.host, broker.port))
        _send_sock(sock, {"client_id":"parent", "role":"parent"})
        _send_sock(sock, {"type":"queue_get", "queue": self.name, "timeout": timeout})
        try:
            resp = _recv_sock(sock)
            return resp.get("item")
        except Exception:
            return None
        finally:
            try:
                sock.close()
            except Exception:
                pass

class Pool:
    def __init__(self, processes=2):
        self.processes = processes

    def map(self, func, iterable):
        procs = []
        for i, item in enumerate(iterable):
            p = Process(target=func, args=(item,), name=f"pool-{i}")
            p.start()
            procs.append(p)
            # limit concurrency
            while len([x for x in procs if x.is_alive()]) >= self.processes:
                time.sleep(0.05)
        results = []
        for p in procs:
            p.join()
            results.append(p.result(timeout=5))
        return results
