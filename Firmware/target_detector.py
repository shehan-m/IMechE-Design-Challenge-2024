import cv2
import numpy as np
import time

class TargetDetector:
    def __init__(self, camera_index=0, desired_fps=30, desired_width=640, desired_height=480):
        """
        Initialize the TargetDetector class with specified parameters.

        Parameters:
        - camera_index: Index of the camera to be used (default is 0 for the default camera).
        - desired_fps: Desired frames per second for video capture.
        - desired_width: Desired frame width for video capture.
        - desired_height: Desired frame height for video capture.
        """
        self.cap = cv2.VideoCapture(camera_index)  # Open a video capture object
        self.desired_fps = desired_fps  # Desired frames per second
        self.desired_width = desired_width  # Desired frame width
        self.desired_height = desired_height  # Desired frame height
        self.color_ranges = [((100, 100, 100), (120, 255, 255))]  # Blue color range
        self.fps_start_time = time.time()  # Initialize the start time for fps control
        self.fps_interval = 1.0 / self.desired_fps  # Calculate time interval for desired fps

        self.y_displacement = 0

        self.is_stopped = False  # Flag to stop the detection loop

        # Set the camera properties
        self.set_camera_properties()

    def set_camera_properties(self):
        """
        Set camera properties such as frame width, frame height, and frames per second.
        """
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.desired_width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.desired_height)
        self.cap.set(cv2.CAP_PROP_FPS, self.desired_fps)

    def centroid(self, contour):
        """
        Calculate the centroid of a contour.

        Parameters:
        - contour: Input contour.

        Returns:
        - Tuple (cx, cy) representing the centroid coordinates.
        """
        M = cv2.moments(contour)
        if M['m00'] != 0:
            cx = int(round(M['m10'] / M['m00']))
            cy = int(round(M['m01'] / M['m00']))
            return cx, cy
        else:
            return None

    def stop_detection(self):
        """
        Stop the detection loop by setting the is_stopped flag.
        """
        self.is_stopped = True

    def align_target(self):
        while not self.is_stopped:
            ret, frame = self.cap.read()
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            centers = []
            for color_range in self.color_ranges:
                lower, upper = np.array(color_range[0]), np.array(color_range[1])
                mask = cv2.inRange(hsv, lower, upper)
                contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                if contours:
                    # Find the largest contour in the color range
                    target_contour = max(contours, key=cv2.contourArea)
                    center = self.centroid(target_contour)

                    if center is not None:
                        centers.append(center)
                        screen_center = (frame.shape[1] // 2, frame.shape[0] // 2)

                        self.y_displacement =  center[1] - screen_center[1]

            elapsed_time = time.time() - self.fps_start_time
            if elapsed_time < self.fps_interval:
                time.sleep(self.fps_interval - elapsed_time)
            self.fps_start_time = time.time()

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Break the loop if 'q' key is pressed
                break

        self.release()

    def detect_targets(self):
        """
        Main function to detect targets in the video stream.
        """
        while True:
            ret, frame = self.cap.read()  # Read a frame from the video stream
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)  # Convert frame to HSV color space

            centers = []
            for color_range in self.color_ranges:
                lower, upper = np.array(color_range[0]), np.array(color_range[1])
                mask = cv2.inRange(hsv, lower, upper)
                contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                if contours:
                    # Find the largest contour in the color range
                    target_contour = max(contours, key=cv2.contourArea)
                    center = self.centroid(target_contour)

                    if center is not None:
                        centers.append(center)

                        # Draw contour and line to the screen center on the frame
                        frame = cv2.drawContours(frame, [target_contour], -1, (0, 255, 0), 3)
                        frame = cv2.circle(frame, center, 2, (0, 0, 255), -1)
                        screen_center = (frame.shape[1] // 2, frame.shape[0] // 2)
                        frame = cv2.line(frame, center, screen_center, (255, 0, 0), 2)

            cv2.imshow("Tracking", frame)  # Display the resulting frame

            elapsed_time = time.time() - self.fps_start_time
            if elapsed_time < self.fps_interval:
                time.sleep(self.fps_interval - elapsed_time)
            self.fps_start_time = time.time()

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Break the loop if 'q' key is pressed
                break

        self.release()  # Release the video capture object

    def get_y_displacement(self):
        return self.y_displacement

    def release(self):
        """
        Release the video capture object and close all OpenCV windows.
        """
        self.cap.release()
        cv2.destroyAllWindows()