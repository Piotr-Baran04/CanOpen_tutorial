# Menu dokumentacji

To jest krótki spis lekcji w folderze `docs_PL/`. Głównym punktem startowym całego repo pozostaje [../README.md](../README.md).

Wersja angielska jest w [../docs_EN/MENU.md](../docs_EN/MENU.md).

## Etapy

1. [00. Przygotowanie środowiska](00-przygotowanie.md)
2. [01. Ręczne testy CANopen](01-reczne-testy-canopen.md)
3. [02. Python bez EDS](02-python-bez-eds.md)
4. [03. Python z EDS](03-python-z-eds.md)
5. [04. Heartbeat i NMT z Pythona](04-heartbeat-i-nmt-python.md)
6. [05. Statusword i stany CiA 402](05-statusword-cia402.md)
7. [06. Ruch strzałkami z klawiatury](06-ruch-strzalkami.md)

## Jak czytać

Każdy rozdział ma najpierw część praktyczną: co uruchomić i jaki wynik jest poprawny. Sekcje typu "Co robi ten skrypt" są po to, żeby zrozumieć mechanizm, ale przy pierwszym przejściu możesz czytać je spokojnie po wykonaniu testu.

## Logika przechodzenia

```text
Linux widzi can0
  -> candump widzi heartbeat
  -> ręczne SDO odpowiada
  -> Python potrafi wysłać SDO bez EDS
  -> Python potrafi czytać przez EDS
  -> rozumiemy Statusword
  -> dopiero wtedy próbujemy Controlword i bardzo mały ruch
```

Jeżeli coś przestaje działać, wróć o jeden etap niżej.
