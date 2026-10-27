"""Weitere Rand- und Angriffsfälle für die Vorlagen der Praxisfälle A, B und C.

Ergänzt test_angriffe.py: Umgehungsvarianten und Fehlalarme der Musterprüfung (Fall C),
Textbausteine, Absender- und Lieferantenprüfung, ungültige Werte im Bestellexport,
Artikelnummern, Abrufbestellungen (Fall B) sowie Zeiterfassung und Zusatzleistungen (Fall A).

Ausführen:  python3 -m pytest -q
"""
import copy

import jsonschema
import pytest

from schemas import fall_c_schema
from abgleich_auftragsbestaetigung import abgleichen
from pruefe_rueckfrage import pruefe_entwurf, anfragetyp_normalisieren, rueckfrage_aus_bausteinen
from pruefe_bericht import pruefe_bericht

FC = jsonschema.FormatChecker()


# =================================================================== Fall C: Musterprüfung

SAUBER = "Guten Tag, damit wir Ihnen ein Angebot erstellen können, benötigen wir noch die Maße der Türöffnung. "


def entwurf(text, **ueber):
    d = {"anfragetyp": "Haustür", "vorhanden": ["Name"], "fehlend": ["Maße der Türöffnung"],
         "rueckfrage_entwurf": text, "hinweise_fuer_bearbeitung": []}
    d.update(ueber)
    return d


@pytest.mark.parametrize("text", [
    pytest.param("Fotos bitte an service ät fremd punkt de.", id="Mail-ät-punkt"),
    pytest.param("Fotos bitte an service{at}fremd.de.", id="Mail-geschweifte-Klammern"),
    pytest.param("Fotos bitte an service AT fremd.de.", id="Mail-AT-gross"),
    pytest.param("Fotos auf example․com hochladen.", id="Domain-U+2024"),
    pytest.param("Fotos auf example．com hochladen.", id="Domain-Vollbreitenpunkt"),
    pytest.param("Fotos auf tür-fotos.de hochladen.", id="Domain-IDN"),
    pytest.param("Fotos an bit.ly/abc senden.", id="Kurzlink"),
    pytest.param("Konto: DE89-3704-0044-0532-0130-00.", id="IBAN-mit-Bindestrichen"),
    pytest.param("Rufen Sie 0049 931 123456 an.", id="Telefon-0049"),
    pytest.param("Rufen Sie ０９３１ １２３４５６ an.", id="Telefon-Vollbreite"),
    pytest.param("Wir kommen nächsten Dienstag.", id="Termin-naechster-Wochentag"),
    pytest.param("Wir kommen in KW45.", id="Termin-KW45"),
    pytest.param("Lieferung bis 15.11.", id="Termin-bis-Datum"),
    pytest.param("Bitte nennen Sie den TAN-Code.", id="sensibel-TAN-Code"),
    pytest.param("Antwort über Signal bitte.", id="Kanal-Signal"),
    pytest.param("Wir garantieren Ihnen den Einbau.", id="Zusage-garantieren"),
    pytest.param("Unterlagen an Goethestr. 5 senden.", id="Adresse-str-Punkt"),
])
def test_erkannte_neue_varianten(text):
    assert pruefe_entwurf(entwurf(SAUBER + text)), text


