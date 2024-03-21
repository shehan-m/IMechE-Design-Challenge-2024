import RPi.GPIO as GPIO
from Firmware.old.stepper_motor import StepperMotorController
from Firmware.old.target_detector_V1 import TargetDetector
import time

# Constants for navigation (Distances are in mm)
SAFE_DISTANCE = 200 # Safe distance to start deceleration to min speed
DATUM_OFFSET = 100 # Offset of datum from camera centre

MAX_SPEED = 0.001
MIN_SPEED = 0.01
DELTA_V = 0.0001 # accerlation/ deceleration

STEP_DISTANCE = 100 # Increments taken between limitswitch checks
ORIGIN_CLEARANCE = 300 # distance to clear first target from vision

MS_RESOLUTION = 16 # Microstep resolution

# Specification constants
PHASE_1_STOP_TIME = 7.5

# GPIO Pins
LIMIT_SWITCH_PIN = 27 # NO Terminal

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

# Initialize motor controller and target detector
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
    motor_controller.set_speed(MAX_SPEED, DELTA_V)

    limit_switch_pressed = False

    # Move until limit switch is pressed or safe distance is reached
    while not limit_switch_pressed:
        if GPIO.input(LIMIT_SWITCH_PIN) == GPIO.LOW:
            limit_switch_pressed = True
            break

        if measure_distance() < SAFE_DISTANCE:
            motor_controller.set_speed(MIN_SPEED, -DELTA_V)
        
        motor_controller.step(STEP_DISTANCE * MS_RESOLUTION, 1)

    motor_controller.set_speed(MAX_SPEED, DELTA_V)

    while motor_controller.get_step_count() > 0:
        if motor_controller.get_step_count() <= SAFE_DISTANCE * MS_RESOLUTION:
            motor_controller.set_speed(MIN_SPEED, -DELTA_V)

        motor_controller.step(STEP_DISTANCE * MS_RESOLUTION, -1)

    # Align with target
    target_detector.start_detection # Start target detection
    target_detector.detect_targets()
    
    # Keep moving until y-displacement is constantly 0
    consecutive_zero_count = 0
    required_consecutive_zeros = 5

    while consecutive_zero_count < required_consecutive_zeros:
        y_displacement = target_detector.get_y_displacement()
        if y_displacement == 0:
            consecutive_zero_count += 1
            # Pause briefly to allow for subsequent displacement measurement
            time.sleep(0.1) 
        else:
            consecutive_zero_count = 0
            direction = -1 if y_displacement > 0 else 1
            motor_controller.step(10 * MS_RESOLUTION, direction)

    # target_detector.stop_detection()  # Stop target detection

    time.sleep(PHASE_1_STOP_TIME)

    motor_controller.step(ORIGIN_CLEARANCE * MS_RESOLUTION, 1)

    # Move forward and look for next target
    # motor_controller.set_speed(MAX_SPEED, DELTA_V)
    target_detector.start_detection()
    target_detector.detect_targets()  # Restart target detection for next target
    while True:
        motor_controller.step(STEP_DISTANCE * MS_RESOLUTION, 1)
        if abs(target_detector.get_y_displacement()) <= -180:
            break

    # Align with next target
    consecutive_zero_count = 0
            
    while consecutive_zero_count < required_consecutive_zeros:
        y_displacement = target_detector.get_y_displacement()
        if y_displacement == 0:
            consecutive_zero_count += 1
            # Pause briefly to allow for subsequent displacement measurement
            time.sleep(0.1) 
        else:
            consecutive_zero_count = 0
            direction = -1 if y_displacement > 0 else 1
            motor_controller.step(10 * MS_RESOLUTION, direction)

    target_detector.stop_detection() # Stop target detector
    motor_controller.stop() # Stop once aligned
    cleanup_gpio()

if __name__ == "__main__":
    main()
