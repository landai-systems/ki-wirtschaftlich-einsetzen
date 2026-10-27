"""Die Beispieldatensätze im Ordner beispiele/ liefern das dokumentierte Ergebnis."""
import pytest
from beispiele.beispiele_pruefen import faelle

FAELLE = list(faelle())


@pytest.mark.parametrize("name,beschreibung,ok,w", FAELLE, ids=[f[0] for f in FAELLE])
def test_beispiel(name, beschreibung, ok, w):
    assert ok, (name, w)


def test_eingaben_schemakonform():
    """Alle Beispiel-Eingaben entsprechen dem Schema der Modellausgabe."""
    import glob, json, os
    import jsonschema
    import schemas
    s = {"fall_a": schemas.FALL_A_MONTAGEBERICHT, "fall_b": schemas.FALL_B_AUFTRAGSBESTAETIGUNG,
         "fall_c": schemas.FALL_C_ANFRAGE}
    h = os.path.join(os.path.dirname(os.path.abspath(__file__)), "beispiele")
    for p in glob.glob(os.path.join(h, "fall_*", "[!_]*.json")):
        fall = os.path.basename(os.path.dirname(p))
        e = json.load(open(p, encoding="utf-8"))["eingabe"]
        fehler = list(jsonschema.Draft202012Validator(s[fall], format_checker=jsonschema.FormatChecker()).iter_errors(e))
        assert not fehler, (p, [f.message for f in fehler])
