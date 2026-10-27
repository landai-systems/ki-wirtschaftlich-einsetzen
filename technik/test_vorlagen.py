"""Tests für Schemas, Abgleich (Fall B) und Entwurfsprüfung (Fall C).

Enthält die Randfälle aus der unabhängigen technischen Prüfung (Review B) als feste Anforderungen.
Ein Test dokumentiert ausdrücklich eine Grenze, die kein Abgleich beheben kann (manipulierte Werte).
"""
import copy
import jsonschema
from schemas import FALL_A_MONTAGEBERICHT, FALL_B_AUFTRAGSBESTAETIGUNG, FALL_C_ANFRAGE
from abgleich_auftragsbestaetigung import abgleichen, Toleranzen
from pruefe_rueckfrage import pruefe_entwurf

FC = jsonschema.FormatChecker()


def valid(schema, obj):
    return jsonschema.Draft202012Validator(schema, format_checker=FC).is_valid(obj)


# ---------------------------------------------------------------- Schemas

def test_schemas_gueltig():
    for s in (FALL_A_MONTAGEBERICHT, FALL_B_AUFTRAGSBESTAETIGUNG, FALL_C_ANFRAGE):
        jsonschema.Draft202012Validator.check_schema(s)


def bericht(**ueber):
    d = {"baustelle_id": "B-2026-114", "abweichendes_datum_genannt": None,
         "personen": [{"mitarbeiter_id": "M01", "name_wie_genannt": "Jonas", "stunden": 8},
                      {"mitarbeiter_id": None, "name_wie_genannt": "der Neue", "stunden": None}],
         "material": [{"bezeichnung": "Dichtband 15 mm", "menge": 2, "einheit": "Rolle", "katalog_nr": None}],
         "zusatzleistungen": [{"beschreibung": "Fensterbank gekürzt auf Kundenwunsch", "stunden": 0.5}],
         "auffaelligkeiten": [], "fehlende_angaben": ["Stunden zweite Person"],
         "unsichere_angaben": ["Mitarbeiter 'der Neue' nicht eindeutig zuzuordnen"]}
    d.update(ueber)
    return d


def test_fall_a_beispiel_mit_luecken():
    assert valid(FALL_A_MONTAGEBERICHT, bericht())


def test_fall_a_leere_listen_erlaubt_null_fuer_listen_nicht():
    assert valid(FALL_A_MONTAGEBERICHT, bericht(material=[], zusatzleistungen=[]))
    assert not valid(FALL_A_MONTAGEBERICHT, bericht(material=None))


def test_fall_a_fremdes_feld_abgelehnt():
    assert not valid(FALL_A_MONTAGEBERICHT, bericht(datum="2026-10-22"))   # Datum kommt aus den Metadaten


def test_unmoegliches_datum_vom_schema_abgelehnt():
    d = ab()
    d["positionen"][0]["liefertermin"] = "2026-02-31"
    assert not valid(FALL_B_AUFTRAGSBESTAETIGUNG, d)
    d["positionen"][0]["liefertermin"] = "03.11.2026"
    assert not valid(FALL_B_AUFTRAGSBESTAETIGUNG, d)


def test_fall_c_beispiel():
    assert valid(FALL_C_ANFRAGE, {"anfragetyp": "Haustür", "vorhanden": ["Name", "Telefon"],
        "fehlend": ["Maße der Türöffnung", "Adresse des Objekts"],
        "rueckfrage_entwurf": "Guten Tag, ...", "hinweise_fuer_bearbeitung": []})


# ---------------------------------------------------------------- Abgleich Fall B

BESTELLUNG = {"bestellnummer": "4500123", "positionen": [
    {"artikelnr_lieferant": "A-100", "menge": 10, "einheit": "Stk", "einzelpreis_netto": 12.50,
     "preiseinheit": 1, "liefertermin": "2026-11-03"},
    {"artikelnr_lieferant": "A-200", "menge": 4, "einheit": "Karton", "einzelpreis_netto": 30.00,
     "preiseinheit": 1, "liefertermin": "2026-11-03"}]}


def pos(nr, bez, menge, einheit, preis, wert, termin, rabatt=None, pe=None, p="1"):
    return {"pos": p, "artikelnr_lieferant": nr, "bezeichnung": bez, "menge": menge, "einheit": einheit,
            "einzelpreis_netto": preis, "preiseinheit": pe, "rabatt_prozent": rabatt,
            "positionswert_netto": wert, "liefertermin": termin}


def ab(**ueber):
    d = {"bestellnummer": "4500123", "lieferant": "Lieferant X", "ab_datum": "2026-10-23",
         "positionen": [pos("A-100", "Winkel", 10, "Stk", 12.50, 125.00, "2026-11-03"),
                        pos("A-200", "Schrauben", 4, "Karton", 30.00, 120.00, "2026-11-04", p="2")],
         "gesamtbetrag_netto": 245.00, "waehrung": "EUR", "hinweise": [], "unvollstaendig_lesbar": False}
    d.update(ueber)
    return d


