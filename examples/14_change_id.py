"""
Change a servo's ID.  USE WITH CAUTION - only one servo should be connected!
"""

import os
from python_st3215 import ST3215

controller = ST3215(os.environ.get("ST3215_PORT", "/dev/ttyUSB0"))

try:
    print("=" * 60)
    print("CHANGE SERVO ID")
    print("=" * 60)
    print("\nWARNING: Only connect ONE servo to avoid ID conflicts!")

    try:
        old_id_input = input("\nEnter CURRENT Servo ID (default 1): ").strip()
        OLD_ID = int(old_id_input) if old_id_input else 1

        new_id_input = input("Enter NEW Servo ID: ").strip()
        if not new_id_input:
            print("New ID is required. Exiting.")
            exit(1)
        NEW_ID = int(new_id_input)
    except ValueError:
        print("Invalid input. Please enter numeric IDs.")
        exit(1)

    print(f"\nThis will change servo ID from {OLD_ID} to {NEW_ID}")

    response = input("\nType 'yes' to continue: ")
    if response.lower() != "yes":
        print("Cancelled.")
    else:
        servo = controller.wrap_servo(OLD_ID)

        print(f"\nCurrent ID: {servo.eeprom.read_id()}")
        print(f"Changing to ID {NEW_ID}...")

        # Unlock EEPROM to allow saving changes
        print("Unlocking EEPROM...")
        servo.sram.unlock()

        print("Writing new ID...")
        servo.eeprom.write_id(NEW_ID)

        # Lock EEPROM again (optional but recommended)
        print("Locking EEPROM...")
        servo.sram.lock()

        print("\nVerifying change...")
        new_servo = controller.wrap_servo(NEW_ID)
        confirmed_id = new_servo.eeprom.read_id()

        if confirmed_id == NEW_ID:
            print(f"✓ Successfully changed to ID {NEW_ID}")
        else:
            print(f"✗ Failed to change ID (read: {confirmed_id})")
finally:
    controller.close()
