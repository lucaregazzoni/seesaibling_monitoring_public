import threading    # Support threading
import time         # Various timing functions
import logging      # Functionality for automated error log creation
import signal       # Safe Ctrl+C/Z functionality
import pwmio        # For use with the main LED
import board        # GPIO assertion
import os           # filepath generation
import subprocess   # calling subprocess commands
from subprocess import call   # calling bash scripts in python
import csv          # writing to a .csv
import serial       # uart connection (for ina260)
import digitalio    # reading GPIO states (for leak sensor)

from picamera2.encoders import H264Encoder, Quality  # Camera functions
from picamera2 import Picamera2
from libcamera import controls

from w1thermsensor import W1ThermSensor # Temperature sensor functionality


class VideoLogFilter(logging.Filter):
    def filter(self, record):
        if "picamera2" in record.name or "libcamera" in record.name:
            record.msg = f"[Video] {record.msg}"
        return True  # Allow the message to be logged

# Main functionality of the system
class CameraSystem:
    def __init__(self):
        try:
            """Initialize system components."""
            self.stop_event = threading.Event()  # Shared stop signal for all threads

            # Configure event logging
            logging.basicConfig(
                filename="/home/pi/seesaibling/error/system_log.txt",
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
            )
            
            # Create a specific handler for camera logs
            video_handler = logging.StreamHandler()
            video_formatter = logging.Formatter("%(asctime)s - %(levelname)s - [Video] %(message)s")
            video_handler.setFormatter(video_formatter)

            # Apply this handler to picamera2 and libcamera loggers
            for lib in ["picamera2", "libcamera"]:
                logger = logging.getLogger(lib)
                logger.setLevel(logging.INFO)
                logger.addHandler(video_handler)
                logger.propagate = False  # Prevent double logging
            
            # Camera setup
            self.picam2 = Picamera2()
            self.picam2.configure(self.picam2.create_video_configuration(
                main={"size": (2028, 1080), "format": "YUV420"},
                controls={"FrameRate": 30}
            ))
            self.encoder = H264Encoder(bitrate=800000)

            # LED
            self.led_main = None
            self.fre = 50  # Main LED PWM frequency
            
            # Audio recording subprocess calling
            self.process = None

            # Register signal handlers
            signal.signal(signal.SIGINT, self.signal_handler)   # Ctrl + C
            signal.signal(signal.SIGTSTP, self.signal_handler)  # Ctrl + Z
            
            # Temperature sensor setup
            self.sensor = W1ThermSensor()
            self.temperature = None
            
            # uart connection setip
            self.ser = serial.Serial('/dev/serial0', baudrate=115200, timeout=0.5)
            
            # initiate variables for handling errors
            self.voltage = None # for low voltage shutdown
            self.voltage_treshold = 10.5 # set the lower voltage limit
            self.current = None # not used at the moment
            self.power = None   # not used at the moment
            
            # Setup leak sensor
            input_pin = board.D16  # Example: GPIO 7 (physical pin 26)
            self.leak_pin = digitalio.DigitalInOut(input_pin)
            self.leak_pin.direction = digitalio.Direction.INPUT
            self.leak_pin.pull = digitalio.Pull.DOWN  # Use pull-down to ensure LOW when no input
            
            # initialize status LEDs (at back of monitoring unit)    
            self.led_green1 = digitalio.DigitalInOut(board.D25)
            self.led_green2 = digitalio.DigitalInOut(board.D26)
            self.led_red1 = digitalio.DigitalInOut(board.D6)
            self.led_red2 = digitalio.DigitalInOut(board.D13)
            
            # put the leds into a list and define as output
            self.leds = [self.led_green1, self.led_green2, self.led_red1, self.led_red2]
            for led in self.leds:
                led.direction = digitalio.Direction.OUTPUT
            
            # You can add more setup code as needed
            logging.info("[System] Initialization successful.")
            
            # if everything worked, blink the green status leds, 3 times
            self.blink_status_leds(leds_to_blink=[self.led_green1, self.led_green2], times=3)
          
        except Exception as e:
            logging.error(f"[System] Error during initialization: {e}")
            self.signal_handler(None, None)  # Trigger shutdown on initialization failure
            raise  # Re-raise the exception to propagate it if necessary

    def signal_handler(self, sig, frame):
        """Handles termination signals and stops all running tasks safely."""
        logging.info("[System] Termination signal received, stopping...")
        print("\n[\033[4;31mSystem \033[0m] Termination signal received, stopping...")

        self.stop_event.set()  # Stop all threads
        try:
            self.picam2.stop_recording()
            # Reset the encoder state
            encoder.reset()  # This should be used if available, or set encoder to a new state
        except:
            pass  # Ignore if already stopped

        self.picam2.close()  # Properly release camera resources

        # Turn off LED safely
        if self.led_main is not None:
            self.led_main.duty_cycle = int((1100 / 20000) * 65535)  # LED OFF
            self.led_main.deinit()
            self.led_main = None
            
        logging.info("[System] Shutdown complete.")
        print("[\033[4;31mSystem\033[0m] Shutdown complete.")
        exit(0)
    
    def shut_down(self, voltage, leak):
        # shuts down rpi
        shutdown_time = 120 # seconds
        if type(self.voltage) == float or leak:
            if self.voltage <= self.voltage_treshold:
                error_reason = "Voltage treshold reached"
            elif leak: 
                error_reason = "Leak"
            else:
                error_reason = "Unknown"
            logging.error(f"[System] Error: {error_reason}, shutting down...")
            rc = call("./shutDown.sh")
            print(f"[\033[4;31mSystem\033[0m] Shutting down in {shutdown_time} seconds")
            # break from the while loop
            print("[\033[4;31mSystem\033[0m] Terminating all threads.")
            self.signal_handler(None, None)  # Manually invoke the shutdown method
            return(True)
    
    def error_sensors(self, duration):
        while not self.stop_event.is_set():
            while self.ser.in_waiting:
                temp = self.ser.readline().decode('utf-8').strip()
                if ',' in temp:  # Avoid clearing valid messages
                    data = temp
                    break
            else:
                data = self.ser.readline().decode('utf-8').strip()

            split_data = data.split(",")  
            split_data = [x.strip() for x in split_data]

            # Ensure the data is valid
            if len(split_data) == 3:
                try:
                    voltage, current, power = map(float, split_data)
                    if 5.0 <= voltage <= 15.0:  # sanity check on voltage range
                        self.voltage, self.current, self.power = voltage, current, power
                    else:
                        print("Voltage out of expected range, ignoring.")
                except ValueError:
                    print("Data conversion error, ignoring.")
            else:
                print("Incomplete data received, ignoring.")
            
            if type(self.voltage) == float:
                if self.voltage <= self.voltage_treshold:
                    print("[\033[4;31mSystem\033[0m] Calling shutdown method.")
                    self.shut_down(self.voltage, self.leak_pin.value)
            
            if self.leak_pin.value:
                print("[\033[4;31mSystem\033[0m] Calling shutdown method.")
                self.shut_down(self.voltage, self.leak_pin.value)
                
            if self.wifi_connection():
                # print("[\033[4;31mSystem\033[0m] Wifi connection reached.")
                self.blink_status_leds(leds_to_blink=[self.led_green2], times=1)
            elif not self.wifi_connection():
                self.blink_status_leds(leds_to_blink=[self.led_red1], times=1)
                
            
            #here we assume everything is okay and we blink the leds
            self.blink_status_leds(leds_to_blink=[self.led_green1], times=1)
            time.sleep(duration)
        
    def log_sensor_data(self, duration):
        """Logs sensor data every `duration` seconds until stopped."""
        while not self.stop_event.is_set():
            print("[Sensor] Logging data...")
            # get temperature data
            self.temperature = self.record_temperature()
            # current, voltage and power data is handled by error_sensors method
            # but data is logged in this method
            data_to_Write = [time.time(), self.voltage, self.current, self.power, self.temperature]  # Merge all values
            with open("/home/pi/seesaibling/data/data.txt", 'at', newline = '') as file:
                wr = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
                wr.writerow(data_to_Write)
            time.sleep(duration)
            
    def monitor_errors(self):
        """Monitors for errors and triggers an emergency stop if needed."""
        while not self.stop_event.is_set():
            error_detected = False
            # Add error detection functionality here
            
            if error_detected:
                logging.error("[Error] Emergency stop triggered!")
                print("[Error] Emergency stop triggered!")
                self.stop_event.set()
                break
            time.sleep(1)  # Check every 1 second
            
    def control_light(self, start_delay, duration):
        """Controls the LED light with a delay and duration."""
        time.sleep(start_delay)
        if self.stop_event.is_set():
            return
        
        logging.info("[Light] ON")
        print("[\033[4;33mLight\033[0m] ON")
        
        # Initialize LED
        self.led_main = pwmio.PWMOut(board.D12, frequency=self.fre, duty_cycle=0)
        
        # Convert microseconds to a duty cycle percentage
        duty_cycle_on = int((1900 / 20000) * 65535)  # LED ON
        duty_cycle_off = int((1100 / 20000) * 65535)  # LED OFF
        
        self.led_main.duty_cycle = duty_cycle_on
        
        for _ in range(duration):
            if self.stop_event.wait(timeout=1):
                logging.info("[Light] OFF (Emergency stop)")
                print("[Light] OFF (Emergency stop)")
                self.led_main.duty_cycle = duty_cycle_off
                self.led_main.deinit()
                self.led_main = None
                return
        
        self.led_main.duty_cycle = duty_cycle_off
        self.led_main.deinit()
        self.led_main = None
        
        logging.info("[Light] OFF")
        print("[\033[4;33mLight\033[0m] OFF")
        
    def record_audio(self, start_delay, duration):
        """Simulates audio recording."""
        if duration == 0:
            return
        else:
            time.sleep(start_delay) # wait to execute
            
        # check if event is already stopped
        if self.stop_event.is_set():
            return
        
        output_folder = "/home/pi/seesaibling/recordings"
        
        timestamp = time.strftime("%Y-%m-%d--%H-%M-%S", time.localtime())
        filename = f"hp_{timestamp}.wav"
        filepath = os.path.join(output_folder, filename)
        
        # Start the audio recording in a separate thread
        def start_recording():
            command = ["arecord", "-D", "hw:3,0", "-f", "S32_LE", "-r", "44100", "-c", "2", "-d", str(int(duration)), filepath]
            # Use Popen to start arecord as a subprocess
            self.process = subprocess.Popen(command)
            
        recording_thread = threading.Thread(target=start_recording)
        recording_thread.start()
        
        logging.info("[Audio] Recording started")
        print("[\033[4;35mAudio\033[0m] Recording started")
        
        # Monitor stop_event and allow interruption during recording
        for _ in range(duration):
            if self.stop_event.wait(timeout=1):
                logging.info("[Audio] Recording stopped (Emergency stop)")
                print("[\033[4;35mAudio\033[0m] Recording stopped (Emergency stop)")
                # Send a termination signal to the arecord process
                self.process.terminate()  # Sends SIGTERM to the process
                self.process.wait()  # Wait for the process to terminate cleanly
                return
        
        # After the duration ends, make sure the process is terminated if not already done
        if self.process is not None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)  # Wait for the process to terminate cleanly
            except subprocess.TimeoutExpired:
                logging.error("[Audio] Timed out waiting for process to terminate")
                print("[Audio] Timed out waiting for process to terminate")
            self.process = None  # Reset the process reference after termination
        
        logging.info("[Audio] Recording finished")
        print("[\033[4;35mAudio\033[0m] Recording finished")

    def record_video(self, start_delay, duration):
        """Records video with a delay and specified duration."""
        time.sleep(start_delay)
        filename = f"/home/pi/seesaibling/video/{time.strftime('%Y-%m-%d--%H-%M-%S')}_d{duration}.h264"

        self.picam2.start_recording(self.encoder, filename, quality=Quality.VERY_HIGH)
        logging.info("[Video] Recording started")
        print("[\033[4;32mVideo\033[0m] Recording started")
        
        for _ in range(duration):
            if self.stop_event.wait(timeout=1):
                logging.info("[Video] Recording stopped (Emergency stop)")
                print("[\033[4;32mVideo\033[0m] Recording stopped (Emergency stop)")
                self.picam2.stop_recording()
                return

        self.picam2.stop_recording()
        logging.info("[Video] Recording finished")
        print("[\033[4;32mVideo\033[0m] Recording finished.")
        
    def record_temperature(self):
        """Retrieve the temperature from the sensor."""
        try:
            temperature = self.sensor.get_temperature()
            return temperature
        except Exception as e:
            logging.error(f"[Temperature] Error reading temperature: {e}")
            print(f"[Temperature] Error reading temperature: {e}")
            return None  # Return None if there's an error
    
    def blink_status_leds(self, leds_to_blink, times, on_duration=0.2, off_duration=0.2):
        for _ in range(times):
            # Turn on the selected LEDs
            for led in leds_to_blink:
                led.value = True  # LED ON
            # Wait for the 'on' duration
            time.sleep(on_duration)
            # Turn off the selected LEDs
            for led in leds_to_blink:
                led.value = False  # LED OFF
            time.sleep(off_duration)
    
    def wifi_connection(self):
        try:
            # Run ifconfig to check for wlan0 interface
            result = subprocess.run(['ifconfig', 'wlan0'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if 'inet ' in result.stdout.decode():
                return True
            else:
                return False
        except Exception as e:
            print(f"Error checking Wi-Fi connection: {e}")
            return False
    
    def start(self):
        """Main loop for continuous monitoring and periodic recording."""
        logging.info("[System] Startup: Monitoring and recording initiated.")
        print("[\033[4;31mSystem\033[0m] System startup: Monitoring and recording initiated.")

        # Start continuous error monitoring
        monitor_thread = threading.Thread(target=self.monitor_errors)
        monitor_thread.start()

        while not self.stop_event.is_set():
            logging.info("[System] Starting new cycle")
            print("[\033[4;31mSystem\033[0m] > Starting new cycle (t=0)")

            cycle_start_time = time.time()

            # Start continuous sensor logging
            error_sensor_thread = threading.Thread(target=self.error_sensors, args=(2,))
            error_sensor_thread.start()
            sensor_thread = threading.Thread(target=self.log_sensor_data, args=(sensor_duration,))
            sensor_thread.start()

            # Overlapping tasks
            video_thread = threading.Thread(target=self.record_video, args=(video_delay, video_duration))
            audio_thread = threading.Thread(target=self.record_audio, args=(audio_delay, audio_duration))
            light_thread = threading.Thread(target=self.control_light, args=(light_delay, light_duration))

            # Start timed tasks
            video_thread.start()
            audio_thread.start()
            light_thread.start()

            # Wait for all threads to finish their tasks
            video_thread.join()
            audio_thread.join()
            light_thread.join()

            # Ensure logging thread stops if an error occurred
            if self.stop_event.is_set():
                break

            # Calculate remaining time and wait for the next cycle
            elapsed_time = time.time() - cycle_start_time
            interval_time = interval_duration
            remaining_time = interval_time - elapsed_time
            if remaining_time > 0:
                print(f"[\033[4;31mSystem\033[0m] Waiting {remaining_time:.2f} seconds for next cycle")
                time.sleep(remaining_time)

        self.stop_event.set()
        error_sensor_thread.join()
        sensor_thread.join()
        monitor_thread.join()

        logging.info("[System] Stopped due to error or shutdown request.")
        print("\n[\033[4;31mSystem\033[0m] Stopped due to error or shutdown request.")


# Run the system
if __name__ == "__main__":
    # Get user input for delays and durations
    print("--Monitoring unit--")
    operation_mode = input("Choose between predefined [p], test [t] or custom [c] operation:")
    if operation_mode == "p":
        interval_duration = 30*60
        sensor_duration = 30
        sensor_delay = 0
        video_delay = 10
        video_duration = 40
        audio_delay = 3
        audio_duration = 50
        light_delay = 15
        light_duration = 40
        print("\n[\033[4;31mSystem\033[0m] [predefined] automatically choosing delay and duration lengths")
    elif operation_mode == "t":
        interval_duration = 60
        sensor_duration = 5
        sensor_delay = 0
        video_delay = 1
        video_duration = 20
        audio_delay = 7
        audio_duration = 23
        light_delay = 10
        light_duration = 20
        print("\n[\033[4;31mSystem\033[0m] [test] automatically choosing delay and duration lengths")
    elif operation_mode == "c":
        interval_duration = int(input("[\033[4;34mInterval\033[0m] Enter total interval duration [s]: "))
        
        sensor_duration = int(input("[Sensor] Enter sensor sampling interval [s]: "))
        sensor_delay = 0

        video_delay = int(input("[\033[4;32mVideo\033[0m] > Recording delay [s]: "))
        video_duration = int(input("[\033[4;32mVideo\033[0m] > Recording duration [s]: "))

        audio_delay = int(input("[\033[4;35mAudio\033[0m] > Recording delay [s]: "))
        audio_duration = int(input("[\033[4;35mAudio\033[0m] > Recording duration [s]: "))

        light_delay = int(input("[\033[4;33mLight\033[0m] > Delay [s]: "))
        light_duration = int(input("[\033[4;33mLight\033[0m] > Duration [s]: "))
    else: 
        print("Please enter [p], [t] or [c]")

    system = CameraSystem()
    system.start()
