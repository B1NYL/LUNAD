import dotenv
import openai
import os
import sounddevice as sd
import numpy as np
import io
import scipy
import time
import pathlib
inputs_path = pathlib.Path("../inputs")
outputs_path = pathlib.Path("../outputs")
mike_path = outputs_path / "mike"

def rec_speech(sec):
    fs = 16000
    audio_data = sd.rec(
        int(fs * sec),
        samplerate=fs,
        channels=1,
        dtype='float32'
    )
    sd.wait()
    audio_data = np.squeeze(audio_data)
    audio = io.BytesIO()
    audio.name = "speech.wav"
    scipy.io.wavfile.write(audio, fs, audio_data)
    audio.seek(0)
    return audio

def rec_path(sec):
    fs = 16000
    audio_data = sd.rec(
        int(fs * sec),
        samplerate=fs,
        channels=1,
        dtype='float32'
    )
    sd.wait()
    ret_path = mike_path / f"{time.time_ns()}.wav"
    scipy.io.wavfile.write(ret_path, fs, audio_data)
    return ret_path.absolute()

def speech2text(audio):
    dotenv.load_dotenv()
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    transcription = client.audio.transcriptions.create(
        model="whisper-1", 
        file=audio
    )
    return transcription.text

def path2text(path):
    with open(path, "rb") as audio:
        return speech2text(audio=audio)