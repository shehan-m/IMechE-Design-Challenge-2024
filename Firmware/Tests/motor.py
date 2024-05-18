import pigpio
import time

# Define GPIO pins for the stepper motor
STEP_PIN = 21
DIR_PIN = 20
pi = pigpio.pi()
pi.set_mode(STEP_PIN, pigpio.OUTPUT)
pi.set_mode(DIR_PIN, pigpio.OUTPUT)

def move_motor(start_frequency, final_frequency, steps, dir=1, run_time=None):
    global last_wave_ids  # Declare global at the start of the function

    if not pi.connected:
        print("Error connecting to pigpio daemon. Is the daemon running?")
        return

    pi.wave_clear()
    pi.write(DIR_PIN, dir)

    # Exponential ramp calculation for smoother acceleration
    base = 1.05  # Smaller base for finer control
    frequency_steps = [(base**i - 1) * (final_frequency - start_frequency) / (base**steps - 1) for i in range(steps)]
    current_frequency = start_frequency

    wid = []

    for i in range(steps):
        micros = int(500000 / (current_frequency + frequency_steps[i]))
        wf = [
            pigpio.pulse(1 << STEP_PIN, 0, micros),
            pigpio.pulse(0, 1 << STEP_PIN, micros)
        ]
        pi.wave_add_generic(wf)
        wave_id = pi.wave_create()
        wid.append(wave_id)  # Append the new wave ID to the list
        current_frequency += frequency_steps[i]
    
    # Generate a chain of waves with variable hold times
    chain = []
    for i, wave_id in enumerate(wid):
        hold_time = max(int(100 * (steps - i) / steps), 1)  # Dynamic hold time
        chain += [255, 0, wave_id, 255, 1, hold_time, 0]  # Apply dynamic hold time

    pi.wave_chain(chain)

    if run_time is not None:
        pi.wave_send_repeat(wid[-1])
        time.sleep(run_time)
        pi.wave_tx_stop()
    else:
        pi.wave_send_repeat(wid[-1])

    last_wave_ids = wid

def stop_motor():
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
