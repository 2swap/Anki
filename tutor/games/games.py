"""Serves the tutor's minigames and relays what happens in them.

The tutor writes live/games/<question id>.html: an HTML fragment (style, markup, script).
The server wraps it in games/frame.html together with games/kit.js and serves it at
/games/<question id>.html with a strict Content-Security-Policy. The page shows it in an
<iframe sandbox="allow-scripts">: the game's code can run, but it has an opaque origin,
can't make requests, and can't touch the worksheet page.

Inside the frame, kit.js posts errors and completion to the page, which forwards them
here (event()). The first error in each version of a game goes to the tutor to fix; after
MAX_ATTEMPTS failing versions the game is dropped. The first completion goes to the tutor
as information.
"""
import json
import re
import shutil
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
FRAME = HERE / "frame.html"
KIT = HERE / "kit.js"
QID = re.compile(r"^[A-Za-z0-9_-]+$")
SETTLE = 1.0                # seconds a game file must be unchanged before it's shown
MAX_BYTES = 200_000
MAX_ATTEMPTS = 2            # failing versions before a game is dropped
CSP = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
       "img-src data:; base-uri 'none'; form-action 'none'")


class Games:
    def __init__(self, live_dir, notify):
        self.dir = Path(live_dir) / "games"
        self.notify = notify
        self.lock = threading.Lock()
        self.failed = {}    # qid -> set of versions that reported an error
        self.solved = set()

    def start(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        self.dir.mkdir(parents=True)
        return self

    def _version(self, qid):
        """The current version (mtime in ns) of a game that's ready to show, or None."""
        path = self.dir / f"{qid}.html"
        try:
            stat = path.stat()
        except OSError:
            return None
        if time.time() - stat.st_mtime < SETTLE or stat.st_size > MAX_BYTES:
            return None
        with self.lock:
            failed = self.failed.get(qid, set())
            if len(failed) >= MAX_ATTEMPTS:
                return None
        return str(stat.st_mtime_ns)

    def states(self):
        """{qid: version} for every game ready to show, or "dropped" after it failed."""
        out = {}
        with self.lock:
            dropped = {qid for qid, f in self.failed.items() if len(f) >= MAX_ATTEMPTS}
        for path in self.dir.glob("*.html"):
            if not QID.match(path.stem):
                continue
            if path.stem in dropped:
                out[path.stem] = "dropped"
            elif v := self._version(path.stem):
                out[path.stem] = v
        return out

    @staticmethod
    def _frame_parts():
        """The frame split around the game, with the kit filled in."""
        before, after = FRAME.read_text().replace("<!--KIT-->", KIT.read_text()).split("<!--GAME-->")
        return before, after

    def page(self, qid):
        """The full HTML document for a game, or None."""
        if not QID.match(qid) or not self._version(qid):
            return None
        game = (self.dir / f"{qid}.html").read_text(errors="replace")
        before, after = self._frame_parts()
        return before + game + after

    def event(self, qid, version, kind, detail):
        """An event posted from a game frame. Returns an error string or None."""
        if not isinstance(qid, str) or not QID.match(qid):
            return "bad id"
        detail = str(detail)[:500]
        # Report line numbers in the tutor's file, not in the wrapped page.
        offset = self._frame_parts()[0].count("\n")
        detail = re.sub(r"\(line (\d+)\)", lambda m: f"(line {int(m[1]) - offset} of your file)"
                        if int(m[1]) > offset else "(in the frame)", detail)
        if kind == "error":
            with self.lock:
                if version != self._version_unlocked(qid):
                    return None    # an old version, already replaced
                failed = self.failed.setdefault(qid, set())
                if version in failed:
                    return None
                failed.add(version)
                last = len(failed) >= MAX_ATTEMPTS
            if not last:
                self.notify(json.dumps({"game_error": {"id": qid, "error": detail}}))
            return None
        if kind == "solved":
            with self.lock:
                if qid in self.solved:
                    return None
                self.solved.add(qid)
            self.notify(json.dumps({"game_solved": {"id": qid, "detail": detail}}))
            return None
        return "unknown event"

    def _version_unlocked(self, qid):
        try:
            return str((self.dir / f"{qid}.html").stat().st_mtime_ns)
        except OSError:
            return None
