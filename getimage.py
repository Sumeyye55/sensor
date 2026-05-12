import serial
import time
from PIL import Image, ImageOps

PORT = "/dev/ttyUSB0"

BAUD_START = 9600
BAUD_FAST = 115200

WIDTH = 258
HEIGHT = 202
IMAGE_SIZE = WIDTH * HEIGHT

CMD_OPEN = 0x0001
CMD_CHANGE_BAUD = 0x0004
CMD_LED = 0x0012
CMD_IS_PRESS_FINGER = 0x0026
CMD_CAPTURE_FINGER = 0x0060
CMD_GET_IMAGE = 0x0062

ser = None

def open_serial(baud, timeout=3):
    return serial.Serial(PORT, baud, timeout=timeout)

def send_packet(cmd, param=0, read_response=True):
    global ser

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
    return send_packet(CMD_LED, 1 if on else 0)

def finger_pressed():
    resp = send_packet(CMD_IS_PRESS_FINGER)
    param, response = parse(resp)

    # param 0 = parmak var
    return response == 0x0030 and param == 0

def wait_for_finger():
    while not finger_pressed():
        print("Parmağınızı koyun...")
        time.sleep(1)

    print("Parmak algılandı.")

def read_exact(size):
    data = bytearray()

    while len(data) < size:
        chunk = ser.read(min(4096, size - len(data)))

        if not chunk:
            print("Veri akışı durdu.")
            break

        data.extend(chunk)
        print(f"Alınan: {len(data)}/{size}")

    return bytes(data)

try:
    print("9600 baud ile sensöre bağlanılıyor...")
    ser = open_serial(BAUD_START, timeout=3)

    print("Sensör açılıyor...")
    resp = send_packet(CMD_OPEN)

    if not is_ack(resp):
        print("❌ Sensör açılamadı.")
        raise SystemExit

    led(True)

    wait_for_finger()

    print("Parmak görüntüsü yakalanıyor...")
    resp = send_packet(CMD_CAPTURE_FINGER, 1)

    if not is_ack(resp):
        print("❌ CaptureFinger başarısız.")
        raise SystemExit

    print("Baud rate 115200'e yükseltiliyor...")
    resp = send_packet(CMD_CHANGE_BAUD, 5)

    if not is_ack(resp):
        print("❌ Baud değiştirme başarısız.")
        raise SystemExit

    ser.close()
    time.sleep(0.5)

    print("115200 baud ile yeniden bağlanılıyor...")
    ser = open_serial(BAUD_FAST, timeout=10)

    print("GetImage komutu gönderiliyor...")
    resp = send_packet(CMD_GET_IMAGE)

    if not is_ack(resp):
        print("❌ GetImage başarısız.")
        raise SystemExit

    print("Görüntü verisi okunuyor...")
    data = read_exact(IMAGE_SIZE)

    print("Toplam alınan byte:", len(data))

    if len(data) != IMAGE_SIZE:
        print("❌ Eksik veri geldi.")
        raise SystemExit

    img = Image.frombytes("L", (WIDTH, HEIGHT), data)

    # Görüntü ters gelirse düzeltir
    img = img.transpose(Image.FLIP_TOP_BOTTOM)

    # Kontrastı biraz iyileştirir
    img = ImageOps.autocontrast(img)

    img.save("fingerprint.png")

    print("✅ Görüntü kaydedildi: fingerprint.png")

finally:
    try:
        if ser and ser.is_open:
            print("LED kapatılıyor...")
            led(False)
            ser.close()
    except:
        pass