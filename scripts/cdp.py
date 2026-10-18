#!/usr/bin/env python3
"""Mini-client CDP (Chrome Debug Protocol) sur le port 9222.

Usage:
    python scripts/cdp.py list
    python scripts/cdp.py open <url>
    python scripts/cdp.py eval <tab-substring> <js-expression>
    python scripts/cdp.py snap <tab-substring>        # DOM text de la page
    python scripts/cdp.py cmd <tab-substring> <method> [json-params]
"""

import json
import sys
import time
import urllib.request

CDP = "http://127.0.0.1:9222"


def http_get(path):
    with urllib.request.urlopen(CDP + path, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))


def list_pages():
    return [p for p in http_get("/json/list") if p.get("type") == "page"]


def find_tab(sub):
    for p in list_pages():
        if sub.lower() in (p.get("title", "") + " " + p.get("url", "")).lower():
            return p
    return None


def open_tab(url):
    req = urllib.request.Request(CDP + "/json/new?" + url, method="PUT")
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


class Tab:
    def __init__(self, ws_url):
        import websocket
        # Chrome rejette toute origine non d�clar�e dans --remote-allow-origins :
        # on n'envoie AUCUNE origine (Chrome l'accepte alors).
        # timeout long : certaines évaluations (scroll/lenteurs) > 60 s.
        self.ws = websocket.create_connection(
            ws_url, timeout=300, suppress_origin=True)
        self.mid = 0

    def call(self, method, params=None):
        self.mid += 1
        self.ws.send(json.dumps({"id": self.mid, "method": method,
                                 "params": params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.mid:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})

    def evaluate(self, expr):
        if expr.startswith("@"):
            # "@fichier.js" : expression lue dans un fichier (évite les
            # pièges d'échappement des shells).
            with open(expr[1:], encoding="utf-8") as f:
                expr = f.read()
        res = self.call("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True,
        })
        if "exceptionDetails" in res:
            det = res["exceptionDetails"]
            txt = det.get("exception", {}).get("description") or det.get("text")
            raise RuntimeError(txt)
        return res.get("result", {}).get("value")

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass

    def set_file_inputs(self, paths, selector='input[type="file"]'):
        """Renseigne un <input type=file> (impossible via JS seul, s�curit� navigateur)."""
        self.call("DOM.enable")
        doc = self.call("DOM.getDocument", {"depth": -1})
        node = self.call("DOM.querySelector", {
            "nodeId": doc["root"]["nodeId"], "selector": selector})
        if not node.get("nodeId"):
            raise RuntimeError(f"input fichier introuvable: {selector}")
        self.call("DOM.setFileInputFiles",
                  {"files": paths, "nodeId": node["nodeId"]})


def wait_for(sub, timeout=60, poll=2):
    end = time.time() + timeout
    while time.time() < end:
        p = find_tab(sub)
        if p:
            return p
        time.sleep(poll)
    raise SystemExit(f"onglet introuvable: {sub}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "list":
        for p in list_pages():
            print(f"{p['id']}  {p.get('title','')[:60]!r}  {p.get('url','')}")

    elif cmd == "open":
        p = open_tab(sys.argv[2])
        print(p["id"], p["url"])

    elif cmd in ("eval", "snap", "cmd", "file", "shot"):
        sub = sys.argv[2]
        p = wait_for(sub)
        tab = Tab(p["webSocketDebuggerUrl"])
        try:
            if cmd == "eval":
                out = tab.evaluate(sys.argv[3])
                print(json.dumps(out, ensure_ascii=False, indent=2)
                      if not isinstance(out, str) else out)
            elif cmd == "snap":
                expr = ("document.body ? (document.body.innerText||'').slice(0,8000)"
                        " : ''")
                print(tab.evaluate(expr))
            elif cmd == "file":
                files = [a for a in sys.argv[3:] if a]
                tab.set_file_inputs(files)
                print(f"OK: {len(files)} fichier(s) assigné(s)")
            elif cmd == "shot":
                tab.call("Page.enable")
                res = tab.call("Page.captureScreenshot", {"format": "png"})
                out = sys.argv[3] if len(sys.argv) > 3 else "temp/shot.png"
                import base64
                with open(out, "wb") as f:
                    f.write(base64.b64decode(res["data"]))
                print("OK:", out)
            else:  # cmd
                params = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
                print(json.dumps(tab.call(sys.argv[3], params),
                                 ensure_ascii=False, indent=2))
        finally:
            tab.close()

    else:
        print(__doc__)


if __name__ == "__main__":
    main()
