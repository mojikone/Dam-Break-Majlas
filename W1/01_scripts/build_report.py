# -*- coding: utf-8 -*-
"""Build the Dam Break Analysis Methodology Report (Word) from the Hydrology Report template.

Keeps from the template: cover, styles, headers/footers, TOC / List of Figures / List of Tables fields, numbering, theme.
Replaces: cover title and date, header title, and everything from 'Abbreviations and Nomenclature' to the end.
Adds: real Word footnotes (word/footnotes.xml), native OMML equations, SEQ-numbered captions with bookmarks and REF
cross-references, landscape sections for maps and wide flowcharts.

Run:  python build_report.py        -> W1/05_report/R0/Wadi Majlas Dam Break Analysis Methodology Report Rev00.docx
"""
import os, re, sys, shutil, zipfile, struct
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
W1 = os.path.abspath(os.path.join(HERE, ".."))
REV = "R0"
TEMPLATE = r"D:/Mojtaba/Renardet/2224 WS11/Majlas/Hydrology/Report/Wadi Majlas Hydrology Report.docx"
OUT_DIR = os.path.join(W1, "05_report", REV)
OUT_DOCX = os.path.join(OUT_DIR, "Wadi Majlas Dam Break Analysis Methodology Report Rev00.docx")
WORK = os.path.join(W1, "05_report", "_build")
FIG = os.path.join(W1, "02_figures")

TITLE_LINE = "Dam Break Analysis Methodology Report"
DATE_LINE = "September 2026"
MINISTRY = "Ministry of Agriculture, Fisheries Wealth & Water Resources"
HEADER_TITLE = "Wadi Majlas Flood Protection Dam-Dam Break Analysis Methodology Report"

W_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

# ------------------------------------------------------------------ text helpers
def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))

def run(text, bold=False, italic=False, sz=None, color=None, sub=False, sup=False):
    inner = ""
    if bold: inner += "<w:b/>"
    if italic: inner += "<w:i/>"
    if color: inner += f'<w:color w:val="{color}"/>'
    if sz: inner += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    if sub: inner += '<w:vertAlign w:val="subscript"/>'
    if sup: inner += '<w:vertAlign w:val="superscript"/>'
    rpr = f"<w:rPr>{inner}</w:rPr>" if inner else ""
    return f'<w:r>{rpr}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'

