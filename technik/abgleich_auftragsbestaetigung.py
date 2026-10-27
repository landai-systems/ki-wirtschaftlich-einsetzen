"""Regelbasierter Abgleich einer ausgelesenen Auftragsbestätigung mit der Bestellung (Praxisfall B).

Das Sprachmodell liest nur aus. Dieser Code vergleicht. Er ist deterministisch:
gleiche Eingaben liefern immer dasselbe Ergebnis.

Grenze: Liefert ein manipuliertes Dokument dem Modell genau die Werte der Bestellung,
erkennt kein Abgleich die Abweichung. Dagegen helfen nur Prozessmaßnahmen
(Prüfmaske mit Original-PDF, Stichproben, Rechnungsprüfung gegen die Bestellung).

Fehler in einem einzelnen Beleg brechen den Lauf nicht ab, sondern werden als Befund
"manuell prüfen" gemeldet.
"""
import math
import numbers
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from difflib import SequenceMatcher
from email.utils import parseaddr


@dataclass(frozen=True)
class Toleranzen:
    preis_prozent: float = 0.5        # Preisabweichung ab der markiert wird
    termin_spaeter_tage: int = 2      # Verspätung in Kalendertagen ab der markiert wird
    termin_frueher_tage: int = 7      # früherer Termin ab dem markiert wird (Lager, Baustellenlogistik)
    menge_absolut: float = 0.0        # erlaubte Mengenabweichung je Artikel
    summe_euro: float = 0.05          # Rundungstoleranz bei Summen- und Positionsprüfung


STANDARD = Toleranzen()

EINHEITEN = {"stk": "Stk", "stück": "Stk", "stueck": "Stk", "st": "Stk", "st.": "Stk", "stk.": "Stk", "pcs": "Stk",
             "karton": "Karton", "ktn": "Karton", "ktn.": "Karton", "krt": "Karton",
             "m": "m", "meter": "m", "lfm": "m", "kg": "kg", "kilogramm": "kg", "l": "l", "liter": "l",
             "rolle": "Rolle", "rol": "Rolle", "psch": "psch", "pauschal": "psch", "satz": "Satz", "set": "Satz"}
WAEHRUNGEN = {"eur": "EUR", "€": "EUR", "euro": "EUR", "chf": "CHF", "usd": "USD", "$": "USD"}
EPS = 1e-9


def _einheit(e):
    if e is None:
        return None
    return EINHEITEN.get(str(e).strip().lower(), str(e).strip())


def _nummer(n):
    """Bestellnummer vergleichbar machen: Leerzeichen und übliche Präfixe entfernen."""
    if n is None:
        return None
    s = "".join(str(n).split()).upper()
    for praefix in ("BESTELLNR.", "BESTELLNR", "BESTELLUNG", "NR.", "NR"):
        if s.startswith(praefix):
            s = s[len(praefix):].lstrip(":.-#")
    return s


RECHTSFORMEN = {"gmbh", "mbh", "ag", "kg", "ohg", "gbr", "ug", "ek", "kgaa", "se", "co", "&", "und",
                "haftungsbeschraenkt", "inh", "inhaber"}
# Rechtsformen, die eine andere juristische Person kennzeichnen (Zusätze wie "& Co." zählen nicht)
RECHTSFORM_KERN = {"gmbh", "ag", "kg", "ohg", "gbr", "ug", "ek", "kgaa", "se"}


UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def _name(s):
    """Firmenname vergleichbar machen: Kleinschreibung, Umlaute, Satzzeichen und Rechtsformzusätze angleichen."""
    if not s:
        return ""
    return " ".join(w for w in _woerter(s) if w not in RECHTSFORMEN)


def _woerter(s):
    t = unicodedata.normalize("NFKC", str(s)).casefold().translate(UMLAUTE)
    t = re.sub(r"\be\.\s?k(fm)?\.?", " ek ", t)
    t = re.sub(r"\bg\.\s?m\.\s?b\.\s?h\.?", " gmbh ", t)
    return re.sub(r"[.,()\-/]", " ", t).split()


