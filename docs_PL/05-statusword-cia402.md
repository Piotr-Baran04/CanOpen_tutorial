# 05. Statusword i stany CiA 402

Po potwierdzeniu komunikacji CANopen najważniejszym obiektem napędu jest:

```text
0x6041:00 = Statusword
```

To jest słowo statusowe CiA 402. Mówi, w jakim stanie jest napęd i czy można przechodzić dalej przez maszynę stanów.

Na tym etapie tylko odczytujemy `Statusword`. Nie zapisujemy jeszcze `Controlword`.

## Odczyt ręczny

Dla node 2:

```bash
cansend can0 602#4041600000000000
```

Odpowiedź przychodzi na `0x582`.

Dla node 3:

```bash
cansend can0 603#4041600000000000
```

Odpowiedź przychodzi na `0x583`.

## Odczyt przez skrypt z EDS

```bash
source .venv/bin/activate
python src/test_canopen_eds.py
```

Skrypt odczytuje między innymi:

```text
0x603F:00 = Error Code
0x6041:00 = Statusword
0x6061:00 = Modes of Operation Display
0x6064:00 = Actual Position
0x606C:00 = Actual Velocity
```

## Co robi kod dekodujący Statusword

Za czytelny opis `Statusword` odpowiada plik:

```text
src/cia402.py
```

Jest on używany przez:

```text
src/test_canopen_eds.py
```

Gdy `test_canopen_eds.py` odczyta obiekt `0x6041`, wywołuje:

```python
format_statusword(value)
```

## Lista bitów

W `src/cia402.py` znajduje się lista bitów:

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

Każdy wpis oznacza:

```text
numer bitu, opis bitu
```

Funkcja:

```python
decode_statusword_bits(value)
```

sprawdza, które bity są ustawione:

```python
bool(value & (1 << bit))
```

Przykład dla bitu 3:

```text
bit 3 = fault
1 << 3 = 0x0008
```

Jeżeli:

```text
Statusword & 0x0008 != 0
```

to bit `fault` jest aktywny.

## Rozpoznawanie stanu CiA 402

Samo sprawdzenie pojedynczych bitów nie wystarcza, bo stan CiA 402 jest kombinacją kilku bitów. Dlatego funkcja:

```python
statusword_state(value)
```

używa masek bitowych.

Przykład:

```python
if (value & 0x004F) == 0x0040:
    return "Switch on disabled"
```

Oznacza to:

```text
weź tylko bity istotne dla tej decyzji
porównaj je ze wzorcem stanu Switch on disabled
```

Inny przykład:

```python
if (value & 0x006F) == 0x0027:
    return "Operation enabled"
```

Jeżeli `Statusword` spełnia ten wzorzec, napęd jest w stanie:

```text
Operation enabled
```

To nadal nie znaczy, że skrypt nakazuje ruch. To tylko opis aktualnego stanu odczytanego z napędu.

## Format wyniku

Funkcja:

```python
format_statusword(value)
```

łączy dwie informacje:

```text
stan CiA 402
lista aktywnych bitów
```

Przykładowy wynik:

```text
0x0040 - Switch on disabled (switch_on_disabled)
```

Oznacza to:

```text
0x0040              = surowa wartość Statusword
Switch on disabled = rozpoznany stan CiA 402
switch_on_disabled = aktywny bit statusowy
```

## Najważniejsze bity Statusword

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

Typowe stany CiA 402:

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

## Co sprawdzić przed jakimkolwiek ruchem

Najpierw trzeba znać odpowiedzi na pytania:

- czy `0x1001 Error Register` zgłasza błąd,
- czy `0x603F Error Code` jest zerowy,
- czy `0x6041 Statusword` pokazuje `Fault`,
- czy `0x6061 Mode Display` zgadza się z oczekiwanym trybem,
- czy aktualna pozycja `0x6064` zmienia się sensownie po ręcznym poruszeniu osią,
- czy aktualna prędkość `0x606C` wraca do zera, gdy oś stoi.

## Dopiero później Controlword

Obiekt:

```text
0x6040:00 = Controlword
```

jest zapisem sterującym maszyną stanów napędu. Typowa sekwencja CiA 402 wygląda tak:

```text
0x0006 = Shutdown
0x0007 = Switch on
0x000F = Enable operation
```

Tego nie robimy jeszcze w pierwszych testach. Najpierw trzeba mieć pewność, że odczyty statusu i błędów są zrozumiałe.

## Dobra granica etapu

Ten etap jest zakończony, gdy potrafisz powiedzieć dla każdego node'a:

```text
node ID
NMT state z heartbeat
Error Register
Error Code
Statusword
stan CiA 402
Mode Display
Actual Position
Actual Velocity
```

## Kiedy przejść dalej

Możesz przejść dalej, jeżeli rozumiesz `Statusword`, nie ma aktywnych błędów i stanowisko jest przygotowane do realnego ruchu.

Następny krok:

[06. Ruch strzałkami z klawiatury](06-ruch-strzalkami.md)
