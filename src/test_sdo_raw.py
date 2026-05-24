import argparse
import time

import can

try:
    from config import CAN_CHANNEL, CAN_INTERFACE, NODE_IDS
except ModuleNotFoundError:
    from src.config import CAN_CHANNEL, CAN_INTERFACE, NODE_IDS


READ_OBJECTS = (
    ("Device type", 0x1000, 0x00),
    ("Error register", 0x1001, 0x00),
    ("Vendor ID", 0x1018, 0x01),
    ("Product code", 0x1018, 0x02),
    ("Revision number", 0x1018, 0x03),
    ("Serial number", 0x1018, 0x04),
)


class SdoAbortError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(f"SDO abort 0x{code:08X}")


def read_sdo_expedited(bus, node_id, index, subindex, timeout):
    request_id = 0x600 + node_id
    response_id = 0x580 + node_id
    request = [
        0x40,
        index & 0xFF,
        (index >> 8) & 0xFF,
        subindex & 0xFF,
        0x00,
        0x00,
        0x00,
        0x00,
    ]

    while bus.recv(timeout=0) is not None:
        pass

    bus.send(
        can.Message(
            arbitration_id=request_id,
            data=request,
            is_extended_id=False,
        ),
        timeout=timeout,
    )

    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"Brak odpowiedzi SDO z node {node_id}")

        message = bus.recv(timeout=remaining)
        if message is None:
            raise TimeoutError(f"Brak odpowiedzi SDO z node {node_id}")
        if message.arbitration_id != response_id:
            continue
        if len(message.data) < 8:
            continue
        if message.data[1] != request[1] or message.data[2] != request[2]:
            continue
        if message.data[3] != request[3]:
            continue

        command = message.data[0]
        if command == 0x80:
            abort_code = int.from_bytes(message.data[4:8], byteorder="little")
            raise SdoAbortError(abort_code)

        if (command & 0xE0) != 0x40:
            raise RuntimeError(f"Nieoczekiwany typ odpowiedzi SDO: 0x{command:02X}")
        if not (command & 0x02):
            raise RuntimeError("Odpowiedź SDO nie jest expedited")

        unused_bytes = (command >> 2) & 0x03 if command & 0x01 else 0
        size = 4 - unused_bytes
        payload = bytes(message.data[4 : 4 + size])
        value = int.from_bytes(payload, byteorder="little", signed=False)
        return value, payload


def format_value(value, payload):
    width = max(2, len(payload) * 2)
    return f"{value} (0x{value:0{width}X}, {len(payload)} B)"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Read basic CANopen SDO objects without using an EDS file."
    )
    parser.add_argument("--interface", default=CAN_INTERFACE)
    parser.add_argument("--channel", default=CAN_CHANNEL)
    parser.add_argument("--nodes", nargs="+", type=int, default=list(NODE_IDS))
    parser.add_argument("--timeout", type=float, default=1.0)
    return parser.parse_args()


def main():
    args = parse_args()

    print(f"CAN: interface={args.interface}, channel={args.channel}")
    print(f"Nodes: {', '.join(str(node_id) for node_id in args.nodes)}")

    with can.Bus(interface=args.interface, channel=args.channel) as bus:
        for node_id in args.nodes:
            print(f"\nNode {node_id}")
            for name, index, subindex in READ_OBJECTS:
                label = f"{name} 0x{index:04X}:{subindex:02X}"
                try:
                    value, payload = read_sdo_expedited(
                        bus, node_id, index, subindex, args.timeout
                    )
                    print(f"  OK   {label:<34} {format_value(value, payload)}")
                except Exception as exc:
                    print(f"  FAIL {label:<34} {exc}")


if __name__ == "__main__":
    main()
