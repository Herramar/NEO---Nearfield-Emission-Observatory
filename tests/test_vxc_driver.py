import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


try:
    import serial  # noqa: F401
except ImportError:
    serial = types.ModuleType("serial")
    sys.modules["serial"] = serial

serial.EIGHTBITS = getattr(serial, "EIGHTBITS", 8)
serial.PARITY_NONE = getattr(serial, "PARITY_NONE", "N")
serial.STOPBITS_ONE = getattr(serial, "STOPBITS_ONE", 1)
serial.Serial = getattr(serial, "Serial", None)


MODULE_PATH = Path(__file__).parents[1] / "neo" / "drivers" / "vxc_driver.py"
SPEC = importlib.util.spec_from_file_location("vxc_driver", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
VXC_Controller = MODULE.VXC_Controller


class FakeSerial:
    def __init__(self, incoming=b"", is_open=True, **kwargs):
        self.kwargs = kwargs
        self.incoming = bytearray(incoming)
        self.is_open = is_open
        self.writes = []
        self.input_resets = 0
        self.output_resets = 0

    @property
    def in_waiting(self):
        return len(self.incoming)

    def write(self, data):
        self.writes.append(data)

    def read(self, size):
        data = bytes(self.incoming[:size])
        del self.incoming[:size]
        return data

    def reset_input_buffer(self):
        self.input_resets += 1

    def reset_output_buffer(self):
        self.output_resets += 1


class VXCDriverTests(unittest.TestCase):
    def test_connect_configures_three_motor_speeds(self):
        connection = FakeSerial()
        with patch.object(MODULE.serial, "Serial", return_value=connection) as serial:
            vxc = VXC_Controller("COM3", motorSpeed=750, timeout=2)
            self.assertTrue(vxc.connect())

        serial.assert_called_once_with(
            port="COM3",
            baudrate=57600,
            timeout=2,
            bytesize=MODULE.serial.EIGHTBITS,
            parity=MODULE.serial.PARITY_NONE,
            stopbits=MODULE.serial.STOPBITS_ONE,
        )
        self.assertEqual(connection.input_resets, 1)
        self.assertEqual(connection.output_resets, 1)
        self.assertEqual(connection.writes, [b"E C S1M750, S2M750, S3M750R"])

    def test_connect_can_disable_echo(self):
        connection = FakeSerial()
        with patch.object(MODULE.serial, "Serial", return_value=connection):
            vxc = VXC_Controller("COM3", motorSpeed=400, echo=0)
            self.assertTrue(vxc.connect())

        self.assertEqual(connection.writes, [b"F C S1M400, S2M400, S3M400R"])

    def test_move_motor_writes_command_and_waits_for_completion(self):
        connection = FakeSerial()
        vxc = VXC_Controller("COM3")
        vxc.connection = connection

        with (
            patch.object(vxc, "wait_for_completion", return_value=True) as wait,
            patch.object(MODULE.time, "sleep") as sleep,
        ):
            self.assertTrue(vxc.move_motor(2, -125))

        self.assertEqual(connection.writes, [b"C I2M-125, R"])
        self.assertEqual(connection.input_resets, 1)
        self.assertEqual(connection.output_resets, 1)
        wait.assert_called_once_with()
        sleep.assert_called_once_with(0.2)

    def test_invalid_motor_is_rejected_without_writing(self):
        connection = FakeSerial()
        vxc = VXC_Controller("COM3")
        vxc.connection = connection
        self.assertIsNone(vxc.move_motor(4, 100))
        self.assertEqual(connection.writes, [])

    def test_wait_for_completion_ignores_data_until_caret(self):
        vxc = VXC_Controller("COM3")
        vxc.connection = FakeSerial(b"x^")
        with patch.object(MODULE.time, "sleep"):
            self.assertTrue(vxc.wait_for_completion(timeout=1))

    def test_wait_for_completion_times_out(self):
        vxc = VXC_Controller("COM3")
        vxc.connection = FakeSerial()
        with (
            patch.object(MODULE.time, "time", side_effect=[0.0, 31.0]),
            patch.object(MODULE.time, "sleep"),
        ):
            self.assertFalse(vxc.wait_for_completion(timeout=30))

    def test_connection_error_is_reported_as_false(self):
        with patch.object(MODULE.serial, "Serial", side_effect=OSError("port busy")):
            self.assertFalse(VXC_Controller("COM3").connect())

    def test_disconnect_sends_quit_command(self):
        connection = FakeSerial()
        vxc = VXC_Controller("COM3")
        vxc.connection = connection
        vxc.disconnect()
        self.assertEqual(connection.writes, [b"Q,"])


if __name__ == "__main__":
    unittest.main()
