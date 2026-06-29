import serial
import time

class VRO_Controller:


    def __init__(self, port, baudrate=9600, timeout=1, echo=1, type = 0):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.echo = echo
        self.connection = None
        self.type = type


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

            if self.type == 0:
                print(f"[SYSTEM] Connection established to {self.port} for XY VRO")
            else:
                print(f"[SYSTEM] Connection established to {self.port} for Phi VRO")

            if self.connection and self.connection.is_open:
                if self.echo == 1:
                    message = "E,"
                    self.connection.write(f"{message}".encode('utf-8'))
                    print(f"[CONFIG] Echo: ON")
                else:
                    message = "F,"
                    self.connection.write(f"{message}".encode('utf-8'))
                message = "Q,"
                self.connection.write(f"{message}".encode('utf-8'))
                return True
            else:
                print(f"[ERROR] Could not connect to VRO\n")
                return False

        except Exception as e:
            print(f"[ERROR] Could not connect: {e}\n")
            return False
    
    def getPosition(self, axis=0):
        if self.connection and self.connection.is_open:
            
            if axis == 0:
                message = "X"
            else:
                message = "Y"

            self.connection.write(f"{message}".encode('utf-8'))
            #print(f"[{self.port}] Sent: {message}")
            response = self.connection.read_until(b'\r').decode('utf-8').strip()
            #print(f"[{self.port}] Received: {response}")
            return response
        else:
            if self.type == 0:
                print(f"[ERROR] Could not connect to XY VRO\n")
            else:
                print(f"[ERROR] Could not connect to Phi VRO\n")
            return None
            

    def setHome(self):
        if self.connection and self.connection.is_open:
            message = "C"
            self.connection.write(f"{message}".encode('utf-8'))
            #print(f"[{self.port}] Sent: {message}")
            response = self.connection.read_until(b'\r').decode('utf-8').strip()
            #print(f"[{self.port}] Received: {response}")
            return response
        else:
            if self.type == 0:
                print(f"[ERROR] Could not connect to XY VRO\n")
            else:
                print(f"[ERROR] Could not connect to Phi VRO\n")
            return None


    def disconnect(self):
        message = "Q,"
        self.connection.write(f"{message}".encode('utf-8'))
        if self.type == 0:
            print(f"[SYSTEM] "+self.port+" - VRO XY disconnected.")
        else:
            print(f"[SYSTEM] "+self.port+" - VRO Phi disconnected.")

        