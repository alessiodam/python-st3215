"""
Monitor servo temperature and voltage during operation.
"""

import os
import time

from python_st3215 import ST3215

controller = ST3215(os.environ.get("ST3215_PORT", "/dev/ttyUSB0"))

try:
    servo = controller.wrap_servo(1)
    servo.sram.torque_enable()
    servo.sram.write_acceleration(50)

    print("Monitoring temperature and voltage.  Press Ctrl+C to exit.")
    print("Moving servo continuously to generate heat.. .\n")

    positions = [1000, 3000]
    pos_index = 0

    while True:
        temp = servo.sram.read_current_temperature()
        voltage = servo.sram.read_current_voltage() / 10
        current = servo.sram.read_current_current() * 6.5

        print(
            f"Temp: {temp:2d}°C | Voltage: {voltage:4.1f}V | Current: {current:6.1f}mA",
            end="\r",
        )

        servo.sram.write_target_location(positions[pos_index])
        pos_index = (pos_index + 1) % 2
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopped.")
    servo.sram.torque_disable()

finally:
    controller.close()
