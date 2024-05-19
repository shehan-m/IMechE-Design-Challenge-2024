import asyncio
import cv2
import numpy as np
import pigpio
import math
import time

# GPIO PINS
STEP_PIN = 21
DIR_PIN = 20
SWITCH_PIN = 16
TRIG_PIN = 17
ECHO_PIN = 18

# NAV CONSTANTS
SAFE_DIST = 250 # in mm
TARGET_CLEARANCE_DIST = 300 # in mm
X_OFFSET_TO_STEPS = 10
MM_TO_STEPS = 10
REQ_CONSEC = 5

# SPECFICIATION
PHASE_1_STOP_TIME = 7.5

# Async Target Detector class
class AsyncTargetDetector:
    def __init__(self, camera_index=0, desired_width=720, desired_height=720):
        self.cap = self.initialize_camera(camera_index, desired_width, desired_height)

    def initialize_camera(self, camera_index, width, height):
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            raise IOError("Cannot open webcam")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        return cap

    async def detect_targets(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                await asyncio.sleep(0.1)
                continue  # Retry if no frame is captured

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, np.array([110, 50, 50]), np.array([130, 255, 255]))

            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                moments = cv2.moments(largest_contour)
                if moments["m00"] != 0:
                    center_x = int(moments["m10"] / moments["m00"])
                    return center_x - (frame.shape[1] // 2)

            await asyncio.sleep(0.1)

# Async function to get the distance from an ultrasonic sensor
async def get_distance(pi, timeout=1.0):
    """
    Measures the distance using an ultrasonic sensor asynchronously.

    Args:
        pi (pigpio.pi): An instance of the pigpio library.
        timeout (float): Maximum time (in seconds) to wait for a signal.

    Returns:
        int: Distance in millimeters, or None if timeout.
    """
    # Send a 10-microsecond pulse to start the measurement
    pi.gpio_trigger(TRIG_PIN, 10, 1)
    
    start_time = time.time()
    # Wait for the echo start
    while pi.read(ECHO_PIN) == 0:
        if time.time() - start_time > timeout:
            print("Timeout waiting for signal to start")
            return None  # Timeout if no start signal
    start_echo = time.time()

    # Wait for the echo end
    while pi.read(ECHO_PIN) == 1:
        if time.time() - start_echo > timeout:
            print("Timeout waiting for signal to end")
            return None  # Timeout if signal doesn't end
    end_echo = time.time()

    # Calculate the distance in millimeters
    elapsed_time = end_echo - start_echo
    distance = (elapsed_time * 343000) / 2  # Dividing by 2 for one-way distance
    
    return round(distance)  # Return the distance rounded to the nearest whole number

async def check_switch(pi, check_interval=0.1):
    """
    Monitors if a button is pressed at regular intervals.
    
    Args:
        pi (pigpio.pi): An instance of the pigpio library.
        check_interval (float): Time in seconds between checks.
    
    Returns:
        True or False
    """
    await asyncio.sleep(check_interval)  # Wait before checking again
    return pi.read(SWITCH_PIN) == 1


# Async function to move the motor with S-curve acceleration
async def move_motor(pi, direction, total_steps, max_speed=500, accel_ratio=0.5):
    """
    Moves the motor with a gradual acceleration profile to reduce traction loss.
    
    Args:
        pi (pigpio.pi): Pigpio instance for GPIO control.
        direction (int): Motor direction (1 for forward, 0 for backward).
        total_steps (int): Total steps to move.
        max_speed (int): Maximum speed in steps per second.
        accel_ratio (float): Ratio of steps used for acceleration and deceleration.
    """
    pi.write(DIR_PIN, direction)
    
    # Calculate the number of steps for acceleration and deceleration
    accel_steps = int(total_steps * accel_ratio)
    decel_start = total_steps - accel_steps
    
    current_speed = 0  # Start speed
    for step in range(total_steps):
        # Determine phase progress based on step count and acceleration ratio
        if step < accel_steps:
            # Acceleration phase with an S-curve profile
            phase_progress = step / accel_steps
            accel_factor = (1 - math.cos(math.pi * phase_progress)) / 2
        elif step >= decel_start:
            # Deceleration phase with an S-curve profile
            phase_progress = (total_steps - step) / accel_steps
            accel_factor = (1 - math.cos(math.pi * phase_progress)) / 2
        else:
            # Constant speed phase
            accel_factor = 1.0
        
        current_speed = max_speed * accel_factor
        delay = 1 / (2 * max(current_speed, 1))  # Ensure delay is never zero
        
        pi.write(STEP_PIN, 1)
        await asyncio.sleep(delay)
        pi.write(STEP_PIN, 0)
        await asyncio.sleep(delay)

async def smooth_acceleration(pi, start_freq, end_freq, duration):
    """
    Smoothly changes the PWM frequency from start_freq to end_freq with an S-curve profile over a specified duration.
    
    Args:
        pi (pigpio.pi): Pigpio instance for GPIO control.
        start_freq (int): Initial PWM frequency.
        end_freq (int): Final PWM frequency.
        duration (float): Duration over which to change the frequency.
    """
    start_time = time.time()
    end_time = start_time + duration
    
    while time.time() < end_time:
        # Calculate elapsed time ratio
        t = time.time() - start_time
        elapsed_ratio = 0.5 * (1 - math.cos(math.pi * (t / duration)))  # Generate S-curve profile
        
        # Determine current frequency based on S-curve
        current_freq = int(start_freq + elapsed_ratio * (end_freq - start_freq))
        
        pi.set_PWM_frequency(STEP_PIN, current_freq)
        await asyncio.sleep(0.1)  # Short delay to avoid excessive loop iterations

# Async function to align with the target
async def align(pi, target_detector, direction):
    consecutive_aligned = 0

    pi.write(DIR_PIN, direction)
    pi.set_PWM_dutycycle(STEP_PIN, 128)  # PWM 1/2 On 1/2 Off
    await smooth_acceleration(pi, 0, 100, 1)

    while consecutive_aligned < REQ_CONSEC:
        x_displacement = await target_detector.detect_targets()
        if x_displacement is not None:
            await smooth_acceleration(pi, 100, 0, 2)
            steps_needed = abs(x_displacement * X_OFFSET_TO_STEPS)
            
            if steps_needed == 0:
                consecutive_aligned += 1
            else:
                direction = 1 if x_displacement > 0 else 0
                await move_motor(pi, direction, steps_needed, 100)
                consecutive_aligned = 0
        else:
            await smooth_acceleration(pi, 0, 100, 1)
            consecutive_aligned = 0

        await asyncio.sleep(0.1)

# Main asynchronous function
async def main():
    pi = pigpio.pi()  # Initialize pigpio
    target_detector = AsyncTargetDetector(camera_index=0, desired_width=640, desired_height=480)

    # Configure GPIO modes
    pi.set_mode(STEP_PIN, pigpio.OUTPUT)
    pi.set_mode(DIR_PIN, pigpio.OUTPUT)
    pi.set_mode(SWITCH_PIN, pigpio.INPUT)
    pi.set_pull_up_down(SWITCH_PIN, pigpio.PUD_UP)
    pi.set_mode(TRIG_PIN, pigpio.OUTPUT)
    pi.set_mode(ECHO_PIN, pigpio.INPUT)

    try:
        # Phase 1
        initial_distance = await get_distance(pi)

        # await align(pi, target_detector, 1)

        pi.write(DIR_PIN, 1) # Set motor direction
        pi.set_PWM_dutycycle(STEP_PIN, 128)

        # Initial acceleration to 500 pulses per second
        await smooth_acceleration(pi, 0, 500, 5)  # Gradual acceleration over 2 seconds

        # Continue moving until the distance is below the safe threshold
        while True:
            current_distance = await get_distance(pi)
            if current_distance < SAFE_DIST:
                break  # Exit when distance is below the safe threshold
            await asyncio.sleep(0.1)  # Delay to avoid busy loop
        
        # Gradual deceleration to 100 pulses per second
        await smooth_acceleration(pi, 500, 100, 2)  # Gradual deceleration over 2 seconds

        while True:
            isPressed = await check_switch(pi)
            if isPressed:
                print("Switch Pressed")
                pi.set_PWM_dutycycle(STEP_PIN, 0)
                break

        # Move the motor back by the initial distance
        await move_motor(pi, 0, initial_distance * MM_TO_STEPS, 500, 0.2)

        # Align with the target
        await align(pi, target_detector, 0)
        
        time.sleep(PHASE_1_STOP_TIME)  # Pause for a specific duration

        # Phase 2
        # Align with the second target
        await move_motor(pi, 1, TARGET_CLEARANCE_DIST * MM_TO_STEPS, 200)
        await align(pi, target_detector, 1)
    finally:
        pi.set_PWM_dutycycle(STEP_PIN, 0)  # Ensure the motor stops
        pi.stop()  # Stop pigpio instance

# Run the main function
asyncio.run(main())
