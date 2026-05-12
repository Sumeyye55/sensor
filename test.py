import serial
import time

PORT = "/dev/ttyUSB0"
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)

# GT-521F52 Open komutu
open_cmd = bytes.fromhex("55 AA 01 00 01 00 00 00 01 00 02 01")

ser.write(open_cmd)
time.sleep(0.5)

response = ser.read(64)

print("Cevap:", response.hex(" "))

ser.close()