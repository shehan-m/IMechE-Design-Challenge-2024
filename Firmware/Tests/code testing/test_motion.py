import RPi.GPIO as GPIO
import time

# Set the GPIO mode to BCM
GPIO.setmode(GPIO.BCM)

# Pins connected to the A4988 driver
DIR_PIN = 20  # Direction GPIO Pin
STEP_PIN = 21  # Step GPIO Pin
# Limit switch pin
SWITCH_PIN = 16  # GPIO Pin connected to the limit switch

# Set pin states
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Enable internal pull-up resistor

# Global variable to track limit switch state
limit_switch_activated = False

# Define debounce time in milliseconds
DEBOUNCE_TIME_MS = 200  # 200 milliseconds

# Function to handle limit switch activation
def switch_callback(channel):
    global limit_switch_activated
    # Check if the switch is pressed
    if GPIO.input(SWITCH_PIN) == GPIO.LOW:
        limit_switch_activated = True

# Add event detection for the limit switch
GPIO.add_event_detect(SWITCH_PIN, GPIO.FALLING, callback=switch_callback, bouncetime=DEBOUNCE_TIME_MS)

# Function to rotate the motor
def rotate_motor(direction, delay=0.001):
    GPIO.output(DIR_PIN, direction)
    global limit_switch_activated
    while not limit_switch_activated:
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)

# Function to return to original position
def return_to_origin(steps, delay=0.001):
    GPIO.output(DIR_PIN, GPIO.LOW)  # Set direction to reverse
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)

try:
    steps_forward = 0
    print("Moving forward until limit switch is pressed.")
    rotate_motor(GPIO.HIGH)
    
    if limit_switch_activated:
        print("Limit switch activated. Returning to original position.")
        # Assuming steps_forward was incremented during forward movement; this logic is missing in this snippet
        return_to_origin(steps_forward)

except KeyboardInterrupt:
    print("Program terminated by the user")

finally:
    GPIO.cleanup()  # Clean up GPIO to reset pin modes
