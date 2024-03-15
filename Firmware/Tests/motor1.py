from time import sleep, time
import pigpio

DIR = 20     # Direction GPIO Pin
STEP = 21    # Step GPIO Pin
SWITCH = 16  # GPIO pin of switch

# Connect to pigpiod daemon
pi = pigpio.pi()

# Set up pins as an output
pi.set_mode(DIR, pigpio.OUTPUT)
pi.set_mode(STEP, pigpio.OUTPUT)

# Set up input switch
pi.set_mode(SWITCH, pigpio.INPUT)
pi.set_pull_up_down(SWITCH, pigpio.PUD_UP)

MODE = (14, 15, 18)   # Microstep Resolution GPIO Pins
RESOLUTION = {'Full': (0, 0, 0),
              'Half': (1, 0, 0),
              '1/4': (0, 1, 0),
              '1/8': (1, 1, 0),
              '1/16': (0, 0, 1),
              '1/32': (1, 0, 1)}
for i in range(3):
    pi.write(MODE[i], RESOLUTION['Full'][i])

# Set duty cycle and frequency
pi.set_PWM_dutycycle(STEP, 128)  # PWM 1/2 On 1/2 Off
pi.set_PWM_frequency(STEP, 500)  # 500 pulses per second

# Initialize direction
direction = 1

last_press_time = 0
debounce_time = 0.1  # 100ms debounce time

# Callback function to toggle direction
def toggle_direction(gpio, level, tick):
    global direction, last_press_time
    current_time = time()
    if (current_time - last_press_time) >= debounce_time:  # Debounce
        direction = not direction
        pi.write(DIR, direction)
        last_press_time = current_time

# Set up a falling edge detection on the switch, calling toggle_direction
pi.callback(SWITCH, pigpio.FALLING_EDGE, toggle_direction)

try:
    while True:
        sleep(0.1)  # Main loop does nothing; direction is changed in the callback

except KeyboardInterrupt:
    print("\nCtrl-C pressed. Stopping PIGPIO and exiting...")
finally:
    pi.set_PWM_dutycycle(STEP, 0)  # PWM off
    pi.stop()
