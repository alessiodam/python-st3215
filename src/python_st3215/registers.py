from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .errors import BroadcastOperationError, ST3215Error

if TYPE_CHECKING:
    from .servo import Servo

from .decorators import (
    decode_signed_word,
    encode_signed_word,
    encode_unsigned_word,
    validate_value_range,
)


def read_byte(servo: "Servo", address: int) -> Optional[int]:
    """Read a single byte from memory."""
    return servo._read_memory(address, 1)


def read_word(servo: "Servo", address: int, signed: bool = False) -> Optional[int]:
    """Read a 16-bit word from memory."""
    raw = servo._read_memory(address, 2)
    if raw is None:
        return None
    if signed:
        return decode_signed_word(raw)
    return raw


def write_byte(
    servo: "Servo", address: int, value: int, reg: bool = False
) -> dict[str, object] | None:
    """Write a single byte to memory."""
    write_fn = servo._reg_write_memory if reg else servo._write_memory
    return write_fn(address, [value & 0xFF])


def write_word(
    servo: "Servo", address: int, value: int, signed: bool = False, reg: bool = False
) -> dict[str, object] | None:
    """Write a 16-bit word to memory."""
    if signed:
        low, high = encode_signed_word(value)
    else:
        low, high = encode_unsigned_word(value)
    write_fn = servo._reg_write_memory if reg else servo._write_memory
    return write_fn(address, [low, high])


