from picamera import PiCamera
from picamera.array import PiRGBArray
import time
from datetime import datetime
import RPi.GPIO as GPIO
import cv2
import numpy as np


OFFSET_DUTY = 0.05        # define pulse offset of servo
SERVO_MIN_DUTY = 2.5 + OFFSET_DUTY  # 2.5 + OFFSET_DUTY     # define pulse duty cycle for minimum angle of servo
SERVO_MAX_DUTY = 12.5 + OFFSET_DUTY  #12.5 + OFFSET_DUTY   # define pulse duty cycle for maximum angle of servo
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
    #GPIO.setmode(GPIO.BOARD)         # use PHYSICAL GPIO Numbering
    GPIO.setup(servoPin, GPIO.OUT)   # Set servoPin to OUTPUT mode
    GPIO.output(servoPin, GPIO.LOW)  # Make servoPin output LOW level

    #GPIO.setmode(GPIO.BOARD)         # use PHYSICAL GPIO Numbering
    GPIO.setup(servoPin2, GPIO.OUT)   # Set servoPin to OUTPUT mode
    GPIO.output(servoPin2, GPIO.LOW)  # Make servoPin output LOW level
    
    x = GPIO.PWM(servoPin, 50)     # set Frequence to 50Hz
    x.start(0)                     # Set initial Duty Cycle to 0

    p = GPIO.PWM(servoPin2, 50)     # set Frequence to 50Hz
    p.start(0)                     # Set initial Duty Cycle to 0
    
def servoWrite(angle,y):      # make the servo rotate to specific angle, 0-180 
    if(angle < 0):
        angle = 0
    elif(angle > 180):
        angle = 180
    dc = SERVO_MIN_DUTY + (SERVO_MAX_DUTY - SERVO_MIN_DUTY) * angle / 180.0 # map the angle to duty cycle
    y.ChangeDutyCycle(dc)
    #time.sleep(0.5)
    #y.ChangeDutyCycle(0) # jitter happenign?

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
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
        if aspect_ratio_range[0] <= aspect_ratio <= aspect_ratio_range[1] or \
           aspect_ratio_range[0] <= 1/aspect_ratio <= aspect_ratio_range[1]:
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
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

"""
    pickup function

    goes to pickup location, picks up card
"""
def pickup():
        for angle in range(50, 140, 1):   # make servo rotate from 0 to 180 deg down
            servoWrite(angle,x)
            time.sleep(SERVO_DELAY_SEC)
        time.sleep(1)
        
        for angle in range(180, -1, -1): # make servo rotate from 180 to 0 deg grip
            servoWrite(angle,p)
            time.sleep(SERVO_DELAY_SEC)
        time.sleep(1)  
        for angle in range(140, 50, -1): # make servo rotate from 180 to 0 deg  up
            servoWrite(angle,x)
            time.sleep(SERVO_DELAY_SEC)

"""
    picture function
    goes to picture location, identifies if it has a card, takes picture if it does. Goes back to pickup if it doesn't. Max retries of 2.
"""
def picture():
    # this code will look at the card for one second, if there is a card. It will take a picture. Else it will try to pick up another card.
    found_card = False
    start_time = time.time()

    for frame in camera.capture_continuous(raw_capture, format="bgr", use_video_port=True):
        image = frame.array

        if detect_card(image):
            found_card = True
            break

        raw_capture.truncate(0)

        if time.time() - start_time >= 1.0:
            break

    return found_card

# this is the set we are scanning, so we can auto put it into the right folder
set_abrev = 'THS'   #TEST is the general and testing directory
is_foil = False

if is_foil:
    is_foil_s = '_FOIL'
else:
    is_foil_s = ''

# camera startup
camera = PiCamera()
camera.resolution = (1920, 1080)
camera.framerate = 30
raw_capture = PiRGBArray(camera, size=(1920, 1080))
camera.start_preview()

print("---")
print("SCRIPT START")
print("---")

