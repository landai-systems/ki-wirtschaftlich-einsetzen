"""Kommandozeile für die drei Prüfprogramme: liest die Modellausgabe und die Vergleichsdaten als JSON-Dateien,
prüft Format und Pflichtfelder und gibt das Ergebnis als JSON aus.

    python pruefen.py a --bericht bericht.json --stammdaten stammdaten.json
    python pruefen.py b --bestaetigung ab.json --bestellung bestellung.json --absender "a@b.de" --dmarc pass
    python pruefen.py c --ergebnis ergebnis.json [--variante bausteine]

Rückgabewert: 0 = unauffällig, 1 = markiert (Mensch prüft), 2 = Eingabefehler (nichts geprüft).
Das Programm ist ein lokaler Prüfschritt. Abholen der Daten, Aufruf des Sprachmodells und Übergabe in andere
Systeme gehören zur betrieblichen Integration (siehe DATENUEBERGABEN.md) und sind nicht Teil dieses Programms.
"""
import argparse
import json
import sys

import schemas
from abgleich_auftragsbestaetigung import abgleichen
from pruefe_bericht import pruefe_bericht
from pruefe_rueckfrage import pruefe_entwurf


class Eingabefehler(Exception):
    pass


def lade_json(pfad, was):
    try:
        with open(pfad, encoding="utf-8") as f:
            daten = json.load(f)
    except FileNotFoundError:
        raise Eingabefehler(f"{was}: Datei nicht gefunden ({pfad})")
    except UnicodeDecodeError:
        raise Eingabefehler(f"{was}: Datei ist nicht UTF-8-kodiert ({pfad})")
    except json.JSONDecodeError as e:
        raise Eingabefehler(f"{was}: kein gültiges JSON, Zeile {e.lineno}, Spalte {e.colno} "
                            f"(oft eine abgebrochene Modellausgabe, Abbruchgrund prüfen)")
    if not isinstance(daten, dict):
        raise Eingabefehler(f"{was}: erwartet wird ein JSON-Objekt")
    return daten


def pruefe_schema(daten, schema, was):
    """Vollständige Prüfung mit jsonschema, sonst Mindestprüfung der Pflichtfelder."""
    try:
        import jsonschema
    except ImportError:
        fehlt = [k for k in schema.get("required", []) if k not in daten]
        if fehlt:
            raise Eingabefehler(f"{was}: Pflichtfelder fehlen: {', '.join(fehlt)}")
        return
    fehler = sorted(jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
                    .iter_errors(daten), key=lambda e: list(e.path))
    if fehler:
        raise Eingabefehler(f"{was}: entspricht nicht dem Schema: " +
                            "; ".join(f"{'/'.join(map(str, e.path)) or '(oben)'}: {e.message}" for e in fehler[:5]))


def fall_a(args):
    bericht = lade_json(args.bericht, "Bericht")
    pruefe_schema(bericht, schemas.FALL_A_MONTAGEBERICHT, "Bericht")
    st = lade_json(args.stammdaten, "Stammdaten")
    for k in ("baustellen", "mitarbeiter"):
        if not isinstance(st.get(k), list):
            raise Eingabefehler(f"Stammdaten: Liste '{k}' fehlt")
    w = pruefe_bericht(bericht, set(st["baustellen"]), set(st["mitarbeiter"]),
                       set(st["katalog"]) if isinstance(st.get("katalog"), list) else None,
                       erfasste_stunden=st.get("erfasste_stunden"))
    return ("markiert" if w else "unauffaellig"), w


def fall_b(args):
    ab = lade_json(args.bestaetigung, "Auftragsbestätigung")
    pruefe_schema(ab, schemas.FALL_B_AUFTRAGSBESTAETIGUNG, "Auftragsbestätigung")
    best = lade_json(args.bestellung, "Bestellung")
    if not isinstance(best.get("positionen"), list):
        raise Eingabefehler("Bestellung: Liste 'positionen' fehlt")
    auth = {"pass": True, "fail": False, "none": None}[args.dmarc]
    r = abgleichen(ab, best, absender=args.absender, authentifiziert=auth, dmarc_pruefen=not args.ohne_dmarc)
    return r.status, r.befunde


def fall_c(args):
    erg = lade_json(args.ergebnis, "Ergebnis")
    schema = dict(schemas.FALL_C_ANFRAGE)
    if args.variante == "bausteine":
        schema = schemas.fall_c_schema([erg.get("anfragetyp") or "unklar"], mit_entwurf=False)
        schema["properties"]["anfragetyp"] = {"type": "string"}
    pruefe_schema(erg, schema, "Ergebnis")
    w = pruefe_entwurf(erg, variante=args.variante)
    return ("markiert" if w else "unauffaellig"), w


def main(argv=None):
    p = argparse.ArgumentParser(description="Prüfprogramme zu „KI wirtschaftlich einsetzen“")
    sub = p.add_subparsers(dest="fall", required=True)
    a = sub.add_parser("a", help="Montagebericht prüfen")
    a.add_argument("--bericht", required=True); a.add_argument("--stammdaten", required=True)
    b = sub.add_parser("b", help="Auftragsbestätigung abgleichen")
    b.add_argument("--bestaetigung", required=True); b.add_argument("--bestellung", required=True)
    b.add_argument("--absender"); b.add_argument("--dmarc", choices=["pass", "fail", "none"], default="none")
    b.add_argument("--ohne-dmarc", action="store_true", help="DMARC-Prüfung bewusst abschalten")
    c = sub.add_parser("c", help="Rückfrage-Ergebnis prüfen")
    c.add_argument("--ergebnis", required=True)
    c.add_argument("--variante", choices=["entwurf", "bausteine"], default="entwurf")
    args = p.parse_args(argv)
    try:
        status, meldungen = {"a": fall_a, "b": fall_b, "c": fall_c}[args.fall](args)
    except Eingabefehler as e:
        print(json.dumps({"status": "fehler", "meldungen": [str(e)]}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps({"status": status, "meldungen": meldungen}, ensure_ascii=False, indent=2))
    return 0 if status == "unauffaellig" else 1


if __name__ == "__main__":
    sys.exit(main())
