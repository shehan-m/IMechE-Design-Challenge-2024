import threading
from target_detector import TargetDetector
import time

def main():
    print("Initializing target detector.")
    target_detector = TargetDetector(camera_index=-1, desired_width=640, desired_height=480, debug_mode=True)
    stop_event = threading.Event()

    def run_detection():
        while not stop_event.is_set():
            target_detector.detect_targets()

    print("Starting target detection.")
    detection_thread = threading.Thread(target=run_detection)
    detection_thread.start()

    try:
        while True:
            time.sleep(1)
            displacement = target_detector.get_x_displacement()
            if displacement is not None:
                print(displacement)
            else:
                print("No target detected.")
    except KeyboardInterrupt:
        print("Stopping target detection.")
       
if __name__ == "__main__":
    main()