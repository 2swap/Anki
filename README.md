# Anki

My Anki decks as editable files. Each deck under `Collection/` mirrors one deck
in the live collection, and `anki_sync.py` compares the two and pushes the repo
into Anki through AnkiConnect (`localhost:8765`, so Anki must be running).

## Layout

```
Anki/
├── anki_sync.py          check / push / build a deck folder
├── list_decks.py         print every live deck with its card counts
├── Collection/           one folder per synced deck; the path IS the deck name
│   ├── Go/                                    -> deck "Go"
│   ├── Humanities/Geography/                  -> deck "Humanities::Geography"
│   └── Natural Sciences/Standard Model/       -> deck "Natural Sciences::Standard Model"
├── Note Types/           note types shared by several decks (symlinked into their Card Types/)
├── In Development/       decks not in the live collection yet (History, Life)
└── Vocab/                card-making tools for the language decks (not mirrored)
```

The Indonesian, Spanish, Chinese and Connect 4 decks live only in Anki.

A deck folder:

```
Collection/Natural Sciences/Standard Model/
├── manifest.json         note types (+ media, + build)
├── Card Types/
│   └── Particle/         one dir per note type
│       ├── fields.txt    field names, in order
│       ├── style.css
│       └── 1_Name_on_Grid/front.html, back.html   one dir per card type (sorted = card order)
├── Particle.tsv          the deck's notes of that note type: fields + Tags
├── Group.tsv
├── media/                files the cards use (images, audio, JS)
└── build.py              optional: regenerates the TSVs from source data
```

To rename or move a deck, rename or move its folder (then push).

A note type used by several decks lives once in `Note Types/<name>/`, and each
deck's `Card Types/<name>` is a relative symlink to it. Clouds, Math and Music
all use `Note Types/Basic`, so editing it and pushing any one of those decks
updates all three. (On Windows, Git needs `core.symlinks=true` and Developer
Mode to check the links out as links.)

## Using anki_sync.py

```
python3 anki_sync.py check "Collection/Humanities/Poems"           # report drift, exit 1 if any
python3 anki_sync.py push  "Collection/Humanities/Poems" --dry-run # show what a push would do
python3 anki_sync.py push  "Collection/Humanities/Poems"           # make Anki match, then sync
python3 anki_sync.py build "Collection/Humanities/Poems"           # only run the build script
```

`check` and `push` run the folder's build script first (`--no-build` skips it).
A push also **deletes** Anki notes in that deck that aren't in the repo, unless
`--no-prune`.

**Always `check` first, and treat Anki-side drift as real.** The live
collection has been edited directly before and was newer than the repo
(2026-11). If `check` shows changes the repo doesn't have, bring them into the
repo first (TSVs, Card Types, build data): a push would overwrite them, and its
pruning deletes notes missing from the repo.

### manifest.json

```json
{
  "models": {
    "Particle": {"modelName": "Standard Model - Particle", "keyField": "Name"}
  },
  "media": {"chem_water.svg": "media/chem_water.svg"},
  "build": ["build.py"]
}
```

- `keyField` matches a TSV row to an Anki note. Use a list (e.g. Go's
  `["Board", "ToPlay"]`) when no single field is unique.
- `templateName` names the card type of a note type with only one, whose
  `front.html`/`back.html` sit directly in its `Card Types/` dir.
- `media` maps each Anki media filename to its file in the folder.
- There is no `decks` section or `ankiDeck`: the folder's path is its deck
  name. `anki_sync.py` refuses manifests that have them, and refuses folders
  outside `Collection/`.

### Decks with a build script

Geography, Math, Minerals, Music, Standard Model and Export Portfolios generate
their TSVs (and sometimes media and the manifest's media list), so edit the
build script or its source data, never the generated TSV, and run `check`
(which builds) to confirm. The others' TSVs are edited by hand.

## Schema changes force a full sync

Adding or removing a field, card type or note type is a schema change: the next
sync needs a one-way full sync, you pick Upload in Anki's dialog, and the phone
must then download. Batch schema changes, and sync the phone beforehand (an
upload discards reviews that only AnkiWeb has).

`push` won't add or remove card types itself: use `modelFieldAdd` /
`modelTemplateAdd` / `modelTemplateRemove`, then push. AnkiConnect can't delete
a note type; do that in Tools > Manage Note Types.

Don't split a deck across several note types just to avoid a full sync (that is
how Standard Model once got a separate Decay type, merged back 2026-11).

