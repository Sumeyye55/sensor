import serial
import time

PORT = "/dev/ttyUSB0"
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=2)

def send_packet(cmd, param=0, read_len=64):
    packet = bytearray()
    packet += b'\x55\xAA'
    packet += (1).to_bytes(2, "little")          # Device ID
    packet += param.to_bytes(4, "little")
    packet += cmd.to_bytes(2, "little")
    checksum = sum(packet) & 0xFFFF
    packet += checksum.to_bytes(2, "little")

    ser.write(packet)
    time.sleep(0.3)
    resp = ser.read(read_len)
    print(f"CMD {cmd:#06x}, PARAM {param} ->", resp.hex(" "))
    return resp

def led(on=True):
    send_packet(0x0012, 1 if on else 0)

def wait_finger(pressed=True):
    while True:
        resp = send_packet(0x0026)
        if len(resp) >= 12:
            param = int.from_bytes(resp[4:8], "little")
            if pressed and param == 0:
                return
            if not pressed and param != 0:
                return
        time.sleep(0.5)

print("Sensör açılıyor...")
send_packet(0x0001)

print("LED açılıyor...")
led(True)

enroll_id = 1

print("Enroll başlatılıyor...")
send_packet(0x0022, enroll_id)

print("1. kez parmağını koy.")
wait_finger(True)
send_packet(0x0060)
send_packet(0x0023)

print("Parmağını kaldır.")
wait_finger(False)

print("2. kez parmağını koy.")
wait_finger(True)
send_packet(0x0060)
send_packet(0x0024)

print("Parmağını kaldır.")
wait_finger(False)

print("3. kez parmağını koy.")
wait_finger(True)
send_packet(0x0060)
send_packet(0x0025)

print("Kayıt tamamlanmış olmalı.")

led(False)
ser.close()