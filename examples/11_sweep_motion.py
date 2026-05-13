"""
Create a smooth sweeping motion between two positions.
"""

import os
import time

from python_st3215 import ST3215

PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

with ST3215(PORT) as controller:
    servo = controller.wrap_servo(1)
    servo.sram.torque_enable()
    servo.sram.write_acceleration(30)

    min_pos = 1000
    max_pos = 3000

    print("Sweeping back and forth.  Press Ctrl+C to exit.")

    try:
        while True:
            servo.sram.write_target_location(max_pos)
            time.sleep(1.5)
            servo.sram.write_target_location(min_pos)
            time.sleep(1.5)
    except KeyboardInterrupt:
        print("\nStopped.")
        servo.sram.write_target_location(2048)
        time.sleep(1)
        servo.sram.torque_disable()
