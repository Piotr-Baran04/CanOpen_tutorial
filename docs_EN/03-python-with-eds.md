# 03. Python With EDS

After confirming SDO communication without EDS, we can use the `canopen` library and the Object Dictionary loaded from the EDS file.

Run:

```bash
source .venv/bin/activate
python src/test_canopen_eds.py
```

By default the script takes the EDS file path from `src/config.py`:

```text
eds/CANOPEN-EDS-MBDV-Servo-DulAxes-V1.0.eds
```

You can also pass the file manually:

```bash
python src/test_canopen_eds.py --eds eds/CANOPEN-EDS-MBDV-Servo-DulAxes-V1.0.eds --nodes 2 3
```

The script reads basic CANopen objects and a few read-only drive objects:

```text
0x1000:00 = Device Type
0x1001:00 = Error Register
0x1018:01 = Vendor ID
0x1018:02 = Product Code
0x1018:03 = Revision Number
0x1018:04 = Serial Number
0x603F:00 = Error Code
0x6041:00 = Statusword
0x6061:00 = Modes of Operation Display
0x6064:00 = Actual Position
0x606C:00 = Actual Velocity
0x6502:00 = Supported Drive Modes
```

## What Is CiA 402

CiA 402 is the CANopen device profile for drives and motion control. The name comes from **CiA**, **CAN in Automation**, the organization that standardizes CANopen.

CANopen defines general communication mechanisms such as NMT, SDO, PDO, heartbeat, and the Object Dictionary. CiA 402 defines how a drive should look inside that CANopen world.

CiA 402 defines, among other things:

- the drive state machine,
- `Controlword` for commanding the drive state,
- `Statusword` for reading the drive state,
- drive operation modes,
- typical position, velocity, and torque objects.

Example CiA 402 objects:

```text
0x6040:00 = Controlword
0x6041:00 = Statusword
0x6060:00 = Modes of Operation
0x6061:00 = Modes of Operation Display
0x6064:00 = Position Actual Value
0x606C:00 = Velocity Actual Value
0x607A:00 = Target Position
0x60FF:00 = Target Velocity
```

That is why indexes `0x60xx` start appearing in this lesson. They do not come from Python or from this project idea. They are standard objects from the CiA 402 drive profile, also described in the EDS file of the MOONS controller.

In practice:

```text
CANopen = general device communication protocol
CiA 402 = CANopen profile for drives
EDS     = file describing which objects this controller supports
```

At this stage we still do not write anything to the drive. This is intentionally diagnostics only.

## What This Script Does

The file being run is:

```text
src/test_canopen_eds.py
```

This script does similar reads as `src/test_sdo_raw.py`, but it no longer builds SDO bytes manually. Instead it uses the `canopen` library and the EDS file.

In short:

```text
test_sdo_raw.py      = manual SDO built in Python
test_canopen_eds.py  = SDO through canopen and Object Dictionary from EDS
```

## Configuration Import

The script takes settings from `src/config.py`:

```python
from config import CAN_CHANNEL, CAN_INTERFACE, EDS_FILE, NODE_IDS
```

These values define:

```text
CAN_INTERFACE = socketcan
CAN_CHANNEL   = can0
NODE_IDS      = 2, 3
EDS_FILE      = EDS file in the eds/ directory
```

## Object List

The code contains a list:

```python
READ_OBJECTS = (
    ("Device type", 0x1000, 0x00),
    ("Error register", 0x1001, 0x00),
    ("Vendor ID", 0x1018, 0x01),
    ("Statusword", 0x6041, 0x00),
    ("Actual position", 0x6064, 0x00),
)
```

Each entry tells the script:

```text
name to print, index, subindex
```

The EDS lets the `canopen` library know what these objects look like in the device Object Dictionary.

## Connecting to the CANopen Network

The script creates a network object:

```python
network = canopen.Network()
network.connect(interface=args.interface, channel=args.channel)
```

For our configuration this means:

```text
connect to SocketCAN through can0
```

This is a higher level than `python-can`. The `canopen` library still uses CAN underneath, but gives convenient objects such as `Network`, `RemoteNode`, and `SDO`.

## Adding a Node with the EDS File

For each node ID, the script creates a remote node:

```python
node = canopen.RemoteNode(node_id, str(eds_path))
network.add_node(node)
```

This means:

```text
create a CANopen node with the given node ID
load its Object Dictionary from the EDS file
add the node to the CANopen network
```

For node 3, the library then knows:

```text
SDO request  = 0x603
SDO response = 0x583
Object Dictionary = from the EDS file
```

## Reading an Object

The most important function is:

```python
def read_object(node, index, subindex):
    entry = node.sdo[index]
    if subindex == 0:
        return entry.raw
    return entry[subindex].raw
```

Example:

```text
index    = 0x1018
subindex = 0x01
```

The script then logically does:

```python
node.sdo[0x1018][1].raw
```

Meaning:

```text
read raw value of object 0x1018:01 through SDO
```

We no longer need to manually write the frame:

```text
40 18 10 01 00 00 00 00
```

The `canopen` library does that for us.

## Formatting the Result

If the object is `0x6041 Statusword`, the script uses:

```python
format_statusword(value)
```

from:

```text
src/cia402.py
```

This makes the drive state easier to read, for example:

```text
0x0040 - Switch on disabled (switch_on_disabled)
```

Other numbers are printed in decimal and hexadecimal:

```text
729 (0x2D9)
```

## What Next

Next steps should go in this order:

1. Read and interpret `Statusword` `0x6041`.
2. Check whether the drive reports errors through `0x1001` and `0x603F`.
3. Only then prepare a separate, controlled CiA 402 test for `Controlword` `0x6040`.
4. Test motion only after confirming limits, operation mode, and safety conditions.

Next step:

[04. Heartbeat and NMT from Python](04-heartbeat-and-nmt-python.md)
