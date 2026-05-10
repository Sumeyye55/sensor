import time

from pyfingerprint.pyfingerprint import PyFingerprint

# GT-521F52 UART defaults to 9600 baud at power-on (not 57600).
# Allow the module to finish boot after Vin is applied.
time.sleep(0.5)

try:
    f = PyFingerprint('/dev/serial0', 9600, 0xFFFFFFFF, 0x00000000)
    if not f.verifyPassword():
        raise ValueError('Sensor password is wrong!')
except Exception as e:
    print('Sensor init failed:', str(e))
    exit(1)

print('Waiting for finger...')
while not f.readImage():
    pass

f.convertImage(0x01)  # Store in buffer 1

print('Remove finger')
time.sleep(2)

print('Place same finger again...')
while not f.readImage():
    pass

f.convertImage(0x02)  # Store in buffer 2

if f.compareCharacteristics() == 0:
    raise Exception('Fingers do not match!')

f.createTemplate()
position = f.storeTemplate()
print(f'Finger enrolled at position #{position}')