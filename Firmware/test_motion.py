import RPi.GPIO as GPIO
import time
from stepper_motor_controller import StepperMotorController  # Make sure this matches your file name

# Initialize the stepper motor controller
step_pin = 20  # Example pin numbers, change according to your setup
dir_pin = 21
stepper = StepperMotorController(step_pin, dir_pin)

# Set up GPIO pins for the limit switch
limit_switch_pin = 23  # Change this to the GPIO pin you're using for the limit switch
GPIO.setmode(GPIO.BCM)
GPIO.setup(limit_switch_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)  # Assuming a normally open switch

try:
    stepper.set_speed(0.01)  # Set a suitable speed for your motor

    # Move forward until the limit switch is pressed (reads HIGH)
    while GPIO.input(limit_switch_pin) == GPIO.LOW:
        stepper.step(1, 1)  # Move one step forward
        time.sleep(0.01)  # Adjust this delay to control step speed, if needed

    total_steps = stepper.get_step_count()  # Get the number of steps taken

    # Return to the original position
    stepper.step(total_steps, -1)  # Move back the same number of steps

finally:
    stepper.cleanup()
    GPIO.cleanup()
