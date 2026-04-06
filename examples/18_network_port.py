"""
Scan for all servos on the bus and display their information.
Supports either a direct serial device (e.g. /dev/ttyUSB0) or a network
socket URL (e.g. socket://<IP>:<PORT>).

Env vars:
- ST3215_URL   : full pyserial URL (takes precedence)
- ST3215_HOST  : IP/hostname for socket connection (default: 100.122.96.71)
- ST3215_PORT  : TCP port for socket connection (default: 2000)
- ST3215_DEV   : fallback serial device (default: /dev/ttyUSB0)

Run this on the host connected to the ST3215 driver board (make sure you have socat installed and set up udev rules for /dev/ttyACM0):
    `stty -F /dev/ttyACM0 1000000 raw -echo && socat -d -d TCP4-LISTEN:2000,bind=0.0.0.0,reuseaddr,fork,nodelay FILE:/dev/ttyACM0,b1000000,raw,echo=0`
"""

import os
import sys

import serial

from python_st3215 import ST3215

url_env = os.environ.get("ST3215_URL")
host = os.environ.get("ST3215_HOST", "st3215-host")
port = os.environ.get("ST3215_PORT", "2000")

if url_env:
    TARGET_URL = url_env
elif host and port:
    TARGET_URL = f"socket://{host}:{port}"
else:
    sys.exit(1)

print(f"Connecting to ST3215 via: {TARGET_URL}")

ser = serial.serial_for_url(TARGET_URL, timeout=0.02)
controller = ST3215(ser=ser, read_timeout=0.02)

try:
    print("Scanning for servos...\n")
    servos = controller.list_servos(timeout=0.02)

    if not servos:
        print("No servos found!")
    else:
        print(f"Found {len(servos)} servo(s)\n")
        print("=" * 80)

        mode_names = {0: "Position", 1: "Constant Speed", 2: "PWM", 3: "Stepper"}

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
            print(f"  Operating Mode: {mode_names.get(mode, 'Unknown')}")

        print("\n" + "=" * 80)
finally:
    controller.close()
