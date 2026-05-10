import atexit
import sys
import time

from pyfingerprint.pyfingerprint import PyFingerprint

# --- Güç anahtarı (MOSFET / röle Sürücü) — kabloya göre ayarlayın ---
# Vin sensöre harici veya GPIO ile kontrol edilen bir hat üzerinden gidiyorsa,
# sensör açılmadan LED yanmaz ve serial init de başarısız olur.
USE_GPIO_POWER = True   # Set True when sensor VCC is controlled via a GPIO pin/transistor
SENSOR_POWER_BCM = 18  # BCM pin number driving the transistor/MOSFET gate (physical pin 12)
# N-channel MOSFET / NPN transistor (high = sensor ON):  True
# P-channel MOSFET / relay active-low (low = sensor ON): False
POWER_ACTIVE_HIGH = True
# Time (seconds) to wait after power-on for sensor LED and UART to stabilise
POWER_STABILIZE_SEC = 2.0

# GT-521F52 fabrika varsayılanı 9600 baud
SERIAL_PORT = "/dev/serial0"
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
