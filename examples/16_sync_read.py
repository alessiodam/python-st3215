"""
Use SYNC READ to query multiple servos simultaneously.
This is more efficient than reading from each servo individually.
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
        servo.sram.torque_disable()

    print("\nManually move the servos.  Press Ctrl+C to exit.")
    print("Reading positions, speeds, and loads from all servos simultaneously.. .\n")

    active_servo_ids = [servo.id for servo in servos]

    while True:
        positions = controller.broadcast.sram.sync_read_current_location(
            active_servo_ids
        )
        speeds = controller.broadcast.sram.sync_read_current_speed(active_servo_ids)
        loads = controller.broadcast.sram.sync_read_current_load(active_servo_ids)

        print("\033[H\033[J")
        print("=" * 60)
        print(f"{'ID':<6} {'Position':<12} {'Speed':<12} {'Load':<12}")
        print("=" * 60)

        for servo_id in active_servo_ids:
            pos = positions.get(servo_id, "N/A")
            spd = speeds.get(servo_id, "N/A")
            load = loads.get(servo_id, "N/A")

            pos_str = f"{pos:5d}" if isinstance(pos, int) else str(pos)
            spd_str = f"{spd:5d}" if isinstance(spd, int) else str(spd)
            load_str = f"{load:4d}" if isinstance(load, int) else str(load)

            print(f"{servo_id:<6} {pos_str:<12} {spd_str:<12} {load_str:<12}")

        print("=" * 60)
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n\nStopped.")
finally:
    controller.close()
