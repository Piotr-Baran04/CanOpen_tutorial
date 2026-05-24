import argparse
import time

import can

try:
    from config import CAN_CHANNEL, CAN_INTERFACE, NODE_IDS
except ModuleNotFoundError:
    from src.config import CAN_CHANNEL, CAN_INTERFACE, NODE_IDS


HEARTBEAT_STATES = {
    0x00: "Boot-up",
    0x04: "Stopped",
    0x05: "Operational",
    0x7F: "Pre-operational",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Listen for CANopen heartbeat frames."
    )
    parser.add_argument("--interface", default=CAN_INTERFACE)
    parser.add_argument("--channel", default=CAN_CHANNEL)
    parser.add_argument("--nodes", nargs="+", type=int, default=list(NODE_IDS))
    parser.add_argument("--duration", type=float, default=10.0)
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show heartbeat from all node IDs, not only configured nodes.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    watched_nodes = set(args.nodes)
    end_time = time.monotonic() + args.duration if args.duration > 0 else None

    print(f"CAN: interface={args.interface}, channel={args.channel}")
    if args.all:
        print("Watching heartbeat from all nodes")
    else:
        print(f"Watching heartbeat from nodes: {', '.join(map(str, args.nodes))}")
    if args.duration > 0:
        print(f"Listening for {args.duration:g} s.\n")
    else:
        print("Press Ctrl+C to stop.\n")

    with can.Bus(interface=args.interface, channel=args.channel) as bus:
        while True:
            if end_time is None:
                timeout = 1.0
            else:
                timeout = max(0.0, end_time - time.monotonic())
                if timeout == 0:
                    break

            message = bus.recv(timeout=timeout)
            if message is None:
                continue

            arbitration_id = message.arbitration_id
            if arbitration_id < 0x700 or arbitration_id > 0x77F:
                continue
            if len(message.data) < 1:
                continue

            node_id = arbitration_id - 0x700
            if not args.all and node_id not in watched_nodes:
                continue

            state = message.data[0]
            state_name = HEARTBEAT_STATES.get(state, "Unknown")
            print(f"node {node_id:3d}: heartbeat 0x{state:02X} ({state_name})")


if __name__ == "__main__":
    main()
