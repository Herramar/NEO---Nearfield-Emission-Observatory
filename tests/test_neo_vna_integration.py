import sys
import types
import unittest
from unittest.mock import patch

import numpy as np

if "serial" not in sys.modules:
    sys.modules["serial"] = types.ModuleType("serial")

from neo.neo_driver import NEO_Controller


class FakeSerialController:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.connection = None
        self.disconnected = False
        self.__class__.instances.append(self)

    def connect(self):
        self.connection = object()
        return True

    def disconnect(self):
        self.disconnected = True
        self.connection = None


class FakeVNAController(FakeSerialController):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.measurement_configuration = None
        self.sweep_configuration = None

    @property
    def is_connected(self):
        return self.connection is not None

    def configure_measurement(self, **kwargs):
        self.measurement_configuration = kwargs

    def configure_sweep(self, **kwargs):
        self.sweep_configuration = kwargs

    def measure(self, **kwargs):
        self.measure_call = kwargs
        return np.array([[1.0e9, 0.5, -0.25]])


class NEOVNAIntegrationTests(unittest.TestCase):
    def setUp(self):
        FakeSerialController.instances = []
        FakeVNAController.instances = []

    def test_vna_is_owned_configured_measured_and_disconnected_by_neo(self):
        with (
            patch("neo.neo_driver.VXC_Controller", FakeSerialController),
            patch("neo.neo_driver.VRO_Controller", FakeSerialController),
            patch("neo.neo_driver.VNA_Controller", FakeVNAController),
        ):
            neo = NEO_Controller(
                "COM3",
                "COM4",
                "COM5",
                "192.0.2.10",
                timeoutVNA=12.5,
                resourceNameVNA="TCPIP0::192.0.2.10::hislip0::INSTR",
            )

            self.assertTrue(neo.connect())
            self.assertIsInstance(neo.Motors, FakeSerialController)
            self.assertIsInstance(neo.Readout_XY, FakeSerialController)
            self.assertIsInstance(neo.Readout_Phi, FakeSerialController)
            self.assertIsInstance(neo.VNA, FakeVNAController)
            self.assertEqual(neo.VNA.kwargs["host"], "192.0.2.10")
            self.assertEqual(neo.VNA.kwargs["timeout"], 12.5)

            neo.configure_vna(
                parameter="S21",
                channel=1,
                trace_name="NEO_S21",
                start_frequency=1.0e9,
                stop_frequency=2.0e9,
                points=201,
                if_bandwidth=1.0e3,
                source_power=-20,
            )
            self.assertEqual(
                neo.VNA.measurement_configuration,
                {"parameter": "S21", "channel": 1, "trace_name": "NEO_S21"},
            )
            self.assertEqual(neo.VNA.sweep_configuration["points"], 201)

            measurement = neo.measure_vna(trace_name="NEO_S21")
            np.testing.assert_allclose(measurement, [[1.0e9, 0.5, -0.25]])
            self.assertEqual(
                neo.VNA.measure_call,
                {"channel": 1, "trace_name": "NEO_S21", "trigger": True},
            )

            controllers = (neo.Motors, neo.Readout_XY, neo.Readout_Phi, neo.VNA)
            neo.disconnect()
            self.assertTrue(all(item.disconnected for item in controllers))

    def test_vna_configuration_requires_all_sweep_arguments(self):
        with (
            patch("neo.neo_driver.VXC_Controller", FakeSerialController),
            patch("neo.neo_driver.VRO_Controller", FakeSerialController),
            patch("neo.neo_driver.VNA_Controller", FakeVNAController),
        ):
            neo = NEO_Controller("COM3", "COM4", "COM5", "192.0.2.10")
            self.assertTrue(neo.connect())
            with self.assertRaisesRegex(ValueError, "required"):
                neo.configure_vna(start_frequency=1.0e9, stop_frequency=2.0e9)


if __name__ == "__main__":
    unittest.main()
