import cv2
import numpy as np

# Initialize the video capture
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    if not ret:
        print("Failed to read frame")
        continue

    # Convert frame to HSV color space
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Define range for blue color and create a mask
    lower_blue = np.array([100, 150, 0])
    upper_blue = np.array([140, 255, 255])
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

    # Bitwise-AND mask and original image to filter only blue parts
    blue_only = cv2.bitwise_and(frame, frame, mask=blue_mask)

    # Convert to grayscale
    gray = cv2.cvtColor(blue_only, cv2.COLOR_BGR2GRAY)

    # Apply GaussianBlur to reduce noise and improve circle detection
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)

    # Apply Hough transform on the blurred image to detect circles
    detected_circles = cv2.HoughCircles(blurred,
                                        cv2.HOUGH_GRADIENT, 1, minDist=50,
                                        param1=100, param2=30, minRadius=10, maxRadius=0)

    # Draw the largest detected circle
    if detected_circles is not None:
        detected_circles = np.uint16(np.around(detected_circles))
        largest_circle = max(detected_circles[0, :], key=lambda x: x[2])  # Select the largest circle

        x, y, r = largest_circle[:3]

        # Draw the circumference of the largest circle
        cv2.circle(frame, (x, y), r, (0, 255, 0), 2)

        # Draw a small circle (of radius 1) to show the center
        cv2.circle(frame, (x, y), 1, (0, 0, 255), 3)

    # Display the frame with the detected circle
    cv2.imshow("Detected Circle", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
