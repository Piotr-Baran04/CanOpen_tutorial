# 02. Python bez EDS

Po ręcznych testach `cansend` można wykonać to samo z Pythona, nadal bez pliku EDS. Ten test używa tylko biblioteki `python-can` i surowych ramek SDO.

Uruchom:

```bash
source .venv/bin/activate
python src/test_sdo_raw.py
```

Domyślnie skrypt używa ustawień z `src/config.py`:

```text
interface = socketcan
channel   = can0
nodes     = 2, 3
```

Możesz też podać parametry ręcznie:

```bash
python src/test_sdo_raw.py --channel can0 --nodes 2 3 --timeout 1.0
```

Skrypt odczytuje:

```text
0x1000:00 = Device Type
0x1001:00 = Error Register
0x1018:01 = Vendor ID
0x1018:02 = Product Code
0x1018:03 = Revision Number
0x1018:04 = Serial Number
```

## Skąd są te indeksy

Indeksy typu `0x1000`, `0x1001` i `0x1018` nie są wymyślone w tym projekcie. To standardowe obiekty CANopen z Object Dictionary: https://en.wikipedia.org/wiki/CANopen

W CANopen urządzenie ma słownik obiektów, czyli tabelę parametrów. Każdy parametr ma adres:

```text
indeks:subindeks
```

Przykład:

```text
0x1018:01
```

oznacza:

```text
indeks    = 0x1018
subindeks = 0x01
```

W pierwszym teście bez EDS wybieramy obiekty, które są bardzo podstawowe i typowo dostępne w urządzeniach CANopen:

```text
0x1000:00 = Device Type
0x1001:00 = Error Register
0x1018:01 = Vendor ID
0x1018:02 = Product Code
0x1018:03 = Revision Number
0x1018:04 = Serial Number
```

Ich numery można znaleźć w:

- standardzie CANopen,
- dokumentacji urządzenia,
- pliku EDS,
- narzędziach producenta pokazujących Object Dictionary.

W tym projekcie potwierdzamy je też w pliku EDS sterownika MOONS:

```text
eds/CANOPEN-EDS-MBDV-Servo-DulAxes-V1.0.eds
```

Dlatego ten test robimy jeszcze "bez EDS", ale nie znaczy to, że indeksy biorą się znikąd. Po prostu wpisujemy ręcznie kilka znanych, standardowych adresów zamiast pozwolić bibliotece `canopen` wczytać je z pliku EDS.

Późniejsze indeksy napędowe, takie jak:

```text
0x6041:00 = Statusword
0x6064:00 = Actual Position
0x606C:00 = Actual Velocity
```

pochodzą z profilu napędowego CiA 402 oraz z EDS/dokumentacji konkretnego napędu.

To jest dobry test, bo potwierdza cztery rzeczy naraz:

- Python widzi `can0`,
- `python-can` działa,
- node 2 i node 3 odpowiadają na SDO,
- podstawowy CANopen działa bez użycia EDS.

## Co robi ten skrypt

Uruchamiany plik to:

```text
src/test_sdo_raw.py
```

Ten skrypt robi programowo to samo, co wcześniej robiliśmy ręcznie przez `cansend`: wysyła zapytanie SDO i czeka na odpowiedź SDO.

Najważniejsza różnica jest taka:

```text
cansend          = ręcznie wpisujesz całą ramkę
test_sdo_raw.py  = Python składa i wysyła ramkę za Ciebie
```

## Import konfiguracji

Na początku skrypt importuje ustawienia:

```python
from config import CAN_CHANNEL, CAN_INTERFACE, NODE_IDS
```

Te wartości pochodzą z `src/config.py`:

```text
CAN_INTERFACE = socketcan
CAN_CHANNEL   = can0
NODE_IDS      = 2, 3
```

Dzięki temu nie trzeba wpisywać w kilku plikach tego samego kanału CAN i tych samych node ID.

## Lista obiektów do odczytu

W kodzie jest lista:

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

Każdy wpis ma format:

```text
nazwa, indeks, subindeks
```

