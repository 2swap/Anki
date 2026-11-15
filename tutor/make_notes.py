"""Add notes of any note type to any deck via AnkiConnect, creating the note type if asked.

Usage: python3 make_notes.py spec.json

spec.json, with an existing note type:
{
  "deck": "Humanities::Geography",
  "note_type": "Basic",
  "tags": ["tutor"],
  "notes": [{"Front": "...", "Back": "..."}, ...]      # field name -> value (HTML)
}

or with a new one (created only if no note type has that name yet; an existing note
type is never changed):
{
  "deck": "...",
  "new_note_type": {
    "name": "Tutor - Map Label",
    "fields": ["Place", "Hint", "Answer"],
    "templates": [{"name": "Card 1", "front": "{{Place}}", "back": "{{FrontSide}}<hr>{{Answer}}"}],
    "css": ".card { ... }",          # optional
    "cloze": false                  # optional; a cloze type has exactly one template
  },
  "tags": ["tutor"],
  "notes": [...]
}

A note whose first field matches a note of the same type already in the deck is
skipped. Prints one line per note, "N <first field> -> <note id>" or "-> SKIPPED" or
"-> FAILED: <reason>", like Vocab/make_cards.py.
"""
import json
import sys
import urllib.request

ANKI_URL = "http://localhost:8765"


def ac(action, **params):
    req = json.dumps({"action": action, "version": 6, "params": params}).encode()
    r = json.load(urllib.request.urlopen(ANKI_URL, req, timeout=30))
    if r["error"]:
        raise RuntimeError(f"{action}: {r['error']}")
    return r["result"]


def quote(text):
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("*", "\\*").replace("_", "\\_")


def main(spec_path):
    with open(spec_path) as f:
        spec = json.load(f)
    deck, tags = spec["deck"], spec.get("tags", [])
    new = spec.get("new_note_type")
    if new:
        model = new["name"]
        if model in ac("modelNames"):
            print(f"note type {model!r} already exists; not changing it")
        else:
            ac("createModel", modelName=model, inOrderFields=new["fields"],
               css=new.get("css", ""), isCloze=bool(new.get("cloze")),
               cardTemplates=[{"Name": t["name"], "Front": t["front"], "Back": t["back"]}
                              for t in new["templates"]])
            print(f"created note type {model!r}")
    else:
        model = spec["note_type"]
    fields = ac("modelFieldNames", modelName=model)
    first = fields[0]
    ac("createDeck", deck=deck)

    added, skipped, failed = 0, [], []
    for values in spec["notes"]:
        label = values.get(first, "")
        if ac("findNotes", query=f'"deck:{quote(deck)}" "note:{quote(model)}" "{quote(first)}:{quote(label)}"'):
            skipped.append(label)
            print("N", label, "-> SKIPPED (already in deck)", flush=True)
            continue
        try:
            nid = ac("addNote", note={"deckName": deck, "modelName": model,
                                      "fields": {f: values.get(f, "") for f in fields},
                                      "tags": tags, "options": {"allowDuplicate": False}})
        except RuntimeError as e:
            failed.append(label)
            print("N", label, "-> FAILED:", e, flush=True)
            continue
        added += 1
        print("N", label, "->", nid, flush=True)
    print(f"\n{added} added, {len(skipped)} skipped, {len(failed)} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
