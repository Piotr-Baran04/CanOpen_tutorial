# 06. Keyboard Jog

This is the first stage that can actually move the motors. Do it only after completing the previous lessons and only after confirming that the test stand is safe.

At this stage we assume:

```text
node 2 = left axis
node 3 = right axis
```

Controls:

```text
arrow up    or W = both motors forward
arrow down  or S = both motors backward
arrow left  or A = turn left
arrow right or D = turn right
space            = stop
q                = quit
```

If physical directions are reversed, stop the test and use `--invert-node`. Do not try to fix direction by increasing speed.

## Conditions Before Start

Before this test, check:

- mechanics can move safely,
- axes are not at limit switches,
- you can cut power in an emergency,
- [03. Python With EDS](03-python-with-eds.md) works correctly,
- `Error register 0x1001:00` is `0`,
- `Error code 0x603F:00` is `0`,
- you understand that this script writes to drive control objects.

## Keyboard Test

First check whether the terminal recognizes keys correctly:

```bash
source .venv/bin/activate
python src/keyboard_jog.py --key-debug
```

This mode does not connect to CAN and does not enable the drive. Press arrows and `W`, `A`, `S`, `D`.

Expected results:

```text
arrow up or W    -> key: 'UP'
arrow down or S  -> key: 'DOWN'
arrow left or A  -> key: 'LEFT'
arrow right or D -> key: 'RIGHT'
space            -> key: 'SPACE'
q                -> key: 'QUIT'
```

If arrows do not work but `WASD` works, use `WASD`. Some terminals send arrow keys differently.

## First Motion Run

The script requires the explicit `--enable` parameter. Without it, it refuses to run.

Do the first test with a low speed:

```bash
python src/keyboard_jog.py --enable --speed-rad-s 0.5
```

Hold an arrow or `W`, `A`, `S`, `D` briefly. After the key is released, the script sends speed `0` if it does not receive another keyboard signal for a short moment.

If everything works and the stand is safe, you can try:

```bash
python src/keyboard_jog.py --enable --speed-rad-s 1.0
```

`--speed-rad-s` means output gearbox speed in radians per second. This is easier than typing raw drive units.

## If an Axis Direction Is Reversed

If node 2 rotates in the wrong direction:

```bash
python src/keyboard_jog.py --enable --speed-rad-s 0.5 --invert-node 2
```

If node 3 rotates in the wrong direction:

```bash
python src/keyboard_jog.py --enable --speed-rad-s 0.5 --invert-node 3
```

If both are reversed:

```bash
python src/keyboard_jog.py --enable --speed-rad-s 0.5 --invert-node 2 3
```

If left and right axes are swapped, change node order:

```bash
python src/keyboard_jog.py --enable --speed-rad-s 0.5 --nodes 3 2
```

## Velocity Scale

In the drive, object:

```text
0x60FF:00 = Target Velocity
```

does not directly store a value in `rad/s`. The drive uses its internal unit, which depends on the encoder and gearbox.

For this outdoor test stand we assume:

```text
P3-05 = 10000 pulses per revolution
gearbox_ratio = 30
```

Therefore:

```text
1.0 rad/s at gearbox output ~= 47746 drive units
```

The scale is stored in `src/config.py`:

```text
node 2: -47746.4829276
node 3:  47746.4829276
```

The minus sign for node 2 comes from the axis mounting direction. Thanks to that, the "forward" command can mean the same physical robot direction for both sides.

## What This Script Does

The file being run is:

```text
src/keyboard_jog.py
```

The script does two different things:

```text
1. Configures the drive through SDO.
2. Sends target velocity through RPDO.
```

### SDO

SDO, **Service Data Object**, works like a single question or command to a specific object in the device dictionary.

Examples:

```text
read Statusword 0x6041:00
set Modes of Operation 0x6060:00
set Profile Acceleration 0x6083:00
```

SDO is convenient for configuration and diagnostics because we explicitly specify:

```text
node ID
index
subindex
value
```

In this script, SDO is used at the beginning to prepare the drive for velocity mode.

### RPDO

PDO, **Process Data Object**, is used for fast process data exchange, for example actual position or target velocity.

RPDO means **Receive PDO** from the drive's point of view:

```text
computer sends the frame
drive receives it
```

During motion, the script sends velocity through RPDO:

```text
0x402 = RPDO node 2
0x403 = RPDO node 3
```

Each such frame contains:

```text
Controlword 0x6040:00
Target Velocity 0x60FF:00
```

In short:

```text
SDO  = calm configuration and reads
RPDO = fast velocity commands during motion
```

## CiA 402 Transition

For keyboard driving we use:

```text
0x6060:00 = Modes of Operation
value 3   = Profile Velocity Mode
```

Before motion, the script goes through the standard `Controlword` sequence:

```text
0x0006 = Shutdown
0x0007 = Switch on
0x000F = Enable operation
```

After each step it checks:

```text
0x6041:00 = Statusword
```

The point is not to assume blindly that the drive accepted the command. The script waits until the drive confirms the correct state.

## How Keys Become Motion

The key is first mapped to a command:

```text
UP    -> forward
DOWN  -> backward
LEFT  -> left
RIGHT -> right
SPACE -> stop
```

Then the command is mapped to two velocities:

```text
forward  = +speed, +speed
backward = -speed, -speed
left     = -speed, +speed
right    = +speed, -speed
stop     = 0, 0
```

Finally these values are converted from `rad/s` to drive units and sent to node 2 and node 3.

## Stop and Exit

During operation:

```text
space = stop
q     = quit
Ctrl+C = interrupt program
```

On exit, the script always tries to send:

```text
0x60FF:00 = 0
0x6040:00 = 0x0000
```

This first commands speed `0`, then sends `Disable voltage`.

## Optional Diagnostics

If the motors still do not rotate even though the drive reaches `Operation enabled`, you can enable the diagnostic view:

```bash
python src/keyboard_jog.py --enable --speed-rad-s 0.5 --telemetry
```

This option prints, among other things:

```text
Target Velocity
Actual Velocity
Mode Display
Error Register / Error Code
Statusword
```

You do not need to analyze these fields on the first pass through the tutorial. They are a diagnostic aid when something does not work.

You can also watch PDO frames in a separate terminal:

```bash
candump can0,282:7FF,283:7FF,402:7FF,403:7FF,482:7FF,483:7FF
```

Typical IDs for this stand:

```text
0x402 = RPDO to node 2
0x403 = RPDO to node 3
0x282 = TPDO from node 2
0x283 = TPDO from node 3
0x482 = TPDO from node 2
0x483 = TPDO from node 3
```

TPDO means **Transmit PDO** from the drive's point of view:

```text
drive sends the frame
computer receives it
```

## When This Stage Is Complete

This stage is complete when:

- you can run the script with `--enable`,
- the drive reaches `Operation enabled`,
- `W/S/A/D` or arrows produce predictable motion,
- space stops motion,
- `q` or `Ctrl+C` stops the axes and ends the program.

## End

Return to the menu:

[MENU.md](MENU.md)
