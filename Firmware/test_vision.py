from target_detector import TargetDetector
import time

def run_alignment(detector):
    detector.detect_targets()

detector = TargetDetector(0, 15, 320, 240, False)

max_consecutive_zeros = 5
consecutive_zeros = 0

not_detected = True

detector.start_detection()

# Use target alignment
# Main thread continuously checks y_displacement
while not_detected:
    y_displacement = detector.get_y_displacement()
    print("Y Displacement:", y_displacement)

    # Add any other processing or conditions as needed
    time.sleep(0.5)

    # Stop detection if needed (e.g., after x consecutive zeros)
    if y_displacement == 0:
        consecutive_zeros += 1
        if consecutive_zeros >= max_consecutive_zeros:
            detector.stop_detection()
            not_detected = False
            break
    else:
        consecutive_zeros = 0

print("done")