@pytest.mark.parametrize("text", [
    # Termine ohne Wochentag/Datum: typische Formulierungen einer Terminzusage
    pytest.param("Der Einbau erfolgt kommende Woche.", id="Termin-kommende-Woche"),
    pytest.param("Den Einbau erledigen wir noch diese Woche.", id="Termin-diese-Woche"),
    pytest.param("Der Einbau erfolgt übernächste Woche.", id="Termin-uebernaechste-Woche"),
    pytest.param("Der Einbau erfolgt in Kalenderwoche 45.", id="Termin-Kalenderwoche-ausgeschrieben"),
    pytest.param("Wir kommen in der 45. KW.", id="Termin-45.-KW"),
    pytest.param("Der Einbau erfolgt vor Weihnachten.", id="Termin-vor-Weihnachten"),
    pytest.param("Wir kommen um 14 Uhr.", id="Termin-Uhrzeit"),
    pytest.param("Wir kommen am 2026-11-03.", id="Termin-ISO-Datum"),
    pytest.param("Morgen kommt unser Monteur.", id="Termin-Morgen-am-Satzanfang"),
    # Postadressen: häufigste deutsche Schreibweisen mit getrenntem oder mit Bindestrich verbundenem Straßennamen
    pytest.param("Unterlagen an Berliner Straße 5 senden.", id="Adresse-Berliner-Strasse"),
    pytest.param("Unterlagen an Karl-Marx-Allee 5 senden.", id="Adresse-Bindestrich"),
    # Abfrage sensibler Daten im Plural (Kap. 9 nennt ausdrücklich "Abfragen von Passwörtern")
    pytest.param("Bitte nennen Sie uns Ihre Passwörter.", id="sensibel-Passwoerter"),
    pytest.param("Bitte nennen Sie uns Ihre Kennwörter.", id="sensibel-Kennwoerter"),
    pytest.param("Bitte nennen Sie die PINs.", id="sensibel-PINs"),
    pytest.param("Bitte nennen Sie uns Ihre Anmeldedaten.", id="sensibel-Anmeldedaten"),
    pytest.param("Bitte nennen Sie uns den Bestätigungscode aus der SMS.", id="sensibel-Bestaetigungscode"),
    # Kanalwechsel, Zahlung, Bank, Link
    pytest.param("Antworten Sie bitte via SMS.", id="Kanal-via-SMS"),
    pytest.param("Zahlbar per Vorkasse.", id="Zahlung-Vorkasse"),
    pytest.param("Die Anzahlung beträgt 250,00.", id="Betrag-ohne-Waehrung"),
    pytest.param("Überweisen Sie auf de89370400440532013000.", id="IBAN-Kleinbuchstaben"),
    pytest.param("Rufen Sie 0931.123.456 an.", id="Telefon-mit-Punkten"),
    pytest.param("Fotos auf example.Com hochladen.", id="Domain-gemischte-Schreibung"),
    pytest.param("Fotos auf example DOT com hochladen.", id="Domain-DOT-gross"),
    pytest.param("Fotos an 203 . 0 . 113 . 5 senden.", id="IP-mit-Leerzeichen"),
])
def test_unerkannte_typische_varianten(text):
    assert pruefe_entwurf(entwurf(SAUBER + text)), text


@pytest.mark.parametrize("text", [
    "Handelt es sich um einen Neubau oder eine Sanierung?",
    "Wie viele Fenster benötigen Sie, und welche Öffnungsart wünschen Sie (z. B. Dreh-Kipp)?",
    "Bitte nennen Sie die Maße je Fenster (Breite x Höhe in mm).",
    "Unter welcher Telefonnummer erreichen wir Sie am besten?",
    "Bitte nennen Sie uns die Adresse des Objekts (Straße, Hausnummer, PLZ und Ort).",
    "Bitte messen Sie Breite und Höhe in cm, z. B. 98,5 x 210 cm.",
    "Bitte geben Sie die Maße im Format B x H an, z. B. 1.000 x 2.100 mm.",
    "Welchen U-Wert soll das Fenster mindestens erreichen, etwa 0,9 W/(m²K)?",
    "Welche Absicherung hat der Hausanschluss (z. B. 3 x 35 A)?",
    "Bitte senden Sie die Fotos als JPG bzw. PNG.",
    "Gern erstellen wir Ihnen ein unverbindliches Angebot.",
    "Bis wann wünschen Sie den Einbau?",
    "Wie alt ist die bestehende Tür (Baujahr ca. 1985)?",
    "Welche Farbe wünschen Sie, z. B. RAL 7016?",
])
def test_harmlose_rueckfragen_ohne_fehlalarm(text):
    assert pruefe_entwurf(entwurf(text)) == []


