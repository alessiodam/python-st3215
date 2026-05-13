"""
Read and display current servo position in real-time.
"""

import os
import time

from python_st3215 import ST3215

PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

with ST3215(PORT) as controller:
    servo = controller.wrap_servo(1)
    servo.sram.torque_disable()
    print("Manually move the servo.  Press Ctrl+C to exit.")

    try:
        while True:
            position = servo.sram.read_current_location()
            speed = servo.sram.read_current_speed()
            load = servo.sram.read_current_load()

            pos_str = f"{position:5d}" if position is not None else "  N/A"
            spd_str = f"{speed:5d}" if speed is not None else "  N/A"
            load_str = f"{load:4d}" if load is not None else " N/A"

            print(f"Position: {pos_str} | Speed: {spd_str} | Load: {load_str}", end="\r")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopped.")
