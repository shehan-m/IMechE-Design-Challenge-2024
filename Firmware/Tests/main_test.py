import cv2
import numpy as np

import time
import pigpio
from gpiozero import Button, DistanceSensor

import queue
import threading

# GPIO PINS
STEP_PIN = 21
DIR_PIN = 20

SWITCH_PIN = 16
START_PIN = 0
RESET_PIN = 0

TRIG_PIN = 4
ECHO_PIN = 17

# NAV CONSTANTS
SAFE_DIST = 250 # in mm
TARGET_CLEARANCE_DIST = 300 # in mm
X_OFFSET_TO_STEPS = 10
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
    return ultrasonic.distance

def move_motor(pi, STEP_PIN, DIR_PIN, start_frequency=100, final_frequency=5000, steps=100, run_time=None):
    global wave_ids

    start_delay = 1 / start_frequency
    final_delay = 1 / final_frequency

    # Determine ramp direction
    ramp_up = start_frequency < final_frequency

    # Calculate ramp steps
    if ramp_up:
        step_size = (final_delay - start_delay) / steps
    else:
        step_size = (start_delay - final_delay) / steps

    # Create waveform for final speed
    wf = [
        pigpio.pulse(1 << STEP_PIN, 0, int(final_delay * 1e6)),
        pigpio.pulse(0, 1 << STEP_PIN, int(final_delay * 1e6))
    ]
    pi.wave_add_generic(wf)
    wid0 = pi.wave_create()

    # Build initial ramp
    wf = []
    delay = start_delay
    for _ in range(steps):
        wf.append(pigpio.pulse(1 << STEP_PIN, 0, int(delay * 1e6)))
        wf.append(pigpio.pulse(0, 1 << STEP_PIN, int(delay * 1e6)))
        if ramp_up:
            delay += step_size
        else:
            delay -= step_size

    pi.wave_add_generic(wf)
    wid1 = pi.wave_create()

    # Send ramp, then repeat final rate
    pi.wave_send_once(wid1)
    offset = pi.wave_get_micros()  # Duration of the ramp in microseconds
    time.sleep(float(offset) / 1e6)  # Wait for ramp to complete

    pi.wave_send_repeat(wid0)  # Start repeating final speed waveform

    # If run_time is specified, run for that duration then stop, otherwise run indefinitely
    if run_time is not None:
        time.sleep(run_time)  # Run motor at final speed for specified time
        pi.wave_tx_stop()  # Stop waveform after run_time
        pi.wave_delete(wid0)  # Delete waveform
        pi.wave_delete(wid1)  # Delete waveform
    else:
        # Leaving the motor running, cleanup will need to be handled externally
        wave_ids.extend([wid0, wid1])
        pass

def stop_motor(pi):
    global wave_ids
    pi.wave_tx_stop()  # Stop any waveform transmission
    for wid in wave_ids:
        pi.wave_delete(wid)  # Clean up waveforms
    wave_ids = []  # Clear the list after cleanup

def align(pi, STEP_PIN, DIR_PIN):
    # Constants for PID control or simple proportional control
    Kp = 0.1  # Proportional gain - This value might need tuning

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
            steps = int(abs(offset) * MM_TO_STEPS * Kp)

            # Create a simple waveform for these steps
            for _ in range(steps):
                pi.gpio_trigger(STEP_PIN, 10, 1)  # Trigger pulse for step
                time.sleep(0.001)  # Small delay between steps to control speed

    # Stop the motor once aligned
    pi.write(STEP_PIN, 0)  # Ensuring no more steps are triggered

def cycle(pi, STEP_PIN, DIR_PIN, SWITCH_PIN):
    global wave_ids
    travel_distance = 0  # This will record the total distance traveled

    # Start moving forward
    move_motor(pi, STEP_PIN, DIR_PIN, start_frequency=100, final_frequency=1000, steps=50)

    # Continuously check distance
    while True:
        current_distance = distance()  # Measure distance from barrier
        
        if current_distance <= SAFE_DIST:
            # Slow down as it gets close to the barrier
            move_motor(pi, STEP_PIN, DIR_PIN, start_frequency=1000, final_frequency=500, steps=50, run_time=None)

        if limit_switch.is_pressed:
            # Stop the motor when the switch is pressed
            stop_motor(pi)
            break  # Exit the loop once the limit switch is pressed

        # Add traveled distance
        travel_distance += MM_TO_STEPS  # Assuming each cycle covers a step equivalent

        time.sleep(0.1)  # Short delay to reduce sensor noise and CPU load

    # Record the distance at which the switch was pressed
    print(f"Switch activated at a distance of {travel_distance} steps from the starting position.")

    # Return to the origin (for simplicity, assume this is reverse of travel_distance)
    move_motor(pi, STEP_PIN, DIR_PIN, start_frequency=500, final_frequency=1000, steps=50, run_time=travel_distance / 1000)

    # Align with the origin / target
    align(pi, STEP_PIN, DIR_PIN)

    # Wait for the specified stop time
    time.sleep(PHASE_1_STOP_TIME)

    # Move forward to find the next target and align with it
    move_motor(pi, STEP_PIN, DIR_PIN, start_frequency=100, final_frequency=1000, steps=50, run_time=None)  # Start moving indefinitely

    # Time to clear the origin / first target
    time.sleep(10)  # Move forward for 10 seconds or until target is found

    # TODO: Once cleared continuously look for target by checking if offset values are consistently found
    
    # Align with the target
    align(pi, STEP_PIN, DIR_PIN)

    # Finally, stop the motor
    stop_motor(pi)
    print("Cycle complete: Aligned with the target.")

def menu():
    # TODO: when the start button is pressed, runs the cycle function. if the reset button is pressed while the cycle funciton is running 
    # or after the cycle function is completed restarts the menu function.
    while True:
        #if start.isPressed():
        time.sleep(5)
        cycle()
        pass
    pass
            
        

pi = pigpio.pi()
if not pi.connected:
    print("Error connecting to pigpio daemon. Is the daemon running?")

pi.set_mode(STEP_PIN, pigpio.OUTPUT)
pi.wave_clear()

ultrasonic = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN)
limit_switch = Button(SWITCH_PIN)

#start = Button(START_PIN)
#reset = Button(RESET_PIN)

wave_ids = []  # Keep track of created wave IDs globally or in shared context

#limit_switch.isPressed()
#print("The button was pressed!")

try:
    detector_thread = threading.Thread(target=detector)
    #menu_thread = threading.Thread(target=menu)
    cycle_thread = threading.Thread(target=cycle)
except KeyboardInterrupt:
    print("KeyboardInterrupt detected, stopping all threads.")
finally:
    detector_thread.join()
    #menu_thread.join()
    cycle_thread.join()
