from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional


HTML_TEMPLATE = """<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Free AI Network</title>
  <style>
    :root {
      --bg: #0a1322;
      --panel: #111f36;
      --accent: #25d1a2;
      --text: #e9f0f8;
      --muted: #9db0c8;
      --danger: #ff746c;
    }
    body {
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      background: radial-gradient(circle at 20% 10%, #15325e 0%, var(--bg) 65%);
      color: var(--text);
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 16px;
    }
    .app {
      width: min(980px, 100%);
      background: linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
      border: 1px solid rgba(255,255,255,0.12);
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 30px 80px rgba(0,0,0,0.35);
    }
    .head {
      padding: 14px 16px;
      border-bottom: 1px solid rgba(255,255,255,0.12);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      background: rgba(0,0,0,0.2);
    }
    .title {
      font-size: 14px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    .model {
      color: var(--muted);
      font-size: 13px;
    }
    #status {
      font-size: 12px;
      color: var(--muted);
    }
    .status-ok { color: var(--accent) !important; }
    .status-bad { color: var(--danger) !important; }
    .chat {
      height: 58vh;
      overflow: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      background: rgba(0,0,0,0.1);
    }
    .msg {
      max-width: 90%;
      border-radius: 12px;
      padding: 10px 12px;
      line-height: 1.5;
      white-space: pre-wrap;
      font-size: 15px;
    }
    .user {
      background: #225db3;
      margin-left: auto;
    }
    .assistant {
      background: #19314f;
      border: 1px solid rgba(255,255,255,0.1);
    }
    .controls {
      padding: 14px 16px;
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 10px;
      border-top: 1px solid rgba(255,255,255,0.12);
    }
    textarea {
      resize: vertical;
      min-height: 62px;
      max-height: 180px;
      border-radius: 10px;
      border: 1px solid rgba(255,255,255,0.18);
      background: #0f1b2f;
      color: var(--text);
      padding: 10px 12px;
      font-size: 15px;
    }
    button {
      border: 0;
      border-radius: 10px;
      cursor: pointer;
      padding: 0 14px;
      font-size: 14px;
      font-weight: 700;
      color: #07241d;
      background: var(--accent);
      min-height: 44px;
      transition: transform 120ms ease;
    }
    button:active { transform: translateY(1px); }
    #micBtn {
      color: #fff;
      background: #324f74;
    }
    #micBtn.recording {
      background: #b92d2d;
    }
    @media (max-width: 820px) {
      .controls {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <main class="app">
    <header class="head">
      <div>
        <div class="title">Free AI Network (Local)</div>
        <div class="model">Model: <span id="modelName">{model}</span></div>
      </div>
      <div id="status">Checking local backend...</div>
    </header>
    <section id="chat" class="chat"></section>
    <section class="controls">
      <textarea id="prompt" placeholder="Nachricht eingeben oder Mic drücken..."></textarea>
      <button id="micBtn" type="button">Mic Start</button>
      <button id="sendBtn" type="button">Senden</button>
    </section>
  </main>
  <script>
    const chatEl = document.getElementById("chat");
    const promptEl = document.getElementById("prompt");
    const sendBtn = document.getElementById("sendBtn");
    const micBtn = document.getElementById("micBtn");
    const statusEl = document.getElementById("status");
    const modelName = document.getElementById("modelName").textContent;

    function appendMessage(role, text) {
      const node = document.createElement("div");
      node.className = "msg " + role;
      node.textContent = text;
      chatEl.appendChild(node);
      chatEl.scrollTop = chatEl.scrollHeight;
    }

    async function checkHealth() {
      try {
        const res = await fetch("/api/health");
        const data = await res.json();
        if (data.ok) {
          statusEl.textContent = "Local backend online";
          statusEl.className = "status-ok";
        } else {
          statusEl.textContent = "Backend issue: " + (data.error || "unknown");
          statusEl.className = "status-bad";
        }
      } catch (err) {
        statusEl.textContent = "Backend unreachable";
        statusEl.className = "status-bad";
      }
    }

    async function sendPrompt() {
      const message = promptEl.value.trim();
      if (!message) return;
      promptEl.value = "";
      appendMessage("user", message);
      sendBtn.disabled = true;
      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message, model: modelName })
        });
        const data = await res.json();
        if (!res.ok) {
          appendMessage("assistant", "Fehler: " + (data.error || res.statusText));
        } else {
          appendMessage("assistant", data.reply || "(leer)");
        }
      } catch (err) {
        appendMessage("assistant", "Netzwerkfehler: " + err.message);
      } finally {
        sendBtn.disabled = false;
      }
    }

    sendBtn.addEventListener("click", sendPrompt);
    promptEl.addEventListener("keydown", (ev) => {
      if ((ev.metaKey || ev.ctrlKey) && ev.key === "Enter") {
        sendPrompt();
      }
    });

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    let rec = null;
    let recording = false;

    if (SpeechRecognition) {
      rec = new SpeechRecognition();
      rec.lang = "de-DE";
      rec.interimResults = true;
      rec.continuous = false;

      rec.onresult = (event) => {
        let finalText = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const t = event.results[i][0].transcript || "";
          if (event.results[i].isFinal) finalText += t + " ";
        }
        if (finalText.trim()) {
          promptEl.value = (promptEl.value + " " + finalText).trim();
        }
      };

      rec.onend = () => {
        recording = false;
        micBtn.classList.remove("recording");
        micBtn.textContent = "Mic Start";
      };
    } else {
      micBtn.disabled = true;
      micBtn.textContent = "Mic nicht verfuegbar";
    }

    micBtn.addEventListener("click", () => {
      if (!rec) return;
      if (!recording) {
        recording = true;
        micBtn.classList.add("recording");
        micBtn.textContent = "Mic Stop";
        rec.start();
      } else {
        rec.stop();
      }
    });

    checkHealth();
    appendMessage("assistant", "Lokaler Chat bereit. Model: " + modelName);
  </script>
</body>
</html>
"""


