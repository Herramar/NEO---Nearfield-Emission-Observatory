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


MODULE_PATH = Path(__file__).parents[1] / "neo" / "drivers" / "vro_driver.py"
SPEC = importlib.util.spec_from_file_location("vro_driver", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
VRO_Controller = MODULE.VRO_Controller


class FakeSerial:
    def __init__(self, responses=(), is_open=True, **kwargs):
        self.kwargs = kwargs
        self.responses = list(responses)
        self.is_open = is_open
        self.writes = []

    def write(self, data):
        self.writes.append(data)

    def read_until(self, terminator):
        if terminator != b"\r":
            raise AssertionError(f"Unexpected terminator: {terminator!r}")
        return self.responses.pop(0)


class VRODriverTests(unittest.TestCase):
    def test_connect_configures_serial_port_and_echo(self):
        connection = FakeSerial()
        with patch.object(MODULE.serial, "Serial", return_value=connection) as serial:
            vro = VRO_Controller("COM4", baudrate=19200, timeout=2.5, echo=1)
            self.assertTrue(vro.connect())

        serial.assert_called_once_with(
            port="COM4",
            baudrate=19200,
            timeout=2.5,
            bytesize=MODULE.serial.EIGHTBITS,
            parity=MODULE.serial.PARITY_NONE,
            stopbits=MODULE.serial.STOPBITS_ONE,
        )
        self.assertEqual(connection.writes, [b"E,", b"Q,"])

    def test_connect_can_disable_echo(self):
        connection = FakeSerial()
        with patch.object(MODULE.serial, "Serial", return_value=connection):
            vro = VRO_Controller("COM5", echo=0, type=1)
            self.assertTrue(vro.connect())

        self.assertEqual(connection.writes, [b"F,", b"Q,"])

    def test_position_and_home_commands_return_stripped_responses(self):
        connection = FakeSerial([b" 12.50\r", b"-3.25\r", b"0.00\r"])
        vro = VRO_Controller("COM4")
        vro.connection = connection

        self.assertEqual(vro.getPosition(axis=0), "12.50")
        self.assertEqual(vro.getPosition(axis=1), "-3.25")
        self.assertEqual(vro.setHome(), "0.00")
        self.assertEqual(connection.writes, [b"X", b"Y", b"C"])

    def test_disconnected_queries_return_none(self):
        vro = VRO_Controller("COM4")
        self.assertIsNone(vro.getPosition())
        self.assertIsNone(vro.setHome())

    def test_connection_error_is_reported_as_false(self):
        with patch.object(MODULE.serial, "Serial", side_effect=OSError("port busy")):
            self.assertFalse(VRO_Controller("COM4").connect())

    def test_disconnect_sends_quit_command(self):
        connection = FakeSerial()
        vro = VRO_Controller("COM4")
        vro.connection = connection
        vro.disconnect()
        self.assertEqual(connection.writes, [b"Q,"])


if __name__ == "__main__":
    unittest.main()