Przykład:

```text
"Vendor ID", 0x1018, 0x01
```

oznacza:

```text
odczytaj obiekt 0x1018:01
```

## Budowanie ramki SDO

Dla każdego obiektu skrypt wywołuje funkcję:

```python
read_sdo_expedited(bus, node_id, index, subindex, timeout)
```

Najpierw wylicza CAN ID:

```python
request_id = 0x600 + node_id
response_id = 0x580 + node_id
```

Dla node 3 daje to:

```text
request_id  = 0x603
response_id = 0x583
```

Potem składa dane zapytania:

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

`0x40` oznacza żądanie odczytu SDO.

Indeks jest dzielony na dwa bajty, bo w ramce SDO idzie little-endian. Dla `0x1018`:

```text
index & 0xFF        = 0x18
(index >> 8) & 0xFF = 0x10
```

Dlatego w ramce widzimy:

```text
18 10
```

a nie:

```text
10 18
```

## Wysłanie ramki

Skrypt wysyła ramkę przez `python-can`:

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

To odpowiada ręcznej komendzie typu:

```bash
cansend can0 603#4018100100000000
```

## Oczekiwanie na odpowiedź

Po wysłaniu zapytania skrypt czeka na ramkę odpowiedzi:

```python
message = bus.recv(timeout=remaining)
```

Potem odrzuca ramki, które nie pasują do oczekiwanej odpowiedzi:

```python
if message.arbitration_id != response_id:
    continue
```

Czyli jeśli pytamy node 3, skrypt ignoruje wszystko oprócz:

```text
0x583
```

Sprawdza też, czy odpowiedź dotyczy tego samego indeksu i subindeksu, o który pytaliśmy:

```python
if message.data[1] != request[1] or message.data[2] != request[2]:
    continue
if message.data[3] != request[3]:
    continue
```

To chroni przed pomyleniem odpowiedzi, gdy na magistrali dzieje się więcej rzeczy.

## SDO abort

Jeżeli odpowiedź zaczyna się od `0x80`, urządzenie zgłosiło błąd SDO:

```python
if command == 0x80:
    abort_code = int.from_bytes(message.data[4:8], byteorder="little")
    raise SdoAbortError(abort_code)
```

Wtedy skrypt wypisze coś w stylu:

```text
FAIL Vendor ID 0x1018:01 SDO abort 0x....
```

To oznacza, że urządzenie odpowiedziało, ale odmówiło dostępu albo nie rozpoznało obiektu.

## Odczyt wartości z odpowiedzi

Gdy odpowiedź jest poprawna, skrypt pobiera bajty danych:

```python
payload = bytes(message.data[4 : 4 + size])
value = int.from_bytes(payload, byteorder="little", signed=False)
```

Przykład:

```text
D9 02 00 00
```

zostaje zamienione na:

```text
0x000002D9
```

czyli `Vendor ID` dla tego urządzenia.

## Wynik na ekranie

Na końcu skrypt wypisuje wynik dla każdego node'a i każdego obiektu:

```text
Node 3
  OK   Vendor ID 0x1018:01              729 (0x000002D9, 4 B)
```

Oznacza to:

```text
OK          = odczyt się udał
Vendor ID  = nazwa testowanego obiektu
0x1018:01   = indeks i subindeks
729         = wartość dziesiętnie
0x000002D9  = ta sama wartość szesnastkowo
4 B         = urządzenie zwróciło 4 bajty danych
```

Jeżeli pojawia się `Brak odpowiedzi SDO`, sprawdź najpierw:

- czy `can0` jest `UP`,
- czy bitrate jest poprawny,
- czy `candump can0` nadal pokazuje heartbeat,
- czy node ID jest poprawny.

## Kiedy przejść dalej

Możesz przejść dalej, jeżeli skrypt pokazuje `OK` dla podstawowych obiektów SDO przynajmniej dla jednego node'a, a najlepiej dla node 2 i node 3.

Następny krok:

[03. Python z EDS](03-python-z-eds.md)
