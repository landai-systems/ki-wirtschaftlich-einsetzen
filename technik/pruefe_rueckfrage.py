"""Deterministische Prüfung eines Rückfrage-Entwurfs (Praxisfall C), bevor er einem Mitarbeiter angezeigt wird.

Ein manipulierter Anfragetext kann das Modell zu Entwürfen mit fremdem Inhalt verleiten.
Diese Prüfung markiert Entwürfe mit typischen Mustern für solchen Inhalt: Links, Web- und IP-Adressen,
E-Mail-, Telefon-, Post- und Bankdaten, Messenger-Kanäle, Abfragen sensibler Daten, Geldbeträge,
Termine und Zusagen. Unsichtbare Zeichen und Steuerzeichen werden gemeldet und vor der Prüfung entfernt.

Grenzen: Die Prüfung arbeitet mit Mustern. Sie erkennt typische Fälle, nicht jede denkbare
Formulierung. Sie erkennt auch nicht, wenn eine Injektion das Prüfergebnis selbst verändert,
etwa „alle Angaben liegen vor“. Sie ersetzt deshalb nicht die Durchsicht durch einen Menschen,
der den Entwurf neben der Originalanfrage sieht, und nicht die Stichprobe der als vollständig
eingestuften Anfragen. Wirksamer als jede Musterprüfung ist, den Rückfragetext aus freigegebenen
Textbausteinen je fehlender Angabe zusammenzusetzen (siehe rueckfrage_aus_bausteinen).
"""
import re
import unicodedata

MONATE = r"(januar|februar|märz|maerz|april|mai|juni|juli|august|september|oktober|november|dezember)"
ZAHLWORT = r"(ein|eine|einem|einer|zwei|drei|vier|fünf|fuenf|sechs|sieben|acht|neun|zehn|zwölf|zwoelf|vierzehn|zwanzig|dreißig)"
WOCHENTAGE = r"(montag|dienstag|mittwoch|donnerstag|freitag|samstag|sonnabend|sonntag)(s|en)?"
PUNKT = r"(\.|\s+\.\s+|\s*[\(\[\{]\s*(\.|dot|punkt)\s*[\)\]\}]\s*|\s+(?-i:dot|DOT|Dot|punkt|PUNKT)\s+)"
ENDUNG = r"(?P<endung>[A-Za-z]{2,24})\b(?!-)"
TLD = {"com", "de", "net", "org", "eu", "info", "io", "at", "ch", "biz", "shop", "online", "app", "ly", "me", "co",
       "uk", "fr", "it", "nl", "es", "pl", "ru", "cn", "xyz", "site", "link", "click", "top"}
ABKUERZUNGEN = {"bzw", "ca", "ggf", "inkl", "evtl", "usw", "etc", "vgl", "max", "min", "nr", "tel", "str", "zzgl",
                "bspw", "insb", "abs", "ff", "mind", "gem", "ugs", "allg", "sog", "dh", "zb", "ua", "uvm"}

