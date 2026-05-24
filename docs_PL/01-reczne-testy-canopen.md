# 01. Ręczne testy CANopen

Ten etap robimy jeszcze bez Pythona. Dzięki temu widać dokładnie, jakie ramki CANopen są wysyłane i jakie odpowiedzi wracają z napędu.

Najwygodniej pracować na dwóch terminalach:

```text
Terminal 1 = cały czas uruchomiony candump can0
Terminal 2 = wpisywanie kolejnych komend cansend
```

## NMT a SDO

W tym etapie pojawiają się dwa różne mechanizmy CANopen:

```text
NMT = Network Management
SDO = Service Data Object
```

NMT służy do zarządzania stanem całego node'a CANopen. Przez NMT mówimy urządzeniu na przykład:

```text
przejdź do Operational
wróć do Pre-operational
zatrzymaj node
```

Komendy NMT nie odczytują parametrów napędu. One zmieniają stan komunikacyjny urządzenia w sieci CANopen.

SDO służy do czytania i zapisywania konkretnych obiektów z Object Dictionary urządzenia. Przez SDO pytamy na przykład:

```text
jaki jest Device Type 0x1000:00
jaki jest Vendor ID 0x1018:01
jaki jest Statusword 0x6041:00
```

Najkrócej:

```text
NMT = w jakim stanie ma być node
SDO = odczytaj albo zapisz konkretny parametr node'a
```

W tej lekcji używamy:

- NMT do przełączenia `Pre-operational` / `Operational`,
- SDO do ręcznego odczytu kilku podstawowych obiektów.

## Test NMT

NMT, czyli Network Management, zarządza stanem node'ów CANopen. Komendy NMT są wysyłane na CAN ID:

```text
0x000
```

Format danych:

```text
[komenda] [node_id]
```

Najważniejsze komendy na ten etap:

```text
0x01 = Start Remote Node
0x80 = Enter Pre-operational
```

Nie używamy jeszcze resetów `0x81` ani `0x82`.

W jednym terminalu zostaw:

```bash
candump can0
```

W drugim terminalu wpisuj kolejne komendy `cansend`.

Node 2 do `Operational`:

```bash
cansend can0 000#0102
```

Oczekiwany heartbeat:

```text
702#05
```

Node 2 z powrotem do `Pre-operational`:

```bash
cansend can0 000#8002
```

Oczekiwany heartbeat:

```text
702#7F
```

Dla node 3:

```bash
cansend can0 000#0103
cansend can0 000#8003
```

Oczekiwane heartbeaty:

```text
703#05
703#7F
```

## Test SDO: Device Type

SDO request dla node 2:

```text
0x600 + 2 = 0x602
```

SDO response dla node 2:

```text
0x580 + 2 = 0x582
```

Odczyt `0x1000:00`, czyli `Device Type`, z node 2:

```bash
cansend can0 602#4000100000000000
```

Przykładowa poprawna odpowiedź:

```text
582   [8]  43 00 10 00 XX XX XX XX
```

Dla node 3:

```bash
cansend can0 603#4000100000000000
```

Odpowiedź powinna przyjść na `0x583`.

## Test SDO: Identity Object

Identity Object to `0x1018`.

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

## Jak czytać odpowiedzi SDO

Poprawne odpowiedzi expedited upload:

```text
0x43 = odpowiedź z 4 bajtami danych
0x4B = odpowiedź z 2 bajtami danych
0x4F = odpowiedź z 1 bajtem danych
```

Przykład z odczytu `0x1018:01`, czyli `Vendor ID`, z node 3:

```text
can0  603   [8]  40 18 10 01 00 00 00 00
can0  583   [8]  43 18 10 01 D9 02 00 00
```

Pierwsza ramka to zapytanie:

```text
603       = SDO request do node 3, bo 0x600 + 3
40        = żądanie odczytu SDO
18 10     = indeks 0x1018 zapisany little-endian
01        = subindeks 1
00...     = puste bajty danych
```

Czyli pytanie brzmi:

```text
odczytaj 0x1018:01 z node 3
```

Obiekt `0x1018:01` to `Vendor ID`.

Druga ramka to odpowiedź:

```text
583          = SDO response z node 3, bo 0x580 + 3
43           = odpowiedź expedited z 4 bajtami danych
18 10 01     = potwierdzenie obiektu 0x1018:01
D9 02 00 00  = wartość danych
```

Dane w CANopen SDO są zapisane little-endian. Dlatego:

```text
D9 02 00 00 = 0x000002D9
```

Odpowiedź oznacza więc:

```text
Vendor ID = 0x000002D9
```

Jeżeli ta wartość zgadza się z EDS, to jest bardzo dobry znak:

```text
node ID jest poprawny
SDO działa
urządzenie odpowiada zgodnie ze słownikiem obiektów
```

Jeżeli odpowiedź zaczyna się od `0x80`, to jest to `SDO abort`.

Najczęstsze przyczyny:

- zły node ID,
- obiekt lub subindeks nie istnieje,
- obiekt nie jest czytelny,
- urządzenie nie pozwala na dostęp w aktualnym stanie,
- mapa obiektów różni się od oczekiwanej.

## Read-only obiekty napędu

Po `0x1000` i `0x1018` można bezpiecznie spróbować odczytów diagnostycznych:

```bash
cansend can0 602#4001100000000000   # 0x1001:00 Error Register
cansend can0 602#403F600000000000   # 0x603F:00 Error Code
cansend can0 602#4041600000000000   # 0x6041:00 Statusword
cansend can0 602#4061600000000000   # 0x6061:00 Mode Display
cansend can0 602#4064600000000000   # 0x6064:00 Actual Position
cansend can0 602#406C600000000000   # 0x606C:00 Actual Velocity
cansend can0 602#4002650000000000   # 0x6502:00 Supported Drive Modes
```

Dla node 3 zmień `602` na `603`.

## Kiedy przejść dalej

Możesz przejść dalej, jeżeli:

- NMT zmienia heartbeat między `0x7F` i `0x05`,
- node 2 odpowiada na SDO,
- node 3 odpowiada na SDO,
- odczyt `0x1018:01` zwraca sensowny `Vendor ID`.

Następny krok:

[02. Python bez EDS](02-python-bez-eds.md)
