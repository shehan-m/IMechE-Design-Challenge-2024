import RPi.GPIO as GPIO
import time

class StepperMotorController:
    def __init__(self, step_pin=, direction_pin, enable_pin=None):
        self.step_pin = step_pin
        self.direction_pin = direction_pin
        self.enable_pin = enable_pin

        self.current_position = 0
        self.target_position = 0
        self.speed = 0.0
        self.max_speed = 1000.0  # Set desired maximum speed
        self.acceleration = 1000.0  # Set desired acceleration

        self.setup_pins()

    def setup_pins(self):
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.output(self.step_pin, GPIO.LOW)

        GPIO.setup(self.direction_pin, GPIO.OUT)
        GPIO.output(self.direction_pin, GPIO.LOW)

        if self.enable_pin is not None:
            GPIO.setup(self.enable_pin, GPIO.OUT)
            GPIO.output(self.enable_pin, GPIO.LOW)

    def set_enable_state(self, state):
        if self.enable_pin is not None:
            GPIO.output(self.enable_pin, state)

    def set_speed(self, speed):
        self.speed = speed

    def set_max_speed(self, max_speed):
        self.max_speed = max_speed

    def set_acceleration(self, acceleration):
        self.acceleration = acceleration

    def move_to(self, absolute):
        self.target_position = absolute

    def move(self, relative):
        self.target_position += relative

    def run(self):
        direction = GPIO.HIGH if self.target_position > self.current_position else GPIO.LOW
        distance_to_go = abs(self.target_position - self.current_position)

        time_to_stop = self.speed / self.acceleration
        max_speed = min(self.max_speed, (2 * distance_to_go * self.acceleration) ** 0.5)

        if self.speed == 0.0:
            self.set_speed(min(max_speed, self.acceleration * time_to_stop))
        elif self.speed > max_speed:
            self.set_speed(max_speed)

        if distance_to_go > 0:
            GPIO.output(self.direction_pin, direction)
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(0.000001)
            GPIO.output(self.step_pin, GPIO.LOW)

            self.current_position += 1 if direction == GPIO.HIGH else -1
            distance_to_go -= 1
            return True
        else:
            self.set_speed(0.0)
            return False

    def run_speed(self):
        return self.run()

    def stop(self):
        self.set_speed(0.0)

    def is_running(self):
        return self.speed != 0.0

    def cleanup(self):
        GPIO.cleanup()