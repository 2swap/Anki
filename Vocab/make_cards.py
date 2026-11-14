"""Create vocab + sentence notes with TTS audio via AnkiConnect.

Usage: python3 make_cards.py cards.json

cards.json:
{
  "deck": "Spanish",
  "front_lang": "Spanish",      # language of Word / Front (see tts.py)
  "back_lang": "Indonesian",    # language of Translation / Back
  "cards": [["V", word, translation], ["V", word, translation, pronunciation],
            ["S", sentence, translation], ...]
}
"V" makes a VocabCard note (optional 4th item fills Pronunciation, e.g. pinyin),
"S" a BasicWithTTS note. A card whose front already exists in the deck is skipped
(checked before any TTS is generated), and the run continues.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.dont_write_bytecode = True  # keep __pycache__ out of the tools folder
from anki_utils import ac, exists, add_vocab, add_sentence


def main(spec_path):
    with open(spec_path) as f:
        spec = json.load(f)
    deck, fl, bl = spec['deck'], spec['front_lang'], spec['back_lang']
    ac('createDeck', deck=deck)
    added, skipped, failed = 0, [], []
    for kind, front, back, *rest in spec['cards']:
        if exists(deck, kind, front):
            skipped.append(front)
            print(kind, front, '-> SKIPPED (already in deck)', flush=True)
            continue
        try:
            if kind == 'V':
                nid = add_vocab(deck, front, back, fl, bl, pronunciation=rest[0] if rest else '')
            else:
                nid = add_sentence(deck, front, back, fl, bl)
        except RuntimeError as e:
            failed.append(front)
            print(kind, front, '-> FAILED:', e, flush=True)
            continue
        added += 1
        print(kind, front, '->', nid, flush=True)
    print(f'\n{added} added, {len(skipped)} skipped, {len(failed)} failed')
    for label, items in (('Skipped', skipped), ('Failed', failed)):
        if items:
            print(f'{label}: ' + ', '.join(items))
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
