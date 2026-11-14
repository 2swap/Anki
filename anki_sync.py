"""Compare an Anki collection against a repo folder, and push the repo downstream.

The repo is the source of truth; Anki (via AnkiConnect) is downstream.

Every deck folder lives under Collection/, and its path there IS the Anki deck
name, with '/' for '::' and the top-level part in [brackets] (which marks the
deck as managed by this repo): Collection/Natural Sciences/Night Sky/ mirrors the
deck "[Natural Sciences]::Night Sky". A folder whose deck has subdecks holds them as
subfolders, each with its own manifest.

Folder layout (see Collection/Natural Sciences/Night Sky/ and .../Periodic Table/
for worked examples):

    <folder>/
        manifest.json
        Card Types/
            <modelKey>/                     one dir per Anki note type
                fields.txt                  field names, one per line, in order
                style.css                   note-type styling
                front.html  back.html       -- single-template note type, OR
                <templateDir>/              -- one dir per card template
                    front.html  back.html   (dirs sorted by name = card order;
                                             the dir name is the Anki template name)
        <modelKey>.tsv                      the deck's notes of that note type;
                                            header row = field names + "Tags"
        media/
            <file>                          e.g. media/sky.js

manifest.json:

    {
      "models": {
        "<modelKey>": {
          "modelName":    "<Anki note type name>",
          "keyField":     "<field used to match a repo row to an Anki note>",
                          (or a list of fields, when no single one is unique)
          "templateName": "<single-template note types only; default = modelKey>"
        }
      },
      "media": { "<filename in Anki>": "<path relative to folder>" }
    }

There is no "decks" section: the folder is one deck (named by its path), and
every note type in "models" belongs to it.

If manifest.json has a "build" key (a list of folder-relative Python scripts),
those are run first -- before check or push reads any TSV -- so a deck can be
derived from source data (e.g. Humanities/Geography/Data/) instead of hand-written.
Each script's job is to (re)write <modelKey>.tsv (and, if it
generates media, manifest.json's "media" map -- the manifest is re-read after
building); it must not touch AnkiConnect. Pass --no-build to skip them, or run them alone with `build`.

Usage:

    python anki_sync.py check <folder>              # report drift, exit 1 if any
                                                    # <folder> e.g. "Collection/Humanities/Poems"
    python anki_sync.py push  <folder> [--dry-run] [--no-prune]
    python anki_sync.py build <folder>              # run manifest "build" scripts only

    check/push also accept --no-build.

`push` is one-directional (repo -> Anki): it creates/updates note types,
decks, notes and media to match the folder, then runs a sync. With pruning on
(default) it also deletes Anki notes in the target decks whose keyField is
absent from the repo. Notes are matched by keyField value, so renaming a
keyField value reads as a delete + add.
"""

import base64
import csv
import difflib
import json
import os
import subprocess
import sys
import urllib.request

ANKICONNECT_URL = "http://localhost:8765"


def invoke(action, **params):
    request = json.dumps({"action": action, "version": 6, "params": params}).encode("utf-8")
    response = json.load(urllib.request.urlopen(urllib.request.Request(ANKICONNECT_URL, request)))
    if response.get("error") is not None:
        raise RuntimeError(f"AnkiConnect '{action}': {response['error']}")
    return response["result"]


# --- reading the repo folder -------------------------------------------------

COLLECTION_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Collection")


def deck_name_for(folder):
    """The Anki deck a folder mirrors: its path under Collection/, '/' -> '::', with
    the top-level part in [brackets] to mark the deck as managed by this repo
    (Collection/Humanities/Geography -> "[Humanities]::Geography")."""
    rel = os.path.relpath(os.path.abspath(folder), COLLECTION_DIR)
    if rel == "." or rel.startswith(".."):
        raise SystemExit(f"{folder}: not inside {COLLECTION_DIR}; the folder path names the deck")
    top, *rest = rel.split(os.sep)
    return "::".join([f"[{top}]", *rest])


