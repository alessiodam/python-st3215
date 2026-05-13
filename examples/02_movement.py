"""
Simple position control - move servo to different positions.
"""

import os
import time

from python_st3215 import ST3215

PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

with ST3215(PORT) as controller:
    servo = controller.wrap_servo(1)
    servo.sram.torque_enable()

    print("Moving to position 1000...")
    servo.sram.write_target_location(1000)
    time.sleep(1)

    print("Moving to position 3000...")
    servo.sram.write_target_location(3000)
    time.sleep(1)

    print("Moving to center (2048)...")
    servo.sram.write_target_location(2048)
    time.sleep(1)

    servo.sram.torque_disable()
