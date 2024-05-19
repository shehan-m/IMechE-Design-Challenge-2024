import threading
from time import sleep, time
import math
import pigpio

# GPIO Pins configuration
STEP_PIN = 21  # Stepper motor step pin
DIR_PIN = 20  # Stepper motor direction pin
SWITCH_PIN = 16  # Normally Open (NO) Terminal of the switch
TRIG_PIN = 17  # Ultrasonic sensor trigger pin
ECHO_PIN = 18  # Ultrasonic sensor echo pin

# Constants for navigation
CM_TO_STEPS = 10  # Conversion factor from cm to steps
Y_OFFSET_TO_STEPS = 10  # Conversion factor from y-offset to steps
SAFE_DISTANCE = 200  # Safe distance in steps for starting deceleration
DATUM_OFFSET = 100  # Offset of datum from camera center in steps
ORIGIN_CLEARANCE = 1000  # Steps to clear first target from vision (actual 185 mm)
REQ_CONSEC = 5  # Required consecutive zero-displacements for alignment

# Specification constants
PHASE_1_STOP_TIME = 7.5  # Stop time in phase 1 in seconds

def move_motor(direction, total_steps, max_speed=500, accel_steps=100):
    """
    Moves the motor with constant acceleration and deceleration.

    Args:
        direction (int): Direction to move (1 for forward, 0 for backward).
        total_steps (int): Total number of steps to move.
        max_speed (int): Maximum speed in steps per second.
        accel_steps (int): Steps over which to accelerate and decelerate.
    """
    pi.write(DIR_PIN, direction)
    
    # Ensure acceleration/deceleration phases don't exceed half the total steps
    accel_steps = min(accel_steps, total_steps // 2)
    decel_start = total_steps - accel_steps
    speed_increment = max_speed / accel_steps  # Calculate speed increment for each step
    
    current_speed = 0

    for step in range(total_steps):
        if step < accel_steps:  # Acceleration phase
            current_speed += speed_increment
        elif step >= decel_start:  # Deceleration phase
            current_speed -= speed_increment

        # Ensure speed does not exceed max_speed during acceleration or drop below 0 during deceleration
        current_speed = max(1, min(current_speed, max_speed))
        
        # Calculate delay for current speed
        delay = 1 / (2 * current_speed)
        
        # Move the motor one step at the current speed
        pi.write(STEP_PIN, 1)
        sleep(delay)
        pi.write(STEP_PIN, 0)
        sleep(delay)

def calibrate_cm_to_steps():
    """
    Calibrates the conversion factor from centimeters to steps.
    """
    print("Place a known distance marker from the sensor.")
    
    while True:
        steps = int(input("Enter the distance in steps: "))
        dir = int(input("Enter direction: "))
        speed = int(input("Enter speed: "))
        acel_steps = int(input("Enter acceleration steps: "))
        print(f'Moving motor {steps} steps...')
        move_motor(dir, steps, speed, acel_steps)
        input("Press Enter to retry...")

print("Connecting to pigpio daemon.")
try:
    pi = pigpio.pi()  # Initialize pigpio
except:
    print("Could not connect to pigpio daemon")

# Configure GPIO modes and initial settings
pi.set_mode(DIR_PIN, pigpio.OUTPUT)
pi.set_mode(STEP_PIN, pigpio.OUTPUT)

pi.set_mode(SWITCH_PIN, pigpio.INPUT)
pi.set_pull_up_down(SWITCH_PIN, pigpio.PUD_UP)

pi.set_mode(TRIG_PIN, pigpio.OUTPUT)
pi.set_mode(ECHO_PIN, pigpio.INPUT)

calibrate_cm_to_steps()
