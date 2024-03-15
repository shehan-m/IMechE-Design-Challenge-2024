import pigpio
from time import sleep

# Initialize pigpio and motor pins
pi = pigpio.pi()
DIR = 20     # Direction GPIO Pin
STEP = 21    # Step GPIO Pin
pi.set_mode(DIR, pigpio.OUTPUT)
pi.set_mode(STEP, pigpio.OUTPUT)

def generate_ramp(ramp):
    """Generate ramp wave forms.
    ramp:  List of [Frequency, Steps]
    """
    pi.wave_clear()     # clear existing waves
    length = len(ramp)  # number of ramp levels
    wid = [-1] * length

    # Generate a wave per ramp level
    for i in range(length):
        frequency = ramp[i][0]
        micros = int(500000 / frequency)
        wf = []
        wf.append(pigpio.pulse(1 << STEP, 0, micros))  # pulse on
        wf.append(pigpio.pulse(0, 1 << STEP, micros))  # pulse off
        pi.wave_add_generic(wf)
        wid[i] = pi.wave_create()

    # Generate a chain of waves
    chain = []
    for i in range(length):
        steps = ramp[i][1]
        x = steps & 255
        y = steps >> 8
        chain += [255, 0, wid[i], 255, 1, x, y]

    pi.wave_chain(chain)  # Transmit chain.

# Example ramp: Start slow, speed up, then slow down
ramp = [[100, 50], [200, 100], [400, 200], [200, 100], [100, 50]]

# Set direction
pi.write(DIR, 1)  # Set to 1 for one direction or 0 for the other

# Generate and transmit the ramp
generate_ramp(ramp)

# Wait for chain to complete
while pi.wave_tx_busy():
    sleep(0.1)

# Clean up
pi.wave_clear()
pi.stop()

