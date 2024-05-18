import pigpio
import time

# Define GPIO pins for the stepper motor
STEP_PIN = 21
DIR_PIN = 20
pi = pigpio.pi()
pi.set_mode(STEP_PIN, pigpio.OUTPUT)
pi.set_mode(DIR_PIN, pigpio.OUTPUT)

def generate_ramp(pi, start_frequency, final_frequency, steps, dir=1, run_time=None):
    """Generate and execute a ramp waveforms with automatic ramp up or down.
    
    Parameters:
    - pi: The pigpio instance.
    - start_frequency: Starting frequency of the ramp.
    - final_frequency: Ending frequency of the ramp.
    - steps: Number of steps in the ramp.
    - dir: Direction to move the motor (0 or 1).
    - run_time: Time in seconds to run the motor at final frequency, None for indefinite run.
    """
    pi.wave_clear()  # clear existing waves
    pi.write(DIR_PIN, dir)  # set motor direction

    # Calculate frequency increments
    frequency_step = (final_frequency - start_frequency) / steps
    current_frequency = start_frequency

    wid = []
    wf = []

    for _ in range(steps):
        micros = int(500000 / current_frequency)  # microseconds for half a step
        wf = [
            pigpio.pulse(1 << STEP_PIN, 0, micros),
            pigpio.pulse(0, 1 << STEP_PIN, micros)
        ]
        pi.wave_add_generic(wf)
        wid.append(pi.wave_create())
        current_frequency += frequency_step  # increment or decrement frequency

    # Chain waves
    chain = []
    for i in range(steps):
        chain += [255, 0, wid[i], 255, 1, 1, 0]  # Transmit each wave once

    # Continue the last waveform indefinitely if no run_time specified
    if run_time is None:
        chain += [255, 0, wid[-1]] * 2  # Repeat last waveform
    pi.wave_chain(chain)  # transmit chain

    if run_time is not None:
        time.sleep(run_time)
        pi.wave_tx_stop()  # stop waveform transmission
    # Clean up after specified run time or if a stop function is called later
    global last_wid
    last_wid = wid

def stop_motor(pi):
    """Stop any running waveforms and clean up."""
    global last_wid
    pi.wave_tx_stop()  # Stop any waveform transmission
    for wave_id in last_wid:
        pi.wave_delete(wave_id)  # Clean up waveforms
    last_wid = []

if not pi.connected:
    print("Error connecting to pigpio daemon. Is the daemon running?")
else:
    try:
        # Set parameters for the ramp
        start_freq = 100 # in Hz
        final_freq = 1000 # in Hz
        ramp_steps = 50 # number of steps in the ramp
        # Generate and execute the ramp
        generate_ramp(pi, start_freq, final_freq, ramp_steps, dir=1, run_time=None)

        # For demonstration, let's assume we want to stop after 30 seconds
        time.sleep(30)
        stop_motor(pi)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        pi.stop()  # Properly close the connection to the pigpio daemon