def _rechtsform(s):
    return frozenset(w for w in _woerter(s) if w in RECHTSFORM_KERN) if s else frozenset()


def _name_vergleich(soll, ist):
    """'gleich', 'aehnlich' oder 'anders'. Nur gleiche Wortmengen und gleiche Rechtsform gelten als passend;
    eine abweichende Rechtsform kann eine andere juristische Person sein und gilt als 'aehnlich'."""
    a, b = _name(soll), _name(ist)
    if not a or not b:
        return "anders"
    if set(a.split()) == set(b.split()):
        fa, fb = _rechtsform(soll), _rechtsform(ist)
        return "aehnlich" if fa and fb and fa != fb else "gleich"
    return "aehnlich" if SequenceMatcher(None, a, b).ratio() >= 0.85 else "anders"


STRICHE = re.compile("[\u2010-\u2015\u2212]")


def _artnr(n):
    """Artikelnummer vergleichbar machen: Unicode-Striche, Groß-/Kleinschreibung und Art des Trennzeichens angleichen.
    Die Position der Trennzeichen bleibt erhalten (1-234 ist nicht 12-34)."""
    if n is None:
        return None
    s = STRICHE.sub("-", unicodedata.normalize("NFKC", str(n))).strip().upper()
    return re.sub(r"[\s\-./]+", "-", s).strip("-")


def _ohne_trenner(key):
    return key.replace("-", "") if key else key


