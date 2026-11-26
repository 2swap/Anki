#!/usr/bin/env python3
"""Worksheet server plus one persistent Claude tutor session.

The tutor writes live/worksheet.json; the student's submissions are appended
to live/answers.jsonl and follow-up questions on feedback to live/asks.jsonl,
and both are forwarded to the tutor. All three files are wiped on startup —
sessions are not kept. Student notes in notes/ persist.
"""
import json
import os
import queue
import random
import re
import signal
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from anki_cards import Cards, ac
from games.games import CSP as GAME_CSP, Games

ROOT = Path(__file__).resolve().parent
LIVE = ROOT / "live"
WORKSHEET = LIVE / "worksheet.json"
ANSWERS = LIVE / "answers.jsonl"
ASKS = LIVE / "asks.jsonl"         # the student's follow-up questions on feedback
NOTES = ROOT / "notes"
COUNTS = NOTES / "question_counts.json"  # questions answered per subject, across sessions
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
    "Read those three subjects' notes, then write 3 questions to live/worksheet.json, "
    "one per thread: thread 1 on {}, thread 2 on {}, thread 3 on {} (the least-asked subjects). "
    "From now on, each message I send is one or more student submissions.\n\n"
    "All subjects (notes/<subject>/notes.md): {}."
)

SWITCH_EVERY = 10          # a thread switches subject after this many questions in a row on one
MAX_SUGGESTION = 2000      # characters
MAX_ASK = 1000             # characters
# Question kinds: the share of application blocks among the last KIND_WINDOW questions is
# kept within APPLICATION_RANGE by requiring the next question's kind when it drifts out.
KIND_WINDOW = 12
KIND_MIN_SAMPLE = 4        # don't steer on fewer questions than this
APPLICATION_RANGE = (0.25, 0.50)

submit_lock = threading.Lock()
required_kinds = {}     # question id -> kind required of the question that follows it
inbox = queue.Queue()   # messages for the tutor
cards = Cards(LIVE, inbox.put)
games = Games(LIVE, inbox.put)


def read_answers():
    answers = {}
    if ANSWERS.exists():
        for line in ANSWERS.read_text().splitlines():
            if line.strip():
                entry = json.loads(line)
                answers[entry["id"]] = entry
    return answers


def read_asks():
    """Follow-up questions in the order asked: [{id, question_id, text, time}]."""
    if not ASKS.exists():
        return []
    return [json.loads(line) for line in ASKS.read_text().splitlines() if line.strip()]


def lan_address():
    """This machine's address on the local network, or None if there isn't one.

    Connecting a UDP socket sends nothing; it only picks the outgoing interface."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return None


def subjects():
    """Every folder in notes/ with a notes.md (notes/dont_use/ has none at its top)."""
    return sorted(p.parent.name for p in NOTES.glob("*/notes.md"))


def read_counts():
    """Questions answered per subject; a subject not in the file counts as 0."""
    try:
        return json.loads(COUNTS.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def write_counts(counts):
    tmp = COUNTS.with_suffix(".tmp")
    tmp.write_text(json.dumps(dict(sorted(counts.items())), indent=2) + "\n")
    os.replace(tmp, COUNTS)


def least_asked(exclude=(), n=1):
    """The n least-asked subjects not in exclude, ties broken at random."""
    counts = read_counts()
    pool = [s for s in subjects() if s not in exclude]
    random.shuffle(pool)
    return sorted(pool, key=lambda s: counts.get(s, 0))[:n]


def subject_decks(subject):
    """The decks named in backticks on the subject's **Anki deck:** line."""
    try:
        text = (NOTES / subject / "notes.md").read_text()
    except OSError:
        return []
    line = re.search(r"^\*\*Anki deck:\*\*(.*)$", text, re.M)
    return re.findall(r"`([^`]+)`", line[1]) if line else []


def anki_misses(subject):
    """Recent Anki misses for the subject, as one line for the tutor ("" if none)."""
    misses = cards.misses(subject_decks(subject))
    if not misses:
        return ""
    return f"Anki misses for {subject}: " + json.dumps(misses, ensure_ascii=False)


def thread_topics(questions):
    """The current subject of each thread: the topic of its latest question."""
    return {q.get("thread"): q.get("topic") for q in questions}


def subject_streak(questions, q):
    """How many questions in a row q's thread has had on q's topic, up to and including q."""
    streak = 0
    for other in reversed(questions[:questions.index(q) + 1]):
        if other.get("thread") != q.get("thread"):
            continue
        if other.get("topic") != q.get("topic"):
            break
        streak += 1
    return streak


def question_kind(q):
    return "application" if isinstance(q.get("items"), list) else "understanding"


