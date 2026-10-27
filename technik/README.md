# Technikpaket: Prüfprogramme, Prompts und Schemas

Für IT-Mitarbeiter, Automatisierungsdienstleister und technisch erfahrene Unternehmer. Die Dateien sind
**Ausgangspunkte** für ein Pilotprojekt nach Kapitel 7 bis 9 und 11 des Buches, keine fertige Software.

## Inhalt

| Datei / Ordner | Zweck |
| --- | --- |
| `anweisungen/` | Prompts (Systemanweisungen) für Fall A, B und C; für Fall C zwei Varianten: Modell-Entwurf und Textbausteine (empfohlen) |
| `*.schema.json`, `schemas.py` | JSON-Schemas der strukturierten Modellausgaben; `fall_c_schema()` erzeugt betriebsspezifische Fassungen |
| `pruefe_bericht.py` | Fall A: Plausibilitätsprüfung eines ausgelesenen Montageberichts gegen Stammdaten und Zeiterfassung |
| `abgleich_auftragsbestaetigung.py` | Fall B: regelbasierter Abgleich Auftragsbestätigung gegen Bestellung, Herkunfts- und DMARC-Prüfung |
| `pruefe_rueckfrage.py` | Fall C: Musterprüfung von Rückfrage-Entwürfen, Rückfrage aus freigegebenen Textbausteinen |
| `pruefen.py` | Kommandozeile für alle drei Prüfungen mit Dateiimport, Schemaprüfung und Rückgabewerten |
| `beispiele/` | konstruierte Testdatensätze mit erwartetem Ergebnis, darunter Negativ- und Angriffsfälle |
| `test_*.py` | automatische Tests |
| `DATENUEBERGABEN.md` | Ein- und Ausgabeformate, Abgrenzung zur betrieblichen Integration |
| `FEHLERBEHANDLUNG.md` | Verhalten bei Fehlern, ungültigen Daten und Manipulationsversuchen |

## Installation und Ausführung

Voraussetzung: Python 3.10 oder neuer. Die Prüfprogramme selbst nutzen nur die Standardbibliothek;
`jsonschema` (Schemaprüfung) und `pytest` (Tests) sind die einzigen Zusatzpakete.

```
cd technik                                        # bzw. den entpackten Ordner des Technikpakets
python -m venv .venv
.venv/bin/pip install -r requirements.txt        # Windows: .venv\Scripts\pip install -r requirements.txt
.venv/bin/python -m pytest                       # alle Tests
.venv/bin/python beispiele/beispiele_pruefen.py  # Beispieldatensätze mit Soll-Ergebnis
.venv/bin/python pruefen.py b --bestaetigung ab.json --bestellung bestellung.json --absender lieferant@example.de --dmarc pass
```

Für die lokalen Tests ist **keine** kostenpflichtige API und kein Zugangsschlüssel nötig: Geprüft wird die
Verarbeitung von Modellausgaben, nicht das Sprachmodell selbst.

## Was die Tests belegen und was nicht

Version 1.0 enthält **482 automatische Tests** (`pytest` zählt sie bei jedem Lauf; Python 3.10 bis 3.13;
der Test des pandas-Rezepts wird übersprungen, wenn pandas fehlt). Sie decken ab: gültige und ungültige
Eingaben, fehlende Pflichtfelder, unplausible Zahlen und Typen, Preis-, Mengen- und Terminabweichungen,
Einheiten- und Schreibvarianten, Toleranzgrenzen und Rundung, gefälschte Absender und fehlende
DMARC-Ergebnisse, manipulierte Dokumentinhalte und Prompt Injection in Rückfrage-Entwürfen, abgebrochene
Modellausgaben und Importfehler.

Die Tests belegen, dass die Programme mit **konstruierten Daten** regelgerecht arbeiten. Sie garantieren
**keinen** erfolgreichen produktiven Einsatz im Unternehmen. Ein Praxistest mit echten Vorgängen eines Betriebs
wurde nicht durchgeführt. Wie zuverlässig das Sprachmodell die Daten ausliest, zeigt erst das Pilotprojekt mit
30 bis 50 eigenen Testfällen mit bekannter Lösung und gezielten Testfällen für seltene, teure Fehler (Kapitel 11).

## Anpassen

Toleranzen (`Toleranzen` in `abgleich_auftragsbestaetigung.py`), Einheiten, Stammdaten, Anfragetypen,
Pflichtangaben, Textbausteine und Prüfmuster an den eigenen Betrieb anpassen und mit eigenen Testfällen prüfen.
Jede Modellausgabe vor der Weiterverarbeitung gegen das Schema validieren und den Abbruchgrund der Antwort
prüfen (Anhang D des Buches).

## Sicherheit und Datenschutz

Keine Zugangsdaten im Code, keine echten personenbezogenen Daten in den Beispielen. Das Sprachmodell erhält
keine Schreib- oder Versandrechte; jede geschäftlich wirksame Aktion gibt ein Mensch frei. Für den Betrieb sind
ein Vertrag zur Auftragsverarbeitung mit jedem Dienst, ein Eintrag im Verarbeitungsverzeichnis und die
Information der Betroffenen nötig (Kapitel 10, Anhang B).
