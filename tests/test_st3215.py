from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from python_st3215.decorators import (
    decode_signed_word,
    encode_signed_word,
    encode_unsigned_word,
)
from python_st3215.errors import (
    BroadcastOperationError,
    ChecksumError,
    CommunicationTimeoutError,
    InvalidIDError,
    InvalidInstructionError,
    ServoNotRespondingError,
    ServoStatusError,
)
from python_st3215.instructions import Instruction
from python_st3215.st3215 import ST3215


def _make_ctrl(read_data: bytes = b"") -> tuple[ST3215, MagicMock]:
    """Return (controller, mock_serial) with ser.read returning read_data."""
    mock_ser = MagicMock()
    mock_ser.is_open = True
    mock_ser.timeout = 0.002
    mock_ser.read.return_value = read_data
    ctrl = ST3215(ser=mock_ser)
    return ctrl, mock_ser


def _valid_response(servo_id: int, params: bytes = b"") -> bytes:
    """Build a well-formed response packet."""
    length = len(params) + 2
    error = 0
    checksum_base = servo_id + length + error + sum(params)
    checksum = (~checksum_base) & 0xFF
    return bytes([0xFF, 0xFF, servo_id, length, error]) + params + bytes([checksum])


def _ping_response(servo_id: int) -> bytes:
    return _valid_response(servo_id)


class TestInit:
    def test_raises_without_port_or_ser(self):
        with pytest.raises(ValueError):
            ST3215()

    def test_accepts_mock_ser(self):
        ctrl, _ = _make_ctrl()
        assert ctrl.is_connected()

    def test_broadcast_servo_created(self):
        ctrl, _ = _make_ctrl()
        assert ctrl.broadcast.id == 254

    def test_close(self):
        ctrl, mock_ser = _make_ctrl()
        ctrl.close()
        mock_ser.close.assert_called_once()

    def test_context_manager(self):
        mock_ser = MagicMock()
        mock_ser.is_open = True
        mock_ser.timeout = 0.002
        mock_ser.read.return_value = b""
        with ST3215(ser=mock_ser) as ctrl:
            assert ctrl.is_connected()
        mock_ser.close.assert_called()

    def test_is_connected_false_when_closed(self):
        ctrl, mock_ser = _make_ctrl()
        mock_ser.is_open = False
        assert not ctrl.is_connected()


class TestBuildPacket:
    def test_basic_ping_packet(self):
        ctrl, _ = _make_ctrl()
        pkt = ctrl.build_packet(1, Instruction.PING)
        assert pkt[0:2] == b"\xff\xff"
        assert pkt[2] == 1  # servo id
        assert pkt[3] == 2  # length = 0 params + 2
        assert pkt[4] == Instruction.PING

    def test_checksum_correctness(self):
        ctrl, _ = _make_ctrl()
        pkt = ctrl.build_packet(1, Instruction.PING)
        checksum_base = pkt[2] + pkt[3] + pkt[4]
        expected = (~checksum_base) & 0xFF
        assert pkt[-1] == expected

    def test_packet_with_params(self):
        ctrl, _ = _make_ctrl()
        params = [0x2A, 0x02]
        pkt = ctrl.build_packet(5, Instruction.READ, params)
        assert pkt[3] == len(params) + 2

    def test_invalid_id_raises(self):
        ctrl, _ = _make_ctrl()
        with pytest.raises(InvalidIDError):
            ctrl.build_packet(255, Instruction.PING)

    def test_invalid_instruction_raises(self):
        ctrl, _ = _make_ctrl()
        with pytest.raises(InvalidInstructionError):
            ctrl.build_packet(1, 0xFF)

    def test_broadcast_id_allowed(self):
        ctrl, _ = _make_ctrl()
        pkt = ctrl.build_packet(254, Instruction.SYNC_WRITE, [0x28, 0x01, 0x01, 0x01])
        assert pkt[2] == 254


