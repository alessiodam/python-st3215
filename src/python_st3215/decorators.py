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
            from .errors import BroadcastOperationError

            raise BroadcastOperationError(
                f"{func.__name__} cannot be used with broadcast ID 254."
            )
        return func(self, servo_id, *args, **kwargs)

    return wrapper


def validate_value_range(min_val: int, max_val: int) -> Callable[[F], F]:
    """
    Decorator to validate that a value parameter is within the specified range.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(self: Any, value: int, *args: Any, **kwargs: Any) -> Any:
            if not (min_val <= value <= max_val):
                raise ValueError(
                    f"{func.__name__}: value {value} out of range [{min_val}, {max_val}]"
                )
            return func(self, value, *args, **kwargs)

        return wrapper  # type: ignore[return-value]

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
