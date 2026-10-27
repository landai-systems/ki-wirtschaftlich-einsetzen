"""Angriffs- und Randfalltests für die Vorlagen der Praxisfälle A, B und C.

Die Tests prüfen Schemas gegen die Grenzen strenger strukturierter Ausgaben, Prompt-Injection-Muster
in Rückfrage-Entwürfen (Fall C), Absender-, Lieferanten- und Zahlenprüfungen im Abgleich (Fall B)
und die Plausibilitätsprüfung des Montageberichts (Fall A).

Ausführen:  python3 -m pytest -q
"""
import copy
import json
import re

import jsonschema
import pytest

from schemas import FALL_A_MONTAGEBERICHT, FALL_B_AUFTRAGSBESTAETIGUNG, FALL_C_ANFRAGE, fall_c_schema
from abgleich_auftragsbestaetigung import abgleichen
from pruefe_rueckfrage import pruefe_entwurf, anfragetyp_normalisieren, rueckfrage_aus_bausteinen
from pruefe_bericht import pruefe_bericht

FC = jsonschema.FormatChecker()


def valid(schema, obj):
    return jsonschema.Draft202012Validator(schema, format_checker=FC).is_valid(obj)


# =================================================================== Schemas gegen Anthropic-Grenzen

SCHEMAS = {"A": FALL_A_MONTAGEBERICHT, "B": FALL_B_AUFTRAGSBESTAETIGUNG, "C": FALL_C_ANFRAGE,
           "C_enum": fall_c_schema(["Haustür", "Fenster", "Reparatur"])}

# laut platform.claude.com/docs/en/build-with-claude/structured-outputs (abgerufen 24.10.2026)
UNTERSTUETZTE_FORMATE = {"date-time", "time", "date", "duration", "email", "hostname", "uri", "ipv4", "ipv6", "uuid"}
NICHT_UNTERSTUETZT = {"minimum", "maximum", "exclusiveMinimum", "exclusiveMaximum", "multipleOf",
                      "minLength", "maxLength", "$ref"}


def _objekte(s):
    if isinstance(s, dict):
        if s.get("type") == "object":
            yield s
        for v in s.values():
            yield from _objekte(v)
    elif isinstance(s, list):
        for v in s:
            yield from _objekte(v)


def _schluessel(s):
    if isinstance(s, dict):
        for k, v in s.items():
            yield k, v
            yield from _schluessel(v)
    elif isinstance(s, list):
        for v in s:
            yield from _schluessel(v)


def _unions(s):
    n = 0
    if isinstance(s, dict):
        if isinstance(s.get("type"), list) or "anyOf" in s:
            n += 1
        n += sum(_unions(v) for v in s.values())
    elif isinstance(s, list):
        n += sum(_unions(v) for v in s)
    return n


@pytest.mark.parametrize("name", SCHEMAS)
def test_schema_strikt_kompatibel(name):
    s = SCHEMAS[name]
    for o in _objekte(s):
        assert o.get("additionalProperties") is False, name          # Pflicht bei Structured Outputs
        assert set(o["required"]) == set(o["properties"]), name       # keine optionalen Parameter (Grenze 24)
    for k, v in _schluessel(s):
        assert k not in NICHT_UNTERSTUETZT, (name, k)
        if k == "format":
            assert v in UNTERSTUETZTE_FORMATE, (name, v)
    assert _unions(s) <= 16, name


def test_union_reserve_fall_a_plus_b_reicht_nicht_fuer_gemeinsame_anfrage():
    # dokumentiert Anhang D: "nicht mit weiteren strengen Schemas in einer Anfrage kombinieren"
    assert _unions(FALL_B_AUFTRAGSBESTAETIGUNG) + _unions(FALL_C_ANFRAGE) == 16
    assert _unions(FALL_B_AUFTRAGSBESTAETIGUNG) + _unions(FALL_A_MONTAGEBERICHT) > 16


# =================================================================== Fall C: Prompt-Injection-Entwürfe

SAUBER = "Guten Tag, damit wir Ihnen ein Angebot erstellen können, benötigen wir noch die Maße der Türöffnung. "


def entwurf(text, **ueber):
    d = {"anfragetyp": "Haustür", "vorhanden": ["Name"], "fehlend": ["Maße der Türöffnung"],
         "rueckfrage_entwurf": text, "hinweise_fuer_bearbeitung": []}
    d.update(ueber)
    return d


