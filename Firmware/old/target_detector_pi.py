from picamera2 import Picamera2
import numpy as np
import cv2
import logging
import time

class TargetDetector:
    def __init__(self, desired_width=320, desired_height=240, debug_mode=False):
        self.camera = None
        self.picamera2 = Picamera2()
        self.preview_config = self.picamera2.create_preview_configuration(main={"size": (desired_width, desired_height)})
        self.debug_mode = debug_mode
        self.y_displacement = 0
        self.inter_target_detected = False
        self.inter_detection_time = None
        self.color_ranges = [((100, 100, 100), (120, 255, 255))]  # Example blue color range
        self.initialize_camera(desired_width, desired_height)

    def initialize_camera(self, width, height):
        try:
            self.picamera2.configure(self.preview_config)
            self.picamera2.start()
            self.camera = self.picamera2
        except Exception as e:
            logging.error("Failed to initialize camera with picamera2: {}".format(e))
            raise

    def centroid(self, contour):
        M = cv2.moments(contour)
        if M['m00'] != 0:
            return int(M['m10'] / M['m00']), int(M['m01'] / M['m00'])
        return None

    def detect_targets(self):
        while True:
            frame = self.camera.capture_array()
            if frame is None:
                logging.error("Failed to capture frame")
                return

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            largest_y_displacement = None

            for color_range in self.color_ranges:
                mask = cv2.inRange(hsv, np.array(color_range[0]), np.array(color_range[1]))
                contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

                if contours:
                    largest_contour = max(contours, key=cv2.contourArea)
                    center = self.centroid(largest_contour)
                    if center:
                        self.inter_target_detected = True
                        self.inter_detection_time = time.time()

                        y_displacement = center[1] - (frame.shape[0] // 2)
                        largest_y_displacement = y_displacement
                        if self.debug_mode:
                            cv2.drawContours(frame, [largest_contour], -1, (0, 255, 0), 2)
                            cv2.circle(frame, center, 5, (255, 0, 0), -1)

            if largest_y_displacement is not None:
                self.y_displacement = largest_y_displacement

            if self.debug_mode:
                cv2.imshow("Debug Stream", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            time.sleep(0.1)

    def get_y_displacement(self):
        return self.y_displacement

    def get_inter_target_detection_time(self):
        if self.inter_target_detected:
            return self.inter_detection_time
        else:
            return None

    def release(self):
        self.picamera2.stop()

    def show_frame(self, frame, window_name="Frame"):
        if self.debug_mode and frame is not None:
            cv2.imshow(window_name, frame)
            cv2.waitKey(1)
