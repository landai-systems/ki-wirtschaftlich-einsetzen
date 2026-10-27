"""Erzeugt die PDF-Dokumente des Unternehmerpakets aus den Markdown-Quellen (pandoc + Chromium/Playwright).
Aufruf: python werkzeuge/pdf_bauen.py"""
import os, subprocess
from playwright.sync_api import sync_playwright
H = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(H)
Q, Z = os.path.join(W, "unternehmer", "quellen"), os.path.join(W, "unternehmer")
DOKS = {"kurzanleitung": "Kurzanleitung.pdf", "entscheidungshilfe": "Entscheidungshilfe.pdf",
        "dienstleister-checkliste": "Dienstleister-Checkliste.pdf"}
with sync_playwright() as p:
    b = p.chromium.launch()
    for q, ziel in DOKS.items():
        html = os.path.join(Q, q + ".html")
        subprocess.run(["pandoc", os.path.join(Q, q + ".md"), "-s", "--embed-resources", "--css",
                        os.path.join(H, "pdf.css"), "-o", html, "--metadata", "lang=de-DE"], check=True)
        pg = b.new_page(); pg.goto("file://" + html)
        pg.pdf(path=os.path.join(Z, ziel), format="A4", print_background=True, display_header_footer=True,
               header_template="<span></span>",
               footer_template='<div style="font-size:8px;width:100%;text-align:center;color:#777">'
                               'KI wirtschaftlich einsetzen · Begleitmaterial 1.0 · Seite <span class="pageNumber"></span>'
                               ' von <span class="totalPages"></span></div>',
               margin={"top": "18mm", "bottom": "20mm", "left": "18mm", "right": "18mm"})
        os.remove(html); print(ziel)
    b.close()