def load_manifest(folder):
    """Read manifest.json and add the folder's one deck to it, as manifest["decks"].

    The directory is the source of truth for the deck: its path gives the name,
    and every note type in "models" belongs to it. A manifest has no "decks"
    section of its own.
    """
    with open(os.path.join(folder, "manifest.json")) as fh:
        manifest = json.load(fh)
    if "decks" in manifest:
        raise SystemExit(f"{folder}/manifest.json: has a \"decks\" section; remove it, the folder "
                         "is the deck (its path gives the name, its models are all in it)")
    name = deck_name_for(folder)
    manifest["decks"] = {name: {"ankiDeck": name, "models": list(manifest["models"])}}
    return manifest


def run_build(folder, manifest):
    """Run each manifest 'build' script (folder-relative) to regenerate TSVs."""
    for script in manifest.get("build", []):
        path = os.path.abspath(os.path.join(folder, script))
        if not os.path.exists(path):
            raise SystemExit(f"build script not found: {path}")
        print(f"build: {script}")
        subprocess.run([sys.executable, path], cwd=os.path.abspath(folder), check=True)


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def normalize(text):
    """Line-wise rstrip + trailing-newline strip, so trivial whitespace and a
    final newline never count as drift."""
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


def model_dir(folder, model_key):
    return os.path.join(folder, "Card Types", model_key)


def read_fields(folder, model_key):
    txt = read_text(os.path.join(model_dir(folder, model_key), "fields.txt"))
    return [line.strip() for line in txt.splitlines() if line.strip()]


def read_styling(folder, model_key):
    return read_text(os.path.join(model_dir(folder, model_key), "style.css"))


def read_templates(folder, model_key, spec):
    """Return an ordered list of (templateName, {'Front':..., 'Back':...})."""
    d = model_dir(folder, model_key)
    if os.path.exists(os.path.join(d, "front.html")):
        name = spec.get("templateName", model_key)
        return [(name, {
            "Front": read_text(os.path.join(d, "front.html")),
            "Back": read_text(os.path.join(d, "back.html")),
        })]
    out = []
    for entry in sorted(e for e in os.listdir(d) if os.path.isdir(os.path.join(d, e))):
        tdir = os.path.join(d, entry)
        out.append((entry, {
            "Front": read_text(os.path.join(tdir, "front.html")),
            "Back": read_text(os.path.join(tdir, "back.html")),
        }))
    if not out:
        raise SystemExit(f"{d}: no front.html and no template subdirectories")
    return out


def read_deck_tsv(folder, model_key, fields):
    path = os.path.join(folder, f"{model_key}.tsv")
    if not os.path.exists(path):
        return None
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh, delimiter="\t")
        header = next(reader)
        expected = fields + ["Tags"]
        if header != expected:
            raise SystemExit(
                f"{path}: header {header} does not match fields.txt + ['Tags'] {expected}"
            )
        for lineno, raw in enumerate(reader, start=2):
            if not raw or all(c == "" for c in raw):
                continue
            if len(raw) != len(expected):
                raise SystemExit(f"{path}:{lineno}: expected {len(expected)} columns, got {len(raw)}")
            values = dict(zip(fields, raw))
            tags = raw[-1].split()
            rows.append({"fields": values, "tags": tags})
    return rows


# --- reading Anki ----------------------------------------------------------

# Tags Anki itself adds from review activity (leech detection, Mark Note). They
# aren't part of the repo's content, so they're invisible to check/push: never
# reported as drift and never removed by a retag.
ANKI_MANAGED_TAGS = {"leech", "marked"}

# Notes with this tag exist only to reference template-loaded media in a field
# ("[sound:x.js]") so Anki's Check Media keeps those files and AnkiWeb syncs
# them. push suspends their cards so the sound tags never autoplay; check
# reports one that isn't suspended. See README.md.
MEDIA_SAVER_TAG = "media_saver"


def note_key(values, key_field):
    """A note's match key: one field's value, or for a list of fields their
    values joined (e.g. ["Board", "ToPlay"] when no single field is unique)."""
    if isinstance(key_field, list):
        return " | ".join(values.get(f, "") for f in key_field)
    return values.get(key_field, "")


