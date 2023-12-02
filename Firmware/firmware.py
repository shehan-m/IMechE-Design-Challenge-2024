from target_detector import TargetDetector
from stepper_motor import StepperMotorController
import RPi.GPIO as GPIO

def limit_switch_event():
    pass

td = TargetDetector()
controller = StepperMotorController()

# Move to wall
while True:
    controller.move(1000)

# Move back from wall

# Use target alignment

# Move to next target