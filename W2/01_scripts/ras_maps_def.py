# -*- coding: utf-8 -*-
"""Register stored result maps (max depth, max velocity, max WSE) for the dam-break plans in Majlas.rasmap, so that
HEC-RAS computes them itself at the end of each run ("Run RASMapper=-1" in the plan) on the plan's own terrain,
including the terrain modifications (dikes, dam removed) that only exist inside RAS Mapper.

Run only while HEC-RAS is closed.   python ras_maps_def.py p28 p30 ...   (default: all DB plans)
Stored files go to <project>/<Short Identifier>/<map>.vrt, as HEC-RAS does for the user's own maps.
"""
import os, re, sys, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); W2 = os.path.abspath(os.path.join(HERE, ".."))
RAS = os.path.abspath(os.path.join(W2, "..", "HEC-RAS Majlas")); RASMAP = os.path.join(RAS, "Majlas.rasmap")
TERRAIN = {"g02": "Terrain (2).Protection2", "g03": "Terrain (2)"}

def plan_info(code):
    t = open(os.path.join(RAS, f"Majlas.{code}"), encoding="latin-1").read()
    title = re.search(r"^Plan Title=([^\r\n]*)", t, flags=re.M).group(1).strip()
    short = re.search(r"^Short Identifier=([^\r\n]*)", t, flags=re.M).group(1).strip()
    geom = re.search(r"^Geom File=([^\r\n]*)", t, flags=re.M).group(1).strip()
    return title, short, geom

def block(code):
    title, short, geom = plan_info(code)
    folder = f".\\{short}"
    def m(name, mtype):
        fn = f"{folder}\\{name}.vrt"
        return (f'    <Layer Name="{name}" Type="RASResultsMap" Filename="{fn}">\n'
                f'      <MapParameters MapType="{mtype}" LayerName="{name}" OutputMode="Stored Current Terrain" StoredFilename="{fn}" '
                f'ProfileIndex="2147483647" ProfileName="Max" OverwriteOutputFilename="{name}" />\n    </Layer>\n')
    return (f'  <Layer Name="{title}" Type="RASResults" Filename=".\\Majlas.{code}.hdf">\n'
            + m("Depth (Max)", "depth") + m("Velocity (Max)", "velocity") + m("WSE (Max)", "elevation")
            + f'    <Terrain Name="{TERRAIN[geom]}" />\n  </Layer>\n')

def main(codes):
    s = open(RASMAP, encoding="utf-8").read()
    shutil.copy(RASMAP, RASMAP + ".bak_before_dambreak_maps") if not os.path.exists(RASMAP + ".bak_before_dambreak_maps") else None
    added = []
    for c in codes:
        if f'Filename=".\\Majlas.{c}.hdf"' in s and 'Type="RASResults"' in s.split(f'Filename=".\\Majlas.{c}.hdf"')[0][-80:]:
            continue
        s = s.replace("  </Results>", block(c) + "  </Results>", 1); added.append(c)
    open(RASMAP, "w", encoding="utf-8", newline="").write(s)
    print("stored-map definitions added for:", added)

if __name__ == "__main__":
    codes = sys.argv[1:] or [f"p{n}" for n in range(28, 43)]
    main(codes)