class Doc:
    """Collects body XML, footnotes, media and figure/table numbers. Content functions receive it as `d`."""
    def __init__(self):
        self.xml = []; self.footnotes = []; self.media = []; self.rels = []
        self.fign = {}; self.tbln = {}; self.eqn = {}
        self._fig = 0; self._tbl = 0; self._eq = 0; self._rid = 900; self._docpr = 1000; self._bmk = 4000
        self.pass_no = 1   # 1 = number figures/tables only, 2 = render

    # ---- inline markup: **bold**, _{sub}, ^{sup}, [[fn: ...]], {{f:key}}, {{t:key}}, {{e:key}}
    def _reffield(self, name, num):
        return ('<w:r><w:fldChar w:fldCharType="begin"/></w:r>'
                f'<w:r><w:instrText xml:space="preserve"> REF {name} \\h \\* CHARFORMAT </w:instrText></w:r>'
                '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
                f'<w:r><w:t>{num}</w:t></w:r>'
                '<w:r><w:fldChar w:fldCharType="end"/></w:r>')

    def _footnote_ref(self, text):
        self.footnotes.append(text); n = len(self.footnotes)
        return f'<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:footnoteReference w:id="{n}"/></w:r>'

    def inline(self, text, bold=False):
        out = ""
        # tokens may arrive with double braces, or single braces when the text was an f-string
        for seg in re.split(r'(\[\[fn:.*?\]\]|\{\{?[fte]:[A-Za-z0-9_]+\}\}?|\*\*.+?\*\*|_\{[^}]*\}|\^\{[^}]*\})', text):
            if not seg: continue
            if seg.startswith("[[fn:"):
                out += self._footnote_ref(seg[5:-2].strip()); continue
            m = re.match(r'\{\{?([fte]):([A-Za-z0-9_]+)\}\}?$', seg)
            if m:
                kind, key = m.groups()
                reg, pref, label = {"f": (self.fign, "_Ref_fig_", "Figure "), "t": (self.tbln, "_Ref_tbl_", "Table "), "e": (self.eqn, "_Ref_eq_", "")}[kind]
                num = reg.get(key, "0")
                out += (run(label, bold=bold) + self._reffield(pref + key, num)) if kind != "e" else run(f"({num})", bold=bold); continue
            if seg.startswith("**") and seg.endswith("**"):
                out += self.inline(seg[2:-2], bold=True); continue
            if seg.startswith("_{"): out += run(seg[2:-1], bold=bold, sub=True); continue
            if seg.startswith("^{"): out += run(seg[2:-1], bold=bold, sup=True); continue
            out += run(seg, bold=bold)
        return out

    # ---- blocks
    def add(self, xml): self.xml.append(xml)
    def H1(self, text, numbered=True):
        st = "Heading1" if numbered else "Heading1NoNumber"
        self.add(f'<w:p><w:pPr><w:pStyle w:val="{st}"/></w:pPr>{run(text)}</w:p>')
    def H2(self, text): self.add(f'<w:p><w:pPr><w:pStyle w:val="Heading2"/></w:pPr>{run(text)}</w:p>')
    def H3(self, text): self.add(f'<w:p><w:pPr><w:pStyle w:val="Heading3"/></w:pPr>{run(text)}</w:p>')
    def P(self, text, style="BodyText", jc=None):
        ppr = f'<w:pStyle w:val="{style}"/>' + (f'<w:jc w:val="{jc}"/>' if jc else "")
        self.add(f'<w:p><w:pPr>{ppr}</w:pPr>{self.inline(text)}</w:p>')
    def BUL(self, text): self.add(f'<w:p><w:pPr><w:pStyle w:val="Bullet"/></w:pPr>{self.inline(text)}</w:p>')
    def BULS(self, items):
        for t in items: self.BUL(t)
    def PAGEBREAK(self): self.add('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')

    CAP_RPR = '<w:rPr><w:b w:val="0"/><w:bCs w:val="0"/><w:i/><w:iCs/><w:color w:val="404040"/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
    def SUB(self, text):
        """Unnumbered sub-heading (bold body paragraph), for appendix sections that must not take chapter numbers."""
        self.add(f'<w:p><w:pPr><w:pStyle w:val="BodyText"/><w:keepNext/><w:spacing w:before="200"/></w:pPr>{run(text, bold=True)}</w:p>')

    def caption(self, kind, text, key):
        self._bmk += 1; bid = self._bmk; name = ("_Ref_fig_" if kind == "Figure" else "_Ref_tbl_") + key
        keep = "<w:keepNext/>" if kind == "Table" else ""      # a table caption stays with its table; a figure caption ends its group
        R = self.CAP_RPR
        field = (f'<w:r>{R}<w:fldChar w:fldCharType="begin"/></w:r>'
                 f'<w:r>{R}<w:instrText xml:space="preserve"> SEQ {kind} \\* ARABIC </w:instrText></w:r>'
                 f'<w:r>{R}<w:fldChar w:fldCharType="separate"/></w:r>'
                 f'<w:r>{R}<w:t>{(self.fign if kind == "Figure" else self.tbln).get(key, 0)}</w:t></w:r>'
                 f'<w:r>{R}<w:fldChar w:fldCharType="end"/></w:r>')
        field = f'<w:bookmarkStart w:id="{bid}" w:name="{name}"/>{field}<w:bookmarkEnd w:id="{bid}"/>'
        return (f'<w:p><w:pPr><w:pStyle w:val="Caption"/>{keep}<w:spacing w:before="0"/>{R}</w:pPr>'
                f'<w:r>{R}<w:t xml:space="preserve">{kind} </w:t></w:r>{field}<w:r>{R}<w:t xml:space="preserve"> - {esc(text)}</w:t></w:r></w:p>')

    # ---- figures
    def _png_size(self, path):
        from PIL import Image
        with Image.open(path) as im: return im.size
    def _add_media(self, src):
        self._rid += 1; rid = f"rId{self._rid}"; name = f"w1_{self._rid}{os.path.splitext(src)[1].lower()}"
        self.media.append((src, name))
        self.rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{name}"/>')
        return rid
    def FIG(self, src, caption, key, width_cm=16.0, max_h_cm=21.0):
        self._fig += 1
        if self.pass_no == 1: self.fign[key] = self._fig; return
        src = src if os.path.isabs(src) else os.path.join(FIG, src)
        rid = self._add_media(src); w, h = self._png_size(src)
        wcm = width_cm; hcm = wcm * h / w
        if hcm > max_h_cm: hcm = max_h_cm; wcm = hcm * w / h
        cx, cy = int(wcm * 360000), int(hcm * 360000)
        self._docpr += 1; did = self._docpr
        draw = (f'<w:p><w:pPr><w:keepNext/><w:spacing w:after="0" w:line="240" w:lineRule="auto"/><w:jc w:val="center"/></w:pPr><w:r><w:drawing>'
                f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
                f'<wp:docPr id="{did}" name="Picture {did}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
                f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
                f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{did}" name="Picture {did}"/><pic:cNvPicPr/></pic:nvPicPr>'
                f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
                f'</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>')
        self.add(draw + self.caption("Figure", caption, key))

    # ---- tables
    def TBL(self, headers, rows, caption, key, col_w=None, font_sz=16, bold_rows=(), align_first_left=True, total=9360):
        self._tbl += 1
        if self.pass_no == 1: self.tbln[key] = self._tbl; return
        ncol = len(headers)
        if col_w is None: col_w = [total // ncol] * ncol
        else:
            s = sum(col_w); col_w = [int(total * c / s) for c in col_w]
        grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in col_w)
        def cell(text, w, bold=False, fill=None, align="left", white=False):
            shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else ""
            rpr = f'<w:rPr>{"<w:b/>" if bold else ""}{"<w:color w:val=\"FFFFFF\"/>" if white else ""}<w:sz w:val="{font_sz}"/><w:szCs w:val="{font_sz}"/></w:rPr>'
            content = self.inline(str(text), bold=bold) if not white else run(str(text), bold=True, color="FFFFFF", sz=font_sz)
            # apply size to inline runs
            content = content.replace("<w:r><w:t", f"<w:r><w:rPr><w:sz w:val=\"{font_sz}\"/><w:szCs w:val=\"{font_sz}\"/></w:rPr><w:t")
            content = content.replace("<w:r><w:rPr>", f"<w:r><w:rPr><w:sz w:val=\"{font_sz}\"/><w:szCs w:val=\"{font_sz}\"/>", 1) if "<w:r><w:rPr>" in content and "<w:sz" not in content[:60] else content
            return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shd}<w:vAlign w:val="center"/></w:tcPr>'
                    f'<w:p><w:pPr><w:jc w:val="{align}"/><w:spacing w:before="20" w:after="20"/>{rpr}</w:pPr>{content}</w:p></w:tc>')
        hdr = "".join(cell(h, col_w[i], bold=True, fill="1F5C99", align="center", white=True) for i, h in enumerate(headers))
        hdr_row = f'<w:tr><w:trPr><w:tblHeader/><w:cantSplit/></w:trPr>{hdr}</w:tr>'
        body = ""
        for ri, r in enumerate(rows):
            fill = "EAF1F8" if ri % 2 else None; bd = ri in bold_rows
            cells = "".join(cell(v, col_w[i], bold=bd, fill=fill, align=("left" if (i == 0 and align_first_left) or ncol <= 2 else "left")) for i, v in enumerate(r))
            body += f'<w:tr><w:trPr><w:cantSplit/></w:trPr>{cells}</w:tr>'
        tblpr = (f'<w:tblPr><w:tblStyle w:val="GridTable4-Accent1"/><w:tblW w:w="{total}" w:type="dxa"/><w:tblBorders>'
                 '<w:top w:val="single" w:sz="4" w:color="BFBFBF"/><w:left w:val="single" w:sz="4" w:color="BFBFBF"/>'
                 '<w:bottom w:val="single" w:sz="4" w:color="BFBFBF"/><w:right w:val="single" w:sz="4" w:color="BFBFBF"/>'
                 '<w:insideH w:val="single" w:sz="4" w:color="BFBFBF"/><w:insideV w:val="single" w:sz="4" w:color="BFBFBF"/>'
                 '</w:tblBorders><w:tblLook w:val="0420"/></w:tblPr>')
        self.add(self.caption("Table", caption, key) + f'<w:tbl>{tblpr}<w:tblGrid>{grid}</w:tblGrid>{hdr_row}{body}</w:tbl><w:p><w:pPr><w:pStyle w:val="BodyText"/><w:spacing w:after="0"/></w:pPr></w:p>')

    # ---- equations (native OMML) in a borderless 2-column table: equation | (n)
    def EQ(self, omml, key, params=None):
        self._eq += 1; self.eqn[key] = self._eq
        if self.pass_no == 1: return
        n = self._eq
        eqp = ('<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:before="60" w:after="60"/></w:pPr>'
               '<m:oMathPara xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"><m:oMath>' + omml + '</m:oMath></m:oMathPara></w:p>')
        nump = f'<w:p><w:pPr><w:jc w:val="right"/></w:pPr>{run(f"({n})")}</w:p>'
        tbl = ('<w:tbl><w:tblPr><w:tblW w:w="9360" w:type="dxa"/><w:tblBorders><w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/><w:insideH w:val="nil"/><w:insideV w:val="nil"/></w:tblBorders></w:tblPr>'
               '<w:tblGrid><w:gridCol w:w="8400"/><w:gridCol w:w="960"/></w:tblGrid><w:tr>'
               f'<w:tc><w:tcPr><w:tcW w:w="8400" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>{eqp}</w:tc>'
               f'<w:tc><w:tcPr><w:tcW w:w="960" w:type="dxa"/><w:vAlign w:val="center"/></w:tcPr>{nump}</w:tc></w:tr></w:tbl>')
        self.add(tbl)
        if params:
            self.P("where:", style="BodyText")
            for sym, meaning in params:
                self.add(f'<w:p><w:pPr><w:pStyle w:val="BodyText"/><w:ind w:left="567"/><w:spacing w:after="40"/></w:pPr>{self.inline(sym)}{run("  ")}{self.inline(meaning)}</w:p>')

    # ---- sections: landscape block for wide figures
    def _sectpr(self, landscape):
        """Section properties. The first body section carries the body header/footer and restarts page numbers at 1;
        later sections (landscape pages and the return to portrait) inherit and continue."""
        pg = '<w:pgSz w:w="15840" w:h="12240" w:orient="landscape"/>' if landscape else '<w:pgSz w:w="12240" w:h="15840"/>'
        first = not getattr(self, "_sect_done", False); self._sect_done = True
        hdr = '<w:headerReference w:type="default" r:id="rId49"/><w:footerReference w:type="default" r:id="rId50"/>' if first else ""
        num = '<w:pgNumType w:start="1"/>' if first else ""
        return (f'<w:sectPr>{hdr}<w:footnotePr><w:numRestart w:val="eachPage"/></w:footnotePr>{pg}'
                '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>'
                f'{num}<w:cols w:space="720"/></w:sectPr>')
    def LANDSCAPE(self, fn):
        """fn(d) adds the wide content; wraps it in a landscape section (Letter landscape, 22.9 cm usable width)."""
        self.add(f'<w:p><w:pPr>{self._sectpr(False)}</w:pPr></w:p>')
        fn(self)
        self.add(f'<w:p><w:pPr>{self._sectpr(True)}</w:pPr></w:p>')

