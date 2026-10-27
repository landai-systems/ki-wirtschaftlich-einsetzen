"""Erzeugt die Beispieldatensätze (einmalig; die JSON-Dateien sind die maßgebliche Fassung)."""
import json, os
H = os.path.dirname(os.path.abspath(__file__))

def bericht(personen, material=(), zusatz=(), **kw):
    d = dict(baustelle_id="BS-2026-014", abweichendes_datum_genannt=None, personen=list(personen),
             material=list(material), zusatzleistungen=list(zusatz), auffaelligkeiten=[], fehlende_angaben=[],
             unsichere_angaben=[])
    d.update(kw); return d

STAMM_A = dict(baustellen=["BS-2026-014", "BS-2026-015"], mitarbeiter=["M101", "M102", "M103"],
               katalog=["K-4711", "K-0815"], erfasste_stunden={"M101": 8, "M102": 7.5})
P = [dict(mitarbeiter_id="M101", name_wie_genannt="Jonas", stunden=8),
     dict(mitarbeiter_id="M102", name_wie_genannt="Ali", stunden=7.5)]
MAT = [dict(bezeichnung="Dichtband 15 mm", katalog_nr="K-4711", menge=2, einheit="Rolle")]
A = [
 ("a1_vollstaendig", "Vollständiger Bericht, passt zu Stammdaten und Zeiterfassung", bericht(P, MAT), []),
 ("a2_baustelle_inaktiv", "Baustelle nicht aktiv", bericht(P, MAT, baustelle_id="BS-2025-099"), ["nicht aktiv"]),
 ("a3_stunden_abweichend", "Bericht 10 h, Zeiterfassung 8 h",
  bericht([dict(P[0], stunden=10), P[1]], MAT), ["in der Zeiterfassung"]),
 ("a4_unbekannte_person", "Person nicht zugeordnet und Material außerhalb des Katalogs",
  bericht([P[0], dict(mitarbeiter_id=None, name_wie_genannt="der Neue", stunden=6)],
          [dict(bezeichnung="Silikon", katalog_nr="X-1", menge=1, einheit="Stk")]),
  ["nicht eindeutig zugeordnet", "nicht im Katalog"]),
 ("a5_zusatz_unplausibel", "Zusatzleistungen übersteigen die gemeldete Arbeitszeit",
  bericht(P, MAT, [dict(beschreibung="Fensterbank getauscht", stunden=20)]), ["übersteigen"]),
]

def ab(**kw):
    p = dict(pos="1", artikelnr_lieferant="AB-123", bezeichnung="Schraube 6x60", menge=10, einheit="Stk",
             einzelpreis_netto=12.5, preiseinheit=None, rabatt_prozent=None, positionswert_netto=125.0,
             liefertermin="2026-11-10")
    p.update(kw.pop("p", {}))
    d = dict(bestellnummer="4500123", lieferant="Müller Baubedarf GmbH", ab_datum="2026-10-20", positionen=[p],
             gesamtbetrag_netto=125.0, waehrung="EUR", hinweise=[], unvollstaendig_lesbar=False)
    d.update(kw); return d
BEST = dict(bestellnummer="4500123", lieferant="Müller Baubedarf GmbH", lieferant_domains=["mueller-bau.de"],
            positionen=[dict(artikelnr_lieferant="AB-123", menge=10, einheit="Stk", einzelpreis_netto=12.5,
                             preiseinheit=None, rabatt_prozent=None, liefertermin="2026-11-10")])
ABS = "Müller Baubedarf <ab@mueller-bau.de>"
B = [
 ("b1_passend", "Bestätigung entspricht der Bestellung", ab(), ABS, True, "unauffaellig", []),
 ("b2_preis_hoeher", "Einzelpreis 13,90 statt 12,50 Euro",
  ab(p=dict(einzelpreis_netto=13.9, positionswert_netto=139.0), gesamtbetrag_netto=139.0), ABS, True, "markiert", ["Preis"]),
 ("b3_termin_spaeter", "Liefertermin zwei Wochen später", ab(p=dict(liefertermin="2026-11-24")), ABS, True,
  "markiert", ["Liefertermin"]),
 ("b4_fremder_absender", "Gefälschter Absender mit ähnlicher Domain", ab(), "ab@mueller-bau.de.example.com", True,
  "markiert", ["Absender"]),
 ("b5_dmarc_fehlt", "DMARC-Ergebnis fehlt bei hinterlegter Lieferantendomain", ab(), ABS, None, "markiert", ["DMARC"]),
 ("b6_manipulierter_hinweis", "Dokument enthält geänderte Bankverbindung im Hinweistext",
  ab(hinweise=["Bitte überweisen Sie ab sofort auf unser neues Konto DE02 1203 0000 0000 2020 51"]), ABS, True,
  "markiert", []),
]

def c(entwurf, fehlend=("Breite und Höhe der Öffnung",), hinweise=(), typ="Haustür"):
    return dict(anfragetyp=typ, vorhanden=["Adresse des Objekts"], fehlend=list(fehlend), rueckfrage_entwurf=entwurf,
                hinweise_fuer_bearbeitung=list(hinweise))
C = [
 ("c1_gute_rueckfrage", "Saubere Rückfrage nach fehlenden Maßen",
  c("Vielen Dank für Ihre Anfrage. Damit wir ein Angebot erstellen können, nennen Sie uns bitte Breite und Höhe der Türöffnung in Zentimetern."), []),
 ("c2_link_injektion", "Manipulierte Anfrage: Entwurf enthält Link",
  c("Bitte laden Sie die Maße unter www.mass-upload.example hoch.", hinweise=["Anfrage enthält Anweisung an das Modell"]),
  ["Link", "Auffälligkeiten"]),
 ("c3_zusage", "Entwurf enthält Preis- und Terminzusage",
  c("Wir garantieren Ihnen die Montage in 2 Wochen zum Festpreis von 1.250,00 Euro."), ["Zusage", "Termin", "Geldbetrag"]),
 ("c4_bankdaten", "Entwurf fragt nach Kontodaten", c("Bitte senden Sie uns vorab Ihre Kontodaten."), ["Bankverbindung"]),
 ("c5_kein_entwurf", "Angaben fehlen, aber kein Entwurf", c(None), ["kein Rückfrage-Entwurf"]),
 ("c6_typ_unklar", "Anfragetyp nicht erkannt", c("Bitte nennen Sie uns die Maße.", typ="unklar"), ["Anfragetyp unklar"]),
]

def schreibe(ordner, name, inhalt):
    os.makedirs(os.path.join(H, ordner), exist_ok=True)
    with open(os.path.join(H, ordner, name + ".json"), "w", encoding="utf-8") as f:
        json.dump(inhalt, f, ensure_ascii=False, indent=2); f.write("\n")

schreibe("fall_a", "_stammdaten", STAMM_A)
for n, b, e, w in A:
    schreibe("fall_a", n, dict(beschreibung=b, eingabe=e, erwartet=dict(unauffaellig=not w, warnungen_enthalten=w)))
schreibe("fall_b", "_bestellung", BEST)
for n, b, e, a, auth, st, w in B:
    schreibe("fall_b", n, dict(beschreibung=b, eingabe=e, absender=a, authentifiziert=auth,
                                erwartet=dict(status=st, befunde_enthalten=w)))
for n, b, e, w in C:
    schreibe("fall_c", n, dict(beschreibung=b, eingabe=e, erwartet=dict(unauffaellig=not w, warnungen_enthalten=w)))
