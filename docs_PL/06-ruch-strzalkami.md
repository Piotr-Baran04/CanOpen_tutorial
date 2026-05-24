# 06. Ruch strzałkami z klawiatury

To jest pierwszy etap, który może realnie poruszyć silnikami. Wykonuj go dopiero po przejściu poprzednich rozdziałów i po upewnieniu się, że stanowisko jest bezpieczne.

Na tym etapie zakładamy:

```text
node 2 = lewa oś
node 3 = prawa oś
```

Sterowanie:

```text
strzałka góra  albo W = oba silniki do przodu
strzałka dół   albo S = oba silniki do tyłu
strzałka lewo  albo A = skręt w lewo
strzałka prawo albo D = skręt w prawo
spacja                 = stop
q                      = wyjście
```

Jeżeli fizycznie kierunki są odwrotne, przerwij test i użyj opcji `--invert-node`. Nie próbuj tego "naprawiać" większą prędkością.

## Warunki przed startem

Przed tym testem sprawdź:

- mechanika może się bezpiecznie poruszyć,
- osie nie są przy krańcówkach,
- masz dostęp do awaryjnego zatrzymania zasilania,
- [03. Python z EDS](03-python-z-eds.md) działa poprawnie,
- `Error register 0x1001:00` ma wartość `0`,
- `Error code 0x603F:00` ma wartość `0`,
- rozumiesz, że ten skrypt będzie zapisywał do obiektów sterujących napędu.

## Test klawiatury

Najpierw sprawdź, czy terminal poprawnie rozpoznaje klawisze:

```bash
source .venv/bin/activate
python src/keyboard_jog.py --key-debug
```

Ten tryb nie łączy się z CAN i nie uruchamia napędu. Naciskaj strzałki oraz `W`, `A`, `S`, `D`.

Oczekiwane wyniki:

```text
strzałka góra albo W  -> key: 'UP'
strzałka dół albo S   -> key: 'DOWN'
strzałka lewo albo A  -> key: 'LEFT'
strzałka prawo albo D -> key: 'RIGHT'
spacja                -> key: 'SPACE'
q                     -> key: 'QUIT'
```

Jeżeli strzałki nie działają, ale `WASD` działa, używaj `WASD`. Niektóre terminale wysyłają strzałki inaczej.

## Pierwsze uruchomienie ruchu

Skrypt wymaga świadomego parametru `--enable`. Bez niego odmówi pracy.

Pierwszy test wykonaj małą prędkością:

```bash
python src/keyboard_jog.py --enable --speed-rad-s 0.5
```

Trzymaj krótko strzałkę albo klawisz `W`, `A`, `S`, `D`. Po puszczeniu klawisza skrypt sam wyśle prędkość `0`, jeżeli przez chwilę nie dostanie kolejnego sygnału z klawiatury.

Jeżeli wszystko działa i stanowisko jest bezpieczne, możesz spróbować:

```bash
python src/keyboard_jog.py --enable --speed-rad-s 1.0
```

Opcja `--speed-rad-s` oznacza prędkość wyjścia przekładni w radianach na sekundę. To jest wygodniejsze niż wpisywanie surowych jednostek napędu.

## Gdy kierunek osi jest odwrotny

Jeżeli node 2 kręci się w złą stronę:

```bash
python src/keyboard_jog.py --enable --speed-rad-s 0.5 --invert-node 2
```

Jeżeli node 3 kręci się w złą stronę:

```bash
python src/keyboard_jog.py --enable --speed-rad-s 0.5 --invert-node 3
```

Jeżeli oba są odwrotnie:

```bash
python src/keyboard_jog.py --enable --speed-rad-s 0.5 --invert-node 2 3
```

Jeżeli lewa i prawa oś są zamienione miejscami, możesz zmienić kolejność node'ów:

```bash
python src/keyboard_jog.py --enable --speed-rad-s 0.5 --nodes 3 2
```

## Skala prędkości

W napędzie obiekt:

```text
0x60FF:00 = Target Velocity
```

nie przechowuje bezpośrednio wartości w `rad/s`. Napęd używa swojej wewnętrznej jednostki, zależnej od enkodera i przekładni.

Dla tego stanowiska outdoor przyjmujemy:

```text
P3-05 = 10000 impulsów na obrót
gearbox_ratio = 30
```

Dlatego:

```text
1.0 rad/s na wyjściu przekładni ~= 47746 jednostek napędu
```

Skala jest zapisana w `src/config.py`:

```text
node 2: -47746.4829276
node 3:  47746.4829276
```

Minus przy node 2 wynika z kierunku montażu osi. Dzięki temu komenda "do przodu" może oznaczać fizycznie ten sam kierunek ruchu robota dla obu stron.

