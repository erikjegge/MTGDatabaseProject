"""
Idea for this program

1. Loop forever until I break it.
2. During said loop, wait 10 seconds, detect a card with the webcam,
then picture which will put on the azure fileshare, #/mnt/imagestorage/MTGImages

"""
#/mnt/imagestorage/MTGImages

from picamera import PiCamera
import time
from datetime import datetime

# this is the set we are scanning, so we can auto put it into the right folder
set_abrev = 'M11'   #HML

camera = PiCamera() 

camera.start_preview()

for i in range(50):
    time.sleep(4)
    # datetime object containing current date and time
    now = datetime.now()
    dt_string = now.strftime("%Y%m%d%H%M%S")
    print("date and time =", dt_string)
    camera.capture('/mnt/imagestorage/MTGImages/%s/image%s.jpg' % (set_abrev,dt_string))
    print(i)
camera.stop_preview()