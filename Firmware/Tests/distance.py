from gpiozero import Button, DistanceSensor
import time

# GPIO PINS
SWITCH_PIN = 16
START_PIN = 23
RESET_PIN = 24

TRIG_PIN = 4
ECHO_PIN = 17

# Initialize the distance sensor and buttons
ultrasonic = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN)
limit_switch = Button(SWITCH_PIN)
start_button = Button(START_PIN)
reset_button = Button(RESET_PIN)

try:
    while True:
        # Measure distance
        distance = ultrasonic.distance * 100  # Convert from meters to centimeters
        print(f"Distance: {distance:.1f} cm")

        # Check if the limit switch is pressed
        if limit_switch.is_pressed:
            print("Limit switch is pressed.")

        # Check if the start button is pressed
        if start_button.is_pressed:
            print("Start button is pressed.")

        # Check if the reset button is pressed
        if reset_button.is_pressed:
            print("Reset button is pressed.")

        # Wait a little before the next read
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Program stopped manually.")
