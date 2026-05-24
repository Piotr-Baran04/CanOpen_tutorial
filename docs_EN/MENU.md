# Documentation Menu

This is the short lesson list for `docs_EN/`. The main entry point for the whole repository is still [../README.md](../README.md).

Polish version:

[../docs_PL/MENU.md](../docs_PL/MENU.md)

## Lessons

1. [00. Environment Setup](00-environment-setup.md)
2. [01. Manual CANopen Tests](01-manual-canopen-tests.md)
3. [02. Python Without EDS](02-python-without-eds.md)
4. [03. Python With EDS](03-python-with-eds.md)
5. [04. Heartbeat and NMT from Python](04-heartbeat-and-nmt-python.md)
6. [05. Statusword and CiA 402 States](05-statusword-cia402.md)
7. [06. Keyboard Jog](06-keyboard-jog.md)

## How to Read

Each lesson starts with the practical part: what to run and what result is expected. Sections named "What this script does" explain the mechanism. On the first pass, you can run the test first and read the explanation afterwards.

## Progression

```text
Linux sees can0
  -> candump sees heartbeat
  -> manual SDO responds
  -> Python can send SDO without EDS
  -> Python can read through EDS
  -> Statusword is understood
  -> only then try Controlword and very small motion
```

If something stops working, go back one lesson.