## Co robi ten skrypt

Uruchamiany plik to:

```text
src/keyboard_jog.py
```

Skrypt robi dwie różne rzeczy:

```text
1. Konfiguruje napęd przez SDO.
2. Wysyła zadaną prędkość przez RPDO.
```

### SDO

SDO, czyli **Service Data Object**, działa jak pojedyncze pytanie albo polecenie do konkretnego obiektu w słowniku urządzenia.

Przykłady:

```text
odczytaj Statusword 0x6041:00
ustaw Modes of Operation 0x6060:00
ustaw Profile Acceleration 0x6083:00
```

SDO jest wygodne do konfiguracji i diagnostyki, bo dokładnie wskazujemy:

```text
node ID
indeks
subindeks
wartość
```

W tym skrypcie SDO jest używane na początku, żeby przygotować napęd do pracy w trybie prędkości.

### RPDO

PDO, czyli **Process Data Object**, służy do szybkiej wymiany danych procesowych, na przykład aktualnej pozycji albo prędkości zadanej.

RPDO oznacza **Receive PDO** z punktu widzenia napędu:

```text
komputer wysyła ramkę
napęd ją odbiera
```

W czasie jazdy skrypt wysyła prędkość przez RPDO:

```text
0x402 = RPDO node 2
0x403 = RPDO node 3
```

Każda taka ramka zawiera:

```text
Controlword 0x6040:00
Target Velocity 0x60FF:00
```

Najprościej:

```text
SDO  = spokojna konfiguracja i odczyty
RPDO = szybkie wysyłanie prędkości podczas ruchu
```

## Przejście przez CiA 402

Do jazdy strzałkami używamy trybu:

```text
0x6060:00 = Modes of Operation
wartość 3 = Profile Velocity Mode
```

Przed ruchem skrypt przechodzi przez standardową sekwencję `Controlword`:

```text
0x0006 = Shutdown
0x0007 = Switch on
0x000F = Enable operation
```

Po każdym kroku sprawdza:

```text
0x6041:00 = Statusword
```

Chodzi o to, żeby nie zakładać na ślepo, że napęd przyjął komendę. Skrypt czeka, aż napęd potwierdzi właściwy stan.

## Jak skrypt zamienia klawisze na ruch

Klawisz jest najpierw zamieniany na komendę:

```text
UP    -> forward
DOWN  -> backward
LEFT  -> left
RIGHT -> right
SPACE -> stop
```

Potem komenda jest zamieniana na dwie prędkości:

```text
forward  = +speed, +speed
backward = -speed, -speed
left     = -speed, +speed
right    = +speed, -speed
stop     = 0, 0
```

Na końcu te wartości są przeliczane z `rad/s` na jednostki napędu i wysyłane do node 2 oraz node 3.

## Zatrzymanie i wyjście

W czasie pracy:

```text
spacja = stop
q      = wyjście
Ctrl+C = przerwanie programu
```

Przy wyjściu skrypt zawsze próbuje:

```text
0x60FF:00 = 0
0x6040:00 = 0x0000
```

czyli najpierw zadaje prędkość `0`, a potem wysyła `Disable voltage`.

## Opcjonalna diagnostyka

Jeżeli silniki nadal nie obracają się mimo poprawnego przejścia do `Operation enabled`, możesz uruchomić podgląd:

```bash
python src/keyboard_jog.py --enable --speed-rad-s 0.5 --telemetry
```

Ta opcja wypisuje między innymi:

```text
Target Velocity
Actual Velocity
Mode Display
Error Register / Error Code
Statusword
```

Na pierwsze czytanie tutoriala nie musisz analizować tych pól. To jest pomoc diagnostyczna, gdy coś nie działa.

Możesz też obserwować ramki PDO w osobnym terminalu:

```bash
candump can0,282:7FF,283:7FF,402:7FF,403:7FF,482:7FF,483:7FF
```

Typowe ID dla tego stanowiska:

```text
0x402 = RPDO do node 2
0x403 = RPDO do node 3
0x282 = TPDO z node 2
0x283 = TPDO z node 3
0x482 = TPDO z node 2
0x483 = TPDO z node 3
```

TPDO oznacza **Transmit PDO** z punktu widzenia napędu:

```text
napęd wysyła ramkę
komputer ją odbiera
```

## Kiedy etap jest zakończony

Ten etap jest zakończony, gdy:

- potrafisz uruchomić skrypt z `--enable`,
- napęd przechodzi do `Operation enabled`,
- `W/S/A/D` albo strzałki powodują przewidywalny ruch,
- spacja zatrzymuje ruch,
- `q` albo `Ctrl+C` zatrzymuje osie i kończy program.

## Koniec

Wróć do menu:

[MENU.md](MENU.md)
