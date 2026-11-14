"""Generate Decks/World History/Event.tsv: one note per event in history.js.

Each note's Blurb comes from Data/blurbs.txt (blocks of "event name" line +
blurb lines, separated by blank lines). Media is always "[sound:history.js]":
the template loads history.js itself, but Anki only counts media referenced
from a note field as used, so this keeps Check Media from deleting it (same
trick as NightSky's [sound:sky.js]; the templates render it in a hidden div).

history.js is both the card's runtime data (Anki media) and the source of
truth for which events get cards. It's JS, not JSON (comments, trailing
commas), so strip those before parsing. Run via `anki_sync.py
build|check|push History` (manifest.json's "build" key), or standalone.
"""

import csv
import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Decks", "World History", "media", "history.js")
BLURBS = os.path.join(HERE, "Data", "blurbs.txt")
OUT = os.path.join(HERE, "Decks", "World History", "Event.tsv")
MEDIA = "[sound:history.js]"


def load_hist():
    s = open(SRC, encoding="utf-8").read()
    s = s.split("=", 1)[1].strip().rstrip(";")
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r",(\s*[\]}])", r"\1", s)
    return json.loads(s)


def load_blurbs():
    lines = [l.rstrip() for l in open(BLURBS, encoding="utf-8") if not l.startswith("#")]
    blurbs = {}
    for block in "\n".join(lines).split("\n\n"):
        block = block.strip()
        if not block:
            continue
        name, _, text = block.partition("\n")
        assert name not in blurbs, f"blurbs.txt: duplicate entry for {name!r}"
        blurbs[name] = " ".join(text.split())
    return blurbs


def tag(group_name):
    return re.sub(r"\W+", "_", group_name).strip("_")


def main():
    blurbs = load_blurbs()
    rows = []
    seen = set()
    for group in load_hist():
        for event in group["events"]:
            name = event["name"]
            assert name not in seen, f"duplicate event name: {name}"
            seen.add(name)
            if not blurbs.get(name):
                print(f"WARNING: no blurb for {name!r}")
            rows.append((name, html.escape(blurbs.get(name, ""), quote=False), MEDIA, tag(group["group_name"])))
    for name in sorted(set(blurbs) - seen):
        print(f"WARNING: blurbs.txt entry {name!r} matches no event")
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(("Event", "Blurb", "Media", "Tags"))
        w.writerows(rows)
    print(f"wrote {len(rows)} events to {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    main()
