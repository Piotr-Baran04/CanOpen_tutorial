import argparse
import os
import select
import sys
import termios
import time
import tty
from contextlib import contextmanager
from pathlib import Path

import canopen

try:
    from cia402 import format_statusword, statusword_state
    from config import (
        CAN_CHANNEL,
        CAN_INTERFACE,
        EDS_FILE,
        NODE_IDS,
        VELOCITY_FROM_DEVICE,
        VELOCITY_TO_DEVICE,
    )
except ModuleNotFoundError:
    from src.cia402 import format_statusword, statusword_state
    from src.config import (
        CAN_CHANNEL,
        CAN_INTERFACE,
        EDS_FILE,
        NODE_IDS,
        VELOCITY_FROM_DEVICE,
        VELOCITY_TO_DEVICE,
    )


PROFILE_VELOCITY_MODE = 3

CONTROLWORD_SHUTDOWN = 0x0006
CONTROLWORD_SWITCH_ON = 0x0007
CONTROLWORD_ENABLE_OPERATION = 0x000F
CONTROLWORD_DISABLE_VOLTAGE = 0x0000
CONTROLWORD_FAULT_RESET = 0x0080

DEFAULT_SPEED_RAD_S = 0.5
ACCELERATION = 100000
DECELERATION = 100000
STATE_TIMEOUT = 3.0
DEADMAN_TIMEOUT = 0.8
PDO_PERIOD = 0.05
TELEMETRY_PERIOD = 0.5

KEY_TO_COMMAND = {
    "UP": "forward",
    "DOWN": "backward",
    "LEFT": "left",
    "RIGHT": "right",
    "SPACE": "stop",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Keyboard jog for two CANopen CiA 402 axes."
    )
    parser.add_argument("--enable", action="store_true", help="pozwala uruchomić napęd")
    parser.add_argument("--key-debug", action="store_true", help="sprawdza klawisze bez CAN")
    parser.add_argument(
        "--nodes",
        nargs=2,
        type=int,
        default=list(NODE_IDS),
        metavar=("LEFT", "RIGHT"),
        help="node lewej i prawej osi",
    )
    parser.add_argument(
        "--speed-rad-s",
        type=float,
        default=DEFAULT_SPEED_RAD_S,
        help="prędkość wyjścia przekładni w rad/s",
    )
    parser.add_argument("--telemetry", action="store_true", help="pokazuje odczyty z napędu")
    parser.add_argument(
        "--invert-node",
        nargs="*",
        type=int,
        default=[],
        help="odwraca znak prędkości dla podanych node'ów",
    )
    return parser.parse_args()


@contextmanager
def raw_terminal():
    if not sys.stdin.isatty():
        raise RuntimeError("Ten skrypt wymaga interaktywnego terminala")

    old_settings = termios.tcgetattr(sys.stdin)
    try:
        tty.setcbreak(sys.stdin.fileno())
        yield
    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


def read_key(timeout):
    ready, _, _ = select.select([sys.stdin], [], [], timeout)
    if not ready:
        return None

    sequence = os.read(sys.stdin.fileno(), 32).decode(errors="replace")
    deadline = time.monotonic() + 0.08
    while time.monotonic() < deadline:
        ready, _, _ = select.select([sys.stdin], [], [], 0.01)
        if ready:
            sequence += os.read(sys.stdin.fileno(), 32).decode(errors="replace")

    return decode_key(sequence) or sequence


def decode_key(sequence):
    if any(sequence.startswith(pattern) for pattern in ("\x1b[A", "\x1bOA", "[A", "OA")):
        return "UP"
    if any(sequence.startswith(pattern) for pattern in ("\x1b[B", "\x1bOB", "[B", "OB")):
        return "DOWN"
    if any(sequence.startswith(pattern) for pattern in ("\x1b[C", "\x1bOC", "[C", "OC")):
        return "RIGHT"
    if any(sequence.startswith(pattern) for pattern in ("\x1b[D", "\x1bOD", "[D", "OD")):
        return "LEFT"

    first_char = sequence[:1].lower()
    return {
        "w": "UP",
        "s": "DOWN",
        "a": "LEFT",
        "d": "RIGHT",
        " ": "SPACE",
        "q": "QUIT",
    }.get(first_char)


def run_key_debug():
    print("Key debug. Press arrows, WASD, space, q.")
    print("This mode does not connect to CAN and does not enable the drive.")
    with raw_terminal():
        while True:
            key = read_key(1.0)
            if key is None:
                continue
            print(f"key: {key!r}")
            if key == "QUIT":
                break


