
# worker script invoked as a separate python process.
import argparse, socket, pickle, struct, sys, os, traceback, importlib, time
parser = argparse.ArgumentParser()
parser.add_argument("--broker-host", required=True)
parser.add_argument("--broker-port", required=True, type=int)
parser.add_argument("--client-id", required=True)
args = parser.parse_args()

def _send_sock(sock, obj):
    data = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
    sock.sendall(struct.pack(">I", len(data)) + data)

def _recv_sock(sock):
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

broker_addr = (args.broker_host, args.broker_port)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(broker_addr)
# handshake
_send_sock(sock, {"client_id": args.client_id, "role": "worker"})
# signal ready and request task
_send_sock(sock, {"type":"ready"})
msg = _recv_sock(sock)
task = msg.get("task")
result = None
exitcode = 0
try:
    if task is None:
        # nothing to do; exit
        result = None
    else:
        t = task.get("target")
        if t.get("type") == "importable":
            spec = t.get("spec")
            # spec format: "module:function"
            if ":" in spec:
                module_name, func_name = spec.split(":", 1)
            elif "." in spec:
                module_name, func_name = spec.rsplit(".", 1)
            else:
                raise RuntimeError("Invalid spec for importable: " + spec)
            mod = importlib.import_module(module_name)
            func = getattr(mod, func_name)
            result = func(*task.get("args", ()), **task.get("kwargs", {}))
        elif t.get("type") == "pickle":
            p = t.get("path")
            with open(p, "rb") as fh:
                obj = pickle.load(fh)
            # obj should be callable
            result = obj(*task.get("args", ()), **task.get("kwargs", {}))
        else:
            result = None
except Exception as e:
    exitcode = 1
    tb = traceback.format_exc()
    # send log
    try:
        _send_sock(sock, {"type":"log", "msg": tb})
    except Exception:
        pass
    result = {"__exception__": True, "type": str(e), "trace": tb}
# send result
try:
    _send_sock(sock, {"type":"result", "result": result, "exitcode": exitcode})
except Exception:
    pass
try:
    sock.close()
except Exception:
    pass
# exit with appropriate code
sys.exit(exitcode)
