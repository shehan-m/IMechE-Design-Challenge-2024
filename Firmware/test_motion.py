import RPi.GPIO as GPIO
import time

# Use Broadcom SOC Pin numbers
GPIO.setmode(GPIO.BCM)

# Pins connected to the A4988 driver
DIR_PIN = 20  # Direction GPIO Pin
STEP_PIN = 21  # Step GPIO Pin
# Set pin states
GPIO.setup(DIR_PIN, GPIO.OUT)
GPIO.setup(STEP_PIN, GPIO.OUT)

# Function to control the motor
def rotate_motor(steps, direction):
    GPIO.output(DIR_PIN, direction)  # Set the direction
    for _ in range(steps):
        GPIO.output(STEP_PIN, GPIO.HIGH)
        time.sleep(0.001)  # Control speed of the steps
        GPIO.output(STEP_PIN, GPIO.LOW)
        time.sleep(0.001)

try:
    while True:
        direction = input("Enter direction (CW for clockwise, CCW for counterclockwise): ").upper()
        if direction not in ["CW", "CCW"]:
            print("Invalid direction. Please enter 'CW' or 'CCW'.")
            continue
        steps = int(input("Enter the number of steps: "))
        rotate_motor(steps, GPIO.HIGH if direction == "CW" else GPIO.LOW)

except KeyboardInterrupt:
    print("Program terminated by the user")

finally:
    GPIO.cleanup()  # Clean up GPIO to reset pin modes