def sdo_read(node, index, subindex=0):
    entry = node.sdo[index]
    return entry.raw if subindex == 0 else entry[subindex].raw


def sdo_write(node, index, value, subindex=0):
    entry = node.sdo[index]
    if subindex == 0:
        entry.raw = value
    else:
        entry[subindex].raw = value


def wait_for_state(node, expected_state, timeout):
    deadline = time.monotonic() + timeout
    last_statusword = None

    while time.monotonic() < deadline:
        last_statusword = sdo_read(node, 0x6041)
        if statusword_state(last_statusword) == expected_state:
            return
        time.sleep(0.05)

    status = format_statusword(last_statusword) if last_statusword is not None else "?"
    raise TimeoutError(f"Node {node.id}: expected {expected_state}, got {status}")


def wait_for_mode(node, mode, timeout):
    deadline = time.monotonic() + timeout
    last_mode = None

    while time.monotonic() < deadline:
        last_mode = sdo_read(node, 0x6061)
        if last_mode == mode:
            return
        time.sleep(0.05)

    raise TimeoutError(f"Node {node.id}: mode display is {last_mode}, expected {mode}")


def enable_profile_velocity(node, accel, decel, timeout):
    node.nmt.send_command(0x01)
    time.sleep(0.1)

    if sdo_read(node, 0x6041) & 0x0008:
        sdo_write(node, 0x6040, CONTROLWORD_FAULT_RESET)
        time.sleep(0.2)

    sdo_write(node, 0x60FF, 0)
    sdo_write(node, 0x6060, PROFILE_VELOCITY_MODE)
    wait_for_mode(node, PROFILE_VELOCITY_MODE, timeout)

    sdo_write(node, 0x6083, accel)
    sdo_write(node, 0x6084, decel)

    sdo_write(node, 0x6040, CONTROLWORD_SHUTDOWN)
    wait_for_state(node, "Ready to switch on", timeout)

    sdo_write(node, 0x6040, CONTROLWORD_SWITCH_ON)
    wait_for_state(node, "Switched on", timeout)

    sdo_write(node, 0x6040, CONTROLWORD_ENABLE_OPERATION)
    wait_for_state(node, "Operation enabled", timeout)


def velocity_to_device(node_id, velocity_rad_s, inverted_nodes):
    if node_id not in VELOCITY_TO_DEVICE:
        raise KeyError(f"Brak skali VELOCITY_TO_DEVICE dla node {node_id}")

    value = int(round(velocity_rad_s * VELOCITY_TO_DEVICE[node_id]))
    return -value if node_id in inverted_nodes else value


def velocity_from_device(node_id, device_velocity):
    if device_velocity is None:
        return None

    scale = VELOCITY_FROM_DEVICE.get(node_id)
    return None if scale is None else device_velocity * scale


def command_to_output_velocities(command, speed_rad_s):
    if command == "forward":
        return speed_rad_s, speed_rad_s
    if command == "backward":
        return -speed_rad_s, -speed_rad_s
    if command == "left":
        return -speed_rad_s, speed_rad_s
    if command == "right":
        return speed_rad_s, -speed_rad_s
    return 0.0, 0.0


def send_target_velocity(network, node_id, target_velocity):
    data = bytearray()
    data.extend(CONTROLWORD_ENABLE_OPERATION.to_bytes(2, "little"))
    data.extend(int(target_velocity).to_bytes(4, "little", signed=True))
    network.send_message(0x400 + node_id, data)


def send_targets(network, targets):
    for node_id, target_velocity in targets.items():
        send_target_velocity(network, node_id, target_velocity)


def zero_targets(node_ids):
    return {node_id: 0 for node_id in node_ids}


def make_targets(node_ids, command, speed_rad_s, inverted_nodes):
    left_rad_s, right_rad_s = command_to_output_velocities(command, speed_rad_s)
    return {
        node_ids[0]: velocity_to_device(node_ids[0], left_rad_s, inverted_nodes),
        node_ids[1]: velocity_to_device(node_ids[1], right_rad_s, inverted_nodes),
    }


def safe_sdo_read(node, index):
    try:
        return sdo_read(node, index)
    except Exception:
        return None


def format_value(value, formatter=str):
    return "?" if value is None else formatter(value)


