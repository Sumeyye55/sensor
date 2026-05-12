import serial
import time

PORT = "/dev/ttyUSB1"
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=2)

def send_packet(cmd, param=0):
    packet = bytearray()
    packet += b'\x55\xAA'
    packet += (1).to_bytes(2, "little")
    packet += param.to_bytes(4, "little")
    packet += cmd.to_bytes(2, "little")
    checksum = sum(packet) & 0xFFFF
    packet += checksum.to_bytes(2, "little")

    ser.write(packet)
    time.sleep(0.25)
    resp = ser.read(64)
    print(f"CMD {cmd:#06x}, PARAM {param} -> {resp.hex(' ')}")
    return resp

def get_param(resp):
    if len(resp) >= 12:
        return int.from_bytes(resp[4:8], "little")
    return None

def is_ack(resp):
    return len(resp) >= 10 and resp[8:10] == b'\x30\x00'

send_packet(0x0001)       # Open

resp = send_packet(0x0020) # GetEnrollCount

if is_ack(resp):
    print("Kayıtlı parmak sayısı:", get_param(resp))
else:
    print("Kayıt sayısı okunamadı.")

ser.close()