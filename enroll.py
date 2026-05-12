import serial
import time

PORT = "/dev/ttyUSB0"
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
    time.sleep(0.2)
    return ser.read(64)

def get_param(resp):
    if len(resp) >= 12:
        return int.from_bytes(resp[4:8], "little")
    return None

def is_ack(resp):
    return len(resp) >= 10 and resp[8:10] == b'\x30\x00'

def led(on):
    send_packet(0x0012, 1 if on else 0)

def is_finger_pressed():
    resp = send_packet(0x0026)  # IsPressFinger
    param = get_param(resp)

    # GT-521: 0 = parmak var, 1 = parmak yok
    return param == 0

try:
    print("Sensör başlatılıyor...")
    send_packet(0x0001)
    led(True)

    while True:
        while not is_finger_pressed():
            print("Parmağınızı koyun...")
            time.sleep(1)

        print("Parmak algılandı, okunuyor...")

        resp = send_packet(0x0060)  # CaptureFinger

        if is_ack(resp):
            print("Parmak okundu.")
        else:
            print("Parmak okunamadı.")

        print("Parmağınızı kaldırın...")

        while is_finger_pressed():
            time.sleep(0.5)

        print("Yeni denemeye geçiliyor.\n")
        time.sleep(1)

except KeyboardInterrupt:
    print("\nÇıkılıyor...")

finally:
    led(False)
    ser.close()