def anki_notes_by_key(anki_deck, model_name, key_field):
    query = f'deck:"{anki_deck}" note:"{model_name}"'
    note_ids = invoke("findNotes", query=query)
    by_key = {}
    if not note_ids:
        return by_key
    for info in invoke("notesInfo", notes=note_ids):
        values = {name: fld["value"] for name, fld in info["fields"].items()}
        key = note_key(values, key_field)
        if key in by_key:
            raise SystemExit(
                f"Anki deck '{anki_deck}' has two '{model_name}' notes with {key_field}={key!r}; "
                "cannot match by key."
            )
        tags = sorted(t for t in info["tags"] if t.lower() not in ANKI_MANAGED_TAGS)
        by_key[key] = {"noteId": info["noteId"], "fields": values, "tags": tags, "cards": info["cards"]}
    return by_key


# --- diffing --------------------------------------------------------------

class Report:
    def __init__(self):
        self.sections = []
        self.in_sync = True

    def line(self, section, msg, drift=True):
        self.sections.append((section, msg))
        if drift:
            self.in_sync = False

    def has_lines(self, section):
        return any(s == section for s, _ in self.sections)

    def dump(self):
        current = None
        for section, msg in self.sections:
            if section != current:
                print(f"\n== {section} ==")
                current = section
            print(msg)
        print()
        print("IN SYNC" if self.in_sync else "DRIFT DETECTED")


def diff_block(label, repo_text, anki_text):
    d = difflib.unified_diff(
        normalize(anki_text).splitlines(),
        normalize(repo_text).splitlines(),
        fromfile=f"anki:{label}",
        tofile=f"repo:{label}",
        lineterm="",
    )
    return "\n".join(d)


def indent(text, prefix="    "):
    return "\n".join(prefix + line for line in text.splitlines())


def check_model(folder, model_key, spec, report):
    model = spec["modelName"]
    section = f"note type: {model}"
    if model not in invoke("modelNames"):
        report.line(section, f"  MISSING in Anki (repo has '{model_key}')")
        return

    repo_fields = read_fields(folder, model_key)
    anki_fields = invoke("modelFieldNames", modelName=model)
    if repo_fields != anki_fields:
        report.line(section, f"  fields differ:\n    repo: {repo_fields}\n    anki: {anki_fields}")

    repo_templates = read_templates(folder, model_key, spec)
    anki_templates = invoke("modelTemplates", modelName=model)
    repo_names = [n for n, _ in repo_templates]
    if set(repo_names) != set(anki_templates):
        report.line(
            section,
            f"  templates differ:\n    repo: {repo_names}\n    anki: {list(anki_templates)}",
        )
    for name, tmpl in repo_templates:
        if name not in anki_templates:
            continue
        for side in ("Front", "Back"):
            block = diff_block(f"{model_key}/{name}/{side}", tmpl[side], anki_templates[name][side])
            if block:
                report.line(section, f"  {name} / {side} differs:\n" + indent(block))

    repo_css = read_styling(folder, model_key)
    anki_css = invoke("modelStyling", modelName=model)["css"]
    block = diff_block(f"{model_key}/style.css", repo_css, anki_css)
    if block:
        report.line(section, "  styling differs:\n" + indent(block))

    if not report.has_lines(section):
        report.line(section, "  ok", drift=False)


def check_deck(folder, deck_key, deck_spec, manifest, report):
    section = f"deck: {deck_spec['ankiDeck']}"
    if deck_spec["ankiDeck"] not in invoke("deckNames"):
        report.line(section, "  MISSING in Anki")
        return

    any_drift = False
    for model_key in deck_spec["models"]:
        spec = manifest["models"][model_key]
        fields = read_fields(folder, model_key)
        repo_rows = read_deck_tsv(folder, model_key, fields)
        if repo_rows is None:
            report.line(section, f"  [{model_key}] no TSV in repo, skipping")
            continue
        key_field = spec["keyField"]
        repo_by_key = {}
        for row in repo_rows:
            k = note_key(row["fields"], key_field)
            if k in repo_by_key:
                raise SystemExit(f"{model_key}.tsv: duplicate {key_field}={k!r}")
            repo_by_key[k] = row
        anki_by_key = anki_notes_by_key(deck_spec["ankiDeck"], spec["modelName"], key_field)

        only_repo = sorted(set(repo_by_key) - set(anki_by_key))
        only_anki = sorted(set(anki_by_key) - set(repo_by_key))
        common = sorted(set(repo_by_key) & set(anki_by_key))

        for k in only_repo:
            any_drift = True
            report.line(section, f"  [{model_key}] + {k}  (in repo, not in Anki)")
        for k in only_anki:
            any_drift = True
            report.line(section, f"  [{model_key}] - {k}  (in Anki, not in repo)")
        for k in common:
            r, a = repo_by_key[k], anki_by_key[k]
            field_diffs = [
                f"      {f}: anki={a['fields'].get(f, '')!r} -> repo={r['fields'][f]!r}"
                for f in fields
                if normalize(a["fields"].get(f, "")) != normalize(r["fields"][f])
            ]
            if sorted(r["tags"]) != a["tags"]:
                field_diffs.append(f"      Tags: anki={a['tags']} -> repo={sorted(r['tags'])}")
            if MEDIA_SAVER_TAG in r["tags"] and not all(invoke("areSuspended", cards=a["cards"])):
                field_diffs.append(f"      {MEDIA_SAVER_TAG} note has unsuspended cards")
            if field_diffs:
                any_drift = True
                report.line(section, f"  [{model_key}] ~ {k}\n" + "\n".join(field_diffs))

        report.line(
            section,
            f"  [{model_key}] {len(common)} matched, {len(only_repo)} to add, {len(only_anki)} to remove",
            drift=False,
        )

    if not any_drift:
        report.line(section, "  ok", drift=False)


