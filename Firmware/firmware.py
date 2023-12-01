from target_detector import TargetDetector
from stepper_motor import StepperMotorController
import RPi.GPIO as GPIO

def limit_switch_event():
    pass

td = TargetDetector()
controller = StepperMotorController()

while True:
    controller.move(1000)