def _endlich(v):
    """None oder eine endliche Zahl (int, float, Decimal); alles andere (NaN, unendlich, Text, bool) wird zu None."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (numbers.Real, Decimal)):
        f = float(v)
        return f if math.isfinite(f) else None
    return None


def _nicht_endlich(ab):
    """Zahlenfelder mit NaN oder unendlich (json.loads akzeptiert NaN, das Schema auch)."""
    felder = [("gesamtbetrag_netto", ab.get("gesamtbetrag_netto"))]
    for p in ab.get("positionen") or []:
        if isinstance(p, dict):
            for k in ("menge", "einzelpreis_netto", "preiseinheit", "rabatt_prozent", "positionswert_netto"):
                felder.append((f"{p.get('artikelnr_lieferant') or 'Position'} {k}", p.get(k)))
    return [k for k, v in felder if isinstance(v, float) and not math.isfinite(v)]


@dataclass
class Ergebnis:
    status: str                       # "unauffaellig" oder "markiert"
    befunde: list = field(default_factory=list)


def _datum(s, was, befunde):
    if s is None:
        return None
    if isinstance(s, datetime):
        return s.date()
    if isinstance(s, date):
        return s
    try:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):    # nur JJJJ-MM-TT, unabhängig von der Python-Version
            raise ValueError
        return date.fromisoformat(s)
    except (TypeError, ValueError):
        befunde.append(f"{was}: ungültiges Datum {s!r}, manuell prüfen")
        return None


def _netto_je_einheit(p):
    """Einzelpreis nach Rabatt, bezogen auf eine Mengeneinheit (Preis je 100 Stück -> je 1 Stück)."""
    preis = p.get("einzelpreis_netto")
    if preis is None:
        return None
    rabatt = p.get("rabatt_prozent") or 0
    pe = p.get("preiseinheit") or 1
    return preis * (1 - rabatt / 100) / pe


def _soll_aggregieren(bestellung, befunde):
    """Bestellzeilen je Artikelnummer zusammenfassen. Bestellung: {"bestellnummer", "positionen": [ {...}, ... ]}."""
    soll = {}
    for z in bestellung.get("positionen", []):
        z = dict(z)
        for k in ("menge", "einzelpreis_netto", "preiseinheit", "rabatt_prozent"):
            if z.get(k) is not None and _endlich(z[k]) is None:
                befunde.append(f"Bestellexport {z.get('artikelnr_lieferant')}: unplausibler Wert für {k} ({z[k]!r}), "
                               f"manuell prüfen")
                z[k] = None
            elif z.get(k) is not None:
                z[k] = _endlich(z[k])
        if z.get("menge") is None:
            befunde.append(f"Bestellexport {z.get('artikelnr_lieferant')}: Menge fehlt, manuell prüfen")
            z["menge"] = 0
        key = _artnr(z["artikelnr_lieferant"])
        nr = z["artikelnr_lieferant"]
        if key in soll:
            s = soll[key]
            ps, pz = _netto_je_einheit(s), _netto_je_einheit(z)
            if _einheit(s["einheit"]) != _einheit(z["einheit"]) or (ps is not None and pz is not None and abs(ps - pz) > EPS):
                befunde.append(f"Bestellung enthält {nr} mehrfach mit unterschiedlichen Einheiten oder Preisen: manuell prüfen")
            if z.get("liefertermin") not in s["termine"]:
                befunde.append(f"Bestellung enthält {nr} mehrfach mit unterschiedlichen Lieferterminen (Abruf): "
                               f"Termine je Teilmenge manuell prüfen")
                s["termine"].append(z.get("liefertermin"))
            s["menge"] += z["menge"]
        else:
            soll[key] = dict(z, termine=[z.get("liefertermin")])
    return soll


def abgleichen(ab: dict, bestellung: dict, tol: Toleranzen = STANDARD, absender: str = None,
               authentifiziert=None, dmarc_pruefen: bool = True) -> Ergebnis:
    """ab: Ausgabe des Modells nach Schema FALL_B.
    bestellung: Export aus der Warenwirtschaft, {"bestellnummer": str, "lieferant": str (optional),
        "lieferant_domains": [str] (optional), "positionen": [
        {"artikelnr_lieferant", "menge", "einheit", "einzelpreis_netto", "preiseinheit", "rabatt_prozent",
         "liefertermin"}, ...]}
    absender: E-Mail-Adresse, von der die Bestätigung kam (optional). Wird gegen lieferant_domains geprüft.
    authentifiziert: Ergebnis der DMARC-Prüfung des Mailservers für die Absenderdomain. Nur True ("dmarc=pass")
        gilt als bestanden. Jeder andere Wert ("fail", "none", False ...) ergibt einen Befund, ebenso ein fehlender
        Wert, wenn lieferant_domains gesetzt ist. Wer bewusst ohne DMARC arbeitet, setzt dmarc_pruefen=False.
        Die Domainprüfung allein schützt nicht vor gefälschten Absendern.
    Zahlen im Bestellexport als int, float oder Decimal, Termine als date oder "JJJJ-MM-TT", leere Felder als None."""
    befunde = []
    if dmarc_pruefen and authentifiziert is not True and (authentifiziert is not None
                                                           or bestellung.get("lieferant_domains")):
        befunde.append("Absender nicht authentifiziert (DMARC nicht bestanden oder nicht geprüft): Herkunft manuell prüfen")
    try:
        _pruefen(ab, bestellung, tol, befunde, absender)
    except Exception as e:                      # ein fehlerhafter Beleg darf den Lauf nicht stoppen
        befunde.append(f"Beleg konnte nicht vollständig geprüft werden ({type(e).__name__}), weitere Prüfungen "
                       f"nicht durchgeführt: manuell prüfen")
    return Ergebnis("markiert" if befunde else "unauffaellig", befunde)


def _pruefen(ab, bestellung, tol, befunde, absender=None):
    if ab.get("unvollstaendig_lesbar"):
        befunde.append("Dokument nicht vollständig lesbar: manuell prüfen")
    if _nummer(ab.get("bestellnummer")) != _nummer(bestellung.get("bestellnummer")):
        befunde.append(f"Bestellnummer passt nicht: {ab.get('bestellnummer')!r}")
    soll_lief = bestellung.get("lieferant")
    if soll_lief:
        ist_lief = ab.get("lieferant")
        if not ist_lief:
            befunde.append("Lieferant nicht ausgelesen: manuell prüfen")
        else:
            v = _name_vergleich(soll_lief, ist_lief)
            if v == "aehnlich":
                befunde.append(f"Lieferant {ist_lief!r} nur ähnlich zu {soll_lief!r}: prüfen")
            elif v == "anders":
                befunde.append(f"Lieferant {ist_lief!r} passt nicht zur Bestellung ({soll_lief!r}): manuell prüfen")
    domains = [d.lower().lstrip("@") for d in bestellung.get("lieferant_domains") or []]
    if domains:
        if not absender:
            befunde.append("Absender nicht übergeben: Herkunft der Bestätigung manuell prüfen")
        else:
            adresse = parseaddr(absender)[1].strip().lower()
            dom = adresse.rsplit("@", 1)[-1] if "@" in adresse else ""
            if not dom or not any(dom == d or dom.endswith("." + d) for d in domains):
                befunde.append(f"Absender {absender!r} gehört nicht zum Lieferanten: manuell prüfen")
    w = ab.get("waehrung")
    if w is None:
        befunde.append("Währung nicht ausgelesen: manuell prüfen")
    elif WAEHRUNGEN.get(str(w).strip().lower(), str(w).strip().upper()) != "EUR":
        befunde.append(f"Währung {w}: manuell prüfen")
    for k in _nicht_endlich(ab):
        befunde.append(f"{k}: unplausibler Wert (keine endliche Zahl), manuell prüfen")
    for h in ab.get("hinweise") or []:          # Zuschläge, Teuerung, Kalenderwochen, Fracht
        befunde.append(f"Hinweis im Dokument: {h}")

    soll = _soll_aggregieren(bestellung, befunde)

    # Ist-Positionen je Artikel zusammenfassen (geteilte Lieferungen sind zulässig, Mengen werden summiert)
    ist, summe, ohne_nr, anzeige = {}, 0.0, [], {}
    for p in ab.get("positionen") or []:
        key = _artnr(p.get("artikelnr_lieferant"))
        nr = p.get("artikelnr_lieferant")
        wert = p.get("positionswert_netto")
        if wert is not None:
            summe += wert
        if nr is None:
            ohne_nr.append(p)
            continue
        if key not in soll:
            kandidaten = [k for k in soll if _ohne_trenner(k) == _ohne_trenner(key)]
            if len(kandidaten) == 1:
                befunde.append(f"Artikelnummer {nr!r} nur ähnlich zu {soll[kandidaten[0]]['artikelnr_lieferant']!r}: prüfen")
                key = kandidaten[0]
        anzeige.setdefault(key, str(nr).strip())
        ist.setdefault(key, []).append(p)
        r = p.get("rabatt_prozent")
        if (r is not None and not 0 <= r <= 100) or any((p.get(k) or 0) < 0 for k in ("menge", "einzelpreis_netto")):
            befunde.append(f"{nr}: unplausibler Wert (negative Menge oder Preis, Rabatt außerhalb 0–100 %)")
        if p.get("preiseinheit") is not None and p["preiseinheit"] <= 0:
            befunde.append(f"{nr}: unplausible Preiseinheit {p['preiseinheit']}")
            p = dict(p, preiseinheit=1)
            ist[key][-1] = p
        # Kreuzprüfung: Menge x Preis je Einheit = Positionswert?
        netto = _netto_je_einheit(p)
        if wert is not None and netto is not None and p.get("menge") is not None:
            if abs(p["menge"] * netto - wert) > tol.summe_euro:
                befunde.append(f"{nr}: Positionswert {wert:.2f} passt nicht zu Menge x Preis "
                               f"{p['menge'] * netto:.2f}: Auslesefehler möglich")

    for p in ohne_nr:
        befunde.append(f"Position ohne Artikelnummer: {p.get('bezeichnung') or 'ohne Bezeichnung'}")

    for key, zeilen in ist.items():
        nr = soll[key]["artikelnr_lieferant"] if key in soll else anzeige[key]
        try:
            _position_pruefen(key, nr, zeilen, soll, tol, befunde)
        except Exception as e:                  # Fehler in einer Position stoppt nicht die übrigen Prüfungen
            befunde.append(f"{nr}: Position konnte nicht vollständig geprüft werden ({type(e).__name__}): manuell prüfen")

    for key, z in soll.items():
        if key not in ist:
            befunde.append(f"Bestellte Position fehlt in der Bestätigung: {z['artikelnr_lieferant']}")

    gb = ab.get("gesamtbetrag_netto")
    if gb is None:
        befunde.append("Gesamtbetrag nicht ausgelesen: Summenprüfung nicht möglich")
    elif abs(summe - gb) > tol.summe_euro:
        befunde.append(f"Summe der Positionen {summe:.2f} weicht vom Gesamtbetrag {gb:.2f} ab: Auslesefehler möglich")


def _position_pruefen(key, nr, zeilen, soll, tol, befunde):
    if key not in soll:
        befunde.append(f"Position nicht bestellt: {nr}")
        return
    s = soll[key]
    if len(zeilen) > 1:
        befunde.append(f"{nr}: {len(zeilen)} Positionen in der Bestätigung (geteilt oder doppelt?)")
    for p in zeilen:
        if _einheit(p.get("einheit")) != _einheit(s["einheit"]):
            befunde.append(f"{nr}: Einheit {p.get('einheit')} statt {s['einheit']}")
    mengen = [p.get("menge") for p in zeilen]
    if any(m is None for m in mengen):
        befunde.append(f"{nr}: Menge fehlt")
    elif abs(sum(mengen) - s["menge"]) > tol.menge_absolut + EPS:
        befunde.append(f"{nr}: Menge {sum(mengen):g} statt {s['menge']:g}")
    soll_preis = _netto_je_einheit(s)
    if soll_preis is None:
        befunde.append(f"{nr}: kein Sollpreis im Bestellexport, Preis manuell prüfen")
    soll_termine = [t for t in (_datum(x, f"{nr} (Bestellung)", befunde) for x in s["termine"]) if t]
    for p in zeilen:
        netto = _netto_je_einheit(p)
        if netto is None:
            befunde.append(f"{nr}: Preis fehlt")
        elif soll_preis is None:
            pass
        elif soll_preis == 0:
            if netto != 0:
                befunde.append(f"{nr}: Preis {netto:.2f} statt 0,00 (kostenlose Position)")
        else:
            abw = (netto - soll_preis) / soll_preis * 100
            if abs(abw) > tol.preis_prozent + EPS:
                befunde.append(f"{nr}: Preis {netto:.2f} statt {soll_preis:.2f} je Einheit ({abw:+.1f} %)")
        ist_t = _datum(p.get("liefertermin"), nr, befunde)
        soll_t = min(soll_termine, key=lambda t: abs((ist_t - t).days)) if ist_t and soll_termine else None
        if p.get("liefertermin") is None:
            befunde.append(f"{nr}: Liefertermin fehlt")
        elif ist_t and soll_t:
            d = (ist_t - soll_t).days
            if d > tol.termin_spaeter_tage:
                befunde.append(f"{nr}: Liefertermin {ist_t} statt {soll_t} (+{d} Tage)")
            elif -d > tol.termin_frueher_tage:
                befunde.append(f"{nr}: Liefertermin {ist_t} statt {soll_t} ({d} Tage, früher als bestellt)")
        elif ist_t and not soll_termine:
            befunde.append(f"{nr}: kein Solltermin im Bestellexport, manuell prüfen")
