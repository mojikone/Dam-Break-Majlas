# -*- coding: utf-8 -*-
"""Open the built report in Word, update every field (TOC, lists, SEQ, REF), save, export PDF, and render pages to PNG for review.
Run after build_report.py:  python render_pdf.py [page numbers to render, e.g. 1 3 5-8]"""
import os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); W1 = os.path.abspath(os.path.join(HERE, ".."))
REV = "R0"
RUNSHEET = "--runsheet" in sys.argv; RESULTS = "--results" in sys.argv; RENDER_ONLY = "--render-only" in sys.argv
for flag in ("--runsheet", "--results", "--render-only"):
    if flag in sys.argv: sys.argv.remove(flag)
DOCX = os.path.join(W1, "05_report", REV, "Wadi Majlas Dam Break Analysis - HEC-RAS Run Sheet Rev00.docx" if RUNSHEET
                    else "Wadi Majlas Dam Break Analysis Report Rev00.docx" if RESULTS
                    else "Wadi Majlas Dam Break Analysis Methodology Report Rev00.docx")
PDF = DOCX[:-5] + ".pdf"
REVIEW = os.path.join(W1, "05_report", "_review_runsheet" if RUNSHEET else "_review_results" if RESULTS else "_review")

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
    doc.Save()
    try:
        doc.ExportAsFixedFormat(PDF, 17); out = PDF
    except Exception:  # target held open by a viewer: export beside it and try to swap in
        tmp = PDF[:-4] + "_new.pdf"; doc.ExportAsFixedFormat(tmp, 17); out = tmp
        try: os.replace(tmp, PDF); out = PDF
        except OSError: print("WARNING: PDF is locked by another program; written to", tmp)
    finally:
        doc.Close(False); app.Quit()
    print("pdf:", os.path.getsize(out) // 1024, "kB")
    return out

def render(pages):
    import fitz
    os.makedirs(REVIEW, exist_ok=True)
    for f in glob.glob(os.path.join(REVIEW, "p*.png")): os.remove(f)
    src = PDF if os.path.exists(PDF) and not os.path.exists(PDF[:-4] + "_new.pdf") else PDF[:-4] + "_new.pdf"
    pdf = fitz.open(src); n = len(pdf)
    want = set()
    for p in pages:
        if "-" in p: a, b = p.split("-"); want.update(range(int(a), int(b) + 1))
        else: want.add(int(p))
    for i in sorted(want):
        if 1 <= i <= n:
            pix = pdf[i - 1].get_pixmap(dpi=80); out = os.path.join(REVIEW, f"p{i:03d}.png"); pix.save(out); print("rendered", out)
    print("total pages", n)

if __name__ == "__main__":
    if not RENDER_ONLY: word_update_and_export()
    if len(sys.argv) > 1: render(sys.argv[1:])
