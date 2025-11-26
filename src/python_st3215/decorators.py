from functools import wraps
from typing import Callable


def validate_servo_id(func: Callable) -> Callable:
    """
    Decorator to validate servo ID is not broadcast ID (254).
    """

    @wraps(func)
    def wrapper(self, servo_id: int, *args, **kwargs):
        if servo_id == 254:
            from .errors import ST3215Error

            raise ST3215Error(f"Cannot {func.__name__} broadcast servo ID 254.")
        return func(self, servo_id, *args, **kwargs)

    return wrapper


def validate_broadcast_only(func: Callable) -> Callable:
    """
    Decorator to ensure operation is only used with broadcast servo (ID 254).
    """

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.servo.id != 254:
            from .errors import ST3215Error

            raise ST3215Error(
                f"{func.__name__} can only be used with broadcast servo (ID 254)."
            )
        return func(self, *args, **kwargs)

    return wrapper


def validate_value_range(min_val: int, max_val: int) -> Callable:
    """
    Decorator to validate that a value parameter is within the specified range.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, value: int, *args, **kwargs):
            if not (min_val <= value <= max_val):
                raise ValueError(
                    f"{func.__name__}: value {value} out of range [{min_val}, {max_val}]"
                )
            return func(self, value, *args, **kwargs)

        return wrapper

    return decorator


def encode_signed_word(value: int) -> tuple[int, int]:
    """
    Encode a signed 16-bit value to low and high bytes.

    Args:
        value: Signed integer (-32768 to 32767)

    Returns:
        Tuple of (low_byte, high_byte)
    """
    if value < 0:
        raw = 65536 + value
    else:
        raw = value
    low = raw & 0xFF
    high = (raw >> 8) & 0xFF
    return low, high


def decode_signed_word(raw: int) -> int:
    """
    Decode a 16-bit raw value to signed integer.

    Args:
        raw: Raw 16-bit value (0-65535)

    Returns:
        Signed integer (-32768 to 32767)
    """
    if raw & 0x8000:
        return raw - 65536
    return raw


def encode_unsigned_word(value: int) -> tuple[int, int]:
    """
    Encode an unsigned 16-bit value to low and high bytes.

    Args:
        value: Unsigned integer (0 to 65535)

    Returns:
        Tuple of (low_byte, high_byte)
    """
    low = value & 0xFF
    high = (value >> 8) & 0xFF
    return low, high


def write_method(address: int, size: int = 1, signed: bool = False):
    """
    Decorator factory to create write methods for memory addresses.

    Args:
        address: Memory address to write to
        size: Size in bytes (1 or 2)
        signed: Whether the value is signed (for 2-byte values)

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, value: int, reg: bool = False):
            write_fn = self.servo._reg_write_memory if reg else self.servo._write_memory
            if size == 1:
                return write_fn(address, [value & 0xFF])
            elif size == 2:
                if signed:
                    low, high = encode_signed_word(value)
                else:
                    low, high = encode_unsigned_word(value)
                return write_fn(address, [low, high])
            raise ValueError(f"Unsupported size {size} for write_method.")

        return wrapper

    return decorator


def read_method(address: int, size: int = 1, signed: bool = False):
    """
    Decorator factory to create read methods for memory addresses.

    Args:
        address: Memory address to read from
        size: Size in bytes (1 or 2)
        signed: Whether the value is signed (for 2-byte values)

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self):
            raw = self.servo._read_memory(address, size)
            if raw is None:
                return None
            if size == 2 and signed:
                return decode_signed_word(raw)
            return raw

        return wrapper

    return decorator


def sync_write_method(address: int, size: int = 1, signed: bool = False):
    """
    Decorator factory to create sync write methods for broadcast operations.

    Args:
        address: Memory address to write to
        size: Size in bytes (1 or 2)
        signed: Whether the value is signed (for 2-byte values)

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @validate_broadcast_only
        def wrapper(self, servo_data: dict[int, int]):
            """
            Perform SYNC WRITE to multiple servos.

            Args:
                servo_data: Dictionary mapping servo_id to value

            Returns:
                None (broadcast operation, no response)
            """
            formatted_data = {}
            for servo_id, value in servo_data.items():
                if size == 1:
                    formatted_data[servo_id] = [value & 0xFF]
                elif size == 2:
                    if signed:
                        low, high = encode_signed_word(value)
                    else:
                        low, high = encode_unsigned_word(value)
                    formatted_data[servo_id] = [low, high]
            return self.servo._sync_write(address, size, formatted_data)

        return wrapper

    return decorator


def sync_read_method(address: int, size: int = 1, signed: bool = False):
    """
    Decorator factory to create sync read methods for broadcast operations.

    Args:
        address: Memory address to read from
        size: Size in bytes (1 or 2)
        signed: Whether the value is signed (for 2-byte values)

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        @validate_broadcast_only
        def wrapper(self, servo_ids: list[int]):
            """
            Perform SYNC READ from multiple servos.

            Args:
                servo_ids: List of servo IDs to query

            Returns:
                Dictionary mapping servo_id to value
            """
            responses = self.servo._sync_read(address, size, servo_ids)
            results = {}
            for servo_id, response in responses.items():
                if response and response.get("parameters"):
                    data = response["parameters"]
                    if size == 1:
                        results[servo_id] = data[0]
                    elif size == 2:
                        raw = data[0] | (data[1] << 8)
                        results[servo_id] = decode_signed_word(raw) if signed else raw
                else:
                    results[servo_id] = None
            return results

        return wrapper

    return decorator
