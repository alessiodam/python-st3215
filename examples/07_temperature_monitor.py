"""
Monitor servo temperature, voltage, and current during operation.
"""

import os
import time

from python_st3215 import ST3215

PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

with ST3215(PORT) as controller:
    servo = controller.wrap_servo(1)
    servo.sram.torque_enable()
    servo.sram.write_acceleration(50)

    print("Monitoring temperature, voltage, and current.  Press Ctrl+C to exit.")
    print("Moving servo continuously to generate load...\n")

    positions = [1000, 3000]
    pos_index = 0

    try:
        while True:
            temp = servo.sram.read_current_temperature()
            voltage_raw = servo.sram.read_current_voltage()
            current_raw = servo.sram.read_current_current()

            # voltage unit: 0.1V; current unit: 6.5mA
            voltage_str = f"{voltage_raw / 10:4.1f}V" if voltage_raw is not None else " N/A "
            current_str = f"{current_raw * 6.5:6.1f}mA" if current_raw is not None else "   N/A  "
            temp_str = f"{temp:2d}°C" if temp is not None else "N/A "

            print(
                f"Temp: {temp_str} | Voltage: {voltage_str} | Current: {current_str}",
                end="\r",
            )

            servo.sram.write_target_location(positions[pos_index])
            pos_index = (pos_index + 1) % 2
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopped.")
        servo.sram.torque_disable()
