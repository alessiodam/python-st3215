"""
Control servo movement speed using the acceleration parameter.

Acceleration unit: 100 steps/s² per unit (e.g. 10 = 1000 steps/s²).
Lower values = slower ramp-up, smoother motion.
"""

import os
import time

from python_st3215 import ST3215

PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

with ST3215(PORT) as controller:
    servo = controller.wrap_servo(1)
    servo.sram.torque_enable()

    print("Slow movement (acceleration = 10 → 1000 steps/s²)...")
    servo.sram.write_acceleration(10)
    servo.sram.write_target_location(3000)
    time.sleep(3)

    print("Medium movement (acceleration = 50 → 5000 steps/s²)...")
    servo.sram.write_acceleration(50)
    servo.sram.write_target_location(1000)
    time.sleep(2)

    print("Fast movement (acceleration = 254 → 25400 steps/s²)...")
    servo.sram.write_acceleration(254)
    servo.sram.write_target_location(2048)
    time.sleep(1)

    servo.sram.torque_disable()
