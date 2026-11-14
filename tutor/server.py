#!/usr/bin/env python3
"""Worksheet server plus one persistent Claude tutor session.

The tutor writes live/worksheet.json; the student's submissions are appended
to live/answers.jsonl and forwarded to the tutor. Both files are wiped on
startup — sessions are not kept. Student notes in notes/ persist.
"""
import json
import queue
import random
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from anki_cards import Cards
from explainer.renderer import Explainers

ROOT = Path(__file__).resolve().parent
LIVE = ROOT / "live"
WORKSHEET = LIVE / "worksheet.json"
ANSWERS = LIVE / "answers.jsonl"
PAGE = ROOT / "worksheet.html"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8770  # 8765 is taken by AnkiConnect

TUTOR_CMD = [
    "claude", "-p",
    "--input-format", "stream-json", "--output-format", "stream-json", "--verbose",
    "--permission-mode", "acceptEdits",
    "--allowedTools", "Read", "Edit", "Write", "Glob", "Grep",
    # Read access to the card makers' guides (e.g. Vocab/CLAUDE.md); the tutor only
    # writes card specs, and the server runs the makers.
    "--add-dir", str(ROOT.parent / "Vocab"),
]
START_MESSAGE = (
    "The worksheet server is running and the student has the page open. "
    "Read notes/, then write 3 questions to live/worksheet.json, one per thread. "
    "From now on, each message I send is one or more student submissions."
)

SWITCH_PROBABILITY = 0.15  # per submission; switches the subject of that question's thread
MAX_SUGGESTION = 2000      # characters

submit_lock = threading.Lock()
inbox = queue.Queue()   # messages for the tutor
explainers = Explainers(LIVE, inbox.put)
cards = Cards(LIVE, inbox.put)


def read_answers():
    answers = {}
    if ANSWERS.exists():
        for line in ANSWERS.read_text().splitlines():
            if line.strip():
                entry = json.loads(line)
                answers[entry["id"]] = entry
    return answers


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def run_tutor(proc):
    """Feed queued messages to a single long-lived Claude session, one turn at a time."""
    while True:
        # Batch everything that arrived while the tutor was busy into one turn.
        messages = [inbox.get()]
        while not inbox.empty():
            messages.append(inbox.get())
        text = "\n".join(messages)

        log(f"tutor ← {text}")
        started = time.monotonic()
        proc.stdin.write(json.dumps({"type": "user", "message": {"role": "user", "content": text}}) + "\n")
        proc.stdin.flush()

        for line in proc.stdout:
            event = json.loads(line)
            if event["type"] == "result":
                status = "done" if event.get("subtype") == "success" else f"error: {event.get('subtype')}"
                log(f"tutor {status} ({time.monotonic() - started:.0f}s)")
                break
        else:
            log(f"tutor process exited (code {proc.wait()}); restart the server")
            return


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, content_type="application/json"):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self.path = urlsplit(self.path).path
        if self.path in ("/", "/index.html"):
            self.send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif self.path == "/state":
            try:
                worksheet = json.loads(WORKSHEET.read_text())
            except (OSError, json.JSONDecodeError):
                # Tutor may be mid-write; the page just retries.
                self.send(503, '{"error": "worksheet not ready"}')
                return
            self.send(200, json.dumps({"worksheet": worksheet, "answers": read_answers(),
                                       "explainers": explainers.states(), "cards": cards.states()}))
        elif self.path.startswith("/explainers/") and self.path.endswith(".mp4"):
            video = explainers.video(self.path[len("/explainers/"):-len(".mp4")])
            if video:
                self.send(200, video.read_bytes(), "video/mp4")
            else:
                self.send(404, '{"error": "no such explainer"}')
        else:
            self.send(404, '{"error": "not found"}')

    def do_POST(self):
        if self.path not in ("/submit", "/suggest", "/cards/accept"):
            self.send(404, '{"error": "not found"}')
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        except (TypeError, ValueError):
            self.send(400, '{"error": "bad request"}')
            return
        if self.path == "/suggest":
            self.suggest(body)
        elif self.path == "/cards/accept":
            self.accept_cards(body)
        else:
            self.submit(body)

    def accept_cards(self, body):
        """The student accepted a question's card proposal: only now are cards written."""
        qid = body.get("id")
        try:
            questions = json.loads(WORKSHEET.read_text()).get("questions", [])
        except (OSError, json.JSONDecodeError):
            self.send(503, '{"error": "worksheet not ready"}')
            return
        q = next((q for q in questions if q.get("id") == qid), None)
        error = cards.accept(qid, q.get("card_proposal") if q else None)
        if error:
            self.send(400, json.dumps({"error": error}))
        else:
            self.send(200, '{"ok": true}')

    def suggest(self, body):
        """A free-text request from the student: a new subject, a goal, a preference."""
        text = str(body.get("text", "")).strip()
        if not text or len(text) > MAX_SUGGESTION:
            self.send(400, '{"error": "empty or too long"}')
            return
        log(f"suggestion: {text}")
        inbox.put(json.dumps({"suggestion": text}))
        self.send(200, '{"ok": true}')

    def submit(self, body):
        qid, answer = body.get("id"), body.get("answer", "")
        with submit_lock:
            if not qid or qid in read_answers():
                self.send(400, '{"error": "unknown or already answered"}')
                return
            entry = {"id": qid, "answer": answer,
                     "time": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            with ANSWERS.open("a") as f:
                f.write(json.dumps(entry) + "\n")
        message = {"submission": {"id": qid, "answer": answer}}
        if random.random() < SWITCH_PROBABILITY:
            message["switch_subject"] = True
        inbox.put(json.dumps(message))
        self.send(200, '{"ok": true}')

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    # Bind before wiping live/ so a failed start doesn't destroy a running session.
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    LIVE.mkdir(exist_ok=True)
    WORKSHEET.write_text(json.dumps({"questions": []}, indent=2))
    ANSWERS.write_text("")
    explainers.start()
    cards.start()
    inbox.put(START_MESSAGE + "\n\n" + cards.catalog_text())
    tutor = subprocess.Popen(TUTOR_CMD, cwd=ROOT, text=True,
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    threading.Thread(target=run_tutor, args=(tutor,), daemon=True).start()
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    log(f"Worksheet at http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        tutor.terminate()