class TestParseResponse:
    def test_valid_response(self):
        ctrl, _ = _make_ctrl()
        data = _valid_response(1, b"\x05\x0a")
        parsed = ctrl.parse_response(data)
        assert parsed is not None
        assert parsed["id"] == 1
        assert parsed["error"] == 0
        assert parsed["checksum_valid"] is True
        assert parsed["parameters"] == b"\x05\x0a"

    def test_too_short_returns_none(self):
        ctrl, _ = _make_ctrl()
        assert ctrl.parse_response(b"\xff\xff\x01") is None

    def test_checksum_mismatch_raises(self):
        ctrl, _ = _make_ctrl()
        data = bytearray(_valid_response(1))
        data[-1] ^= 0xFF  # corrupt checksum
        with pytest.raises(ChecksumError):
            ctrl.parse_response(bytes(data))

    def test_error_status_no_raise_by_default(self):
        ctrl, _ = _make_ctrl()
        servo_id = 1
        length = 2
        error = 0x04
        checksum = (~(servo_id + length + error)) & 0xFF
        data = bytes([0xFF, 0xFF, servo_id, length, error, checksum])
        parsed = ctrl.parse_response(data)
        assert parsed is not None
        assert parsed["error"] == 0x04

    def test_error_status_raises_when_flag_set(self):
        ctrl, _ = _make_ctrl()
        servo_id = 1
        length = 2
        error = 0x04
        checksum = (~(servo_id + length + error)) & 0xFF
        data = bytes([0xFF, 0xFF, servo_id, length, error, checksum])
        with pytest.raises(ServoStatusError):
            ctrl.parse_response(data, raise_on_error=True)

    def test_no_params_empty_bytes(self):
        ctrl, _ = _make_ctrl()
        data = _valid_response(3)
        parsed = ctrl.parse_response(data)
        assert parsed["parameters"] == b""


class TestReadResponse:
    def test_strips_sent_packet_echo(self):
        sent = b"\xff\xff\x01\x02\x01\xfb"
        reply = _valid_response(1)
        ctrl, mock_ser = _make_ctrl(read_data=sent + reply)
        result = ctrl.read_response(sent)
        assert result == reply

    def test_no_echo_returns_raw(self):
        reply = _valid_response(1)
        ctrl, mock_ser = _make_ctrl(read_data=reply)
        sent = b"\xff\xff\x01\x02\x01\xfb"
        result = ctrl.read_response(sent)
        assert result == reply

    def test_empty_read_returns_none(self):
        ctrl, _ = _make_ctrl(read_data=b"")
        result = ctrl.read_response(b"\xff\xff\x01\x02\x01\xfb")
        assert result is None


class TestPing:
    def test_ping_returns_parsed_response(self):
        servo_id = 1
        reply = _ping_response(servo_id)
        ctrl, mock_ser = _make_ctrl(read_data=reply)
        result = ctrl.ping(servo_id, use_retry=False)
        assert result is not None
        assert result["id"] == servo_id

    def test_ping_broadcast_raises(self):
        ctrl, _ = _make_ctrl()
        with pytest.raises(BroadcastOperationError):
            ctrl.ping(254)

    def test_ping_no_response_returns_none(self):
        ctrl, _ = _make_ctrl(read_data=b"")
        result = ctrl.ping(1, use_retry=False)
        assert result is None

    def test_ping_with_retry_success(self):
        servo_id = 2
        reply = _ping_response(servo_id)
        ctrl, mock_ser = _make_ctrl()
        mock_ser.read.side_effect = [b"", b"", reply]
        result = ctrl.ping(servo_id, use_retry=True)
        assert result is not None


class TestWrapServo:
    def test_wrap_servo_with_verify(self):
        servo_id = 3
        reply = _ping_response(servo_id)
        ctrl, mock_ser = _make_ctrl(read_data=reply)
        servo = ctrl.wrap_servo(servo_id, verify=True)
        assert servo.id == servo_id

    def test_wrap_servo_no_response_raises(self):
        ctrl, _ = _make_ctrl(read_data=b"")
        with pytest.raises(ServoNotRespondingError):
            ctrl.wrap_servo(5, verify=True)

    def test_wrap_servo_no_verify(self):
        ctrl, _ = _make_ctrl()
        servo = ctrl.wrap_servo(7, verify=False)
        assert servo.id == 7

    def test_wrap_servo_broadcast_raises(self):
        ctrl, _ = _make_ctrl()
        with pytest.raises(BroadcastOperationError):
            ctrl.wrap_servo(254)


