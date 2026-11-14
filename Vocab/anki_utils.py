"""Shared AnkiConnect helpers for the language decks: notes with TTS audio on both sides."""
import json, os, random, re, string, tempfile, urllib.request

from tts import generate_tts

ANKI_URL = 'http://localhost:8765'

# Audio is copied into Anki's media folder by storeMediaFile, so local mp3s are throwaway.
AUDIO_DIR = tempfile.mkdtemp(prefix='anki_tts_')


def ac(action, **params):
    req = json.dumps({'action': action, 'version': 6, 'params': params}).encode()
    r = json.load(urllib.request.urlopen(ANKI_URL, req))
    if r['error']:
        raise RuntimeError(f'{action}: {r["error"]}')
    return r['result']


def _quote(text):
    return text.replace('\\', '\\\\').replace('"', '\\"').replace('*', '\\*').replace('_', '\\_')


def exists(deck, kind, front):
    """True if `deck` already has a note whose first field is exactly `front`."""
    field = 'Word' if kind == 'V' else 'Front'
    return bool(ac('findNotes', query=f'"deck:{deck}" "{field}:{_quote(front)}"'))


def audio(text, lang):
    """Generate TTS for `text`, store it in Anki's media, and return the [sound:] tag."""
    name = re.sub(r'[^A-Za-z0-9]', '_', text)[:30] + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + '.mp3'
    path = os.path.join(AUDIO_DIR, name)
    generate_tts(text, lang, path)
    ac('storeMediaFile', filename=name, path=path)
    return f'[sound:{name}]'


def add_vocab(deck, word, translation, front_lang, back_lang, pronunciation='', tags=()):
    return _add(deck, 'VocabCard', {
        'Word': word, 'Pronunciation': pronunciation, 'Translation': translation,
        'FrontTTS': audio(word, front_lang), 'BackTTS': audio(translation, back_lang)}, tags)


def add_sentence(deck, front, back, front_lang, back_lang, tags=()):
    return _add(deck, 'BasicWithTTS', {
        'Front': front, 'Back': back,
        'FrontTTS': audio(front, front_lang), 'BackTTS': audio(back, back_lang)}, tags)


def _add(deck, model, fields, tags):
    return ac('addNote', note={'deckName': deck, 'modelName': model, 'fields': fields,
                               'tags': list(tags), 'options': {'allowDuplicate': False}})
