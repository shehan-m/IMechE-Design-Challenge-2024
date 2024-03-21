import RPi.GPIO as GPIO
from Firmware.old.stepper_motorV2 import StepperMotorController
import time

# Constants
MAX_SPEED = 0.00001
MIN_SPEED = 0.0001
DELTA_V = 0.0001  # Acceleration/deceleration

MS_RESOLUTION = 16  # Microstep resolution

# GPIO Pins
LIMIT_SWITCH_PIN = 27  # NO Terminal

STEP_PIN = 22
DIR_PIN = 23
MS1_PIN = 24
MS2_PIN = 25
MS3_PIN = 12

# Setup GPIO mode and pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(LIMIT_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize motor controller
motor_controller = StepperMotorController(step_pin=STEP_PIN, dir_pin=DIR_PIN, ms1_pin=MS1_PIN, ms2_pin=MS2_PIN, ms3_pin=MS3_PIN)
motor_controller.set_microstepping(MS_RESOLUTION)

def cleanup_gpio():
    motor_controller.cleanup()
    GPIO.cleanup()

# Main logic
motor_controller.set_speed(MAX_SPEED, DELTA_V)

steps_forward = 0  # Track the number of steps taken forward

# Move forward until limit switch is pressed
limit_switch_pressed = False
while not limit_switch_pressed:
    if GPIO.input(LIMIT_SWITCH_PIN) == GPIO.LOW:
        limit_switch_pressed = True
        break

    motor_controller.step(100 * MS_RESOLUTION, 1)  # Move forward
    steps_forward += 100 * MS_RESOLUTION  # Accumulate steps moved forward

# Once the limit switch is pressed, move backward by the same number of steps
motor_controller.set_speed(MAX_SPEED, DELTA_V)  # Reset speed if necessary
motor_controller.step(steps_forward, -1)  # Move backward

cleanup_gpio()  # Clean up GPIO pins and motor controller
