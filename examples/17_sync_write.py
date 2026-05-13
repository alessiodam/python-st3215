"""
Use SYNC WRITE to control multiple servos simultaneously.
More efficient than writing to each servo individually.
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

    # Enable torque on all servos using SYNC WRITE
    controller.broadcast.sram.sync_write_torque_switch({s.id: 1 for s in servo_objects})

    print("\nSetting acceleration for all servos via SYNC WRITE...")
    controller.broadcast.sram.sync_write_acceleration({s.id: 50 for s in servo_objects})
    time.sleep(0.5)

    print("Moving all servos to center (2048) simultaneously...")
    controller.broadcast.sram.sync_write_target_location({s.id: 2048 for s in servo_objects})
    time.sleep(2)

    print("Moving servos to staggered positions...")
    # Spread servos evenly between 1000 and 3000, clamped to valid range
    n = len(servo_objects)
    targets = {}
    for i, servo in enumerate(servo_objects):
        pos = 1000 + int((i / max(n - 1, 1)) * 2000) if n > 1 else 2048
        targets[servo.id] = max(0, min(4095, pos))
    controller.broadcast.sram.sync_write_target_location(targets)
    time.sleep(2)

    print("Returning all servos to center...")
    controller.broadcast.sram.sync_write_target_location({s.id: 2048 for s in servo_objects})
    time.sleep(2)

    # Disable torque on all servos using SYNC WRITE
    controller.broadcast.sram.sync_write_torque_switch({s.id: 0 for s in servo_objects})

    print("\nDone!")
