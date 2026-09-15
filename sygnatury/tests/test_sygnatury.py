import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sygnatury import waliduj, normalizuj, znajdz  # noqa: E402


def test_sn_csk():
    w = waliduj("II CSK 331/12")
    assert w.poprawna and w.sad == "SN" and w.repertorium == "CSK"
    assert w.wydzial == "II" and w.numer == 331 and w.rok == 2012
    assert w.znormalizowana == "II CSK 331/12"


def test_sn_uchwala():
    w = waliduj("III CZP 61/03")
    assert w.poprawna and w.sad == "SN" and w.rok == 2003


def test_apelacyjny():
    w = waliduj("I ACa 1102/20")
    assert w.poprawna and w.sad == "powszechny" and w.repertorium == "ACa"


def test_okregowy_cywilny():
    w = waliduj("I C 1113/25")
    assert w.poprawna and w.sad == "powszechny" and w.rok == 2025


def test_gospodarczy():
    w = waliduj("VI GC 665/26")
    assert w.poprawna and w.repertorium == "GC" and w.rok == 2026


def test_karny_rybnik():
    w = waliduj("III K 106/24")
    assert w.poprawna and w.sad == "powszechny" and w.repertorium == "K"


def test_nsa():
    w = waliduj("II FSK 1/20")
    assert w.poprawna and w.sad == "NSA"


def test_wsa():
    w = waliduj("III SA/Wa 123/20")
    assert w.poprawna and w.sad == "WSA" and w.miasto == "Wa"
    assert w.znormalizowana == "III SA/Wa 123/20"


def test_wsa_nieznane_miasto():
    w = waliduj("I SA/Xx 5/21")
    assert not w.poprawna


def test_tk():
    w = waliduj("SK 7/06")
    assert w.poprawna and w.sad == "TK"
    w = waliduj("Kp 3/09")
    assert w.poprawna and w.sad == "TK"


def test_tk_k_bez_wydzialu_ma_uwage():
    w = waliduj("K 1/20")
    assert w.poprawna and w.sad == "TK" and w.uwagi


def test_normalizacja_zapisu():
    assert normalizuj("ii csk 331 / 12") == "II CSK 331/12"
    assert normalizuj("I  ACa   1102/2020") == "I ACa 1102/2020"
    assert normalizuj("II CSK 331/12") == "II CSK 331/12"


def test_rok_czterocyfrowy():
    w = waliduj("I ACa 1102/2020")
    assert w.rok == 2020


def test_rok_dwucyfrowy_xx_wiek():
    assert waliduj("III CZP 61/95").rok == 1995


def test_nieznane_repertorium():
    w = waliduj("II XYZ 12/20")
    assert not w.poprawna and "nieznane repertorium" in w.uwagi[0]


def test_zla_liczba_rzymska():
    w = waliduj("IIII C 1/20")
    assert w.poprawna and w.wydzial is None and w.uwagi


def test_smieci():
    for s in ("art. 471 k.c.", "12/2020", "CSK", "", "Dz.U. 2020 poz. 1"):
        assert not waliduj(s).poprawna, s


def test_znajdz_w_tekscie():
    tekst = (
        "Por. wyrok SN z 12.03.2013 r., II CSK 331/12, oraz uchwałę III CZP 61/03; "
        "odmiennie WSA w wyroku III SA/Wa 123/20. Art. 9999 k.c. nie istnieje. "
        "Sygnatura II CSK 331/12 powtórzona."
    )
    z = znajdz(tekst)
    assert [w.znormalizowana for w in z] == ["II CSK 331/12", "III CZP 61/03", "III SA/Wa 123/20"]


def test_as_dict():
    d = waliduj("II CSK 331/12").as_dict()
    assert d["sad"] == "SN" and d["poprawna"] is True