_media_dir = None


def anki_media_bytes(anki_name):
    """Current contents of an Anki media file, or None if Anki doesn't have it.

    Anki runs on this machine, so read its media folder directly (fast for
    hundreds of files, e.g. Geography's map tiles); fall back to AnkiConnect.
    """
    global _media_dir
    if _media_dir is None:
        try:
            _media_dir = invoke("getMediaDirPath")
        except RuntimeError:
            _media_dir = ""
    if _media_dir and os.path.isdir(_media_dir):
        path = os.path.join(_media_dir, anki_name)
        if not os.path.exists(path):
            return None
        with open(path, "rb") as fh:
            return fh.read()
    try:
        b64 = invoke("retrieveMediaFile", filename=anki_name)
    except RuntimeError:
        return None
    return None if b64 is False or b64 is None else base64.b64decode(b64)


def check_media(folder, manifest, report):
    section = "media"
    if not manifest.get("media"):
        return
    ok = 0
    for anki_name, rel in manifest["media"].items():
        path = os.path.join(folder, rel)
        if not os.path.exists(path):
            report.line(section, f"  {anki_name}: repo file '{rel}' missing")
            continue
        with open(path, "rb") as fh:
            repo_bytes = fh.read()
        anki_bytes = anki_media_bytes(anki_name)
        if anki_bytes is None:
            report.line(section, f"  {anki_name}: MISSING in Anki")
        elif anki_bytes != repo_bytes:
            report.line(section, f"  {anki_name}: contents differ ({len(repo_bytes)} B in repo)")
        else:
            ok += 1
    report.line(section, f"  {ok} of {len(manifest['media'])} files ok", drift=False)


# --- commands ------------------------------------------------------------

def cmd_build(folder):
    run_build(folder, load_manifest(folder))
    return 0


def cmd_check(folder, build=True):
    manifest = load_manifest(folder)
    if build:
        run_build(folder, manifest)
        manifest = load_manifest(folder)  # a build script may rewrite it (e.g. media list)
    report = Report()
    for model_key, spec in manifest["models"].items():
        check_model(folder, model_key, spec, report)
    for deck_key, deck_spec in manifest["decks"].items():
        check_deck(folder, deck_key, deck_spec, manifest, report)
    check_media(folder, manifest, report)
    report.dump()
    return 0 if report.in_sync else 1


