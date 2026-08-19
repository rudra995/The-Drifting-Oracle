"""Real wall-clock check (no virtual-time-budget) of whether the Dashboard's
KPI cards / PSI chart actually resolve their framer-motion opacity animation
given real time to run, sidestepping any headless rAF/virtual-time ambiguity."""
import json
import sys
import time
import requests
import websocket

PORT = 9333
URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5173/"
WAIT = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0

tab = requests.put(f"http://localhost:{PORT}/json/new?{URL}").json()
ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=20)
msg_id = 0


def send(method, params=None):
    global msg_id
    msg_id += 1
    ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
    while True:
        raw = ws.recv()
        evt = json.loads(raw)
        if evt.get("id") == msg_id:
            return evt


send("Runtime.enable")
time.sleep(WAIT)  # real wall-clock wait, no virtual time

result = send("Runtime.evaluate", {
    "expression": """
        JSON.stringify(
            Array.from(document.querySelectorAll('.glass-panel'))
                .map(el => ({
                    text: (el.querySelector('h3,h4')?.textContent || '').slice(0, 40),
                    opacity: getComputedStyle(el).opacity,
                }))
        )
    """,
    "returnByValue": True,
})
print(result["result"]["result"]["value"])
ws.close()
