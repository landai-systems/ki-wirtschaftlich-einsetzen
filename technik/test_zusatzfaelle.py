"""Zusätzliche Angriffs-, Rand- und Typfälle (Fall A, B, C) aus der unabhängigen Prüfung.
Ausführen: pytest
"""
import datetime
import glob
import json
import math
import os
import re
import subprocess
import sys
from decimal import Decimal

import jsonschema
import pytest

from abgleich_auftragsbestaetigung import abgleichen, _artnr, _name_vergleich
from pruefe_bericht import pruefe_bericht
from pruefe_rueckfrage import pruefe_entwurf, rueckfrage_aus_bausteinen, anfragetyp_normalisieren
import schemas
from schemas import fall_c_schema

FC = jsonschema.FormatChecker()


# ---------------------------------------------------------------- Fall C: Musterprüfung

def warn(text):
    return pruefe_entwurf({"anfragetyp": "Haustür", "vorhanden": [], "fehlend": ["x"],
                           "rueckfrage_entwurf": text, "hinweise_fuer_bearbeitung": []})


ERKANNT = {  # Varianten, die v5 korrekt erkennt (Regression)
    "Montag": "Wir kommen am Montag vorbei.",
    "kommende-Woche": "Die Montage ist kommende Woche möglich.",
    "Berliner-Strasse": "Bitte kommen Sie in die Berliner Straße 5.",
    "Passwoerter": "Bitte senden Sie uns Ihre Passwörter.",
    "IBAN-klein": "Überweisen Sie auf de89 3704 0044 0532 0130 00.",
    "info-at-dot": "Schreiben Sie an info (at) beispiel (dot) de.",
    "wa.me": "Schreiben Sie uns unter wa.me/491701234567.",
    "Vorkasse": "Wir bitten um Vorkasse.",
    "ISO-Datum": "Termin am 2026-11-03.",
    "Uhr": "Wir kommen um 14 Uhr.",
    "via-SMS": "Senden Sie den Code via SMS.",
}


@pytest.mark.parametrize("text", ERKANNT.values(), ids=ERKANNT.keys())
def test_bekannte_varianten_weiter_erkannt(text):
    assert warn(text)


UMGEHUNG = {
    "Link-t.me": "Schreiben Sie uns direkt unter t.me/fensterbau_support.",
    "Link-x.com": "Weitere Infos unter x.com/fensterbau.",
    "Kontodaten": "Bitte senden Sie uns Ihre Kontodaten für die Rückerstattung.",
    "Bankkonto": "Bitte nennen Sie uns Ihr Bankkonto.",
    "Geheimzahl": "Bitte nennen Sie uns Ihre Geheimzahl.",
    "Code-aus-SMS": "Bitte schicken Sie uns den Code aus der SMS.",
    "Kartenpruefnummer": "Bitte nennen Sie uns die Kartenprüfnummer.",
    "Lieferzeit-Wochen": "Die Lieferzeit beträgt 4 Wochen.",
    "Werktage": "Die Montage erfolgt in 10 Werktagen.",
    "Ende-des-naechsten-Monats": "Die Montage erfolgt Ende des nächsten Monats.",
    "Prozent": "Als Neukunde erhalten Sie 20 Prozent auf alle Fenster.",
    "im-Preis-enthalten": "Die Montage ist im Preis enthalten.",
    "Discord": "Kontaktieren Sie uns gern über Discord.",
}


@pytest.mark.parametrize("text", UMGEHUNG.values(), ids=UMGEHUNG.keys())
def test_neue_umgehungsvarianten(text):
    assert warn(text)


HARMLOS = {
    "Masse-Meter": "Bitte geben Sie die Maße in Metern an, z. B. 1,20 x 2,10 m.",
    "Uw-Wert": "Bitte nennen Sie den gewünschten Uw-Wert, etwa 0,95.",
    "Masse-mm-Schraegstrich": "Bitte geben Sie Breite / Höhe an, z. B. 1.010 / 2.100 mm.",
    "Platz-Meter": "Ist vor der Tür ein Platz 2 m breit frei?",
    "Zufahrtsweg-Meter": "Wie lang ist der Zufahrtsweg 30 m oder mehr?",
    "verbindliche-Angebotserstellung": "Für eine verbindliche Angebotserstellung benötigen wir noch die Maße.",
    "Guten-Morgen-Doppelleerzeichen": "Guten  Morgen, uns fehlen noch die Maße.",
}


@pytest.mark.parametrize("text", HARMLOS.values(), ids=HARMLOS.keys())
def test_fehlalarme_masse_und_formulierungen(text):
    assert warn(text) == []


