# 04. Heartbeat and NMT from Python

After manual tests with `candump` and `cansend`, we can do the same stage more comfortably from Python. We still do not command drive motion.

## Heartbeat Monitor

Heartbeat is a cyclic frame:

```text
0x700 + node_id
```

For node 2 and 3:

```text
0x702
0x703
```

Run the monitor:

```bash
source .venv/bin/activate
python src/monitor_heartbeat.py
```

Example result:

```text
node   2: heartbeat 0x7F (Pre-operational)
node   3: heartbeat 0x7F (Pre-operational)
```

Listen for longer:

```bash
python src/monitor_heartbeat.py --duration 30
```

Show heartbeat from all nodes:

```bash
python src/monitor_heartbeat.py --all
```

## What the Heartbeat Monitor Does

The file being run is:

```text
src/monitor_heartbeat.py
```

The script uses `python-can`, so it works with raw CAN frames.

First it opens the bus:

```python
with can.Bus(interface=args.interface, channel=args.channel) as bus:
```

For our configuration:

```text
interface = socketcan
channel   = can0
```

Then it receives frames:

```python
message = bus.recv(timeout=timeout)
```

It only cares about heartbeat frames, CAN IDs from:

```text
0x700 to 0x77F
```

In the code:

```python
if arbitration_id < 0x700 or arbitration_id > 0x77F:
    continue
```

Node ID is calculated from the CAN ID:

```python
node_id = arbitration_id - 0x700
```

Example:

```text
0x703 - 0x700 = 3
```

so frame `0x703` is heartbeat from node 3.

The first data byte is the NMT state:

```python
state = message.data[0]
```

The script translates it through:

```python
HEARTBEAT_STATES = {
    0x00: "Boot-up",
    0x04: "Stopped",
    0x05: "Operational",
    0x7F: "Pre-operational",
}
```

Therefore:

```text
node   3: heartbeat 0x7F (Pre-operational)
```

means:

```text
CAN ID 0x703
node ID 3
NMT state 0x7F
state name Pre-operational
```

## NMT Commands

NMT is sent on CAN ID:

```text
0x000
```

`src/nmt_command.py` supports only three basic commands:

```text
start = 0x01
stop  = 0x02
preop = 0x80
```

There are intentionally no resets `0x81` and `0x82` here. At the beginning, it is easier to diagnose the system without restarting devices.

## What the NMT Script Does

The file being run is:

```text
src/nmt_command.py
```

The script maps the command name to an NMT byte:

```python
NMT_COMMANDS = {
    "start": 0x01,
    "stop": 0x02,
    "preop": 0x80,
}
```

When you type:

```bash
python src/nmt_command.py start 2
```

the script builds this frame:

```python
can.Message(
    arbitration_id=0x000,
    data=[0x01, 0x02],
    is_extended_id=False,
)
```

This matches the manual command:

```bash
cansend can0 000#0102
```

Data meaning:

```text
0x01 = Start Remote Node
0x02 = node ID 2
```

After sending the command, the script waits for heartbeat from that node:

```python
response_id = 0x700 + node_id
```

For node 2:

```text
0x700 + 2 = 0x702
```

If heartbeat arrives with:

```text
0x05
```

the script prints:

```text
Heartbeat node 2: 0x05 (Operational)
```

If you use node ID `0`, that means broadcast. The script sends the command to all nodes, but does not wait for one specific heartbeat.

## Node 2

Go to `Operational`:

```bash
python src/nmt_command.py start 2
```

Expected heartbeat:

```text
0x05 (Operational)
```

Return to `Pre-operational`:

```bash
python src/nmt_command.py preop 2
```

Expected heartbeat:

```text
0x7F (Pre-operational)
```

## Node 3

```bash
python src/nmt_command.py start 3
python src/nmt_command.py preop 3
```

## Broadcast

Node ID `0` means broadcast:

```bash
python src/nmt_command.py start 0
python src/nmt_command.py preop 0
```

At the beginning, test nodes separately. Broadcast is convenient only after you know which devices are on the bus.

## Safety

NMT `Operational` is not the same as `Enable Operation` in CiA 402. NMT alone should not command motion, but it can enable normal PDO communication of the device.

After the test, it is good to return to:

```bash
python src/nmt_command.py preop 2
python src/nmt_command.py preop 3
```

## When to Continue

You can continue if the heartbeat monitor shows node states and the NMT script can switch node 2 and node 3 to `Operational` and back to `Pre-operational`.

Next step:

[05. Statusword and CiA 402 States](05-statusword-cia402.md)
