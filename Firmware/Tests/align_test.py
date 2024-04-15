import threading
from time import sleep, time
from target_detector import TargetDetector
import pigpio
import math

# Constants for navigation
MM_TO_STEPS = 10  # Conversion factor from cm to steps
X_OFFSET_TO_STEPS = 10  # Conversion factor from y-offset to steps
DATUM_OFFSET = 300 # Offset of datum from camera center in mm
ORIGIN_CLEARANCE = 1000  # Steps to clear first target from vision (actual 185 mm)

REQ_CONSEC = 5  # Required consecutive zero-displacements for alignment

# Specification constants
PHASE_1_STOP_TIME = 7.5  # Stop time in phase 1 in seconds

# GPIO Pins configuration
STEP_PIN = 21  # Stepper motor step pin
DIR_PIN = 20  # Stepper motor direction pin
SWITCH_PIN = 16  # Normally Open (NO) Terminal of the switch
TRIG_PIN = 17  # Ultrasonic sensor trigger pin
ECHO_PIN = 18  # Ultrasonic sensor echo pin

def move_motor(direction, total_steps, max_speed=500, accel_steps=100):
    """
    Moves the motor with an S-curve acceleration and deceleration profile.

    Args:
        direction (int): Direction to move (1 for forward, 0 for backward).
        total_steps (int): Total number of steps to move.
        max_speed (int): Maximum speed in steps per second.
        accel_steps (int): Steps over which to accelerate and decelerate.
    """
    pi.write(DIR_PIN, direction)
    
    # Prepare S-curve acceleration parameters
    accel_steps = min(accel_steps, total_steps // 2)
    decel_start = total_steps - accel_steps
    current_speed = 0

    for step in range(total_steps):
        phase_progress = step / accel_steps if step < accel_steps else (total_steps - step) / accel_steps

        # Adjust acceleration based on an S-curve profile
        accel_factor = (1 - math.cos(math.pi * phase_progress)) / 2  # Generates an S-curve shape factor

        if step < accel_steps:  # Acceleration phase
            current_speed = max_speed * accel_factor
        elif step >= decel_start:  # Deceleration phase
            current_speed = max_speed * accel_factor
        else:
            current_speed = max_speed  # Constant speed phase

        delay = 1 / (2 * max(current_speed, 1))  # Ensure delay is never zero

        # Move the motor one step
        pi.write(STEP_PIN, 1)
        sleep(delay)
        pi.write(STEP_PIN, 0)
        sleep(delay)

def align():
    consecutive_aligned = 0  # Counter for how many times the target is consecutively aligned
    
    while consecutive_aligned <= REQ_CONSEC:
        x_displacement = target_detector.get_x_displacement()
        
        # Check if target is detected
        if x_displacement is not None:
            # Convert x_displacement to steps for the motor
            steps_needed = int(x_displacement * X_OFFSET_TO_STEPS)
            
            # If steps needed is too small, consider it aligned
            if abs(steps_needed) == 0:
                consecutive_aligned += 1
            else:
                consecutive_aligned = 0  # Reset the counter if it's not aligned

            if steps_needed != 0:
                direction = 1 if x_displacement > 0 else 0  # Determine direction
                move_motor(direction, abs(steps_needed))
                print(f"Moved {abs(steps_needed)} steps {'right' if direction else 'left'} to align.")
        else:
            consecutive_aligned = 0  # Reset if no target is detected
        
        sleep(0.1)  # Small delay to prevent high CPU usage

    print("Camera aligned with target centre.")

    move_motor(0, DATUM_OFFSET * MM_TO_STEPS)
    print("Aligned datum with target")

    print("Waiting")
    sleep(PHASE_1_STOP_TIME)

# Initialization and setup code
print("Initializing target detector.")
target_detector = TargetDetector(camera_index=-1, desired_width=640, desired_height=480, debug_mode=True)

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

# Start the target detector and main code threads
detector_thread = threading.Thread(target=target_detector.detect_targets)
detector_thread.start()

main_thread = threading.Thread(target=align)
main_thread.start()

main_thread.join()
detector_thread.join()