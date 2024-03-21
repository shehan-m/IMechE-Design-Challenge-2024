from time import sleep
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
    pi.set_mode(MODE[i], pigpio.OUTPUT)
    pi.write(MODE[i], RESOLUTION['Full'][i])

# Frequency and speed settings
frequency = 500  # steps per second
pi.set_PWM_frequency(STEP, frequency)

# Function to move motor
def move_motor(direction, steps):
    pi.write(DIR, direction)
    for _ in range(steps):
        pi.write(STEP, 1)
        sleep(1 / (2 * frequency))
        pi.write(STEP, 0)
        sleep(1 / (2 * frequency))

try:
    steps = 0
    # Move forward until switch is pressed
    while pi.read(SWITCH) == 1:  # Assuming switch is normally high and goes low when pressed
        move_motor(1, 10)  # Move one step forward
        steps += 10
        sleep(0.0001)  # Short delay to debounce and slow down the step rate if necessary

    # Once switch is pressed, reverse direction
    sleep(0.5)  # Short delay to ensure switch is fully pressed
    move_motor(0, steps)  # Move back the same number of steps

except KeyboardInterrupt:
    print("\nCtrl-C pressed. Stopping PIGPIO and exiting...")
finally:
    pi.stop()
