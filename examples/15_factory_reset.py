"""
Reset an ST3215 servo to factory settings.

After reset the servo reboots briefly. This example waits for it to
come back online and confirms it responds to a ping.

NOTE: Factory reset restores default ID (1) and baudrate (1,000,000).
"""

import os
import time

from python_st3215 import ST3215

PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

with ST3215(PORT) as controller:
    servo = controller.wrap_servo(1)

    print("Sending factory reset command...")
    servo.reset()
    print("Reset command sent. Waiting for servo to reboot...")

    timeout = 5.0
    start = time.time()
    while time.time() - start < timeout:
        try:
            if servo.ping():
                print("Servo is back online.")
                break
        except Exception:
            pass
        time.sleep(0.2)
    else:
        print("Timeout: servo did not come back online within 5 seconds.")
