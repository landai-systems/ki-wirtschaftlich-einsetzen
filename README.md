# KI wirtschaftlich einsetzen

**Kostenloses Begleitmaterial zum gleichnamigen Buch**

Verständliche Werkzeuge zur wirtschaftlichen Bewertung und technischen Vorbereitung von KI-Anwendungen in deutschen kleinen und mittleren Unternehmen. Ohne Registrierung, ohne Kosten.

## Herunterladen

### Für Unternehmer – ohne Programmierkenntnisse

Excel-Rechner, Kurzanleitung, Entscheidungshilfe und Checkliste für die Beauftragung eines Dienstleisters.
Sie brauchen nur Microsoft Excel und einen PDF-Betrachter.

**[⬇ Unternehmerpaket herunterladen (ZIP)](https://github.com/landai-systems/ki-wirtschaftlich-einsetzen/releases/download/v1.0/KI-Wirtschaftlich-Einsetzen_Unternehmer_V1.0.zip)**

### Für IT-Verantwortliche und Dienstleister

Prompts, JSON-Schemas, Prüfprogramme in Python, Testdatensätze mit erwarteten Ergebnissen und automatische Tests als Ausgangsbasis für ein Pilotprojekt.

**[⬇ Technikpaket herunterladen (ZIP)](https://github.com/landai-systems/ki-wirtschaftlich-einsetzen/releases/download/v1.0/KI-Wirtschaftlich-Einsetzen_Technik_V1.0.zip)**

Alle Versionen: [Releases](https://github.com/landai-systems/ki-wirtschaftlich-einsetzen/releases) · Aktuelle Version: [1.0](https://github.com/landai-systems/ki-wirtschaftlich-einsetzen/releases/tag/v1.0)

---

## Worum geht es in dem Buch?

„KI wirtschaftlich einsetzen“ zeigt Inhabern und Geschäftsführern kleiner und mittlerer Unternehmen, wie man nüchtern rechnet, ob sich eine KI-Anwendung lohnt: was KI-Dienste tatsächlich kosten, wie man Abonnement, nutzungsabhängige Abrechnung und eigene Rechner vergleicht, wie man Zeitersparnis bewertet und wann man besser auf KI verzichtet. Drei Praxisfälle werden vollständig durchgerechnet.

## Was enthalten die beiden Pakete?

| Unternehmerpaket | Technikpaket |
| --- | --- |
| Wirtschaftlichkeitsrechner für Excel mit Startblatt und Blatt „Mein Vorhaben“ | Prompts (Anweisungen an das Sprachmodell) für alle drei Fälle |
| Kurzanleitung (PDF, 3 Seiten) | JSON-Schemas der Modellausgaben |
| Entscheidungshilfe zur KI-Einführung (PDF) | Prüfprogramme in Python mit Kommandozeile |
| Checkliste zur Beauftragung eines IT-Dienstleisters (PDF) | Testdatensätze mit erwarteten Ergebnissen, 482 automatische Tests |
| Anonymisierte Beispieldaten zum Messen und Zählen | Dokumentation der Datenübergaben und der Fehlerbehandlung |

## Welche drei Praxisfälle werden behandelt?

| Fall | Was passiert | Was der Mensch tut |
| --- | --- | --- |
| **A: Montageberichte per Sprachnachricht** | Monteure sprechen den Bericht ein; Spracherkennung und Sprachmodell füllen die Berichtsfelder; ein Programm prüft gegen Baustellen, Personal und Zeiterfassung. | Das Büro prüft und gibt jeden Bericht frei. |
| **B: Auftragsbestätigungen prüfen** | Das Sprachmodell liest die Bestätigung aus; ein Programm gleicht sie mit der Bestellung ab und markiert Abweichungen bei Preis, Menge, Termin und Herkunft. | Der Einkauf klärt markierte Abweichungen. |
| **C: Unvollständige Kundenanfragen** | Das Sprachmodell erkennt fehlende Angaben; die Rückfrage wird aus freigegebenen Textbausteinen zusammengesetzt. | Ein Mitarbeiter prüft und versendet selbst. |

Die Fälle sind **keine fertigen Produkte**. Vor dem Einsatz sind Einrichtung, Anpassung an den eigenen Betrieb und Tests mit eigenen Vorgängen nötig.

## Was kann ein Unternehmer selbst tun?

- Vorgänge zählen und Bearbeitungszeiten messen (Beispiel im Unternehmerpaket)
- den Rechner ausfüllen und Szenarien vergleichen
- mit der Entscheidungshilfe entscheiden, ob sich ein Pilotprojekt lohnt, oder begründet dagegen entscheiden
- Angebote mit der Dienstleister-Checkliste einholen und vergleichen

## Wann ist ein IT-Dienstleister erforderlich?

Eine **technisch interessierte Person im Betrieb** kann einen Automatisierungsdienst einrichten und das Pilotprojekt betreuen, besonders bei Fall C mit einem zentralen Postfach. Einen **qualifizierten Dienstleister** braucht man in der Regel, wenn Warenwirtschaft oder Abrechnungssoftware nur über eine Programmierschnittstelle erreichbar sind, wenn Daten zwischen mehreren Systemen übergeben werden oder wenn niemand im Betrieb den Ablauf bei Störungen betreuen kann.

## Welche Grenzen haben die Programme?

- Die Prüfprogramme prüfen **Ausgaben** eines Sprachmodells nach festen Regeln. Sie rufen selbst kein Sprachmodell auf und binden keine Systeme an; das ist Aufgabe der betrieblichen Integration.
- Die automatischen Tests belegen, dass die Programme mit konstruierten Daten regelgerecht arbeiten. **Sie garantieren keinen erfolgreichen produktiven Einsatz.** Ein Praxistest mit echten Vorgängen eines Betriebs wurde nicht durchgeführt.
- Die Musterprüfung gegen manipulierte Anfragen erkennt typische, nicht alle Formulierungen. Jedes Ergebnis prüft ein Mensch, bevor es wirkt.
- Der Rechner liefert Modellrechnungen mit Ihren Annahmen, keine Zusage einer Zeitersparnis oder Rentabilität.

## Datenschutz und Sicherheit

KI-Anwendungen verarbeiten oft personenbezogene Daten. Nötig sind unter anderem ein Vertrag zur Auftragsverarbeitung mit jedem Dienst, die Prüfung des Verarbeitungsorts, ein Eintrag im Verarbeitungsverzeichnis, die Information der Betroffenen und bei Beschäftigtendaten gegebenenfalls die Beteiligung des Betriebsrats. Das Sprachmodell erhält keine Rechte, selbst zu versenden oder Daten zu ändern; ein Mensch gibt jede geschäftlich wirksame Aktion frei. Für die KI-Verordnung der EU sind unter anderem die KI-Kompetenz der Mitarbeitenden (Art. 4) und Transparenzpflichten (Art. 50) zu prüfen. Einzelheiten: Kapitel 10 und Anhang B des Buches. Dieses Material ist keine Rechtsberatung.

Das Repository enthält keine Zugangsdaten und keine echten personenbezogenen Daten.

## Versionsstand

Version **1.0** vom 27.10.2026, Preisstand der Beispiele 23.10.2026. Änderungen: [CHANGELOG.md](CHANGELOG.md). Prüfung des Rechners und der Programme: [PRUEFBERICHT.md](PRUEFBERICHT.md).

## Lizenz

Programme, Schemas und Prompts im Ordner `technik/`: MIT-Lizenz. Rechner, PDF-Dokumente und Beispieldaten im Ordner `unternehmer/`: CC BY-NC-ND 4.0, kostenlose Nutzung im eigenen Betrieb erlaubt. Einzelheiten: [LIZENZ.md](LIZENZ.md).

## Aufbau des Repositorys

```
unternehmer/    Inhalt des Unternehmerpakets; quellen/ enthält die Texte der PDF-Dokumente
technik/        Inhalt des Technikpakets mit Tests
werkzeuge/      Skripte, die Rechner, PDFs und Pakete erzeugen und prüfen
```
