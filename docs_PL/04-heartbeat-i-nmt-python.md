# 04. Heartbeat i NMT z Pythona

Po ręcznych testach przez `candump` i `cansend` można zrobić ten sam etap wygodniej z Pythona. Nadal nie uruchamiamy ruchu napędu.

## Monitor heartbeat

Heartbeat to cykliczna ramka:

```text
0x700 + node_id
```

Dla node 2 i 3:

```text
0x702
0x703
```

Uruchom monitor:

```bash
source .venv/bin/activate
python src/monitor_heartbeat.py
```

Przykładowy wynik:

```text
node   2: heartbeat 0x7F (Pre-operational)
node   3: heartbeat 0x7F (Pre-operational)
```

Możesz słuchać dłużej:

```bash
python src/monitor_heartbeat.py --duration 30
```

Albo pokazać heartbeat ze wszystkich node'ów:

```bash
python src/monitor_heartbeat.py --all
```

## Co robi monitor heartbeat

Uruchamiany plik to:

```text
src/monitor_heartbeat.py
```

Skrypt używa biblioteki `python-can`, czyli pracuje na surowych ramkach CAN.

Najpierw otwiera magistralę:

```python
with can.Bus(interface=args.interface, channel=args.channel) as bus:
```

Dla naszej konfiguracji oznacza to:

```text
interface = socketcan
channel   = can0
```

Potem cały czas odbiera ramki:

```python
message = bus.recv(timeout=timeout)
```

Interesują go tylko ramki heartbeat, czyli CAN ID od:

```text
0x700 do 0x77F
```

W kodzie wygląda to tak:

```python
if arbitration_id < 0x700 or arbitration_id > 0x77F:
    continue
```

Node ID jest wyliczany z CAN ID:

```python
node_id = arbitration_id - 0x700
```

Przykład:

```text
0x703 - 0x700 = 3
```

czyli ramka `0x703` jest heartbeatem node 3.

Pierwszy bajt danych to stan NMT:

```python
state = message.data[0]
```

Skrypt tłumaczy go przez słownik:

```python
HEARTBEAT_STATES = {
    0x00: "Boot-up",
    0x04: "Stopped",
    0x05: "Operational",
    0x7F: "Pre-operational",
}
```

Dlatego wynik:

```text
node   3: heartbeat 0x7F (Pre-operational)
```

oznacza:

```text
CAN ID 0x703
node ID 3
stan NMT 0x7F
opis stanu Pre-operational
```

## Komendy NMT

NMT wysyła się na CAN ID:

```text
0x000
```

Skrypt `src/nmt_command.py` obsługuje tylko trzy podstawowe komendy:

```text
start = 0x01
stop  = 0x02
preop = 0x80
```

Celowo nie ma tu resetów `0x81` i `0x82`, bo na początku łatwiej diagnozować układ bez restartowania urządzeń.

## Co robi skrypt NMT

Uruchamiany plik to:

```text
src/nmt_command.py
```

Skrypt zamienia nazwę komendy na bajt NMT:

```python
NMT_COMMANDS = {
    "start": 0x01,
    "stop": 0x02,
    "preop": 0x80,
}
```

Gdy wpisujesz:

```bash
python src/nmt_command.py start 2
```

skrypt buduje ramkę:

```python
can.Message(
    arbitration_id=0x000,
    data=[0x01, 0x02],
    is_extended_id=False,
)
```

To odpowiada ręcznej komendzie:

```bash
cansend can0 000#0102
```

Znaczenie danych:

```text
0x01 = Start Remote Node
0x02 = node ID 2
```

Po wysłaniu komendy skrypt czeka na heartbeat tego node'a:

```python
response_id = 0x700 + node_id
```

Dla node 2:

```text
0x700 + 2 = 0x702
```

Jeżeli przyjdzie heartbeat:

```text
0x05
```

skrypt wypisze:

```text
Heartbeat node 2: 0x05 (Operational)
```

Jeżeli użyjesz node ID `0`, to jest broadcast. Wtedy skrypt wysyła komendę do wszystkich node'ów, ale nie czeka na jeden konkretny heartbeat.

## Node 2

Przejście do `Operational`:

```bash
python src/nmt_command.py start 2
```

Oczekiwany heartbeat:

```text
0x05 (Operational)
```

Powrót do `Pre-operational`:

```bash
python src/nmt_command.py preop 2
```

Oczekiwany heartbeat:

```text
0x7F (Pre-operational)
```

## Node 3

```bash
python src/nmt_command.py start 3
python src/nmt_command.py preop 3
```

## Broadcast

Node ID `0` oznacza broadcast:

```bash
python src/nmt_command.py start 0
python src/nmt_command.py preop 0
```

Na początku lepiej testować node'y osobno. Broadcast jest wygodny dopiero wtedy, gdy wiadomo, które urządzenia są na magistrali.

## Bezpieczeństwo

NMT `Operational` nie jest tym samym co `Enable Operation` w CiA 402. Samo NMT nie powinno jeszcze uruchamiać ruchu, ale może aktywować normalną komunikację PDO urządzenia.

Dlatego po teście warto wrócić do:

```bash
python src/nmt_command.py preop 2
python src/nmt_command.py preop 3
```

## Kiedy przejść dalej

Możesz przejść dalej, jeżeli monitor heartbeat pokazuje stany node'ów, a skrypt NMT potrafi przełączyć node 2 i node 3 do `Operational` oraz z powrotem do `Pre-operational`.

Następny krok:

[05. Statusword i stany CiA 402](05-statusword-cia402.md)