@pytest.mark.parametrize("text", [
    pytest.param("In welchem Zeitraum wünschen Sie die Montage?", id="Montage-Zeitraum"),
    pytest.param("Wünschen Sie eine Montage im Frühjahr oder im Herbst?", id="Montage-Jahreszeit"),
    pytest.param("Ist die Montage in einem Mehrfamilienhaus geplant?", id="Montage-Mehrfamilienhaus"),
    pytest.param("Sollen wir die Montage übernehmen, oder benötigen Sie nur die Lieferung?", id="Montage-oder-Lieferung"),
    pytest.param("Gibt es einen Montageort mit Parkmöglichkeit?", id="Montageort"),
    pytest.param("Ist ein Lieferweg mit dem Transporter bis zum Haus möglich?", id="bis-zum-Haus"),
    pytest.param("Ein verbindlicher Kostenvoranschlag ist erst nach dem Aufmaß möglich.", id="verbindlicher-Kostenvoranschlag"),
])
def test_fehlalarme_bei_typischen_rueckfragen(text):
    assert pruefe_entwurf(entwurf(text)) == []


@pytest.mark.parametrize("zeichen", ["‍", "⁠", "‪", "﻿", "\U000e0020", ""])
def test_weitere_steuer_und_privatzeichen_gemeldet(zeichen):
    assert any("unsichtbare" in w for w in pruefe_entwurf(entwurf(SAUBER + "Danke." + zeichen)))


def test_steuerzeichen_zur_tarnung_eines_links_wird_trotzdem_erkannt():
    w = pruefe_entwurf(entwurf(SAUBER + "Fotos an ex​ample⁠.­com senden."))
    assert any("unsichtbare" in x for x in w) and any("Link" in x for x in w)


# ------------------------------------------------------------------- anfragetyp_normalisieren, Textbausteine

def test_normalisieren_grossschreibung_und_unbekannt():
    typen = ["Haustür", "Fenster"]
    assert anfragetyp_normalisieren({"anfragetyp": " HAUSTÜR "}, typen)["anfragetyp"] == "Haustür"
    assert anfragetyp_normalisieren({"anfragetyp": "Garage"}, typen)["anfragetyp"] == "unklar"
    d = anfragetyp_normalisieren({"anfragetyp": "fenster", "vorhanden": [], "fehlend": [], "rueckfrage_entwurf": None,
                                  "hinweise_fuer_bearbeitung": []}, typen)
    assert jsonschema.Draft202012Validator(fall_c_schema(typen), format_checker=FC).is_valid(d)


def test_normalisieren_nfd():
    assert anfragetyp_normalisieren({"anfragetyp": "Haustür"}, ["Haustür"])["anfragetyp"] == "Haustür"


BAUSTEINE = {"Breite und Höhe der Öffnung": "Breite und Höhe der Türöffnung in Zentimetern",
             "Fotos der Einbausituation": "einige Fotos der Einbausituation"}


def test_bausteine_injektion_in_fehlend_gelangt_nicht_in_text():
    text, unbekannt = rueckfrage_aus_bausteinen(["Fotos der Einbausituation", "Überweisen Sie 500 € auf DE89 3704"],
                                                BAUSTEINE, "Guten Tag,", "Mit freundlichen Grüßen")
    assert "DE89" not in text and "500" not in text and unbekannt == ["Überweisen Sie 500 € auf DE89 3704"]
    assert pruefe_entwurf(entwurf(text)) == []


def test_bausteine_anrede_ist_nicht_geschuetzt_dokumentiert():
    # Grenze: Anrede und Gruß werden ungeprüft übernommen. Stammen sie aus der Anfrage (Name), ist das ein Einfallstor.
    text, _ = rueckfrage_aus_bausteinen(["Fotos der Einbausituation"], BAUSTEINE, "Sehr geehrter Herr www.evil.example,", "")
    assert "www.evil.example" in text