def cmd_push(folder, dry_run=False, prune=True, build=True):
    manifest = load_manifest(folder)
    if build:
        run_build(folder, manifest)
        manifest = load_manifest(folder)  # a build script may rewrite it (e.g. media list)
    plan = []

    def do(desc, fn):
        plan.append(desc)
        if dry_run:
            print(f"[dry-run] {desc}")
        else:
            print(desc)
            fn()

    # One-time key-field renames: rename matching notes in place (keeping their
    # scheduling) before the diff runs, so a renamed clade is not seen as a
    # delete + re-add. Idempotent: skips anything already renamed.
    renames = manifest.get("renames", {})
    if renames:
        for model_key, spec in manifest["models"].items():
            model, kf = spec["modelName"], spec["keyField"]
            if isinstance(kf, list):
                raise SystemExit(f"{model_key}: \"renames\" needs a single keyField, not {kf}")
            note_ids = invoke("findNotes", query=f'note:"{model}"')
            if not note_ids:
                continue
            key_to_id = {}
            for info in invoke("notesInfo", notes=note_ids):
                key_to_id[info["fields"].get(kf, {}).get("value", "")] = info["noteId"]
            # Loop to a fixpoint so rename chains (A->B where B->C also renames)
            # resolve once the intermediate name is freed.
            progress = True
            while progress:
                progress = False
                for old, new in renames.items():
                    if old in key_to_id and new not in key_to_id:
                        nid = key_to_id.pop(old)
                        key_to_id[new] = nid
                        do(f"rename note {kf} {old!r} -> {new!r}",
                           lambda nid=nid, new=new, kf=kf: invoke(
                               "updateNoteFields", note={"id": nid, "fields": {kf: new}}))
                        progress = True

    existing_models = set(invoke("modelNames"))
    for model_key, spec in manifest["models"].items():
        model = spec["modelName"]
        fields = read_fields(folder, model_key)
        templates = read_templates(folder, model_key, spec)
        css = read_styling(folder, model_key)

        if model not in existing_models:
            do(
                f"createModel {model!r} (fields {fields}, templates {[n for n, _ in templates]})",
                lambda model=model, fields=fields, css=css, templates=templates: invoke(
                    "createModel",
                    modelName=model,
                    inOrderFields=fields,
                    css=css,
                    isCloze=False,
                    cardTemplates=[
                        {"Name": n, "Front": t["Front"], "Back": t["Back"]} for n, t in templates
                    ],
                ),
            )
            continue

        anki_fields = invoke("modelFieldNames", modelName=model)
        if anki_fields != fields:
            raise SystemExit(
                f"{model!r} field mismatch (anki {anki_fields} vs repo {fields}); "
                "fix fields manually in Anki before pushing."
            )
        anki_templates = invoke("modelTemplates", modelName=model)
        repo_names = {n for n, _ in templates}
        if repo_names != set(anki_templates):
            raise SystemExit(
                f"{model!r} template mismatch (anki {list(anki_templates)} vs repo {sorted(repo_names)}); "
                "add/remove card templates manually in Anki before pushing (removing one deletes cards)."
            )
        do(
            f"updateModelTemplates {model!r} ({len(templates)} templates)",
            lambda model=model, templates=templates: invoke(
                "updateModelTemplates",
                model={
                    "name": model,
                    "templates": {n: {"Front": t["Front"], "Back": t["Back"]} for n, t in templates},
                },
            ),
        )
        do(
            f"updateModelStyling {model!r}",
            lambda model=model, css=css: invoke("updateModelStyling", model={"name": model, "css": css}),
        )

    existing_decks = set(invoke("deckNames"))
    for deck_key, deck_spec in manifest["decks"].items():
        anki_deck = deck_spec["ankiDeck"]
        if anki_deck not in existing_decks:
            do(f"createDeck {anki_deck!r}", lambda anki_deck=anki_deck: invoke("createDeck", deck=anki_deck))

        for model_key in deck_spec["models"]:
            spec = manifest["models"][model_key]
            model = spec["modelName"]
            key_field = spec["keyField"]
            fields = read_fields(folder, model_key)
            repo_rows = read_deck_tsv(folder, model_key, fields)
            if repo_rows is None:
                continue
            repo_by_key = {note_key(r["fields"], key_field): r for r in repo_rows}
            anki_by_key = anki_notes_by_key(anki_deck, model, key_field)

            to_add = [k for k in repo_by_key if k not in anki_by_key]
            to_update = [k for k in repo_by_key if k in anki_by_key]
            to_remove = [k for k in anki_by_key if k not in repo_by_key]

            for k in to_add:
                row = repo_by_key[k]
                note = {
                    "deckName": anki_deck,
                    "modelName": model,
                    "fields": row["fields"],
                    "tags": row["tags"],
                    "options": {"allowDuplicate": True},
                }
                do(f"addNote [{model_key}] {k}", lambda note=note: invoke("addNote", note=note))

            for k in to_update:
                row, existing = repo_by_key[k], anki_by_key[k]
                nid = existing["noteId"]
                fields_changed = any(
                    normalize(existing["fields"].get(f, "")) != normalize(row["fields"][f]) for f in fields
                )
                tags_changed = sorted(row["tags"]) != existing["tags"]
                if fields_changed:
                    do(
                        f"updateNoteFields [{model_key}] {k}",
                        lambda nid=nid, row=row: invoke(
                            "updateNoteFields", note={"id": nid, "fields": row["fields"]}
                        ),
                    )
                if tags_changed:
                    do(
                        f"retag [{model_key}] {k} -> {sorted(row['tags'])}",
                        lambda nid=nid, existing=existing, row=row: (
                            invoke("removeTags", notes=[nid], tags=" ".join(existing["tags"]))
                            if existing["tags"] else None,
                            invoke("addTags", notes=[nid], tags=" ".join(row["tags"]))
                            if row["tags"] else None,
                        ),
                    )

            saver_keys = [k for k, r in repo_by_key.items() if MEDIA_SAVER_TAG in r["tags"]]
            saver_query = f'deck:"{anki_deck}" note:"{model}" tag:{MEDIA_SAVER_TAG} -is:suspended'
            if saver_keys and ([k for k in saver_keys if k not in anki_by_key]
                               or invoke("findCards", query=saver_query)):
                do(
                    f"suspend [{model_key}] {MEDIA_SAVER_TAG} cards: {', '.join(saver_keys)}",
                    lambda q=saver_query: invoke("suspend", cards=invoke("findCards", query=q)),
                )

            if prune and to_remove:
                nids = [anki_by_key[k]["noteId"] for k in to_remove]
                do(
                    f"deleteNotes [{model_key}] {len(nids)}: {', '.join(to_remove)}",
                    lambda nids=nids: invoke("deleteNotes", notes=nids),
                )
            elif to_remove:
                print(f"[skip prune] {len(to_remove)} orphan Anki notes [{model_key}]: {', '.join(to_remove)}")

    unchanged = 0
    for anki_name, rel in manifest.get("media", {}).items():
        path = os.path.abspath(os.path.join(folder, rel))
        with open(path, "rb") as fh:
            if fh.read() == anki_media_bytes(anki_name):
                unchanged += 1
                continue
        do(
            f"storeMediaFile {anki_name!r} <- {rel}",
            # data= rather than path=: a path-based store was seen to be undone
            # by the sync that follows, leaving the old file in Anki.
            lambda anki_name=anki_name, path=path: invoke(
                "storeMediaFile", filename=anki_name,
                data=base64.b64encode(open(path, "rb").read()).decode()),
        )

    if unchanged:
        print(f"{unchanged} media file(s) unchanged, not re-sent")
    do("sync", lambda: invoke("sync"))

    # The sync sometimes swaps a just-stored media file back to the older
    # AnkiWeb copy (seen repeatedly with Geography's geog.js); storing it again
    # and re-syncing has always stuck.
    if not dry_run:
        reverted = []
        for anki_name, rel in manifest.get("media", {}).items():
            with open(os.path.join(folder, rel), "rb") as fh:
                data = fh.read()
            if data != anki_media_bytes(anki_name):
                reverted.append(anki_name)
                invoke("storeMediaFile", filename=anki_name, data=base64.b64encode(data).decode())
        if reverted:
            print(f"sync reverted {', '.join(reverted)}; re-stored, syncing again")
            invoke("sync")

    print(f"\n{len(plan)} operation(s){' (dry run, nothing sent)' if dry_run else ''}")
    return 0


def main(argv):
    if len(argv) < 2 or argv[0] not in ("check", "push", "build"):
        print(__doc__)
        return 2
    cmd, folder, flags = argv[0], argv[1].rstrip("/"), argv[2:]
    if not os.path.isdir(folder):
        raise SystemExit(f"not a folder: {folder}")
    if cmd == "build":
        return cmd_build(folder)
    build = "--no-build" not in flags
    if cmd == "check":
        return cmd_check(folder, build=build)
    return cmd_push(folder, dry_run="--dry-run" in flags,
                    prune="--no-prune" not in flags, build=build)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
