from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play
import os
import uuid

load_dotenv()

# Read file at ~/elevenlabskey
api_key_path = os.path.expanduser("~/elevenlabskey")
with open(api_key_path, "r") as f:
    api_key_text = f.read().strip()
elevenlabs = ElevenLabs(
  api_key=api_key_text
)

MODEL_ID = "eleven_v4"

def get_voice_id_by_language(language):
    if language=="Chinese":
        return "ByhETIclHirOlWnWKhHc"
    if language=="English":
        return "kPzsL2i3teMYv0FxEYQ6"
    if language=="Japanese":
        return "3JDquces8E8bkmvbh6Bc"
    if language=="Indonesian":
        return "RWiGLY9uXI70QL540WNd"
    if language=="Arabic":
        return "JjTirzdD7T3GMLkwdd3a"
    if language=="Spanish":
        return "n4x17EKVqyxfey8QMqvy"
    if language=="Russian":
        return "t6lBrEl93uCiLR1Lgm8v"
    if language=="Portuguese":
        return "33B4UnXyTNbgLmdEDh5P"
    if language=="Amharic":
        return "dmMLCyMoSXGROoBNzDXo"
    if language=="French":
        return "FvmvwvObRqIHojkEGh5N"
    if language=="Dutch":
        return "SXBL9NbvTrjsJQYay2kT"
    if language=="Lao":
        return "h4beepvV9qkgKhIDGbGi"
    if language=="Burmese":
        return "ClAtsC1ukzT6U0XgCO4c"
    if language=="Italian":
        return "13Cuh3NuYvWOVQtLbRN8"
    if language=="German":
        return "dCnu06FiOZma2KVNUoPZ"
    if language=="Czech":
        return "MpbYQvoTmXjHkaxtLiSh"
    if language=="Slovak":
        return "2ST3sI2j7fz4A5oXjnbA"
    if language=="Greek":
        return "0oYUKTNPbymIKVAkDQqh"
    if language=="Urdu":
        return "UT6USLtoAlXHj5k4sOLY"
    if language=="Croatian":
        return "0jvpZ98RZwx5FBOSZAc3"
    if language=="Persian":
        return "8Ebkg5uUcbSbeqGucAoR"
    if language=="Georgian":
        return "rUqJWt6F3HmoAR7Vd7we"
    if language=="Vietnamese":
        return "558B1EcdabtcSdleer40"
    if language=="Korean":
        return "uyVNoMrnUku1dZyVEXwD"
    return None

def generate_tts(text, language, audio_filepath):
    text = '... ' + text + ' ...'
    response = elevenlabs.text_to_speech.convert(
        text=text,
        voice_id=get_voice_id_by_language(language),
        model_id=MODEL_ID,
        output_format="mp3_44100_128",
    )

    with open(audio_filepath, "wb") as f:
        for chunk in response:
            if chunk:
                f.write(chunk)
    print(f"{audio_filepath} generated successfully.")
