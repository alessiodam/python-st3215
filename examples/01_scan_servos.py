"""
Scan for all servos on the bus and display their information.
"""

import os

from python_st3215 import ST3215

controller = ST3215(os.environ.get("ST3215_PORT", "/dev/ttyUSB0"))

try:
    print("Scanning for servos...\n")
    servos = controller.list_servos()

    if not servos:
        print("No servos found!")
    else:
        print(f"Found {len(servos)} servo(s)\n")
        print("=" * 80)

        for servo_id in servos:
            servo = controller.wrap_servo(servo_id)

            print(f"\nServo ID: {servo_id}")
            print(
                f"  Firmware: v{servo.eeprom.read_firmware_major_version()}.{servo.eeprom.read_firmware_minor_version()}"
            )
            print(f"  Position: {servo.sram.read_current_location()}")
            print(f"  Temperature: {servo.sram.read_current_temperature()}°C")
            print(f"  Voltage: {servo.sram.read_current_voltage() / 10:.1f}V")
            print(
                f"  Min/Max Angle: {servo.eeprom.read_min_angle_limit()} / {servo.eeprom.read_max_angle_limit()}"
            )

            mode = servo.eeprom.read_operating_mode()
            mode_names = {0: "Position", 1: "Constant Speed", 2: "PWM", 3: "Stepper"}
            print(f"  Operating Mode: {mode_names.get(mode, 'Unknown')}")

        print("\n" + "=" * 80)
finally:
    controller.close()
