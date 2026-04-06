from __future__ import annotations

from typing import TYPE_CHECKING, Any, Sequence, cast

if TYPE_CHECKING:
    from .st3215 import ST3215

from .instructions import Instruction
from .registers import EEPROMRegisters, SRAMRegisters


class Servo:
    def __init__(self, controller: "ST3215", servo_id: int) -> None:
        """Wrap a single servo for convenient register access.

        Instances are normally obtained via :meth:`ST3215.wrap_servo` rather than
        constructed directly.  The broadcast pseudo-servo (ID 254) is available as
        ``controller.broadcast`` and exposes the ``sync_write_*`` / ``sync_read_*``
        helpers on its ``sram`` attribute.

        Args:
            controller (ST3215): The parent controller that owns the serial connection.
            servo_id (int): The servo's bus ID (0-253, or 254 for broadcast).
        """
        self.controller = controller
        self.id = servo_id
        self.logger = controller.logger
        self.eeprom = EEPROMRegisters(self)
        self.sram = SRAMRegisters(self)

    def send(
        self, instruction: int | Instruction, parameters: Sequence[int] | None = None
    ) -> dict[str, object] | None:
        """Send a raw instruction to this servo and return the parsed response.

        This is the low-level building block used by all register helpers.  Prefer
        the typed methods on :attr:`eeprom` and :attr:`sram` for normal use.

        Args:
            instruction (int | Instruction): Instruction byte to send.
            parameters (Sequence[int] | None): Optional parameter bytes.

        Returns:
            dict | None: Parsed response dict (see :meth:`ST3215.parse_response`),
            or ``None`` if no response was received.
        """
        self.logger.debug(
            f"Servo {self.id}: sending instruction {instruction} with parameters {parameters}"
        )
        packet = self.controller.send_instruction(self.id, instruction, parameters)
        response = self.controller.read_response(packet)
        if response:
            parsed: dict[str, object] | None = self.controller.parse_response(response)
            self.logger.debug(f"Servo {self.id}: received response {parsed}")
            return parsed
        self.logger.warning(
            f"Servo {self.id}: no response received for instruction {instruction}"
        )
        return None

    def ping(self) -> dict[str, object] | None:
        """Send PING command to the servo to check if it is responsive."""
        return cast(dict[str, object] | None, self.controller.ping(self.id))

    def action(self) -> dict[str, object] | None:
        """Send ACTION command to the servo to execute all registered commands."""
        self.logger.debug(f"Sending ACTION command to servo {self.id}")
        return self.send(Instruction.ACTION)

    def reset(self) -> dict[str, object] | None:
        """Send RESET command to the servo to reset it to factory defaults."""
        self.logger.debug(f"Sending RESET command to servo {self.id}")
        return self.send(Instruction.RESET)

    def _read_memory(self, address: int, length: int = 1) -> int | None:
        self.logger.debug(
            f"Reading {length} bytes from address {address:#02x} on servo {self.id}"
        )
        response = self.send(Instruction.READ, [address, length])
        if response and response.get("parameters"):
            data = response["parameters"]
            if isinstance(data, (bytes, bytearray)):
                if length == 1:
                    return data[0]
                value = 0
                for i, byte in enumerate(data):
                    value |= byte << (8 * i)
                self.logger.debug(
                    f"Read value {value} (0x{value:04X}) from servo {self.id}"
                )
                return value
        self.logger.warning(
            f"Failed to read memory from servo {self.id} at address {address:#02x}"
        )
        return None

    def _write_memory(
        self, address: int, values: Sequence[int]
    ) -> dict[str, object] | None:
        if not isinstance(values, Sequence):
            values = [values]
        self.logger.debug(
            f"Writing values {values} to address {address:#02x} on servo {self.id}"
        )
        return self.send(Instruction.WRITE, [address, *values])

    def _reg_write_memory(
        self, address: int, values: Sequence[int]
    ) -> dict[str, object] | None:
        if not isinstance(values, Sequence):
            values = [values]
        self.logger.debug(
            f"Reg Writing values {values} to address {address:#02x} on servo {self.id}"
        )
        return self.send(Instruction.REG_WRITE, [address, *values])

    def _sync_write(
        self, address: int, data_length: int, servo_data: dict[int, Sequence[int]]
    ) -> None:
        return self.controller._sync_write(address, data_length, servo_data)

    def _sync_read(
        self, address: int, data_length: int, servo_ids: Sequence[int]
    ) -> dict[int, dict[str, Any] | None]:
        return self.controller._sync_read(address, data_length, servo_ids)
