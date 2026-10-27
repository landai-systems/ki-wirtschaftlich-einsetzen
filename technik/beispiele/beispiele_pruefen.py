"""Führt alle Beispieldatensätze aus beispiele/fall_a, fall_b, fall_c durch die Prüfprogramme und vergleicht
das Ergebnis mit dem erwarteten Ergebnis. Aufruf aus dem Ordner vorlagen:  python beispiele/beispiele_pruefen.py

Die Datensätze sind konstruierte Beispiele mit bekannter Lösung, darunter Negativ- und Angriffsfälle.
Sie belegen, dass die Programme regelgerecht arbeiten. Sie ersetzen nicht den Test mit eigenen, echten
Vorgängen im Pilotprojekt (Kapitel 11); ein solcher Praxistest wurde für dieses Buch nicht durchgeführt.
"""
import glob, json, os, sys
H = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(H))
from pruefe_bericht import pruefe_bericht                      # noqa: E402
from abgleich_auftragsbestaetigung import abgleichen           # noqa: E402
from pruefe_rueckfrage import pruefe_entwurf                   # noqa: E402


def _lade(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def faelle():
    sa = _lade(os.path.join(H, "fall_a", "_stammdaten.json"))
    best = _lade(os.path.join(H, "fall_b", "_bestellung.json"))
    for p in sorted(glob.glob(os.path.join(H, "fall_*", "[!_]*.json"))):
        d, fall = _lade(p), os.path.basename(os.path.dirname(p))
        if fall == "fall_a":
            w = pruefe_bericht(d["eingabe"], set(sa["baustellen"]), set(sa["mitarbeiter"]), set(sa["katalog"]),
                               erfasste_stunden=sa["erfasste_stunden"])
            ok = (not w) == d["erwartet"]["unauffaellig"] and all(any(x in m for m in w)
                                                                  for x in d["erwartet"]["warnungen_enthalten"])
        elif fall == "fall_b":
            r = abgleichen(d["eingabe"], best, absender=d["absender"], authentifiziert=d["authentifiziert"])
            w = r.befunde
            ok = r.status == d["erwartet"]["status"] and all(any(x in m for m in w)
                                                             for x in d["erwartet"]["befunde_enthalten"])
        else:
            w = pruefe_entwurf(d["eingabe"])
            ok = (not w) == d["erwartet"]["unauffaellig"] and all(any(x in m for m in w)
                                                                  for x in d["erwartet"]["warnungen_enthalten"])
        yield os.path.relpath(p, H), d["beschreibung"], ok, w


def main():
    fehler = 0
    for name, beschreibung, ok, w in faelle():
        fehler += not ok
        print(f"{'OK    ' if ok else 'FEHLER'} {name:38} {beschreibung}")
        for m in w:
            print(f"         - {m}")
    print(f"\n{'Alle Beispiele wie erwartet.' if not fehler else f'{fehler} Beispiel(e) weichen ab.'}")
    return 1 if fehler else 0


if __name__ == "__main__":
    sys.exit(main())
