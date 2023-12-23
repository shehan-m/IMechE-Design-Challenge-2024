import RPi.GPIO as GPIO
from stepper_motor import StepperMotorController
from target_detector import TargetDetector
import time

# Constants for navigation (Distances are in mm)
SAFE_DISTANCE = 200 # Safe distance to start deceleration to min speed
DATUM_OFFSET = 100 # Offset of datum from camera centre

MAX_SPEED = 0.001
MIN_SPEED = 0.01
DELTA_V = 0.0001 # accerlation/ deceleration

MS_RESOLUTION = 16 # Microstep resolution

# Specification constants
PHASE_1_STOP_TIME = 7.5

# GPIO Pins
LIMIT_SWITCH_PIN = 27

TRIG_PIN = 17
ECHO_PIN = 18

STEP_PIN = 22
DIR_PIN = 23
MS1_PIN = 24
MS2_PIN = 25
MS3_PIN = 12

# Setup GPIO mode and pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(LIMIT_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# Initialize your motor controller and target detector here
motor_controller = StepperMotorController(step_pin=STEP_PIN, dir_pin=DIR_PIN, ms1_pin=MS1_PIN, ms2_pin=MS2_PIN, ms3_pin=MS3_PIN)
motor_controller.set_microstepping(16)  # Set to 16 microsteps per step

target_detector = TargetDetector(camera_index=0, desired_fps=30, desired_width=640, desired_height=480)

def measure_distance():
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()

    while GPIO.input(ECHO_PIN) == 1:
        stop_time = time.time()

    time_elapsed = stop_time - start_time
    distance = (time_elapsed * 343000) / 2  # Speed of sound in air (343000 mm/s)
    
    return distance # distance in mm

def cleanup_gpio():
    motor_controller.cleanup()
    target_detector.release()
    GPIO.cleanup()

def main():
    motor_controller.set_microstepping(16)
    motor_controller.set_speed(MAX_SPEED, DELTA_V)

    limit_switch_pressed = False

    while not limit_switch_pressed:
        if measure_distance() < SAFE_DISTANCE:
            motor_controller.set_speed(MIN_SPEED, -DELTA_V)
        
        motor_controller.step(100, 1)

    motor_controller.step(motor_controller.get_steps, -1)

    # TODO: using y displacement given by target_detector move until y_displacement is constantly 0

    time.sleep(PHASE_1_STOP_TIME)

    motor_controller.step(300*MS_RESOLUTION, 1)

    # TODO: move forward while looking for target once found align with it using same procedure as previously

    motor_controller.stop() # Stop once aligned
    cleanup_gpio()

if __name__ == "__main__":
    main()