MUSTER = {
    "E-Mail-Adresse": re.compile(r"[\w.+-]+\s*(@|[\(\[\{]\s*(at|ät)\s*[\)\]\}]|\s+(?-i:at|AT|ät)\s+)\s*[\w-]+" + PUNKT + r"[a-z]{2,}", re.I),
    "Bankverbindung": re.compile(r"(\b(IBAN|BIC|SWIFT|Kontonummer|Bankverbindung|Bankdaten|Bankkont\w*|Kontodaten|Kontoverbindung|Kreditkart\w*|PayPal)\b"
                                 r"|(?-i:\b[A-Z]{2}\d{2}(?:[\s-]?[A-Z0-9]){11,30}\b)|(?-i:\b[A-Z]{2}\d{2}([\s-]?[A-Z0-9]{4})+\b))", re.I),
    "Abfrage sensibler Daten": re.compile(
        r"\b(passw(o|ö)rt\w*|kennw(o|ö)rt\w*|PINs?|TANs?|TAN-\w*|Zugangsdaten|Zugangsnummer|Anmeldedaten|Benutzername|"
        r"(Bestätigungs|Sicherheits|Zugangs|Freischalt|Aktivierungs|SMS-)code\w*|Login\w*|Geburtsdatum|Personalausweis\w*|"
        r"Ausweis\w*|Steuer-?ID|Sozialversicherungs\w*|EC-Karte\w*|Girocard|Kartennummer|\w*prüfnummer|Geheimzahl\w*|"
        r"Codes?\s+(aus|in)\s+(der|einer|Ihrer)\s+SMS|"
        r"CVC|CVV|Online-?Banking)\b", re.I),
    "Messenger oder anderer Kanal": re.compile(r"\b(WhatsApp|Telegram|Signal|Threema|Messenger|Instagram|Facebook|"
                                               r"TikTok|Skype|Discord|Snapchat|WeChat|Viber|(per|via|über)\s+SMS)\b", re.I),
    "Postadresse": re.compile(r"((straße|strasse|str\.|weg|gasse|platz|allee|ring|damm)\s+\d+(?!\d)(?![.,]\d)(?!\s?(m|cm|mm|km|m²|qm|Meter)\b)|\b\d{5}\s+[A-ZÄÖÜ][a-zäöüß]+"
                              r"|\bPostfach\b|(?-i:\b(Am|An der|Im|In der|Auf der|Zum|Zur)\s+[A-ZÄÖÜ][a-zäöüß]+\s+\d+[a-z]?\b))",
                              re.I),
    "Geldbetrag oder Zahlung": re.compile(r"(\d[\d.,]*\s?(,-|€|£|¥|EUR|Euro|USD|CHF|GBP|\$|Dollar|Pfund|Franken)"
                             r"|(€|£|EUR|USD|CHF|GBP|\$)\s?\d|\b(Euro|Dollar|Franken|Pfund)\b"
                             r"|\b(Vorkasse|Anzahlung|Vorauszahlung|Überweisung|überweisen)\b)", re.I),
    "Datum oder Termin": re.compile(
        r"(\b\d{1,2}\.\s?(\d{1,2}\.(\d{2,4})?|" + MONATE + r")|\b" + MONATE + r"\b|\bKW\s?\d{1,2}|\b\d{1,2}\.\s*KW\b"
        r"|\bKalenderwoche\s*\d|\b" + WOCHENTAGE + r"\b|\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}([:.]\d{2})?\s*Uhr\b|"
        r"\b(innerhalb|binnen|in|nach)\s+(von\s+)?(\d+|" + ZAHLWORT + r")\s+(Werk|Arbeits)?(tag|tage|tagen|woche|wochen|monat|monaten)\b|"
        r"\b\d+\s*(-\s*\d+\s*)?(Werk|Arbeits)?(Tag|Tage|Tagen|Woche|Wochen|Monat|Monate|Monaten)\b|"
        r"\b(Monats|Wochen|Jahres|Quartals)(ende|anfang|beginn)\b|"
        r"\b(Ende|Anfang|Mitte)\s+(des|dieses|nächsten)(\s+(nächsten|kommenden|laufenden))?\s+(Monats|Jahres|Quartals)\b|"
        r"(?<!Guten )\b(heute|morgen|übermorgen)\b|\b(Weihnachten|Ostern|Pfingsten|Silvester|Neujahr)\b|"
        r"\b(diese|kommende|nächste|übernächste)\w*\s+Woche\b|"
        r"\bbis\s+(zum|spätestens)\s+(\d|Ende|Monats|Jahres|nächst|kommend|Wochenende|" + MONATE + r")|\bab\s+sofort\b)", re.I),
    "Zusage": re.compile(r"\b(garantier\w*|verbindlich\w*|zusag\w*|sichern\s+(wir|Ihnen)\s+zu|Festpreis|Rabatt|"
                         r"kostenlos\w*|kostenfrei\w*|gratis|unentgeltlich|ohne\s+Aufpreis|Preisnachlass|Nachlass|Skonto|"
                         r"übernehmen\s+wir|wir\s+übernehmen|geht\s+auf\s+uns|im\s+Preis\s+(enthalten|inbegriffen|inklusive)|"
                         r"Preis\s+inklusive)\b|\b\d+([.,]\d+)?\s?(%|Prozent\b)", re.I),
}
LINK = re.compile(r"(https?://|\bwww\s*" + PUNKT + r"|\b(?P<links>[\w-]{2,})" + PUNKT + ENDUNG + ")", re.I)
IPV4 = re.compile(r"\b\d{1,3}(\s*\.\s*\d{1,3}){3}\b")
TELEFON = re.compile(r"(\+|(?<![\d.,])\b0)[\d\s()/.-]{5,}\d(?![\d.,]*\s?(mm|cm|m|x|×)\b)")
# Ein-Buchstaben-Domains wie t.me/ oder x.com/ (nur bekannte Endung mit Pfad)
LINK_KURZ = re.compile(r"\b\w\.(?P<endung>[a-z]{2,6})/", re.I)
# Dezimalzahl ohne Währung (z. B. 1.250,00) gilt als Betrag, außer vor Einheiten oder nach "...wert"
BETRAG = re.compile(r"\b\d{1,3}(\.\d{3})*,\d{2}\b")
EINHEIT = re.compile(r"\s?(x|×|m|cm|mm|km|m²|m2|qm|kW|W|kg|t|l|°|/|Meter|Zentimeter|Millimeter)\b|\s?(/|×|°)", re.I)
IBAN_LOSE = re.compile(r"\b[a-z]{2}\d{2}(?:[\s-]?[a-z0-9]){11,30}\b", re.I)
# übliche, harmlose Wendungen, die sonst als Zusage gälten
HARMLOS = re.compile(r"\b((un)?verbindliche[nrs]?|kostenlose[nrs]?)\s+(Angebot\w*|Kostenvoranschl\w*|Aufmaß\w*|Beratung\w*)\b",
                     re.I)