class TestListServos:
    def test_finds_responding_servo(self):
        servo_id = 1
        reply = _ping_response(servo_id)
        ctrl, mock_ser = _make_ctrl()

        def read_side_effect(size):
            last_write = mock_ser.write.call_args[0][0]
            if last_write[2] == servo_id:
                return reply
            return b""

        mock_ser.read.side_effect = read_side_effect
        found = ctrl.list_servos(start_id=0, end_id=5)
        assert servo_id in found

    def test_invalid_start_id_raises(self):
        ctrl, _ = _make_ctrl()
        with pytest.raises(InvalidIDError):
            ctrl.list_servos(start_id=254)

    def test_invalid_end_id_raises(self):
        ctrl, _ = _make_ctrl()
        with pytest.raises(InvalidIDError):
            ctrl.list_servos(end_id=254)

    def test_start_greater_than_end_raises(self):
        ctrl, _ = _make_ctrl()
        with pytest.raises(ValueError):
            ctrl.list_servos(start_id=10, end_id=5)

    def test_progress_callback_called(self):
        ctrl, mock_ser = _make_ctrl(read_data=b"")
        calls = []
        ctrl.list_servos(
            start_id=0, end_id=2, progress_callback=lambda c, t: calls.append((c, t))
        )
        assert len(calls) == 3
        assert calls[0] == (1, 3)
        assert calls[-1] == (3, 3)


class TestSyncWrite:
    def test_sync_write_sends_instruction(self):
        ctrl, mock_ser = _make_ctrl()
        ctrl._sync_write(0x28, 1, {1: [0x01], 2: [0x01]})
        mock_ser.write.assert_called_once()
        pkt = mock_ser.write.call_args[0][0]
        assert pkt[4] == Instruction.SYNC_WRITE

    def test_sync_write_wrong_data_length_raises(self):
        ctrl, _ = _make_ctrl()
        with pytest.raises(ValueError):
            ctrl._sync_write(0x28, 2, {1: [0x01]})  # expects 2 bytes, got 1


class TestEncodeDecode:
    @pytest.mark.parametrize("val", [0, 1, 100, 32767, -1, -100, -32767])
    def test_signed_word_roundtrip(self, val):
        low, high = encode_signed_word(val)
        raw = low | (high << 8)
        assert decode_signed_word(raw) == val

    def test_encode_signed_word_out_of_range(self):
        with pytest.raises(ValueError):
            encode_signed_word(32768)
        with pytest.raises(ValueError):
            encode_signed_word(-32768)

    @pytest.mark.parametrize("val", [0, 1, 255, 1000, 65535])
    def test_unsigned_word_roundtrip(self, val):
        low, high = encode_unsigned_word(val)
        assert (low | (high << 8)) == val

    def test_decode_negative(self):
        raw = 0x8064  # sign bit set, magnitude 100
        assert decode_signed_word(raw) == -100

    def test_decode_positive(self):
        assert decode_signed_word(0x0064) == 100


class TestValidateValueRange:
    def test_write_id_in_range(self):
        servo_id = 1
        reply = _valid_response(servo_id)
        ctrl, _ = _make_ctrl(read_data=reply)
        servo = ctrl.wrap_servo(servo_id, verify=False)
        ctrl.ser.read.return_value = reply
        servo.eeprom.write_id(10)

    def test_write_id_out_of_range_raises(self):
        ctrl, _ = _make_ctrl()
        servo = ctrl.wrap_servo(1, verify=False)
        with pytest.raises(ValueError):
            servo.eeprom.write_id(254)

    def test_write_baudrate_out_of_range_raises(self):
        ctrl, _ = _make_ctrl()
        servo = ctrl.wrap_servo(1, verify=False)
        with pytest.raises(ValueError):
            servo.eeprom.write_baudrate(8)


class TestValidateServoId:
    def test_broadcast_ping_raises(self):
        ctrl, _ = _make_ctrl()
        with pytest.raises(BroadcastOperationError):
            ctrl.ping(254)

    def test_valid_id_passes(self):
        ctrl, _ = _make_ctrl(read_data=_ping_response(1))
        result = ctrl.ping(1, use_retry=False)
        assert result is not None


