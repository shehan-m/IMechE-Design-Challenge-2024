import threading
from time import sleep, time
from Firmware.target_detector import TargetDetector
import pigpio

STEP_PIN = 21  # Stepper motor step pin
DIR_PIN = 20  # Stepper motor direction pin

def move_motor(direction, steps, speed=500):
    """
    Moves the motor in the specified direction and steps at the given speed.

    Args:
        direction (int): The direction to move the motor (1 for forward, 0 for backward).
        steps (int): The number of steps to move the motor.
        speed (int, optional): The speed at which to move the motor. Defaults to 500 steps per second.
    """
    pi.write(DIR_PIN, direction)
    for _ in range(steps):
        pi.write(STEP_PIN, 1)
        sleep(1 / (2 * speed))
        pi.write(STEP_PIN, 0)
        sleep(1 / (2 * speed))

def move_motor_pwm(direction, steps, speed=500):
    """
    Moves the motor a certain number of steps using PWM at the specified speed and direction.

    Args:
        direction (int): The direction to move the motor (1 for forward, 0 for backward).
        steps (int): The number of steps to move the motor.
        speed (int): The speed in Hz at which the motor should move.
    """
    pi.write(DIR_PIN, direction)  # Set direction

    duration = steps / (speed * 1)  # Calculate the duration for the desired steps
    pi.set_PWM_frequency(STEP_PIN, speed)  # Set the PWM frequency
    pi.set_PWM_dutycycle(STEP_PIN, 128)  # Set to 50% duty cycle for movement

    sleep(duration)  # Wait for movement to complete
    
    pi.set_PWM_dutycycle(STEP_PIN, 0)  # Stop the motor