"""Kommandozeile: Datenimport, ungültiges JSON, fehlende Pflichtfelder, abgebrochene Modellausgaben."""
import json
import os

import pytest

from pruefen import main

H = os.path.join(os.path.dirname(os.path.abspath(__file__)), "beispiele")


def lauf(capsys, *argv):
    rc = main(list(argv))
    return rc, json.loads(capsys.readouterr().out)


def eingabe(tmp_path, name, d):
    p = tmp_path / name
    p.write_text(json.dumps(d["eingabe"] if "eingabe" in d else d, ensure_ascii=False), encoding="utf-8")
    return str(p)


def lade(rel):
    with open(os.path.join(H, rel), encoding="utf-8") as f:
        return json.load(f)


def test_fall_a_unauffaellig_und_markiert(capsys, tmp_path):
    st = os.path.join(H, "fall_a", "_stammdaten.json")
    assert lauf(capsys, "a", "--bericht", eingabe(tmp_path, "a.json", lade("fall_a/a1_vollstaendig.json")),
                "--stammdaten", st)[0] == 0
    rc, out = lauf(capsys, "a", "--bericht", eingabe(tmp_path, "b.json", lade("fall_a/a2_baustelle_inaktiv.json")),
                   "--stammdaten", st)
    assert rc == 1 and out["status"] == "markiert"


def test_fall_b_mit_dmarc(capsys, tmp_path):
    best = os.path.join(H, "fall_b", "_bestellung.json")
    ab = eingabe(tmp_path, "ab.json", lade("fall_b/b1_passend.json"))
    assert lauf(capsys, "b", "--bestaetigung", ab, "--bestellung", best, "--absender", "ab@mueller-bau.de",
                "--dmarc", "pass")[0] == 0
    rc, out = lauf(capsys, "b", "--bestaetigung", ab, "--bestellung", best, "--absender", "ab@mueller-bau.de")
    assert rc == 1 and any("DMARC" in m for m in out["meldungen"])


def test_fall_c_beide_varianten(capsys, tmp_path):
    erg = lade("fall_c/c1_gute_rueckfrage.json")["eingabe"]
    assert lauf(capsys, "c", "--ergebnis", eingabe(tmp_path, "c.json", erg))[0] == 0
    ohne = {k: v for k, v in erg.items() if k != "rueckfrage_entwurf"}
    assert lauf(capsys, "c", "--ergebnis", eingabe(tmp_path, "d.json", ohne), "--variante", "bausteine")[0] == 0


def test_abgebrochene_modellausgabe(capsys, tmp_path):
    p = tmp_path / "x.json"
    p.write_text('{"anfragetyp": "Haustür", "vorhanden": ["Adr', encoding="utf-8")
    rc, out = lauf(capsys, "c", "--ergebnis", str(p))
    assert rc == 2 and "kein gültiges JSON" in out["meldungen"][0]


def test_datei_fehlt_und_falsche_kodierung(capsys, tmp_path):
    assert lauf(capsys, "c", "--ergebnis", str(tmp_path / "fehlt.json"))[0] == 2
    p = tmp_path / "latin.json"
    p.write_bytes('{"anfragetyp": "Haustür"}'.encode("latin-1"))
    rc, out = lauf(capsys, "c", "--ergebnis", str(p))
    assert rc == 2 and "UTF-8" in out["meldungen"][0]


def test_kein_objekt(capsys, tmp_path):
    p = tmp_path / "l.json"; p.write_text("[1, 2]", encoding="utf-8")
    assert lauf(capsys, "c", "--ergebnis", str(p))[0] == 2


def test_fehlendes_pflichtfeld(capsys, tmp_path):
    d = dict(lade("fall_b/b1_passend.json")["eingabe"]); del d["positionen"]
    rc, out = lauf(capsys, "b", "--bestaetigung", eingabe(tmp_path, "ab.json", d),
                   "--bestellung", os.path.join(H, "fall_b", "_bestellung.json"))
    assert rc == 2 and "positionen" in out["meldungen"][0]


def test_unplausibler_typ_im_schema(capsys, tmp_path):
    d = lade("fall_a/a1_vollstaendig.json")["eingabe"]
    d["personen"][0]["stunden"] = "acht"
    rc, out = lauf(capsys, "a", "--bericht", eingabe(tmp_path, "a.json", d),
                   "--stammdaten", os.path.join(H, "fall_a", "_stammdaten.json"))
    assert rc == 2 and "stunden" in out["meldungen"][0]


def test_stammdaten_unvollstaendig(capsys, tmp_path):
    st = tmp_path / "st.json"; st.write_text('{"baustellen": []}', encoding="utf-8")
    rc, out = lauf(capsys, "a", "--bericht", eingabe(tmp_path, "a.json", lade("fall_a/a1_vollstaendig.json")),
                   "--stammdaten", str(st))
    assert rc == 2 and "mitarbeiter" in out["meldungen"][0]


def test_ohne_jsonschema_mindestpruefung(capsys, tmp_path, monkeypatch):
    import builtins
    echt = builtins.__import__
    monkeypatch.setattr(builtins, "__import__",
                        lambda n, *a, **k: (_ for _ in ()).throw(ImportError()) if n == "jsonschema" else echt(n, *a, **k))
    rc, out = lauf(capsys, "c", "--ergebnis", eingabe(tmp_path, "c.json", {"anfragetyp": "Haustür"}))
    assert rc == 2 and "Pflichtfelder fehlen" in out["meldungen"][0]
