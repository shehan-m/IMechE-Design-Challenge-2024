from time import sleep
from target_detector import TargetDetector
import pigpio

# Constants for navigation (Distances are in steps)
SAFE_DISTANCE = 200 # Safe distance to start deceleration to low speed
DATUM_OFFSET = 100 # Offset of datum from camera centre

ORIGIN_CLEARANCE = 300 # distance to clear first target from vision

# Specification constants
PHASE_1_STOP_TIME = 7.5

# GPIO Pins
STEP_PIN = 21
DIR_PIN = 20

SWITCH_PIN = 16 # NO Terminal

TRIG_PIN = 17
ECHO_PIN = 18

def generate_ramp(ramp):
    """Generate ramp wave forms.
    ramp:  List of [Frequency, Steps]
    """
    pi.wave_clear()     # clear existing waves
    length = len(ramp)  # number of ramp levels
    wid = [-1] * length

    # Generate a wave per ramp level
    for i in range(length):
        frequency = ramp[i][0]
        micros = int(500000 / frequency)
        wf = []
        wf.append(pigpio.pulse(1 << STEP, 0, micros))  # pulse on
        wf.append(pigpio.pulse(0, 1 << STEP, micros))  # pulse off
        pi.wave_add_generic(wf)
        wid[i] = pi.wave_create()

    # Generate a chain of waves
    chain = []
    for i in range(length):
        steps = ramp[i][1]
        x = steps & 255
        y = steps >> 8
        chain += [255, 0, wid[i], 255, 1, x, y]

    pi.wave_chain(chain)  # Transmit chain.

# Initialise motor controller and target detector
target_detector = TargetDetector(camera_index=0, desired_fps=30, desired_width=640, desired_height=480, debug_mode=False)

# Connect to pigiod daemon
try:
    pi = pigpio.pi()
except:
    print("Could not connect to pigpio daemon")

# Set up stepper pins
pi.set_mode(DIR_PIN, pigpio.OUTPUT)
pi.set_mode(STEP_PIN, pigpio.OUTPUT)

# Set up input switch
pi.set_mode(SWITCH_PIN, pigpio.INPUT)
pi.set_pull_down(SWITCH_PIN, pigpio.PUD_UP)

# Set up ultrasonic sensor pins
pi.set_mode(TRIG_PIN, pigpio.OUTPUT)
pi.set_mode(ECHO_PIN, pigpio.INPUT)

# main
try:
    # Move forward until in contact with wall
    while pi.read(SWITCH_PIN):
        pi.write(DIR_PIN, 1)
        sleep(.1)

    # TODO: Stop while target detector starts up and then proceed to move to target

    # Move back to target and use detector
    target_detector.start_detection()
    target_detector.detect_targets()

    consec_zero_count = 0
    req_consec_zeros = 5

    while consec_zero_count < req_consec_zeros:
        y_offset = target_detector.get_y_displacement()
        if y_offset == 0:
            consec_zero_count += 1
            sleep(0.1) # Pause briefly to allow for subsequent displacment measurement
        else:
            consec_zero_count = 0
            direction = -1 if y_offset > 0 else 1 

    # TODO: Stop for PHASE_1_STOP_TIME once aligned
    # TODO: move forward first target clearance distance
    # TODO: Move forward 

except KeyboardInterrupt:
    print("\nCtrl-C Pressed.  Stopping PIGPIO and exiting...")
finally:
    pi.set_PWM_dutycycle(STEP_PIN, 0) # PWM off
    pi.stop()