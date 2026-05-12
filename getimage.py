import serial
import time
from PIL import Image, ImageOps

PORT = "/dev/ttyUSB1"   # sende ttyUSB1 görünüyor
BAUD = 9600

WIDTH = 258
HEIGHT = 202
IMAGE_SIZE = WIDTH * HEIGHT

CMD_OPEN = 0x0001
CMD_LED = 0x0012
CMD_IS_PRESS_FINGER = 0x0026
CMD_CAPTURE_FINGER = 0x0060
CMD_GET_IMAGE = 0x0062

ser = serial.Serial(PORT, BAUD, timeout=60)

def send_packet(cmd, param=0):
    packet = bytearray()
    packet += b"\x55\xAA"
    packet += (1).to_bytes(2, "little")
    packet += param.to_bytes(4, "little")
    packet += cmd.to_bytes(2, "little")

    checksum = sum(packet) & 0xFFFF
    packet += checksum.to_bytes(2, "little")

    ser.write(packet)
    time.sleep(0.25)

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
    return send_packet(CMD_LED, 1 if on else 0)

def finger_pressed():
    resp = send_packet(CMD_IS_PRESS_FINGER)
    param, response = parse(resp)

    # param 0 = parmak var
    # param 0x1012 = parmak yok
    return response == 0x0030 and param == 0

def wait_for_finger():
    while not finger_pressed():
        print("Parmağınızı koyun...")
        time.sleep(1)

    print("Parmak algılandı.")

def read_image_data():
    data = bytearray()

    print("Görüntü verisi okunuyor. 9600 baud olduğu için 45-60 saniye sürebilir...")

    while len(data) < IMAGE_SIZE:
        chunk = ser.read(min(4096, IMAGE_SIZE - len(data)))

        if not chunk:
            print("Veri akışı durdu.")
            break

        data.extend(chunk)
        print(f"Alınan: {len(data)}/{IMAGE_SIZE}")

    return bytes(data)

try:
    print("Sensör açılıyor...")
    resp = send_packet(CMD_OPEN)

    if not is_ack(resp):
        print("❌ Sensör açılamadı.")
        raise SystemExit

    print("LED açılıyor...")
    led(True)

    wait_for_finger()

    print("Parmak görüntüsü yakalanıyor...")
    resp = send_packet(CMD_CAPTURE_FINGER, 1)

    if not is_ack(resp):
        print("❌ CaptureFinger başarısız.")
        raise SystemExit

    print("GetImage komutu gönderiliyor...")
    resp = send_packet(CMD_GET_IMAGE)

    if not is_ack(resp):
        print("❌ GetImage başarısız.")
        raise SystemExit

    data = read_image_data()

    print("Toplam alınan byte:", len(data))

    if len(data) != IMAGE_SIZE:
        print("❌ Eksik veri geldi.")
        raise SystemExit

    img = Image.frombytes("L", (WIDTH, HEIGHT), data)

    img = img.transpose(Image.FLIP_TOP_BOTTOM)
    img = ImageOps.autocontrast(img)

    img.save("fingerprint.png")

    print("✅ Görüntü kaydedildi: fingerprint.png")

finally:
    try:
        print("LED kapatılıyor...")
        led(False)
    except:
        pass

    ser.close()