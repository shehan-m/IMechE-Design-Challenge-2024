import threading
from time import sleep, time
from target_detector_v2 import TargetDetector
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

def move_motor(direction, steps, speed=500):
    """
    Moves the motor in the specified direction and steps at the given speed.

    Args:
        direction (int): The direction to move the motor (1 for forward, 0 for backward).
        steps (int): The number of steps to move the motor.
        speed (int, optional): The speed at which to move the motor. Defaults to 500 steps per second.
    """
    pi.write(DIR_PIN, direction)
    for _ in range(steps):
        pi.write(STEP_PIN, 1)
        sleep(1 / (2 * speed))
        pi.write(STEP_PIN, 0)
        sleep(1 / (2 * speed))

def move_motor_pwm(direction, steps, speed=500):
    """
    Moves the motor a certain number of steps using PWM at the specified speed and direction.

    Args:
        direction (int): The direction to move the motor (1 for forward, 0 for backward).
        steps (int): The number of steps to move the motor.
        speed (int): The speed in Hz at which the motor should move.
    """
    pi.write(DIR_PIN, direction)  # Set direction

    duration = steps / (speed * 1)  # Calculate the duration for the desired steps
    pi.set_PWM_frequency(STEP_PIN, speed)  # Set the PWM frequency
    pi.set_PWM_dutycycle(STEP_PIN, 128)  # Set to 50% duty cycle for movement

    sleep(duration)  # Wait for movement to complete
    
    pi.set_PWM_dutycycle(STEP_PIN, 0)  # Stop the motor

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

def measure_distance():
    """
    Measures the distance using an ultrasonic sensor.

    Returns:
        int: The measured distance in millimeters.
    """
    pi.gpio_trigger(TRIG_PIN, 10, 1)  # Trigger ultrasonic pulse

    start_time = time()
    while pi.read(ECHO_PIN) == 0:  # Wait for echo start
        start_time = time()

    end_time = time()
    while pi.read(ECHO_PIN) == 1:  # Wait for echo end
        end_time = time()

    elapsed_time = end_time - start_time  # Calculate time taken for the echo to return
    distance = (elapsed_time * 343000) / 2  # Calculate distance based on speed of sound
    
    return round(distance)

def main_code():
    """
    Main code execution function.
    """
    print("Main code thread started.")

    global frequency  # Use the global frequency variable

    start_time = time()
    distance_to_wall = measure_distance()  # Measure distance to the wall
    steps_to_wall = distance_to_wall * CM_TO_STEPS  # Convert distance to steps

    print(f"{distance_to_wall} mm to wall")
    print(f"{steps_to_wall} steps to wall")

    try:
        move_motor_pwm(1, steps_to_wall)  # Move towards the wall

        while pi.read(SWITCH_PIN):  # Wait until the switch is pressed
            sleep(0.01)

        print("Switch pressed. Stopping motor...")
        pi.set_PWM_dutycycle(STEP_PIN, 0)  # Stop the motor

        sleep(0.5)  # Short delay before moving back
        move_motor_pwm(0, steps_to_wall)  # Move back to the original position

        align(REQ_CONSEC)  # Alignment process

        print("Alignment completed. Waiting for phase 1 stop time.")
        sleep(PHASE_1_STOP_TIME)

        print("Moving forward clearance distance.")
        move_motor_pwm(1, ORIGIN_CLEARANCE)  # Move forward for clearance

        # Further operations omitted for brevity
    except KeyboardInterrupt:
        print("\nCtrl-C Pressed. Stopping PIGPIO and exiting...")
    finally:
        pi.set_PWM_dutycycle(STEP_PIN, 0)  # Ensure motor is stopped
        pi.stop()

# Initialization and setup code
print("Initializing target detector.")
target_detector = TargetDetector(camera_index=0, desired_width=640, desired_height=480, debug_mode=False)

print("Connecting to pigpio daemon.")
try:
    pi = pigpio.pi()  # Initialize pigpio
except:
    print("Could not connect to pigpio daemon")

# Configure GPIO modes and initial settings
pi.set_mode(DIR_PIN, pigpio.OUTPUT)
pi.set_mode(STEP_PIN, pigpio.OUTPUT)
frequency = 500  # Set a default frequency for stepper movement
pi.set_PWM_frequency(STEP_PIN, frequency)

pi.set_mode(SWITCH_PIN, pigpio.INPUT)
pi.set_pull_up_down(SWITCH_PIN, pigpio.PUD_UP)

pi.set_mode(TRIG_PIN, pigpio.OUTPUT)
pi.set_mode(ECHO_PIN, pigpio.INPUT)

# Start the target detector and main code threads
detector_thread = threading.Thread(target=target_detector.detect_targets)
detector_thread.start()

main_thread = threading.Thread(target=main_code)
main_thread.start()

main_thread.join()
detector_thread.join()