def _json_response(handler: BaseHTTPRequestHandler, status: int, payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(body)


def _read_json(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    length = int(handler.headers.get("Content-Length", "0") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def _ollama_request(base_url: str, payload: Dict[str, Any], timeout: int = 180) -> Dict[str, Any]:
    endpoint = base_url.rstrip("/") + "/api/generate"
    req = urllib.request.Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8") if exc.fp else str(exc)
        raise RuntimeError(f"Ollama HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama connection error: {exc}") from exc


def _ollama_health(base_url: str, timeout: int = 10) -> Dict[str, Any]:
    endpoint = base_url.rstrip("/") + "/api/tags"
    req = urllib.request.Request(endpoint, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            parsed = json.loads(raw)
            models = parsed.get("models") if isinstance(parsed, dict) else None
            count = len(models) if isinstance(models, list) else 0
            return {"ok": True, "model_count": count}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def build_handler(model: str, ollama_url: str) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "FreeNetwork/1.0"

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()

        def do_GET(self) -> None:
            if self.path == "/" or self.path.startswith("/index"):
                html = HTML_TEMPLATE.format(model=model).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html)))
                self.end_headers()
                self.wfile.write(html)
                return

            if self.path == "/api/health":
                _json_response(self, 200, _ollama_health(ollama_url))
                return

            _json_response(self, 404, {"ok": False, "error": "not found"})

        def do_POST(self) -> None:
            if self.path != "/api/chat":
                _json_response(self, 404, {"ok": False, "error": "not found"})
                return

            data = _read_json(self)
            message = str(data.get("message", "")).strip()
            if not message:
                _json_response(self, 400, {"ok": False, "error": "message is required"})
                return

            chosen_model = str(data.get("model", "")).strip() or model
            payload: Dict[str, Any] = {
                "model": chosen_model,
                "prompt": message,
                "stream": False,
            }
            system_prompt = str(data.get("system", "")).strip()
            if system_prompt:
                payload["system"] = system_prompt

            try:
                raw = _ollama_request(ollama_url, payload)
                reply = str(raw.get("response", "")).strip()
                _json_response(self, 200, {"ok": True, "reply": reply, "raw": raw})
            except Exception as exc:
                _json_response(self, 502, {"ok": False, "error": str(exc)})

        def log_message(self, format: str, *args: Any) -> None:
            return

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(description="Local free AI network server (mic + llama via Ollama)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    args = parser.parse_args()

    handler = build_handler(model=args.model, ollama_url=args.ollama_url)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(
        json.dumps(
            {
                "ok": True,
                "url": f"http://{args.host}:{args.port}",
                "model": args.model,
                "ollama_url": args.ollama_url,
            },
            ensure_ascii=False,
        )
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
