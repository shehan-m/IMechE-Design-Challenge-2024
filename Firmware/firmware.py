'''
sudo apt-get install python3-opencv
sudo apt-get install fswebcam
'''

from target_detector import TargetDetector

td = TargetDetector()
td.detect_targets()