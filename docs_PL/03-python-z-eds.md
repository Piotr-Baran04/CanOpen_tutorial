# 03. Python z EDS

Po potwierdzeniu SDO bez EDS można przejść do biblioteki `canopen` i Object Dictionary z pliku EDS.

Uruchom:

```bash
source .venv/bin/activate
python src/test_canopen_eds.py
```

Domyślnie skrypt bierze plik EDS z `src/config.py`:

```text
eds/CANOPEN-EDS-MBDV-Servo-DulAxes-V1.0.eds
```

Możesz też wskazać plik ręcznie:

```bash
python src/test_canopen_eds.py --eds eds/CANOPEN-EDS-MBDV-Servo-DulAxes-V1.0.eds --nodes 2 3
```

Skrypt odczytuje podstawowe obiekty CANopen i kilka read-only obiektów napędu:

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

## Co to jest CiA 402

CiA 402 to profil urządzenia CANopen dla napędów i sterowania ruchem. Nazwa pochodzi od organizacji **CiA**, czyli **CAN in Automation**, która standaryzuje CANopen.

Sam CANopen określa ogólne mechanizmy komunikacji, takie jak NMT, SDO, PDO, heartbeat i Object Dictionary. CiA 402 doprecyzowuje, jak w tym świecie ma wyglądać napęd.

CiA 402 definiuje między innymi:

- maszynę stanów napędu,
- `Controlword` do sterowania stanem napędu,
- `Statusword` do odczytu stanu napędu,
- tryby pracy napędu,
- typowe obiekty pozycji, prędkości i momentu.

Przykładowe obiekty CiA 402:

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

Dlatego w tym rozdziale zaczynają pojawiać się indeksy `0x60xx`. One nie biorą się z samego Pythona ani z naszego pomysłu na projekt. To standardowe obiekty profilu napędowego CiA 402, opisane dodatkowo w EDS konkretnego sterownika MOONS.

W praktyce:

```text
CANopen = ogólny protokół komunikacji urządzeń
CiA 402 = profil CANopen dla napędów
EDS     = plik opisujący, które obiekty obsługuje konkretny sterownik
```

Na tym etapie dalej nie zapisujemy nic do napędu. To jest celowo tylko diagnostyka.

## Co robi ten skrypt

Uruchamiany plik to:

```text
src/test_canopen_eds.py
```

Ten skrypt robi podobne odczyty jak `src/test_sdo_raw.py`, ale już nie składa ręcznie bajtów SDO. Zamiast tego używa biblioteki `canopen` oraz pliku EDS.

Najkrócej:

```text
test_sdo_raw.py      = ręczne SDO zbudowane w Pythonie
test_canopen_eds.py  = SDO przez bibliotekę canopen i Object Dictionary z EDS
```

## Import konfiguracji

Skrypt bierze ustawienia z `src/config.py`:

```python
from config import CAN_CHANNEL, CAN_INTERFACE, EDS_FILE, NODE_IDS
```

Te wartości określają:

```text
CAN_INTERFACE = socketcan
CAN_CHANNEL   = can0
NODE_IDS      = 2, 3
EDS_FILE      = plik EDS w katalogu eds/
```

## Lista obiektów

W kodzie znajduje się lista:

```python
READ_OBJECTS = (
    ("Device type", 0x1000, 0x00),
    ("Error register", 0x1001, 0x00),
    ("Vendor ID", 0x1018, 0x01),
    ("Statusword", 0x6041, 0x00),
    ("Actual position", 0x6064, 0x00),
)
```

Każdy wpis mówi skryptowi:

```text
nazwa do wypisania, indeks, subindeks
```

EDS pozwala bibliotece `canopen` wiedzieć, jak te obiekty wyglądają w Object Dictionary urządzenia.

## Połączenie z siecią CANopen

Skrypt tworzy obiekt sieci:

```python
network = canopen.Network()
network.connect(interface=args.interface, channel=args.channel)
```

Dla naszej konfiguracji oznacza to:

```text
połącz się z SocketCAN przez can0
```

To jest wyższy poziom niż `python-can`. Biblioteka `canopen` nadal korzysta z CAN pod spodem, ale daje wygodne obiekty typu `Network`, `RemoteNode` i `SDO`.

## Dodanie node'a z plikiem EDS

Dla każdego node ID skrypt tworzy zdalny node:

```python
node = canopen.RemoteNode(node_id, str(eds_path))
network.add_node(node)
```

To oznacza:

```text
utwórz node CANopen o danym node ID
wczytaj jego Object Dictionary z pliku EDS
dodaj node do sieci CANopen
```

Dla node 3 biblioteka wie wtedy:

```text
SDO request  = 0x603
SDO response = 0x583
Object Dictionary = z pliku EDS
```

## Odczyt obiektu

Najważniejsza funkcja to:

```python
def read_object(node, index, subindex):
    entry = node.sdo[index]
    if subindex == 0:
        return entry.raw
    return entry[subindex].raw
```

Przykład:

```text
index    = 0x1018
subindex = 0x01
```

Skrypt robi wtedy logicznie:

```python
node.sdo[0x1018][1].raw
```

Czyli:

```text
odczytaj przez SDO surową wartość obiektu 0x1018:01
```

Nie musimy już ręcznie pisać ramki:

```text
40 18 10 01 00 00 00 00
```

Biblioteka `canopen` robi to za nas.

## Formatowanie wyniku

Jeżeli odczytywany obiekt to `0x6041 Statusword`, skrypt używa funkcji:

```python
format_statusword(value)
```

z pliku:

```text
src/cia402.py
```

Dzięki temu zamiast samej liczby można zobaczyć bardziej czytelny opis stanu napędu, na przykład:

```text
0x0040 - Switch on disabled (switch_on_disabled)
```

Pozostałe liczby są wypisywane w dwóch formach:

```text
729 (0x2D9)
```

czyli dziesiętnie i szesnastkowo.

## Co dalej

Kolejne kroki powinny iść w tej kolejności:

1. Odczytać i zinterpretować `Statusword` `0x6041`.
2. Sprawdzić, czy napęd nie zgłasza błędu przez `0x1001` i `0x603F`.
3. Dopiero potem przygotować osobny, kontrolowany test CiA 402 dla `Controlword` `0x6040`.
4. Ruch testować dopiero po potwierdzeniu limitów, trybu pracy i warunków bezpieczeństwa.

Następny krok:

[04. Heartbeat i NMT z Pythona](04-heartbeat-i-nmt-python.md)
