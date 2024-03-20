import cv2
import numpy as np
import logging

class TargetDetector:
    def __init__(self, camera_index=0, desired_width=320, desired_height=240, debug_mode=False):
        self.cap = self.initialize_camera(camera_index, desired_width, desired_height)
        self.color_ranges = [((100, 100, 100), (120, 255, 255))]  # Example blue color range
        self.debug_mode = debug_mode
        self.y_displacement = 0  # Store y displacement of the most recently detected target

    def initialize_camera(self, camera_index, width, height):
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            logging.error("Failed to open camera")
            raise Exception("Cannot open camera")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        return cap

    def centroid(self, contour):
        M = cv2.moments(contour)
        if M['m00'] != 0:
            return int(M['m10'] / M['m00']), int(M['m01'] / M['m00'])
        return None

    def detect_targets(self):
        ret, frame = self.cap.read()
        if not ret:
            logging.error("Failed to read frame")
            return

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        largest_y_displacement = None  # To hold the y displacement of the largest detected target

        for color_range in self.color_ranges:
            mask = cv2.inRange(hsv, np.array(color_range[0]), np.array(color_range[1]))
            contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                center = self.centroid(largest_contour)
                if center:
                    y_displacement = center[1] - (frame.shape[0] // 2)
                    largest_y_displacement = y_displacement  # Update with the latest y displacement
                    if self.debug_mode:
                        # Draw the contour and centroid for debugging
                        cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)
                        cv2.circle(frame, center, 5, (255, 0, 0), -1)

        if largest_y_displacement is not None:
            self.y_displacement = largest_y_displacement

        if self.debug_mode:
            cv2.imshow("Debug Stream", frame)
            cv2.waitKey(1)

    def get_y_displacement(self):
        return self.y_displacement

    def release(self):
        self.cap.release()

    def show_frame(self, frame, window_name="Frame"):
        if self.debug_mode and frame is not None:
            cv2.imshow(window_name, frame)
            cv2.waitKey(1)


def main():
    print("Starting target detection. Press Ctrl+C to stop.")
    detector = TargetDetector(debug_mode=True)  # Enable debug mode to see the detection window
    
    try:
        while True:
            detector.detect_targets()
            y_displacement = detector.get_y_displacement()
            print(f"Current Y displacement: {y_displacement}")
    except KeyboardInterrupt:
        print("Stopping detection...")
    finally:
        detector.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
