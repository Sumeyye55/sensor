python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

ls /dev/ttyUSB*

//PORT = "/dev/ttyUSB*" --> change if different

python enroll.py
python check.py
python identify.py
python getimage.py --> raw_fingerprint.png

