import argparse
import time

import can

try:
    from config import CAN_CHANNEL, CAN_INTERFACE
except ModuleNotFoundError:
    from src.config import CAN_CHANNEL, CAN_INTERFACE


NMT_COMMANDS = {
    "start": 0x01,
    "stop": 0x02,
    "preop": 0x80,
}

HEARTBEAT_STATES = {
    0x00: "Boot-up",
    0x04: "Stopped",
    0x05: "Operational",
    0x7F: "Pre-operational",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Send a simple CANopen NMT command."
    )
    parser.add_argument("command", choices=sorted(NMT_COMMANDS))
    parser.add_argument("node_id", type=int, help="Node ID, or 0 for broadcast")
    parser.add_argument("--interface", default=CAN_INTERFACE)
    parser.add_argument("--channel", default=CAN_CHANNEL)
    parser.add_argument("--timeout", type=float, default=2.0)
    return parser.parse_args()


def wait_for_heartbeat(bus, node_id, timeout):
    response_id = 0x700 + node_id
    deadline = time.monotonic() + timeout

    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None

        message = bus.recv(timeout=remaining)
        if message is None:
            return None
        if message.arbitration_id != response_id:
            continue
        if len(message.data) < 1:
            continue

        return message.data[0]


def main():
    args = parse_args()
    command = NMT_COMMANDS[args.command]

    if not 0 <= args.node_id <= 127:
        raise ValueError("node_id musi być w zakresie 0..127")

    print(f"CAN: interface={args.interface}, channel={args.channel}")
    print(f"NMT: {args.command} node {args.node_id}")

    with can.Bus(interface=args.interface, channel=args.channel) as bus:
        while bus.recv(timeout=0) is not None:
            pass

        message = can.Message(
            arbitration_id=0x000,
            data=[command, args.node_id],
            is_extended_id=False,
        )
        bus.send(message, timeout=args.timeout)

        if args.node_id == 0:
            print("Wysłano broadcast. Obserwuj heartbeat przez candump albo monitor.")
            return

        state = wait_for_heartbeat(bus, args.node_id, args.timeout)
        if state is None:
            print("Nie odebrano heartbeat po komendzie NMT.")
            return

        state_name = HEARTBEAT_STATES.get(state, "Unknown")
        print(f"Heartbeat node {args.node_id}: 0x{state:02X} ({state_name})")


if __name__ == "__main__":
    main()
