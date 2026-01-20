import logging
import time
from typing import Callable, Literal, Optional, Sequence

import serial

from .decorators import validate_servo_id
from .errors import (
    ChecksumError,
    CommunicationTimeoutError,
    InvalidIDError,
    InvalidInstructionError,
    ServoNotRespondingError,
    ServoStatusError,
)
from .instructions import Instruction
from .servo import Servo


class ST3215:
    logger = logging.getLogger("ST3215")
    logger.setLevel(logging.WARN)
    _console_handler = logging.StreamHandler()
    _console_handler.setFormatter(
        logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    )
    logger.addHandler(_console_handler)

    @classmethod
    def set_log_level(cls, level: int) -> None:
        cls.logger.setLevel(level)

    @classmethod
    def disable_logging(cls) -> None:
        cls.logger.disabled = True

    @classmethod
    def enable_logging(cls) -> None:
        cls.logger.disabled = False

    def __init__(
        self,
        port: str,
        baudrate: int = 1000000,
        read_timeout: float = 0.002,
        retry_count: int = 3,
        retry_delay: float = 0.01,
    ) -> None:
        """
        Initialize the ST3215 controller with the given serial port settings.

        Args:
            port (str): Serial port to connect to (e.g., 'COM3' or '/dev/ttyUSB0').
            baudrate (int): Baud rate for serial communication. Default is 1,000,000.
            read_timeout (float): Read timeout in seconds. Default is 0.002.
            retry_count (int): Number of retries for failed communication. Default is 3.
            retry_delay (float): Delay between retries in seconds. Default is 0.01.

        Raises:
            serial.SerialException: If the serial port cannot be opened.
        """
        self.logger.debug(
            f"Initializing ST3215 on port {port} with baudrate {baudrate}"
        )
        self.port = port
        self.baudrate = baudrate
        self.read_timeout = read_timeout
        self.retry_count = retry_count
        self.retry_delay = retry_delay

        try:
            self.ser = serial.Serial(port, baudrate=baudrate, timeout=read_timeout)
            self.logger.debug(f"Serial port opened at {baudrate} baud.")
        except serial.SerialException as e:
            self.logger.error(f"Failed to open serial port {port}: {e}")
            raise
        self.broadcast = Servo(self, 254)

    def close(self) -> None:
        """
        Close the serial connection.

        Safe to call multiple times.
        """
        if hasattr(self, "ser") and self.ser.is_open:
            self.ser.close()
            self.logger.info("Serial port closed.")

    def is_connected(self) -> bool:
        """
        Check if the serial connection is open and healthy.

        Returns:
            bool: True if connected, False otherwise.
        """
        return hasattr(self, "ser") and self.ser.is_open

    def build_packet(
        self, servo_id: int, instruction: int, parameters: Sequence[int] | None = None
    ) -> bytes:
        """
        Build a command packet for the ST3215 protocol.

        Args:
            servo_id: Target servo ID (0-253) or 254 for broadcast.
            instruction: Instruction code from Instruction enum.
            parameters: Optional list of parameter bytes.

        Returns:
            bytes: Complete packet ready to send.

        Raises:
            InvalidInstructionError: If instruction code is invalid.
            InvalidIDError: If servo_id is out of range.
        """
        if not 0 <= servo_id <= 254:
            raise InvalidIDError(servo_id)
        if not Instruction.has_value(instruction):
            raise InvalidInstructionError(f"Invalid instruction: {instruction:#04x}")
        params = tuple(parameters) if parameters else ()
        length = len(params) + 2
        checksum_base = servo_id + length + instruction + sum(params)
        checksum = (~checksum_base) & 0xFF
        packet = bytearray(
            [0xFF, 0xFF, servo_id & 0xFF, length & 0xFF, instruction & 0xFF]
        )
        packet.extend(p & 0xFF for p in params)
        packet.append(checksum)
        self.logger.debug(
            f"Built packet for servo {servo_id:#02x}: instruction={instruction:#02x}, params={params}, checksum={checksum:#02x}, bytes={list(packet)}"
        )
        return bytes(packet)

    def send_instruction(
        self,
        servo_id: int,
        instruction: int | Instruction,
        parameters: Sequence[int] | None = None,
    ) -> bytes:
        """
        Send an instruction packet to a servo.

        Args:
            servo_id: Target servo ID.
            instruction: Instruction code (int or Instruction enum).
            parameters: Optional parameter bytes.

        Returns:
            bytes: The packet that was sent.

        Raises:
            serial.SerialException: If write fails.
        """
        instruction_value = (
            instruction.value if isinstance(instruction, Instruction) else instruction
        )
        packet = self.build_packet(servo_id, instruction_value, parameters)
        self.logger.debug(f"Sending packet: {list(packet)}")

        try:
            self.ser.write(packet)
            self.ser.flush()
            return packet
        except serial.SerialException as e:
            self.logger.error(f"Failed to send packet: {e}")
            raise

    def read_response(
        self, sent_packet: bytes, timeout: Optional[float] = None
    ) -> Optional[bytes]:
        """
        Read and parse response from servo.

        Args:
            sent_packet: The packet that was sent (for echo filtering).
            timeout: Optional timeout override in seconds.

        Returns:
            Optional[bytes]: Response data or None if no response.
        """
        if timeout is not None:
            old_timeout = self.ser.timeout
            self.ser.timeout = timeout

        try:
            raw_data = self.ser.read(1024)
            self.logger.debug(f"Raw data read: {list(raw_data)}")
            if not raw_data:
                self.logger.warning("No response received.")
                return None
            if raw_data.startswith(sent_packet):
                self.logger.debug(
                    "Response includes sent packet header, stripping sent packet."
                )
                return raw_data[len(sent_packet) :]
            return raw_data
        finally:
            if timeout is not None:
                self.ser.timeout = old_timeout

    def parse_response(
        self, data: bytes, raise_on_error: bool = False
    ) -> Optional[dict[str, object]]:
        """
        Parse a response packet from a servo.

        Args:
            data: Raw response data.
            raise_on_error: If True, raise exception on servo error status.

        Returns:
            Optional[dict]: Parsed response or None if invalid.

        Raises:
            ChecksumError: If checksum validation fails.
            ServoStatusError: If servo reports error and raise_on_error is True.
        """
        self.logger.debug(f"Parsing response data: {list(data)}")
        if len(data) < 6:
            self.logger.warning("Response too short to parse.")
            return None
        header = data[0:2]
        servo_id = data[2]
        length = data[3]
        error = data[4]
        parameters = data[5:-1] if length > 2 else b""
        received_checksum = data[-1]
        checksum_base = servo_id + length + error + sum(parameters)
        calculated_checksum = (~checksum_base) & 0xFF
        valid_checksum = calculated_checksum == received_checksum
        if not valid_checksum:
            error_msg = (
                f"Checksum mismatch: received {received_checksum:#02x}, "
                f"calculated {calculated_checksum:#02x}"
            )
            self.logger.error(error_msg)
            raise ChecksumError(error_msg)
        if error != 0:
            if raise_on_error:
                raise ServoStatusError(servo_id, error)
            self.logger.warning(f"Servo {servo_id} reported error code: {error:#02x}")
        parsed: dict[str, object] = {
            "header": header,
            "id": servo_id,
            "length": length,
            "error": error,
            "parameters": parameters,
            "received_checksum": received_checksum,
            "calculated_checksum": calculated_checksum,
            "checksum_valid": valid_checksum,
        }
        self.logger.debug(f"Parsed response: {parsed}")
        return parsed

    def _retry_operation(
        self,
        operation: Callable[[], Optional[dict[str, object]]],
        operation_name: str = "operation",
    ) -> Optional[dict[str, object]]:
        """
        Retry an operation with exponential backoff.

        Args:
            operation: Function to execute.
            operation_name: Name for logging.

        Returns:
            Result from operation or None if all retries fail.
        """
        last_exception = None

        for attempt in range(self.retry_count):
            try:
                result = operation()
                if result is not None:
                    return result
                if attempt < self.retry_count - 1:
                    delay = self.retry_delay * (2**attempt)
                    self.logger.debug(
                        f"{operation_name} attempt {attempt + 1} failed, "
                        f"retrying in {delay:.3f}s..."
                    )
                    time.sleep(delay)
            except (ChecksumError, serial.SerialException) as e:
                last_exception = e
                if attempt < self.retry_count - 1:
                    delay = self.retry_delay * (2**attempt)
                    self.logger.debug(
                        f"{operation_name} attempt {attempt + 1} failed with {type(e).__name__}, "
                        f"retrying in {delay:.3f}s..."
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"{operation_name} failed after {self.retry_count} attempts"
                    )

        if last_exception:
            raise CommunicationTimeoutError(
                f"{operation_name} failed after {self.retry_count} retries"
            ) from last_exception

        return None

    @validate_servo_id
    def ping(
        self, servo_id: int, use_retry: bool = True
    ) -> Optional[dict[str, object]]:
        """
        Send PING command to the servo to check if it is responsive.

        Args:
            servo_id: ID of servo to ping (0-253).
            use_retry: Whether to use retry logic. Default is True.

        Returns:
            dict: Parsed response from the servo if it responds, else None.

        Raises:
            CommunicationTimeoutError: If servo doesn't respond after retries.
        """
        self.logger.debug(f"Pinging servo {servo_id}")

        def _ping() -> Optional[dict[str, object]]:
            packet = self.send_instruction(servo_id, Instruction.PING)
            response = self.read_response(packet)
            if response:
                return self.parse_response(response)
            return None

        if use_retry:
            return self._retry_operation(_ping, f"Ping servo {servo_id}")
        else:
            return _ping()

    @validate_servo_id
    def wrap_servo(self, servo_id: int, verify: bool = True) -> Servo:
        """
        Create a Servo instance for the given servo ID.

        Args:
            servo_id: ID of servo to wrap (0-253).
            verify: If True, ping servo first to verify it responds. Default is True.

        Returns:
            Servo: An instance of the Servo class for the given ID.

        Raises:
            ServoNotRespondingError: If verify=True and servo does not respond to ping.
        """
        if verify:
            try:
                parsed = self.ping(servo_id)
                if not parsed or parsed.get("error") != 0:
                    raise ServoNotRespondingError(
                        f"Servo ID {servo_id} did not respond to ping or reported an error."
                    )
            except CommunicationTimeoutError as e:
                raise ServoNotRespondingError(
                    f"Servo ID {servo_id} did not respond to ping."
                ) from e
        return Servo(self, servo_id)

    def list_servos(
        self,
        start_id: int = 0,
        end_id: int = 253,
        timeout: float = 0.001,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> list[int]:
        """
        Scan for connected servos by pinging a range of IDs.

        Args:
            start_id: Starting servo ID (inclusive). Default is 0.
            end_id: Ending servo ID (inclusive). Default is 253.
            timeout: Timeout for each ping in seconds. Default is 0.001.
            progress_callback: Optional callback function(current, total) for progress updates.

        Returns:
            List of servo IDs that responded to the ping.

        Example:
            >>> def show_progress(current, total):
            ...     print(f"Scanning: {current}/{total}")
            >>> servos = controller.list_servos(progress_callback=show_progress)
        """
        if not 0 <= start_id <= 253:
            raise InvalidIDError(start_id)
        if not 0 <= end_id <= 253:
            raise InvalidIDError(end_id)
        if start_id > end_id:
            raise ValueError(f"start_id ({start_id}) must be <= end_id ({end_id})")

        found = []
        total = end_id - start_id + 1
        old_retry_count = self.retry_count
        self.retry_count = 1

        try:
            for i, servo_id in enumerate(range(start_id, end_id + 1)):
                if progress_callback:
                    progress_callback(i + 1, total)
                try:
                    packet = self.send_instruction(servo_id, Instruction.PING)
                    response = self.read_response(packet, timeout=timeout)
                    if response:
                        parsed = self.parse_response(response)
                        if parsed and parsed.get("error") == 0:
                            found.append(servo_id)
                            self.logger.info(f"Found servo at ID {servo_id}")
                except (
                    serial.SerialException,
                    ChecksumError,
                    CommunicationTimeoutError,
                ):
                    continue
        finally:
            self.retry_count = old_retry_count
        self.logger.info(f"Scan complete. Found {len(found)} servo(s): {found}")
        return found

    def _sync_write(
        self, address: int, data_length: int, servo_data: dict[int, Sequence[int]]
    ) -> None:
        self.logger.debug(
            f"SYNC WRITE to address {address:#02x} for {len(servo_data)} servos"
        )
        parameters = [address, data_length]
        for servo_id, data in servo_data.items():
            if len(data) != data_length:
                raise ValueError(
                    f"Servo {servo_id} data length {len(data)} does not match "
                    f"specified length {data_length}"
                )
            parameters.append(servo_id)
            parameters.extend(data)
        self.send_instruction(0xFE, Instruction.SYNC_WRITE, parameters)
        self.logger.debug("SYNC WRITE command sent, no response expected")

    def _sync_read(
        self, address: int, data_length: int, servo_ids: Sequence[int]
    ) -> dict[int, Optional[dict[str, object]]]:
        self.logger.debug(
            f"SYNC READ from address {address:#02x}, length {data_length} "
            f"for servos {servo_ids}"
        )
        parameters = [address, data_length, *servo_ids]
        packet = self.send_instruction(0xFE, Instruction.SYNC_READ, parameters)
        responses: dict[int, Optional[dict[str, object]]] = {}
        for servo_id in servo_ids:
            response = self.read_response(packet)
            if response:
                parsed = self.parse_response(response)
                self.logger.debug(
                    f"Servo {servo_id}: received SYNC READ response {parsed}"
                )
                responses[servo_id] = parsed
            else:
                self.logger.warning(
                    f"Servo {servo_id}: no response received for SYNC READ"
                )
                responses[servo_id] = None
        return responses

    def __enter__(self) -> "ST3215":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> Literal[False]:
        try:
            self.close()
        except Exception as e:
            self.logger.error(f"Error closing connection: {e}")
        return False

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