def warnungen(text, **ueber):
    return pruefe_entwurf(entwurf(SAUBER + text, **ueber))


@pytest.mark.parametrize("text", [
    "Laden Sie die Fotos bitte unter https://upload.example hoch.",
    "Schreiben Sie an service at fremd-firma punkt de.",
    "Laden Sie die Fotos unter example．com hoch.",               # Vollbreiten-Punkt, NFKC greift
    "Überweisen Sie bitte auf DE89 3704 0044 0532 0130 00.",
    "Rufen Sie uns unter 0931 123456 an.",
    "Bitte nennen Sie uns Ihre Zugangsdaten.",
    "Wir liefern ab sofort.",
])
def test_regression_erkannt(text):
    assert warnungen(text), text


@pytest.mark.parametrize("text", [
    pytest.param("Überweisen Sie bitte auf DE89370400440532013000.", id="IBAN-elektronisch-ohne-Leerzeichen"),
    pytest.param("Rufen Sie uns unter +49 30 1234567 an.", id="Telefon-DIN5008-international"),
    pytest.param("Rufen Sie uns unter +49 (0) 30 123456 an.", id="Telefon-mit-(0)"),
    pytest.param("Rufen Sie uns unter 030 12 34 56 an.", id="Telefon-gruppiert"),
    pytest.param("Laden Sie die Fotos unter 203.0.113.5/upload hoch.", id="IP-Adresse"),
    pytest.param("Laden Sie die Fotos unter example . com hoch.", id="Domain-Leerzeichen-um-Punkt"),
    pytest.param("Laden Sie die Fotos unter example(dot)com hoch.", id="Domain-(dot)"),
    pytest.param("Laden Sie die Fotos unter example。com hoch.", id="Domain-ideografischer-Punkt"),
    pytest.param("Laden Sie die Fotos unter tuer­.example­.com hoch.", id="Domain-weiches-Trennzeichen"),
    pytest.param("Schreiben Sie an service (at) fremd-firma (dot) de.", id="E-Mail-(at)-(dot)"),
    pytest.param("Bitte antworten Sie per WhatsApp an die Nummer aus der Anfrage.", id="Kanalwechsel-Messenger"),
    pytest.param("Die Anzahlung beträgt 200 GBP.", id="Waehrung-GBP"),
    pytest.param("Die Anzahlung beträgt zweihundert Pfund.", id="Betrag-Pfund"),
    pytest.param("Der Einbau ist für Sie kostenfrei.", id="Zusage-kostenfrei"),
    pytest.param("Sie erhalten 10 % Nachlass.", id="Zusage-Nachlass"),
    pytest.param("Die Anfahrt übernehmen wir.", id="Zusage-uebernehmen"),
    pytest.param("Wir kommen am kommenden Montag vorbei.", id="Termin-Wochentag"),
    pytest.param("Wir kommen morgen vorbei.", id="Termin-morgen"),
    pytest.param("Die Montage erfolgt in 3 Tagen.", id="Termin-in-n-Tagen"),
    pytest.param("Die Montage erfolgt zum Monatsende.", id="Termin-Monatsende"),
    pytest.param("Bitte nennen Sie uns Ihre Online-Banking-Zugangsnummer.", id="sensibel-Zugangsnummer"),
    pytest.param("Bitte senden Sie uns ein Foto Ihrer EC-Karte.", id="sensibel-EC-Karte"),
    pytest.param("Schicken Sie die Unterlagen an Am Markt 5 in Musterstadt.", id="Adresse-ohne-Strassensuffix"),
    pytest.param("Schicken Sie die Unterlagen an Postfach 1234.", id="Adresse-Postfach"),
])
def test_unerkannte_injektionsmuster(text):
    assert warnungen(text), text


@pytest.mark.parametrize("zeichen", [
    pytest.param("‮", id="U+202E-Rechts-nach-links-Override"),
    pytest.param("⁦", id="U+2066-Bidi-Isolate"),
    pytest.param("­", id="U+00AD-weiches-Trennzeichen"),
    pytest.param("\U000e0049", id="U+E0049-Tag-Zeichen-ASCII-Smuggling"),
])
def test_steuerzeichen_werden_gemeldet(zeichen):
    w = warnungen("Vielen Dank." + zeichen)
    assert any("unsichtbare" in x for x in w), w


