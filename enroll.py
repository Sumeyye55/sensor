from pyfingerprint.pyfingerprint import PyFingerprint

try:
    f = PyFingerprint('/dev/serial0', 57600, 0xFFFFFFFF, 0x00000000)
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
import time
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