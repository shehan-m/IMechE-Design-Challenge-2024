import RPi.GPIO as GPIO
from time import sleep

# Stepper motor pins
DIR = 20   # Direction GPIO Pin
STEP = 21  # Step GPIO Pin
CW = 1     # Clockwise Rotation
CCW = 0    # Counterclockwise Rotation

# Limit switch pin
SWITCH_PIN = 16

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR, GPIO.OUT)
GPIO.setup(STEP, GPIO.OUT)
GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Motor parameters
delay = .0208

def motor_step(direction, steps, delay):
    """
    Function to move the motor a given number of steps in a specified direction
    """
    GPIO.output(DIR, direction)
    for _ in range(steps):
        GPIO.output(STEP, GPIO.HIGH)
        sleep(delay)
        GPIO.output(STEP, GPIO.LOW)
        sleep(delay)

try:
    # Move forward until the limit switch is pressed
    while GPIO.input(SWITCH_PIN):  # While the switch is not pressed
        motor_step(CW, 1, delay)  # Move one step at a time

    # Once limit switch is pressed, wait a bit and return to original position
    sleep(0.5)  # Short delay before moving back
    motor_step(CCW, 200, delay)  # Move back 200 steps or adjust as needed

except KeyboardInterrupt:
    # Clean up GPIO on exit
    GPIO.cleanup()
