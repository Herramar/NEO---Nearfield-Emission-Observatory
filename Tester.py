from neo_driver import NEO_Controller
import time
import numpy as np

Wait = 1
Horizontal_Length = 5 #mm
Vertical_Length = 5 #mm
Step_Size = 1 #mm

if __name__ == "__main__":


    # COM3 = VXC Motors.   COM4 = Readout XY.   COM5 = Readout Phi
    NEO = NEO_Controller('COM3', 'COM4', 'COM5', motorSpeed=100, baudrateVXC=57600, baudrateVRO=9600, timeout=1, echo=0)
    
    if not NEO.connect():
        print("[ERROR] Failed to connect to NEO.")
        NEO.disconnect()
        exit(1)

    time.sleep(Wait)

    if not NEO.calibrate() or not NEO.home():
        print("[ERROR] Failed to calibrate NEO.")
        NEO.disconnect()
        exit(1)

    time.sleep(Wait)

    order = np.zeros((Horizontal_Length, Vertical_Length, 2))  # Store the order of measurements for Phi=0 and Phi=90
    positions = np.zeros((Horizontal_Length, Vertical_Length, 4))  # Store X, Z, positions for Phi=0 and Phi=90
    measurements = np.zeros((Horizontal_Length, Vertical_Length, 2))  # Store measurements for Phi=0 and Phi=90

    order[:,:,0], positions[:,:,0:2], measurements[:,:,0] = NEO.measure(Horizontal_Length, Vertical_Length, Step_Size)

    if not NEO.home(homePhi=False):
        print("[ERROR] Failed to home NEO.")
        NEO.disconnect()
        exit(1)


    print("\n[SYSTEM] Rotating to Phi=90...\n")
    NEO.rotate(90)

    order[:,:,1], positions[:,:,2:4], measurements[:,:,1] = NEO.measure(Horizontal_Length, Vertical_Length, Step_Size)

    print("\n[SYSTEM] Measurement completed successfully.\n")

    if not NEO.home():
        print("[ERROR] Failed to home NEO.")
        NEO.disconnect()
        exit(1)

    print("\n[RESULTS] Phi = 0:")

    print("\n[RESULTS] Order:")
    print(order[:, :, 0])

    print("\n[RESULTS] X Positions:")    
    print(positions[:, :, 0])
    print("\n[RESULTS] Z Positions:") 
    print(positions[:, :, 1])

    print("\n[RESULTS] Measurements:")
    print(measurements[:, :, 0])

    print("\n\n[RESULTS] Phi = 90:")

    print("\n[RESULTS] Order:")
    print(order[:, :, 1])

    print("\n[RESULTS] X Positions:")
    print(positions[:, :, 2])
    print("\n[RESULTS] Z Positions:") 
    print(positions[:, :, 3])

    print("\n[RESULTS] Measurements:")
    print(measurements[:, :, 1])

    time.sleep(Wait)

    NEO.disconnect()
