"""
Use position correction to offset the zero position.

Position correction is stored in EEPROM and shifts all position readings
and targets by the given number of steps (-2047 to +2047).
The original correction is saved and restored at the end.
"""

import os
import time

from python_st3215 import ST3215

PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

with ST3215(PORT) as controller:
    servo = controller.wrap_servo(1)

    original_correction = servo.eeprom.read_position_correction()
    print(f"Original position correction: {original_correction}")

    servo.sram.torque_enable()
    servo.sram.write_acceleration(50)

    print("\nMoving to 2048 with no correction...")
    servo.eeprom.write_position_correction(0)
    servo.sram.write_target_location(2048)
    time.sleep(1.5)
    print(f"Actual position: {servo.sram.read_current_location()}")

    print("\nApplying +500 step correction...")
    servo.eeprom.write_position_correction(500)
    servo.sram.write_target_location(2048)
    time.sleep(1.5)
    print(f"Actual position: {servo.sram.read_current_location()}")

    print("\nApplying -500 step correction...")
    servo.eeprom.write_position_correction(-500)
    servo.sram.write_target_location(2048)
    time.sleep(1.5)
    print(f"Actual position: {servo.sram.read_current_location()}")

    print(f"\nRestoring original correction ({original_correction})...")
    servo.eeprom.write_position_correction(original_correction)

    servo.sram.torque_disable()
