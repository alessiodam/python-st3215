"""
Demonstrate torque limiting to reduce servo force.

Torque limit unit: 0.1% per unit (0-1000, where 1000 = 100%).
This affects SRAM only; it resets to max_torque (EEPROM) on power-up.
"""

import os
import time

from python_st3215 import ST3215

PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

with ST3215(PORT) as controller:
    servo = controller.wrap_servo(1)
    servo.sram.torque_enable()

    print("Full torque (1000 = 100%)...")
    servo.sram.write_torque_limit(1000)
    servo.sram.write_target_location(3000)
    time.sleep(1.5)

    print("Half torque (500 = 50%) - try resisting the movement...")
    servo.sram.write_torque_limit(500)
    servo.sram.write_target_location(1000)
    time.sleep(1.5)

    print("Low torque (200 = 20%) - very easy to resist...")
    servo.sram.write_torque_limit(200)
    servo.sram.write_target_location(3000)
    time.sleep(1.5)

    # Restore full torque before disabling so the next power-on is predictable
    servo.sram.write_torque_limit(1000)
    servo.sram.torque_disable()
