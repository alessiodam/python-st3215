"""
Change a servo's ID.

WARNING: Only one servo should be connected to avoid ID conflicts.
The new ID is written to EEPROM and is permanent across power cycles.
"""

import os
import sys

from python_st3215 import ST3215

PORT = os.environ.get("ST3215_PORT", "/dev/ttyUSB0")

print("=" * 60)
print("CHANGE SERVO ID")
print("=" * 60)
print("\nWARNING: Only connect ONE servo to avoid ID conflicts!")

try:
    old_id_input = input("\nEnter CURRENT Servo ID (default 1): ").strip()
    OLD_ID = int(old_id_input) if old_id_input else 1

    new_id_input = input("Enter NEW Servo ID (0-253): ").strip()
    if not new_id_input:
        print("New ID is required. Exiting.")
        sys.exit(1)
    NEW_ID = int(new_id_input)
except ValueError:
    print("Invalid input. Please enter numeric IDs.")
    sys.exit(1)

if not (0 <= NEW_ID <= 253):
    print(f"Invalid ID {NEW_ID}. Must be 0-253.")
    sys.exit(1)

print(f"\nThis will change servo ID from {OLD_ID} to {NEW_ID}")
response = input("\nType 'yes' to continue: ")
if response.lower() != "yes":
    print("Cancelled.")
    sys.exit(0)

with ST3215(PORT) as controller:
    servo = controller.wrap_servo(OLD_ID)
    print(f"\nCurrent ID confirmed: {servo.eeprom.read_id()}")

    # EEPROM is unlocked by default; unlock explicitly to be safe
    servo.sram.unlock()
    print(f"Writing new ID {NEW_ID}...")
    servo.eeprom.write_id(NEW_ID)
    servo.sram.lock()

    print("Verifying change...")
    new_servo = controller.wrap_servo(NEW_ID)
    confirmed_id = new_servo.eeprom.read_id()

    if confirmed_id == NEW_ID:
        print(f"Successfully changed to ID {NEW_ID}")
    else:
        print(f"Failed to change ID (read back: {confirmed_id})")
