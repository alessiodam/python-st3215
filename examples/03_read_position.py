"""
Read and display current servo position in real-time.
"""

import os
import time

from python_st3215 import ST3215

controller = ST3215(os.environ.get("ST3215_PORT", "/dev/ttyUSB0"))

try:
    servo = controller.wrap_servo(1)
    servo.sram.torque_disable()
    print("Manually move the servo.  Press Ctrl+C to exit.")
    while True:
        position = servo.sram.read_current_location()
        speed = servo.sram.read_current_speed()
        load = servo.sram.read_current_load()

        print(
            f"Position: {position:5d} | Speed: {speed:5d} | Load: {load:4d}", end="\r"
        )
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\nStopped.")
finally:
    controller.close()