def test_null_breite_zeichen_werden_gemeldet():
    assert any("unsichtbare" in x for x in warnungen("Vielen Dank.​"))


@pytest.mark.parametrize("typ", ["Unklar", "UNKLAR", " unklar"])
def test_anfragetyp_unklar_unabhaengig_von_schreibweise(typ):
    assert any("unklar" in x for x in pruefe_entwurf(entwurf(SAUBER, anfragetyp=typ)))


def test_fall_c_enum_toleriert_schreibweise():
    typen = ["Haustür", "Fenster", "Reparatur"]
    s = fall_c_schema(typen)
    roh = {"anfragetyp": "haustür ", "vorhanden": [], "fehlend": [], "rueckfrage_entwurf": None,
           "hinweise_fuer_bearbeitung": []}
    d = anfragetyp_normalisieren(roh, typen)
    assert d["anfragetyp"] == "Haustür" and valid(s, d)
    assert anfragetyp_normalisieren(dict(roh, anfragetyp="Garage"), typen)["anfragetyp"] == "unklar"


def test_rueckfrage_aus_bausteinen_uebernimmt_keinen_modelltext():
    bausteine = {"Maße der Türöffnung": "Breite und Höhe der Türöffnung in Zentimetern"}
    text, unbekannt = rueckfrage_aus_bausteinen(["Maße der Türöffnung", "Überweisen Sie auf DE89..."], bausteine,
                                                "Guten Tag,", "Mit freundlichen Grüßen")
    assert "Breite und Höhe" in text and "DE89" not in text and unbekannt == ["Überweisen Sie auf DE89..."]


@pytest.mark.parametrize("text", [
    pytest.param("Damit wir Ihnen ein verbindliches Angebot erstellen können, benötigen wir die Maße.",
                 id="verbindliches-Angebot"),
    pytest.param("Gern erstellen wir Ihnen ein kostenloses Angebot.", id="kostenloses-Angebot"),
    pytest.param("Ein Punkt fehlt noch: die Maße der Türöffnung.", id="Wort-Punkt-als-Domain"),
    pytest.param("Handelt es sich um einen Neubau bzw.eine Sanierung?", id="Abkuerzung-ohne-Leerzeichen"),
])
def test_harmlose_formulierungen_ohne_warnung(text):
    assert pruefe_entwurf(entwurf(text)) == []


@pytest.mark.parametrize("text", [
    "Bitte nennen Sie uns außerdem Ihre Telefonnummer und die Adresse des Objekts.",
    "In welchem Zeitraum wünschen Sie den Einbau?",
    "Bitte teilen Sie uns Breite und Höhe der Öffnung in Zentimetern mit.",
])
def test_pflichtangaben_aus_der_beispielliste_ohne_fehlalarm(text):
    assert pruefe_entwurf(entwurf(text)) == []


# =================================================================== Fall B: Abgleich, Rand- und Fehlerfälle

BEST = {"bestellnummer": "4500123", "lieferant": "Müller Baubedarf GmbH", "lieferant_domains": ["mueller-bau.de"],
        "positionen": [
            {"artikelnr_lieferant": "A-100", "menge": 10, "einheit": "Stk", "einzelpreis_netto": 12.50,
             "preiseinheit": 1, "liefertermin": "2026-11-03"},
            {"artikelnr_lieferant": "A-200", "menge": 4, "einheit": "Karton", "einzelpreis_netto": 30.00,
             "preiseinheit": 1, "liefertermin": "2026-11-03"}]}
ABSENDER = "Auftragsbestaetigung <ab@mueller-bau.de>"


def pos(nr, menge, einheit, preis, wert, termin, rabatt=None, pe=None, p="1"):
    return {"pos": p, "artikelnr_lieferant": nr, "bezeichnung": "Artikel", "menge": menge, "einheit": einheit,
            "einzelpreis_netto": preis, "preiseinheit": pe, "rabatt_prozent": rabatt,
            "positionswert_netto": wert, "liefertermin": termin}


