import time
import pigpio

# GPIO PINS
STEP_PIN = 21
DIR_PIN = 20

def move_motor(pi, STEP_PIN, DIR_PIN, start_frequency=100, final_frequency=5000, steps=100, run_time=None):
    global wave_ids

    pi.write(DIR_PIN, pi.read(1))

    start_delay = 1 / start_frequency
    final_delay = 1 / final_frequency

    # Determine ramp direction
    ramp_up = start_frequency < final_frequency

    # Calculate ramp steps
    if ramp_up:
        step_size = (final_delay - start_delay) / steps
    else:
        step_size = (start_delay - final_delay) / steps

    # Create waveform for final speed
    wf = [
        pigpio.pulse(1 << STEP_PIN, 0, int(final_delay * 1e6)),
        pigpio.pulse(0, 1 << STEP_PIN, int(final_delay * 1e6))
    ]
    pi.wave_add_generic(wf)
    wid0 = pi.wave_create()

    # Build initial ramp
    wf = []
    delay = start_delay
    for _ in range(steps):
        wf.append(pigpio.pulse(1 << STEP_PIN, 0, int(delay * 1e6)))
        wf.append(pigpio.pulse(0, 1 << STEP_PIN, int(delay * 1e6)))
        if ramp_up:
            delay += step_size
        else:
            delay -= step_size

    pi.wave_add_generic(wf)
    wid1 = pi.wave_create()

    # Send ramp, then repeat final rate
    pi.wave_send_once(wid1)
    offset = pi.wave_get_micros()  # Duration of the ramp in microseconds
    time.sleep(float(offset) / 1e6)  # Wait for ramp to complete

    pi.wave_send_repeat(wid0)  # Start repeating final speed waveform

    # If run_time is specified, run for that duration then stop, otherwise run indefinitely
    if run_time is not None:
        time.sleep(run_time)  # Run motor at final speed for specified time
        pi.wave_tx_stop()  # Stop waveform after run_time
        pi.wave_delete(wid0)  # Delete waveform
        pi.wave_delete(wid1)  # Delete waveform
    else:
        # Leaving the motor running, cleanup will need to be handled externally
        wave_ids.extend([wid0, wid1])
        pass

def stop_motor(pi):
    global wave_ids
    pi.wave_tx_stop()  # Stop any waveform transmission
    for wid in wave_ids:
        pi.wave_delete(wid)  # Clean up waveforms
    wave_ids = []  # Clear the list after cleanup

pi = pigpio.pi()
if not pi.connected:
    print("Error connecting to pigpio daemon. Is the daemon running?")

pi.set_mode(STEP_PIN, pigpio.OUTPUT)
pi.set_mode(DIR_PIN, pigpio.OUTPUT)
pi.wave_clear()

try:
    move_motor(pi, STEP_PIN, DIR_PIN, 0, 500, 50, None)
except KeyboardInterrupt:
    print("interrupted")
finally:
    pi.stop()