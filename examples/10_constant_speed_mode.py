"""
Use constant speed mode to make servo rotate continuously.

Operating mode is stored in EEPROM, so the original mode is saved and
restored at the end. Torque must be disabled before switching modes.
"""

import os
import time

from python_st3215 import ST3215

PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

with ST3215(PORT) as controller:
    servo = controller.wrap_servo(1)

    original_mode = servo.eeprom.read_operating_mode()
    print(f"Original operating mode: {original_mode}")

    # Torque must be off before changing operating mode
    servo.sram.torque_disable()

    print("Switching to constant speed mode (mode 1)...")
    servo.eeprom.write_operating_mode(1)
    servo.sram.torque_enable()

    print("Rotating clockwise at speed 500 steps/s...")
    servo.sram.write_running_speed(500)
    time.sleep(3)

    print("Rotating counter-clockwise at speed -500 steps/s...")
    servo.sram.write_running_speed(-500)
    time.sleep(3)

    print("Fast clockwise rotation at 1500 steps/s...")
    servo.sram.write_running_speed(1500)
    time.sleep(2)

    print("Stopping...")
    servo.sram.write_running_speed(0)
    time.sleep(0.5)

    # Torque must be off before changing operating mode
    servo.sram.torque_disable()
    print(f"Restoring original mode ({original_mode})...")
    servo.eeprom.write_operating_mode(original_mode)
