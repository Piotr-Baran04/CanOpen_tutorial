# 00. Environment Setup

This stage is done before the CANopen tests. The goal is to reach a state where Linux sees the USB-CAN adapter as `can0`, Python has the required libraries installed, and `candump` shows heartbeat frames from the devices.

If the adapter is not immediately visible as `can0`, that is still part of this stage. A common case is that the adapter appears as `/dev/ttyUSB0` or `/dev/ttyACM0` and needs `slcand`.

Node IDs `2` and `3`, bitrate `500000`, and the EDS file in this repository are settings for the specific MOONS controller used here. With another device, use its node IDs, bitrate, and correct EDS file.

In CANopen, a `node` means a device on the network. In this example one MOONS controller exposes two nodes:

```text
node 2 = one drive axis
node 3 = the other drive axis
```

At this stage we do not command motion. We only test CAN communication and basic CANopen diagnostics.

## Target Configuration

After this stage we want:

- Linux system,
- Visual Studio Code or a normal terminal,
- USB-CAN adapter visible as `can0`,
- CAN handled through SocketCAN,
- bitrate `500000`,
- node IDs `2` and `3`,
- tests with `can-utils`, `python-can`, and `canopen`.

## Project Structure

```text
CanOpen_MikroKursy/
├── .venv/
├── docs_PL/
├── docs_EN/
├── eds/
│   └── CANOPEN-EDS-MBDV-Servo-DulAxes-V1.0.eds
├── src/
│   ├── config.py
│   ├── test_sdo_raw.py
│   └── test_canopen_eds.py
├── requirements.txt
└── README.md
```

Meaning of the directories:

- `.venv` - local Python environment,
- `docs_PL` - Polish tutorial lessons,
- `docs_EN` - English tutorial lessons,
- `eds` - EDS files for CANopen devices,
- `src` - small Python test scripts,
- `requirements.txt` - Python dependencies,
- `README.md` - project entry point.

## What Is an EDS File

An EDS file, or **Electronic Data Sheet**, is a text description of a CANopen device.

You can think of it as a data sheet for software. A person can read the manufacturer's PDF documentation, while a CANopen library can read the EDS file.

An EDS describes, among other things:

- which CANopen objects exist in the device,
- their indexes and subindexes,
- data types,
- whether an object is read-only or writable,
- default values,
- which objects can be mapped to PDO,
- basic device identity information.

Example drive object:

```text
0x6041:00 = Statusword
```

In the EDS file it may be described like this:

```text
ParameterName = Status word
DataType      = 0x0006
AccessType    = ro
```

This means:

```text
0x6041:00   = object address in the Object Dictionary
Statusword = object name
0x0006     = data type, here UNSIGNED16
ro         = read-only
```

You can communicate with the device without an EDS file, but then you must know object numbers and data types manually.

Example manual SDO read:

```bash
cansend can0 602#4041600000000000
```

This frame means:

```text
node ID 2
read object 0x6041:00
```

The frame itself does not tell you that `0x6041` is `Statusword`. That information comes from the documentation or from the EDS file.

In practice:

```text
without EDS = manual indexes, manual types, more knowledge required from the user
with EDS    = the library knows the device Object Dictionary
```

The EDS file is not device firmware, a Linux driver, or CAN bus configuration. It describes the device capabilities. Current parameter values are still read from the drive through CANopen, most often through SDO.

## Python Environment

Create and activate a local environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Quick check:

```bash
python -c "import can, canopen; print('OK')"
```

## CAN Adapter

Check whether the system sees the interface:

```bash
ip link show
```

If you see:

```text
can0
```

continue in this section.

If you do not see `can0`, but you see a serial port:

```text
/dev/ttyUSB0
/dev/ttyACM0
```

go first to [When the Adapter Appears as ttyUSB](#when-the-adapter-appears-as-ttyusb), then return here.

Set the bitrate and bring the interface up:

```bash
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up
```

Check details:

```bash
ip -details link show can0
```

Common CAN bitrates:

```text
125000
250000
500000
1000000
```

The bitrate must match the CANopen device.

## can-utils

For the first tests we use `candump` and `cansend`:

```bash
sudo apt install can-utils
```

Listen for CAN frames:

```bash
candump can0
```

Send a raw test CAN frame:

```bash
cansend can0 123#11223344
```

This only checks the raw CAN layer. It is not CANopen communication yet.

## CANopen Heartbeat

If `candump can0` shows:

```text
702   [1]  7F
703   [1]  7F
```

these are CANopen heartbeat frames.

Heartbeat uses the CAN identifier:

```text
0x700 + Node ID
```

Therefore:

```text
0x702 = heartbeat from node ID 2
0x703 = heartbeat from node ID 3
```

The data byte describes the device state:

```text
0x00 = boot-up
0x04 = stopped
0x05 = operational
0x7F = pre-operational
```

The result:

```text
702#7F
703#7F
```

means:

```text
Node 2 is in Pre-operational
Node 3 is in Pre-operational
```

This is a good and safe starting state for diagnostics. In `Pre-operational`, SDO reads are usually possible, while normal PDO operation is not active yet.

## When the Adapter Appears as ttyUSB

If the adapter does not appear as `can0`, but as a serial port, for example:

```text
/dev/ttyUSB0
/dev/ttyACM0
```

there are two common cases.

If the adapter supports SLCAN, you can use `slcand` to create `can0`:

```bash
sudo slcand -o -c -s6 /dev/ttyUSB0 can0
sudo ip link set can0 up
```

Example `slcand` speeds:

```text
-s4 = 125 kbit/s
-s5 = 250 kbit/s
-s6 = 500 kbit/s
-s8 = 1 Mbit/s
```

If the adapter does not support SLCAN, `slcand` will not help. You then need the manufacturer's driver, SDK, a matching `python-can` backend, or separate serial protocol handling.

## Hardware Checklist

Before testing, check:

```text
adapter CAN_H  -> device CAN_H
adapter CAN_L  -> device CAN_L
adapter GND    -> device GND, if required
termination    -> 120 ohm at the ends of the bus
bitrate        -> the same in adapter and device
Node ID        -> matches the device configuration
```

If the bus consists only of a USB-CAN adapter and one device, a 120 ohm termination between CAN_H and CAN_L is usually required.

## When to Continue

You can continue to the next stage if:

- `python -c "import can, canopen; print('OK')"` works,
- `ip -details link show can0` shows an active interface,
- `candump can0` shows heartbeat,
- node IDs `2` and `3` are visible,
- heartbeat has value `0x7F` or another understood NMT state.

Next step:

[01. Manual CANopen Tests](01-manual-canopen-tests.md)
