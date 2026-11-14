"""Anki card proposals: the tutor proposes, the student accepts, then cards are made.

Flow for one question (qid):
1. At session start, catalog_text() tells the tutor which Anki decks exist. Decks
   this repo manages (Collection/, synced by anki_sync.py) have a [bracketed]
   top-level name in Anki ("[Humanities]::Geography") and are off limits. Each other deck lists the note
   types its notes use, and the card maker that can add notes of exactly those
   types, if any. A deck is eligible only if one maker covers all its note types,
   so a deck never gets a note type it doesn't already use.
2. The tutor may put "card_proposal": {"deck", "label", "search"} on a graded
   question. It names what the cards would be about, not their contents.
3. The student clicks "Add to Anki" -> accept(): the server looks up existing
   notes matching `search` in that deck and sends the tutor a "card_accept"
   message. Nothing is generated or spent before this click.
4. The tutor writes live/cards/<qid>.json in the maker's spec format. A worker
   thread validates it and runs the maker (for the language decks,
   Vocab/make_cards.py: ElevenLabs TTS + AnkiConnect addNote). The result shows
   on the page through states().
"""
import json
import re
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
COLLECTION = REPO / "Collection"
ANKI_URL = "http://localhost:8765"
QID = re.compile(r"^[A-Za-z0-9_-]+$")
SCAN_INTERVAL = 1.0
SETTLE = 1.0            # wait until a spec file hasn't changed for this long
MAX_ATTEMPTS = 2        # a spec that fails validation goes back to the tutor once
MAX_CARDS = 6           # per accepted proposal: caps the ElevenLabs credits one click can spend
RUN_TIMEOUT = 300       # seconds for one make_cards.py run
SAMPLES = 2             # example notes per eligible deck, so the tutor sees its direction and style
EXISTING_LIMIT = 20     # existing-note matches sent to the tutor on accept

# Card makers: the only ways cards get added. A deck is eligible for a maker if
# every note in it uses one of the maker's note types.
MAKERS = {
    "vocab": {
        "script": REPO / "Vocab" / "make_cards.py",
        "guide": REPO / "Vocab" / "CLAUDE.md",
        "note_types": {"VocabCard", "BasicWithTTS"},
    },
}


def ac(action, **params):
    req = json.dumps({"action": action, "version": 6, "params": params}).encode()
    r = json.load(urllib.request.urlopen(ANKI_URL, req, timeout=30))
    if r["error"]:
        raise RuntimeError(f"{action}: {r['error']}")
    return r["result"]


def quote(text):
    """Escape a value for an Anki search term (inside double quotes)."""
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("*", "\\*").replace("_", "\\_")


def plain(field):
    """A field's text without [sound:] tags or HTML, for showing the tutor."""
    text = re.sub(r"\[sound:[^\]]*\]", "", field)
    text = re.sub(r"<[^>]+>", " ", text).replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


def managed_decks():
    """Deck names anki_sync.py manages: each Collection/ folder with a manifest, named
    like anki_sync.deck_name_for() does ("[Humanities]::Geography")."""
    names = set()
    for p in COLLECTION.rglob("manifest.json"):
        top, *rest = p.parent.relative_to(COLLECTION).parts
        names.add("::".join([f"[{top}]", *rest]))
    return names


def is_managed(deck, managed):
    """Managed decks have a [bracketed] top-level name; this also covers their parent
    decks ("[Humanities]") and any deck synced from Collection/."""
    top = deck.split("::")[0]
    return (top.startswith("[") and top.endswith("]")) or deck in managed


def tts_languages():
    """Languages Vocab/tts.py has a voice for."""
    text = (REPO / "Vocab" / "tts.py").read_text()
    return set(re.findall(r'language\s*==\s*"([^"]+)"', text))


def build_catalog():
    """[{name, managed, note_types: {type: count}, maker, samples}] for every deck."""
    managed = managed_decks()
    by_type = {m: set(ac("findNotes", query=f'"note:{quote(m)}"')) for m in ac("modelNames")}
    catalog = []
    for deck in sorted(ac("deckNames")):
        ids = set(ac("findNotes", query=f'"deck:{quote(deck)}" -"deck:{quote(deck)}::*"'))
        types = {m: len(ids & s) for m, s in by_type.items() if ids & s}
        managed_deck = is_managed(deck, managed)
        maker = None
        if not managed_deck and types:
            maker = next((name for name, mk in MAKERS.items() if set(types) <= mk["note_types"]), None)
        samples = []
        if maker:
            for info in ac("notesInfo", notes=sorted(ids)[:SAMPLES]):
                samples.append({"type": info["modelName"],
                                "fields": {k: plain(v["value"]) for k, v in info["fields"].items()
                                           if plain(v["value"])}})
        catalog.append({"name": deck, "managed": managed_deck, "note_types": types,
                        "maker": maker, "samples": samples})
    return catalog


