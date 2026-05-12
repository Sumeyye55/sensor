import serial
import time

PORT = "/dev/ttyUSB0"
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=2)

def send_packet(cmd, param=0, read_len=64):
    packet = bytearray()
    packet += b'\x55\xAA'
    packet += (1).to_bytes(2, "little")
    packet += param.to_bytes(4, "little")
    packet += cmd.to_bytes(2, "little")
    checksum = sum(packet) & 0xFFFF
    packet += checksum.to_bytes(2, "little")

    ser.write(packet)
    time.sleep(0.25)
    resp = ser.read(read_len)
    print(f"CMD {cmd:#06x}, PARAM {param} -> {resp.hex(' ')}")
    return resp

def get_param(resp):
    if len(resp) >= 12:
        return int.from_bytes(resp[4:8], "little")
    return None

def is_ack(resp):
    return len(resp) >= 10 and resp[8:10] == b'\x30\x00'

def led(on=True):
    send_packet(0x0012, 1 if on else 0)

def wait_for_finger():
    print("Parmağını sensöre koy...")
    while True:
        resp = send_packet(0x0026)  # IsPressFinger
        param = get_param(resp)

        # GT-521: param 0 = parmak var, 1 = parmak yok
        if param == 0:
            print("Parmak algılandı.")
            return

        time.sleep(0.3)

print("Sensör açılıyor...")
send_packet(0x0001)

led(True)

wait_for_finger()

print("Parmak görüntüsü yakalanıyor...")
capture = send_packet(0x0060)  # CaptureFinger

if not is_ack(capture):
    print("Parmak görüntüsü alınamadı.")
    led(False)
    ser.close()
    exit()

print("Tanıma yapılıyor...")
identify = send_packet(0x0060, 1)  # Identify

if is_ack(identify):
    finger_id = get_param(identify)
    print(f" Parmak tanındı. ID: {finger_id}")
else:
    print(" Parmak tanınmadı.")

led(False)
ser.close()