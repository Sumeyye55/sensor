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
    time.sleep(0.35)
    resp = ser.read(64)
    print(f"CMD {cmd:#06x}, PARAM {param} -> {resp.hex(' ')}")
    return resp

def get_param(resp):
    if len(resp) >= 12:
        return int.from_bytes(resp[4:8], "little")
    return None

def is_ack(resp):
    return len(resp) >= 10 and resp[8:10] == b'\x30\x00'

def led(on):
    send_packet(0x0012, 1 if on else 0)

def finger_pressed():
    resp = send_packet(0x0026)
    return get_param(resp) == 0

def wait_put():
    while not finger_pressed():
        print("Parmağınızı koyun...")
        time.sleep(1)

def wait_remove():
    while finger_pressed():
        print("Parmağınızı kaldırın...")
        time.sleep(1)

def capture():
    resp = send_packet(0x0060, 1)  # kaliteli capture
    return is_ack(resp)

def enroll_step(step_cmd, text):
    print(text)
    wait_put()

    if not capture():
        print("❌ Capture başarısız.")
        return False

    resp = send_packet(step_cmd)

    if not is_ack(resp):
        print("❌ Enroll adımı başarısız.")
        return False

    print("✅ Bu okuma başarılı.")
    wait_remove()
    return True

try:
    enroll_id = 1

    send_packet(0x0001)
    led(True)

    print("ID 1 için kayıt başlıyor...")

    resp = send_packet(0x0022, enroll_id)  # EnrollStart
    if not is_ack(resp):
        print(" EnrollStart başarısız. ID dolu olabilir.")
        raise SystemExit

    if not enroll_step(0x0023, "1. kez aynı parmağı koy."):
        raise SystemExit

    if not enroll_step(0x0024, "2. kez aynı parmağı koy."):
        raise SystemExit

    if not enroll_step(0x0025, "3. kez aynı parmağı koy."):
        raise SystemExit

    print(" Parmak başarıyla ID 1 olarak kaydedildi.")

finally:
    led(False)
    ser.close()