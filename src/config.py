from pathlib import Path

CAN_INTERFACE = "systec"
CAN_CHANNEL = 0
CAN_BITRATE = 500000
CAN_DEVICE_NUMBER = 255

NODE_ID = 1
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EDS_FILE = str(PROJECT_ROOT / "CANOPEN-EDS-MBDV-Servo-DulAxes-V1.0.eds")
