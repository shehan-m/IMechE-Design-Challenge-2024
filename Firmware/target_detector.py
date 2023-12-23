import cv2
import numpy as np
import time
import logging
import threading

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
        for attempt in range(3):
            cap = cv2.VideoCapture(camera_index)
            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                return cap
            time.sleep(1)  # Wait a bit before retrying
        logging.error("Failed to open camera after several attempts")
        raise Exception("Cannot open camera")

    def centroid(self, contour):
        M = cv2.moments(contour)
        if M['m00'] != 0:
            return int(M['m10'] / M['m00']), int(M['m01'] / M['m00'])
        return None

    def start_detection(self):
        self.is_stopped = False
        self.detection_thread = threading.Thread(target=self.detect_targets)
        self.detection_thread.start()

    def stop_detection(self):
        self.is_stopped = True
        if self.detection_thread is not None:
            self.detection_thread.join()

    def detect_targets(self):
        while not self.is_stopped:
            ret, frame = self.cap.read()
            if not ret:
                logging.error("Failed to read frame, retrying...")
                time.sleep(0.5)
                continue

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
                        # Draw the contour and centroid for debuggingcx
                        cv2.drawContours(frame, [target_contour], -1, (0, 255, 0), 2)
                        cv2.circle(frame, center, 5, (255, 0, 0), -1)

            cv2.imshow("Debug Stream", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            if time.time() - self.fps_start_time < self.fps_interval:
                time.sleep(self.fps_interval - (time.time() - self.fps_start_time))
            self.fps_start_time = time.time()

        self.release()
        cv2.destroyAllWindows()

    def get_y_displacement(self):
        return self.y_displacement

    def release(self):
        self.cap.release()
