# 05. Statusword and CiA 402 States

After CANopen communication is confirmed, the most important drive object is:

```text
0x6041:00 = Statusword
```

This is the CiA 402 status word. It tells us what state the drive is in and whether we can move further through the state machine.

At this stage we only read `Statusword`. We do not write `Controlword` yet.

## Manual Read

For node 2:

```bash
cansend can0 602#4041600000000000
```

The response arrives on `0x582`.

For node 3:

```bash
cansend can0 603#4041600000000000
```

The response arrives on `0x583`.

## Read Through the EDS Script

```bash
source .venv/bin/activate
python src/test_canopen_eds.py
```

The script reads, among other objects:

```text
0x603F:00 = Error Code
0x6041:00 = Statusword
0x6061:00 = Modes of Operation Display
0x6064:00 = Actual Position
0x606C:00 = Actual Velocity
```

## What the Statusword Decoder Does

The readable `Statusword` description is produced by:

```text
src/cia402.py
```

It is used by:

```text
src/test_canopen_eds.py
```

When `test_canopen_eds.py` reads object `0x6041`, it calls:

```python
format_statusword(value)
```

## Bit List

In `src/cia402.py` there is a list of bits:

```python
STATUSWORD_BITS = (
    (0, "ready_to_switch_on"),
    (1, "switched_on"),
    (2, "operation_enabled"),
    (3, "fault"),
    (4, "voltage_enabled"),
    (5, "quick_stop_not_active"),
    (6, "switch_on_disabled"),
)
```

Each entry means:

```text
bit number, bit description
```

The function:

```python
decode_statusword_bits(value)
```

checks which bits are set:

```python
bool(value & (1 << bit))
```

Example for bit 3:

```text
bit 3 = fault
1 << 3 = 0x0008
```

If:

```text
Statusword & 0x0008 != 0
```

then bit `fault` is active.

## Recognizing the CiA 402 State

Checking individual bits is not enough, because the CiA 402 state is a combination of several bits. That is why:

```python
statusword_state(value)
```

uses bit masks.

Example:

```python
if (value & 0x004F) == 0x0040:
    return "Switch on disabled"
```

Meaning:

```text
take only the bits needed for this decision
compare them with the Switch on disabled pattern
```

Another example:

```python
if (value & 0x006F) == 0x0027:
    return "Operation enabled"
```

If `Statusword` matches this pattern, the drive is in:

```text
Operation enabled
```

This still does not mean that the script commands motion. It only describes the current state read from the drive.

## Output Format

The function:

```python
format_statusword(value)
```

combines two pieces of information:

```text
CiA 402 state
list of active status bits
```

Example result:

```text
0x0040 - Switch on disabled (switch_on_disabled)
```

Meaning:

```text
0x0040              = raw Statusword value
Switch on disabled = recognized CiA 402 state
switch_on_disabled = active status bit
```

## Most Important Statusword Bits

```text
bit 0  = ready to switch on
bit 1  = switched on
bit 2  = operation enabled
bit 3  = fault
bit 4  = voltage enabled
bit 5  = quick stop not active
bit 6  = switch on disabled
bit 7  = warning
bit 9  = remote
bit 10 = target reached
bit 11 = internal limit active
```

Typical CiA 402 states:

```text
Not ready to switch on
Switch on disabled
Ready to switch on
Switched on
Operation enabled
Quick stop active
Fault reaction active
Fault
```

## What to Check Before Any Motion

First, know the answers to these questions:

- does `0x1001 Error Register` report an error,
- is `0x603F Error Code` zero,
- does `0x6041 Statusword` show `Fault`,
- does `0x6061 Mode Display` match the expected mode,
- does current position `0x6064` change sensibly if the axis is moved manually,
- does current velocity `0x606C` return to zero when the axis is stopped.

## Only Later: Controlword

Object:

```text
0x6040:00 = Controlword
```

is a write object that controls the drive state machine. A typical CiA 402 sequence is:

```text
0x0006 = Shutdown
0x0007 = Switch on
0x000F = Enable operation
```

We do not do this in the first tests. First, status and error reads must be understood.

## Good End Point for This Stage

This stage is complete when you can say for each node:

```text
node ID
NMT state from heartbeat
Error Register
Error Code
Statusword
CiA 402 state
Mode Display
Actual Position
Actual Velocity
```

## When to Continue

You can continue if you understand `Statusword`, there are no active errors, and the test stand is ready for real motion.

Next step:

[06. Keyboard Jog](06-keyboard-jog.md)
