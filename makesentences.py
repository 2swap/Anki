#!/usr/bin/env python3
import sys
import os
import json
import requests
import openai
import re
from gtts import gTTS

# A mapping from language names to their gTTS language codes.
LANG_MAP = {
    "Indonesian": "id",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Chinese": "zh-cn",
    "Korean": "ko",
    "Italian": "it",
    "Russian": "ru"
}

def main():
    # Expect at least two arguments: the language and the foreign word.
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <language> <foreign_word>")
        sys.exit(1)

    # The first argument is the language, the rest join to form the word.
    language = sys.argv[1].strip()
    foreign_word = " ".join(sys.argv[2:]).strip()

    # Get the gTTS language code from the mapping.
    lang_code = LANG_MAP.get(language.capitalize())
    if lang_code is None:
        print("Unsupported language. Supported languages are:", ", ".join(LANG_MAP.keys()))
        sys.exit(1)

    # Read the OpenAI API key from file.
    try:
        with open('/home/swap/openaikey', 'r') as keyFile:
            openai_api_key = keyFile.readline().strip()
    except Exception as e:
        print("Error reading API key:", e)
        sys.exit(1)

    if not openai_api_key:
        print("Error: OPENAI_API_KEY is not set.")
        sys.exit(1)

    openai.api_key = openai_api_key

    # Build the prompt for generating sentences.
    prompt = (
        f"Generate 3 sentences in {language} for each of the following words: '{foreign_word}'. "
    )
    
    try:
        completion = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": (
                    "You are a helpful assistant that generates flashcards. Provide the flashcards as a JSON object "
                    "where each key is a sentence (in the foreign language) and each value is the corresponding English translation. "
                    "Ensure the sentences are natural, diverse, and include the given foreign word. They should contain 4-7 words. "
                    "Do not include any extra commentary or formatting. "
                    "Even if the user types a romanized word, produce the target-language sentence in the native writing system."
                )},
                {"role": "user", "content": prompt}
            ],
        )
    except Exception as e:
        print("Error querying OpenAI API:", e)
        sys.exit(1)
        
    raw_response = completion.choices[0].message.content.strip()
    print("Got GPT response json. Parsing...")
    json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
    if json_match:
        flashcards_json = json_match.group(0)
        try:
            sentences_dict = json.loads(flashcards_json)
        except json.JSONDecodeError as e:
            print("Failed to decode JSON from OpenAI response. Response was:")
            print(flashcards_json)
            sys.exit(1)
    else:
        print("No valid JSON found in OpenAI response. Full response was:")
        print(raw_response)
        sys.exit(1)

    notes = []
    # Set the media directory to ~/anki_media and ensure it exists.
    media_dir = os.path.expanduser("~/anki_media")
    os.makedirs(media_dir, exist_ok=True)
    # Process each sentence and its translation.
    for sentence, translation in sentences_dict.items():
        # Create a file name for the audio snippet.
        # Remove non-word characters and replace spaces with underscores.
        audio_filename = re.sub(r'\W+', '_', sentence).strip('_') + ".mp3"
        audio_filepath = os.path.join(media_dir, audio_filename)
        try:
            # Generate TTS audio for the sentence.
            tts = gTTS(sentence, lang=lang_code)
            tts.save(audio_filepath)
        except Exception as e:
            print("Error generating TTS audio for sentence:", e)
            sys.exit(1)

        note = {
            "deckName": language.capitalize(),
            "modelName": "SentenceWithAudio",
            "fields": {
                "Text": sentence,
                "Translation": translation,
                "Audio": "[sound:" + audio_filename + "]",
            },
            "options": {
                "allowDuplicate": True
            },
            "tags": []
        }
        notes.append(note)

    payload = {
        "action": "addNotes",
        "version": 6,
        "params": {
            "notes": notes
        }
    }

    # Send the generated notes to AnkiConnect.
    anki_url = "http://localhost:8765"
    try:
        anki_response = requests.post(anki_url, json=payload)
        result = anki_response.json()
        print("AnkiConnect response:")
        print(json.dumps(result, indent=2))
    except Exception as e:
        print("Error sending request to AnkiConnect:", e)
        sys.exit(1)

if __name__ == '__main__':
    main()
