from Firmware.target_detector import TargetDetector
import time
import threading

# Initialize the TargetDetector
print("Initializing target detector.")
target_detector = TargetDetector(camera_index=0, desired_width=640, desired_height=480, debug_mode=True)

# Define a function to run target detection in a background thread
def run_detection():
    target_detector.detect_targets()

# Start the detection process in a separate thread
detection_thread = threading.Thread(target=run_detection)
detection_thread.start()

try:
    while True:
        # Main thread continues running and can periodically check the y displacement
        y_offset = target_detector.get_y_displacement()
        print(f"Current Y Displacement: {y_offset}")
        time.sleep(1)  # Adjust the sleep time as needed

except KeyboardInterrupt:
    print("Stopping detection and exiting...")
finally:
    # Stop the background detection thread and release resources
    if detection_thread.is_alive():
        # Here, you'd need a way to gracefully terminate detect_targets or just wait for it to complete
        # This may require adding some mechanism in your class to stop the loop in detect_targets, as threading.Thread does not have a direct stop method.
        pass  # Implement stopping mechanism
    
    target_detector.release()