def _unsichtbar(c: str) -> bool:
    return unicodedata.category(c) in ("Cf", "Co", "Cn")


def _normalisieren(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("。", ".").replace("｡", ".")
    return " ".join(text.split())   # Leerraum vereinheitlichen (doppelte Leerzeichen, Zeilenumbrüche)


def _link(text: str) -> bool:
    for m in LINK.finditer(text):
        links, endung = m.group("links"), m.group("endung")
        if links is None:
            return True
        if links.casefold() in ABKUERZUNGEN:
            continue
        # Endung klein oder groß geschrieben gilt immer, gemischte Schreibung nur bei bekannten Endungen
        if endung.islower() or endung.isupper() or endung.casefold() in TLD:
            return True
    if any(m.group("endung").casefold() in TLD for m in LINK_KURZ.finditer(text)):
        return True
    return bool(IPV4.search(text))


def _betrag(text: str) -> bool:
    for m in BETRAG.finditer(text):
        if EINHEIT.match(text, m.end()) or re.search(r"wert\W{0,3}(\w+\W+)?$", text[max(0, m.start() - 25):m.start()], re.I):
            continue
        return True
    return False


def _iban(text: str) -> bool:
    """IBAN in beliebiger Schreibweise, bestätigt über die Prüfziffer (mod 97)."""
    for m in IBAN_LOSE.finditer(text):
        s = re.sub(r"[\s-]", "", m.group()).upper()
        if 15 <= len(s) <= 34:
            n = "".join(str(int(c, 36)) for c in s[4:] + s[:4])
            if int(n) % 97 == 1:
                return True
    return False


def _telefon(text: str) -> bool:
    return any(sum(ch.isdigit() for ch in m.group()) >= 7 for m in TELEFON.finditer(text))


def anfragetyp_normalisieren(ergebnis: dict, typen: list) -> dict:
    """Bildet den Anfragetyp auf die kanonische Schreibweise der Liste ab (Groß-/Kleinschreibung und
    Leerzeichen sind bei enum-Werten nicht garantiert). Unbekannte Werte werden zu "unklar"."""
    kanon = {_schluessel(t): t for t in list(typen) + ["unklar"]}
    typ = ergebnis.get("anfragetyp")
    return dict(ergebnis, anfragetyp=kanon.get(_schluessel(typ), "unklar") if typ is not None else None)


def _schluessel(s) -> str:
    """Vergleichsschlüssel: Unicode-NFC, Groß-/Kleinschreibung und Leerraum ignorieren."""
    return " ".join(unicodedata.normalize("NFC", str(s)).casefold().split())


def rueckfrage_aus_bausteinen(fehlend: list, bausteine: dict, anrede: str, gruss: str) -> tuple:
    """Setzt die Rückfrage aus freigegebenen Textbausteinen zusammen. Das Modell liefert nur die Liste
    der fehlenden Angaben; kein Modelltext gelangt in die Nachricht. Rückgabe: (text, unbekannte_angaben).
    Passt keine Angabe zu einem Baustein, ist text None. Anrede und Gruß nur aus festen Vorlagen oder geprüften
    Stammdaten übergeben, nie aus der Anfrage selbst."""
    nach_schluessel = {_schluessel(k): v for k, v in bausteine.items()}
    zeilen, unbekannt = [], []
    for f in dict.fromkeys(fehlend):
        b = nach_schluessel.get(_schluessel(f))
        if b is None:
            unbekannt.append(f)
        elif "- " + b not in zeilen:
            zeilen.append("- " + b)
    if not zeilen:
        return None, unbekannt
    text = "\n".join([anrede, "", "damit wir Ihre Anfrage bearbeiten können, benötigen wir noch:", *zeilen, "", gruss])
    return text, unbekannt


def pruefe_entwurf(ergebnis: dict, max_laenge: int = 1200, variante: str = "entwurf") -> list:
    """ergebnis: Modellausgabe nach Schema FALL_C. Rückgabe: Liste von Warnungen (leer = unauffällig).
    variante="bausteine": Ergebnis aus dem Schema ohne Entwurf (fall_c_schema(..., mit_entwurf=False)); dann
    entfallen die Regeln zum Entwurf, ein dennoch vorhandener Entwurf wird gemeldet."""
    if variante not in ("entwurf", "bausteine"):
        raise ValueError("variante muss 'entwurf' oder 'bausteine' sein")
    warnungen = []
    entwurf = ergebnis.get("rueckfrage_entwurf")
    fehlend = ergebnis.get("fehlend") or []
    if variante == "bausteine":
        if entwurf:
            warnungen.append("Rückfrage-Entwurf vorhanden, obwohl die Baustein-Variante keinen vorsieht")
    elif fehlend and not entwurf:
        warnungen.append("Angaben fehlen, aber kein Rückfrage-Entwurf vorhanden")
    elif entwurf and not fehlend:
        warnungen.append("Rückfrage-Entwurf vorhanden, obwohl nichts als fehlend gemeldet ist")
    typ = ergebnis.get("anfragetyp")
    if typ is None or _schluessel(typ) in ("", "unklar"):
        warnungen.append("Anfragetyp unklar: Anfrage selbst prüfen")
    if entwurf:
        if any(_unsichtbar(c) for c in entwurf):
            warnungen.append("Entwurf enthält unsichtbare Zeichen oder Steuerzeichen: vor Versand prüfen")
        text = _normalisieren("".join(c for c in entwurf if not _unsichtbar(c)))
        if _link(text):
            warnungen.append("Entwurf enthält Link oder Webadresse: vor Versand prüfen")
        if _telefon(text):
            warnungen.append("Entwurf enthält Telefonnummer: vor Versand prüfen")
        if _iban(text):
            warnungen.append("Entwurf enthält Bankverbindung (IBAN): vor Versand prüfen")
        ohne_harmlos = HARMLOS.sub(" ", text)
        for name, muster in MUSTER.items():
            if muster.search(ohne_harmlos if name == "Zusage" else text):
                warnungen.append(f"Entwurf enthält {name}: vor Versand prüfen")
        if _betrag(text) and "Entwurf enthält Geldbetrag oder Zahlung: vor Versand prüfen" not in warnungen:
            warnungen.append("Entwurf enthält Geldbetrag oder Zahlung: vor Versand prüfen")
        if len(text) > max_laenge:
            warnungen.append("Entwurf ungewöhnlich lang")
    if ergebnis.get("hinweise_fuer_bearbeitung"):
        warnungen.append("Modell meldet Auffälligkeiten im Anfragetext")
    return warnungen
