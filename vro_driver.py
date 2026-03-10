import serial
import time

class VRO_Controller:
    def __init__(self, port, baudrate=115200, timeout=1, echo=1):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.echo = echo
        self.connection = None

    def connect(self):
        try:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )

            time.sleep(2)

            print(f"[SYSTEM] Connection established to {self.port}\n")
            if self.connection and self.connection.is_open:
                if self.echo == 1:
                    message = "E,"
                    self.connection.write(f"{message}".encode('utf-8'))
                    print(f"[CONFIG] Echo: ON")
                else:
                    message = "F,"
                    self.connection.write(f"{message}".encode('utf-8'))
                    print(f"[CONFIG] Echo: OFF")

            else:
                print(f"[ERROR] Could not connect to motors\n")

        except Exception as e:
            print(f"[ERROR] Could not connect: {e}\n")