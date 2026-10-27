# Datenübergaben

Die Programme in diesem Paket sind **lokale Prüfschritte**. Sie erhalten bereits vorliegende Daten als
Python-Objekte (`dict`) oder über `pruefen.py` als JSON-Dateien und geben Meldungen zurück. Alles andere ist
**betriebliche Integration** und Aufgabe des Ablaufwerkzeugs (Automatisierungsdienst oder eigenes Programm):

| Schritt | Zuständig |
| --- | --- |
| Daten abholen (Postfach, App, Formular, Warenwirtschaft) | Integration |
| Spracherkennung, Aufruf des Sprachmodells mit Anweisung und Schema | Integration |
| Modellausgabe gegen Schema validieren, Abbruchgrund prüfen | Integration oder `pruefen.py` |
| Fachliche Prüfung, Befunde erzeugen | **dieses Paket** |
| Ergebnis anzeigen, Freigabe durch einen Menschen | Integration |
| Übergabe in Abrechnung, Warenwirtschaft oder Versand | Integration, erst nach Freigabe |

## Fall A: Montagebericht

**Eingabe 1 – Modellausgabe** nach `fall_a_montagebericht.schema.json`: `baustelle_id`, `abweichendes_datum_genannt`,
`personen[]` (mitarbeiter_id, name_wie_genannt, stunden), `material[]`, `zusatzleistungen[]`, `auffaelligkeiten`,
`fehlende_angaben`, `unsichere_angaben`.

**Eingabe 2 – Stammdaten** (Format von `beispiele/fall_a/_stammdaten.json`): `baustellen` (aktive Kennungen),
`mitarbeiter` (Personalnummern), optional `katalog` und `erfasste_stunden` (`{Personalnummer: Stunden}`).

**Ausgabe:** Liste von Warnungen; leer = unauffällig. Über `pruefen.py`: `{"status", "meldungen"}`.

## Fall B: Auftragsbestätigung

**Eingabe 1 – Modellausgabe** nach `fall_b_auftragsbestaetigung.schema.json`.

**Eingabe 2 – Bestellung** aus dem Export der Warenwirtschaft (Format von `beispiele/fall_b/_bestellung.json`):
`bestellnummer`, `lieferant`, `lieferant_domains`, `positionen[]` mit `artikelnr_lieferant`, `menge`, `einheit`,
`einzelpreis_netto`, `preiseinheit`, `rabatt_prozent`, `liefertermin`. Zahlen als int, float oder Decimal, Termine
als `date` oder `"JJJJ-MM-TT"`, leere Felder als `None`/`null`. Die Bestellung sucht das Ablaufwerkzeug über die
ausgelesene Bestellnummer.

**Eingabe 3 – Herkunft:** Absenderadresse und Ergebnis der DMARC-Prüfung des Mailservers (`True` nur bei
`dmarc=pass`). Fehlt das Ergebnis bei hinterlegten Lieferantendomains, wird markiert.

**Ausgabe:** `Ergebnis(status, befunde)` mit `status` = `unauffaellig` oder `markiert`.

## Fall C: Kundenanfrage

**Eingabe – Modellausgabe** nach `fall_c_anfrage.schema.json` oder, für die Textbaustein-Variante,
`fall_c_schema(typen, pflichtangaben, mit_entwurf=False)`.

**Textbausteine:** `rueckfrage_aus_bausteinen(fehlend, bausteine, anrede, gruss)` gibt `(text, unbekannte_angaben)`
zurück. Anrede und Gruß nur aus festen Vorlagen, nie aus der Anfrage.

**Ausgabe:** Liste von Warnungen; der Entwurf geht nie automatisch hinaus.
