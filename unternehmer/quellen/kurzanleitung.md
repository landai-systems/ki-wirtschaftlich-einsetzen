---
title: Kurzanleitung zum Wirtschaftlichkeitsrechner
subtitle: KI wirtschaftlich einsetzen · Begleitmaterial Version 1.0
---

# 1. Welche Datei Sie öffnen

Öffnen Sie **KI-Wirtschaftlichkeitsrechner.xlsx** mit Microsoft Excel. Die Datei enthält keine Makros und keine Verbindungen ins Internet. Sie startet mit dem Blatt **Start**. Von dort führt ein Link zum Blatt **Mein Vorhaben**. Nur dieses Blatt brauchen Sie für Ihre eigene Rechnung. Die übrigen Blätter enthalten die Rechnungen aus dem Buch.

| Farbe | Bedeutung |
| --- | --- |
| blau hinterlegt | Eingabe: hier tragen Sie Ihre Zahlen ein |
| grau hinterlegt | Ergebnis: rechnet die Tabelle selbst |
| grün hinterlegt | wichtigstes Ergebnis |

Formeln sind gegen versehentliches Überschreiben geschützt. Ein Kennwort gibt es nicht.

# 2. Welche Zahlen Sie brauchen

| Angabe | Woher |
| --- | --- |
| Wie oft fällt der Vorgang im Monat an? | Zählen, zum Beispiel Auftragsbestätigungen oder Kundenanfragen eines Monats |
| Wie viele Minuten dauert ein Vorgang heute? | Messen: 20 bis 30 Vorgänge mit der Uhr, Durchschnitt bilden. Ein Beispiel liegt im Ordner Beispieldaten. |
| Wie viele Minuten bleiben mit KI? | Schätzung des Dienstleisters, später im Pilotprojekt messen |
| Was kostet eine Arbeitsstunde? | Lohnbuchhaltung: Bruttolohn plus Arbeitgeberanteile, geteilt durch tatsächlich geleistete Stunden |
| Einmalige und laufende Kosten | Angebot des Dienstleisters; Datenschutz und IT-Sicherheit nicht vergessen |

Ein **Vorgang** ist ein einzelner, wiederkehrender Arbeitsschritt, etwa eine Anfrage oder ein Bericht. **KI-Kosten** sind die Gebühren, die der Anbieter des Sprachmodells je Nutzung berechnet; sie liegen in den Beispielen des Buches bei rund einem Cent je Vorgang.

# 3. Wo Sie die Zahlen eintragen

Im Blatt **Mein Vorhaben** stehen drei Spalten nebeneinander:

- **Erwartet:** Ihre beste Schätzung. Vorbelegt mit dem Beispiel aus Kapitel 5 des Buches.
- **Vorsichtig:** dieselben Zahlen, aber nur die halbe Zeitersparnis. So sehen Sie, wie empfindlich das Ergebnis ist.
- **Ihre Variante:** frei für eigene Szenarien, etwa mehr Vorgänge oder ein anderes Angebot.

Ersetzen Sie die blauen Werte Zeile für Zeile. Rechts steht zu jeder Zeile eine kurze Erläuterung. Unplausible Werte, etwa negative Zahlen, lehnt die Tabelle mit einer Meldung ab. Auffällige Kombinationen zeigt sie unten unter **Hinweise zu den Eingaben** in Rot.

# 4. Wie Sie die Ergebnisse lesen

Das Beispiel aus dem Buch: 600 Vorgänge im Monat, heute 6 Minuten je Vorgang, mit KI 2 Minuten, bei 8 Prozent der Vorgänge 5 Minuten Nacharbeit, 45 Euro Arbeitskosten je Stunde, 50 Euro Softwarekosten und gut 4,7 Stunden Wartung im Monat.

| Ergebnis | Erwartet | Vorsichtig |
| --- | --- | --- |
| Frei werdende Arbeitszeit je Monat | 31,3 Stunden | 11,3 Stunden |
| Nettoeffekt kalkulatorisch je Monat | 1.354 € | 454 € |
| Nettoeffekt zahlungswirksam je Monat (30 % der Zeit sparen Geld) | 367 € | 97 € |
| Einmalkosten gesamt | 7.260 € | 7.260 € |
| Amortisation kalkulatorisch | 5,4 Monate | 16,0 Monate |
| Amortisation zahlungswirksam | 16,3 Monate | 61,7 Monate |
| Ergebnis nach 24 Monaten, zahlungswirksam | 2.814 € | −3.666 € |

