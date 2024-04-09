import cv2
import numpy as np
import time  # Import the time module

# Function to get center of contour
def centroid(contour):
    M = cv2.moments(contour)
    if M['m00'] != 0:
        cx = int(round(M['m10'] / M['m00']))
        cy = int(round(M['m01'] / M['m00']))
        center = (cx, cy)
        return center
    else:
        return None

# Define color ranges for each ring
color_ranges = [
    ((100, 100, 100), (120, 255, 255))  # Blue
]

# Open camera
cap = cv2.VideoCapture(1)  # Use 0 for the default camera

# Set desired fps and resolution
desired_fps = 30
desired_width = 640
desired_height = 480

# Set camera properties
cap.set(cv2.CAP_PROP_FRAME_WIDTH, desired_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, desired_height)
cap.set(cv2.CAP_PROP_FPS, desired_fps)

# Check if the camera properties were set correctly
print("Actual FPS:", cap.get(cv2.CAP_PROP_FPS))
print("Actual Resolution:", (cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

# Variables for controlling the frame rate
fps_start_time = time.time()
fps_interval = 1.0 / desired_fps

while True:
    # Capture frame from camera
    ret, frame = cap.read()

    # Convert frame to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Track target center for each color range
    centers = []
    for color_range in color_ranges:
        lower, upper = np.array(color_range[0]), np.array(color_range[1])
        mask = cv2.inRange(hsv, lower, upper)
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Find the biggest contour
        if contours:
            blue_contour = max(contours, key=cv2.contourArea)
            center = centroid(blue_contour)

            # Check if center is not None before appending
            if center is not None:
                centers.append(center)

                # Draw contour centers
                frame = cv2.drawContours(frame, [blue_contour], -1, (0, 255, 0), 3)
                frame = cv2.circle(frame, center, 2, (0, 0, 255), -1)

                # Draw line from the center of the blue circle to the center of the screen
                screen_center = (frame.shape[1] // 2, frame.shape[0] // 2)
                frame = cv2.line(frame, center, screen_center, (255, 0, 0), 2)

    # Display the result
    cv2.imshow("Tracking", frame)

    # Control the frame rate
    elapsed_time = time.time() - fps_start_time
    if elapsed_time < fps_interval:
        time.sleep(fps_interval - elapsed_time)
    fps_start_time = time.time()

    # Break the loop if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the camera and close the window
cap.release()
cv2.destroyAllWindows()
