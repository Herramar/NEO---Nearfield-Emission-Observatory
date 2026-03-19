import serial
import time
from vxc_driver import VXC_Controller
from vro_driver import VRO_Controller

class NEO_Controller:
    def __init__(self, port_Motors, port_Readout_XY, port_Readout_Phi, baudrate=115200, timeout=1, echo=1):
        self.port_Motors = port_Motors
        self.port_Readout_XY = port_Readout_XY
        self.port_Readout_Phi = port_Readout_Phi
        self.baudrate = baudrate
        self.timeout = timeout
        self.echo = echo
        self.connection = None

    def connect(self):
        print("\n[SYSTEM] Connecting...\n")
        self.Motors = VXC_Controller(port=self.port_Motors, baudrate=57600, timeout=1) # COM3
        self.Motors.connect()
        self.Readout_XY = VRO_Controller(port=self.port_Readout_XY, baudrate=57600, timeout=1, type = 0) # COM4
        self.Readout_XY.connect()
        self.Readout_Phi = VRO_Controller(port=self.port_Readout_Phi, baudrate=57600, timeout=1, type = 1) # COM5
        self.Readout_Phi.connect()
        print("\n")

        self.connection = self.Motors.connection and self.Readout_XY.connection and self.Readout_Phi.connection

    def disconnect(self):
        print("\n[SYSTEM] Disconnecting...\n")
        self.Motors.disconnect()
        self.Readout_XY.disconnect()
        self.Readout_Phi.disconnect()
        print("\n")