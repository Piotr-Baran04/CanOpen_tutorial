import argparse
from pathlib import Path

import canopen

try:
    from cia402 import format_statusword
    from config import CAN_CHANNEL, CAN_INTERFACE, EDS_FILE, NODE_IDS
except ModuleNotFoundError:
    from src.cia402 import format_statusword
    from src.config import CAN_CHANNEL, CAN_INTERFACE, EDS_FILE, NODE_IDS


READ_OBJECTS = (
    ("Device type", 0x1000, 0x00),
    ("Error register", 0x1001, 0x00),
    ("Vendor ID", 0x1018, 0x01),
    ("Product code", 0x1018, 0x02),
    ("Revision number", 0x1018, 0x03),
    ("Serial number", 0x1018, 0x04),
    ("Error code", 0x603F, 0x00),
    ("Statusword", 0x6041, 0x00),
    ("Mode display", 0x6061, 0x00),
    ("Actual position", 0x6064, 0x00),
    ("Actual velocity", 0x606C, 0x00),
    ("Supported modes", 0x6502, 0x00),
)


def read_object(node, index, subindex):
    entry = node.sdo[index]
    if subindex == 0:
        return entry.raw
    return entry[subindex].raw


def format_object_value(index, value):
    if index == 0x6041 and isinstance(value, int):
        return format_statusword(value)
    if isinstance(value, int):
        return f"{value} (0x{value:X})"
    return repr(value)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Read basic CANopen objects through the EDS object dictionary."
    )
    parser.add_argument("--interface", default=CAN_INTERFACE)
    parser.add_argument("--channel", default=CAN_CHANNEL)
    parser.add_argument("--nodes", nargs="+", type=int, default=list(NODE_IDS))
    parser.add_argument("--eds", default=EDS_FILE)
    return parser.parse_args()


def main():
    args = parse_args()
    eds_path = Path(args.eds)
    if not eds_path.exists():
        raise FileNotFoundError(f"Brak pliku EDS: {eds_path}")

    print(f"CAN: interface={args.interface}, channel={args.channel}")
    print(f"EDS: {eds_path}")
    print(f"Nodes: {', '.join(str(node_id) for node_id in args.nodes)}")

    network = canopen.Network()
    network.connect(interface=args.interface, channel=args.channel)

    try:
        for node_id in args.nodes:
            node = canopen.RemoteNode(node_id, str(eds_path))
            network.add_node(node)

            print(f"\nNode {node_id}")
            for name, index, subindex in READ_OBJECTS:
                label = f"{name} 0x{index:04X}:{subindex:02X}"
                try:
                    value = read_object(node, index, subindex)
                    print(f"  OK   {label:<34} {format_object_value(index, value)}")
                except Exception as exc:
                    print(f"  FAIL {label:<34} {exc}")
    finally:
        network.disconnect()


if __name__ == "__main__":
    main()
