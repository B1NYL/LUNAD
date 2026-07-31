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

def rec(sec):
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

def s2t(path):
    with open(path, "rb") as audio:
        dotenv.load_dotenv()
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio
        )
        return transcription.text

def t2s(text):
    dotenv.load_dotenv()
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    with client.audio.speech.with_streaming_response.create(
        model="gpt-4o-mini-tts",
        voice="coral",
        input=text,
        response_format="wav",
    ) as response:
        response.stream_to_file(mike_path / f"{time.time_ns()}.wav")