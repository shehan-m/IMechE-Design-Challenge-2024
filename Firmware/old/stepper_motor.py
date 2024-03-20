import time
import logging
import math
import RPi.GPIO as GPIO

class StepperMotorController:
    def __init__(self, step_pin, dir_pin, ms1_pin, ms2_pin, ms3_pin):
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.ms_pins = [ms1_pin, ms2_pin, ms3_pin]
        self.current_speed = 0.01  # Default speed
        self.target_speed = self.current_speed
        self.acceleration = 0.0001  # Default acceleration
        self.moving = False
        self.step_count = 0  # Track the number of steps taken

        try:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.step_pin, GPIO.OUT)
            GPIO.setup(self.dir_pin, GPIO.OUT)
            for pin in self.ms_pins:
                GPIO.setup(pin, GPIO.OUT)
            logging.info("Stepper motor controller initialized")
        except Exception as e:
            logging.error("Error initializing stepper motor controller: %s", e)
            raise

    def set_microstepping(self, resolution):
        if resolution not in [1, 2, 4, 8, 16]:
            raise ValueError("Invalid resolution. Must be one of [1, 2, 4, 8, 16]")
        settings = {
            1: (0, 0, 0),
            2: (1, 0, 0),
            4: (0, 1, 0),
            8: (1, 1, 0),
            16: (1, 1, 1)
        }
        for pin, value in zip(self.ms_pins, settings[resolution]):
            GPIO.output(pin, value)

    def set_speed(self, speed, acceleration=None):
        if not (0 < speed <= 1):
            raise ValueError("Speed must be between 0 and 1")
        self.target_speed = speed
        if acceleration is not None:
            if not (0 < acceleration <= 0.01):
                raise ValueError("Acceleration must be between 0 and 0.01")
            self.acceleration = acceleration

    def get_speed(self):
        return self.current_speed

    def accelerate(self):
        if self.current_speed < self.target_speed:
            self.current_speed = min(self.current_speed + self.acceleration, self.target_speed)
        elif self.current_speed > self.target_speed:
            self.current_speed = max(self.current_speed - self.acceleration, self.target_speed)

    def step(self, steps, dir):
        if not isinstance(steps, int) or steps <= 0:
            raise ValueError("Steps must be a positive integer")
        if dir not in [1, -1]:
            raise ValueError("Direction must be 1 (forward) or -1 (backward)")

        GPIO.output(self.dir_pin, GPIO.HIGH if dir > 0 else GPIO.LOW)
        self.moving = True
        try:
            for _ in range(steps):
                self.accelerate()
                GPIO.output(self.step_pin, GPIO.HIGH)
                time.sleep(abs(self.current_speed))
                GPIO.output(self.step_pin, GPIO.LOW)
                time.sleep(abs(self.current_speed))
                self.step_count += dir  # Increment or decrement step count based on direction
        finally:
            self.moving = False
    
    def get_step_count(self):
        return self.step_count

    def is_moving(self):
        return self.moving

    def stop(self):
        GPIO.output(self.step_pin, GPIO.LOW)
        self.moving = False

    def cleanup(self):
        GPIO.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
