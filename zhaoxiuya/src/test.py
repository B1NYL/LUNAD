import time
from modi_plus import MODIPlus

bundle = MODIPlus()
time.sleep(3)

speaker = bundle.speakers[0]

speaker.play_music("Success", 100)
