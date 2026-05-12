import serial
import time
from PIL import Image, ImageOps

PORT = "/dev/ttyUSB1"
BAUD = 9600

WIDTH = 160
HEIGHT = 120
IMAGE_SIZE = WIDTH * HEIGHT

CMD_OPEN = 0x0001
CMD_LED = 0x0012
CMD_CAPTURE_FINGER = 0x0060
CMD_GET_RAW_IMAGE = 0x0063

ser = serial.Serial(PORT, BAUD, timeout=30)

def send_packet(cmd, param=0):
    packet = bytearray()
    packet += b"\x55\xAA"
    packet += (1).to_bytes(2, "little")
    packet += param.to_bytes(4, "little")
    packet += cmd.to_bytes(2, "little")
    checksum = sum(packet) & 0xFFFF
    packet += checksum.to_bytes(2, "little")

    ser.write(packet)
    time.sleep(0.3)

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

def read_exact(size):
    data = bytearray()

    while len(data) < size:
        chunk = ser.read(min(1024, size - len(data)))
        if not chunk:
            break
        data.extend(chunk)
        print(f"Alınan: {len(data)}/{size}")

    return bytes(data)

try:
    send_packet(CMD_OPEN)
    send_packet(CMD_LED, 1)

    input("Parmağını koy, sonra ENTER'a bas...")

    resp = send_packet(CMD_CAPTURE_FINGER, 1)
    if not is_ack(resp):
        print("Capture başarısız.")
        raise SystemExit

    resp = send_packet(CMD_GET_RAW_IMAGE)
    if not is_ack(resp):
        print("GetRawImage başarısız.")
        raise SystemExit

    data = read_exact(IMAGE_SIZE)

    print("Toplam byte:", len(data))

    if len(data) != IMAGE_SIZE:
        print("Eksik veri geldi.")
        raise SystemExit

    img = Image.frombytes("L", (WIDTH, HEIGHT), data)
    img = ImageOps.autocontrast(img)
    img.save("raw_fingerprint.png")

    print("✅ Kaydedildi: raw_fingerprint.png")

finally:
    try:
        send_packet(CMD_LED, 0)
    except:
        pass
    ser.close()