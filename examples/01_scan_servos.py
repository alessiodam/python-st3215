"""
Scan for all servos on the bus and display their information.
"""

import os

from python_st3215 import ST3215

PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

with ST3215(PORT) as controller:
    print("Scanning for servos...\n")
    servos = controller.list_servos()

    if not servos:
        print("No servos found!")
    else:
        print(f"Found {len(servos)} servo(s)\n")
        print("=" * 80)

        mode_names = {0: "Position", 1: "Constant Speed", 2: "PWM", 3: "Stepper"}

        for servo_id in servos:
            servo = controller.wrap_servo(servo_id)

            voltage_raw = servo.sram.read_current_voltage()
            voltage_str = f"{voltage_raw / 10:.1f}V" if voltage_raw is not None else "N/A"

            mode = servo.eeprom.read_operating_mode()

            print(f"\nServo ID: {servo_id}")
            print(
                f"  Firmware: v{servo.eeprom.read_firmware_major_version()}.{servo.eeprom.read_firmware_minor_version()}"
            )
            print(f"  Position: {servo.sram.read_current_location()}")
            print(f"  Temperature: {servo.sram.read_current_temperature()}°C")
            print(f"  Voltage: {voltage_str}")
            print(
                f"  Min/Max Angle: {servo.eeprom.read_min_angle_limit()} / {servo.eeprom.read_max_angle_limit()}"
            )
            print(f"  Operating Mode: {mode_names.get(mode, 'Unknown')}")

        print("\n" + "=" * 80)
