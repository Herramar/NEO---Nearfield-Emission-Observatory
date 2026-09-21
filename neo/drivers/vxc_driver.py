import serial
import time

class VXC_Controller:


    def __init__(self, port, motorSpeed=500, baudrate=57600, timeout=1, echo=1):
        self.number_of_motors = 3
        self.port = port
        self.motorSpeed = motorSpeed
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

            print(f"[SYSTEM] Connection established to {self.port} for VXC Motors.")
            if self.connection and self.connection.is_open:
                self.connection.reset_input_buffer()
                self.connection.reset_output_buffer()
                if self.echo == 1:
                    message = "E C S1M" + str(self.motorSpeed) + ", S2M" + str(self.motorSpeed) + ", S3M" + str(self.motorSpeed) + "R"
                    print(f"[CONFIG] Echo: ON")
                else:
                    message = "F C S1M" + str(self.motorSpeed) + ", S2M" + str(self.motorSpeed) + ", S3M" + str(self.motorSpeed) + "R"
                    print(f"[CONFIG] Echo: OFF")

                self.connection.write(f"{message}".encode('utf-8'))
                return True
            else:
                print(f"[ERROR] Could not connect to motors\n")
                return False


        except Exception as e:
            print(f"[ERROR] Could not connect: {e}\n")
            return False
        

    def move_motor(self, motor_number, steps):
        if self.connection and self.connection.is_open:
            motor_number = int(motor_number)
            if motor_number > 0 and motor_number <4:
                # Clear buffer before sending to ensure clean state
                self.connection.reset_input_buffer()
                self.connection.reset_output_buffer()
                
                # Adding \n because terminals usually wait for a newline to display
                message = "C I" + str(motor_number) + "M" + str(steps) + ", R"
                self.connection.write(f"{message}".encode('utf-8'))
                #print(f"[{self.port}] Sent: {message}")
                if self.wait_for_completion():
                    time.sleep(0.2)  # Additional delay to ensure movement is fully settled
                    return True
                else:
                    return False
            else:
                print(f"[ERROR] Motor not found [1,2,3] for [Horizontal, Vertical, Rotary]\n")
        else:
            print(f"[ERROR] Could not connect to motors\n")

    def wait_for_completion(self, timeout=30):
        """Blocks until the '^' character is received or timeout occurs."""
        start_time = time.time()
        buffer = ""
        
        #print("[SYSTEM] Waiting for movement to finish...")
        
        while (time.time() - start_time) < timeout:
            if self.connection.in_waiting > 0:
                # Read one byte at a time to catch the '^' immediately
                char = self.connection.read(1).decode('utf-8')
                if char == '^':
                    #print(f"[{self.port}] Movement complete (^ received)")
                    return True
            time.sleep(0.01) # Tiny sleep to prevent 100% CPU usage
            
        print("[ERROR] Movement timed out!")
        return False


    def disconnect(self):
        message = "Q,"
        self.connection.write(f"{message}".encode('utf-8'))
        print(f"[SYSTEM] "+self.port+" - VXC Motors disconnected.")
