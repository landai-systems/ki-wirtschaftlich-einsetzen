"""JSON-Schemas für die strukturierten Ausgaben der drei Praxisfälle.

Regeln: Fehlt ein Einzelwert, ist er null. Gibt es zu einer Liste keine Einträge, ist sie leer ([]).
Fehlendes wird zusätzlich in einer eigenen Liste benannt, damit die Prüfmaske es hervorheben kann.
Ein Datum muss ein gültiges Kalenderdatum sein ("format": "date"); der Validator wird dafür mit
FormatChecker aufgerufen. Wertebereiche (keine negativen Mengen, Rabatt 0–100 %) prüft der
nachgelagerte Code, weil nicht jede Schnittstelle für strukturierte Ausgaben Zahlengrenzen im Schema unterstützt.
"""

NULLABLE_STR = {"type": ["string", "null"]}
NULLABLE_NUM = {"type": ["number", "null"]}
NULLABLE_DATE = {"anyOf": [{"type": "string", "format": "date"}, {"type": "null"}]}
STR_LIST = {"type": "array", "items": {"type": "string"}}

# Fall A: Datum und Uhrzeit kommen aus den Metadaten der Aufnahme, nicht vom Modell.
FALL_A_MONTAGEBERICHT = {
    "type": "object",
    "additionalProperties": False,
    "required": ["baustelle_id", "abweichendes_datum_genannt", "personen", "material", "zusatzleistungen",
                 "auffaelligkeiten", "fehlende_angaben", "unsichere_angaben"],
    "properties": {
        "baustelle_id": NULLABLE_STR,
        "abweichendes_datum_genannt": NULLABLE_STR,
        "personen": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["mitarbeiter_id", "name_wie_genannt", "stunden"],
            "properties": {"mitarbeiter_id": NULLABLE_STR, "name_wie_genannt": NULLABLE_STR,
                           "stunden": NULLABLE_NUM}}},
        "material": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["bezeichnung", "menge", "einheit", "katalog_nr"],
            "properties": {"bezeichnung": NULLABLE_STR, "menge": NULLABLE_NUM,
                           "einheit": NULLABLE_STR, "katalog_nr": NULLABLE_STR}}},
        "zusatzleistungen": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["beschreibung", "stunden"],
            "properties": {"beschreibung": NULLABLE_STR, "stunden": NULLABLE_NUM}}},
        "auffaelligkeiten": STR_LIST,
        "fehlende_angaben": STR_LIST,
        "unsichere_angaben": STR_LIST,
    },
}

FALL_B_AUFTRAGSBESTAETIGUNG = {
    "type": "object",
    "additionalProperties": False,
    "required": ["bestellnummer", "lieferant", "ab_datum", "positionen",
                 "gesamtbetrag_netto", "waehrung", "hinweise", "unvollstaendig_lesbar"],
    "properties": {
        "bestellnummer": NULLABLE_STR,
        "lieferant": NULLABLE_STR,
        "ab_datum": NULLABLE_DATE,
        "positionen": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["pos", "artikelnr_lieferant", "bezeichnung", "menge", "einheit",
                         "einzelpreis_netto", "preiseinheit", "rabatt_prozent", "positionswert_netto", "liefertermin"],
            "properties": {
                "pos": NULLABLE_STR, "artikelnr_lieferant": NULLABLE_STR,
                "bezeichnung": NULLABLE_STR, "menge": NULLABLE_NUM, "einheit": NULLABLE_STR,
                "einzelpreis_netto": NULLABLE_NUM, "preiseinheit": NULLABLE_NUM, "rabatt_prozent": NULLABLE_NUM,
                "positionswert_netto": NULLABLE_NUM, "liefertermin": NULLABLE_DATE}}},
        "gesamtbetrag_netto": NULLABLE_NUM,
        "waehrung": NULLABLE_STR,
        "hinweise": STR_LIST,
        "unvollstaendig_lesbar": {"type": "boolean"},
    },
}

FALL_C_ANFRAGE = {
    "type": "object",
    "additionalProperties": False,
    "required": ["anfragetyp", "vorhanden", "fehlend", "rueckfrage_entwurf", "hinweise_fuer_bearbeitung"],
    "properties": {
        "anfragetyp": {"type": "string"},
        "vorhanden": STR_LIST,
        "fehlend": STR_LIST,
        "rueckfrage_entwurf": NULLABLE_STR,
        "hinweise_fuer_bearbeitung": STR_LIST,
    },
}


def fall_c_schema(anfragetypen, pflichtangaben=None, mit_entwurf=True):
    """Schema für Fall C mit fester Liste der Anfragetypen des eigenen Betriebs (plus "unklar").
    Ein Anfragetyp außerhalb der Liste wird dann schon vom Schema abgelehnt. Mit pflichtangaben
    (Liste der Bezeichnungen, für die es Textbausteine gibt) dürfen "vorhanden" und "fehlend" nur
    diese Werte enthalten. Für die empfohlene Variante rueckfrage_aus_bausteinen mit_entwurf=False setzen:
    Das Modell liefert dann keinen Rückfrage-Entwurf, das Feld entfällt. Doppelte Werte werden entfernt."""
    import copy
    s = copy.deepcopy(FALL_C_ANFRAGE)
    typen = list(dict.fromkeys([*anfragetypen, "unklar"]))
    s["properties"]["anfragetyp"] = {"type": "string", "enum": typen}
    if pflichtangaben:
        werte = list(dict.fromkeys(pflichtangaben))
        for feld in ("vorhanden", "fehlend"):
            s["properties"][feld] = {"type": "array", "items": {"type": "string", "enum": werte}}
    if not mit_entwurf:
        del s["properties"]["rueckfrage_entwurf"]
        s["required"].remove("rueckfrage_entwurf")
    return s
