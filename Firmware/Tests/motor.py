import pigpio
import time

STEP_PIN = 21
DIR_PIN = 20
pi = pigpio.pi()
pi.set_mode(STEP_PIN, pigpio.OUTPUT)
pi.set_mode(DIR_PIN, pigpio.OUTPUT)

def generate_ramp(pi, start_frequency, final_frequency, steps, dir=1, run_time=None):
    if not pi.connected:
        print("Error connecting to pigpio daemon. Is the daemon running?")
        return

    pi.wave_clear()
    pi.write(DIR_PIN, dir)

    frequency_step = (final_frequency - start_frequency) / steps
    current_frequency = start_frequency

    wid = []
    wf = []

    for i in range(steps):
        micros = int(500000 / current_frequency)
        wf = [pigpio.pulse(1 << STEP_PIN, 0, micros), pigpio.pulse(0, 1 << STEP_PIN, micros)]
        pi.wave_add_generic(wf)
        wave_id = pi.wave_create()
        if wave_id < 0:
            print("Failed to create wave at step", i)
            return
        wid.append(wave_id)
        current_frequency += frequency_step

    chain = []
    for wave_id in wid:
        chain += [255, 0, wave_id, 255, 1, 1, 0]

    if run_time is None:
        chain += [255, 0, wid[-1]] * 2  # Repeat last waveform indefinitely
    pi.wave_chain(chain)

    if run_time is not None:
        time.sleep(run_time)
        pi.wave_tx_stop()
        for wave_id in wid:
            pi.wave_delete(wave_id)

def move_motor(start_frequency, final_frequency, steps, dir=1, run_time=None):
    """Generate ramp wave forms.
    ramp:  List of [Frequency, Steps]
    """
    pi.wave_clear()     # clear existing waves
    pi.write(DIR_PIN, dir)

    # Calculate frequency increments
    frequency_step = (final_frequency - start_frequency) / steps
    current_frequency = start_frequency

    wid = []
    wf = [-1] * steps

    for i in range(steps):
        micros = int(500000 / current_frequency)  # microseconds for half a step
        wf = [
            pigpio.pulse(1 << STEP_PIN, 0, micros),
            pigpio.pulse(0, 1 << STEP_PIN, micros)
        ]
        pi.wave_add_generic(wf)
        wid[i-1]=pi.wave_create()
        current_frequency += frequency_step  # increment or decrement frequency
    
    # Generate a chain of waves
    chain = []
    for wave_id in wid:
        chain += [255, 0, wave_id, 255, 1, 1, 0]  # Transmit each wave once

    pi.wave_chain(chain)  # Transmit chain

    # Handle run time
    if run_time is not None:
        pi.wave_send_repeat(wid[-1])
        time.sleep(run_time)
        pi.wave_tx_stop()  # Stop waveform transmission
    else:
        # If no run_time specified, repeat the last waveform indefinitely
        pi.wave_send_repeat(wid[-1])

    # Clean up waveforms
    global last_wave_ids
    last_wave_ids = wid  # Store wave IDs globally to allow stopping later

def generate_ramp_author(ramp, start_frequency, final_frequency, steps, dir=1, run_time=None):
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
        wf.append(pigpio.pulse(1 << STEP_PIN, 0, micros))  # pulse on
        wf.append(pigpio.pulse(0, 1 << STEP_PIN, micros))  # pulse off
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

def stop_motor(pi):
    pi.wave_tx_stop()
    pi.wave_clear()

try:
    #generate_ramp(pi, 100, 1000, 50, dir=1, run_time=None)
    # Ramp up
    pi.write(DIR_PIN, 1)
    #generate_ramp_author([[320, 200], [500, 400], [800, 500], [1000, 700], [1600, 900], [2000, 10000]])
    move_motor(100, 2000, 50, 1, None)
    time.sleep(30)  # For demonstration, run the motor then stop
finally:
    stop_motor(pi)
    pi.stop()
