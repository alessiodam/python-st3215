"""
Connect to an ST3215 controller over a network socket instead of a direct
serial port. Useful when the servo controller is on a remote machine.

Env vars:
  ST3215_URL      Full pyserial URL (takes precedence over host/port)
  ST3215_HOST     IP or hostname of the remote machine (default: st3215-host)
  ST3215_TCP_PORT TCP port on the remote machine (default: 2000)

On the remote host (requires socat and the servo connected to /dev/ttyACM0):
  stty -F /dev/ttyACM0 1000000 raw -echo
  socat TCP4-LISTEN:2000,bind=0.0.0.0,reuseaddr,fork,nodelay FILE:/dev/ttyACM0,b1000000,raw,echo=0
"""

import os
import sys

import serial

from python_st3215 import ST3215

url_env = os.environ.get("ST3215_URL")
host = os.environ.get("ST3215_HOST", "st3215-host")
# ST3215_TCP_PORT is the TCP port on the remote machine, not the local serial device
tcp_port = os.environ.get("ST3215_TCP_PORT", "2000")

if url_env:
    target_url = url_env
elif host:
    target_url = f"socket://{host}:{tcp_port}"
else:
    print("Set ST3215_URL or ST3215_HOST to connect.")
    sys.exit(1)

print(f"Connecting to ST3215 via: {target_url}")

# Network latency is higher than USB, so use a larger timeout
ser = serial.serial_for_url(target_url, timeout=0.02)

with ST3215(ser=ser, read_timeout=0.02) as controller:
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