#-----------------------------------------------------------------------
# initiate the TMC_2209 class
# use your pins for pin_en, pin_step, pin_dir here
#-----------------------------------------------------------------------
if BOARD == Board.RASPBERRY_PI:
    tmc = TMC_2209(21, 16, 20, loglevel=Loglevel.DEBUG)
elif BOARD == Board.RASPBERRY_PI5:
    tmc = TMC_2209(21, 16, 20, serialport="/dev/ttyAMA0", loglevel=Loglevel.DEBUG)
elif BOARD == Board.NVIDIA_JETSON:
    tmc = TMC_2209(13, 6, 5, serialport="/dev/ttyTHS1", loglevel=Loglevel.DEBUG)
else:
    # just in case
    tmc = TMC_2209(21, 16, 20, loglevel=Loglevel.DEBUG)

def loop():
    #-----------------------------------------------------------------------
    # set the loglevel of the libary (currently only printed)
    # set whether the movement should be relative or absolute
    # both optional
    #-----------------------------------------------------------------------
    tmc.tmc_logger.set_loglevel(Loglevel.DEBUG)
    tmc.set_movement_abs_rel(MovementAbsRel.ABSOLUTE)

    #-----------------------------------------------------------------------
    # these functions change settings in the TMC register
    #-----------------------------------------------------------------------
    tmc.set_direction_reg(False)
    tmc.set_current(300)
    tmc.set_interpolation(True)
    tmc.set_spreadcycle(False)
    tmc.set_microstepping_resolution(2)
    tmc.set_internal_rsense(False)

    #-----------------------------------------------------------------------
    # these functions read and print the current settings in the TMC register
    #-----------------------------------------------------------------------
    tmc.read_ioin()
    tmc.read_chopconf()
    tmc.read_drv_status()
    tmc.read_gconf()

    #-----------------------------------------------------------------------
    # set the Acceleration and maximal Speed
    #-----------------------------------------------------------------------
    #tmc.set_acceleration(2000)
    #tmc.set_max_speed(500)

    #-----------------------------------------------------------------------
    # set the Acceleration and maximal Speed in fullsteps
    #-----------------------------------------------------------------------
    # test 1: up speed, leave acc same  500 good 750 good 1000 good 1250
    tmc.set_acceleration_fullstep(1000)
    tmc.set_max_speed_fullstep(2000)

    #-----------------------------------------------------------------------
    # activate the motor current output
    #-----------------------------------------------------------------------
    tmc.set_motor_enabled(True)

    for angle in range(0, 181, 1):   # make servo rotate from 0 to 180 deg  release
        servoWrite(angle,p)
        time.sleep(SERVO_DELAY_SEC)
    
    max_retry = 3
    retry = 0
    # this is where loop begins!
    while True:
        tmc.run_to_position_steps(-5750) # Pickup
        pickup()
        time.sleep(1)

        tmc.run_to_position_steps(-3250) # Picture
        if picture():
            now = datetime.now()
            dt_string = now.strftime("%Y%m%d%H%M%S")
            camera.capture('/mnt/imagestorage/MTGImages/%s/image_%s%s_%s.jpg' % (set_abrev,set_abrev,is_foil_s,dt_string))
            time.sleep(1)
        else:
            retry += 1
            if retry >= max_retry:
                destroy()
            else:
                continue

        tmc.run_to_position_steps(0) # Dropoff
        for angle in range(0, 181, 1):   # make servo rotate from 0 to 180 deg  release
            servoWrite(angle,p)
            time.sleep(SERVO_DELAY_SEC)
        time.sleep(1)

def destroy():
    tmc.run_to_position_steps(0)
    camera.stop_preview()
    p.stop()
    x.stop()
    GPIO.cleanup()
    #-----------------------------------------------------------------------
    # deactivate the motor current output
    #-----------------------------------------------------------------------
    tmc.set_motor_enabled(False)
    #-----------------------------------------------------------------------
    # deinitiate the TMC_2209 class
    #-----------------------------------------------------------------------
    del tmc

if __name__ == '__main__':     # Program entrance
    print ('Program is starting...')
    setup()
    try:
        loop()
    except KeyboardInterrupt:  # Press ctrl-c to end the program.
        destroy()