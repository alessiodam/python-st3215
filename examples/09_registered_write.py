"""
Use registered write to prepare multiple servos, then execute simultaneously.
"""

import os
import time
from python_st3215 import ST3215

controller = ST3215(os.environ.get("ST3215_PORT", "/dev/ttyUSB0"))

try:
    servos = controller.list_servos()

    if len(servos) < 2:
        print("This example requires at least 2 servos")
    else:
        servo_objects = [controller.wrap_servo(sid) for sid in servos[:2]]

        for servo in servo_objects:
            servo.sram.torque_enable()
            servo.sram.write_acceleration(50)

        print("Preparing movements with registered write...")
        servo_objects[0].sram.write_target_location(1000, reg=True)
        servo_objects[1].sram.write_target_location(3000, reg=True)

        print("Executing all movements simultaneously!")
        controller.broadcast.action()
        time.sleep(2)

        print("Preparing opposite movements...")
        servo_objects[0].sram.write_target_location(3000, reg=True)
        servo_objects[1].sram.write_target_location(1000, reg=True)

        print("Executing!")
        controller.broadcast.action()
        time.sleep(2)

        for servo in servo_objects:
            servo.sram.torque_disable()
finally:
    controller.close()
