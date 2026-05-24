from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CAN_INTERFACE = "socketcan"
CAN_CHANNEL = "can0"
CAN_BITRATE = 500000

NODE_IDS = (2, 3)
NODE_ID = NODE_IDS[0]

EDS_FILE = str(PROJECT_ROOT / "eds" / "CANOPEN-EDS-MBDV-Servo-DulAxes-V1.0.eds")

# MOONS outdoor robot scaling for this test stand:
# device velocity units = output velocity [rad/s] * scale_vel_to_dev
VELOCITY_TO_DEVICE = {
    2: -47746.4829276,
    3: 47746.4829276,
}
VELOCITY_FROM_DEVICE = {
    2: -0.00002094395,
    3: 0.00002094395,
}
