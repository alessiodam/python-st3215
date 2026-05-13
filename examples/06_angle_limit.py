"""
Set minimum and maximum angle limits to restrict servo range.

Limits are stored in EEPROM and persist across power cycles.
The servo will clamp movement to stay within the configured limits.
"""

import os
import time

from python_st3215 import ST3215

PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

with ST3215(PORT) as controller:
    servo = controller.wrap_servo(1)

    print("Setting angle limits: 1500 to 2500")
    servo.eeprom.write_min_angle_limit(1500)
    servo.eeprom.write_max_angle_limit(2500)

    servo.sram.torque_enable()
    servo.sram.write_acceleration(50)

    print("Trying to move to 500 (below min limit)...")
    servo.sram.write_target_location(500)
    time.sleep(1)
    print(f"Actual position: {servo.sram.read_current_location()}")

    print("Trying to move to 3500 (above max limit)...")
    servo.sram.write_target_location(3500)
    time.sleep(1)
    print(f"Actual position: {servo.sram.read_current_location()}")

    print("Moving to 2000 (within limits)...")
    servo.sram.write_target_location(2000)
    time.sleep(1)
    print(f"Actual position: {servo.sram.read_current_location()}")

    print("\nRestoring full range (0-4095)...")
    servo.eeprom.write_min_angle_limit(0)
    servo.eeprom.write_max_angle_limit(4095)

    servo.sram.torque_disable()
