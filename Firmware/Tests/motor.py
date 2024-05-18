import pigpio
import time

# Define GPIO pins for the stepper motor
STEP_PIN = 21
DIR_PIN = 20
pi = pigpio.pi()
pi.set_mode(STEP_PIN, pigpio.OUTPUT)
pi.set_mode(DIR_PIN, pigpio.OUTPUT)

def move_motor(start_frequency, final_frequency, steps, dir=1, run_time=None):
    """Generate ramp waveforms from start to final frequency.
    
    Parameters:
    - start_frequency: Starting frequency of the ramp.
    - final_frequency: Ending frequency of the ramp.
    - steps: Number of steps in the ramp.
    - dir: Direction to move the motor (0 or 1).
    - run_time: Time in seconds to run the motor at final frequency, None for indefinite run.
    """
    if not pi.connected:
        print("Error connecting to pigpio daemon. Is the daemon running?")
        return

    pi.wave_clear()  # clear existing waves
    pi.write(DIR_PIN, dir)

    # Calculate frequency increments
    frequency_step = (final_frequency - start_frequency) / steps
    current_frequency = start_frequency

    wid = []

    for _ in range(steps):
        micros = int(500000 / current_frequency)  # microseconds for half a step
        wf = [
            pigpio.pulse(1 << STEP_PIN, 0, micros),
            pigpio.pulse(0, 1 << STEP_PIN, micros)
        ]
        pi.wave_add_generic(wf)
        wave_id = pi.wave_create()
        wid.append(wave_id)  # Append the new wave ID to the list
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

def stop_motor():
    """Stop any running waveforms and clean up."""
    global last_wave_ids
    pi.wave_tx_stop()  # Stop any waveform transmission
    if last_wave_ids is not None:
        for wave_id in last_wave_ids:
            pi.wave_delete(wave_id)  # Clean up each waveform individually
    last_wave_ids = None

# Example usage:
if not pi.connected:
    print("Error connecting to pigpio daemon. Is the daemon running?")
else:
    try:
        move_motor(100, 2000, 50, 1, None)
        time.sleep(30)
        move_motor(2000, 500, 50, 1, None)
        time.sleep(20)
    finally:
        stop_motor()
        pi.stop()  # Properly close the connection to the pigpio daemon
