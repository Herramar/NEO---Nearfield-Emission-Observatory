from neo_driver import NEO_Controller
import time

if __name__ == "__main__":

    """
    COM3 = VXC Motors
    COM4 = Readout XY
    COM5 = Readout Phi
    """ 
    NEO = NEO_Controller('COM3', 'COM4', 'COM5', baudrate=115200, timeout=1, echo=1)
    NEO.connect()

    time.sleep(5)

    NEO.disconnect()
