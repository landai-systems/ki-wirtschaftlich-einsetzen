"""Plausibilitätsprüfung eines ausgelesenen Montageberichts (Praxisfall A), bevor er in der Prüfmaske erscheint.

Das Schema prüft nur Form und Pflichtfelder. Diese Funktion prüft die Inhalte gegen die Stammdaten:
aktive Baustelle, bekannte Mitarbeitende, Katalog, plausible Stunden und Mengen. Sie markiert nur;
die Entscheidung trifft die Person, die den Bericht freigibt.
"""
import math


def _zahl(x):
    """Endliche Zahl oder None (NaN und unendlich gelten als fehlend-unplausibel)."""
    if isinstance(x, bool):
        return None
    return x if isinstance(x, (int, float)) and math.isfinite(x) else None


def pruefe_bericht(bericht: dict, baustellen: set, mitarbeiter: set, katalog: set = None,
                   max_stunden_je_person: float = 10.0, erfasste_stunden: dict = None,
                   max_zusatzstunden: float = None) -> list:
    """bericht: Modellausgabe nach Schema FALL_A_MONTAGEBERICHT.
    baustellen: Kennungen der aktiven Baustellen. mitarbeiter: Personalnummern.
    katalog: Katalognummern (optional). erfasste_stunden: {mitarbeiter_id: Stunden} aus der Zeiterfassung (optional).
    max_zusatzstunden: Obergrenze für die Summe der Zusatzleistungen (Standard: max_stunden_je_person je Person).
    Rückgabe: Liste von Warnungen (leer = unauffällig)."""
    w = []
    bs = bericht.get("baustelle_id")
    if bs is None:
        w.append("Baustelle nicht zugeordnet")
    elif bs not in baustellen:
        w.append(f"Baustelle {bs} ist nicht aktiv")
    if bericht.get("abweichendes_datum_genannt"):
        w.append(f"Monteur nennt anderen Tag: {bericht['abweichendes_datum_genannt']!r}, Datum prüfen")
    personen = bericht.get("personen") or []
    if not personen:
        w.append("Keine Personen erfasst")
    gesehen = set()
    gemeldet = 0.0
    je_person = {}
    for p in personen:
        mid, name, std = p.get("mitarbeiter_id"), p.get("name_wie_genannt"), p.get("stunden")
        wer = mid or name or "unbekannt"
        if mid is None:
            w.append(f"Person {name!r} nicht eindeutig zugeordnet")
        elif mid not in mitarbeiter:
            w.append(f"Personalnummer {mid} unbekannt")
        elif mid in gesehen:
            w.append(f"{mid} mehrfach im Bericht")
        if mid:
            gesehen.add(mid)
        if std is None:
            w.append(f"{wer}: Stunden fehlen")
        elif _zahl(std) is None or std <= 0 or std > max_stunden_je_person:
            w.append(f"{wer}: unplausible Stunden {std!r}")
        else:
            gemeldet += std
            if mid is not None:
                je_person[mid] = je_person.get(mid, 0.0) + std
    # Vergleich mit der Zeiterfassung je Person (mehrere Einträge derselben Person werden summiert)
    if erfasste_stunden is not None:
        for mid, std in je_person.items():
            if mid not in erfasste_stunden:
                w.append(f"{mid}: keine Zeiterfassung für diesen Tag")
            elif _zahl(erfasste_stunden[mid]) is None:
                w.append(f"{mid}: Zeiterfassung ohne gültigen Wert ({erfasste_stunden[mid]!r})")
            elif abs(erfasste_stunden[mid] - std) > 0.25:
                w.append(f"{mid}: {std:g} h im Bericht, {erfasste_stunden[mid]:g} h in der Zeiterfassung")
    for m in bericht.get("material") or []:
        if _zahl(m.get("menge")) is None or m["menge"] <= 0:
            w.append(f"Material {m.get('bezeichnung')!r}: Menge fehlt oder ist unplausibel")
        if katalog is not None and m.get("katalog_nr") not in katalog:
            w.append(f"Material {m.get('bezeichnung')!r}: nicht im Katalog")
    grenze = max_zusatzstunden if max_zusatzstunden is not None else max_stunden_je_person * max(len(personen), 1)
    summe = 0.0
    for z in bericht.get("zusatzleistungen") or []:
        st = z.get("stunden")
        if st is None:
            w.append(f"Zusatzleistung {z.get('beschreibung')!r}: Stunden fehlen")
        elif _zahl(st) is None:
            w.append(f"Zusatzleistung {z.get('beschreibung')!r}: unplausible Stunden {st!r}")
        elif st < 0:
            w.append(f"Zusatzleistung {z.get('beschreibung')!r}: negative Stunden")
        else:
            summe += st
    if summe > grenze:
        w.append(f"Zusatzleistungen zusammen {summe:g} h, mehr als plausibel ({grenze:g} h): prüfen")
    if summe > gemeldet:
        w.append(f"Zusatzleistungen ({summe:g} h) übersteigen die gemeldete Arbeitszeit ({gemeldet:g} h): prüfen")
    if bericht.get("unsichere_angaben"):
        w.append("Modell meldet unsichere Angaben: in der Prüfmaske hervorheben")
    if bericht.get("fehlende_angaben"):
        w.append("Modell meldet fehlende Angaben: Rückfrage prüfen")
    return w
