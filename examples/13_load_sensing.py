"""
Read servo load to detect when it is being blocked or resisted.

Load unit: 0.1% per unit (0-1000, where 1000 = 100% duty cycle).
"""

import os
import time

from python_st3215 import ST3215

PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

with ST3215(PORT) as controller:
    servo = controller.wrap_servo(1)
    servo.sram.torque_enable()
    servo.sram.write_acceleration(50)

    print("Moving servo.  Try to resist the movement to see load change.")
    print("Press Ctrl+C to exit.\n")

    positions = [1000, 3000]
    pos_index = 0

    try:
        while True:
            servo.sram.write_target_location(positions[pos_index])
            pos_index = (pos_index + 1) % 2

            for _ in range(15):
                load = servo.sram.read_current_load()
                position = servo.sram.read_current_location()

                if load is not None:
                    load_percent = load / 10
                    # Clamp bar to [0, 50] in case load briefly exceeds 100%
                    bar_length = max(0, min(50, int(load_percent / 2)))
                    bar = "█" * bar_length + "░" * (50 - bar_length)
                    load_str = f"{load_percent:5.1f}%"
                else:
                    bar = "░" * 50
                    load_str = "  N/A "

                pos_str = f"{position:4d}" if position is not None else " N/A"
                print(f"Pos: {pos_str} | Load: {load_str} [{bar}]\033[K", end="\r")
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("\nStopped.")
        servo.sram.torque_disable()
