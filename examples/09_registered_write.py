"""
Use registered write to prepare multiple servos, then execute simultaneously.

REG_WRITE stages the command in each servo's buffer without executing it.
ACTION then fires all buffered commands at once across all servos.
"""

import os
import sys
import time

from python_st3215 import ST3215

PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

with ST3215(PORT) as controller:
    print("Scanning for servos...")
    servo_ids = controller.list_servos()
    if not servo_ids:
        print("No servos found!")
        sys.exit(1)
    print(f"Found {len(servo_ids)} servo(s): {servo_ids}")

    servo_objects = [controller.wrap_servo(sid) for sid in servo_ids]

    for servo in servo_objects:
        servo.sram.torque_enable()
        servo.sram.write_acceleration(50)

    print("\nPreparing movements with registered write...")
    for i, servo in enumerate(servo_objects):
        target = 1000 if i % 2 == 0 else 3000
        servo.sram.write_target_location(target, reg=True)

    print("Executing all movements simultaneously!")
    controller.broadcast.action()
    time.sleep(2)

    print("Preparing opposite movements...")
    for i, servo in enumerate(servo_objects):
        target = 3000 if i % 2 == 0 else 1000
        servo.sram.write_target_location(target, reg=True)

    print("Executing!")
    controller.broadcast.action()
    time.sleep(2)

    for servo in servo_objects:
        servo.sram.torque_disable()
