import RPi.GPIO as GPIO
from stepper_motor import StepperMotorController
from target_detector import TargetDetector
import threading
import time

# Constants for navigation (in mm)
WALL_DISTANCE = 100 # Distance from the wall to start slowing down
SAFE_DISTANCE = 200 # Safe distance to start deceleration to min speed
DATUM_OFFSET = 100 # Offset of datum from camera centre

# GPIO Pins
LIMIT_SWITCH_PIN = 27
TRIG_PIN = 17
ECHO_PIN = 18
STEP_PIN = 22
DIR_PIN = 23
MS1_PIN = 24
MS2_PIN = 25
MS3_PIN = 12

# Setup GPIO mode and pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(LIMIT_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# Initialize your motor controller and target detector here
motor_controller = StepperMotorController(step_pin=STEP_PIN, dir_pin=DIR_PIN, ms1_pin=MS1_PIN, ms2_pin=MS2_PIN, ms3_pin=MS3_PIN)
motor_controller.set_microstepping(16)  # Set to 16 microsteps per step

target_detector = TargetDetector(camera_index=0, desired_fps=30, desired_width=640, desired_height=480)

def measure_distance():
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)

    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()

    while GPIO.input(ECHO_PIN) == 1:
        stop_time = time.time()

    time_elapsed = stop_time - start_time
    distance = (time_elapsed * 343000) / 2  # Speed of sound in air (343000 mm/s)
    
    return distance # distance in mm

def navigate_to_targets():
    # Speed parameters
    max_speed = 0.0005
    min_speed = 0.005
    current_speed = min_speed
    motor_controller.set_speed(current_speed)

    # Start with acceleration
    while current_speed > max_speed:
        current_speed -= 0.0001
        motor_controller.set_speed(current_speed)
        time.sleep(0.1)

    # Main navigation loop
    while True:
        # Assuming target_detector returns target coordinates
        targets = target_detector.detect_targets()
        for target in targets:
            # Here you need to implement logic to convert target coordinates to motor steps
            # steps = convert_target_to_steps(target)

            # Assuming motor_controller has a method to move a certain number of steps
            # motor_controller.move(steps)

            # Check for wall approach and decelerate
            if measure_distance() < 10:  # 10 cm threshold
                while current_speed < min_speed:
                    current_speed += 0.0001
                    motor_controller.set_speed(current_speed)
                    time.sleep(0.1)
                motor_controller.stop()
                break

        # Re-accelerate after moving away from wall or target
        while current_speed > max_speed:
            current_speed -= 0.0001
            motor_controller.set_speed(current_speed)
            time.sleep(0.1)

        time.sleep(0.1)  # Add a short delay to prevent CPU hogging

def cleanup_gpio():
    motor_controller.cleanup()
    target_detector.release()
    GPIO.cleanup()

def main():
    try:
        navigation_thread = threading.Thread(target=navigate_to_targets)
        navigation_thread.start()
        navigation_thread.join()
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        cleanup_gpio()

if __name__ == "__main__":
    main()