class EEPROMRegisters:
    def __init__(self, servo: "Servo") -> None:
        self.servo = servo

    def read_firmware_major_version(self) -> Optional[int]:
        """
        Read the firmware major version number.

        Returns:
            int: Major version number, or None if read fails
        """
        return read_byte(self.servo, 0x00)

    def read_firmware_minor_version(self) -> Optional[int]:
        """
        Read the firmware minor version number.

        Returns:
            int: Minor version number, or None if read fails
        """
        return read_byte(self.servo, 0x01)

    def read_servo_main_version(self) -> Optional[int]:
        """
        Read the servo main version number.

        Returns:
            int: Main version number, or None if read fails
        """
        return read_byte(self.servo, 0x03)

    def read_servo_version(self) -> Optional[int]:
        """
        Read the servo version number.

        Returns:
            int: Servo version number, or None if read fails
        """
        return read_byte(self.servo, 0x04)

    def read_id(self) -> Optional[int]:
        """
        Read the servo ID.

        Returns:
            int: Servo ID (0-253), or None if read fails
        """
        return read_byte(self.servo, 0x05)

    @validate_value_range(0, 253)
    def write_id(self, value: int, reg: bool = False) -> dict[str, object] | None:
        """
        Set the servo ID.

        Args:
            value (int): Servo ID (0-253).  254 is reserved for broadcast.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x05, value, reg)

    def read_baudrate(self) -> Optional[int]:
        """
        Read the baud rate setting.

        Returns:
            int: Baud rate code (0-7), where:
                 0 = 1,000,000 baud
                 1 = 500,000 baud
                 2 = 250,000 baud
                 3 = 115,200 baud
                 4 = 57,600 baud
                 5 = 38,400 baud
                 6 = 19,200 baud
                 7 = 9,600 baud
            Returns None if read fails
        """
        return read_byte(self.servo, 0x06)

    @validate_value_range(0, 7)
    def write_baudrate(self, value: int, reg: bool = False) -> dict[str, object] | None:
        """
        Set the baud rate.

        Args:
            value (int): Baud rate code (0-7). See read_baudrate for mapping.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x06, value, reg)

    def read_return_delay(self) -> Optional[int]:
        """
        Read the return delay time.

        Returns:
            int: Delay in 2µs units (0-254).  Max = 508µs.  Returns None if read fails.
        """
        return read_byte(self.servo, 0x07)

    @validate_value_range(0, 254)
    def write_return_delay(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the return delay time.

        Args:
            value (int): Delay in 2µs units (0-254). Max configurable = 508µs.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x07, value, reg)

    def read_response_status_level(self) -> Optional[int]:
        """
        Read the response status level.

        Returns:
            int: 0 = No response except for READ/PING commands
                 1 = Response returned for all commands
            Returns None if read fails
        """
        return read_byte(self.servo, 0x08)

    @validate_value_range(0, 1)
    def write_response_status_level(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the response status level.

        Args:
            value (int): 0 = No response except READ/PING
                        1 = Response for all commands
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x08, value, reg)

    def read_min_angle_limit(self) -> Optional[int]:
        """
        Read the minimum angle limit.

        Returns:
            int: Minimum position in steps (0-4094), or None if read fails.
                 Must be less than max_angle_limit.
        """
        return read_word(self.servo, 0x09)

    @validate_value_range(0, 4094)
    def write_min_angle_limit(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the minimum angle limit.

        Args:
            value (int): Minimum position in steps (0-4094).
                        Must be less than max_angle_limit.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_word(self.servo, 0x09, value, reg=reg)

    def read_max_angle_limit(self) -> Optional[int]:
        """
        Read the maximum angle limit.

        Returns:
            int: Maximum position in steps (1-4095), or None if read fails.
                 Must be greater than min_angle_limit.
        """
        return read_word(self.servo, 0x0B)

    @validate_value_range(0, 4095)
    def write_max_angle_limit(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the maximum angle limit.

        Args:
            value (int): Maximum position in steps (1-4095).
                        Must be greater than min_angle_limit.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_word(self.servo, 0x0B, value, reg=reg)

    def read_max_temperature_limit(self) -> Optional[int]:
        """
        Read the maximum temperature limit.

        Returns:
            int: Temperature in °C (0-100), or None if read fails.
        """
        return read_byte(self.servo, 0x0D)

    @validate_value_range(0, 100)
    def write_max_temperature_limit(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the maximum temperature limit.

        Args:
            value (int): Temperature in °C (0-100).
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x0D, value, reg)

    def read_max_input_voltage(self) -> Optional[int]:
        """
        Read the maximum input voltage limit.

        Returns:
            int: Voltage in 0.1V units (0-254).  Example: 120 = 12.0V.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x0E)

    @validate_value_range(0, 254)
    def write_max_input_voltage(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the maximum input voltage limit.

        Args:
            value (int): Voltage in 0.1V units (0-254).  Example: 120 = 12.0V.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x0E, value, reg)

    def read_min_input_voltage(self) -> Optional[int]:
        """
        Read the minimum input voltage limit.

        Returns:
            int: Voltage in 0.1V units (0-254). Example: 60 = 6.0V.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x0F)

    @validate_value_range(0, 254)
    def write_min_input_voltage(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the minimum input voltage limit.

        Args:
            value (int): Voltage in 0.1V units (0-254). Example: 60 = 6.0V.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x0F, value, reg)

    def read_max_torque(self) -> Optional[int]:
        """
        Read the maximum torque limit.

        Returns:
            int: Torque in 0.1% units (0-1000).  Example: 500 = 50.0%.
                 This value is assigned to torque_limit on power-up.
                 Returns None if read fails.
        """
        return read_word(self.servo, 0x10)

    @validate_value_range(0, 1000)
    def write_max_torque(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the maximum torque limit.

        Args:
            value (int): Torque in 0.1% units (0-1000). Example: 500 = 50.0%.
                        This value is assigned to torque_limit on power-up.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_word(self.servo, 0x10, value, reg=reg)

    def read_phase(self) -> Optional[int]:
        """
        Read the phase register (special function).

        Returns:
            int: Phase value (0-254), or None if read fails.
                 Do not modify unless required.
        """
        return read_byte(self.servo, 0x12)

    @validate_value_range(0, 254)
    def write_phase(self, value: int, reg: bool = False) -> dict[str, object] | None:
        """
        Set the phase register (special function).

        Args:
            value (int): Phase value (0-254).  Do not modify unless required.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x12, value, reg)

    def read_uninstallation_conditions(self) -> Optional[int]:
        """
        Read the uninstallation conditions (protection settings).

        Returns:
            int: Bitmask (0-254) where bit 1 enables/disables corresponding protection.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x13)

    @validate_value_range(0, 254)
    def write_uninstallation_conditions(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the uninstallation conditions (protection settings).

        Args:
            value (int): Bitmask (0-254) where bit 1 enables/disables protection.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x13, value, reg)

    def read_led_alarm_conditions(self) -> Optional[int]:
        """
        Read the LED alarm conditions.

        Returns:
            int: Bitmask (0-254) where bit 1 enables/disables LED flashing alarm.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x14)

    @validate_value_range(0, 254)
    def write_led_alarm_conditions(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the LED alarm conditions.

        Args:
            value (int): Bitmask (0-254) where bit 1 enables/disables LED alarm.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x14, value, reg)

    def read_position_p(self) -> Optional[int]:
        """
        Read the position control loop P (proportional) coefficient.

        Returns:
            int: P coefficient (0-254), or None if read fails.
        """
        return read_byte(self.servo, 0x15)

    @validate_value_range(0, 254)
    def write_position_p(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the position control loop P (proportional) coefficient.

        Args:
            value (int): P coefficient (0-254).
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x15, value, reg)

    def read_position_d(self) -> Optional[int]:
        """
        Read the position control loop D (differential) coefficient.

        Returns:
            int: D coefficient (0-254), or None if read fails.
        """
        return read_byte(self.servo, 0x16)

    @validate_value_range(0, 254)
    def write_position_d(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the position control loop D (differential) coefficient.

        Args:
            value (int): D coefficient (0-254).
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x16, value, reg)

    def read_position_i(self) -> Optional[int]:
        """
        Read the position control loop I (integral) coefficient.

        Returns:
            int: I coefficient (0-254), or None if read fails.
        """
        return read_byte(self.servo, 0x17)

    @validate_value_range(0, 254)
    def write_position_i(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the position control loop I (integral) coefficient.

        Args:
            value (int): I coefficient (0-254).
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x17, value, reg)

    def read_min_starting_force(self) -> Optional[int]:
        """
        Read the minimum starting force.

        Returns:
            int: Force in 0.1% units (0-254).  Example: 10 = 1% of stall torque.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x18)

    @validate_value_range(0, 254)
    def write_min_starting_force(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the minimum starting force.

        Args:
            value (int): Force in 0.1% units (0-254). Example: 10 = 1% stall torque.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x18, value, reg)

    def read_points_limit(self) -> Optional[int]:
        """
        Read the points limit.

        Returns:
            int: Points limit value (0-254).  Max score = value * 4.
                 0 disables the limit. Returns None if read fails.
        """
        return read_byte(self.servo, 0x19)

    @validate_value_range(0, 254)
    def write_points_limit(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the points limit.

        Args:
            value (int): Points limit (0-254). Max score = value * 4.
                        0 disables the limit.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x19, value, reg)

    def read_cw_insensitive_area(self) -> Optional[int]:
        """
        Read the clockwise insensitive area (deadzone).

        Returns:
            int: Deadzone in steps (0-32).  Smallest unit is minimum resolution angle.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x1A)

    @validate_value_range(0, 32)
    def write_cw_insensitive_area(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the clockwise insensitive area (deadzone).

        Args:
            value (int): Deadzone in steps (0-32).
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x1A, value, reg)

    def read_ccw_insensitive_area(self) -> Optional[int]:
        """
        Read the counterclockwise insensitive area (deadzone).

        Returns:
            int: Deadzone in steps (0-32).  Smallest unit is minimum resolution angle.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x1B)

    @validate_value_range(0, 32)
    def write_ccw_insensitive_area(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the counterclockwise insensitive area (deadzone).

        Args:
            value (int): Deadzone in steps (0-32).
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x1B, value, reg)

    def read_protective_current(self) -> Optional[int]:
        """
        Read the protective current limit.

        Returns:
            int: Current in 6.5mA units (0-511). Max = 500*6.5mA = 3250mA.
                 Returns None if read fails.
        """
        return read_word(self.servo, 0x1C)

    @validate_value_range(0, 511)
    def write_protective_current(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the protective current limit.

        Args:
            value (int): Current in 6.5mA units (0-511).  Max = 3250mA.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_word(self.servo, 0x1C, value, reg=reg)

    def read_angular_resolution(self) -> Optional[int]:
        """
        Read the angular resolution setting.

        Returns:
            int: Resolution mode (1-3). Modifies magnification factor for
                 sensor minimum resolution angle.  Returns None if read fails.
        """
        return read_byte(self.servo, 0x1E)

    @validate_value_range(1, 3)
    def write_angular_resolution(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the angular resolution.

        Args:
            value (int): Resolution mode (1-3).
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x1E, value, reg)

    def read_position_correction(self) -> Optional[int]:
        """
        Read the position correction offset.

        Returns:
            int: Position offset in steps (-2047 to +2047), or None if read fails.
        """
        raw = self.servo._read_memory(0x1F, 2)
        if raw is None:
            return None
        if raw & 0x800:
            return raw - 4096
        return raw

    @validate_value_range(-2047, 2047)
    def write_position_correction(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the position correction offset.

        Args:
            value (int): Position offset in steps (-2047 to +2047).
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        if value < 0:
            raw = (abs(value) & 0x7FF) | 0x800
        else:
            raw = value & 0x7FF
        low, high = encode_unsigned_word(raw)
        write_fn = self.servo._reg_write_memory if reg else self.servo._write_memory
        return write_fn(0x1F, [low, high])

    def read_operating_mode(self) -> Optional[int]:
        """
        Read the operating mode.

        Returns:
            int: Mode (0-3):
                 0 = Position control mode
                 1 = Constant speed mode
                 2 = PWM open-loop mode
                 3 = Stepper servo mode
            Returns None if read fails.
        """
        return read_byte(self.servo, 0x21)

    @validate_value_range(0, 3)
    def write_operating_mode(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the operating mode.

        Args:
            value (int): Mode (0-3):
                        0 = Position control mode
                        1 = Constant speed mode
                        2 = PWM open-loop mode
                        3 = Stepper servo mode
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x21, value, reg)

    def read_protective_torque(self) -> Optional[int]:
        """
        Read the protective torque setting.

        Returns:
            int: Torque in 1.0% units (0-100). Output torque after overload protection.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x22)

    @validate_value_range(0, 100)
    def write_protective_torque(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the protective torque.

        Args:
            value (int): Torque in 1.0% units (0-100).
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x22, value, reg)

    def read_protection_time(self) -> Optional[int]:
        """
        Read the protection time.

        Returns:
            int: Time in 10ms units (0-254). Duration exceeding overload torque
                 before reset. Returns None if read fails.
        """
        return read_byte(self.servo, 0x23)

    @validate_value_range(0, 254)
    def write_protection_time(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the protection time.

        Args:
            value (int): Time in 10ms units (0-254).  Max = 2540ms.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x23, value, reg)

    def read_overload_torque(self) -> Optional[int]:
        """
        Read the overload torque threshold.

        Returns:
            int: Torque in 1.0% units (0-100). Max torque threshold for
                 overload protection. Returns None if read fails.
        """
        return read_byte(self.servo, 0x24)

    @validate_value_range(0, 100)
    def write_overload_torque(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the overload torque threshold.

        Args:
            value (int): Torque in 1.0% units (0-100).
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x24, value, reg)

    def read_speed_p(self) -> Optional[int]:
        """
        Read the speed control loop P (proportional) coefficient.

        Returns:
            int: P coefficient (0-254) for constant speed mode.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x25)

    @validate_value_range(0, 254)
    def write_speed_p(self, value: int, reg: bool = False) -> dict[str, object] | None:
        """
        Set the speed control loop P (proportional) coefficient.

        Args:
            value (int): P coefficient (0-254) for constant speed mode.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x25, value, reg)

    def read_overcurrent_protection_time(self) -> Optional[int]:
        """
        Read the overcurrent protection time.

        Returns:
            int: Time in 10ms units (0-254).  Max = 2540ms.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x26)

    @validate_value_range(0, 254)
    def write_overcurrent_protection_time(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the overcurrent protection time.

        Args:
            value (int): Time in 10ms units (0-254). Max = 2540ms.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x26, value, reg)

    def read_speed_i(self) -> Optional[int]:
        """
        Read the speed control loop I (integral) coefficient.

        Returns:
            int: I coefficient (0-254) in 1/10 units.  Reduced by factor 10 vs v3.6.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x27)

    @validate_value_range(0, 254)
    def write_speed_i(self, value: int, reg: bool = False) -> dict[str, object] | None:
        """
        Set the speed control loop I (integral) coefficient.

        Args:
            value (int): I coefficient (0-254) in 1/10 units.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x27, value, reg)


