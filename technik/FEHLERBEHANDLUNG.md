# Fehler- und Ausnahmebehandlung

Grundsatz: **Im Zweifel markieren, nie still durchlassen.** Kein Programm bricht bei unerwarteten Daten mit einer
Ausnahme ab, ohne dass ein Befund entsteht; jede Unsicherheit landet beim Menschen.

| Situation | Verhalten | Getestet in |
| --- | --- | --- |
| Datei fehlt, nicht UTF-8, kein gültiges JSON, kein Objekt | `pruefen.py`: Status `fehler`, Rückgabewert 2, keine Prüfung | `test_pruefen_cli.py` |
| Abgebrochene Modellausgabe (z. B. Abbruchgrund `max_tokens`) | ungültiges JSON → Status `fehler` | `test_pruefen_cli.py` |
| Pflichtfeld fehlt, falscher Typ | Schemaprüfung meldet Feld und Grund; ohne `jsonschema` Mindestprüfung der Pflichtfelder | `test_pruefen_cli.py`, `test_vorlagen.py` |
| NaN, unendlich, Text oder bool statt Zahl | Befund „unplausibler Wert“, Position wird markiert | `test_randfaelle.py`, `test_zusatzfaelle.py` |
| Negative Mengen oder Preise, Rabatt außerhalb 0–100 % | Befund | `test_erweitert.py` |
| Preis-, Mengen-, Termin-, Einheitenabweichung | Befund je Position; Toleranzen in `Toleranzen` | `test_vorlagen.py`, `test_erweitert.py` |
| Toleranzgrenzen, Rundung von Summen | Grenzwerte und Rundung (0,05 €) getestet | `test_angriffe.py`, `test_erweitert.py` |
| Abweichende Einheiten- oder Schreibweisen (Stk/Stück, A-100/A 100) | normalisiert; nur ähnliche Artikelnummern werden markiert | `test_erweitert.py`, `test_randfaelle.py` |
| Unerwartete Ausnahme während der Prüfung | abgefangen, Befund „nicht vollständig geprüft“, Status `markiert` | `test_randfaelle.py` |
| Gefälschter oder fremder Absender, DMARC nicht bestanden oder fehlt | Befund | `test_angriffe.py`, `test_zusatzfaelle.py` |
| Andere Rechtsform beim Lieferanten | Befund (möglicherweise andere juristische Person) | `test_zusatzfaelle.py` |
| Hinweistexte im Dokument (z. B. neue Bankverbindung) | jeder Hinweis wird Befund; Bankdaten nie übernehmen | `beispiele/fall_b` |
| Prompt Injection in Kundenanfragen | Musterprüfung (Links, Kontaktdaten, Bankdaten, Beträge, Termine, Zusagen, unsichtbare Zeichen); Textbaustein-Variante lässt keinen Modelltext in die Nachricht | `test_angriffe.py`, `test_zusatzfaelle.py` |
| Fehlende Zeiterfassung, Stunden über Grenze, Zusatzleistungen über gemeldeter Zeit | Warnung | `test_vorlagen.py`, `test_zusatzfaelle.py` |

Die Musterprüfung in Fall C erkennt typische, nicht alle denkbaren Formulierungen. Sie ersetzt nicht die
Durchsicht durch einen Menschen neben der Originalanfrage.
