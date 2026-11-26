"""Write Tsumego.tsv from notes.py (run by anki_sync.py check/push).

Every note is transcribed from Sensei's Library diagrams (Data/sldata.json, made by
Data/extract.py from saved pages). Each line is replayed with capture and ko rules,
and checked against the position its source diagram shows, before it is written.
"""
import csv, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import notes  # noqa: E402  (defines the notes)
from sensei import build  # noqa: E402

FIELDS = [l.strip() for l in open(os.path.join(HERE, 'Card Types', 'Tsumego', 'fields.txt')) if l.strip()]

rows = build()
with open(os.path.join(HERE, 'Tsumego.tsv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh, delimiter='\t', lineterminator='\n')
    w.writerow(FIELDS + ['Tags'])
    for r in rows:
        w.writerow([r[f] for f in FIELDS] + ['tsumego'])
print(f'Tsumego.tsv: {len(rows)} notes')
