"""Connect to a running headless Chrome (--remote-debugging-port) via CDP,
navigate to a URL, and print console messages + JS exceptions."""
import json
import sys
import time
import requests
import websocket

PORT = 9333
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173/"

tabs = requests.put(f"http://localhost:{PORT}/json/new?{URL}").json()
ws_url = tabs["webSocketDebuggerUrl"]

ws = websocket.create_connection(ws_url, timeout=15)
msg_id = 0


def send(method, params=None):
    global msg_id
    msg_id += 1
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    return msg_id


send("Runtime.enable")
send("Page.enable")
send("Log.enable")

time.sleep(6)  # let the SPA fetch + render

console_lines = []
deadline = time.time() + 2
ws.settimeout(1)
while time.time() < deadline:
    try:
        raw = ws.recv()
    except Exception:
        continue
    try:
        evt = json.loads(raw)
    except Exception:
        continue
    method = evt.get("method", "")
    if method == "Runtime.consoleAPICalled":
        p = evt["params"]
        args = " ".join(str(a.get("value", a.get("description", ""))) for a in p.get("args", []))
        console_lines.append(f"[console.{p['type']}] {args}")
    elif method == "Runtime.exceptionThrown":
        ex = evt["params"]["exceptionDetails"]
        console_lines.append(f"[EXCEPTION] {ex.get('text')} -- {ex.get('exception', {}).get('description', '')}")
    elif method == "Log.entryAdded":
        e = evt["params"]["entry"]
        console_lines.append(f"[log.{e['level']}] {e['text']}")

print(f"=== Console output for {URL} ===")
if not console_lines:
    print("(no console messages or exceptions captured)")
for line in console_lines:
    print(line[:400])

ws.close()
