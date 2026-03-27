from functools import wraps
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def validate_servo_id(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to validate servo ID is not broadcast ID (254).
    """

    @wraps(func)
    def wrapper(self: Any, servo_id: int, *args: Any, **kwargs: Any) -> Any:
        if servo_id == 254:
            from .errors import ST3215Error

            raise ST3215Error(f"Cannot {func.__name__} broadcast servo ID 254.")
        return func(self, servo_id, *args, **kwargs)

    return wrapper


def validate_value_range(
    min_val: int, max_val: int
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to validate that a value parameter is within the specified range.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(self: Any, value: int, *args: Any, **kwargs: Any) -> Any:
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
    Encoding uses most-significant bit as sign bit.

    Args:
        value: Signed integer (-32767 to 32767)

    Returns:
        Tuple of (low_byte, high_byte)
    """
    if value < -32767 or value > 32767:
        raise ValueError
    low, high = abs(value) & 0xFF, (abs(value) >> 8) & 0x7F
    if value < 0:
        high |= 0x80
    return low, high


def decode_signed_word(raw: int) -> int:
    """
    Decode a 16-bit raw value to signed integer.

    Args:
        raw: Raw 16-bit value (0-65535) with dedicated sign bit.

    Returns:
        Signed integer (-32767 to 32767)
    """
    if raw & 0x8000:
        return -(raw & 0x7FFF)
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