class TestServoRegisters:
    def _ctrl_with_reply(self, servo_id: int, params: bytes):
        reply = _valid_response(servo_id, params)
        ctrl, mock_ser = _make_ctrl(read_data=reply)
        return ctrl, mock_ser

    def test_read_id(self):
        ctrl, _ = self._ctrl_with_reply(1, bytes([0x01]))
        servo = ctrl.wrap_servo(1, verify=False)
        assert servo.eeprom.read_id() == 1

    def test_read_torque_switch(self):
        ctrl, _ = self._ctrl_with_reply(1, bytes([0x01]))
        servo = ctrl.wrap_servo(1, verify=False)
        assert servo.sram.read_torque_switch() == 1

    def test_is_moving_true(self):
        ctrl, _ = self._ctrl_with_reply(1, bytes([0x01]))
        servo = ctrl.wrap_servo(1, verify=False)
        assert servo.sram.is_moving() is True

    def test_is_moving_false(self):
        ctrl, _ = self._ctrl_with_reply(1, bytes([0x00]))
        servo = ctrl.wrap_servo(1, verify=False)
        assert servo.sram.is_moving() is False

    def test_read_target_location_positive(self):
        val = 500
        low, high = encode_signed_word(val)
        ctrl, _ = self._ctrl_with_reply(1, bytes([low, high]))
        servo = ctrl.wrap_servo(1, verify=False)
        assert servo.sram.read_target_location() == val

    def test_read_target_location_negative(self):
        val = -300
        low, high = encode_signed_word(val)
        ctrl, _ = self._ctrl_with_reply(1, bytes([low, high]))
        servo = ctrl.wrap_servo(1, verify=False)
        assert servo.sram.read_target_location() == val

    def test_write_target_location_out_of_range_raises(self):
        ctrl, _ = _make_ctrl()
        servo = ctrl.wrap_servo(1, verify=False)
        with pytest.raises(ValueError):
            servo.sram.write_target_location(99999)


class TestBroadcastSync:
    def test_sync_write_torque_from_non_broadcast_raises(self):
        ctrl, _ = _make_ctrl()
        servo = ctrl.wrap_servo(1, verify=False)
        with pytest.raises(BroadcastOperationError):
            servo.sram.sync_write_torque_switch({1: 1})

    def test_sync_write_torque_from_broadcast(self):
        ctrl, mock_ser = _make_ctrl()
        ctrl.broadcast.sram.sync_write_torque_switch({1: 1, 2: 0})
        mock_ser.write.assert_called_once()

    def test_sync_read_current_location_from_non_broadcast_raises(self):
        ctrl, _ = _make_ctrl()
        servo = ctrl.wrap_servo(1, verify=False)
        with pytest.raises(BroadcastOperationError):
            servo.sram.sync_read_current_location([1, 2])

    def test_sync_read_current_location_no_response(self):
        ctrl, _ = _make_ctrl(read_data=b"")
        result = ctrl.broadcast.sram.sync_read_current_location([1, 2])
        assert result == {1: None, 2: None}


class TestRetryOperation:
    def test_returns_on_first_success(self):
        ctrl, _ = _make_ctrl()
        call_count = 0

        def op():
            nonlocal call_count
            call_count += 1
            return {"ok": True}

        result = ctrl._retry_operation(op, "test")
        assert result == {"ok": True}
        assert call_count == 1

    def test_retries_on_none(self):
        ctrl, _ = _make_ctrl()
        ctrl.retry_delay = 0
        ctrl.retry_count = 3
        call_count = 0

        def op():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return None
            return {"ok": True}

        result = ctrl._retry_operation(op, "test")
        assert result == {"ok": True}
        assert call_count == 3

    def test_raises_after_all_retries(self):
        ctrl, _ = _make_ctrl()
        ctrl.retry_delay = 0
        ctrl.retry_count = 2

        def op():
            raise ChecksumError("bad checksum")

        with pytest.raises(CommunicationTimeoutError):
            ctrl._retry_operation(op, "test")