# ------------------------------------------------------------------ OMML helpers
def mr(t, italic=True):
    sty = '' if italic else '<m:rPr><m:sty m:val="p"/></m:rPr>'
    return f'<m:r>{sty}<m:t xml:space="preserve">{esc(t)}</m:t></m:r>'
def mtxt(t): return mr(t, italic=False)
def mfrac(n, d): return f'<m:f><m:num>{n}</m:num><m:den>{d}</m:den></m:f>'
def msup(e, s): return f'<m:sSup><m:e>{e}</m:e><m:sup>{s}</m:sup></m:sSup>'
def msub(e, s): return f'<m:sSub><m:e>{e}</m:e><m:sub>{s}</m:sub></m:sSub>'
def msubsup(e, a, b): return f'<m:sSubSup><m:e>{e}</m:e><m:sub>{a}</m:sub><m:sup>{b}</m:sup></m:sSubSup>'
def mrad(e, deg=None):
    return (f'<m:rad><m:radPr><m:degHide m:val="1"/></m:radPr><m:deg/><m:e>{e}</m:e></m:rad>' if deg is None
            else f'<m:rad><m:deg>{deg}</m:deg><m:e>{e}</m:e></m:rad>')
def mdelim(e, b="(", c=")"): return f'<m:d><m:dPr><m:begChr m:val="{b}"/><m:endChr m:val="{c}"/></m:dPr><m:e>{e}</m:e></m:d>'

