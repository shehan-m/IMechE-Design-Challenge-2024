from time import sleep, time
from target_detector import TargetDetector
import pigpio

# Constants for navigation (Distances are in steps)
SAFE_DISTANCE = 200 # Safe distance to start deceleration to low speed
DATUM_OFFSET = 100 # Offset of datum from camera centre

ORIGIN_CLEARANCE = 1000 # distance to clear first target from vision

# Specification constants
PHASE_1_STOP_TIME = 7.5

# GPIO Pins
STEP_PIN = 21
DIR_PIN = 20

SWITCH_PIN = 16 # NO Terminal

TRIG_PIN = 17
ECHO_PIN = 18

# Function to move motor
def move_motor(direction, steps, speed):
    pi.write(DIR_PIN, direction)
    for _ in range(steps):
        pi.write(STEP_PIN, 1)
        sleep(1 / (2 * frequency))
        pi.write(STEP_PIN, 0)
        sleep(1 / (2 * frequency))

def measure_distance():
    # Send a 10us pulse to start the measurement
    pi.gpio_trigger(TRIG_PIN, 10, 1)

    # Wait for the echo start
    start_time = time()
    while pi.read(ECHO_PIN) == 0:
        start_time = time()

    # Wait for the echo end
    end_time = time()
    while pi.read(ECHO_PIN) == 1:
        end_time = time()

    # Calculate the distance
    elapsed_time = end_time - start_time
    distance = (elapsed_time * 34300) / 2  # Speed of sound is ~34300 cm/s at sea level

    return distance

# Initialise motor controller and target detector
target_detector = TargetDetector(camera_index=1, desired_fps=30, desired_width=640, desired_height=480, debug_mode=False)

# Connect to pigiod daemon
try:
    pi = pigpio.pi()
except:
    print("Could not connect to pigpio daemon")

# Set up stepper pins
pi.set_mode(DIR_PIN, pigpio.OUTPUT)
pi.set_mode(STEP_PIN, pigpio.OUTPUT)

# Frequency and speed settings
frequency = 500  # steps per second
pi.set_PWM_frequency(STEP_PIN, frequency)

# Set up input switch
pi.set_mode(SWITCH_PIN, pigpio.INPUT)
pi.set_pull_up_down(SWITCH_PIN, pigpio.PUD_UP)

# Set up ultrasonic sensor pins
pi.set_mode(TRIG_PIN, pigpio.OUTPUT)
pi.set_mode(ECHO_PIN, pigpio.INPUT)

# Start target detector
target_detector.start_detection()
target_detector.detect_targets()

# main
try:
   steps = 0
   # Move forward until switch is pressed
   while pi.read(SWITCH_PIN) == 1:  # Assuming switch is normally high and goes low when pressed
    move_motor(1, 1)  # Move one step forward
    steps += 1
    sleep(0.01)  # Short delay to debounce and slow down the step rate if necessary

    # Once switch is pressed, reverse direction
    sleep(0.5)  # Short delay to ensure switch is fully pressed
    move_motor(0, steps)  # Move back the same number of steps

    consec_zero_count = 0  # Counter for consecutive zero-displacements
    required_consec_zeros = 5  # Required number of consecutive zero-displacements for alignment
    
    while consec_zero_count < required_consec_zeros:
        y_displacement = target_detector.get_y_displacement()
        print(f"Current Y displacement: {y_displacement}")

        if abs(y_displacement) <= 1 :  # Adjust threshold as needed
            consec_zero_count += 1
            print(f"Alignment count: {consec_zero_count}/{required_consec_zeros}")
        else:
            consec_zero_count = 0  # Reset counter if displacement is outside the threshold

            # Determine direction based on displacement
            direction = 1 if y_displacement > 0 else 0
            # Move motor in small steps for finer control
            move_motor(direction, 1)

        sleep(0.01)  # Short delay to allow for displacement updates

    # Wait for PHASE_1_STOP_TIME
    sleep(PHASE_1_STOP_TIME)

    # Move Forward clearance distance
    move_motor(1, ORIGIN_CLEARANCE)

    # Move forward until the target is detected
    target_detected = False
    while not target_detected:
        y_displacement = target_detector.get_y_displacement()
        if abs(y_displacement) < 200:  # Adjust condition based on how target detection is defined
            target_detected = True
            print("Target detected. Starting alignment process.")
        else:
            move_motor(1, 1)  # Move forward in search of the target
        time.sleep(0.01)

    # Alignment process
    consec_zero_count = 0
    required_consec_zeros = 5
    while consec_zero_count < required_consec_zeros:
        y_displacement = target_detector.get_y_displacement()
        
        if abs(y_displacement) <= 10:  # Alignment threshold
            consec_zero_count += 1
            print(f"Alignment count: {consec_zero_count}/{required_consec_zeros}")
        else:
            consec_zero_count = 0  # Reset counter if displacement is significant
            direction = 1 if y_displacement > 0 else 0
            move_motor(direction, 1)

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nCtrl-C Pressed.  Stopping PIGPIO and exiting...")
finally:
    pi.set_PWM_dutycycle(STEP_PIN, 0) # PWM off
    pi.stop()