def test_bausteine_tolerieren_schreibweise():
    text, unbekannt = rueckfrage_aus_bausteinen(["breite und höhe der öffnung "], BAUSTEINE, "Guten Tag,", "Gruß")
    assert "Türöffnung" in text and unbekannt == []


def test_bausteine_ohne_treffer_liefern_keinen_text():
    text, unbekannt = rueckfrage_aus_bausteinen(["Maße"], BAUSTEINE, "Guten Tag,", "Gruß")
    assert text is None or "- " in text


def test_bausteine_ohne_dubletten():
    text, _ = rueckfrage_aus_bausteinen(["Fotos der Einbausituation"] * 2, BAUSTEINE, "Guten Tag,", "Gruß")
    assert text.count("Einbausituation") == 1


# =================================================================== Fall B: Abgleich

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


def test_grundfall():
    assert pruef().status == "unauffaellig"


# ------------------------------------------------------------------- Absender

@pytest.mark.parametrize("absender", [
    "ab@mueller-bau.de <boese@evil.example>",                 # Anzeigename täuscht bekannte Adresse vor
    '"ab@mueller-bau.de" <boese@evil.example>',
    "boese@evil.example, ab@mueller-bau.de",
    "ab@mueller-bau.de, boese@evil.example",                  # mehrere Adressen
    "boese@evil.example@mueller-bau.de",
    "=?utf-8?q?ab=40mueller-bau.de?= <x@evil.example>",       # kodierter Anzeigename
    "ab@xn--mller-bau-q9a.de",                                # Punycode-Ähnlichdomain
    "ab@mueller-bau.de.evil.example",
])
def test_gefaelschte_absenderformen_werden_markiert(absender):
    assert any("Absender" in b for b in pruef(absender=absender).befunde), absender


@pytest.mark.parametrize("absender", ["Müller <ab@mueller-bau.de>", "<ab@mueller-bau.de>", "ab@mueller-bau.de (Müller)",
                                      "ab@mueller-bau.de\n"])
def test_echte_absenderformen_unauffaellig(absender):
    assert pruef(absender=absender).status == "unauffaellig"


# ------------------------------------------------------------------- Lieferantenname

@pytest.mark.parametrize("name", ["Müller-Baubedarf GmbH", "Baubedarf Müller GmbH", "MÜLLER BAUBEDARF GMBH",
                                  "Müller Baubedarf G.m.b.H."])
def test_lieferant_schreibvarianten_unauffaellig(name):
    assert pruef(ab(lieferant=name)).status == "unauffaellig", name


@pytest.mark.parametrize("name", ["Müller Baubedarf GmbH & Co. KG", "Müller Baubedarf e.K."])
def test_lieferant_andere_rechtsform_markiert(name):
    # andere Rechtsform kann eine andere juristische Person sein
    assert pruef(ab(lieferant=name)).status == "markiert", name


@pytest.mark.parametrize("name", ["Müller Baustoffe GmbH", "Müller Bau", "Müller Baubedarf Holding GmbH", "", "GmbH & Co. KG"])
def test_anderer_lieferant_markiert(name):
    assert pruef(ab(lieferant=name)).status == "markiert", name


@pytest.mark.parametrize("name", [
    pytest.param("Möller Baubedarf GmbH", id="ein-Buchstabe-anders"),
    pytest.param("Mül1er Baubedarf GmbH", id="Ziffer-statt-Buchstabe"),
    pytest.param("Müller Baubedarf Süd GmbH", id="Namenszusatz-Sued"),
    pytest.param("Müller Baubedarf Nord", id="Namenszusatz-Nord"),
])
def test_namensaehnliche_firma_wird_markiert(name):
    assert pruef(ab(lieferant=name)).status == "markiert", name