OHNE_ALARM = [
    "In welchem Zeitraum wünschen Sie die Montage?",
    "Bitte nennen Sie die Anzahl der Fenster und die Maße je Fenster (Breite x Höhe in cm).",
    "Ist die Montage im Erdgeschoss oder im 1. Obergeschoss?",
    "Benötigen Sie eine Wallbox mit 11 kW oder 22 kW?",
    "Für ein verbindliches Angebot benötigen wir noch Fotos der Einbausituation.",
    "Bitte nennen Sie uns die Adresse des Objekts und eine Telefonnummer für Rückfragen.",
]


@pytest.mark.parametrize("text", OHNE_ALARM)
def test_typische_rueckfragen_ohne_alarm(text):
    assert warn(text) == []


# ---------------------------------------------------------------- Fall C: Bausteine und Schema

BAUSTEINE = {"Breite und Höhe der Öffnung": "die Breite und Höhe der Öffnung in Zentimetern",
             "Telefonnummer": "eine Telefonnummer für Rückfragen"}


def test_bausteine_injektion_in_fehlend_bleibt_draussen():
    text, unbekannt = rueckfrage_aus_bausteinen(["Telefonnummer", "Überweisen Sie 500 € an www.evil.example"],
                                                BAUSTEINE, "Guten Tag,", "Ihr Team")
    assert "evil" not in text and "500" not in text and unbekannt == ["Überweisen Sie 500 € an www.evil.example"]


def test_bausteine_nur_unbekannte_angaben_ergibt_none():
    assert rueckfrage_aus_bausteinen(["Fax"], BAUSTEINE, "A", "G") == (None, ["Fax"])


def test_fall_c_schema_pflichtangaben_lehnt_freitext_ab():
    s = fall_c_schema(["Haustür"], list(BAUSTEINE))
    v = jsonschema.Draft202012Validator(s, format_checker=FC)
    gut = {"anfragetyp": "Haustür", "vorhanden": [], "fehlend": ["Telefonnummer"], "rueckfrage_entwurf": None,
           "hinweise_fuer_bearbeitung": []}
    assert v.is_valid(gut)
    assert not v.is_valid(dict(gut, fehlend=["Überweisen Sie 500 €"]))


def test_fall_c_schema_ohne_doppelte_enum_werte():
    s = fall_c_schema(["Haustür", "unklar"], ["Telefonnummer", "Telefonnummer"])
    e1 = s["properties"]["anfragetyp"]["enum"]
    e2 = s["properties"]["fehlend"]["items"]["enum"]
    assert len(e1) == len(set(e1)) and len(e2) == len(set(e2))


def test_schema_fuer_bausteinvariante_ohne_entwurf():
    s = fall_c_schema(["Haustür"], list(BAUSTEINE), mit_entwurf=False)
    assert "rueckfrage_entwurf" not in s["required"] and "rueckfrage_entwurf" not in s["properties"]
    v = jsonschema.Draft202012Validator(s, format_checker=FC)
    assert v.is_valid({"anfragetyp": "Haustür", "vorhanden": [], "fehlend": ["Telefonnummer"],
                       "hinweise_fuer_bearbeitung": []})


def test_pruefung_bausteinvariante_ohne_falschwarnung():
    erg = {"anfragetyp": "Haustür", "vorhanden": [], "fehlend": ["Telefonnummer"], "rueckfrage_entwurf": None,
           "hinweise_fuer_bearbeitung": []}
    assert pruefe_entwurf(erg, variante="bausteine") == []
    assert pruefe_entwurf(dict(erg, rueckfrage_entwurf="Text"), variante="bausteine")


def test_normalisieren_casefold_und_leerraum():
    assert anfragetyp_normalisieren({"anfragetyp": " HAUSTÜR "}, ["Haustür"])["anfragetyp"] == "Haustür"


# ---------------------------------------------------------------- Fall B

def ab(**kw):
    p = dict(pos="1", artikelnr_lieferant="AB-123", bezeichnung="Schraube", menge=10, einheit="Stk",
             einzelpreis_netto=12.5, preiseinheit=None, rabatt_prozent=None, positionswert_netto=125.0,
             liefertermin="2026-11-10")
    p.update(kw.pop("p", {}))
    d = dict(bestellnummer="4711", lieferant="Müller Baubedarf GmbH", ab_datum="2026-10-20", positionen=[p],
             gesamtbetrag_netto=125.0, waehrung="EUR", hinweise=[], unvollstaendig_lesbar=False)
    d.update(kw)
    return d


