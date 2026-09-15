# sygnatury — walidator formatu sygnatur polskich orzeczeń

Jeden plik, zero zależności, Python 3.9+. Licencja MIT.

Sprawdza, czy ciąg znaków ma budowę sygnatury akt polskiego sądu, rozpoznaje sąd (SN, powszechny, NSA, WSA, TK) i repertorium, normalizuje zapis i wyciąga sygnatury z dowolnego tekstu.

**Nie sprawdza, czy orzeczenie istnieje.** To robi zapytanie do rejestru (SAOS, CBOSA, OTK). Walidator jest sitem przed zapytaniem: odsiewa to, co sygnaturą być nie może, i ujednolica zapis, żeby zapytanie w ogóle trafiło.

```python
from sygnatury import waliduj, normalizuj, znajdz

waliduj("II CSK 331/12")
# Sygnatura(poprawna=True, sad='SN', wydzial='II', repertorium='CSK',
#           opis='SN, Izba Cywilna — skarga kasacyjna', numer=331, rok=2012,
#           znormalizowana='II CSK 331/12', uwagi=[])

normalizuj("ii  csk 331 / 12")      # 'II CSK 331/12'
normalizuj("art. 471 k.c.")         # None

znajdz("por. III CZP 61/03 oraz III SA/Wa 123/20")
# [Sygnatura(... 'III CZP 61/03' ...), Sygnatura(... 'III SA/Wa 123/20' ...)]
```

Z linii poleceń:

```
python sygnatury.py "I ACa 1102/20" "K 1/20"
```

## Co rozpoznaje

- Sąd Najwyższy: CSK, CSKP, CZP, CNP, KK, KZP, PK, PSKP, UK, USKP, NSNc, NSNk, WK i inne.
- Sądy powszechne: C, Ca, ACa, Cz, Co, Ns, Nc, K, Ka, AKa, Kz, W, P, Pa, U, Ua, GC, Ga, AGa, GNc, GU, GUp, GR, AmC, GW i inne.
- NSA: OSK, FSK, GSK, OZ, FZ, GZ, OPS, FPS, GPS, ONP, FNP, GNP.
- WSA: `SA/<kod miasta>` dla 16 sądów (Wa, Kr, Gl, Po, Wr, Gd, Łd, Lu, Bk, Bd, Go, Ke, Ol, Op, Rz, Sz).
- Trybunał Konstytucyjny: K, P, SK, U, Kp, Kpt, Pp, Tw, Ts, Tp, S.

Rok dwucyfrowy jest rozwijany: `12` → 2012, `95` → 1995 (granica: bieżący rok + 1).

## Czego nie robi

- Nie potwierdza istnienia orzeczenia ani sądu, który je wydał.
- Nie rozstrzyga, czy `K 1/20` to TK czy sąd karny bez podanego wydziału — zwraca TK z uwagą.
- Nie zna wszystkich repertoriów historycznych ani lokalnych oznaczeń; nieznane repertorium daje `poprawna=False` z uwagą. Zgłoś brak przez issue z przykładem.

## Testy

```
python -m pytest sygnatury/tests
```