# ------------------------------------------------------------------ package assembly
def unpack_template():
    if os.path.exists(WORK): shutil.rmtree(WORK)
    with zipfile.ZipFile(TEMPLATE) as z: z.extractall(WORK)

def patch_cover_and_headers(header_title="Dam Break Analysis Methodology Report"):
    p = os.path.join(WORK, "word", "document.xml"); x = open(p, encoding="utf-8").read()
    x = x.replace(">Hydrology Report<", f">{esc(TITLE_LINE)}<", 1)
    x = x.replace(">July 2026<", f">{DATE_LINE}<", 1)
    x = x.replace(">Ministry of Agriculture, Fisheries &amp; Water Resources<", f">{esc(MINISTRY)}<", 1)
    # lists of figures and tables: include the label and number ("\c" switch) instead of the template's "\a" (caption text only)
    x = x.replace('TOC \\a "Figure" \\h', 'TOC \\c "Figure" \\h').replace('TOC \\a "Table" \\h', 'TOC \\c "Table" \\h')
    open(p, "w", encoding="utf-8").write(x)
    for h in ("header1.xml", "header2.xml"):
        hp = os.path.join(WORK, "word", h); hx = open(hp, encoding="utf-8").read()
        hx = re.sub(r"Hydrology Report", header_title, hx)
        hx = hx.replace("Fisheries &amp; Water Resources", "Fisheries Wealth &amp; Water Resources")
        open(hp, "w", encoding="utf-8").write(hx)

