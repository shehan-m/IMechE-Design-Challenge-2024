import cv2
import numpy as np

import time
import pigpio
from gpiozero import Button, DistanceSensor

import queue
import threading

# GPIO PINS
# GPIO PINS
STEP_PIN = 21
DIR_PIN = 20

SWITCH_PIN = 16
START_PIN = 23
RESET_PIN = 24

TRIG_PIN = 27
ECHO_PIN = 17

# NAV CONSTANTS
SAFE_DIST = 250 # in mm
TARGET_CLEARANCE_TIME = 300 # in mm
X_OFFSET_CONV_FACTOR = 10
MM_TO_STEPS = 10
REQ_CONSEC = 5

# SPECFICIATION
PHASE_1_STOP_TIME = 7.5

# Create a queue to hold target offsets
target_offset_queue = queue.Queue()

def detector(fps_limit=30, width=640, height=480, debug=False):
    cap = cv2.VideoCapture(0)
    
    # Set the properties for resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    # Set the frame rate limit
    cap.set(cv2.CAP_PROP_FPS, fps_limit)

    while True:
        _, frame = cap.read()
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Blue color
        low_blue = np.array([94, 80, 2])
        high_blue = np.array([126, 255, 255])
        blue_mask = cv2.inRange(hsv_frame, low_blue, high_blue)
        blue = cv2.bitwise_and(frame, frame, mask=blue_mask)

        median = cv2.medianBlur(blue, 15)

        # Find contours
        gray = cv2.cvtColor(median, cv2.COLOR_BGR2GRAY)
        contours, _ = cv2.findContours(gray, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        if contours:
            # Find the largest contour
            largest_contour = max(contours, key=cv2.contourArea)

            # Get the moments to calculate the center of the contour
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                cX = int(M["m10"] / M["m00"])
                cY = int(M["m01"] / M["m00"])
            else:
                cX, cY = 0, 0

            # Calculate x displacement from the center of the frame
            center_frame_x = width // 2
            displacement_x = cX - center_frame_x
            target_offset_queue.put(displacement_x)

            if debug:
                # Display the displacement on the frame
                cv2.putText(frame, f"Displacement: {displacement_x}px", (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                # Draw the largest contour and its center
                cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 3)
                cv2.circle(frame, (cX, cY), 7, (255, 255, 255), -1)
                cv2.putText(frame, "center", (cX - 20, cY - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        else:
            # Clear the queue if no contours are found
            while not target_offset_queue.empty():
                target_offset_queue.get()

        if debug:
            cv2.imshow("Blue", median)
            cv2.imshow("Frame", frame)

        key = cv2.waitKey(1)
        if key == 27:  # Escape key
            break

    cap.release()
    if debug:
        cv2.destroyAllWindows()

def distance():
    return ultrasonic.distance / 1000

def move_motor(start_frequency, final_frequency, steps, dir=1, run_time=None):
    """Generate ramp waveforms from start to final frequency.
    
    Parameters:
    - start_frequency: Starting frequency of the ramp.
    - final_frequency: Ending frequency of the ramp.
    - steps: Number of steps in the ramp.
    - dir: Direction to move the motor (0 or 1).
    - run_time: Time in seconds to run the motor at final frequency, None for indefinite run.
    """
    if not pi.connected:
        print("Error connecting to pigpio daemon. Is the daemon running?")
        return

    pi.wave_clear()  # clear existing waves
    pi.write(DIR_PIN, dir)

    # Calculate frequency increments
    frequency_step = (final_frequency - start_frequency) / steps
    current_frequency = start_frequency

    wid = []

    for _ in range(steps):
        micros = int(500000 / current_frequency)  # microseconds for half a step
        wf = [
            pigpio.pulse(1 << STEP_PIN, 0, micros),
            pigpio.pulse(0, 1 << STEP_PIN, micros)
        ]
        pi.wave_add_generic(wf)
        wave_id = pi.wave_create()
        wid.append(wave_id)  # Append the new wave ID to the list
        current_frequency += frequency_step  # increment or decrement frequency
    
    # Generate a chain of waves
    chain = []
    for wave_id in wid:
        chain += [255, 0, wave_id, 255, 1, 1, 0]  # Transmit each wave once

    pi.wave_chain(chain)  # Transmit chain

    # Handle run time
    if run_time is not None:
        pi.wave_send_repeat(wid[-1])
        time.sleep(run_time)
        pi.wave_tx_stop()  # Stop waveform transmission
    else:
        # If no run_time specified, repeat the last waveform indefinitely
        pi.wave_send_repeat(wid[-1])

    # Clean up waveforms
    global last_wave_ids
    last_wave_ids = wid  # Store wave IDs globally to allow stopping later

def stop_motor():
    """Stop any running waveforms and clean up."""
    global last_wave_ids
    pi.wave_tx_stop()  # Stop any waveform transmission
    if last_wave_ids is not None:
        for wave_id in last_wave_ids:
            pi.wave_delete(wave_id)  # Clean up each waveform individually
    last_wave_ids = None

def align():
    consecutive_aligned = 0
    while consecutive_aligned < REQ_CONSEC:
        if not target_offset_queue.empty():
            offset = target_offset_queue.get()
            # Calculate the step delay and direction based on offset
            if offset == 0:
                consecutive_aligned += 1  # Increment if aligned
                continue
            else:
                consecutive_aligned = 0  # Reset if not aligned

            # Determine direction based on the sign of the offset
            direction = 1 if offset > 0 else 0
            pi.write(DIR_PIN, direction)

            # Calculate number of steps (proportional to the offset)
            steps = int(abs(offset) * X_OFFSET_CONV_FACTOR)

            # Create a simple waveform for these steps
            for _ in range(steps):
                pi.gpio_trigger(STEP_PIN, 10, 1)  # Trigger pulse for step
                time.sleep(0.001)  # Small delay between steps to control speed

    # Stop the motor once aligned
    pi.write(STEP_PIN, 0)  # Ensuring no more steps are triggered

def cycle():
    global wave_ids

    # Start moving forward
    move_motor(start_frequency=10, final_frequency=1000, steps=100, dir=1, run_time=None)
    start_time = time.time()

    # Continuously check distance
    while True:
        current_distance = distance()  # Measure distance from barrier
        
        if current_distance <= SAFE_DIST:
            # Slow down as it gets close to the barrier
            move_motor(start_frequency=1000, final_frequency=400, steps=100, dir=1, run_time=None)
            end_time = time.time()

        if limit_switch.is_pressed:
            # Stop the motor when the switch is pressed
            stop_motor()
            break  # Exit the loop once the limit switch is pressed

        time.sleep(0.1)  # Short delay to reduce sensor noise and CPU load

    # Return to the origin (for simplicity, assume this is reverse of travel_distance)
    move_motor(start_frequency=500, final_frequency=1000, steps=50, dir=0, run_time=(end_time - start_time) + 20)

    # Align with the origin / target
    align()

    # Wait for the specified stop time
    time.sleep(PHASE_1_STOP_TIME)

    # Move forward to find the next target and align with it
    move_motor(start_frequency=100, final_frequency=1000, steps=100, dir=1, run_time=None)

    # Time to clear the origin / first target
    time.sleep(10)  # Move forward for 10 seconds or until target is found

    while True:
        if not target_offset_queue.empty():
            move_motor(start_frequency=1000, final_frequency=300, steps=100, dir=1, run_time=None)
            break
    
    # Align with the target
    align()

    # Finally, stop the motor
    stop_motor(pi)
    print("Cycle complete: Aligned with the target.")

def menu():
    while True:
        # Wait for the start button to be pressed
        start.wait_for_press()
        start.wait_for_release()

        time.sleep(3)

        # Start the cycle function in a new thread
        cycle_thread = threading.Thread(target=cycle)
        cycle_thread.start()

        # Monitor for the reset button to be pressed
        while cycle_thread.is_alive():
            if reset.is_pressed:
                print("Reset pressed, stopping the cycle and resetting.")
                stop_motor()  # Ensure motor stops immediately
                cycle_thread.join()  # Wait for the cycle thread to finish
                break  # Exit the loop to reset the menu
            
        cycle_thread.join()  # Ensure the cycle thread has fully finished before looping back

        # Optionally add a small delay
        time.sleep(0.1)  # Helps with debouncing and CPU load

pi = pigpio.pi()
if not pi.connected:
    print("Error connecting to pigpio daemon. Is the daemon running?")

pi.set_mode(STEP_PIN, pigpio.OUTPUT)
pi.wave_clear()

ultrasonic = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN)
limit_switch = Button(SWITCH_PIN)

start = Button(START_PIN)
reset = Button(RESET_PIN)

wave_ids = []  # Keep track of created wave IDs globally or in shared context

#limit_switch.isPressed()
#print("The button was pressed!")

try:
    detector_thread = threading.Thread(target=detector)
    detector_thread.start()
    
    #menu_thread = threading.Thread(target=menu)
    #menu_thread.start()
    
    cycle_thread = threading.Thread(target=cycle)
    cycle_thread.start()
except KeyboardInterrupt:
    print("KeyboardInterrupt detected, stopping all threads.")
finally:
    detector_thread.join()
    #menu_thread.join()
    cycle_thread.join()
