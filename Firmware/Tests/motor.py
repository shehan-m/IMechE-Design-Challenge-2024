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

def stop_motor(pi):
    pi.wave_tx_stop()
    pi.wave_clear()

try:
    generate_ramp(pi, 100, 1000, 50, dir=1, run_time=None)
    time.sleep(30)  # For demonstration, run the motor then stop
finally:
    stop_motor(pi)
    pi.stop()