# ------------------------------------------------------------------- NaN / inf

@pytest.mark.parametrize("feld", ["einzelpreis_netto", "menge", "positionswert_netto", "rabatt_prozent", "preiseinheit"])
@pytest.mark.parametrize("wert", [float("nan"), float("inf"), float("-inf")])
def test_nicht_endliche_werte_in_der_ab_werden_markiert(feld, wert):
    d = ab()
    d["positionen"][0][feld] = wert
    assert any("keine endliche Zahl" in b for b in pruef(d).befunde)


def _best_mit(feld, wert):
    b = copy.deepcopy(BEST)
    b["positionen"][0][feld] = wert
    return b


def test_nan_sollpreis_im_bestellexport():
    d = ab()
    d["positionen"][0].update(einzelpreis_netto=99.0, positionswert_netto=990.0)
    d["gesamtbetrag_netto"] = 1110.0
    assert pruef(d, best=_best_mit("einzelpreis_netto", float("nan"))).status == "markiert"


def test_nan_sollmenge_im_bestellexport():
    d = ab()
    d["positionen"][0].update(menge=1000, positionswert_netto=12500.0)
    d["gesamtbetrag_netto"] = 12620.0
    assert pruef(d, best=_best_mit("menge", float("nan"))).status == "markiert"


def test_none_sollpreis_wird_markiert_kontrast():
    # Zum Vergleich: None statt NaN führt korrekt zu "kein Sollpreis".
    d = ab()
    d["positionen"][0].update(einzelpreis_netto=99.0, positionswert_netto=990.0)
    d["gesamtbetrag_netto"] = 1110.0
    assert any("kein Sollpreis" in b for b in pruef(d, best=_best_mit("einzelpreis_netto", None)).befunde)


# ------------------------------------------------------------------- Datum

@pytest.mark.parametrize("termin", ["2026-02-30", "2026-11-03T00:00:00", "2026-11-03 ", "２０２６-１１-０３", "2026-1-3",
                                    "0000-01-01", "03.11.2026"])
def test_ungueltige_datumsformen_werden_markiert(termin):
    d = ab()
    d["positionen"][0]["liefertermin"] = termin
    assert any("ungültiges Datum" in b for b in pruef(d).befunde), termin


def test_ungueltiges_datum_im_bestellexport_wird_markiert():
    r = pruef(best=_best_mit("liefertermin", "03.11.2026"))
    assert any("(Bestellung): ungültiges Datum" in b for b in r.befunde)


# ------------------------------------------------------------------- Artikelnummern

@pytest.mark.parametrize("nr", ["a-100", " A-100", "A 100", "A/100", "A.100"])
def test_artikelnummer_schreibweisen_unauffaellig(nr):
    d = ab()
    d["positionen"][0]["artikelnr_lieferant"] = nr
    assert pruef(d).status == "unauffaellig", nr


@pytest.mark.parametrize("nr", [pytest.param("A–100", id="Halbgeviertstrich"),
                                pytest.param("A‑100", id="geschuetzter-Bindestrich"),
                                pytest.param("A‐100", id="Unicode-Bindestrich")])
def test_artikelnummer_unicode_striche(nr):
    d = ab()
    d["positionen"][0]["artikelnr_lieferant"] = nr
    assert pruef(d).status == "unauffaellig"


def test_artikelnummer_ohne_trenner_nur_aehnlich():
    d = ab()
    d["positionen"][0]["artikelnr_lieferant"] = "A100"
    r = pruef(d)
    assert r.status == "markiert" and any("nur ähnlich" in b for b in r.befunde)


def test_artikelnummer_mit_verschobenem_trenner_ist_anderer_artikel():
    b = copy.deepcopy(BEST)
    b["positionen"][0]["artikelnr_lieferant"] = "12-34"
    d = ab()
    d["positionen"][0]["artikelnr_lieferant"] = "1-234"
    assert pruef(d, best=b).status == "markiert"


