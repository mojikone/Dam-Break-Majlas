# -*- coding: utf-8 -*-
"""Open the built report in Word, update every field (TOC, lists, SEQ, REF), save, export PDF, and render pages to PNG for review.
Run after build_report.py:  python render_pdf.py [page numbers to render, e.g. 1 3 5-8]"""
import os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); W1 = os.path.abspath(os.path.join(HERE, ".."))
REV = "R0"
RUNSHEET = "--runsheet" in sys.argv
if RUNSHEET: sys.argv.remove("--runsheet")
DOCX = os.path.join(W1, "05_report", REV, "Wadi Majlas Dam Break Analysis - HEC-RAS Run Sheet Rev00.docx" if RUNSHEET
                    else "Wadi Majlas Dam Break Analysis Methodology Report Rev00.docx")
PDF = DOCX[:-5] + ".pdf"
REVIEW = os.path.join(W1, "05_report", "_review_runsheet" if RUNSHEET else "_review")

def word_update_and_export():
    import win32com.client as w
    app = w.dynamic.Dispatch("Word.Application"); app.Visible = False; app.DisplayAlerts = 0
    doc = app.Documents.Open(DOCX, ReadOnly=False)
    doc.Fields.Update()
    for t in doc.TablesOfContents: t.Update()
    for t in doc.TablesOfFigures: t.Update()
    doc.Fields.Update(); doc.Repaginate()
    print("pages:", doc.ComputeStatistics(2), "words:", doc.ComputeStatistics(0), "footnotes:", doc.Footnotes.Count,
          "tables:", doc.Tables.Count, "pictures:", doc.InlineShapes.Count)
    doc.Save(); doc.ExportAsFixedFormat(PDF, 17); doc.Close(False); app.Quit()
    print("pdf:", os.path.getsize(PDF) // 1024, "kB")

def render(pages):
    import fitz
    os.makedirs(REVIEW, exist_ok=True)
    for f in glob.glob(os.path.join(REVIEW, "p*.png")): os.remove(f)
    pdf = fitz.open(PDF); n = len(pdf)
    want = set()
    for p in pages:
        if "-" in p: a, b = p.split("-"); want.update(range(int(a), int(b) + 1))
        else: want.add(int(p))
    for i in sorted(want):
        if 1 <= i <= n:
            pix = pdf[i - 1].get_pixmap(dpi=80); out = os.path.join(REVIEW, f"p{i:03d}.png"); pix.save(out); print("rendered", out)
    print("total pages", n)

if __name__ == "__main__":
    word_update_and_export()
    if len(sys.argv) > 1: render(sys.argv[1:])
