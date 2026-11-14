# Anki language decks

Cards are added to the running Anki app through AnkiConnect (`http://localhost:8765`) using `make_cards.py`, with audio from `tts.py` (ElevenLabs, `eleven_v4`).

## Decks

| Deck | Front | Back |
|---|---|---|
| Indonesian | Indonesian | Spanish |
| Spanish | Spanish | Indonesian |

## Note types

- **VocabCard**: `Word`, `Pronunciation` (empty except for Chinese/Japanese pinyin or furigana, via an optional 4th spec item), `Translation`, `FrontTTS`, `BackTTS`
- **BasicWithTTS** (example sentences): `Front`, `Back`, `FrontTTS`, `BackTTS`

Both sides of every note get TTS audio (`[sound:...]`), generated in the language of that side.

## Cards per word

1. A VocabCard for the word. Use the dictionary form, such as the infinitive or singular. If the user gives an inflected form (e.g. *aturdiéndolos*), use it in a sentence instead.
2. Two BasicWithTTS sentences. Keep them very short: natural phrases of 2–5 words (e.g. `rueda de repuesto`, `Kuncinya gemerincing`), not full long sentences. Indonesian sentences have no trailing period.
3. Optionally, a VocabCard for a related form, such as a derived word, the standard form of slang, or the expansion of an abbreviation. Follow it with one sentence.

Spanish nouns always include the definite article (`el`/`la`) in the VocabCard word, whether or not the user gave it (e.g. `el tenedor`, `la cuchara`; `el agua` for feminine nouns with a stressed *a-*). When a noun's meaning changes with gender (e.g. `el cura` / `la cura`), make a separate VocabCard for each gender, each with its own sentences.

Translations separate senses with `;` and note regional or abbreviation info in parentheses, e.g. `trabajador sanitario (abrev. de tenaga kesehatan)`.

## Workflow

1. Check the deck for existing notes so nothing is duplicated. Search by root as well as exact form (`findNotes` with `"deck:<Deck>" "Word:*x*"` and `"Front:*x*"`, one query per field: combined `OR` queries have missed matches). If the word already has a VocabCard, skip it and its sentences rather than adding sentences to it.
2. Write the batch spec as JSON in the scratchpad, **not** in this folder. Only reusable tools live here.
3. Run `python3 Vocab/make_cards.py <spec.json>`. It skips any card whose exact front already exists in the deck (checked before TTS, so no credits are spent), keeps going on errors, and ends with a summary of added / skipped / failed.

Files here: `make_cards.py` (reads a spec and adds the cards), `anki_utils.py` (AnkiConnect helpers: `ac`, `exists`, `add_vocab`, `add_sentence`), `tts.py` (ElevenLabs voices per language).

Spec format:

```json
{
  "deck": "Indonesian",
  "front_lang": "Indonesian",
  "back_lang": "Spanish",
  "cards": [["V", "word", "translation"], ["S", "sentence", "translation"]]
}
```

If a requested word looks misspelled or doesn't exist, ask before adding it.
