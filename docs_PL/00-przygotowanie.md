# 00. Przygotowanie środowiska

Ten etap robi się przed testami CANopen. Celem jest doprowadzenie do sytuacji, w której Linux widzi adapter jako `can0`, Python ma zainstalowane biblioteki, a w `candump` widać heartbeat urządzeń.

Jeżeli adapter nie jest od razu widoczny jako `can0`, to nadal jest część tego etapu. Niżej jest opisany przypadek, gdy adapter pojawia się jako `/dev/ttyUSB0` albo `/dev/ttyACM0` i trzeba użyć `slcand`.

Node ID `2` i `3`, bitrate `500000` oraz plik EDS w tym repo są ustawieniami dla konkretnego testowanego sterownika MOONS. Przy innym urządzeniu trzeba użyć jego node ID, bitrate i właściwego pliku EDS.

W CANopen słowo `node` oznacza urządzenie w sieci. W tym przykładzie jeden sterownik MOONS udostępnia dwa node'y:

```text
node 2 = jedna oś napędu
node 3 = druga oś napędu
```

Na tym etapie nie uruchamiamy jeszcze napędu ruchowo. Testowana jest wyłącznie komunikacja CAN oraz podstawowa diagnostyka CANopen.

## Docelowa konfiguracja

Po tym etapie chcemy mieć:

- system Linux,
- edytor Visual Studio Code albo zwykły terminal,
- adapter USB-CAN widoczny jako `can0`,
- obsługę magistrali przez SocketCAN,
- bitrate `500000`,
- node ID `2` i `3`,
- testy przez `can-utils`, `python-can` i `canopen`.

## Struktura projektu

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

Znaczenie katalogów:

- `.venv` - lokalne środowisko Pythona,
- `docs_PL` - kolejne lekcje samouczka po polsku,
- `docs_EN` - te same lekcje po angielsku,
- `eds` - pliki EDS urządzeń CANopen,
- `src` - skrypty testowe w Pythonie,
- `requirements.txt` - zależności Pythona,
- `README.md` - punkt startowy projektu.

## Co to jest plik EDS

Plik EDS, czyli **Electronic Data Sheet**, to tekstowy opis urządzenia CANopen.

Można o nim myśleć jak o karcie katalogowej dla programu. Człowiek może czytać dokumentację producenta w PDF, a biblioteka CANopen może czytać plik EDS.

EDS opisuje między innymi:

- jakie obiekty CANopen istnieją w urządzeniu,
- jakie mają indeksy i subindeksy,
- jakiego typu są dane,
- czy obiekt jest tylko do odczytu, czy można go zapisywać,
- jakie są wartości domyślne,
- jakie obiekty mogą być mapowane do PDO,
- podstawowe informacje identyfikacyjne urządzenia.

Przykład obiektu z napędu:

```text
0x6041:00 = Statusword
```

W pliku EDS może być opisane, że:

```text
ParameterName = Status word
DataType      = 0x0006
AccessType    = ro
```

Oznacza to:

```text
0x6041:00   = adres obiektu w Object Dictionary
Statusword = nazwa obiektu
0x0006     = typ danych, tutaj UNSIGNED16
ro         = read-only, czyli tylko do odczytu
```

Bez pliku EDS nadal można komunikować się z urządzeniem, ale trzeba ręcznie znać numery obiektów i typy danych.

Przykład ręcznego odczytu SDO:

```bash
cansend can0 602#4041600000000000
```

Ta ramka oznacza:

```text
node ID 2
odczytaj obiekt 0x6041:00
```

Z samej ramki nie widać jednak, że `0x6041` to `Statusword`. Tę informację daje dokumentacja albo plik EDS.

W praktyce:

```text
bez EDS = ręczne indeksy, ręczne typy, więcej wiedzy po stronie użytkownika
z EDS   = biblioteka zna słownik obiektów urządzenia
```

Plik EDS nie jest firmware urządzenia, sterownikiem Linuxa ani konfiguracją magistrali CAN. To opis możliwości urządzenia. Aktualne wartości parametrów nadal są odczytywane z napędu przez CANopen, najczęściej przez SDO.

## Środowisko Python

Utwórz i aktywuj lokalne środowisko:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Zainstaluj zależności:

```bash
pip install -r requirements.txt
```

Szybkie sprawdzenie:

