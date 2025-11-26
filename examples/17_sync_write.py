"""
Use SYNC WRITE to control multiple servos simultaneously.
This is more efficient than writing to each servo individually.
"""

import os
import time
from python_st3215 import ST3215

controller = ST3215(os.environ.get("ST3215_PORT", "/dev/ttyUSB0"))

try:
    print("Scanning for servos...")
    servo_ids = controller.list_servos()
    if not servo_ids:
        print("No servos found!")
        exit(1)
    print(f"Found {len(servo_ids)} servo(s): {servo_ids}")

    servos = []
    for servo_id in servo_ids:
        servo = controller.wrap_servo(servo_id)
        servos.append(servo)
        print(f"Connected to servo {servo_id}")

    for servo in servos:
        servo.sram.torque_enable()

    print("\nSetting acceleration for all servos using SYNC WRITE...")
    acceleration_data = {servo.id: 50 for servo in servos}
    controller.broadcast.sram.sync_write_acceleration(acceleration_data)
    time.sleep(0.5)

    print("Moving all servos to position 2048 simultaneously...")
    target_positions = {servo.id: 2048 for servo in servos}
    controller.broadcast.sram.sync_write_target_location(target_positions)
    time.sleep(2)

    print("Moving servos to different positions...")
    target_positions = {}
    for i, servo in enumerate(servos):
        target_positions[servo.id] = 1000 + (i * 500)
    controller.broadcast.sram.sync_write_target_location(target_positions)
    time.sleep(2)

    print("Returning to center position...")
    target_positions = {servo.id: 2048 for servo in servos}
    controller.broadcast.sram.sync_write_target_location(target_positions)
    time.sleep(2)

    for servo in servos:
        servo.sram.torque_disable()

    print("\nDone!")

except KeyboardInterrupt:
    print("\nStopped.")
finally:
    controller.close()
