import atexit
import sys
import time

from pyfingerprint.pyfingerprint import PyFingerprint

# --- Güç anahtarı (MOSFET / röle Sürücü) — kabloya göre ayarlayın ---
# Vin sensöre harici veya GPIO ile kontrol edilen bir hat üzerinden gidiyorsa,
# sensör açılmadan LED yanmaz ve serial init de başarısız olur.
# GT-521F52: power VCC directly from Pi 3.3V pin (pin 1 or 17) — no GPIO switching needed.
# The sensor LED only lights during an active scan, not just from being powered — this is normal.
USE_GPIO_POWER = True
SENSOR_POWER_BCM = 18
POWER_ACTIVE_HIGH = True
POWER_STABILIZE_SEC = 0.5

# RPi 3B+: Bluetooth occupies /dev/ttyAMA0 (hardware UART).
# To use the reliable UART, disable BT: add "dtoverlay=disable-bt" to /boot/firmware/config.txt
# then reboot — after that /dev/serial0 -> /dev/ttyAMA0 and this will work reliably.
# If you haven't done that yet, try /dev/ttyS0 (mini-UART, less reliable but may work).
SERIAL_PORT = "/dev/ttyS0"
BAUD = 9600

_power_ctl = None


def _gpio_power_on():
    global _power_ctl
    try:
        from gpiozero import DigitalOutputDevice
    except ImportError:
        print(
            "gpiozero yok: sudo apt install python3-gpiozero",
            file=sys.stderr,
        )
        sys.exit(1)

    _power_ctl = DigitalOutputDevice(
        SENSOR_POWER_BCM,
        active_high=POWER_ACTIVE_HIGH,
        initial_value=False,
    )
    _power_ctl.on()

    def _cleanup():
        if _power_ctl is not None:
            try:
                _power_ctl.off()
                _power_ctl.close()
            except Exception:
                pass

    atexit.register(_cleanup)


if USE_GPIO_POWER:
    _gpio_power_on()
time.sleep(POWER_STABILIZE_SEC)

try:
    f = PyFingerprint(SERIAL_PORT, BAUD, 0xFFFFFFFF, 0x00000000)
    if not f.verifyPassword():
        raise ValueError("Sensor password is wrong!")
except Exception as e:
    print("Sensor init failed:", str(e), file=sys.stderr)
    print("  → Check: serial enabled? correct port/baud? sensor powered?", file=sys.stderr)
    if USE_GPIO_POWER:
        print(f"  → GPIO power was used (BCM {SENSOR_POWER_BCM}, active_high={POWER_ACTIVE_HIGH})", file=sys.stderr)
    sys.exit(1)

print("Waiting for finger...")
while not f.readImage():
    pass

f.convertImage(0x01)  # Store in buffer 1

print("Remove finger")
time.sleep(2)

print("Place same finger again...")
while not f.readImage():
    pass

f.convertImage(0x02)  # Store in buffer 2

if f.compareCharacteristics() == 0:
    raise Exception("Fingers do not match!")

f.createTemplate()
position = f.storeTemplate()
print(f"Finger enrolled at position #{position}")
