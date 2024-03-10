import RPi.GPIO as GPIO
import time

# Set up GPIO pins
limit_switch_pin = 23  # Change this to the GPIO pin you're using for the limit switch
GPIO.setmode(GPIO.BCM)
GPIO.setup(limit_switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Configure for normally open switch

try:
    while True:
        if GPIO.input(limit_switch_pin) == GPIO.HIGH:
            print("Limit switch is pressed")
        else:
            print("Limit switch is not pressed")
        time.sleep(0.5)  # Simple debounce - adjust as necessary

finally:
    GPIO.cleanup()