class SRAMRegisters:
    def __init__(self, servo: "Servo") -> None:
        self.servo = servo

    def read_torque_switch(self) -> Optional[int]:
        """
        Read the torque switch state.

        Returns:
            int: 0 = Torque off
                 1 = Torque on
                 128 = Correct current position to 2048
            Returns None if read fails.
        """
        return read_byte(self.servo, 0x28)

    def write_torque_switch(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the torque switch state.

        Args:
            value (int): 0 = Off, 1 = On, 128 = Correct position to 2048.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x28, value, reg)

    def torque_enable(self, reg: bool = False) -> dict[str, object] | None:
        """
        Enable servo torque (motor power on).

        Args:
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return self.write_torque_switch(1, reg=reg)

    def torque_disable(self, reg: bool = False) -> dict[str, object] | None:
        """
        Disable servo torque (motor power off, free-spinning).

        Args:
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return self.write_torque_switch(0, reg=reg)

    def correct_position_to_2048(self, reg: bool = False) -> dict[str, object] | None:
        """
        Correct the current position to 2048 (mid-point calibration).

        Args:
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return self.write_torque_switch(128, reg=reg)

    def read_acceleration(self) -> Optional[int]:
        """
        Read the acceleration setting.

        Returns:
            int: Acceleration in 100 steps/s² units (0-254).
                 Example: 10 = 1000 steps/s².
            Returns None if read fails.
        """
        return read_byte(self.servo, 0x29)

    @validate_value_range(0, 254)
    def write_acceleration(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the acceleration/deceleration.

        Args:
            value (int): Acceleration in 100 steps/s² units (0-254).
                        Example: 10 = 1000 steps/s².
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x29, value, reg)

    def sync_write_acceleration(self, servo_data: dict[int, int]) -> None:
        """
        SYNC WRITE acceleration to multiple servos.

        Args:
            servo_data: Dictionary mapping servo_id to acceleration value

        Returns:
            None (broadcast operation, no response)
        """
        if self.servo.id != 254:
            raise BroadcastOperationError(
                "sync_write_acceleration can only be called on the broadcast servo (ID 254)."
            )
        formatted_data: dict[int, list[int]] = {}
        for servo_id, value in servo_data.items():
            formatted_data[servo_id] = [value & 0xFF]
        return self.servo._sync_write(0x29, 1, formatted_data)  # type: ignore

    def read_target_location(self) -> Optional[int]:
        """
        Read the target position.

        Returns:
            int: Target position in steps (-32766 to +32766).
                 Each step = minimum resolvable angle.
            Returns None if read fails.
        """
        return read_word(self.servo, 0x2A, signed=True)

    @validate_value_range(-32766, 32766)
    def write_target_location(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the target position (absolute position control).

        Args:
            value (int): Target position in steps (-32766 to +32766).
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_word(self.servo, 0x2A, value, signed=True, reg=reg)

    def sync_write_target_location(self, servo_data: dict[int, int]) -> None:
        """
        SYNC WRITE target position to multiple servos.

        Args:
            servo_data: Dictionary mapping servo_id to target position value

        Returns:
            None (broadcast operation, no response)
        """
        if self.servo.id != 254:
            raise BroadcastOperationError(
                "sync_write_target_location can only be called on the broadcast servo (ID 254)."
            )
        formatted_data: dict[int, list[int]] = {}
        for servo_id, value in servo_data.items():
            low, high = encode_signed_word(value)
            formatted_data[servo_id] = [low, high]
        return self.servo._sync_write(0x2A, 2, formatted_data)  # type: ignore

    def read_runtime(self) -> Optional[int]:
        """
        Read the runtime setting (PWM open-loop mode).

        Returns:
            int: Runtime value (0-1000).  BIT10 indicates direction.
                 Used for PWM open-loop speed control.
            Returns None if read fails.
        """
        return read_word(self.servo, 0x2C)

    @validate_value_range(0, 2047)
    def write_runtime(self, value: int, reg: bool = False) -> dict[str, object] | None:
        """
        Set the runtime (PWM open-loop mode).

        Args:
            value (int): Runtime value (0-1000).  BIT10 indicates direction.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_word(self.servo, 0x2C, value, reg=reg)

    def read_running_speed(self) -> Optional[int]:
        """
        Read the running speed setpoint.

        Returns:
            int: Speed in steps/s (-32766 to +32766).
                 Sign indicates direction.  50 steps/s ≈ 0.732 RPM.
            Returns None if read fails.
        """
        return read_word(self.servo, 0x2E, signed=True)

    @validate_value_range(-32766, 32766)
    def write_running_speed(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the running speed (constant speed mode).

        Args:
            value (int): Speed in steps/s (-32766 to +32766).
                        Sign indicates direction. 50 steps/s ≈ 0.732 RPM.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_word(self.servo, 0x2E, value, signed=True, reg=reg)

    def sync_write_running_speed(self, servo_data: dict[int, int]) -> None:
        """
        SYNC WRITE running speed to multiple servos.

        Args:
            servo_data: Dictionary mapping servo_id to speed value

        Returns:
            None (broadcast operation, no response)
        """
        if self.servo.id != 254:
            raise BroadcastOperationError(
                "sync_write_running_speed can only be called on the broadcast servo (ID 254)."
            )
        formatted_data: dict[int, list[int]] = {}
        for servo_id, value in servo_data.items():
            low, high = encode_signed_word(value)
            formatted_data[servo_id] = [low, high]
        return self.servo._sync_write(0x2E, 2, formatted_data)  # type: ignore

    def read_torque_limit(self) -> Optional[int]:
        """
        Read the current torque limit.

        Returns:
            int: Torque limit in 0.1% units (0-1000).  Example: 500 = 50.0%.
                 Initial value is set from max_torque (EEPROM) on power-up.
            Returns None if read fails.
        """
        return read_word(self.servo, 0x30)

    @validate_value_range(0, 1000)
    def write_torque_limit(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the torque limit.

        Args:
            value (int): Torque limit in 0.1% units (0-1000).  Example: 500 = 50.0%.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_word(self.servo, 0x30, value, reg=reg)

    def sync_write_torque_limit(self, servo_data: dict[int, int]) -> None:
        """
        SYNC WRITE torque limit to multiple servos.

        Args:
            servo_data: Dictionary mapping servo_id to torque limit value

        Returns:
            None (broadcast operation, no response)
        """
        if self.servo.id != 254:
            raise BroadcastOperationError(
                "sync_write_torque_limit can only be called on the broadcast servo (ID 254)."
            )
        formatted_data: dict[int, list[int]] = {}
        for servo_id, value in servo_data.items():
            low, high = encode_unsigned_word(value)
            formatted_data[servo_id] = [low, high]
        self.servo._sync_write(0x30, 2, formatted_data)  # type: ignore

    def read_lock_symbol(self) -> Optional[int]:
        """
        Read the EEPROM write lock status.

        Returns:
            int: 0 = Write lock disabled (can save to EEPROM)
                 1 = Write lock enabled (cannot save to EEPROM)
            Returns None if read fails.
        """
        return read_byte(self.servo, 0x37)

    @validate_value_range(0, 1)
    def write_lock_symbol(
        self, value: int, reg: bool = False
    ) -> dict[str, object] | None:
        """
        Set the EEPROM write lock status.

        Args:
            value (int): 0 = Disable write lock, 1 = Enable write lock.
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return write_byte(self.servo, 0x37, value, reg)

    def lock(self, reg: bool = False) -> dict[str, object] | None:
        """
        Enable EEPROM write lock (prevent saving settings to EEPROM).

        Args:
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return self.write_lock_symbol(1, reg=reg)

    def unlock(self, reg: bool = False) -> dict[str, object] | None:
        """
        Disable EEPROM write lock (allow saving settings to EEPROM).

        Args:
            reg (bool): If True, use registered write mode.

        Returns:
            Response dict or None
        """
        return self.write_lock_symbol(0, reg=reg)

    def read_current_location(self) -> Optional[int]:
        """
        Read the current position (feedback).

        Returns:
            int: Current position in steps.  Returns None if read fails.
        """
        return read_word(self.servo, 0x38)

    def sync_read_current_location(
        self, servo_ids: list[int]
    ) -> dict[int, Optional[int]]:
        """
        SYNC READ current position from multiple servos.

        Args:
            servo_ids: List of servo IDs to query

        Returns:
            Dictionary mapping servo_id to current position
        """
        if self.servo.id != 254:
            raise BroadcastOperationError(
                "sync_read_current_location can only be called on the broadcast servo (ID 254)."
            )
        responses: dict[int, dict[str, Any] | None] = self.servo._sync_read(
            0x38, 2, servo_ids
        )
        results: dict[int, int | None] = {}
        for servo_id, response in responses.items():
            if response and isinstance(response, dict) and response.get("parameters"):
                data: bytes = response["parameters"]
                results[servo_id] = data[0] | (data[1] << 8)
            else:
                results[servo_id] = None
        return results

    def read_current_speed(self) -> Optional[int]:
        """
        Read the current speed (feedback).

        Returns:
            int: Current speed in steps/s.    Returns None if read fails.
        """
        return read_word(self.servo, 0x3A, signed=True)

    def sync_read_current_speed(self, servo_ids: list[int]) -> dict[int, Optional[int]]:
        """
        SYNC READ current speed from multiple servos.

        Args:
            servo_ids: List of servo IDs to query

        Returns:
            Dictionary mapping servo_id to current speed
        """
        if self.servo.id != 254:
            raise BroadcastOperationError(
                "sync_read_current_speed can only be called on the broadcast servo (ID 254)."
            )
        responses: dict[int, dict[str, Any] | None] = self.servo._sync_read(
            0x3A, 2, servo_ids
        )
        results: dict[int, int | None] = {}
        for servo_id, response in responses.items():
            if response and isinstance(response, dict) and response.get("parameters"):
                data: list[int] | bytes = response["parameters"]
                if isinstance(data, (bytes, bytearray)):
                    raw = data[0] | (data[1] << 8)
                else:
                    raw = data[0] | (data[1] << 8)
                results[servo_id] = decode_signed_word(raw)
            else:
                results[servo_id] = None
        return results

    def read_current_load(self) -> Optional[int]:
        """
        Read the current load (motor drive duty cycle).

        Returns:
            int: Load in 0.1% units (0-1000). Example: 500 = 50.0%.
                 Returns None if read fails.
        """
        return read_word(self.servo, 0x3C)

    def sync_read_current_load(self, servo_ids: list[int]) -> dict[int, Optional[int]]:
        """
        SYNC READ current load from multiple servos.

        Args:
            servo_ids: List of servo IDs to query

        Returns:
            Dictionary mapping servo_id to current load
        """
        if self.servo.id != 254:
            raise BroadcastOperationError(
                "sync_read_current_load can only be called on the broadcast servo (ID 254)."
            )
        responses: dict[int, dict[str, Any] | None] = self.servo._sync_read(
            0x3C, 2, servo_ids
        )
        results: dict[int, Optional[int]] = {}
        for servo_id, response in responses.items():
            if response and response.get("parameters"):
                data = response["parameters"]
                raw = data[0] | (data[1] << 8)
                results[servo_id] = raw
            else:
                results[servo_id] = None
        return results

    def read_current_voltage(self) -> Optional[int]:
        """
        Read the current operating voltage.

        Returns:
            int: Voltage in 0.1V units. Example: 120 = 12.0V.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x3E)

    def sync_read_current_voltage(
        self, servo_ids: list[int]
    ) -> dict[int, Optional[int]]:
        """
        SYNC READ current voltage from multiple servos.

        Args:
            servo_ids: List of servo IDs to query

        Returns:
            Dictionary mapping servo_id to current voltage
        """
        if self.servo.id != 254:
            raise BroadcastOperationError(
                "sync_read_current_voltage can only be called on the broadcast servo (ID 254)."
            )
        responses: dict[int, dict[str, Any] | None] = self.servo._sync_read(
            0x3E, 1, servo_ids
        )
        results: dict[int, Optional[int]] = {}
        for servo_id, response in responses.items():
            if response and response.get("parameters"):
                data = response["parameters"]
                results[servo_id] = data[0]
            else:
                results[servo_id] = None
        return results

    def read_current_temperature(self) -> Optional[int]:
        """
        Read the current internal temperature.

        Returns:
            int: Temperature in °C. Returns None if read fails.
        """
        return read_byte(self.servo, 0x3F)

    def sync_read_current_temperature(
        self, servo_ids: list[int]
    ) -> dict[int, Optional[int]]:
        """
        SYNC READ current temperature from multiple servos.

        Args:
            servo_ids: List of servo IDs to query

        Returns:
            Dictionary mapping servo_id to current temperature
        """
        if self.servo.id != 254:
            raise BroadcastOperationError(
                "sync_read_current_temperature can only be called on the broadcast servo (ID 254)."
            )
        responses: dict[int, dict[str, Any] | None] = self.servo._sync_read(
            0x3F, 1, servo_ids
        )
        results: dict[int, Optional[int]] = {}
        for servo_id, response in responses.items():
            if response and response.get("parameters"):
                data = response["parameters"]
                results[servo_id] = data[0]
            else:
                results[servo_id] = None
        return results

    def read_async_write_flag(self) -> Optional[int]:
        """
        Read the asynchronous write flag.

        Returns:
            int: Flag value for asynchronous write instructions.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x40)

    def read_servo_status(self) -> Optional[int]:
        """
        Read the servo status (error flags).

        Returns:
            int: Status bitmask. Bit = 1 indicates error, 0 = no error.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x41)

    def sync_read_servo_status(self, servo_ids: list[int]) -> dict[int, Optional[int]]:
        """
        SYNC READ servo status from multiple servos.

        Args:
            servo_ids: List of servo IDs to query

        Returns:
            Dictionary mapping servo_id to servo status
        """
        if self.servo.id != 254:
            raise BroadcastOperationError(
                "sync_read_servo_status can only be called on the broadcast servo (ID 254)."
            )
        responses: dict[int, dict[str, Any] | None] = self.servo._sync_read(
            0x41, 1, servo_ids
        )
        results: dict[int, Optional[int]] = {}
        for servo_id, response in responses.items():
            if response and response.get("parameters"):
                data = response["parameters"]
                results[servo_id] = data[0]
            else:
                results[servo_id] = None
        return results

    def read_mobile_sign(self) -> Optional[int]:
        """
        Read the movement flag.

        Returns:
            int: 1 = Servo in motion, 0 = Stationary.
                 Returns None if read fails.
        """
        return read_byte(self.servo, 0x42)

    def is_moving(self) -> bool:
        """
        Check if the servo is currently moving.

        Returns:
            bool: True if servo is moving, False if stationary or read fails.
        """
        value = self.read_mobile_sign()
        return value == 1 if value is not None else False

    def read_current_current(self) -> Optional[int]:
        """
        Read the current motor current draw.

        Returns:
            int: Current in 6.5mA units (0-500). Max = 500*6.5mA = 3250mA.
                 Returns None if read fails.
        """
        return read_word(self.servo, 0x45)

    def sync_read_current_current(
        self, servo_ids: list[int]
    ) -> dict[int, Optional[int]]:
        """
        SYNC READ current draw from multiple servos.

        Args:
            servo_ids: List of servo IDs to query

        Returns:
            Dictionary mapping servo_id to current draw
        """
        if self.servo.id != 254:
            raise BroadcastOperationError(
                "sync_read_current_current can only be called on the broadcast servo (ID 254)."
            )
        responses: dict[int, dict[str, Any] | None] = self.servo._sync_read(
            0x45, 2, servo_ids
        )
        results: dict[int, Optional[int]] = {}
        for servo_id, response in responses.items():
            if response and response.get("parameters"):
                data = response["parameters"]
                raw = data[0] | (data[1] << 8)
                results[servo_id] = raw
            else:
                results[servo_id] = None
        return results