**Kalkulatorisch** heißt: Die frei werdende Zeit wird mit den Arbeitskosten bewertet. **Zahlungswirksam** heißt: Es zählt nur, was tatsächlich an Ausgaben wegfällt. **Amortisation** ist die Zeit, nach der die Einmalkosten zurückverdient sind.

Die Zeile **Einschätzung** fasst das Ergebnis in einem Satz zusammen. Die Zeile **Mindestmenge** zeigt, ab wie vielen Vorgängen im Monat sich der laufende Betrieb trägt.

# 5. Wann sich eine KI-Lösung rechnerisch lohnt

Eine Lösung lohnt sich rechnerisch, wenn drei Dinge zusammenkommen:

1. Der **Nettoeffekt je Monat ist deutlich positiv**, auch in der Spalte „Vorsichtig“.
2. Die **Einmalkosten sind im Betrachtungszeitraum** von meist 24 Monaten **zurückverdient**. KI-Modelle und Preise ändern sich schnell; längere Zeiträume sind unsicher.
3. Die **Mindestmenge liegt klar unter** Ihrer tatsächlichen Menge.

Entscheidend ist fast immer die Zeitersparnis je Vorgang, nicht der Preis der KI. Messen Sie diese Zahl, bevor Sie viel Geld ausgeben: Ein kleines Pilotprojekt mit echten Vorgängen kostet wenig und ersetzt Schätzungen durch Messwerte (Kapitel 11 des Buches).

# 6. Warum gesparte Zeit nicht automatisch gespartes Geld ist

Wenn eine Mitarbeiterin 31 Stunden im Monat weniger für einen Vorgang braucht, bleibt ihr Gehalt gleich. Geld spart der Betrieb erst, wenn deshalb Überstunden, Aushilfen oder eine geplante Neueinstellung wegfallen, oder wenn die frei werdende Zeit nachweislich zusätzlichen **Deckungsbeitrag** bringt, also Umsatz abzüglich der direkt dafür anfallenden Kosten.

Deshalb fragt der Rechner nach dem **Anteil der frei werdenden Zeit, der tatsächlich Ausgaben vermeidet**. Im Buchbeispiel sind es 30 Prozent. Setzen Sie hier 0 Prozent ein, wenn Sie nichts davon sicher in Geld umsetzen können. Dann zeigt der Rechner einen reinen Kapazitätsgewinn: mehr Zeit für andere Aufgaben, aber keine Kostensenkung.

Umsatz zählt nie direkt. Wer zum Beispiel erwartet, dass vollständigere Berichte zu mehr abgerechneten Leistungen führen, trägt nur den zusätzlichen Deckungsbeitrag ein, und auch nur den Teil, den Kunden tatsächlich bezahlen.

# 7. Wer was übernehmen kann

| Aufgabe | Wer |
| --- | --- |
| Vorgänge zählen, Zeiten messen, Rechner ausfüllen, Entscheidungshilfe durchgehen | Sie selbst |
| Angebote einholen und mit der Dienstleister-Checkliste vergleichen | Sie selbst |
| Automatisierungsdienst einrichten, Testfälle zusammenstellen, Pilotprojekt betreuen | eine technisch interessierte Person im Betrieb |
| Anbindung an Warenwirtschaft oder Abrechnung, Programmierung, Betreuung bei Störungen | ein qualifizierter Dienstleister |

Die drei Praxisfälle des Buches sind keine fertigen Produkte. Vor dem Einsatz sind Einrichtung, Anpassung an den Betrieb und Tests mit eigenen Vorgängen nötig.

*Die Ergebnisse des Rechners sind Modellrechnungen mit Ihren Annahmen. Sie sind keine Zusage einer Zeitersparnis oder Rentabilität und keine Steuer- oder Rechtsberatung.*