## Per-deck tools

- **Chemicals:** `python3 draw_structure.py "Name" "SMILES"` draws a new
  structure in the deck's style (RDKit) and prints the TSV row to add.
- **Go:** `go_tsumego.py check|add spec.json` verifies corner life-and-death
  problems by exhaustive search (with `go_search.c`) before they become cards.
- **Geography:** source data is `Data/<folder>/` (map JS + pronunciation mp3s);
  `AUDIO_CREDITS.tsv` credits every recording and marks AI voices;
  `build_tiles.py` regenerates the git-ignored Blue Marble tiles in `bluemarble/`.
- **Language decks:** see `Vocab/CLAUDE.md`.

Keep these tools' scratch files (specs, backups) out of the repo.

## Media loaded only by a card template: one suspended "media saver" note

Some cards load files by script instead of through a note field (e.g.
`<script src="geog.js">`, which then fetches map files). Anki only counts a
media file as used if some note *field* references it, so a file only a
template loads shows as unused in Tools > Check Media (which can delete it) and
never reaches AnkiWeb or other devices.

The fix is one extra note per deck (key field `_media_saver`, tagged
`media_saver`) whose field lists every such file as a sound tag:
`[sound:geog.js][sound:geog_usa.js]...`. Don't put those tags on regular notes:
Anki tries to autoplay every `[sound:]` it renders, even in a hidden div.
`push` suspends the media saver's cards, and `check` flags one that isn't.
Geography's build makes its media saver this way. Night Sky still uses the old
form (`[sound:sky.js]` on every note).

## AnkiConnect gotchas

- After `sync` (including the one at the end of `push`), other actions fail with
  "Collection lifecycle operation is active" for a while. Poll a cheap read
  (`modelNames`) until it succeeds before the next call.
- Scheduling: `setSpecificValueOfCard` refuses due/interval/type/queue ("Use
  native scheduling commands"). `setDueDate` (days from today) and
  `setEaseFactors` work, but this version ignores the `!` suffix, so a card's
  interval can't be set. Moving cards between notes loses history; at best copy
  due date and ease.
- `cardsInfo` calls the interval `interval`, not `ivl`.
- Stored media names are lowercased; card scripts must ask for the lowercase name.
- Duplicate checks only look at the first field; search by exact field values
  (one query per field) when it matters.

### Full sync without the dialog: the `fullSync` patch (currently NOT installed)

AnkiConnect's `sync` pops Anki's Upload/Download dialog when a full sync is
needed and waits, so it can't finish unattended. A local `fullSync` action was
once patched into `~/.local/share/Anki2/addons21/2055492159/`, but AnkiConnect
auto-updates and wipes it (`grep -c fullSync .../__init__.py` was 0 on
2026-11-13). Without it, click Upload yourself. To reinstall:

- `gui.py`: `collection_sync(self, includeMedia=True, fullSyncUpload=None)`;
  right after the `directions = ...` line in `synced()`, if `fullSyncUpload` is
  not None, call `full(out, fullSyncUpload)` (or `fail(...)` if that direction
  isn't allowed) and `return` instead of showing `ask_user_dialog`.
- `__init__.py`: `@util.api() def fullSync(self, upload=True)` after `sync`,
  returning `self.runtime.gui.collection_sync(fullSyncUpload=bool(upload))`;
  and in `handler_async`, before the `elif name.startswith('gui') ...` branch:
  `elif name == 'fullSync': value = self.fullSync(**params); pending = value if
  isinstance(value, Deferred) else completed(value)`.
- Restart Anki: `kill -9 $(pgrep -f '^/usr/bin/python /usr/bin/anki$')` (never
  `pkill -f /usr/bin/anki`, which also kills the calling shell), then relaunch
  with the old process's display env (DISPLAY, WAYLAND_DISPLAY, XAUTHORITY,
  XDG_RUNTIME_DIR, DBUS_SESSION_BUS_ADDRESS from `/proc/<pid>/environ`) via
  `setsid nohup /usr/bin/anki &`, and poll `localhost:8765`.

`fullSync(upload=True)` overwrites AnkiWeb (the usual direction here);
`upload=False` overwrites local. Whichever side isn't chosen is discarded.

## In Development

Decks that aren't in the live collection yet. `anki_sync.py` ignores anything
outside `Collection/`. To launch one, bring its folder up to the layout above
(drop the manifest's `decks` section, move its TSVs next to the manifest) and
move it into `Collection/` at the deck path it should have.
