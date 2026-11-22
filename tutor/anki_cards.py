"""Anki card proposals: the tutor proposes, the student accepts, then cards are made.

Flow for one question (qid):
1. At session start, catalog_text() tells the tutor which Anki decks and note types
   exist. Every deck is eligible, including those synced from Collection/ by
   anki_sync.py. A deck whose notes all use the vocab note types gets the vocab
   maker (TTS audio); every other deck gets the notes maker, which adds notes of
   any existing note type or of a new one the tutor defines.
2. The tutor may put "card_proposal": {"deck", "label", "search"} on a graded
   question. It names what the cards would be about, not their contents.
3. The student clicks "Add to Anki" -> accept(): the server looks up existing
   notes matching `search` in that deck and sends the tutor a "card_accept"
   message. Nothing is generated or spent before this click.
4. The tutor writes live/cards/<qid>.json in the maker's spec format. A worker
   thread validates it, adds the "tutor" tag, and runs the maker (Vocab/make_cards.py:
   ElevenLabs TTS + AnkiConnect addNote; or tutor/make_notes.py). The result shows
   on the page through states().

Every note added this way is tagged "tutor". anki_sync.py ignores such notes, so
they can live in synced decks without being reported as drift or pruned by a push.
"""
import html
import json
import re
import subprocess
import sys
import threading
import time
import urllib.request
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TUTOR_TAG = "tutor"     # anki_sync.py skips notes with this tag; keep the two in sync
ANKI_URL = "http://localhost:8765"
QID = re.compile(r"^[A-Za-z0-9_-]+$")
SCAN_INTERVAL = 1.0
SETTLE = 1.0            # wait until a spec file hasn't changed for this long
MAX_ATTEMPTS = 2        # a spec that fails validation goes back to the tutor once
MAX_CARDS = 6           # notes per accepted proposal: caps the ElevenLabs credits one click can spend
RUN_TIMEOUT = 300       # seconds for one make_cards.py run
SAMPLES = 2             # example notes per deck and note type, so the tutor sees its direction and style
SAMPLE_CHARS = 100      # a sample field is cut to this length (some decks hold long data fields)
EXISTING_LIMIT = 20     # existing-note matches sent to the tutor on accept
MISSES = 10             # recent "Again" cards per deck, sent as starting points for a subject

# Card makers: the only ways cards get added. A deck whose notes all use the vocab
# note types gets "vocab", so its new notes get audio like the rest; every other deck
# (including empty ones) gets "notes".
MAKERS = {
    "vocab": {
        "script": REPO / "Vocab" / "make_cards.py",
        "guide": REPO / "Vocab" / "CLAUDE.md",
        "note_types": {"VocabCard", "BasicWithTTS"},
    },
    "notes": {
        "script": REPO / "tutor" / "make_notes.py",
        "guide": REPO / "tutor" / "CLAUDE.md",   # section "The notes maker"
    },
}


def maker_for(note_types):
    vocab = MAKERS["vocab"]["note_types"]
    return "vocab" if note_types and set(note_types) <= vocab else "notes"


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
    text = re.sub(r"</?(?:sub|sup|b|i|u|em|strong|span|font)\b[^>]*>", "", text)  # inline: no gap
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"\s+", " ", text).strip()


def clip(text):
    return text if len(text) <= SAMPLE_CHARS else text[:SAMPLE_CHARS] + "…"


def tts_languages():
    """Languages Vocab/tts.py has a voice for."""
    text = (REPO / "Vocab" / "tts.py").read_text()
    return set(re.findall(r'language\s*==\s*"([^"]+)"', text))


def build_catalog():
    """{"decks": [{name, note_types: {type: count}, maker, samples}],
        "note_types": {type: [fields]}} for the whole collection."""
    models = ac("modelNames")
    by_type = {m: set(ac("findNotes", query=f'"note:{quote(m)}"')) for m in models}
    decks = []
    for deck in sorted(ac("deckNames")):
        ids = set(ac("findNotes", query=f'"deck:{quote(deck)}" -"deck:{quote(deck)}::*"'))
        types = {m: len(ids & s) for m, s in by_type.items() if ids & s}
        maker = maker_for(types)
        samples = []
        # A few notes of each type in the deck (the tutor's own left out), to show its style.
        for m in types:
            own = sorted(ids & by_type[m])[:SAMPLES * 3]
            infos = [i for i in ac("notesInfo", notes=own) if TUTOR_TAG not in i["tags"]][:SAMPLES]
            for info in infos:
                samples.append({"type": m,
                                "fields": {k: clip(plain(v["value"])) for k, v in info["fields"].items()
                                           if plain(v["value"])}})
        decks.append({"name": deck, "note_types": types, "maker": maker, "samples": samples})
    return {"decks": decks,
            "note_types": {m: ac("modelFieldNames", modelName=m) for m in sorted(models)}}