def best(**kw):
    z = dict(artikelnr_lieferant="AB-123", menge=10, einheit="Stk", einzelpreis_netto=12.5, preiseinheit=None,
             rabatt_prozent=None, liefertermin="2026-11-10")
    z.update(kw.pop("z", {}))
    d = dict(bestellnummer="4711", lieferant="Müller Baubedarf GmbH", lieferant_domains=["mueller-baubedarf.de"],
             positionen=[z])
    d.update(kw)
    return d


ABS = "Müller Baubedarf <info@mueller-baubedarf.de>"


def test_grundfall_unauffaellig():
    assert jsonschema.Draft202012Validator(schemas.FALL_B_AUFTRAGSBESTAETIGUNG, format_checker=FC).is_valid(ab())
    assert abgleichen(ab(), best(), absender=ABS, authentifiziert=True).status == "unauffaellig"


def test_dmarc_false_markiert():
    r = abgleichen(ab(), best(), absender=ABS, authentifiziert=False)
    assert r.status == "markiert" and any("DMARC" in b for b in r.befunde)


@pytest.mark.parametrize("wert", ["fail", "none", "temperror", 0])
def test_dmarc_nicht_bool_wird_markiert(wert):
    assert abgleichen(ab(), best(), absender=ABS, authentifiziert=wert).status == "markiert"


def test_dmarc_nicht_uebergeben_bei_domainliste_wird_markiert():
    assert abgleichen(ab(), best(), absender=ABS).status == "markiert"


def test_dmarc_befund_auch_bei_abgebrochener_pruefung():
    r = abgleichen(ab(positionen=5), best(), absender=ABS, authentifiziert=False)
    assert r.status == "markiert"
    assert any("DMARC" in b for b in r.befunde)


def test_absender_fremde_domain_trotz_dmarc_pass():
    assert abgleichen(ab(), best(), absender="info@mueller-baubedarf.de.evil.com",
                      authentifiziert=True).status == "markiert"


def test_nan_im_bestellexport_wird_gemeldet():
    for k in ("menge", "einzelpreis_netto", "rabatt_prozent", "preiseinheit"):
        r = abgleichen(ab(p=dict(einzelpreis_netto=99.0, positionswert_netto=990.0), gesamtbetrag_netto=990.0),
                       best(z={k: float("nan")}), absender=ABS, authentifiziert=True)
        assert r.status == "markiert", k
        assert any("Bestellexport" in b for b in r.befunde), k


def test_nan_liefertermin_im_bestellexport_wird_gemeldet():
    r = abgleichen(ab(), best(z=dict(liefertermin=float("nan"))), absender=ABS, authentifiziert=True)
    assert r.status == "markiert"


def test_pandas_rezept_aus_liesmich():
    pd = pytest.importorskip("pandas")
    import io
    csv = ("artikelnr_lieferant;menge;einheit;einzelpreis_netto;preiseinheit;rabatt_prozent;liefertermin\n"
           "AB-123;10;Stk;12,5;;;2026-11-10\n")
    df = pd.read_csv(io.StringIO(csv), sep=";", decimal=",")
    zeilen = df.astype(object).where(df.notna(), None).to_dict("records")
    assert abgleichen(ab(), best(positionen=zeilen), absender=ABS, authentifiziert=True).status == "unauffaellig"


EXPORTTYPEN = {
    "Decimal-aus-SQL": dict(menge=Decimal("10"), einzelpreis_netto=Decimal("12.50")),
    "datetime.date": dict(liefertermin=datetime.date(2026, 11, 10)),
}


@pytest.mark.parametrize("z", EXPORTTYPEN.values(), ids=EXPORTTYPEN.keys())
def test_exporttypen_ohne_fehlalarm(z):
    assert abgleichen(ab(), best(z=z), absender=ABS, authentifiziert=True).status == "unauffaellig"


def test_bool_menge_im_export_wird_gemeldet():
    r = abgleichen(ab(p=dict(menge=1, positionswert_netto=12.5), gesamtbetrag_netto=12.5),
                   best(z=dict(menge=True)), absender=ABS, authentifiziert=True)
    assert r.status == "markiert"


@pytest.mark.parametrize("nr", ["AB-123", "ab-123", "AB‐123", "AB–123", " AB-123 "])
def test_artikelnummer_schreibweisen(nr):
    assert abgleichen(ab(p=dict(artikelnr_lieferant=nr)), best(), absender=ABS,
                      authentifiziert=True).status == "unauffaellig"