def befunde(d, best=BESTELLUNG, **kw):
    return " | ".join(abgleichen(d, best, **kw).befunde)


def test_unauffaellig_innerhalb_toleranz():
    d = ab()
    assert valid(FALL_B_AUFTRAGSBESTAETIGUNG, d)
    e = abgleichen(d, BESTELLUNG)
    assert e.status == "unauffaellig", e.befunde   # 1 Tag später liegt innerhalb der Toleranz


def test_preis_termin_einheit():
    d = ab()
    d["positionen"][0].update(einzelpreis_netto=13.10, positionswert_netto=131.00)
    d["positionen"][1].update(liefertermin="2026-11-17", einheit="Stk")
    d["gesamtbetrag_netto"] = 251.00
    t = befunde(d)
    assert "Preis 13.10 statt 12.50" in t and "+14 Tage" in t and "Einheit Stk statt Karton" in t


def test_frueherer_termin():
    d = ab()
    d["positionen"][0]["liefertermin"] = "2026-10-20"
    assert "früher als bestellt" in befunde(d)


def test_mengenabweichung():
    d = ab()
    d["positionen"][0].update(menge=12, positionswert_netto=150.00)
    d["gesamtbetrag_netto"] = 270.00
    assert "A-100: Menge 12 statt 10" in befunde(d)


def test_fehlende_position_und_summenfehler():
    d = ab()
    d["positionen"] = d["positionen"][:1]
    t = befunde(d)
    assert "fehlt in der Bestätigung: A-200" in t
    assert "Summe der Positionen 125.00 weicht vom Gesamtbetrag 245.00 ab" in t


def test_nicht_bestellte_position_und_falsche_bestellnummer():
    d = ab(bestellnummer="4500999")
    d["positionen"].append(pos("X-1", "Ersatzartikel", 1, "Stk", 5.0, 5.0, "2026-11-03", p="3"))
    d["gesamtbetrag_netto"] = 250.00
    t = befunde(d)
    assert "Position nicht bestellt: X-1" in t and "Bestellnummer passt nicht" in t


def test_rabatt_wird_beruecksichtigt():
    d = ab()
    d["positionen"][0].update(einzelpreis_netto=13.89, rabatt_prozent=10, positionswert_netto=125.01)
    d["gesamtbetrag_netto"] = 245.01
    assert abgleichen(d, BESTELLUNG).status == "unauffaellig"


def test_preis_je_100_stueck():
    best = copy.deepcopy(BESTELLUNG)
    best["positionen"][0].update(einzelpreis_netto=1250.0, preiseinheit=100)
    d = ab()
    d["positionen"][0].update(einzelpreis_netto=1250.0, preiseinheit=100)
    assert abgleichen(d, best).status == "unauffaellig"


def test_zuschlag_nur_als_hinweis_wird_markiert():
    d = ab(hinweise=["Materialteuerungszuschlag 4 % auf alle Positionen"])
    assert "Hinweis im Dokument: Materialteuerungszuschlag" in befunde(d)


def test_doppelte_position_wird_markiert():
    d = ab()
    d["positionen"].append(pos("A-200", "Schrauben", 4, "Karton", 30.00, 120.00, "2026-11-04", p="3"))
    d["gesamtbetrag_netto"] = 365.00
    t = befunde(d)
    assert "A-200: 2 Positionen" in t and "Menge 8 statt 4" in t


def test_geteilte_lieferung_ergibt_hinweis_aber_keinen_mengenfehler():
    d = ab()
    d["positionen"][0:1] = [pos("A-100", "Winkel", 6, "Stk", 12.50, 75.00, "2026-11-03"),
                            pos("A-100", "Winkel", 4, "Stk", 12.50, 50.00, "2026-11-04", p="1b")]
    t = befunde(d)
    assert "A-100: 2 Positionen" in t and "Menge" not in t


def test_positionswert_passt_nicht_zu_menge_mal_preis():
    d = ab()
    d["positionen"][0]["einzelpreis_netto"] = 12.05     # falsch gelesen, Positionswert 125,00 korrekt
    t = befunde(d)
    assert "passt nicht zu Menge x Preis" in t and "Preis 12.05 statt 12.50" in t


def test_fehlender_gesamtbetrag_wird_gemeldet():
    assert "Gesamtbetrag nicht ausgelesen" in befunde(ab(gesamtbetrag_netto=None))


def test_falsche_waehrung():
    assert "Währung CHF" in befunde(ab(waehrung="CHF"))


