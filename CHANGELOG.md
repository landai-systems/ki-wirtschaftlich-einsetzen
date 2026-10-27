# Änderungsprotokoll

## 1.0 – 2026-10-27

Erste veröffentlichte Fassung zur Erstausgabe des Buches.

**Unternehmerpaket**
- Wirtschaftlichkeitsrechner auf Basis des Rechenmodells zum Buch (Version 5) mit neuem Startblatt und Blatt „Mein Vorhaben“: drei Szenariospalten, getrennter Ausweis von Kapazitätsgewinn, vermiedenen Auszahlungen und Deckungsbeitrag, Eingabeprüfung mit Fehlermeldungen, Hinweise bei unplausiblen Kombinationen, Blattschutz ohne Kennwort.
- Korrektur: `Wirtschaftlichkeit!B36:D36` ergab bei 0 Vorgängen einen Divisionsfehler; jetzt „-“. Alle übrigen Werte des Buchmodells unverändert.
- Kurzanleitung, Entscheidungshilfe und Dienstleister-Checkliste als PDF; konstruierte Beispieldaten.

**Technikpaket**
- Prüfprogramme für Fall A, B und C, zwei Prompt-Varianten für Fall C, JSON-Schemas.
- Neu: Kommandozeile `pruefen.py` mit Dateiimport, Schemaprüfung und Rückgabewerten; Testdatensätze mit erwarteten Ergebnissen; Dokumentation der Datenübergaben und Fehlerbehandlung.
- 482 automatische Tests (Python 3.10 bis 3.13).
