import cv2
import numpy as np

cap = cv2.VideoCapture(0)

while True:
    _, frame = cap.read()
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Blue color
    low_blue = np.array([94, 80, 2])
    high_blue = np.array([126, 255, 255])
    blue_mask = cv2.inRange(hsv_frame, low_blue, high_blue)
    blue = cv2.bitwise_and(frame, frame, mask=blue_mask)

    median = cv2.medianBlur(blue, 15)

    cv2.imshow("Blue", blue)
    cv2.imshow("median", median)


    key = cv2.waitKey(1)
    if key == 27:
        break

cv2.destroyAllWindows()
cap.release()