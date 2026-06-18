import serial
import time
from vxc_driver import VXC_Controller
from vro_driver import VRO_Controller

class NEO_Controller:


    def __init__(self, port_Motors, port_Readout_XY, port_Readout_Phi, motorSpeed=200, baudrateVRO=9600, baudrateVXC=57600, timeout=1, echo=1):
        self.port_Motors = port_Motors
        self.port_Readout_XY = port_Readout_XY
        self.port_Readout_Phi = port_Readout_Phi
        self.motorSpeed = motorSpeed
        self.baudrateVRO = baudrateVRO
        self.baudrateVXC = baudrateVXC
        self.timeout = timeout
        self.echo = echo
        self.connection = None


    def connect(self):
        print("\n[SYSTEM] Connecting...\n")

        # COM3 - VXC Motors
        self.Motors = VXC_Controller(port=self.port_Motors, motorSpeed = self.motorSpeed, baudrate = self.baudrateVXC, timeout= self.timeout, echo=self.echo) 
        
        # COM4 - Readout XY 
        self.Readout_XY = VRO_Controller(port=self.port_Readout_XY, baudrate = self.baudrateVRO, timeout= self.timeout, echo=self.echo, type = 0) # COM4
        
        # COM5 - Readout Phi
        self.Readout_Phi = VRO_Controller(port=self.port_Readout_Phi, baudrate = self.baudrateVRO, timeout= self.timeout, echo=self.echo, type = 1) # COM5
        
        self.connection = self.Motors.connect() and self.Readout_XY.connect() and self.Readout_Phi.connect()

        if not self.connection:
            return False
        else:
            print("\n[SYSTEM] Setting Home Coordinates...\n")
            return True


    def calibrate(self, step):

        if not self.Readout_XY.setHome() and self.Readout_Phi.setHome():
            print(f"[ERROR] Failed to set home coordinates.")
            return False

        print("\n[SYSTEM] Calibrating...\n")

        self.Motors.move_motor(1, 100)
        self.Motors.move_motor(2, 100)
        self.Motors.move_motor(3, 100)

        # Allow time for readout to update after movement
        time.sleep(0.2)

        #mm/step
        self.X_sensitivity = float(self.Readout_XY.getPosition(0))/100000
        self.Z_sensitivity = float(self.Readout_XY.getPosition(1))/100000
        self.Phi_sensitivity = float(self.Readout_Phi.getPosition(0))/100

        print(f"[SYSTEM] X sensitivity: {self.X_sensitivity} mm/step")
        print(f"[SYSTEM] Z sensitivity: {self.Z_sensitivity} mm/step")
        print(f"[SYSTEM] Phi sensitivity: {self.Phi_sensitivity} degrees/step\n")

        print(f"[SYSTEM] Calibration completed successfully, returning to home position.\n")

        if self.home():
            self.move_up(step)
            self.move_right(step)
            return True
        
        return False


    def home(self):
        print("\n[SYSTEM] Homing...\n")
        if self.Motors.home():
            print(f"[SYSTEM] Motors homed successfully.")
            return True
        else:
            print(f"[ERROR] Failed to home motors.")
            return False
        print("\n")


    def spiral_traverse(self, m, n, distance):
        x = (m-1)//2
        y = (n-1)//2
        yield x, y
        count = 1
        steps = 1
        dirs = [(0,1),(1,0),(0,-1),(-1,0)]  # derecha, abajo, izquierda, arriba
        move = [self.move_right, self.move_down, self.move_left, self.move_up]  # derecha, abajo, izquierda, arriba
        dir_idx = 0
        while count < m*n:
            print(f"[SYSTEM] Current direction: {['Right', 'Down', 'Left', 'Up'][dir_idx % 4]}")
            print(f"[SYSTEM] Total count: {count}/{m*n}\n")
            for _ in range(2):
                dx, dy = dirs[dir_idx % 4]
                move_func = move[dir_idx % 4]
                for _ in range(steps):
                    if not move_func(distance):
                        print(f"[ERROR] Failed to move {['Right', 'Down', 'Left', 'Up'][dir_idx % 4]}")
                        return False
                    x += dx; y += dy
                    if 0 <= x < m and 0 <= y < n:
                        yield x, y
                        count += 1
                        if count >= m*n:
                            print(f"[SYSTEM] Spiral traversal completed successfully.")
                            return True
                dir_idx += 1
            steps += 1


    def move_up(self, distance):
        if self.Motors.move_motor(2, round(distance/self.Z_sensitivity)):
            return True
        else:
            return False


    def move_down(self, distance):
        if self.Motors.move_motor(2, round(-distance/self.Z_sensitivity)):
            return True
        else:            
            return False


    def move_left(self, distance):
        if self.Motors.move_motor(1, round(-distance/self.X_sensitivity)):
            return True
        else:
            return False


    def move_right(self, distance):
        if self.Motors.move_motor(1, round(distance/self.X_sensitivity)):
            return True
        else:
            return False


    def rotate(self, Phi):
        if self.Motors.move_motor(3, round(Phi/self.Phi_sensitivity)):
            return True
        else:
            return False
    
    
    def disconnect(self):
        print("\n[SYSTEM] Disconnecting...\n")
        self.Motors.disconnect()
        self.Readout_XY.disconnect()
        self.Readout_Phi.disconnect()
        print("\n")