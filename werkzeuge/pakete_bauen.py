"""Baut die beiden Release-Pakete nach dist/. Aufruf aus dem Repository-Wurzelordner: python werkzeuge/pakete_bauen.py"""
import os, zipfile
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = "1.0"
AUSLASSEN = {"__pycache__", ".pytest_cache", ".venv", "quellen"}
PAKETE = {f"KI-Wirtschaftlich-Einsetzen_Unternehmer_V{VERSION}.zip": "unternehmer",
          f"KI-Wirtschaftlich-Einsetzen_Technik_V{VERSION}.zip": "technik"}
os.makedirs(os.path.join(W, "dist"), exist_ok=True)
for name, ordner in PAKETE.items():
    wurzel = name[:-4]
    with zipfile.ZipFile(os.path.join(W, "dist", name), "w", zipfile.ZIP_DEFLATED) as z:
        for d, dirs, files in os.walk(os.path.join(W, ordner)):
            dirs[:] = sorted(x for x in dirs if x not in AUSLASSEN)
            for f in sorted(files):
                if f.endswith(".pyc"):
                    continue
                p = os.path.join(d, f)
                z.write(p, os.path.join(wurzel, os.path.relpath(p, os.path.join(W, ordner))))
        for f in ("LIZENZ.md", "CHANGELOG.md"):
            z.write(os.path.join(W, f), os.path.join(wurzel, f))
    print(name, len(z.namelist()) if False else "")
