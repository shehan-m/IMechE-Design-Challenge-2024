from machine import Pin
import utime

class Stepper:
    def __init__(self, step_pin, dir_pin, ms1_pin, ms2_pin, ms3_pin):
        self.step_pin = Pin(step_pin, Pin.OUT)
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.position = 0

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
            Pin(pin, Pin.OUT).value(value)
 
    def set_speed(self, speed, accelration):
        self.delay = 1 / abs(speed)  # delay in seconds
 
    def set_direction(self, direction):
        self.dir_pin.value(direction)
 
    def move_to(self, position):
        self.set_direction(1 if position > self.position else 0)
        while self.position != position:
            self.step_pin.value(1)
            utime.sleep(self.delay)
            self.step_pin.value(0)
            self.position += 1 if position > self.position else -1

    def move(self):
        pass