def assemble(d, drop_front=False):
    p = os.path.join(WORK, "word", "document.xml"); x = open(p, encoding="utf-8").read()
    bs = x.index("<w:body>") + len("<w:body>"); be = x.rindex("</w:body>")
    head, body, tail = x[:bs], x[bs:be], x[be:]
    # the heading paragraph, not the TOC entry of the same text (which sits inside a content control)
    idx = body.find("Abbreviations and Nomenclature", body.rfind("</w:sdt>"))
    cut = 0 if drop_front else body.rfind("<w:p ", 0, idx)     # drop_front: no cover, no contents lists
    final = d._sectpr(False)
    new_body = body[:cut] + "".join(d.xml) + final
    open(p, "w", encoding="utf-8").write(head + new_body + tail)
    # relationships
    rp = os.path.join(WORK, "word", "_rels", "document.xml.rels"); rx = open(rp, encoding="utf-8").read()
    rx = rx.replace("</Relationships>", "".join(d.rels) + "</Relationships>")
    open(rp, "w", encoding="utf-8").write(rx)
    # media
    md = os.path.join(WORK, "word", "media")
    for src, name in d.media: shutil.copy(src, os.path.join(md, name))
    # content types: ensure png / jpg defaults
    cp = os.path.join(WORK, "[Content_Types].xml"); cx = open(cp, encoding="utf-8").read()
    for ext, mime in (("png", "image/png"), ("jpg", "image/jpeg"), ("jpeg", "image/jpeg")):
        if f'Extension="{ext}"' not in cx: cx = cx.replace("<Default ", f'<Default Extension="{ext}" ContentType="{mime}"/><Default ', 1)
    open(cp, "w", encoding="utf-8").write(cx)
    # footnotes
    fp = os.path.join(WORK, "word", "footnotes.xml"); fx = open(fp, encoding="utf-8").read()
    notes = ""
    for i, t in enumerate(d.footnotes, 1):
        notes += (f'<w:footnote w:id="{i}"><w:p><w:pPr><w:pStyle w:val="FootnoteText"/></w:pPr>'
                  f'<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:footnoteRef/></w:r>'
                  f'<w:r><w:t xml:space="preserve"> {esc(t)}</w:t></w:r></w:p></w:footnote>')
    fx = fx.replace("</w:footnotes>", notes + "</w:footnotes>")
    open(fp, "w", encoding="utf-8").write(fx)
    # settings: ask Word to refresh TOC / lists / fields on open
    sp = os.path.join(WORK, "word", "settings.xml"); sx = open(sp, encoding="utf-8").read()
    if "w:updateFields" not in sx: sx = sx.replace("<w:zoom", '<w:updateFields w:val="true"/><w:zoom', 1)
    open(sp, "w", encoding="utf-8").write(sx)