def ab(**ueber):
    d = {"bestellnummer": "4500123", "lieferant": "Müller Baubedarf GmbH", "ab_datum": "2026-10-23",
         "positionen": [pos("A-100", 10, "Stk", 12.50, 125.00, "2026-11-03"),
                        pos("A-200", 4, "Karton", 30.00, 120.00, "2026-11-03", p="2")],
         "gesamtbetrag_netto": 245.00, "waehrung": "EUR", "hinweise": [], "unvollstaendig_lesbar": False}
    d.update(ueber)
    return d


def pruef(d=None, best=BEST, absender=ABSENDER):
    return abgleichen(ab() if d is None else d, best, absender=absender, authentifiziert=True)


def test_grundfall_unauffaellig():
    assert valid(FALL_B_AUFTRAGSBESTAETIGUNG, ab())
    assert pruef().status == "unauffaellig"


@pytest.mark.parametrize("absender", ["x@evil.example", "x@mueller-bau.de.evil.example", "x@evil-mueller-bau.de",
                                      "Müller Baubedarf <ab@mueller-bau.de.attacker.example>"])
def test_fremder_absender_wird_markiert(absender):
    e = pruef(absender=absender)
    assert e.status == "markiert" and "gehört nicht zum Lieferanten" in " ".join(e.befunde)


@pytest.mark.parametrize("absender", ["ab@mueller-bau.de", "AB@MUELLER-BAU.DE ", "ab@eu.mueller-bau.de",
                                      "Müller <ab@mueller-bau.de>"])
def test_bekannter_absender_unauffaellig(absender):
    assert pruef(absender=absender).status == "unauffaellig"


@pytest.mark.parametrize("absender", [None, ""])
def test_fehlender_absender_wird_markiert(absender):
    assert "Absender nicht übergeben" in " ".join(pruef(absender=absender).befunde)


def test_absender_ohne_at_wird_markiert():
    assert pruef(absender="mueller-bau.de").status == "markiert"


def test_falscher_lieferant_mit_anderem_namen_wird_markiert():
    assert pruef(ab(lieferant="Müller-Fälscher GmbH")).status == "markiert"


@pytest.mark.parametrize("lieferant", ["GmbH", ".", "M", "Baubedarf"])
def test_bruchstueck_als_lieferant_wird_markiert(lieferant):
    assert pruef(ab(lieferant=lieferant)).status == "markiert"


def _mit_nan(feld_pfad):
    roh = json.dumps(ab())
    d = json.loads(roh)
    ziel = d
    for k in feld_pfad[:-1]:
        ziel = ziel[k]
    ziel[feld_pfad[-1]] = float("nan")
    return d


def test_nan_ist_schemakonform_und_von_json_loads_akzeptiert():
    assert json.loads('{"x": NaN}')["x"] != json.loads('{"x": NaN}')["x"]
    assert valid(FALL_B_AUFTRAGSBESTAETIGUNG, _mit_nan(["positionen", 0, "einzelpreis_netto"]))


@pytest.mark.parametrize("pfad", [["positionen", 0, "einzelpreis_netto"], ["positionen", 0, "menge"],
                                  ["gesamtbetrag_netto"]], ids=["preis", "menge", "gesamtbetrag"])
def test_nan_wird_markiert(pfad):
    assert pruef(_mit_nan(pfad)).status == "markiert"


@pytest.mark.parametrize("termin", ["2026-W45-2", "20261103"])
def test_nicht_iso_kalenderdatum_wird_markiert(termin):
    d = ab()
    d["positionen"][0]["liefertermin"] = termin
    assert not valid(FALL_B_AUFTRAGSBESTAETIGUNG, d)
    assert pruef(d).status == "markiert"


@pytest.mark.parametrize("nr", ["a-100", "A-100 ", "A 100"])
def test_artikelnummer_schreibweise(nr):
    d = ab()
    d["positionen"][0]["artikelnr_lieferant"] = nr
    assert pruef(d).status == "unauffaellig"


def test_bestellung_mit_artikel_zu_zwei_terminen():
    best = copy.deepcopy(BEST)
    best["positionen"].append(dict(best["positionen"][0], liefertermin="2026-11-20"))
    d = ab()
    d["positionen"][0:1] = [pos("A-100", 10, "Stk", 12.50, 125.00, "2026-11-03"),
                            pos("A-100", 10, "Stk", 12.50, 125.00, "2026-11-20", p="1b")]
    d["gesamtbetrag_netto"] = 370.00
    t = " | ".join(pruef(d, best).befunde)
    assert "mehrfach" in t and "früher als bestellt" not in t