def catalog_text(catalog):
    """The deck list for the tutor's start message."""
    if catalog is None:
        return ("Anki isn't reachable (AnkiConnect at localhost:8765), so don't propose Anki "
                "cards this session.")
    lines = ["Anki decks (see 'Anki card proposals' in CLAUDE.md). Any deck may get cards; "
             "each names the maker that adds them."]
    for d in catalog["decks"]:
        types = ", ".join(f"{t} ({n})" for t, n in d["note_types"].items()) or "empty"
        lines.append(f"- {d['name']}: {types}. Maker '{d['maker']}' "
                     f"(guide: {MAKERS[d['maker']]['guide']}).")
        for s in d["samples"]:
            lines.append(f"    example {s['type']}: {json.dumps(s['fields'], ensure_ascii=False)}")
    lines.append("Note types and their fields (for the notes maker):")
    for m, fields in catalog["note_types"].items():
        lines.append(f"- {m}: {', '.join(fields)}")
    return "\n".join(lines)


def recent_misses(deck, n=MISSES):
    """The last n distinct cards answered "Again" in `deck` itself, newest first."""
    # cardReviews rows: (reviewTime ms, cardID, usn, buttonPressed, newInterval,
    # previousInterval, newFactor, reviewDuration, reviewType). It covers only cards
    # whose deck is exactly `deck`, matching how decks are listed in the catalog.
    reviews = ac("cardReviews", deck=deck, startID=0)
    latest = {}
    for r in sorted(reviews, key=lambda r: r[0], reverse=True):
        if r[3] == 1 and r[1] not in latest:
            latest[r[1]] = r[0]
            if len(latest) == n:
                break
    if not latest:
        return []
    infos = {i["cardId"]: i for i in ac("cardsInfo", cards=list(latest))}
    out = []
    for cid, ms in latest.items():
        info = infos.get(cid)
        if not info or not info.get("fields"):
            continue  # card deleted since
        fields = sorted(info["fields"].items(), key=lambda kv: kv[1]["order"])
        out.append({"deck": deck,
                    "missed": datetime.fromtimestamp(ms / 1000).strftime("%Y-%m-%d"),
                    "fields": {k: clip(plain(v["value"])) for k, v in fields if plain(v["value"])}})
    return out