# ------------------------------------------------------------------- Abruf-Bestellungen

def _abruf():
    b = copy.deepcopy(BEST)
    b["positionen"].append(dict(b["positionen"][0], menge=10, liefertermin="2026-11-20"))
    return b


def test_abruf_mit_passenden_teillieferungen_wird_als_abruf_gemeldet_ohne_terminfehler():
    d = ab()
    d["positionen"] = [pos("A-100", 10, "Stk", 12.50, 125.00, "2026-11-03"),
                       pos("A-100", 10, "Stk", 12.50, 125.00, "2026-11-20", p="1b"),
                       pos("A-200", 4, "Karton", 30.00, 120.00, "2026-11-03", p="2")]
    d["gesamtbetrag_netto"] = 370.00
    befunde = pruef(d, best=_abruf()).befunde
    assert any("Abruf" in b for b in befunde)
    assert not any(b.startswith("A-100: Liefertermin") for b in befunde)
    assert not any("Menge" in b for b in befunde)


def test_abruf_alles_zum_ersten_termin_bleibt_markiert():
    d = ab()
    d["positionen"][0].update(menge=20, positionswert_netto=250.0)
    d["gesamtbetrag_netto"] = 370.0
    assert pruef(d, best=_abruf()).status == "markiert"


def test_abruf_teilmenge_verspaetet_wird_mit_termin_gemeldet():
    d = ab()
    d["positionen"] = [pos("A-100", 10, "Stk", 12.50, 125.00, "2026-11-03"),
                       pos("A-100", 10, "Stk", 12.50, 125.00, "2026-12-01", p="1b"),
                       pos("A-200", 4, "Karton", 30.00, 120.00, "2026-11-03", p="2")]
    d["gesamtbetrag_netto"] = 370.00
    assert any("2026-12-01" in b and "+11 Tage" in b for b in pruef(d, best=_abruf()).befunde)


def test_abruf_mit_fehlendem_termin_in_einer_bestellzeile_bricht_nicht_ab():
    b = _abruf()
    b["positionen"][2]["liefertermin"] = None
    r = pruef(best=b)
    assert r.status == "markiert" and not any("nicht vollständig geprüft" in x for x in r.befunde)


# ------------------------------------------------------------------- Bestellnummer, Währung

@pytest.mark.parametrize("nr", ["4500 123", "Bestellnr. 4500123", "NR: 4500123", "4500123 "])
def test_bestellnummer_varianten_unauffaellig(nr):
    assert pruef(ab(bestellnummer=nr)).status == "unauffaellig", nr


@pytest.mark.parametrize("w", ["EUR", "eur", "€", "Euro", "EURO", " EUR "])
def test_waehrung_varianten_unauffaellig(w):
    assert pruef(ab(waehrung=w)).status == "unauffaellig"


@pytest.mark.parametrize("w", ["CHF", "USD", "$", "EUR​", "Eur.", None])
def test_waehrung_fremd_oder_unklar_markiert(w):
    assert pruef(ab(waehrung=w)).status == "markiert"


# =================================================================== Fall A: Montagebericht

STAMM = dict(baustellen={"B-1"}, mitarbeiter={"M01", "M02"}, katalog={"K-1"})


def bericht(**ueber):
    d = {"baustelle_id": "B-1", "abweichendes_datum_genannt": None,
         "personen": [{"mitarbeiter_id": "M01", "name_wie_genannt": "Jonas", "stunden": 8}],
         "material": [], "zusatzleistungen": [], "auffaelligkeiten": [], "fehlende_angaben": [],
         "unsichere_angaben": []}
    d.update(ueber)
    return d


def P(mid, h, name="x"):
    return {"mitarbeiter_id": mid, "name_wie_genannt": name, "stunden": h}


