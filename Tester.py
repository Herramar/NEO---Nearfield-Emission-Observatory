from vxc_driver import VXC_Controller
import time

if __name__ == "__main__":
    Motors = VXC_Controller(port='COM3', baudrate=57600, timeout=1)
    Motors.connect()
    
    Motors.move_motor(1, 1500)
    Motors.move_motor(2, 1500)
    Motors.move_motor(3, 1500)

    Motors.disconnect()