@pytest.mark.parametrize("kaputt", [
    {"positionen": [["keine", "dict"]]},
    {"positionen": None},
    {},
])
def test_kaputte_ausgabe_bricht_nicht_ab_und_wird_markiert(kaputt):
    d = ab()
    d.update(kaputt) if kaputt else d.clear()
    assert pruef(d).status == "markiert"


def test_negativer_positionswert_wird_markiert():
    d = ab()
    d["positionen"].append(pos(None, 1, "psch", -50.0, -50.0, None, p="3"))
    d["gesamtbetrag_netto"] = 195.0
    assert pruef(d).status == "markiert"


def test_unendlich_wird_markiert():
    d = ab()
    d["positionen"][0].update(einzelpreis_netto=float("inf"), positionswert_netto=float("inf"))
    d["gesamtbetrag_netto"] = float("inf")
    assert pruef(d).status == "markiert"


def test_bankverbindung_im_hinweis_wird_markiert():
    assert "Neue Bankverbindung" in " ".join(pruef(ab(hinweise=["Neue Bankverbindung: DE12 ..."])).befunde)


def test_preisabweichung_knapp_unter_toleranz_bleibt_unauffaellig_dokumentiert():
    d = ab()
    d["positionen"][0].update(einzelpreis_netto=12.56, positionswert_netto=125.60)   # +0,48 %
    d["gesamtbetrag_netto"] = 245.60
    assert pruef(d).status == "unauffaellig"


# =================================================================== Fall A: Plausibilitätsprüfung

STAMM = dict(baustellen={"B-1"}, mitarbeiter={"M01", "M02"}, katalog={"K-1"})


def bericht(**ueber):
    d = {"baustelle_id": "B-1", "abweichendes_datum_genannt": None,
         "personen": [{"mitarbeiter_id": "M01", "name_wie_genannt": "Jonas", "stunden": 8}],
         "material": [], "zusatzleistungen": [], "auffaelligkeiten": [], "fehlende_angaben": [],
         "unsichere_angaben": []}
    d.update(ueber)
    return d


def test_bericht_grundfall():
    assert valid(FALL_A_MONTAGEBERICHT, bericht())
    assert pruefe_bericht(bericht(), **STAMM) == []


@pytest.mark.parametrize("ueber,erwartet", [
    (dict(baustelle_id=None), "nicht zugeordnet"),
    (dict(personen=[{"mitarbeiter_id": "M99", "name_wie_genannt": "X", "stunden": 8}]), "unbekannt"),
    (dict(personen=[{"mitarbeiter_id": "M01", "name_wie_genannt": "J", "stunden": 8}] * 2), "mehrfach"),
    (dict(personen=[{"mitarbeiter_id": "M01", "name_wie_genannt": "J", "stunden": 14}]), "unplausible Stunden"),
    (dict(material=[{"bezeichnung": "Silikon", "menge": -2, "einheit": "Stk", "katalog_nr": "K-1"}]), "Menge"),
    (dict(zusatzleistungen=[{"beschreibung": "x", "stunden": -1}]), "negative"),
    (dict(abweichendes_datum_genannt="gestern"), "anderen Tag"),
])
def test_bericht_regeln(ueber, erwartet):
    assert erwartet in " | ".join(pruefe_bericht(bericht(**ueber), **STAMM))


def test_bericht_nan_stunden():
    assert pruefe_bericht(bericht(personen=[{"mitarbeiter_id": "M01", "name_wie_genannt": "J",
                                             "stunden": float("nan")}]), **STAMM)


def test_bericht_zusatzleistung_unplausibel_lang():
    assert pruefe_bericht(bericht(zusatzleistungen=[{"beschreibung": "Fensterbank", "stunden": 80}]), **STAMM)


def test_bericht_person_fehlt_in_zeiterfassung():
    b = bericht(personen=[{"mitarbeiter_id": "M02", "name_wie_genannt": "Ali", "stunden": 8}])
    assert pruefe_bericht(b, **STAMM, erfasste_stunden={"M01": 8.0})
