# 01. Manual CANopen Tests

This stage is done without Python. That makes it clear which CANopen frames are sent and which responses come back from the drive.

It is easiest to use two terminals:

```text
Terminal 1 = keep candump can0 running
Terminal 2 = type the following cansend commands
```

## NMT and SDO

This lesson uses two different CANopen mechanisms:

```text
NMT = Network Management
SDO = Service Data Object
```

NMT controls the communication state of a CANopen node. With NMT we tell the device things like:

```text
go to Operational
go back to Pre-operational
stop the node
```

NMT commands do not read drive parameters. They change the node's communication state on the CANopen network.

SDO reads or writes specific objects from the device Object Dictionary. With SDO we can ask, for example:

```text
what is Device Type 0x1000:00
what is Vendor ID 0x1018:01
what is Statusword 0x6041:00
```

In short:

```text
NMT = what state the node should be in
SDO = read or write a specific parameter of the node
```

In this lesson we use:

- NMT to switch between `Pre-operational` and `Operational`,
- SDO to manually read a few basic objects.

## NMT Test

NMT commands are sent on CAN ID:

```text
0x000
```

Data format:

```text
[command] [node_id]
```

Important commands for this stage:

```text
0x01 = Start Remote Node
0x80 = Enter Pre-operational
```

Do not use resets `0x81` or `0x82` yet.

In one terminal keep:

```bash
candump can0
```

In the second terminal type the following `cansend` commands.

Move node 2 to `Operational`:

```bash
cansend can0 000#0102
```

Expected heartbeat:

```text
702#05
```

Move node 2 back to `Pre-operational`:

```bash
cansend can0 000#8002
```

Expected heartbeat:

```text
702#7F
```

For node 3:

```bash
cansend can0 000#0103
cansend can0 000#8003
```

Expected heartbeats:

```text
703#05
703#7F
```

## SDO Test: Device Type

SDO request for node 2:

```text
0x600 + 2 = 0x602
```

SDO response for node 2:

```text
0x580 + 2 = 0x582
```

Read `0x1000:00`, `Device Type`, from node 2:

```bash
cansend can0 602#4000100000000000
```

Example correct response:

```text
582   [8]  43 00 10 00 XX XX XX XX
```

For node 3:

```bash
cansend can0 603#4000100000000000
```

The response should arrive on `0x583`.

## SDO Test: Identity Object

Identity Object is `0x1018`.

Node 2:

```bash
cansend can0 602#4018100100000000   # Vendor ID
cansend can0 602#4018100200000000   # Product Code
cansend can0 602#4018100300000000   # Revision Number
cansend can0 602#4018100400000000   # Serial Number
```

Node 3:

```bash
cansend can0 603#4018100100000000   # Vendor ID
cansend can0 603#4018100200000000   # Product Code
cansend can0 603#4018100300000000   # Revision Number
cansend can0 603#4018100400000000   # Serial Number
```

## How to Read SDO Responses

Correct expedited upload responses:

```text
0x43 = response with 4 data bytes
0x4B = response with 2 data bytes
0x4F = response with 1 data byte
```

Example from reading `0x1018:01`, `Vendor ID`, from node 3:

```text
can0  603   [8]  40 18 10 01 00 00 00 00
can0  583   [8]  43 18 10 01 D9 02 00 00
```

The first frame is the request:

```text
603       = SDO request to node 3, because 0x600 + 3
40        = SDO read request
18 10     = index 0x1018 in little-endian
01        = subindex 1
00...     = empty data bytes
```

The question is:

```text
read 0x1018:01 from node 3
```

Object `0x1018:01` is `Vendor ID`.

The second frame is the response:

```text
583          = SDO response from node 3, because 0x580 + 3
43           = expedited response with 4 data bytes
18 10 01     = confirmation of object 0x1018:01
D9 02 00 00  = data value
```

CANopen SDO data is little-endian. Therefore:

```text
D9 02 00 00 = 0x000002D9
```

The response means:

```text
Vendor ID = 0x000002D9
```

If this value matches the EDS, that is a very good sign:

```text
node ID is correct
SDO works
the device responds according to its Object Dictionary
```

If the response starts with `0x80`, it is an `SDO abort`.

Common causes:

- wrong node ID,
- object or subindex does not exist,
- object is not readable,
- device does not allow access in the current state,
- object map differs from what was expected.

## Read-only Drive Objects

After `0x1000` and `0x1018`, you can safely try diagnostic reads:

```bash
cansend can0 602#4001100000000000   # 0x1001:00 Error Register
cansend can0 602#403F600000000000   # 0x603F:00 Error Code
cansend can0 602#4041600000000000   # 0x6041:00 Statusword
cansend can0 602#4061600000000000   # 0x6061:00 Mode Display
cansend can0 602#4064600000000000   # 0x6064:00 Actual Position
cansend can0 602#406C600000000000   # 0x606C:00 Actual Velocity
cansend can0 602#4002650000000000   # 0x6502:00 Supported Drive Modes
```

For node 3, change `602` to `603`.

## When to Continue

You can continue if:

- NMT changes heartbeat between `0x7F` and `0x05`,
- node 2 responds to SDO,
- node 3 responds to SDO,
- reading `0x1018:01` returns a sensible `Vendor ID`.

Next step:

[02. Python Without EDS](02-python-without-eds.md)
