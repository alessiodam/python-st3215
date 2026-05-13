"""
Wait for servo to complete movement before proceeding.
"""

import os
import time

from python_st3215 import ST3215


def wait_for_stop(servo, timeout=5.0):
    """Wait until servo stops moving or timeout expires."""
    # Brief delay so the servo has time to set the moving flag before we poll
    time.sleep(0.05)
    start_time = time.time()
    while servo.sram.is_moving():
        if time.time() - start_time > timeout:
            print("Timeout!")
            return False
        time.sleep(0.05)
    return True


PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

with ST3215(PORT) as controller:
    servo = controller.wrap_servo(1)
    servo.sram.torque_enable()
    servo.sram.write_acceleration(30)

    print("Moving to 1000 and waiting...")
    servo.sram.write_target_location(1000)
    wait_for_stop(servo)
    print("Arrived!")

    print("Moving to 3000 and waiting...")
    servo.sram.write_target_location(3000)
    wait_for_stop(servo)
    print("Arrived!")

    print("Moving to center and waiting...")
    servo.sram.write_target_location(2048)
    wait_for_stop(servo)
    print("Arrived!")

    servo.sram.torque_disable()