def required_kind(questions):
    """The kind the next question must be, or None while the mix is in range.

    Counts the last KIND_WINDOW questions on the worksheet, plus questions already
    required but not written yet (a thread whose latest question has a requirement
    recorded), so several submissions arriving together don't all overshoot."""
    kinds = [question_kind(q) for q in questions]
    latest = {q.get("thread"): q.get("id") for q in questions}
    kinds += [required_kinds[qid] for qid in latest.values() if qid in required_kinds]
    kinds = kinds[-KIND_WINDOW:]
    if len(kinds) < KIND_MIN_SAMPLE:
        return None
    share = kinds.count("application") / len(kinds)
    low, high = APPLICATION_RANGE
    return "application" if share < low else "understanding" if share > high else None


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
    def send(self, code, body, content_type="application/json", headers=()):
        data = body.encode() if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        for name, value in headers:
            self.send_header(name, value)
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
                                       "asks": read_asks(),
                                       "cards": cards.states(), "games": games.states()}))
        elif self.path.startswith("/games/") and self.path.endswith(".html"):
            page = games.page(self.path[len("/games/"):-len(".html")])
            if page:
                self.send(200, page, "text/html; charset=utf-8",
                          [("Content-Security-Policy", GAME_CSP), ("X-Content-Type-Options", "nosniff")])
            else:
                self.send(404, '{"error": "no such game"}')
        else:
            self.send(404, '{"error": "not found"}')

    def do_POST(self):
        if self.path not in ("/submit", "/suggest", "/ask", "/cards/accept", "/games/event"):
            self.send(404, '{"error": "not found"}')
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        except (TypeError, ValueError):
            self.send(400, '{"error": "bad request"}')
            return
        if self.path == "/suggest":
            self.suggest(body)
        elif self.path == "/ask":
            self.ask(body)
        elif self.path == "/cards/accept":
            self.accept_cards(body)
        elif self.path == "/games/event":
            error = games.event(body.get("id"), body.get("version"), body.get("type"), body.get("detail", ""))
            if error:
                self.send(400, json.dumps({"error": error}))
            else:
                self.send(200, '{"ok": true}')
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

    def ask(self, body):
        """A follow-up question about a graded question's feedback. One may be open
        (unanswered) per question at a time."""
        qid, text = body.get("id"), str(body.get("text", "")).strip()
        if not text or len(text) > MAX_ASK:
            self.send(400, '{"error": "empty or too long"}')
            return
        try:
            questions = json.loads(WORKSHEET.read_text()).get("questions", [])
        except (OSError, json.JSONDecodeError):
            self.send(503, '{"error": "worksheet not ready"}')
            return
        q = next((q for q in questions if q.get("id") == qid), None)
        if not q or not q.get("credit"):
            self.send(400, '{"error": "no graded question with that id"}')
            return
        with submit_lock:
            mine = [a for a in read_asks() if a["question_id"] == qid]
            if any(a["id"] not in (q.get("replies") or {}) for a in mine):
                self.send(400, '{"error": "the tutor is still answering your last question"}')
                return
            entry = {"id": f"{qid}-a{len(mine) + 1}", "question_id": qid, "text": text,
                     "time": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            with ASKS.open("a") as f:
                f.write(json.dumps(entry) + "\n")
        log(f"ask {entry['id']}: {text}")
        inbox.put(json.dumps({"ask": {k: entry[k] for k in ("id", "question_id", "text")}}))
        self.send(200, '{"ok": true}')

    def submit(self, body):
        qid, answer = body.get("id"), body.get("answer", "")
        try:
            questions = json.loads(WORKSHEET.read_text()).get("questions", [])
        except (OSError, json.JSONDecodeError):
            questions = []
        q = next((q for q in questions if q.get("id") == qid), {})
        # An application question has one answer per item; any other question has one string.
        items = q.get("items")
        if isinstance(items, list):
            ok = (isinstance(answer, list) and len(answer) == len(items)
                  and all(isinstance(a, str) for a in answer))
        else:
            ok = isinstance(answer, str)
        if not ok:
            self.send(400, '{"error": "answer doesn\'t match the question"}')
            return
        with submit_lock:
            if not qid or qid in read_answers():
                self.send(400, '{"error": "unknown or already answered"}')
                return
            entry = {"id": qid, "answer": answer,
                     "time": datetime.now(timezone.utc).isoformat(timespec="seconds")}
            with ANSWERS.open("a") as f:
                f.write(json.dumps(entry) + "\n")
            if q.get("topic"):
                counts = read_counts()
                counts[q["topic"]] = counts.get(q["topic"], 0) + 1
                write_counts(counts)
            kind = required_kind(questions)
            if kind:
                required_kinds[qid] = kind
        message = {"submission": {"id": qid, "answer": answer}}
        if kind:
            message["next_kind"] = kind
        if q and subject_streak(questions, q) >= SWITCH_EVERY:
            # Load balancing: the thread moves to the least-asked subject that no
            # thread is on now.
            busy = set(thread_topics(questions).values())
            message["switch_subject"] = True
            message["switch_to"] = least_asked(exclude=busy)[0]
        text = json.dumps(message)
        if message.get("switch_to"):
            text = "\n".join(filter(None, [text, anki_misses(message["switch_to"])]))
        inbox.put(text)
        self.send(200, '{"ok": true}')

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    # The tutor depends on Anki (decks, misses, card proposals): refuse to start without it.
    try:
        ac("version")
    except (OSError, RuntimeError, ValueError) as e:
        sys.exit(f"Anki isn't reachable (AnkiConnect at localhost:8765: {e}). "
                 "Open Anki and try again.")
    # Bind before wiping live/ so a failed start doesn't destroy a running session.
    # All interfaces, so a phone on the same network can open the page too.
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    LIVE.mkdir(exist_ok=True)
    WORKSHEET.write_text(json.dumps({"questions": []}, indent=2))
    ANSWERS.write_text("")
    ASKS.write_text("")
    games.start()
    cards.start()
    if cards.catalog is None:
        sys.exit("Couldn't read the Anki deck catalog; not starting the tutor.")
    first = least_asked(n=3)
    misses = "\n".join(filter(None, map(anki_misses, first)))
    inbox.put("\n\n".join(filter(None, [START_MESSAGE.format(*first, ", ".join(subjects())), cards.catalog_text(), misses])))
    tutor = subprocess.Popen(TUTOR_CMD, cwd=ROOT, text=True,
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    threading.Thread(target=run_tutor, args=(tutor,), daemon=True).start()
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    log(f"Worksheet at http://localhost:{PORT}")
    if lan := lan_address():
        log(f"On a phone on the same network: http://{lan}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        tutor.terminate()
