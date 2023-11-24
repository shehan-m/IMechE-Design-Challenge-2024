import cv2
import numpy as np

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
    ((0, 0, 0), (0, 0, 50)),    # Black
    ((100, 100, 100), (120, 255, 255)),  # Blue
    ((0, 100, 100), (10, 255, 255)),  # Red
    ((20, 100, 100), (30, 255, 255)),  # Yellow
    ((0, 0, 200), (255, 50, 255))  # White
]

# Open video file
video_path = 'path/to/your/video/file.mp4'
cap = cv2.VideoCapture(video_path)

# Set desired FPS and resolution
desired_fps = 30
desired_width = 640
desired_height = 480

cap.set(cv2.CAP_PROP_FPS, desired_fps)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, desired_width)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, desired_height)

while True:
    # Capture frame from video
    ret, frame = cap.read()

    if not ret:
        break

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
            biggest_contour = max(contours, key=cv2.contourArea)
            center = centroid(biggest_contour)

            if center is not None:
                centers.append(center)

                # Draw contour centers
                frame = cv2.drawContours(frame, [biggest_contour], -1, (0, 255, 0), 3)
                frame = cv2.circle(frame, center, 2, (0, 0, 255), -1)

    # Draw coordinate axes
    frame = cv2.line(frame, (frame.shape[1] // 2, 0), (frame.shape[1] // 2, frame.shape[0]), (255, 255, 255), 2)
    frame = cv2.line(frame, (0, frame.shape[0] // 2), (frame.shape[1], frame.shape[0] // 2), (255, 255, 255), 2)

    # Display marker coordinates
    for i, center in enumerate(centers):
        cv2.putText(frame, f"Marker {i + 1}: ({center[0] - frame.shape[1] // 2}, {frame.shape[0] // 2 - center[1]})", 
                    (10, 30 * (i + 1)), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

    # Display the result
    cv2.imshow("Tracking", frame)

    # Break the loop if 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture and close the window
cap.release()
cv2.destroyAllWindows()
