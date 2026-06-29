import serial
import time
import numpy as np
from vxc_driver import VXC_Controller
from vro_driver import VRO_Controller

class NEO_Controller:

    def __init__(self, port_Motors, port_Readout_XY, port_Readout_Phi, motorSpeed=100, baudrateVRO=9600, baudrateVXC=57600, timeout=1, echo=1):
        self.port_Motors = port_Motors
        self.port_Readout_XY = port_Readout_XY
        self.port_Readout_Phi = port_Readout_Phi
        self.motorSpeed = motorSpeed
        self.baudrateVRO = baudrateVRO
        self.baudrateVXC = baudrateVXC
        self.timeout = timeout
        self.echo = echo
        self.connection = None
        self.X_sensitivity = 1.0
        self.Z_sensitivity =  1.0
        self.Phi_sensitivity = 1.0


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


    def calibrate(self):

        if not self.Readout_XY.setHome() and self.Readout_Phi.setHome():
            print(f"[ERROR] Failed to set home coordinates.")
            return False

        print("\n[SYSTEM] Calibrating...\n")

        self.move_right(1000)
        self.move_up(1000)
        self.rotate(1000)

        # Allow time for readout to update after movement
        time.sleep(0.2)

        #mm/step
        self.X_sensitivity = round(float(self.Readout_XY.getPosition(0))/1000, 6)
        self.Z_sensitivity = round(float(self.Readout_XY.getPosition(1))/1000, 6)
        self.Phi_sensitivity = round(float(self.Readout_Phi.getPosition(0))/1000, 6)

        print(f"[SYSTEM] X sensitivity: {self.X_sensitivity} mm/step")
        print(f"[SYSTEM] Z sensitivity: {self.Z_sensitivity} mm/step")
        print(f"[SYSTEM] Phi sensitivity: {self.Phi_sensitivity} degrees/step\n")

        print(f"[SYSTEM] Calibration completed successfully, returning to home position.\n")
        
        return True


    def home(self, homePhi=True):
        print("\n[SYSTEM] Homing...")

        h_coord = float(self.Readout_XY.getPosition(0))
        v_coord = float(self.Readout_XY.getPosition(1))
        angle_coord = float(self.Readout_Phi.getPosition(0))

        if h_coord > 0:
            self.move_left(float(h_coord))
        else:
            self.move_right(float(h_coord))

        if v_coord > 0:
            self.move_down(float(v_coord))
        else:
            self.move_up(float(v_coord))

        if angle_coord > 0 and homePhi:
            self.rotate(float(-angle_coord))
        elif homePhi:
            self.rotate(float(angle_coord))

        print("[SYSTEM] Homed...\n")

        return True


    def measure(self, m, n, distance):
        print("\n[MEASUREMENT] Starting measurement...\n")
        phi_axis = 0
        x = (m-1)//2
        y = (n-1)//2
        order_matrix = np.zeros((m, n))  # Store the order of measurements
        position_matrix = np.zeros((m, n, 2))  # Store X, Y
        measurement_matrix = np.zeros((m, n))  # Store measurements
        count = 1
        steps = 1
        dirs = [(0,1),(1,0),(0,-1),(-1,0)]  # derecha, abajo, izquierda, arriba
        move = [self.move_right, self.move_down, self.move_left, self.move_up]  # derecha, abajo, izquierda, arriba
        dir_idx = 0
        while count < m*n:
            if count == 1:
                order_matrix[x, y] = 0
                measurement_matrix[x, y] = 1
                position_matrix[x, y, 0] = float(self.Readout_XY.getPosition(0))
                position_matrix[x, y, 1] = float(self.Readout_XY.getPosition(1))
            for _ in range(2):
                print(f"[MEASUREMENT] Current direction: {['Right', 'Down', 'Left', 'Up'][dir_idx % 4]}")
                print(f"[MEASUREMENT] Total count: {count}/{m*n}\n")
                dx, dy = dirs[dir_idx % 4]
                move_func = move[dir_idx % 4]
                for _ in range(steps):
                    if not move_func(distance):
                        print(f"[ERROR] Failed to move {['Right', 'Down', 'Left', 'Up'][dir_idx % 4]}")
                        return False
                    x += dx; y += dy
                    order_matrix[x, y] = count
                    time.sleep(0.2)  # Allow time for readout to update after movement
                    position_matrix[x, y, 0] = float(self.Readout_XY.getPosition(0))
                    position_matrix[x, y, 1] = float(self.Readout_XY.getPosition(1))
                    measurement_matrix[x, y] = 1
                    if 0 <= x < m and 0 <= y < n:
                        count += 1
                        if count >= m*n:
                            print(f"[MEASUREMENT] Spiral traversal completed successfully.")
                            return order_matrix, position_matrix, measurement_matrix
                dir_idx += 1
            steps += 1


    def move_up(self, distance):
        if self.Motors.move_motor(2, round(-distance/self.Z_sensitivity)):
            return True
        else:
            return False


    def move_down(self, distance):
        if self.Motors.move_motor(2, round(distance/self.Z_sensitivity)):
            return True
        else:            
            return False


    def move_left(self, distance):
        if self.Motors.move_motor(1, round(distance/self.X_sensitivity)):
            return True
        else:
            return False


    def move_right(self, distance):
        if self.Motors.move_motor(1, round(-distance/self.X_sensitivity)):
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