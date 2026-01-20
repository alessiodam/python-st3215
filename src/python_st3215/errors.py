class ST3215Error(Exception):
    """Base exception for all ST3215-related errors."""

    pass


class ServoNotRespondingError(ST3215Error):
    """
    Raised when a servo does not respond to a command.
    """

    pass


class InvalidInstructionError(ST3215Error):
    """
    Raised when an invalid instruction code is used.
    """

    pass


class ChecksumError(ST3215Error):
    """
    Raised when response checksum validation fails.
    """

    pass


class InvalidParameterError(ST3215Error):
    """
    Raised when a parameter value is outside valid range.
    """

    def __init__(
        self,
        parameter: str,
        value: int | float,
        min_val: int | float,
        max_val: int | float,
    ):
        self.parameter = parameter
        self.value = value
        self.min_val = min_val
        self.max_val = max_val
        super().__init__(
            f"Parameter '{parameter}' value {value} is outside valid range [{min_val}, {max_val}]"
        )


class ServoAngleLimitError(ST3215Error):
    """
    Raised when attempting to move servo beyond configured angle limits.
    """

    pass


class CommunicationTimeoutError(ST3215Error):
    """
    Raised when communication with servo times out.
    """

    pass


class ServoLockedError(ST3215Error):
    """
    Raised when attempting to write to a locked servo.

    The servo's lock must be disabled before writing to EEPROM.
    """

    pass


class BroadcastOperationError(ST3215Error):
    """
    Raised when an invalid operation is attempted on broadcast ID (254).

    Some operations like ping cannot be performed on the broadcast address.
    """

    pass


class InvalidIDError(ST3215Error):
    """
    Raised when an invalid servo ID is specified.

    Valid IDs are 0-253. ID 254 is reserved for broadcast.
    """

    def __init__(self, servo_id: int):
        self.servo_id = servo_id
        super().__init__(
            f"Invalid servo ID {servo_id}. Valid range is 0-253 (254 is broadcast)"
        )


class ServoStatusError(ST3215Error):
    """
    Raised when servo reports an error status.

    The error code from the servo can be inspected to determine
    the specific issue.
    """

    def __init__(self, servo_id: int, error_code: int, message: str = ""):
        self.servo_id = servo_id
        self.error_code = error_code
        error_details = None
        detail_str = ", ".join(error_details) if error_details else "Unknown error"
        full_message = f"Servo {servo_id} error (code {error_code:#02x}): {detail_str}"
        if message:
            full_message += f" - {message}"
        super().__init__(full_message)
