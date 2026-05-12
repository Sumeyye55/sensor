import serial
import time

PORT = "/dev/ttyUSB1"
BAUD = 9600

AUTHORIZED_ID = 0   # Parmağı ID 0'a kaydettiysen 0 yap. ID 1'e kaydettiysen 1 yap.

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
    time.sleep(0.3)
    resp = ser.read(64)
    print(f"CMD {cmd:#06x}, PARAM {param} -> {resp.hex(' ')}")
    return resp

def parse(resp):
    if len(resp) < 12:
        return None, None

    param = int.from_bytes(resp[4:8], "little")
    response = int.from_bytes(resp[8:10], "little")
    return param, response

def is_ack(resp):
    param, response = parse(resp)
    return response == 0x0030

def is_nack(resp):
    param, response = parse(resp)
    return response == 0x0031

def led(on):
    send_packet(0x0012, 1 if on else 0)

def finger_pressed():
    resp = send_packet(0x0026)
    param, response = parse(resp)

    # IsPressFinger:
    # param 0 = parmak var
    # param 0x1012 = parmak yok
    return response == 0x0030 and param == 0

def wait_for_finger():
    while not finger_pressed():
        print("Parmağınızı koyun...")
        time.sleep(1)
    print("Parmak algılandı.")

def wait_remove():
    while finger_pressed():
        print("Parmağınızı kaldırın...")
        time.sleep(1)

try:
    print("Sensör açılıyor...")
    send_packet(0x0001)

    led(True)

    while True:
        wait_for_finger()

        print("Parmak görüntüsü yakalanıyor...")
        capture = send_packet(0x0060, 1)

        if not is_ack(capture):
            cap_param, cap_response = parse(capture)
            print(f" Parmak okunamadı. Hata kodu: {cap_param}")
            wait_remove()
            continue

        print("Tanıma yapılıyor...")
        ident = send_packet(0x0051)
        ident_param, ident_response = parse(ident)

        if is_ack(ident) and ident_param == AUTHORIZED_ID:
            print(f" Yetkili parmak tanındı. ID: {ident_param}")
        elif is_ack(ident):
            print(f" Parmak kayıtlı ama yetkili değil. Gelen ID: {ident_param}")
        elif is_nack(ident):
            print(f" Parmak tanınmadı. Hata kodu: {ident_param}")
        else:
            print(" Bilinmeyen cevap geldi.")

        wait_remove()
        print("Yeni deneme.\n")

except KeyboardInterrupt:
    print("\nÇıkılıyor...")

finally:
    led(False)
    ser.close()