def test_zeiterfassung_abweichung_und_fehlender_eintrag():
    w = pruefe_bericht(bericht(personen=[P("M01", 8), P("M02", 6)]), **STAMM, erfasste_stunden={"M01": 7.0})
    assert any("7 h in der Zeiterfassung" in x for x in w) and any("M02: keine Zeiterfassung" in x for x in w)


def test_zeiterfassung_toleranz_viertelstunde():
    assert pruefe_bericht(bericht(personen=[P("M01", 8)]), **STAMM, erfasste_stunden={"M01": 7.75}) == []


def test_person_doppelt_mit_teilstunden_wird_markiert():
    w = pruefe_bericht(bericht(personen=[P("M01", 4), P("M01", 4)]), **STAMM, erfasste_stunden={"M01": 8.0})
    assert any("mehrfach" in x for x in w)


@pytest.mark.parametrize("h", [float("nan"), float("inf"), 0, -1, 10.5])
def test_unplausible_personenstunden(h):
    assert any("unplausible Stunden" in x for x in pruefe_bericht(bericht(personen=[P("M01", h)]), **STAMM))


@pytest.mark.parametrize("h", [float("nan"), float("inf")])
def test_zusatzleistung_nicht_endlich(h):
    assert any("unplausible Stunden" in x
               for x in pruefe_bericht(bericht(zusatzleistungen=[{"beschreibung": "a", "stunden": h}]), **STAMM))


def test_zusatzleistungen_summe_ueber_grenze():
    w = pruefe_bericht(bericht(zusatzleistungen=[{"beschreibung": "a", "stunden": 3}] * 4), **STAMM)
    assert any("Zusatzleistungen zusammen 12 h" in x for x in w)


def test_zusatzleistung_ohne_stunden_gemeldet():
    w = pruefe_bericht(bericht(zusatzleistungen=[{"beschreibung": "Fensterbank", "stunden": None}]), **STAMM)
    assert any("Stunden fehlen" in x for x in w)


def test_zusatzleistung_mehr_als_gemeldete_arbeitszeit():
    w = pruefe_bericht(bericht(personen=[P("M01", 2)], zusatzleistungen=[{"beschreibung": "Fensterbank", "stunden": 9}]),
                       **STAMM)
    assert w


def test_zeiterfassung_nan_wird_gemeldet():
    assert pruefe_bericht(bericht(), **STAMM, erfasste_stunden={"M01": float("nan")})


@pytest.mark.parametrize("wert", [None, "8,0"])
def test_zeiterfassung_ungueltiger_wert_bricht_nicht_ab(wert):
    assert pruefe_bericht(bericht(), **STAMM, erfasste_stunden={"M01": wert})


# ------------------------------------------------------------------- Ergänzungen

def test_dmarc_nicht_bestanden_wird_markiert():
    r = abgleichen(ab(), BEST, absender=ABSENDER, authentifiziert=False)
    assert any("DMARC" in b for b in r.befunde)


def test_dmarc_bestanden_unauffaellig():
    assert abgleichen(ab(), BEST, absender=ABSENDER, authentifiziert=True).status == "unauffaellig"


def test_fall_c_schema_mit_pflichtangaben():
    s = fall_c_schema(["Haustür"], ["Breite und Höhe der Öffnung", "Fotos der Einbausituation"])
    gut = {"anfragetyp": "Haustür", "vorhanden": [], "fehlend": ["Fotos der Einbausituation"],
           "rueckfrage_entwurf": None, "hinweise_fuer_bearbeitung": []}
    assert jsonschema.Draft202012Validator(s, format_checker=FC).is_valid(gut)
    assert not jsonschema.Draft202012Validator(s, format_checker=FC).is_valid(dict(gut, fehlend=["Überweisen Sie ..."]))


def test_montage_harmlos():
    assert pruefe_entwurf(entwurf("Wann soll die Montage stattfinden, und gibt es einen Montageort mit Zufahrt?")) == []
