import socket, threading, pickle, struct, time, subprocess, tempfile, uuid, os, sys
def _send(sock,obj):
    data = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
    sock.sendall(struct.pack(">I", len(data))+data)
def _recv(sock):
    hdr = sock.recv(4)
    if not hdr or len(hdr)<4: raise EOFError
    n = struct.unpack(">I", hdr)[0]
    buf = b''
    while len(buf)<n:
        chunk = sock.recv(n-len(buf))
        if not chunk: raise EOFError
        buf += chunk
    return pickle.loads(buf)
class _Broker(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        self.sock.bind(("127.0.0.1",0))
        self.port = self.sock.getsockname()[1]
        self.sock.listen(8)
        self.lock = threading.Lock()
        self.queues = {}
        self.tasks = {}
        self.results = {}
        self.running = True
    def run(self):
        while self.running:
            try:
                conn,addr = self.sock.accept()
                threading.Thread(target=self._handle, args=(conn,), daemon=True).start()
            except Exception:
                break
    def _handle(self,conn):
        try:
            msg = _recv(conn)
            cid = msg.get("client_id")
            role = msg.get("role")
            while True:
                cmd = _recv(conn)
                typ = cmd.get("type")
                if typ=="ready":
                    t = None
                    with self.lock:
                        t = self.tasks.pop(cid, None)
                    _send(conn, {"type":"task", "task": t})
                elif typ=="result":
                    with self.lock:
                        self.results[cid] = cmd.get("result")
                elif typ=="queue_put":
                    q = cmd.get("queue")
                    item = cmd.get("item")
                    with self.lock:
                        self.queues.setdefault(q, []).append(item)
                    _send(conn, {"type":"ok"})
                elif typ=="queue_get":
                    q = cmd.get("queue"); timeout = cmd.get("timeout", None)
                    start = time.time(); val=None
                    while True:
                        with self.lock:
                            qq = self.queues.setdefault(q, [])
                            if qq:
                                val = qq.pop(0); break
                        if timeout is not None and time.time()-start>timeout: break
                        time.sleep(0.05)
                    _send(conn, {"type":"queue_item", "item": val})
                else:
                    _send(conn, {"type":"unknown"})
        except Exception:
            pass
        finally:
            try: conn.close()
            except: pass
    def assign(self, cid, task): 
        with self.lock: self.tasks[cid]=task
    def get_result(self, cid, timeout=None):
        start=time.time()
        while True:
            with self.lock:
                if cid in self.results: return self.results.pop(cid)
            if timeout is not None and time.time()-start>timeout: return None
            time.sleep(0.05)
    def shutdown(self):
        self.running=False
        try: self.sock.close()
        except: pass
_BROKER=None
def ensure_manager():
    global _BROKER
    if _BROKER is None:
        _BROKER = _Broker(); _BROKER.start()
    return _BROKER
def shutdown_manager():
    global _BROKER
    if _BROKER is not None:
        _BROKER.shutdown(); _BROKER=None
class Process:
    def __init__(self,target=None,args=(),kwargs=None,name=None):
        self.target=target; self.args=args; self.kwargs=kwargs or {}; self.name=name or "proc-"+str(uuid.uuid4())
        self._proc=None; self._pid=None; self._exit=None
    def start(self):
        b=ensure_manager()
        task={"target": None, "args": self.args, "kwargs": self.kwargs}
        if isinstance(self.target, str):
            task["target"] = {"type":"importable","spec":self.target}
        else:
            tf = tempfile.NamedTemporaryFile(delete=False); pickle.dump(self.target, tf); tf.close()
            task["target"] = {"type":"pickle","path":tf.name}
        b.assign(self.name, task)
        cmd=[sys.executable, os.path.join(os.path.dirname(__file__),"worker.py"), "--broker-host", "127.0.0.1", "--broker-port", str(b.port), "--client-id", self.name]
        self._proc = subprocess.Popen(cmd); self._pid=self._proc.pid
    def join(self, timeout=None):
        if self._proc: 
            try: self._proc.wait(timeout=timeout); self._exit=self._proc.returncode
            except: pass
    def is_alive(self): return self._proc is not None and self._proc.poll() is None
    def terminate(self): 
        try: self._proc.terminate()
        except: pass
    def result(self, timeout=None):
        return ensure_manager().get_result(self.name, timeout=timeout)
class Queue:
    def __init__(self,name=None): self.name = name or "q-"+str(uuid.uuid4())
    def put(self,item):
        b=ensure_manager(); s=socket.socket(); s.connect(("127.0.0.1", b.port)); _send(s, {"client_id":"parent","role":"parent"}); _send(s, {"type":"queue_put","queue":self.name,"item":item}); 
        try: r=_recv(s)
        except: r=None
        try: s.close()
        except: pass
        return r
    def get(self, timeout=None):
        b=ensure_manager(); s=socket.socket(); s.connect(("127.0.0.1", b.port)); _send(s, {"client_id":"parent","role":"parent"}); _send(s, {"type":"queue_get","queue":self.name,"timeout":timeout});
        try: r=_recv(s); return r.get("item")
        except: return None
    def qsize(self):
        return 0
class Pool:
    def __init__(self, processes=2): self.processes=processes
    def map(self, func, iterable):
        procs=[]; results=[]
        for i,it in enumerate(iterable):
            p=Process(target=func,args=(it,),name=f"pool-{i}"); p.start(); procs.append(p)
            while len([x for x in procs if x.is_alive()])>=self.processes: time.sleep(0.05)
        for p in procs:
            p.join(); results.append(p.result(timeout=5))
        return results
