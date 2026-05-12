import serial
import time

PORT = "/dev/ttyUSB1"
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)

def send_packet(cmd, param=0):
    device_id = 1

    packet = bytearray()
    packet += b'\x55\xAA'
    packet += device_id.to_bytes(2, 'little')
    packet += param.to_bytes(4, 'little')
    packet += cmd.to_bytes(2, 'little')

    checksum = sum(packet) & 0xFFFF
    packet += checksum.to_bytes(2, 'little')

    ser.write(packet)
    time.sleep(0.2)
    resp = ser.read(64)
    print(f"CMD {cmd:#04x} cevap:", resp.hex(" "))
    return resp

# Open
send_packet(0x0001)

# CMOS LED ON
send_packet(0x0012, 1)

time.sleep(5)

# CMOS LED OFF
send_packet(0x0012, 0)

ser.close()