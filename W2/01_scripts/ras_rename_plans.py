# -*- coding: utf-8 -*-
"""One-off (2026-09-22): rename the dam-break plans to scenario-based names in the plan files and the RAS Mapper file.
S1 = sunny day failure, S2 = flood day PMF failure, S3 = PMF no failure; D = dikes, N = no dikes;
suffix = the one thing changed: W<breach width m>, T<formation time>, C<weir coefficient>, F<flood return period>."""
import os, re
RAS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "HEC-RAS Majlas"))
NEW = {
 "p27": ("Fill",       "Fill reservoir to 84.5 m (restart)"),
 "p28": ("S1D",        "S1D sunny day failure, dikes"),
 "p29": ("S1N",        "S1N sunny day failure, no dikes"),
 "p30": ("S2D",        "S2D flood day PMF failure, dikes"),
 "p31": ("S2N",        "S2N flood day PMF failure, no dikes"),
 "p32": ("S3D",        "S3D PMF no failure, dikes"),
 "p33": ("S3N",        "S3N PMF no failure, no dikes"),
 "p34": ("S2D-W51",    "S2D-W51 flood day, breach width 51 m"),
 "p35": ("S2D-W119",   "S2D-W119 flood day, breach width 119 m"),
 "p36": ("S2D-W153",   "S2D-W153 flood day, breach width 153 m"),
 "p37": ("S1D-W51",    "S1D-W51 sunny day, breach width 51 m"),
 "p38": ("S1D-W153",   "S1D-W153 sunny day, breach width 153 m"),
 "p39": ("S2D-T18m",   "S2D-T18m flood day, breach time 18 min"),
 "p40": ("S2D-T3m",    "S2D-T3m flood day, breach time 3 min"),
 "p41": ("S1D-C1.44",  "S1D-C1.44 sunny day, breach coefficient 1.44"),
 "p42": ("S2D-F10000", "S2D-F10000 flood day, 10000-yr flood"),
}
rm_path = os.path.join(RAS, "Majlas.rasmap"); rasmap = open(rm_path, encoding="utf-8").read()
for code, (short, title) in NEW.items():
    p = os.path.join(RAS, f"Majlas.{code}"); b = open(p, "rb").read()
    old_title = re.search(rb"^Plan Title=([^\r\n]*)", b, flags=re.M).group(1).decode("latin-1")
    old_short = re.search(rb"^Short Identifier=([^\r\n]*)", b, flags=re.M).group(1).decode("latin-1").strip()
    b = re.sub(rb"^Plan Title=[^\r\n]*", ("Plan Title=" + title).encode("latin-1"), b, count=1, flags=re.M)
    b = re.sub(rb"^Short Identifier=[^\r\n]*", ("Short Identifier=" + short.ljust(64)).encode("latin-1"), b, count=1, flags=re.M)
    open(p, "wb").write(b)
    old_layer = '<Layer Name="' + old_title + '" Type="RASResults" Filename=".\\Majlas.' + code + '.hdf">'
    new_layer = '<Layer Name="' + title + '" Type="RASResults" Filename=".\\Majlas.' + code + '.hdf">'
    n1 = rasmap.count(old_layer); rasmap = rasmap.replace(old_layer, new_layer)
    old_fn = 'Filename=".\\' + old_short + '\\'; new_fn = 'Filename=".\\' + short + '\\'
    n2 = rasmap.count(old_fn); rasmap = rasmap.replace(old_fn, new_fn)
    print(f"{code}: '{old_title}' [{old_short}] -> '{title}' [{short}]  (rasmap layer {n1}, stored paths {n2})")
open(rm_path, "w", encoding="utf-8", newline="").write(rasmap)
from lxml import etree; etree.parse(rm_path); print("rasmap XML ok")