def catalog_text(catalog):
    """The deck list for the tutor's start message."""
    if catalog is None:
        return ("Anki isn't reachable (AnkiConnect at localhost:8765), so don't propose Anki "
                "cards this session.")
    lines = ["Anki decks (see 'Anki card proposals' in CLAUDE.md). Decks whose top-level "
             "name is in [brackets] are managed by another tool: never propose cards for them."]
    for d in catalog:
        if d["managed"]:
            lines.append(f"- {d['name']} (managed)")
            continue
        types = ", ".join(f"{t} ({n})" for t, n in d["note_types"].items()) or "empty"
        if d["maker"]:
            lines.append(f"- {d['name']}: {types}. Eligible: maker '{d['maker']}' "
                         f"(guide: {MAKERS[d['maker']]['guide']}).")
            for s in d["samples"]:
                lines.append(f"    example {s['type']}: {json.dumps(s['fields'], ensure_ascii=False)}")
        else:
            lines.append(f"- {d['name']}: {types}. Not eligible: no maker for these note types.")
    return "\n".join(lines)


class Cards:
    def __init__(self, live_dir, notify):
        self.dir = Path(live_dir) / "cards"
        self.notify = notify
        self.lock = threading.Lock()
        self.state = {}         # qid -> {"state", "deck", "label", "summary", "mtime", "attempts"}
        self.catalog = None     # None: Anki unreachable at startup
        self.languages = set()

    def start(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        for old in self.dir.iterdir():
            old.unlink()
        try:
            self.catalog = build_catalog()
            self.languages = tts_languages()
        except (OSError, RuntimeError, ValueError) as e:
            print(f"cards: Anki catalog unavailable ({e}); no card proposals this session", flush=True)
            self.catalog = None
        threading.Thread(target=self._run, daemon=True).start()
        return self

    def catalog_text(self):
        return catalog_text(self.catalog)

    def eligible(self, deck):
        """The maker for `deck`, or None if the tutor may not add cards to it."""
        for d in self.catalog or []:
            if d["name"] == deck and not d["managed"]:
                return d["maker"]
        return None

    def states(self):
        """{qid: {"state": "writing" | "adding" | "done" | "failed", "summary"}}."""
        with self.lock:
            return {qid: {"state": s["state"], "summary": s.get("summary", "")}
                    for qid, s in self.state.items()}

    def accept(self, qid, proposal):
        """The student clicked "Add to Anki". Returns an error string, or None."""
        if not QID.match(qid or ""):
            return "bad question id"
        if not isinstance(proposal, dict):
            return "that question has no card proposal"
        deck, search = proposal.get("deck"), str(proposal.get("search", "")).strip()
        maker = self.eligible(deck)
        if not maker:
            return f"no cards can be added to deck {deck!r}"
        with self.lock:
            if qid in self.state:
                return "already accepted"
            self.state[qid] = {"state": "writing", "deck": deck, "maker": maker,
                               "label": proposal.get("label", ""), "mtime": None, "attempts": 0}
        try:
            existing = self._existing(deck, maker, search) if search else []
        except (OSError, RuntimeError) as e:
            existing = [f"(couldn't search the deck: {e})"]
        self.notify(json.dumps({"card_accept": {
            "id": qid, "deck": deck, "label": proposal.get("label", ""),
            "spec_path": f"live/cards/{qid}.json", "existing": existing}}, ensure_ascii=False))
        print(f"cards {qid}: accepted ({deck}: {proposal.get('label', '')})", flush=True)
        return None

    def _existing(self, deck, maker, search):
        """Notes in `deck` whose first field contains `search`: one query per note type."""
        ids = set()
        for note_type in MAKERS[maker]["note_types"]:
            first = ac("modelFieldNames", modelName=note_type)[0]
            ids |= set(ac("findNotes", query=f'"deck:{quote(deck)}" "note:{quote(note_type)}" '
                                             f'"{quote(first)}:*{quote(search)}*"'))
        found = []
        for info in ac("notesInfo", notes=sorted(ids)[:EXISTING_LIMIT]):
            values = [plain(v["value"]) for v in info["fields"].values()]
            found.append(" | ".join(v for v in values if v))
        return found

    # ---------------------------------------------------------------- worker
    def _run(self):
        while True:
            for qid in self._ready_specs():
                self._make(qid)
            time.sleep(SCAN_INTERVAL)

    def _ready_specs(self):
        now = time.time()
        ready = []
        for spec in sorted(self.dir.glob("*.json")):
            qid, mtime = spec.stem, spec.stat().st_mtime
            if now - mtime < SETTLE:
                continue
            with self.lock:
                s = self.state.get(qid)
                # Only specs for accepted proposals run, once per version of the file.
                if not s or s["state"] != "writing" or s["mtime"] == mtime or s["attempts"] >= MAX_ATTEMPTS:
                    continue
                s["mtime"] = mtime
            ready.append(qid)
        return ready

    def _validate(self, spec, s):
        if not isinstance(spec, dict):
            return "the spec must be a JSON object"
        if spec.get("deck") != s["deck"]:
            return f'"deck" must be {s["deck"]!r}, the deck the student accepted'
        for key in ("front_lang", "back_lang"):
            if spec.get(key) not in self.languages:
                return f'"{key}" must be one of: {", ".join(sorted(self.languages))}'
        cards = spec.get("cards")
        if not isinstance(cards, list) or not 1 <= len(cards) <= MAX_CARDS:
            return f'"cards" must be a list of 1 to {MAX_CARDS} cards'
        for card in cards:
            if (not isinstance(card, list) or len(card) not in (3, 4) or card[0] not in ("V", "S")
                    or not all(isinstance(x, str) and x.strip() for x in card[1:3])
                    or (len(card) == 4 and not isinstance(card[3], str))):
                return f'bad card {json.dumps(card, ensure_ascii=False)}: use ["V"|"S", front, back] (+ optional pronunciation)'
        return None

    def _make(self, qid):
        path = self.dir / f"{qid}.json"
        with self.lock:
            s = self.state[qid]
            s["attempts"] += 1
        try:
            spec = json.loads(path.read_text())
            error = self._validate(spec, s)
        except (OSError, json.JSONDecodeError) as e:
            error = f"couldn't read the spec as JSON: {e}"
        if error:
            with self.lock:
                give_up = s["attempts"] >= MAX_ATTEMPTS
                if give_up:
                    s["state"], s["summary"] = "failed", "The tutor couldn't write valid cards."
            print(f"cards {qid}: invalid spec ({error})" + ("; dropped" if give_up else ""), flush=True)
            if not give_up:
                self.notify(json.dumps({"card_error": {"id": qid, "error": error}}, ensure_ascii=False))
            return

        with self.lock:
            s["state"] = "adding"
        script = MAKERS[s["maker"]]["script"]
        try:
            result = subprocess.run([sys.executable, str(script), str(path)], cwd=REPO,
                                    capture_output=True, text=True, timeout=RUN_TIMEOUT)
            out = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            result, out = None, f"timed out after {RUN_TIMEOUT}s"
        (self.dir / f"{qid}.log").write_text(out)
        added = [m.group(2) for m in re.finditer(r"^([VS]) (.+) -> \d+$", out, re.M)]
        skipped = [m.group(2) for m in re.finditer(r"^([VS]) (.+) -> SKIPPED", out, re.M)]
        failed = [m.group(2) for m in re.finditer(r"^([VS]) (.+) -> FAILED", out, re.M)]
        parts = []
        if added:
            parts.append(f"Added to {s['deck']}: " + ", ".join(added))
        if skipped:
            parts.append("Already in the deck: " + ", ".join(skipped))
        if failed:
            parts.append("Failed: " + ", ".join(failed))
        if not parts:
            last = out.strip().splitlines()[-1] if out.strip() else "no output"
            parts.append(f"Couldn't add the cards ({last})")
        with self.lock:
            s["state"] = "done" if added or skipped else "failed"
            s["summary"] = ". ".join(parts) + "."
        print(f"cards {qid}: {s['state']}: {s['summary']}", flush=True)
