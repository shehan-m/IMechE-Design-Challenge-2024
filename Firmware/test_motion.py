import RPi.GPIO as GPIO
import time

# Use Broadcom SOC Pin numbers
GPIO.setmode(GPIO.BCM)

# Pins connected to the A4988 driver
DIR_PIN = 20  # Direction GPIO Pin
STEP_PIN = 21  # Step GPIO Pin
# Limit switch pin
LIMIT_SWITCH_PIN = 16  # GPIO Pin connected to the limit switch

# Set pin states
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)
GPIO.setup(LIMIT_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Enable internal pull-up resistor

# Function to rotate the motor
def rotate_motor(direction, delay=0.001):
    GPIO.output(DIR_PIN, direction)
    while True:
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(delay)
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(delay)
        # Check if the limit switch is pressed
        if GPIO.input(LIMIT_SWITCH_PIN) == GPIO.LOW:
            break

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
    # Move forward until limit switch is pressed
    print("Moving forward until limit switch is pressed.")
    rotate_motor(GPIO.HIGH)
    
    # Once limit switch is pressed, return to the original position
    print("Limit switch activated. Returning to original position.")
    return_to_origin(steps_forward)

except KeyboardInterrupt:
    print("Program terminated by the user")

finally:
    GPIO.cleanup()  # Clean up GPIO to reset pin modes
