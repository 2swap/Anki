"""Renders the tutor's Manim explainer scenes in the background.

The tutor writes live/explainers/<question id>.py with one `class Explainer(Scene)`.
A worker thread notices new or changed scene files, renders each one in a
sandbox (bwrap: no network, read-only filesystem except its own output
directory), and leaves live/explainers/<question id>.mp4 next to it.

The server only needs: Explainers(live_dir, notify).start(), .states() for
/state, and .video(qid) for serving the file. notify(text) sends a message to
the tutor; it's used to report render errors so the tutor can fix the scene.
"""
import json
import re
import shutil
import subprocess
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
MANIM = HERE / ".venv" / "bin" / "manim"
QUALITY = "-ql"             # 480p15: fast, and enough for diagrams
TIMEOUT = 120               # seconds per render
MEMORY_LIMIT = 4 * 1024**3  # bytes of address space
MAX_ATTEMPTS = 2            # first failure goes back to the tutor; second drops the explainer
LOG_LINES = 30
SCAN_INTERVAL = 1.0
SETTLE = 1.0                # wait until a scene file hasn't changed for this long
QID = re.compile(r"^[A-Za-z0-9_-]+$")


class Explainers:
    def __init__(self, live_dir, notify):
        self.dir = Path(live_dir) / "explainers"
        self.work = self.dir / ".work"
        self.notify = notify
        self.lock = threading.Lock()
        self.state = {}     # qid -> {"state", "mtime", "attempts"}

    def start(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        self.work.mkdir(parents=True)
        threading.Thread(target=self._run, daemon=True).start()
        return self

    def states(self):
        """{qid: "rendering" | "ok" | "error"} for every scene the tutor has written."""
        with self.lock:
            return {qid: s["state"] for qid, s in self.state.items()}

    def video(self, qid):
        with self.lock:
            ok = self.state.get(qid, {}).get("state") == "ok"
        return self.dir / f"{qid}.mp4" if ok and QID.match(qid) else None

    def _run(self):
        while True:
            for scene in self._ready_scenes():
                self._render(scene)
            time.sleep(SCAN_INTERVAL)

    def _ready_scenes(self):
        now = time.time()
        ready = []
        for scene in sorted(self.dir.glob("*.py")):
            qid, mtime = scene.stem, scene.stat().st_mtime
            if not QID.match(qid) or now - mtime < SETTLE:
                continue
            with self.lock:
                s = self.state.get(qid)
                if s and s["mtime"] == mtime:
                    continue
                attempts = s["attempts"] if s else 0
                if attempts >= MAX_ATTEMPTS:
                    continue
                self.state[qid] = {"state": "rendering", "mtime": mtime, "attempts": attempts}
            ready.append(scene)
        return ready

    def _render(self, scene):
        qid = scene.stem
        job = self.work / qid
        shutil.rmtree(job, ignore_errors=True)
        (job / "media").mkdir(parents=True)
        shutil.copy(scene, job / "scene.py")
        ok, log = self._manim(job)
        with self.lock:
            s = self.state[qid]
            s["attempts"] += 1
            if ok:
                out = next((job / "media" / "videos").rglob("explainer.mp4"))
                shutil.move(out, self.dir / f"{qid}.mp4")
                s["state"] = "ok"
            else:
                s["state"] = "error"
            attempts = s["attempts"]
        shutil.rmtree(job, ignore_errors=True)
        if ok:
            print(f"explainer {qid}: rendered", flush=True)
        elif attempts < MAX_ATTEMPTS:
            print(f"explainer {qid}: failed, sent log to tutor", flush=True)
            self.notify(json.dumps({"render_error": {"id": qid, "log": log}}))
        else:
            print(f"explainer {qid}: failed again, dropped", flush=True)

    def _manim(self, job):
        if not MANIM.exists():
            return False, f"Manim isn't installed at {MANIM}; don't write explainers this session."
        cmd = [
            "bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp",
            "--bind", str(job), str(job), "--chdir", str(job),
            "--unshare-all", "--die-with-parent", "--new-session",
            "--setenv", "PYTHONDONTWRITEBYTECODE", "1", "--setenv", "COLUMNS", "100",
            "prlimit", f"--as={MEMORY_LIMIT}", "--",
            str(MANIM), "render", QUALITY, "--progress_bar", "none", "--disable_caching",
            "--media_dir", str(job / "media"), "-o", "explainer.mp4",
            str(job / "scene.py"), "Explainer",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            return False, f"Render timed out after {TIMEOUT}s; make the scene shorter or simpler."
        log = "\n".join((result.stdout + result.stderr).splitlines()[-LOG_LINES:])
        ok = result.returncode == 0 and any((job / "media").rglob("explainer.mp4"))
        return ok, log
