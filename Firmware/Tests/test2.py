import cv2
from picamera2 import Picamera2
import time
import numpy as np

picam2 = Picamera2()
dispW = 1280
dispH = 720
picam2.preview_configuration.main.size = (dispW, dispH)
picam2.preview_configuration.main.format = "RGB888"
picam2.preview_configuration.controls.FrameRate = 30
picam2.preview_configuration.align()
picam2.configure("preview")
picam2.start()
fps = 0
pos = (30, 60)
font = cv2.FONT_HERSHEY_SIMPLEX
height = 1.5
weight = 3
myColor = (0, 0, 255)

# Define the lower and upper bounds for the blue color (you may need to adjust these values)
blueLower = np.array([100, 50, 50])
blueUpper = np.array([120, 255, 255])

while True:
    tStart = time.time()
    frame = picam2.capture_array()
    frame = cv2.flip(frame, -1)
    frameHSV = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    cv2.putText(frame, str(int(fps)) + ' FPS', pos, font, height, myColor, weight)

    # Threshold the frame to get only blue pixels
    blueMask = cv2.inRange(frameHSV, blueLower, blueUpper)

    # Find contours in the blue mask
    contours, _ = cv2.findContours(blueMask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if len(contours) > 0:
        # Sort contours based on area and get the largest one
        contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
        contour = contours[0]

        # Fit a circle to the contour
        (x, y), radius = cv2.minEnclosingCircle(contour)
        center = (int(x), int(y))
        radius = int(radius)

        # Check if the detected circle has approximately 80mm diameter
        if 78 < 2 * radius < 82:
            # Draw the circle and its center
            cv2.circle(frame, center, radius, (0, 0, 255), 3)
            cv2.circle(frame, center, 5, (0, 255, 0), -1)

    cv2.imshow("Camera", frame)
    if cv2.waitKey(1) == ord('q'):
        break

    tEnd = time.time()
    loopTime = tEnd - tStart
    fps = 0.9 * fps + 0.1 * (1 / loopTime)

cv2.destroyAllWindows()