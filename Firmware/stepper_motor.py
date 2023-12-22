import RPi.GPIO as GPIO
import time

class StepperMotorController:
    def __init__(self, step_pin, dir_pin, ms1_pin, ms2_pin, ms3_pin):
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.ms_pins = [ms1_pin, ms2_pin, ms3_pin]

        self.current_speed = 0.01  # Default speed, you can change this as needed

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        for pin in self.ms_pins:
            GPIO.setup(pin, GPIO.OUT)

    def set_microstepping(self, resolution):
        """
        Set microstepping resolution.
        resolution should be one of [1, 2, 4, 8, 16].
        """
        resolution_settings = {
            1: (0, 0, 0),
            2: (1, 0, 0),
            4: (0, 1, 0),
            8: (1, 1, 0),
            16: (1, 1, 1)
        }
        settings = resolution_settings.get(resolution, (0, 0, 0))
        for pin, value in zip(self.ms_pins, settings):
            GPIO.output(pin, value)

    def set_speed(self, speed):
        """
        Set the speed of the motor.
        speed - delay between steps in seconds, smaller is faster.
        """
        self.current_speed = speed

    def get_speed(self):
        """
        Get the current speed of the motor.
        Returns the delay between steps in seconds.
        """
        return self.current_speed

    def step(self, steps, dir):
        """
        Move the motor.
        steps - number of steps to move.
        dir - direction, either 1 (forward) or -1 (backward).
        """
        GPIO.output(self.dir_pin, GPIO.HIGH if dir > 0 else GPIO.LOW)
        for _ in range(steps):
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(self.get_speed())
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(self.get_speed())

    def stop(self):
        """
        Immediately stop the motor by disabling the step pin.
        """
        GPIO.output(self.step_pin, GPIO.LOW)

    def cleanup(self):
        """
        Clean up by resetting the GPIO pins.
        """
        GPIO.cleanup()