def test_kostenlose_position_ohne_absturz():
    best = copy.deepcopy(BESTELLUNG)
    best["positionen"].append({"artikelnr_lieferant": "M-1", "menge": 1, "einheit": "Stk",
                               "einzelpreis_netto": 0.0, "preiseinheit": 1, "liefertermin": "2026-11-03"})
    d = ab()
    d["positionen"].append(pos("M-1", "Muster", 1, "Stk", 0.0, 0.0, "2026-11-03", p="3"))
    assert abgleichen(d, best).status == "unauffaellig"
    d["positionen"][-1].update(einzelpreis_netto=9.0, positionswert_netto=9.0)
    d["gesamtbetrag_netto"] = 254.0
    assert "kostenlose Position" in befunde(d, best)


def test_fehlerhafter_beleg_stoppt_lauf_nicht():
    best = copy.deepcopy(BESTELLUNG)
    best["positionen"][0]["liefertermin"] = None
    t = befunde(ab(), best)
    assert "kein Solltermin" in t
    d = ab()
    d["positionen"][0]["liefertermin"] = "2026-02-31"
    assert "ungültiges Datum" in befunde(d)


def test_unplausible_werte():
    d = ab()
    d["positionen"][0].update(rabatt_prozent=150)
    assert "unplausibler Wert" in befunde(d)


def test_unlesbar_wird_markiert():
    assert "nicht vollständig lesbar" in befunde(ab(unvollstaendig_lesbar=True))


def test_toleranzen_unveraenderlich():
    import dataclasses
    try:
        Toleranzen().termin_spaeter_tage = 100
        assert False, "Toleranzen dürfen nicht nachträglich änderbar sein"
    except dataclasses.FrozenInstanceError:
        pass


def test_grenze_manipulierte_werte_bleiben_unentdeckt():
    """Bekannte Grenze: Gibt das Modell (etwa durch versteckten Text im PDF) genau die Bestellwerte aus,
    kann kein Abgleich die tatsächlich gedruckte Abweichung erkennen. Dagegen helfen nur Prozessmaßnahmen."""
    d = ab()
    d["positionen"][1]["liefertermin"] = "2026-11-03"
    assert abgleichen(d, BESTELLUNG).status == "unauffaellig"


# ---------------------------------------------------------------- Entwurfsprüfung Fall C

def test_entwurf_unauffaellig():
    assert pruefe_entwurf({"anfragetyp": "Haustür", "vorhanden": [], "fehlend": ["Maße"],
        "rueckfrage_entwurf": "Guten Tag, damit wir Ihnen ein Angebot erstellen können, benötigen wir die Maße der Türöffnung.",
        "hinweise_fuer_bearbeitung": []}) == []


def test_entwurf_mit_link_betrag_und_zusage():
    w = pruefe_entwurf({"anfragetyp": "Haustür", "vorhanden": [], "fehlend": ["Maße"],
        "rueckfrage_entwurf": "Bitte zahlen Sie 200 € an DE12 3456 und laden Sie Fotos auf www.example.com hoch. Wir garantieren Lieferung in KW 45.",
        "hinweise_fuer_bearbeitung": []})
    t = " | ".join(w)
    for erwartet in ("Link", "Bankverbindung", "Geldbetrag", "Datum oder Termin", "Zusage"):
        assert erwartet in t


def test_entwurf_widerspruechlich():
    assert pruefe_entwurf({"anfragetyp": "Fenster", "vorhanden": [], "fehlend": ["Anzahl"],
        "rueckfrage_entwurf": None, "hinweise_fuer_bearbeitung": ["Text enthält Anweisungen an das System"]})


# ---------------------------------------------------------------- Plausibilität Fall A
from pruefe_bericht import pruefe_bericht

STAMM = dict(baustellen={"B-2026-114"}, mitarbeiter={"M01", "M02"}, katalog={"K-77"})


def test_bericht_mit_luecken_wird_markiert():
    t = " | ".join(pruefe_bericht(bericht(), **STAMM))
    for erwartet in ("nicht eindeutig zugeordnet", "Stunden fehlen", "nicht im Katalog", "unsichere Angaben"):
        assert erwartet in t


def test_bericht_vollstaendig_unauffaellig():
    b = bericht(personen=[{"mitarbeiter_id": "M01", "name_wie_genannt": "Jonas", "stunden": 8}],
                material=[{"bezeichnung": "Dichtband", "menge": 2, "einheit": "Rolle", "katalog_nr": "K-77"}],
                fehlende_angaben=[], unsichere_angaben=[])
    assert pruefe_bericht(b, **STAMM) == []


def test_bericht_unplausible_werte_und_zeiterfassung():
    b = bericht(baustelle_id="B-1999-001",
                personen=[{"mitarbeiter_id": "M01", "name_wie_genannt": "Jonas", "stunden": -8},
                          {"mitarbeiter_id": "M02", "name_wie_genannt": "Ali", "stunden": 9}],
                fehlende_angaben=[], unsichere_angaben=[])
    t = " | ".join(pruefe_bericht(b, **STAMM, erfasste_stunden={"M02": 7.5}))
    assert "nicht aktiv" in t and "unplausible Stunden -8" in t and "Zeiterfassung" in t