def print_telemetry(nodes):
    lines = []
    for node in nodes:
        target = safe_sdo_read(node, 0x60FF)
        actual = safe_sdo_read(node, 0x606C)
        statusword = safe_sdo_read(node, 0x6041)
        mode = safe_sdo_read(node, 0x6061)
        error_register = safe_sdo_read(node, 0x1001)
        error_code = safe_sdo_read(node, 0x603F)

        lines.append(
            " ".join(
                (
                    f"n{node.id}:",
                    f"tv={format_value(target, lambda value: f'{value:+d}')}",
                    f"tv_rad={format_value(velocity_from_device(node.id, target), lambda value: f'{value:+.3f}')}",
                    f"av={format_value(actual, lambda value: f'{value:+d}')}",
                    f"av_rad={format_value(velocity_from_device(node.id, actual), lambda value: f'{value:+.3f}')}",
                    f"mode={format_value(mode)}",
                    f"err={format_value(error_register)}/{format_value(error_code)}",
                    f"sw={format_value(statusword, lambda value: f'0x{value:04X}')}",
                )
            )
        )
    print("\n" + " | ".join(lines), flush=True)


def stop_axes(network, node_ids, nodes):
    print("\nZatrzymuję osie...")
    try:
        send_targets(network, zero_targets(node_ids))
    except Exception as exc:
        print(f"PDO stop failed: {exc}")

    for node in nodes:
        try:
            sdo_write(node, 0x60FF, 0)
            sdo_write(node, 0x6040, CONTROLWORD_DISABLE_VOLTAGE)
        except Exception as exc:
            print(f"Node {node.id}: stop/disable failed: {exc}")


def connect_nodes(network, node_ids, eds_path):
    nodes = []
    for node_id in node_ids:
        node = canopen.RemoteNode(node_id, str(eds_path))
        network.add_node(node)
        nodes.append(node)
    return nodes


def main():
    args = parse_args()

    if args.key_debug:
        run_key_debug()
        return

    if not args.enable:
        raise SystemExit("Ten skrypt może poruszyć napędem. Dodaj parametr --enable.")

    node_ids = tuple(args.nodes)
    inverted_nodes = set(args.invert_node)
    eds_path = Path(EDS_FILE)
    if not eds_path.exists():
        raise FileNotFoundError(f"Brak pliku EDS: {eds_path}")

    print(f"CAN: interface={CAN_INTERFACE}, channel={CAN_CHANNEL}")
    print(f"EDS: {eds_path}")
    print(f"Nodes: left={node_ids[0]}, right={node_ids[1]}")
    print(f"Speed: {args.speed_rad_s} rad/s")
    print(f"Accel/decel device units: {ACCELERATION}/{DECELERATION}")
    print("Sterowanie: strzałki albo WASD, spacja=stop, q=wyjście")

    network = canopen.Network()
    network.connect(interface=CAN_INTERFACE, channel=CAN_CHANNEL)
    nodes = []

    try:
        nodes = connect_nodes(network, node_ids, eds_path)

        for node in nodes:
            print(f"Konfiguruję node {node.id}...")
            enable_profile_velocity(node, ACCELERATION, DECELERATION, STATE_TIMEOUT)
            print(f"  {format_statusword(sdo_read(node, 0x6041))}")

        command = "stop"
        targets = zero_targets(node_ids)
        last_key_time = time.monotonic()
        last_pdo_time = 0.0
        last_telemetry_time = 0.0
        send_targets(network, targets)

        with raw_terminal():
            while True:
                key = read_key(0.05)
                if key == "QUIT":
                    break

                if key in KEY_TO_COMMAND:
                    command = KEY_TO_COMMAND[key]
                    last_key_time = time.monotonic()
                    targets = make_targets(
                        node_ids, command, args.speed_rad_s, inverted_nodes
                    )
                    send_targets(network, targets)
                    print(f"\r{command:<8} {targets}   ", end="", flush=True)

                if command != "stop" and time.monotonic() - last_key_time > DEADMAN_TIMEOUT:
                    command = "stop"
                    targets = zero_targets(node_ids)
                    send_targets(network, targets)
                    print("\rstop     target velocities = 0   ", end="", flush=True)

                if time.monotonic() - last_pdo_time >= PDO_PERIOD:
                    send_targets(network, targets)
                    last_pdo_time = time.monotonic()

                if args.telemetry and time.monotonic() - last_telemetry_time >= TELEMETRY_PERIOD:
                    print_telemetry(nodes)
                    last_telemetry_time = time.monotonic()
    except KeyboardInterrupt:
        print("\nPrzerwano Ctrl+C.")
    finally:
        stop_axes(network, node_ids, nodes)
        network.disconnect()


if __name__ == "__main__":
    main()
