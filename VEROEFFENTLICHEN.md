# Veröffentlichung einer Version

Diese Anleitung gilt für die Person mit Schreibrechten am Repository `landai-systems/ki-wirtschaftlich-einsetzen`.
Die Download-Links in der README zeigen auf `releases/download/v1.0/…`; sie funktionieren erst, wenn das Release
mit genau diesem Tag und diesen Dateinamen veröffentlicht ist.

## 1. Prüfen

```
pip install -r technik/requirements.txt openpyxl
cd technik && python -m pytest -q && python beispiele/beispiele_pruefen.py && cd ..
python werkzeuge/kontrollrechnung.py unternehmer/KI-Wirtschaftlichkeitsrechner.xlsx
```

## 2. Pakete bauen

```
python werkzeuge/pakete_bauen.py
```

Ergebnis in `dist/`: `KI-Wirtschaftlich-Einsetzen_Unternehmer_V1.0.zip` und `KI-Wirtschaftlich-Einsetzen_Technik_V1.0.zip`.

## 3. Hochladen und Release anlegen

```
git init -b main          # nur beim ersten Mal
git add . && git commit -m "Version 1.0"
git remote add origin https://github.com/landai-systems/ki-wirtschaftlich-einsetzen.git   # nur beim ersten Mal
git push -u origin main
gh release create v1.0 dist/KI-Wirtschaftlich-Einsetzen_Unternehmer_V1.0.zip dist/KI-Wirtschaftlich-Einsetzen_Technik_V1.0.zip \
  --title "Version 1.0" --notes-file CHANGELOG.md
```

Ohne GitHub-Kommandozeile: auf github.com unter „Releases › Draft a new release“ den Tag `v1.0` anlegen und die
beiden ZIP-Dateien hochladen.

## 4. Kontrollieren

Beide Download-Links der README in einem privaten Browserfenster (ohne Anmeldung) anklicken.

## Neue Version

Version in `werkzeuge/pakete_bauen.py`, README (Links und Versionsstand), `CHANGELOG.md` und `technik/README.md`
anpassen, Rechner bei Änderungen mit `werkzeuge/excel_unternehmer.py` neu erzeugen und mit LibreOffice neu
berechnen, dann Schritte 1 bis 4.
