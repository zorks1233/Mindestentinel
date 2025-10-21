import argparse, socket, pickle, struct, sys, os, importlib, traceback, time
parser = argparse.ArgumentParser(); parser.add_argument("--broker-host", required=True); parser.add_argument("--broker-port", required=True, type=int); parser.add_argument("--client-id", required=True)
args = parser.parse_args()
def _send(sock,obj):
    data = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL); sock.sendall(struct.pack(">I", len(data))+data)
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
sock = socket.socket(); sock.connect((args.broker_host, args.broker_port))
_send(sock, {"client_id": args.client_id, "role":"worker"})
_send(sock, {"type":"ready"})
msg = _recv(sock)
task = msg.get("task")
result=None; exitcode=0
try:
    if task is None:
        result=None
    else:
        t = task.get("target")
        if t.get("type")=="importable":
            spec = t.get("spec")
            if ":" in spec: module_name, func_name = spec.split(":",1)
            elif "." in spec: module_name, func_name = spec.rsplit(".",1)
            else: raise RuntimeError("Invalid spec")
            mod = importlib.import_module(module_name); func = getattr(mod, func_name); result = func(*task.get("args",()), **task.get("kwargs",{}))
        elif t.get("type")=="pickle":
            p = t.get("path"); fh=open(p,"rb"); obj=pickle.load(fh); fh.close(); result = obj(*task.get("args",()), **task.get("kwargs",{}))
except Exception as e:
    exitcode=1; tb = traceback.format_exc()
    try: _send(sock, {"type":"log", "msg": tb})
    except: pass
    result = {"__exception__": True, "type": str(e), "trace": tb}
try: _send(sock, {"type":"result", "result": result, "exitcode": exitcode})
except: pass
try: sock.close()
except: pass
sys.exit(exitcode)
