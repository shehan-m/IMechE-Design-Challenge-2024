from time import sleep, time
from target_detector import TargetDetector
import pigpio

# Constants for navigation
CM_TO_STEPS = 10  # Conversion factor from cm to steps
Y_OFFSET_TO_STEPS = 10  # Conversion factor from y-offset to steps
SAFE_DISTANCE = 200  # Safe distance in steps for starting deceleration
DATUM_OFFSET = 100  # Offset of datum from camera center in steps
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

def align(req_consec_zero_count):
    """
    Aligns the mechanism by adjusting its position based on y-offset until the required number of consecutive
    zero-displacements is achieved.

    Args:
        req_consec_zero_count (int): The number of consecutive zero-displacements required for alignment.
    """
    consec_zero_count = 0  # Counter for consecutive zero-displacements

    while consec_zero_count < req_consec_zero_count:
        y_offset = target_detector.get_y_displacement()
        print(f"Current Y offset: {y_offset}")

        if abs(y_offset) <= 1:
            consec_zero_count += 1
            print(f"Alignment count: {consec_zero_count}/{req_consec_zero_count}")
        else:
            consec_zero_count = 0  # Reset counter if displacement is outside threshold
            direction = 1 if y_offset > 0 else 0  # Determine direction based on displacement
            move_motor(direction, abs(y_offset) * Y_OFFSET_TO_STEPS)  # Adjust alignment
            print("Adjusting alignment...")

        sleep(0.1)  # Short delay for displacement updates

# Initialization and setup code
print("Initializing target detector.")
target_detector = TargetDetector(camera_index=0, desired_width=640, desired_height=480, debug_mode=True)

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

align(5)