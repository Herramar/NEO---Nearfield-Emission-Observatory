from neo_driver import NEO_Controller
import time


Horizontal_Length = 100 #mm
Vertical_Length = 100 #mm
Step_Size = 1 #mm

if __name__ == "__main__":


    # COM3 = VXC Motors.   COM4 = Readout XY.   COM5 = Readout Phi
    NEO = NEO_Controller('COM3', 'COM4', 'COM5', baudrateVXC=57600, baudrateVRO=9600, timeout=1, echo=0)
    
    if not NEO.connect():
        print("[ERROR] Failed to connect to NEO.")
        NEO.disconnect()
        exit(1)


    if not NEO.calibrate():
        print("[ERROR] Failed to calibrate NEO.")
        NEO.disconnect()
        exit(1)

    time.sleep(5)

    NEO.disconnect()
