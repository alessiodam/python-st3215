"""
Use SYNC READ to query multiple servos simultaneously.
More efficient than reading from each servo individually.
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

    for servo_id in servo_ids:
        controller.wrap_servo(servo_id).sram.torque_disable()

    print("\nManually move the servos.  Press Ctrl+C to exit.")
    print("Reading positions, speeds, and loads from all servos simultaneously...\n")

    try:
        while True:
            positions = controller.broadcast.sram.sync_read_current_location(servo_ids)
            speeds = controller.broadcast.sram.sync_read_current_speed(servo_ids)
            loads = controller.broadcast.sram.sync_read_current_load(servo_ids)

            # \033[H\033[J moves cursor to top-left and clears screen for in-place refresh
            print("\033[H\033[J", end="")
            print("=" * 60)
            print(f"{'ID':<6} {'Position':<12} {'Speed':<12} {'Load':<12}")
            print("=" * 60)

            for servo_id in servo_ids:
                pos = positions.get(servo_id)
                spd = speeds.get(servo_id)
                load = loads.get(servo_id)

                pos_str = f"{pos:5d}" if pos is not None else "  N/A"
                spd_str = f"{spd:5d}" if spd is not None else "  N/A"
                load_str = f"{load:4d}" if load is not None else " N/A"

                print(f"{servo_id:<6} {pos_str:<12} {spd_str:<12} {load_str:<12}")

            print("=" * 60)
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\nStopped.")
