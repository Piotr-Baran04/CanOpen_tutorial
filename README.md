# CanOpen_MikroKursy

To repo jest prostym samouczkiem uruchamiania CANopen na Linuxie: od doprowadzenia adaptera USB-CAN do interfejsu `can0`, przez ręczne ramki `cansend`, aż do pierwszych odczytów z Pythona bez EDS i z EDS.

Ten plik jest punktem startowym. Szczegółowe instrukcje są w folderach:

```text
docs_PL/ = instrukcje po polsku
docs_EN/ = the same tutorial in English
```

To jest konkretny przykład dla używanego tutaj sterownika MOONS: node ID, bitrate oraz plik EDS trzeba traktować jako ustawienia tego stanowiska, a nie uniwersalne wartości dla każdego urządzenia CANopen.

## Docelowy stan po przygotowaniu

Po przejściu pierwszej lekcji chcemy mieć taki stan:

- adapter USB-CAN działa jako SocketCAN `can0`,
- `candump can0` pokazuje heartbeat,
- widoczne są node'y `2` i `3`,
- heartbeat `0x7F` oznacza stan `Pre-operational`,
- wykonujemy tylko diagnostykę i odczyty, bez uruchamiania ruchu.

Jeżeli adapter nie pojawia się od razu jako `can0`, tylko np. jako `/dev/ttyUSB0`, zacznij od [00. Przygotowanie środowiska](docs_PL/00-przygotowanie.md). Tam jest sekcja o `slcand` i SLCAN.

## Kolejność pracy

1. [00. Przygotowanie środowiska](docs_PL/00-przygotowanie.md)
2. [01. Ręczne testy CANopen](docs_PL/01-reczne-testy-canopen.md)
3. [02. Python bez EDS](docs_PL/02-python-bez-eds.md)
4. [03. Python z EDS](docs_PL/03-python-z-eds.md)
5. [04. Heartbeat i NMT z Pythona](docs_PL/04-heartbeat-i-nmt-python.md)
6. [05. Statusword i stany CiA 402](docs_PL/05-statusword-cia402.md)
7. [06. Ruch strzałkami z klawiatury](docs_PL/06-ruch-strzalkami.md)

Krótkie menu całej dokumentacji jest w [docs_PL/MENU.md](docs_PL/MENU.md).

English version:

[docs_EN/MENU.md](docs_EN/MENU.md)

## Co jest w repo

```text
.
├── docs_PL/     # lekcje samouczka po polsku
├── docs_EN/     # English version of the tutorial
├── eds/         # pliki EDS urządzeń CANopen
├── src/         # małe skrypty diagnostyczne
├── README.md    # punkt startowy
└── requirements.txt
```

Najważniejsze skrypty:

```text
src/test_sdo_raw.py      # SDO bez EDS, przez python-can
src/test_canopen_eds.py  # odczyty przez bibliotekę canopen i EDS
src/monitor_heartbeat.py # podgląd heartbeatów
src/nmt_command.py       # proste komendy NMT: start, preop, stop
src/keyboard_jog.py      # ostrożny ruch strzałkami w trybie prędkości
```

## Zasada bezpieczeństwa

Najpierw tylko odczyty. Zapisy do obiektów takich jak `0x6040 Controlword`, `0x6060 Modes of Operation`, `0x607A Target Position` albo `0x60FF Target Velocity` robimy dopiero w osobnym etapie, po zrozumieniu `Statusword` i aktualnego stanu napędu.

## Start

Zacznij tutaj:

[docs_PL/00-przygotowanie.md](docs_PL/00-przygotowanie.md)
