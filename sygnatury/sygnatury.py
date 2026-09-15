"""
sygnatury — walidator formatu sygnatur polskich orzeczeń.

Sprawdza, czy ciąg znaków ma budowę sygnatury akt sądu polskiego, rozpoznaje
rodzaj sądu i repertorium, normalizuje zapis. NIE sprawdza, czy orzeczenie
istnieje — to robi zapytanie do rejestru (SAOS, orzeczenia NSA, OTK), nie ten
plik. Walidator odsiewa to, co nie może być sygnaturą, zanim zapyta się
rejestr, i ujednolica zapis, żeby zapytanie w ogóle trafiło.

Budowa sygnatury sądu powszechnego, SN i sądów wojskowych:
    [wydział rzymski] [repertorium] [numer]/[rok]
    np. II CSK 331/12, I ACa 1102/20, III CZP 61/03, VI GC 665/26

Sądy administracyjne:
    NSA:  [wydział rzymski] [repertorium] [numer]/[rok]   np. II FSK 1/20
    WSA:  [wydział rzymski] SA/[kod miasta] [numer]/[rok]  np. III SA/Wa 123/20

Trybunał Konstytucyjny:
    [repertorium] [numer]/[rok]   np. K 1/20, SK 7/06, P 10/07, Kp 3/09

Licencja: MIT. Bez gwarancji. Zgłoszenia: issue w repozytorium.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Optional

__all__ = ["Sygnatura", "waliduj", "normalizuj", "znajdz"]

# --- repertoria -------------------------------------------------------------

# Sąd Najwyższy
_SN = {
    "CSK": "SN, Izba Cywilna — skarga kasacyjna",
    "CSKP": "SN, Izba Cywilna — skarga kasacyjna (po 2020)",
    "CZP": "SN, Izba Cywilna — zagadnienie prawne (uchwała)",
    "CNP": "SN, Izba Cywilna — skarga o stwierdzenie niezgodności z prawem",
    "CZ": "SN, Izba Cywilna — zażalenie",
    "CO": "SN, Izba Cywilna — inne",
    "KK": "SN, Izba Karna — kasacja",
    "KZP": "SN, Izba Karna — zagadnienie prawne (uchwała)",
    "KZ": "SN, Izba Karna — zażalenie",
    "KO": "SN, Izba Karna — inne",
    "KS": "SN, Izba Karna — skarga na wyrok sądu odwoławczego",
    "PK": "SN, Izba Pracy — skarga kasacyjna",
    "PSK": "SN, Izba Pracy — skarga kasacyjna",
    "PSKP": "SN, Izba Pracy — skarga kasacyjna (po 2020)",
    "PZP": "SN, Izba Pracy — zagadnienie prawne (uchwała)",
    "UK": "SN, Izba Pracy i Ubezpieczeń — skarga kasacyjna (ubezpieczenia)",
    "USK": "SN, Izba Pracy i Ubezpieczeń — skarga kasacyjna (ubezpieczenia)",
    "USKP": "SN, Izba Pracy i Ubezpieczeń — skarga kasacyjna (po 2020)",
    "UZP": "SN, Izba Pracy i Ubezpieczeń — zagadnienie prawne",
    "BP": "SN, Izba Pracy — skarga o stwierdzenie niezgodności z prawem",
    "BU": "SN, Izba Ubezpieczeń — skarga o stwierdzenie niezgodności z prawem",
    "NSNc": "SN, Izba Kontroli Nadzwyczajnej — skarga nadzwyczajna (cywilna)",
    "NSNk": "SN, Izba Kontroli Nadzwyczajnej — skarga nadzwyczajna (karna)",
    "NSNP": "SN, Izba Kontroli Nadzwyczajnej — skarga nadzwyczajna",
    "NSW": "SN, Izba Kontroli Nadzwyczajnej — protest wyborczy",
    "SNO": "SN, Izba Dyscyplinarna / Odpowiedzialności Zawodowej",
    "DSK": "SN — sprawy dyscyplinarne",
    "WK": "SN, Izba Wojskowa — kasacja",
    "WZ": "SN, Izba Wojskowa — zażalenie",
    "WA": "SN, Izba Wojskowa — apelacja",
}

# Sądy powszechne (rejonowe, okręgowe, apelacyjne)
_POWSZECHNE = {
    "C": "cywilne, I instancja",
    "Ca": "cywilne, apelacja (sąd okręgowy)",
    "ACa": "cywilne, apelacja (sąd apelacyjny)",
    "Cz": "cywilne, zażalenie",
    "ACz": "cywilne, zażalenie (sąd apelacyjny)",
    "Co": "cywilne, inne (np. zabezpieczenie, egzekucja)",
    "Cps": "cywilne, pomoc sądowa",
    "Ns": "cywilne, nieprocesowe",
    "Nc": "cywilne, nakazowe / upominawcze",
    "Nsm": "rodzinne i nieletnich, nieprocesowe",
    "RC": "rodzinne, procesowe",
    "RCo": "rodzinne, inne",
    "Now": "nieletni, opiekuńczo-wychowawcze",
    "Nkd": "nieletni, demoralizacja / czyny karalne",
    "K": "karne, I instancja",
    "Ka": "karne, apelacja (sąd okręgowy)",
    "AKa": "karne, apelacja (sąd apelacyjny)",
    "Kz": "karne, zażalenie",
    "AKz": "karne, zażalenie (sąd apelacyjny)",
    "Kp": "karne, postępowanie przygotowawcze",
    "Ko": "karne, inne",
    "Kop": "karne, pomoc prawna międzynarodowa",
    "Kow": "karne, wykonawcze",
    "AKo": "karne, inne (sąd apelacyjny)",
    "AKzw": "karne wykonawcze, zażalenie (sąd apelacyjny)",
    "W": "wykroczenia",
    "Ws": "wykroczenia, inne",
    "Waz": "wykroczenia, zażalenie",
    "P": "pracy, I instancja",
    "Pa": "pracy, apelacja",
    "Pz": "pracy, zażalenie",
    "Po": "pracy, inne",
    "Np": "pracy, nakazowe",
    "APa": "pracy, apelacja (sąd apelacyjny)",
    "APz": "pracy, zażalenie (sąd apelacyjny)",
    "U": "ubezpieczeń społecznych, I instancja",
    "Ua": "ubezpieczeń społecznych, apelacja",
    "Uz": "ubezpieczeń społecznych, zażalenie",
    "AUa": "ubezpieczeń społecznych, apelacja (sąd apelacyjny)",
    "AUz": "ubezpieczeń społecznych, zażalenie (sąd apelacyjny)",
    "GC": "gospodarcze, I instancja",
    "Ga": "gospodarcze, apelacja",
    "AGa": "gospodarcze, apelacja (sąd apelacyjny)",
    "Gz": "gospodarcze, zażalenie",
    "AGz": "gospodarcze, zażalenie (sąd apelacyjny)",
    "GNc": "gospodarcze, nakazowe / upominawcze",
    "GCo": "gospodarcze, inne",
    "GU": "gospodarcze, upadłościowe",
    "GUp": "gospodarcze, upadłość — postępowanie właściwe",
    "GUo": "gospodarcze, upadłość — inne",
    "GR": "gospodarcze, restrukturyzacyjne",
    "GRp": "gospodarcze, restrukturyzacja — postępowanie właściwe",
    "GRz": "gospodarcze, restrukturyzacja — zażalenie",
    "Gzd": "gospodarcze, zakaz prowadzenia działalności",
    "Ns-Rej": "rejestrowe",
    "KRS": "rejestrowe (KRS)",
    "AmC": "ochrona konkurencji i konsumentów (SOKiK), klauzule",
    "AmA": "ochrona konkurencji (SOKiK)",
    "AmE": "regulacja energetyki (SOKiK)",
    "AmT": "regulacja telekomunikacji (SOKiK)",
    "AmK": "regulacja kolejowa (SOKiK)",
    "AmW": "SOKiK, inne",
    "S": "skarga na przewlekłość",
    "Wp": "własność przemysłowa (Sąd Okręgowy w Warszawie, XXII Wydział)",
    "GW": "własność intelektualna (od 2020)",
    "GWo": "własność intelektualna, inne",
    "GWz": "własność intelektualna, zażalenie",
    "AGW": "własność intelektualna, apelacja",
}

# Sądownictwo administracyjne
_NSA = {
    "OSK": "NSA — skarga kasacyjna, Izba Ogólnoadministracyjna",
    "FSK": "NSA — skarga kasacyjna, Izba Finansowa",
    "GSK": "NSA — skarga kasacyjna, Izba Gospodarcza",
    "OZ": "NSA — zażalenie, Izba Ogólnoadministracyjna",
    "FZ": "NSA — zażalenie, Izba Finansowa",
    "GZ": "NSA — zażalenie, Izba Gospodarcza",
    "OPS": "NSA — uchwała, Izba Ogólnoadministracyjna",
    "FPS": "NSA — uchwała, Izba Finansowa",
    "GPS": "NSA — uchwała, Izba Gospodarcza",
    "OW": "NSA — spór kompetencyjny",
    "ONP": "NSA — niezgodność z prawem (Izba Ogólnoadministracyjna)",
    "FNP": "NSA — niezgodność z prawem (Izba Finansowa)",
    "GNP": "NSA — niezgodność z prawem (Izba Gospodarcza)",
    "OPP": "NSA — przewlekłość (Izba Ogólnoadministracyjna)",
    "FPP": "NSA — przewlekłość (Izba Finansowa)",
    "GPP": "NSA — przewlekłość (Izba Gospodarcza)",
    "OSA": "NSA — skarga administracyjna (dawne)",
    "SA": "NSA / ośrodek zamiejscowy — skarga (dawne)",
}

# Kody miast WSA (po "SA/")
_WSA = {
    "Wa": "WSA w Warszawie", "Kr": "WSA w Krakowie", "Gl": "WSA w Gliwicach",
    "Po": "WSA w Poznaniu", "Wr": "WSA we Wrocławiu", "Gd": "WSA w Gdańsku",
    "Łd": "WSA w Łodzi", "Ld": "WSA w Łodzi", "Lu": "WSA w Lublinie",
    "Bk": "WSA w Białymstoku", "Bd": "WSA w Bydgoszczy", "Go": "WSA w Gorzowie Wlkp.",
    "Ke": "WSA w Kielcach", "Ol": "WSA w Olsztynie", "Op": "WSA w Opolu",
    "Rz": "WSA w Rzeszowie", "Sz": "WSA w Szczecinie",
}

# Trybunał Konstytucyjny
_TK = {
    "K": "TK — wniosek o kontrolę konstytucyjności (abstrakcyjny)",
    "P": "TK — pytanie prawne sądu",
    "SK": "TK — skarga konstytucyjna",
    "U": "TK — kontrola aktu podustawowego",
    "Kp": "TK — kontrola prewencyjna (wniosek Prezydenta)",
    "Kpt": "TK — spór kompetencyjny",
    "Pp": "TK — cele lub działalność partii politycznej",
    "Tw": "TK — wstępne rozpoznanie wniosku",
    "Ts": "TK — wstępne rozpoznanie skargi konstytucyjnej",
    "Tp": "TK — wstępne rozpoznanie pytania prawnego",
    "S": "TK — postanowienie sygnalizacyjne",
    "M": "TK — inne",
}

_ROMAN = re.compile(r"^(?=[IVXL])(L?X{0,3})(IX|IV|V?I{0,3})$")

_RE_ZWYKLA = re.compile(
    r"^(?P<wydzial>[IVXLivxl]{1,5})?\s*"
    r"(?P<rep>[A-Za-z][A-Za-z\-]{0,4})\s+"
    r"(?P<numer>\d{1,6})\s*/\s*(?P<rok>\d{2}|\d{4})$"
)
_RE_WSA = re.compile(
    r"^(?P<wydzial>[IVXLivxl]{1,5})?\s*SA/(?P<miasto>[A-ZŁ][a-zł])\s+"
    r"(?P<numer>\d{1,6})\s*/\s*(?P<rok>\d{2}|\d{4})$"
)
_RE_TK = re.compile(
    r"^(?P<rep>K|P|SK|U|Kp|Kpt|Pp|Tw|Ts|Tp|S|M)\s+(?P<numer>\d{1,4})\s*/\s*(?P<rok>\d{2}|\d{4})$"
)

# Znajdowanie sygnatur w tekście (do wyciągania kandydatów).
_RE_W_TEKSCIE = re.compile(
    r"\b(?:[IVXL]{1,5}\s+)?(?:SA/[A-ZŁ][a-zł]|[A-Z][A-Za-z\-]{0,4})\s+\d{1,6}\s*/\s*(?:\d{2}|\d{4})\b"
)


@dataclass
class Sygnatura:
    wejscie: str
    poprawna: bool
    znormalizowana: Optional[str] = None
    sad: Optional[str] = None          # "SN" | "powszechny" | "NSA" | "WSA" | "TK" | None
    wydzial: Optional[str] = None
    repertorium: Optional[str] = None
    opis: Optional[str] = None
    numer: Optional[int] = None
    rok: Optional[int] = None
    miasto: Optional[str] = None       # tylko WSA
    uwagi: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def _rok_pelny(rok: str) -> int:
    r = int(rok)
    if len(rok) == 4:
        return r
    # dwucyfrowy: 00–(bieżący rok+1) → 20xx, reszta → 19xx
    granica = (date.today().year + 1) % 100
    return 2000 + r if r <= granica else 1900 + r


def _sprawdz_wydzial(w: Optional[str], uwagi: list[str]) -> Optional[str]:
    if not w:
        return None
    w = w.upper()
    if not _ROMAN.match(w):
        uwagi.append(f"'{w}' nie jest poprawną liczbą rzymską")
        return None
    return w


def waliduj(tekst: str) -> Sygnatura:
    """Zwraca Sygnatura z polem `poprawna` i rozpoznaniem sądu/repertorium."""
    s = " ".join(str(tekst).strip().replace(" ", " ").split())
    uwagi: list[str] = []

    # Trybunał Konstytucyjny (bez wydziału, repertoria jednoznaczne)
    m = _RE_TK.match(s)
    if m and m.group("rep") in _TK:
        rep = m.group("rep")
        rok = _rok_pelny(m.group("rok"))
        # "K 1/20" może być też sądem powszechnym bez wydziału — TK nie ma wydziału,
        # sądy powszechne prawie zawsze go podają. Traktujemy jako TK, z uwagą.
        if rep in ("K", "P", "U", "S"):
            uwagi.append("zapis bez wydziału odczytany jako sygnatura TK; jeśli to sąd powszechny, podaj wydział (np. 'II K 1/20')")
        return Sygnatura(
            wejscie=tekst, poprawna=True,
            znormalizowana=f"{rep} {int(m.group('numer'))}/{m.group('rok')}",
            sad="TK", repertorium=rep, opis=_TK[rep],
            numer=int(m.group("numer")), rok=rok, uwagi=uwagi,
        )

    # WSA
    m = _RE_WSA.match(s)
    if m:
        wydzial = _sprawdz_wydzial(m.group("wydzial"), uwagi)
        miasto = m.group("miasto")
        rok = _rok_pelny(m.group("rok"))
        opis = _WSA.get(miasto)
        if not opis:
            uwagi.append(f"nieznany kod WSA '{miasto}'")
        return Sygnatura(
            wejscie=tekst, poprawna=opis is not None,
            znormalizowana=f"{(wydzial + ' ') if wydzial else ''}SA/{miasto} {int(m.group('numer'))}/{m.group('rok')}",
            sad="WSA", wydzial=wydzial, repertorium=f"SA/{miasto}",
            opis=opis, numer=int(m.group("numer")), rok=rok, miasto=miasto, uwagi=uwagi,
        )

    # SN / sądy powszechne / NSA
    m = _RE_ZWYKLA.match(s)
    if not m:
        return Sygnatura(wejscie=tekst, poprawna=False,
                         uwagi=["nie pasuje do budowy [wydział] [repertorium] [numer]/[rok]"])

    wydzial = _sprawdz_wydzial(m.group("wydzial"), uwagi)
    rep_raw = m.group("rep")
    numer = int(m.group("numer"))
    rok = _rok_pelny(m.group("rok"))

    # dopasowanie repertorium bez rozróżniania wielkości liter, ale normalizacja
    # do zapisu kanonicznego (np. "aca" → "ACa", "csk" → "CSK")
    def _znajdz(slownik: dict) -> Optional[str]:
        for k in slownik:
            if k.lower() == rep_raw.lower():
                return k
        return None

    sad = None
    rep = None
    opis = None
    for nazwa, slownik in (("SN", _SN), ("NSA", _NSA), ("powszechny", _POWSZECHNE)):
        k = _znajdz(slownik)
        if k:
            sad, rep, opis = nazwa, k, slownik[k]
            break

    if rep is None:
        return Sygnatura(
            wejscie=tekst, poprawna=False, wydzial=wydzial, repertorium=rep_raw,
            numer=numer, rok=rok,
            uwagi=uwagi + [f"nieznane repertorium '{rep_raw}'"],
        )

    if sad == "SN" and rep in ("CSK", "CZP", "KK", "KZP", "PK", "UK") and wydzial and wydzial not in ("I", "II", "III", "IV", "V"):
        uwagi.append(f"wydział {wydzial} nietypowy dla Sądu Najwyższego")
    if rok < 1918 or rok > date.today().year + 1:
        uwagi.append(f"rok {rok} poza zakresem")

    if rep in ("K", "P", "U", "S") and not wydzial:
        uwagi.append("brak wydziału — dla sądu powszechnego wydział jest zwykle podawany")

    rok_zapis = m.group("rok")
    znorm = f"{(wydzial + ' ') if wydzial else ''}{rep} {numer}/{rok_zapis}"
    return Sygnatura(
        wejscie=tekst, poprawna=True, znormalizowana=znorm, sad=sad, wydzial=wydzial,
        repertorium=rep, opis=opis, numer=numer, rok=rok, uwagi=uwagi,
    )


def normalizuj(tekst: str) -> Optional[str]:
    """Zwraca znormalizowany zapis albo None, gdy format jest niepoprawny."""
    w = waliduj(tekst)
    return w.znormalizowana if w.poprawna else None


def znajdz(tekst: str) -> list[Sygnatura]:
    """Wyszukuje w dowolnym tekście ciągi wyglądające jak sygnatury i waliduje każdy."""
    wyniki: list[Sygnatura] = []
    widziane: set[str] = set()
    for m in _RE_W_TEKSCIE.finditer(tekst):
        kandydat = m.group(0)
        w = waliduj(kandydat)
        klucz = w.znormalizowana or kandydat
        if w.poprawna and klucz not in widziane:
            widziane.add(klucz)
            wyniki.append(w)
    return wyniki


if __name__ == "__main__":
    import json
    import sys

    args = sys.argv[1:]
    if not args:
        print("użycie: python sygnatury.py 'II CSK 331/12' ['I ACa 1102/20' ...]")
        sys.exit(2)
    for a in args:
        print(json.dumps(waliduj(a).as_dict(), ensure_ascii=False, indent=2))
