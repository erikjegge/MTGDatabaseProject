from picamera2 import Picamera2
from libcamera import Transform

import time
from datetime import datetime
import RPi.GPIO as GPIO
import cv2
import numpy as np


OFFSET_DUTY = 0.05
SERVO_MIN_DUTY = 2.5 + OFFSET_DUTY
SERVO_MAX_DUTY = 12.5 + OFFSET_DUTY
SERVO_DELAY_SEC = 0.001
servoPin = 18   # up down
servoPin2 = 24  # succ

try:
    from src.TMC_2209.TMC_2209_StepperDriver import *
    from src.TMC_2209._TMC_2209_GPIO_board import Board
except ModuleNotFoundError:
    from TMC_2209.TMC_2209_StepperDriver import *
    from TMC_2209._TMC_2209_GPIO_board import Board


def setup():
    global p
    global x

    # Use BCM numbering because your pins are BCM (18 and 24)
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(servoPin, GPIO.OUT)
    GPIO.output(servoPin, GPIO.LOW)

    GPIO.setup(servoPin2, GPIO.OUT)
    GPIO.output(servoPin2, GPIO.LOW)

    x = GPIO.PWM(servoPin, 50)
    x.start(0)

    p = GPIO.PWM(servoPin2, 50)
    p.start(0)


def servoWrite(angle, y):
    if angle < 0:
        angle = 0
    elif angle > 180:
        angle = 180
    dc = SERVO_MIN_DUTY + (SERVO_MAX_DUTY - SERVO_MIN_DUTY) * angle / 180.0
    y.ChangeDutyCycle(dc)


# card detection start
def is_card_like(contour, min_area=10000, aspect_ratio_range=(0.6, 0.75)):
    area = cv2.contourArea(contour)
    if area < min_area:
        return False

    peri = cv2.arcLength(contour, True)
    approx = cv2.approxPolyDP(contour, 0.02 * peri, True)

    if len(approx) == 4:
        x, y, w, h = cv2.boundingRect(approx)
        aspect_ratio = float(w) / h if h != 0 else 0
        if (aspect_ratio_range[0] <= aspect_ratio <= aspect_ratio_range[1]) or (
            aspect_ratio_range[0] <= 1 / aspect_ratio <= aspect_ratio_range[1]
        ):
            return True
    return False


def detect_card(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 75, 200)

    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        if is_card_like(cnt):
            return True
    return False
# card detection end


def pickup():
    for angle in range(50, 140, 1):   # down
        servoWrite(angle, x)
        time.sleep(SERVO_DELAY_SEC)
    time.sleep(1)

    for angle in range(180, -1, -1):  # grip
        servoWrite(angle, p)
        time.sleep(SERVO_DELAY_SEC)
    time.sleep(1)

    for angle in range(140, 50, -1):  # up
        servoWrite(angle, x)
        time.sleep(SERVO_DELAY_SEC)


def picture():
    found_card = False
    start_time = time.time()

    while True:
        image = picam2.capture_array()  # BGR888 numpy array

        if detect_card(image):
            found_card = True
            break

        if time.time() - start_time >= 1.0:
            break

    return found_card


# set info
set_abrev = 'THS'
is_foil = False
is_foil_s = '_FOIL' if is_foil else ''


# camera startup (Picamera2)
picam2 = Picamera2()
camera_config = picam2.create_preview_configuration(
    main={"size": (1920, 1080), "format": "BGR888"},
    transform=Transform(vflip=False, hflip=False)  # toggle if your image is flipped
)
picam2.configure(camera_config)
picam2.start()
time.sleep(1)  # warm up


print("---")
print("SCRIPT START")
print("---")


# initiate the TMC_2209 class
if BOARD == Board.RASPBERRY_PI:
    tmc = TMC_2209(21, 16, 20, loglevel=Loglevel.DEBUG)
elif BOARD == Board.RASPBERRY_PI5:
    tmc = TMC_2209(21, 16, 20, serialport="/dev/ttyAMA0", loglevel=Loglevel.DEBUG)
elif BOARD == Board.NVIDIA_JETSON:
    tmc = TMC_2209(13, 6, 5, serialport="/dev/ttyTHS1", loglevel=Loglevel.DEBUG)
else:
    tmc = TMC_2209(21, 16, 20, loglevel=Loglevel.DEBUG)


def loop():
    tmc.tmc_logger.set_loglevel(Loglevel.DEBUG)
    tmc.set_movement_abs_rel(MovementAbsRel.ABSOLUTE)

    tmc.set_direction_reg(False)
    tmc.set_current(300)
    tmc.set_interpolation(True)
    tmc.set_spreadcycle(False)
    tmc.set_microstepping_resolution(2)
    tmc.set_internal_rsense(False)

    tmc.read_ioin()
    tmc.read_chopconf()
    tmc.read_drv_status()
    tmc.read_gconf()

    tmc.set_acceleration_fullstep(1000)
    tmc.set_max_speed_fullstep(2000)

    tmc.set_motor_enabled(True)

    for angle in range(0, 181, 1):  # release
        servoWrite(angle, p)
        time.sleep(SERVO_DELAY_SEC)

    max_retry = 3
    retry = 0

    while True:
        tmc.run_to_position_steps(-5750)  # Pickup
        pickup()
        time.sleep(1)

        tmc.run_to_position_steps(-3250)  # Picture
        if picture():
            now = datetime.now()
            dt_string = now.strftime("%Y%m%d%H%M%S")
            picam2.capture_file(
                '/mnt/imagestorage/MTGImages/%s/image_%s%s_%s.jpg' %
                (set_abrev, set_abrev, is_foil_s, dt_string)
            )
            time.sleep(1)
        else:
            retry += 1
            if retry >= max_retry:
                destroy()
            else:
                continue

        tmc.run_to_position_steps(0)  # Dropoff
        for angle in range(0, 181, 1):  # release
            servoWrite(angle, p)
            time.sleep(SERVO_DELAY_SEC)
        time.sleep(1)


def destroy():
    tmc.run_to_position_steps(0)

    try:
        picam2.stop()
    except Exception:
        pass

    p.stop()
    x.stop()
    GPIO.cleanup()

    tmc.set_motor_enabled(False)
    del tmc


if __name__ == '__main__':
    print('Program is starting...')
    setup()
    try:
        loop()
    except KeyboardInterrupt:
        destroy()
