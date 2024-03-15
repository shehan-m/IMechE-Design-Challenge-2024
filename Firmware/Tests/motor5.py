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
    pi.write(MODE[i], RESOLUTION['Full'][i])

# Ramp method
def generate_ramp(ramp):
    """Generate ramp wave forms."""
    pi.wave_clear()  # clear existing waves
    length = len(ramp)  # number of ramp levels
    wid = [-1] * length

    for i in range(length):
        frequency = ramp[i][0]
        micros = int(500000 / frequency)
        wf = [pigpio.pulse(1 << STEP, 0, micros), pigpio.pulse(0, 1 << STEP, micros)]
        pi.wave_add_generic(wf)
        wid[i] = pi.wave_create()

    chain = []
    for i in range(length):
        steps = ramp[i][1]
        chain += [255, 0, wid[i], 255, 1, steps & 255, steps >> 8]

    pi.wave_chain(chain)  # Transmit chain.
    while pi.wave_tx_busy():  # Wait for chain to complete
        sleep(0.1)

    for wid_i in wid:  # Clear waves
        pi.wave_delete(wid_i)

# Example ramp: Accelerate, then decelerate
forward_ramp = [[500, 100], [1000, 200], [500, 100]]
reverse_ramp = [[500, 100], [1000, 200], [500, 100],  [320, 100]]

try:
    # Move forward until switch is pressed
    pi.write(DIR, 1)  # Set direction forward
    while pi.read(SWITCH):
        generate_ramp(forward_ramp)
        if not pi.read(SWITCH):  # Check if switch is pressed
            break

    # Once switch is pressed, reverse direction
    sleep(0.5)  # Delay for debounce
    pi.write(DIR, 0)  # Set direction reverse
    generate_ramp(reverse_ramp)  # Move back using ramp

except KeyboardInterrupt:
    print("\nCtrl-C pressed. Stopping PIGPIO and exiting...")
finally:
    pi.stop()
