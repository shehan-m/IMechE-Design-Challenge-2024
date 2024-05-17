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

def move_motor(pi, STEP_PIN=STEP_PIN, DIR_PIN=DIR_PIN, final_delay=100, start_delay=5000, steps=100, run_time=1):
    # Create waveform for final speed
    wf = [
        pigpio.pulse(1 << STEP_PIN, 0, final_delay),
        pigpio.pulse(0, 1 << STEP_PIN, final_delay)
    ]
    pi.wave_add_generic(wf)
    wid0 = pi.wave_create()

    # Build initial ramp
    wf = []
    for delay in range(start_delay, final_delay, -steps):
        wf.append(pigpio.pulse(1 << STEP_PIN, 0, delay))
        wf.append(pigpio.pulse(0, 1 << STEP_PIN, delay))
    pi.wave_add_generic(wf)
    wid1 = pi.wave_create()

    # Send ramp, then repeat final rate
    pi.wave_send_once(wid1)
    offset = pi.wave_get_micros()  # Duration of the ramp in microseconds
    time.sleep(float(offset) / 1000000)  # Wait for ramp to complete

    pi.wave_send_repeat(wid0)  # Start repeating final speed waveform
    time.sleep(run_time)  # Run motor at final speed for specified time

    # Cleanup and stop
    pi.wave_tx_stop()  # Stop waveform
    pi.wave_delete(wid0)  # Delete waveform
    pi.wave_delete(wid1)  # Delete waveform

def align():
    if not target_offset_queue.empty():
        offset = target_offset_queue.get()

def cycle():
    # Move forward until switch is pressed
    # Return to origin 
    pass

pi = pigpio.pi()
if not pi.connected:
    print("Error connecting to pigpio daemon. Is the daemon running?")

pi.set_mode(STEP_PIN, pigpio.OUTPUT)
pi.wave_clear()

ultrasonic = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN)
limit_switch = Button(SWITCH_PIN)

#limit_switch.isPressed()
#print("The button was pressed!")

try:
    detector_thread = threading.Thread(target=detector)
except KeyboardInterrupt:
    print("KeyboardInterrupt detected, stopping all threads.")
finally:
    detector_thread.join()

# Example usage with debug mode enabled
detector(fps_limit=30, width=640, height=480, debug=False)
