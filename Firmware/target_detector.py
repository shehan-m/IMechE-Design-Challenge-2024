import cv2
import numpy as np

class TargetDetector:
    def __init__(self, camera_index=0, desired_width=720, desired_height=720, debug_mode=False):
        self.cap = self.initialize_camera(camera_index, desired_width, desired_height)
        self.debug_mode = debug_mode
        self.x_displacement = 0
        self.blue_hsv_lower = np.array([110, 50, 50])
        self.blue_hsv_upper = np.array([130, 255, 255])

    def initialize_camera(self, camera_index, width, height):
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            raise IOError("Cannot open webcam")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        return cap

    def detect_targets(self):
        ret, frame = self.cap.read()
        if not ret:
            raise IOError("Cannot read from webcam")

        # Convert the image to the HSV color space
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Create a mask for the blue color using the predefined range
        mask = cv2.inRange(hsv, self.blue_hsv_lower, self.blue_hsv_upper)

        # Find contours in the mask
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        valid_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue  # Avoid division by zero
            circularity = 4 * np.pi * (area / (perimeter * perimeter))
            if area > 100 and circularity > 0.7:  # Adjust thresholds as needed
                valid_contours.append(cnt)

        if valid_contours:
            # Find the largest contour, assumed to be the target
            largest_contour = max(valid_contours, key=cv2.contourArea)
            moments = cv2.moments(largest_contour)
            if moments["m00"] != 0:
                center_x = int(moments["m10"] / moments["m00"])
                center_y = int(moments["m01"] / moments["m00"])
                self.x_displacement = center_x - (frame.shape[1] // 2)

                if self.debug_mode:
                    # Draw the center of the target
                    cv2.circle(frame, (center_x, center_y), 5, (0, 255, 0), -1)
                    # Draw center line of the frame
                    cv2.line(frame, (frame.shape[1] // 2, 0), (frame.shape[1] // 2, frame.shape[0]), (0, 0, 255), 2)
                    # Show the frame with the detected target
                    cv2.imshow('Target Detection', frame)
                    cv2.waitKey(1)
        else:
            self.x_displacement = None  # Reset displacement when no valid targets are detected

    def get_x_displacement(self):
        return self.x_displacement

    def release(self):
        self.cap.release()
        if self.debug_mode:
            cv2.destroyAllWindows()
