"""Regenerate the Music deck: audio in media/, Basic.tsv, and
manifest.json's "media" map. Run from this folder (anki_sync.py does this).

To add a new kind of card (e.g. chords), add a generator to CARD_SETS that
yields (media_stem, steps, back_html, tags), where steps is a list of chords
(each a list of MIDI notes) played one after another -- see synth.render_sequence.
"""

import csv
import json
import os
import random

from synth import render_sequence, write_mp3

MEDIA_DIR = "media"
TSV_PATH = "Basic.tsv"

INTERVALS = [
    "Unison", "Minor 2nd", "Major 2nd", "Minor 3rd", "Major 3rd", "Perfect 4th",
    "Tritone", "Perfect 5th", "Minor 6th", "Major 6th", "Minor 7th", "Major 7th",
    "Octave",
]


def intervals():
    """Melodic intervals, minor 2nd through octave: low note, then high note.
    Each is rooted on an arbitrary fixed note (seeded, so rebuilds don't change it)."""
    rng = random.Random("music-intervals")
    for semitones, name in enumerate(INTERVALS):
        root = rng.randrange(48, 72)  # C3..B4, so the top note stays <= B5
        if semitones == 0:
            # No unison card. Its root is still drawn above so every other
            # interval keeps the same notes (and audio) as before.
            continue
        stem = f"music_interval_{semitones:02d}"
        yield stem, [[root], [root + semitones]], name, ["music::interval"]


CARD_SETS = [intervals]


def main():
    os.makedirs(MEDIA_DIR, exist_ok=True)
    rows, media = [], {}
    for card_set in CARD_SETS:
        for stem, steps, back, tags in card_set():
            fname = f"{stem}.mp3"
            write_mp3(render_sequence(steps), os.path.join(MEDIA_DIR, fname))
            media[fname] = f"{MEDIA_DIR}/{fname}"
            rows.append([f"[sound:{fname}]", back, " ".join(tags)])

    # Drop stale audio no longer referenced by any card.
    for f in os.listdir(MEDIA_DIR):
        if f not in media:
            os.remove(os.path.join(MEDIA_DIR, f))

    with open(TSV_PATH, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["Front", "Back", "Tags"])
        w.writerows(rows)

    with open("manifest.json") as fh:
        manifest = json.load(fh)
    manifest["media"] = media
    with open("manifest.json", "w") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"wrote {len(rows)} notes, {len(media)} audio files")


if __name__ == "__main__":
    main()
