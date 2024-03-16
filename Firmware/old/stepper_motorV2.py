from time import sleep
import pigpio

class StepperController:
    def __init__(self, dir_pin=20, step_pin=21):
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.direction = 1 # 1 forward, 0 backward

        # Connect to pigpiod daemon
        pi = pigpio.pi()

        # Set up pins as an output
        pi.set_mode(dir_pin, pigpio.OUTPUT)
        pi.set_mode(step_pin, pigpio.OUTPUT)
    
    def set_pwm(self, duty_cycle, frequency):
        self.pi.set_PWM_dutycycle(self.step_pin, duty_cycle)
        self.pi.set_PWM_frequency(self.step_pin, frequency)

    def change_direction(self):
        self.direction = not self.direction
        self.pi.write(self.dir_pin, self.direction)

    def run(self, duration=10):
        start_time = sleep.time()
        try:
            while sleep.time() - start_time < duration:
                self.pi.write(self.dir_pin, self.direction)
                sleep(0.1)
        except KeyboardInterrupt:
            print("\nCtrl-C pressed. Stopping motor.")
        finally:
            self.stop()

    def stop(self):
        self.pi.set_PWM_dutycycle(self.step_pin, 0)  # Turn PWM off
        self.pi.stop()  # Disconnect from pigpiod
