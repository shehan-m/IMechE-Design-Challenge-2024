import cv2
import numpy as np
import time
import logging

class TargetDetector:
    def __init__(self, camera_index=0, desired_fps=30, desired_width=640, desired_height=480):
        self.cap = self.initialize_camera(camera_index, desired_width, desired_height)
        self.desired_fps = desired_fps
        self.color_ranges = [((100, 100, 100), (120, 255, 255))]  # Example blue color range
        self.fps_start_time = time.time()
        self.fps_interval = 1.0 / self.desired_fps
        self.y_displacement = 0
        self.is_stopped = False

    def initialize_camera(self, camera_index, width, height):
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            logging.error("Cannot open camera")
            raise Exception("Cannot open camera")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        return cap

    def centroid(self, contour):
        M = cv2.moments(contour)
        if M['m00'] != 0:
            return int(M['m10'] / M['m00']), int(M['m01'] / M['m00'])
        return None

    def stop_detection(self):
        self.is_stopped = True

    def detect_targets(self):
        while not self.is_stopped:
            ret, frame = self.cap.read()
            if not ret:
                logging.error("Failed to read frame")
                break

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            centers = []
            for color_range in self.color_ranges:
                mask = cv2.inRange(hsv, np.array(color_range[0]), np.array(color_range[1]))
                contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                if contours:
                    target_contour = max(contours, key=cv2.contourArea)
                    center = self.centroid(target_contour)
                    if center:
                        centers.append(center)
                        self.y_displacement = center[1] - (frame.shape[0] // 2)

            # Additional processing or feedback mechanisms can be added here

            if time.time() - self.fps_start_time < self.fps_interval:
                time.sleep(self.fps_interval - (time.time() - self.fps_start_time))
            self.fps_start_time = time.time()

        self.release()

    def get_y_displacement(self):
        return self.y_displacement

    def release(self):
        self.cap.release()