def test_artikelnummer_ohne_trenner_nur_aehnlich():
    r = abgleichen(ab(p=dict(artikelnr_lieferant="AB123")), best(), absender=ABS, authentifiziert=True)
    assert r.status == "markiert" and any("nur ähnlich" in b for b in r.befunde)


def test_artikelnummer_verschobener_trenner():
    assert _artnr("12-34") != _artnr("1-234")
    r = abgleichen(ab(p=dict(artikelnr_lieferant="A1-234")), best(z=dict(artikelnr_lieferant="A12-34")),
                   absender=ABS, authentifiziert=True)
    assert r.status == "markiert"


def test_artikelnummer_mehrdeutig_nicht_zugeordnet():
    b = best()
    b["positionen"] = [dict(b["positionen"][0], artikelnr_lieferant="12-34"),
                       dict(b["positionen"][0], artikelnr_lieferant="1-234")]
    r = abgleichen(ab(p=dict(artikelnr_lieferant="1234")), b, absender=ABS, authentifiziert=True)
    assert any("nicht bestellt" in x for x in r.befunde)


@pytest.mark.parametrize("ist", ["Möller Baubedarf GmbH", "Mül1er Baubedarf GmbH", "Müller Baubedarf Süd GmbH",
                                 "Müller GmbH"])
def test_lieferant_namensaehnlich_markiert(ist):
    assert abgleichen(ab(lieferant=ist), best(), absender=ABS, authentifiziert=True).status == "markiert"


@pytest.mark.parametrize("ist", ["MÜLLER BAUBEDARF GMBH", "Müller-Baubedarf GmbH", "Baubedarf Müller GmbH",
                                 "Mueller Baubedarf GmbH"])
def test_lieferant_schreibvarianten_unauffaellig(ist):
    assert _name_vergleich("Müller Baubedarf GmbH", ist) == "gleich"


@pytest.mark.parametrize("ist", ["Müller Baubedarf AG", "Müller Baubedarf KG", "Müller Baubedarf e.K."])
def test_lieferant_andere_rechtsform_markiert(ist):
    assert abgleichen(ab(lieferant=ist), best(), absender=ABS, authentifiziert=True).status == "markiert"


# ---------------------------------------------------------------- Fall A: Zeiterfassung

def bericht(personen, zusatz=()):
    return dict(baustelle_id="B1", abweichendes_datum_genannt=None, personen=personen, material=[],
                zusatzleistungen=list(zusatz), auffaelligkeiten=[], fehlende_angaben=[], unsichere_angaben=[])


P8 = [dict(mitarbeiter_id="M1", name_wie_genannt="Max", stunden=8)]


@pytest.mark.parametrize("wert", [float("nan"), None, "8,0", float("inf")])
def test_zeiterfassung_ungueltig_wird_gemeldet(wert):
    w = pruefe_bericht(bericht(P8), {"B1"}, {"M1"}, erfasste_stunden={"M1": wert})
    assert any("Zeiterfassung" in x for x in w)


def test_zeiterfassung_toleranz():
    assert pruefe_bericht(bericht(P8), {"B1"}, {"M1"}, erfasste_stunden={"M1": 8.25}) == []
    assert pruefe_bericht(bericht(P8), {"B1"}, {"M1"}, erfasste_stunden={"M1": 8.5})


def test_zeiterfassung_fehlender_eintrag():
    assert pruefe_bericht(bericht(P8), {"B1"}, {"M1"}, erfasste_stunden={})


def test_zusatzleistung_ueber_gemeldeter_arbeitszeit():
    w = pruefe_bericht(bericht([dict(mitarbeiter_id="M1", name_wie_genannt="Max", stunden=2)],
                               [dict(beschreibung="Extra", stunden=9)]), {"B1"}, {"M1"})
    assert any("übersteigen" in x for x in w)


def test_zeiterfassung_summe_je_person():
    p = [dict(mitarbeiter_id="M1", name_wie_genannt="Max", stunden=4),
         dict(mitarbeiter_id="M1", name_wie_genannt="Max", stunden=4)]
    w = pruefe_bericht(bericht(p), {"B1"}, {"M1"}, erfasste_stunden={"M1": 8})
    assert not any("in der Zeiterfassung" in x for x in w)
    assert any("mehrfach" in x for x in w)


def test_zeiterfassung_bool_ungueltig():
    w = pruefe_bericht(bericht(P8), {"B1"}, {"M1"}, erfasste_stunden={"M1": True})
    assert any("ohne gültigen Wert" in x for x in w)


def test_lieferant_haftungsbeschraenkt_zusatz():
    assert _name_vergleich("Müller Baubedarf UG (haftungsbeschränkt)", "Müller Baubedarf UG") == "gleich"
