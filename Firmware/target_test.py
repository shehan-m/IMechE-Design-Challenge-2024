from target_detector import TargetDetector
import threading

def align(req_consec_zero_count):
    """
    Aligns the mechanism by adjusting its position based on y-offset until the required number of consecutive
    zero-displacements is achieved.

    Args:
        req_consec_zero_count (int): The number of consecutive zero-displacements required for alignment.
    """
    consec_zero_count = 0  # Counter for consecutive zero-displacements

    while consec_zero_count < req_consec_zero_count:
        y_offset = target_detector.get_y_displacement()
        print(f"Current Y offset: {y_offset}")

        if abs(y_offset) <= 1:
            consec_zero_count += 1
            print(f"Alignment count: {consec_zero_count}/{req_consec_zero_count}")
        else:
            consec_zero_count = 0  # Reset counter if displacement is outside threshold
            print("Adjusting alignment...")

# Initialization and setup code
print("Initializing target detector.")
target_detector = TargetDetector(camera_index=1, desired_width=1280, desired_height=720, debug_mode=True)

# Start the target detector and main code threads
detector_thread = threading.Thread(target=target_detector.detect_targets)
detector_thread.start()

detector_thread.join()