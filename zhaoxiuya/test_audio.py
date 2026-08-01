import scipy.io.wavfile
import sounddevice as sd

print("Reading...")
spr, audio = scipy.io.wavfile.read("outputs/mike/1785602919312212626.wav")
print(f"Sample rate: {spr}")
print(f"Audio shape: {audio.shape}, dtype: {audio.dtype}")
print("Playing...")
try:
    sd.play(audio, spr)
    sd.wait()
    print("Done playing!")
except Exception as e:
    print(f"Error playing: {e}")
