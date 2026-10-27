# Prüfbericht Version 1.0

Stand 27.10.2026. Jede Aussage lässt sich mit den angegebenen Befehlen wiederholen.

## Technikpaket

| Prüfung | Befehl | Ergebnis |
| --- | --- | --- |
| Automatische Tests | `cd technik && python -m pytest -q` | 482 bestanden (Python 3.13); 481 bestanden, 1 übersprungen (Python 3.10 und 3.11, ohne pandas) |
| Beispieldatensätze | `python beispiele/beispiele_pruefen.py` | 17 von 17 wie erwartet, alle Eingaben schemakonform |
| Prompts wortgleich mit dem Buch | Abgleich der Dateien in `anweisungen/` mit den Textblöcken des Manuskripts | 4 von 4 wortgleich |

Die bisher im Buch genannte Zahl von 472 Tests war richtig; neu hinzugekommen sind 10 Tests der Kommandozeile
(Dateiimport, ungültiges JSON, abgebrochene Modellausgabe, fehlende Pflichtfelder, falsche Typen, Kodierung).

## Wirtschaftlichkeitsrechner

| Prüfung | Ergebnis |
| --- | --- |
| Neuberechnung mit LibreOffice | 827 Formeln, 0 Fehlerwerte |
| Buchblätter gegenüber Rechenmodell Version 5 | 0 abweichende Werte (Zelle für Zelle verglichen) |
| Blatt „Mein Vorhaben“ gegen unabhängige Python-Kontrollrechnung (`werkzeuge/kontrollrechnung.py`) | 0 Abweichungen in allen drei Spalten |
| Übereinstimmung mit dem Buch, Kapitel 5, mittleres Volumen | Nettoeffekt kalkulatorisch 1.354,26 €, zahlungswirksam 367,26 €, Einmalkosten 7.260 €, Amortisation 5,4 bzw. 16,3 Monate, Break-even 97 Vorgänge: identisch |
| Spalte „Vorsichtig“ gegen Empfindlichkeit „halbe Zeitersparnis“ im Buch | 454,26 €: identisch |
| Grenzfälle (`werkzeuge/grenzfaelle.py`): 0 Vorgänge, mit KI langsamer, sehr geringe Ersparnis, 0 % realisierbar, Amortisation nicht erreichbar, unplausible Eingaben | 6 von 6 mit richtiger Einschätzung und Hinweis, Kontrollrechnung ohne Abweichung |
| Eingabeprüfung | alle 57 Eingabezellen mit Wertebereich und Fehlermeldung |

**Korrigierte Abweichung:** `Wirtschaftlichkeit!B36:D36` (Kosten je Vorgang mit KI) teilte durch die Zahl der Vorgänge
und ergab bei 0 Vorgängen einen Divisionsfehler. Jetzt wird „-“ angezeigt. Die Buchwerte ändern sich dadurch nicht.

**Neue Kennzeichnung, keine neuen Annahmen:** Die Vorbelegung von „Mein Vorhaben“ übernimmt die Werte aus
Kapitel 5; die Spalte „Vorsichtig“ entspricht der Empfindlichkeitsrechnung des Buches. Die Prüfhinweise (zum
Beispiel Nacharbeit über 50 %, Arbeitskosten unter 15 oder über 150 €/h) sind Plausibilitätsgrenzen des Rechners
und lösen nur einen Hinweis aus, keine Sperre.

## Nicht geprüft

- Kein Praxistest mit echten Vorgängen eines Betriebs.
- Kein Test mit Microsoft Excel selbst; geprüft wurde mit LibreOffice. Verwendet werden nur Standardfunktionen
  (IF, IFERROR, ROUNDUP, INDEX, MATCH, HYPERLINK) ohne Makros.
- Keine Prüfung der Aufrufe von Sprachmodellen; die Programme verarbeiten deren Ausgaben.
