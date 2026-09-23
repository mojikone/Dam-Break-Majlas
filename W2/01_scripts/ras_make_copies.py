# -*- coding: utf-8 -*-
"""Create lightweight copies of the HEC-RAS project for parallel runs: text files, geometry HDFs, restart file and RAS Mapper
file are copied; the Terrain and Land Classification folders are linked (NTFS junctions) so nothing large is duplicated.
Plans in a copy get UNET D2 Cores set to `cores` (default 8) so two or three copies share the 16 physical cores.
Usage: python ras_make_copies.py run2 run3 [--cores 8]"""
import os, sys, shutil, re, subprocess, glob
HERE = os.path.dirname(os.path.abspath(__file__)); W2 = os.path.abspath(os.path.join(HERE, ".."))
SRC = os.path.abspath(os.path.join(W2, "..", "HEC-RAS Majlas"))
LINK_DIRS = ["Terrain", "Land Classification"]
COPY_GLOBS = ["Majlas.prj", "Majlas.rasmap", "Majlas.g0[23]", "Majlas.g0[23].hdf", "Majlas.u2[6-9]", "Majlas.u3?", "Majlas.p2[7-9]", "Majlas.p3?", "Majlas.p4?",
              "Majlas.p27.*.rst", "Majlas.p43.*.rst", "Projection WGS 84 UTM zone 40.prj"]

def prune_prj(dst):
    """Keep only the geometry/flow/plan entries whose files exist in the copy; HEC-RAS (and ras_run.plans) fail on a missing file."""
    p = os.path.join(dst, "Majlas.prj"); lines = open(p, "rb").read().decode("latin-1").split("\r\n"); out = []
    for l in lines:
        m = re.match(r"^(Plan File|Unsteady File|Geom File|Flow File)=(\w+)$", l)
        if m and not os.path.exists(os.path.join(dst, f"Majlas.{m.group(2)}")): continue
        out.append(l)
    open(p, "wb").write("\r\n".join(out).encode("latin-1"))

def make(name, cores):
    dst = os.path.abspath(os.path.join(W2, "..", f"HEC-RAS Majlas_{name}")); os.makedirs(dst, exist_ok=True)
    for g in COPY_GLOBS:
        for f in glob.glob(os.path.join(SRC, g)):
            shutil.copy2(f, dst)
    for d in LINK_DIRS:
        target = os.path.join(dst, d)
        if not os.path.exists(target):
            subprocess.run(["cmd", "/c", "mklink", "/J", target, os.path.join(SRC, d)], check=True, capture_output=True)
    for p in glob.glob(os.path.join(dst, "Majlas.p[234]?")):
        b = open(p, "rb").read()
        b = re.sub(rb"^UNET D2 Cores=[^\r\n]*", f"UNET D2 Cores={cores}".encode(), b, flags=re.M)
        b = re.sub(rb"^UNET D2 Cores= [^\r\n]*", f"UNET D2 Cores= {cores} ".encode(), b, flags=re.M)
        open(p, "wb").write(b)
    prune_prj(dst)
    n = len(os.listdir(dst)); print(f"{dst}: {n} entries, plans set to {cores} cores")
    return dst

if __name__ == "__main__":
    cores = 8
    if "--cores" in sys.argv: cores = int(sys.argv[sys.argv.index("--cores") + 1])
    for name in [a for a in sys.argv[1:] if not a.startswith("--") and not a.isdigit()]:
        make(name, cores)