class Cards:
    def __init__(self, live_dir, notify):
        self.dir = Path(live_dir) / "cards"
        self.notify = notify
        self.lock = threading.Lock()
        self.state = {}         # qid -> {"state", "deck", "label", "summary", "mtime", "attempts"}
        self.catalog = None     # None: Anki unreachable at startup
        self.languages = set()
        self.miss_cache = {}    # deck -> recent_misses(deck)

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

    def misses(self, decks):
        """The last MISSES cards answered "Again" in each of `decks` (subdecks not
        included), newest first, as [{deck, missed, fields}]. Cached for the session."""
        try:
            known = set(ac("deckNames"))    # fresh, so decks made mid-session count
        except (OSError, RuntimeError, ValueError) as e:
            print(f"cards: deck list unavailable ({e})", flush=True)
            return []
        out = []
        for deck in decks:
            if deck not in known:
                continue
            if deck not in self.miss_cache:
                try:
                    self.miss_cache[deck] = recent_misses(deck)
                except (OSError, RuntimeError, ValueError) as e:
                    print(f"cards: misses for {deck} unavailable ({e})", flush=True)
                    self.miss_cache[deck] = []
            out += self.miss_cache[deck]
        return out

    def eligible(self, deck):
        """The maker for `deck`, or None if there is no such deck. Asks Anki fresh
        each time, so decks made mid-session are found."""
        try:
            if deck not in ac("deckNames"):
                return None
            own = f'"deck:{quote(deck)}" -"deck:{quote(deck)}::*"'
            types = [m for m in ac("modelNames")
                     if ac("findNotes", query=f'{own} "note:{quote(m)}"')]
        except (OSError, RuntimeError, ValueError) as e:
            print(f"cards: couldn't look up deck {deck!r} ({e})", flush=True)
            return None
        return maker_for(types)

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
        """Notes in `deck` matching `search`: for vocab decks, in the first field (one
        query per note type); otherwise anywhere in the note."""
        ids = set()
        if maker == "vocab":
            for note_type in MAKERS[maker]["note_types"]:
                first = ac("modelFieldNames", modelName=note_type)[0]
                ids |= set(ac("findNotes", query=f'"deck:{quote(deck)}" "note:{quote(note_type)}" '
                                                 f'"{quote(first)}:*{quote(search)}*"'))
        else:
            ids = set(ac("findNotes", query=f'"deck:{quote(deck)}" "{quote(search)}"'))
        found = []
        for info in ac("notesInfo", notes=sorted(ids)[:EXISTING_LIMIT]):
            values = [plain(v["value"]) for v in info["fields"].values()]
            found.append(clip(" | ".join(v for v in values if v)))
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
        if s["maker"] == "vocab":
            return self._validate_vocab(spec)
        return self._validate_notes(spec)

    def _validate_vocab(self, spec):
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

    def _validate_notes(self, spec):
        existing = ac("modelNames")
        name, new = spec.get("note_type"), spec.get("new_note_type")
        if (name is None) == (new is None):
            return 'give exactly one of "note_type" (an existing one) or "new_note_type"'
        if name is not None:
            if name not in existing:
                return f'note type {name!r} doesn\'t exist; use one listed, or "new_note_type"'
            fields = ac("modelFieldNames", modelName=name)
        else:
            if not isinstance(new, dict):
                return '"new_note_type" must be an object'
            if new.get("name") in existing:
                return f'note type {new.get("name")!r} already exists: use "note_type" instead'
            if not isinstance(new.get("name"), str) or not new["name"].strip():
                return '"new_note_type.name" must be a non-empty string'
            fields = new.get("fields")
            if (not isinstance(fields, list) or not fields
                    or not all(isinstance(f, str) and f.strip() for f in fields)
                    or len(set(fields)) != len(fields)):
                return '"new_note_type.fields" must be a list of distinct field names'
            templates = new.get("templates")
            if (not isinstance(templates, list) or not templates
                    or not all(isinstance(t, dict) and all(isinstance(t.get(k), str) and t[k].strip()
                                                           for k in ("name", "front", "back"))
                               for t in templates)):
                return '"new_note_type.templates" must be a list of {"name", "front", "back"}'
            if new.get("cloze") and len(templates) != 1:
                return "a cloze note type has exactly one template"
            if not isinstance(new.get("css", ""), str):
                return '"new_note_type.css" must be a string'
        notes = spec.get("notes")
        if not isinstance(notes, list) or not 1 <= len(notes) <= MAX_CARDS:
            return f'"notes" must be a list of 1 to {MAX_CARDS} notes'
        for note in notes:
            if not isinstance(note, dict) or not all(isinstance(v, str) for v in note.values()):
                return 'each note must be an object of field name -> string'
            unknown = set(note) - set(fields)
            if unknown:
                return f'unknown fields {sorted(unknown)}; the fields are {fields}'
            if not note.get(fields[0], "").strip():
                return f'every note needs its first field, {fields[0]!r}'
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
        except RuntimeError as e:   # AnkiConnect, while checking note types
            error = f"couldn't check the spec against Anki: {e}"
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
        # The maker runs a copy of the spec tagged "tutor" (and nothing else), so every note
        # the tutor adds is one anki_sync.py knows to ignore.
        spec["tags"] = [TUTOR_TAG]
        run = self.dir / f"{qid}.run"
        run.write_text(json.dumps(spec, ensure_ascii=False, indent=2))
        try:
            result = subprocess.run([sys.executable, str(script), str(run)], cwd=REPO,
                                    capture_output=True, text=True, timeout=RUN_TIMEOUT)
            out = result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            result, out = None, f"timed out after {RUN_TIMEOUT}s"
        (self.dir / f"{qid}.log").write_text(out)
        added = [m.group(2) for m in re.finditer(r"^([VSN]) (.+) -> \d+$", out, re.M)]
        skipped = [m.group(2) for m in re.finditer(r"^([VSN]) (.+) -> SKIPPED", out, re.M)]
        failed = [m.group(2) for m in re.finditer(r"^([VSN]) (.+) -> FAILED", out, re.M)]
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
