import serial
import time
from PIL import Image

PORT = "/dev/ttyUSB0"
BAUD = 9600

WIDTH = 258
HEIGHT = 202
IMAGE_SIZE = WIDTH * HEIGHT

CMD_OPEN = 0x0001
CMD_LED = 0x0012
CMD_IS_PRESS_FINGER = 0x0026
CMD_CAPTURE_FINGER = 0x0060
CMD_GET_IMAGE = 0x0062

ser = serial.Serial(PORT, BAUD, timeout=3)

def send_packet(cmd, param=0, read_response=True):
    packet = bytearray()
    packet += b"\x55\xAA"
    packet += (1).to_bytes(2, "little")
    packet += param.to_bytes(4, "little")
    packet += cmd.to_bytes(2, "little")
    checksum = sum(packet) & 0xFFFF
    packet += checksum.to_bytes(2, "little")

    ser.write(packet)
    time.sleep(0.25)

    if read_response:
        resp = ser.read(12)
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

def led(on):
    send_packet(CMD_LED, 1 if on else 0)

def finger_pressed():
    resp = send_packet(CMD_IS_PRESS_FINGER)
    param, response = parse(resp)
    return response == 0x0030 and param == 0

def wait_for_finger():
    while not finger_pressed():
        print("Parmağınızı koyun...")
        time.sleep(1)
    print("Parmak algılandı.")

try:
    print("Sensör açılıyor...")
    send_packet(CMD_OPEN)
    led(True)

    wait_for_finger()

    print("Parmak görüntüsü yakalanıyor...")
    resp = send_packet(CMD_CAPTURE_FINGER, 1)

    if not is_ack(resp):
        print("Capture başarısız.")
        raise SystemExit

    print("Görüntü sensörden indiriliyor...")
    resp = send_packet(CMD_GET_IMAGE)

    if not is_ack(resp):
        print("GetImage başarısız.")
        raise SystemExit

    data = ser.read(IMAGE_SIZE)
    print("Alınan byte:", len(data))

    if len(data) != IMAGE_SIZE:
        print("Eksik veri geldi.")
        raise SystemExit

    img = Image.frombytes("L", (WIDTH, HEIGHT), data)
    img = img.transpose(Image.FLIP_TOP_BOTTOM)

    img.save("fingerprint.png")
    print(" Görüntü kaydedildi: fingerprint.png")

finally:
    led(False)
    ser.close()