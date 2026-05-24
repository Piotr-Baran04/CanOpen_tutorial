# 02. Python Without EDS

After manual `cansend` tests, we can do the same from Python, still without using the EDS file. This test uses only `python-can` and raw SDO frames.

Run:

```bash
source .venv/bin/activate
python src/test_sdo_raw.py
```

By default the script uses settings from `src/config.py`:

```text
interface = socketcan
channel   = can0
nodes     = 2, 3
```

You can also pass parameters manually:

```bash
python src/test_sdo_raw.py --channel can0 --nodes 2 3 --timeout 1.0
```

The script reads:

```text
0x1000:00 = Device Type
0x1001:00 = Error Register
0x1018:01 = Vendor ID
0x1018:02 = Product Code
0x1018:03 = Revision Number
0x1018:04 = Serial Number
```

## Where These Indexes Come From

Indexes such as `0x1000`, `0x1001`, and `0x1018` are not invented in this project. They are standard CANopen Object Dictionary entries: https://en.wikipedia.org/wiki/CANopen

In CANopen, the device has an Object Dictionary, which is a table of parameters. Each parameter has an address:

```text
index:subindex
```

Example:

```text
0x1018:01
```

means:

```text
index    = 0x1018
subindex = 0x01
```

For the first test without EDS we choose very basic objects that are typically available in CANopen devices:

```text
0x1000:00 = Device Type
0x1001:00 = Error Register
0x1018:01 = Vendor ID
0x1018:02 = Product Code
0x1018:03 = Revision Number
0x1018:04 = Serial Number
```

Their numbers can be found in:

- the CANopen standard,
- the device documentation,
- the EDS file,
- manufacturer tools that show the Object Dictionary.

In this project they are also confirmed by the MOONS EDS file:

```text
eds/CANOPEN-EDS-MBDV-Servo-DulAxes-V1.0.eds
```

This test is "without EDS", but that does not mean the indexes come from nowhere. We manually enter a few known standard addresses instead of letting the `canopen` library read them from the EDS file.

Later drive-specific indexes, such as:

```text
0x6041:00 = Statusword
0x6064:00 = Actual Position
0x606C:00 = Actual Velocity
```

come from the CiA 402 drive profile and from the EDS/documentation of the specific drive.

This is a good test because it confirms four things at once:

- Python sees `can0`,
- `python-can` works,
- node 2 and node 3 respond to SDO,
- basic CANopen works without loading the EDS file.

## What This Script Does

The file being run is:

```text
src/test_sdo_raw.py
```

This script does in Python what we previously did manually with `cansend`: it sends an SDO request and waits for an SDO response.

Main difference:

```text
cansend          = you type the whole frame manually
test_sdo_raw.py  = Python builds and sends the frame for you
```

## Configuration Import

At the beginning the script imports:

```python
from config import CAN_CHANNEL, CAN_INTERFACE, NODE_IDS
```

These values come from `src/config.py`:

```text
CAN_INTERFACE = socketcan
CAN_CHANNEL   = can0
NODE_IDS      = 2, 3
```

This avoids repeating the same CAN channel and node IDs in many files.

## Object List

The code contains:

```python
READ_OBJECTS = (
    ("Device type", 0x1000, 0x00),
    ("Error register", 0x1001, 0x00),
    ("Vendor ID", 0x1018, 0x01),
    ("Product code", 0x1018, 0x02),
    ("Revision number", 0x1018, 0x03),
    ("Serial number", 0x1018, 0x04),
)
```

Each entry has this format:

```text
name, index, subindex
```

Example:

```text
"Vendor ID", 0x1018, 0x01
```

means:

```text
read object 0x1018:01
```

## Building the SDO Frame

For each object, the script calls:

```python
read_sdo_expedited(bus, node_id, index, subindex, timeout)
```

It first calculates the CAN IDs:

```python
request_id = 0x600 + node_id
response_id = 0x580 + node_id
```

For node 3:

```text
request_id  = 0x603
response_id = 0x583
```

Then it builds the request data:

```python
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
```

`0x40` means SDO read request.

The index is split into two bytes because SDO uses little-endian. For `0x1018`:

```text
index & 0xFF        = 0x18
(index >> 8) & 0xFF = 0x10
```

That is why the frame contains:

```text
18 10
```

and not:

```text
10 18
```

## Sending the Frame

The script sends the frame through `python-can`:

```python
bus.send(
    can.Message(
        arbitration_id=request_id,
        data=request,
        is_extended_id=False,
    ),
    timeout=timeout,
)
```

This corresponds to a manual command like:

```bash
cansend can0 603#4018100100000000
```

## Waiting for the Response

After sending the request, the script waits for a response frame:

```python
message = bus.recv(timeout=remaining)
```

It ignores frames that are not the expected response:

```python
if message.arbitration_id != response_id:
    continue
```

So if we ask node 3, the script ignores everything except:

```text
0x583
```

It also checks that the response is for the same index and subindex that we requested.

## SDO Abort

If the response starts with `0x80`, the device reported an SDO error:

```python
if command == 0x80:
    abort_code = int.from_bytes(message.data[4:8], byteorder="little")
    raise SdoAbortError(abort_code)
```

Then the script prints something like:

```text
FAIL Vendor ID 0x1018:01 SDO abort 0x....
```

That means the device responded, but refused access or did not recognize the object.

## Reading the Value

When the response is correct, the script extracts data bytes:

```python
payload = bytes(message.data[4 : 4 + size])
value = int.from_bytes(payload, byteorder="little", signed=False)
```

Example:

```text
D9 02 00 00
```

becomes:

```text
0x000002D9
```

which is the `Vendor ID` for this device.

## Result on Screen

The script prints a result for each node and object:

```text
Node 3
  OK   Vendor ID 0x1018:01              729 (0x000002D9, 4 B)
```

Meaning:

```text
OK          = read succeeded
Vendor ID  = tested object name
0x1018:01   = index and subindex
729         = decimal value
0x000002D9  = the same value in hexadecimal
4 B         = the device returned 4 data bytes
```

If you see `Brak odpowiedzi SDO` / no SDO response, first check:

- whether `can0` is `UP`,
- whether the bitrate is correct,
- whether `candump can0` still shows heartbeat,
- whether the node ID is correct.

## When to Continue

You can continue if the script shows `OK` for the basic SDO objects for at least one node, preferably for both node 2 and node 3.

Next step:

[03. Python With EDS](03-python-with-eds.md)
