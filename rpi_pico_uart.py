from machine import Pin, I2C, UART
import time

# Define I2C bus (I2C1 on GP4 and GP5)
i2c = I2C(0, scl=Pin(5), sda=Pin(4), freq=400000)

# Define UART setup
uart = UART(0, baudrate=115200, tx=Pin(0), rx=Pin(1))

# Initialize onboard LED
led = Pin("LED", Pin.OUT)

# INA260 I2C address (default 0x40)
INA260_ADDR = 0x44 # I've bridged the corresponding address on the INA260 to change the address!
# Since there were problems with access, with another I2C device

# Register Addresses
REG_VOLTAGE = 0x02
REG_CURRENT = 0x01
REG_POWER = 0x03

# blink onboard led in different patterns
def blink_led(times, delay=0.25):
    """Blink the onboard LED a specified number of times."""
    for _ in range(times):
        led.on()
        time.sleep(delay)
        led.off()

# Read 16-bit data from a register
def read_register(register):
    data = i2c.readfrom_mem(INA260_ADDR, register, 2)
    return int.from_bytes(data, 'big')

while True:
    try: 
        voltage = read_register(REG_VOLTAGE) * 1.25 / 1000  # Convert to volts
        current = read_register(REG_CURRENT) * 1.25 / 1000  # Convert to Amps
        power = read_register(REG_POWER) * 10 / 1000  # Convert to Watts
        print(f"Voltage: {voltage:.2f} V, Current: {current:.2f} A, Power: {power:.2f} W")
        uart.write(f"{voltage:.2f}, {current:.2f}, {power:.2f}\n")
        blink_led(1, 0.25) #one blink if successfull
        time.sleep(0.75)
        uart.flush()
    except Exception as e:
        print(f"Error occured: {e}")
        blink_led(3, 0.25) # triple blink for error
        time.sleep(1) # retry so that led blinks continuously
