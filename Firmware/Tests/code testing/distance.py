import pigpio
from time import time, sleep


TRIG_PIN = 17
ECHO_PIN = 18

def measure_distance():
    # Send a 10us pulse to start the measurement
    pi.gpio_trigger(TRIG_PIN, 10, 1)

    # Wait for the echo start
    start_time = time()
    while pi.read(ECHO_PIN) == 0:
        start_time = time()

    # Wait for the echo end
    end_time = time()
    while pi.read(ECHO_PIN) == 1:
        end_time = time()

    # Calculate the distance
    elapsed_time = end_time - start_time
    distance = (elapsed_time * 343000) / 2  # Speed of sound is ~343000 mm/s at sea level

    return round(distance)

# Connect to pigiod daemon
print("Connecting to pigpio daemon.")
try:
    pi = pigpio.pi()
except:
    print("Could not connect to pigpio daemon")

# Set up ultrasonic sensor pins
pi.set_mode(TRIG_PIN, pigpio.OUTPUT)
pi.set_mode(ECHO_PIN, pigpio.INPUT)

try:
    while True:
        print(measure_distance())
        sleep(0.5)
except KeyboardInterrupt:
    print("stopped")