```bash
python -c "import can, canopen; print('OK')"
```

## Adapter CAN

Sprawdź, czy system widzi interfejs:

```bash
ip link show
```

Jeżeli widzisz interfejs:

```text
can0
```

to możesz iść dalej w tej sekcji.

Jeżeli nie widzisz `can0`, ale widzisz port szeregowy:

```text
/dev/ttyUSB0
/dev/ttyACM0
```

przejdź najpierw do sekcji [Gdy adapter jest widoczny jako ttyUSB](#gdy-adapter-jest-widoczny-jako-ttyusb), a potem wróć tutaj.

Ustaw bitrate i uruchom interfejs:

```bash
sudo ip link set can0 down
sudo ip link set can0 type can bitrate 500000
sudo ip link set can0 up
```

Sprawdzenie szczegółów:

```bash
ip -details link show can0
```

Typowe prędkości CAN:

```text
125000
250000
500000
1000000
```

Bitrate musi być zgodny z urządzeniem CANopen.

## can-utils

Do pierwszych testów używamy `candump` i `cansend`:

```bash
sudo apt install can-utils
```

Nasłuch ramek:

```bash
candump can0
```

Wysłanie testowej surowej ramki CAN:

```bash
cansend can0 123#11223344
```

To sprawdza tylko surową warstwę CAN. Nie jest to jeszcze komunikacja CANopen.

## Heartbeat CANopen

Jeżeli w `candump can0` widać:

```text
702   [1]  7F
703   [1]  7F
```

to są ramki heartbeat CANopen.

Heartbeat ma identyfikator:

```text
0x700 + Node ID
```

Dlatego:

```text
0x702 = heartbeat node ID 2
0x703 = heartbeat node ID 3
```

Bajt danych określa stan urządzenia:

```text
0x00 = boot-up
0x04 = stopped
0x05 = operational
0x7F = pre-operational
```

Wynik:

```text
702#7F
703#7F
```

oznacza:

```text
Node 2 jest w stanie Pre-operational
Node 3 jest w stanie Pre-operational
```

To jest dobry i bezpieczny stan startowy do diagnostyki. W stanie `Pre-operational` można zwykle wykonywać odczyty SDO, natomiast urządzenie nie pracuje jeszcze normalnie przez PDO.

## Gdy adapter jest widoczny jako ttyUSB

Jeżeli adapter nie pojawia się jako `can0`, ale jako port szeregowy, np.:

```text
/dev/ttyUSB0
/dev/ttyACM0
```

to są dwa możliwe przypadki.

Jeżeli adapter obsługuje SLCAN, można użyć `slcand`, aby utworzyć interfejs `can0`:

```bash
sudo slcand -o -c -s6 /dev/ttyUSB0 can0
sudo ip link set can0 up
```

Przykładowe prędkości dla `slcand`:

```text
-s4 = 125 kbit/s
-s5 = 250 kbit/s
-s6 = 500 kbit/s
-s8 = 1 Mbit/s
```

Jeżeli adapter nie obsługuje SLCAN, `slcand` nie pomoże. Wtedy potrzebny jest sterownik, SDK producenta, backend `python-can` dla danego adaptera albo osobna obsługa protokołu przez port szeregowy.

## Warunki sprzętowe

Przed testami sprawdź:

```text
CAN_H adaptera  -> CAN_H urządzenia
CAN_L adaptera  -> CAN_L urządzenia
GND adaptera    -> GND urządzenia, jeżeli wymagane
terminacja      -> 120 ohm na końcach magistrali
bitrate         -> taki sam w adapterze i urządzeniu
Node ID         -> zgodny z konfiguracją urządzenia
```

Jeżeli magistrala składa się tylko z adaptera USB-CAN i jednego urządzenia, zwykle potrzebna jest terminacja 120 ohm między CAN_H i CAN_L.

## Kiedy przejść dalej

Możesz przejść do kolejnego etapu, jeżeli:

- `python -c "import can, canopen; print('OK')"` działa,
- `ip -details link show can0` pokazuje aktywny interfejs,
- `candump can0` pokazuje heartbeat,
- widać node ID `2` i `3`,
- heartbeat ma wartość `0x7F` albo inną zrozumiałą wartość stanu NMT.

Następny krok:

[01. Ręczne testy CANopen](01-reczne-testy-canopen.md)