def zip_out(out_docx=None):
    out_docx = out_docx or OUT_DOCX
    os.makedirs(OUT_DIR, exist_ok=True)
    if os.path.exists(out_docx): os.remove(out_docx)
    with zipfile.ZipFile(out_docx, "w", zipfile.ZIP_DEFLATED) as z:
        # [Content_Types].xml first
        z.write(os.path.join(WORK, "[Content_Types].xml"), "[Content_Types].xml")
        for root, _, files in os.walk(WORK):
            for f in files:
                full = os.path.join(root, f); arc = os.path.relpath(full, WORK).replace("\\", "/")
                if arc == "[Content_Types].xml": continue
                z.write(full, arc)
    print("wrote", out_docx)

RUNSHEET_DOCX = os.path.join(OUT_DIR, "Wadi Majlas Dam Break Analysis - HEC-RAS Run Sheet Rev00.docx")

def prune_unreferenced_media():
    """Drop template images (cover, hydrology figures) that the new body no longer references, so the file stays small."""
    rp = os.path.join(WORK, "word", "_rels", "document.xml.rels"); rx = open(rp, encoding="utf-8").read()
    dx = open(os.path.join(WORK, "word", "document.xml"), encoding="utf-8").read()
    used = set(re.findall(r'r:(?:embed|id|link)="(rId\d+)"', dx))
    keep, removed = [], 0
    for rel in re.findall(r'<Relationship [^>]*/>', rx):
        rid = re.search(r'Id="([^"]+)"', rel).group(1); tgt = re.search(r'Target="([^"]+)"', rel).group(1)
        if tgt.startswith("media/") and rid not in used:
            f = os.path.join(WORK, "word", tgt)
            if os.path.exists(f): os.remove(f); removed += 1
            continue
        keep.append(rel)
    rx = re.sub(r'<Relationship [^>]*/>', "", rx).replace("</Relationships>", "".join(keep) + "</Relationships>")
    open(rp, "w", encoding="utf-8").write(rx)
    print("pruned media files:", removed)

def build_runsheet():
    """Short companion to the methodology report: values and actions only, no cover, no contents lists."""
    import rpt_runsheet
    unpack_template(); patch_cover_and_headers(header_title="Dam Break Analysis-HEC-RAS Run Sheet")
    d = Doc(); rpt_runsheet.content(d)
    d2 = Doc(); d2.fign, d2.tbln, d2.eqn = d.fign, d.tbln, d.eqn; d2.pass_no = 2
    rpt_runsheet.content(d2)
    assemble(d2, drop_front=True); prune_unreferenced_media(); zip_out(RUNSHEET_DOCX)
    print(f"run sheet: tables {d._tbl}, figures {d._fig}")

def build():
    import rpt_content
    unpack_template(); patch_cover_and_headers()
    d = Doc(); rpt_content.content(d)                      # pass 1: numbers
    d2 = Doc(); d2.fign, d2.tbln, d2.eqn = d.fign, d.tbln, d.eqn; d2.pass_no = 2
    rpt_content.content(d2)                                # pass 2: render
    assemble(d2); zip_out()
    print(f"figures {d._fig}, tables {d._tbl}, equations {d._eq}, footnotes {len(d2.footnotes)}")

if __name__ == "__main__":
    if "--runsheet" in sys.argv: build_runsheet()
    else: build()
