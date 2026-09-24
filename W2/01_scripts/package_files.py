# -*- coding: utf-8 -*-
"""Assemble the hand-over package "Majlas Dam Break files" (user, 2026-09-24): reports, the two models with their terrains, and every
layer, raster, map, chart and table, organised in subfolders. Nothing is linked; the package works on another machine.
The QGIS project inside layers/qgis is built afterwards inside QGIS (package_qgis.py through the MCP), from these copies.

Left out on purpose: the old flood-study results in the HEC-RAS project (plans p01-p26, 2 GB), the parallel run copies, W1, the
trial maps that did not make the report.

python package_files.py            -> D:/Mojtaba/Renardet/2224 WS11/Majlas/Hydraulic/Dam Breack/Majlas Dam Break files
"""
import os, re, json, glob, shutil, csv, subprocess, time
HERE = os.path.dirname(os.path.abspath(__file__)); W2 = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(W2, ".."))                       # Dam Breack
MAJ = os.path.abspath(os.path.join(ROOT, "..", ".."))                # Majlas
PKG = os.path.join(ROOT, "Majlas Dam Break files")
import ras_setup as S
CODE = S.FIXED_P
ORDER = ["S1D", "S1N", "S1D-W51", "S1D-W153", "S1D-C1.44", "S1D-T3m", "S1D-T18m", "S2D", "S2D-W119", "S2D-F10000", "S3D", "S3D-F10000"]
DESC = {"S1D": "sunny-day failure, dikes in place", "S1N": "sunny-day failure, no dikes", "S2D": "flood-day (PMF) failure, dikes in place",
        "S3D": "PMF without failure, dikes in place", "S1D-W51": "sunny-day failure, breach 51 m", "S1D-W153": "sunny-day failure, breach 153 m",
        "S1D-C1.44": "sunny-day failure, weir coefficient 1.44", "S1D-T3m": "sunny-day failure, breach formed in 3 min",
        "S1D-T18m": "sunny-day failure, breach formed in 18 min", "S2D-W119": "flood-day failure, breach 119 m",
        "S2D-F10000": "flood-day failure, 10,000-year flood", "S3D-F10000": "10,000-year flood without failure"}
PLAN_TXT = {sid: CODE[sid] for sid in ORDER}; PLAN_TXT.update(Fill="p27", FillN="p43")

def log(*a): print(time.strftime("%H:%M:%S"), *a, flush=True)
def mk(p): os.makedirs(p, exist_ok=True); return p
def cp(src, dst_dir, name=None):
    if not os.path.exists(src): log("MISSING", src); return None
    mk(dst_dir); dst = os.path.join(dst_dir, name or os.path.basename(src)); shutil.copy2(src, dst); return dst
def cp_shp(src_shp, dst_dir, name=None):
    """a shapefile is a family of files"""
    base = os.path.splitext(src_shp)[0]; out = None
    for f in glob.glob(glob.escape(base) + ".*"):
        ext = os.path.splitext(f)[1]; out = cp(f, dst_dir, (name + ext) if name else None)
    return out
def robocopy(src, dst, *extra):
    mk(dst); r = subprocess.run(["robocopy", src, dst, "/E", "/R:1", "/W:1", "/NFL", "/NDL", "/NJH", "/NP", "/MT:8"] + list(extra), capture_output=True, text=True)
    log("robocopy", os.path.basename(src), "->", os.path.relpath(dst, PKG), "exit", r.returncode); return r.returncode

def reports():
    d = mk(os.path.join(PKG, "reports"))
    for f in glob.glob(os.path.join(W2, "05_report", "R1", "*.pdf")) + glob.glob(os.path.join(W2, "05_report", "R1", "*.docx")): cp(f, d)
    for f in glob.glob(os.path.join(W2, "06_references", "*")): cp(f, os.path.join(d, "references"))
    log("reports done")

def layers():
    L = os.path.join(PKG, "layers")
    # --- vectors used by the maps
    shp = mk(os.path.join(L, "shp"))
    cp_shp(os.path.join(W2, "04_data", "gis", "dam_axis_straight_indicative.shp"), shp, "Dam axis straight (indicative)")
    cp_shp(os.path.join(ROOT, "Data", "SHP", "Dam Axis.shp"), shp, "Dam axis original arch")
    cp_shp(os.path.join(MAJ, "Hydraulic", "Flood Protection", "Risk", "Data", "SHP", "Dykes.shp"), shp, "Training dikes")
    cp_shp(os.path.join(MAJ, "Hydraulic", "Flood Protection", "Risk", "Data", "SHP", "Landuse Majlas Clip.shp"), shp, "Land use plots Qurayat")
    cp_shp(os.path.join(MAJ, "Hydraulic", "Flood Protection", "Risk", "Data", "SHP", "Project Outline.shp"), shp, "Project outline")
    for f in glob.glob(os.path.join(MAJ, "Hydrology", "SHP", "*.shp")): cp_shp(f, os.path.join(shp, "hydrology"))
    for f in glob.glob(os.path.join(W2, "04_data", "gis", "*.geojson")): cp(f, os.path.join(L, "gis"))
    for f in ("places.shp", "model_extents.shp", "data_extents.shp"): cp_shp(os.path.join(ROOT, "W1", "04_data", "gis", f), os.path.join(L, "gis"))
    # --- base rasters
    rb = mk(os.path.join(L, "rasters", "base"))
    cp(os.path.join(ROOT, "Data", "Terrain", "Majlas Terrain Dam Break.tif"), os.path.join(L, "terrain"))
    cp(os.path.join(MAJ, "Hydraulic", "Flood Protection", "Risk", "Data", "Population", "GHS POP 2025 Majlas.tif"), rb, "GHS-POP 2025 population (100 m).tif")
    # --- result rasters and vectors per scenario
    for sid in ORDER:
        src = os.path.join(W2, "04_data", "results", CODE[sid]); dst = mk(os.path.join(L, "rasters", sid))
        for f in ("max_depth.tif", "max_velocity.tif", "max_dv.tif", "arrival_h.tif", "duration_h.tif", "hazard_aidr.tif", "warning_arrival_h.tif"): cp(os.path.join(src, f), dst)
        cp(os.path.join(src, "flood_extent.geojson"), dst)
        for f in ("isochrones_v3.geojson", "hazard_lines_v3.geojson"):
            if os.path.exists(os.path.join(src, f)): cp(os.path.join(src, f), dst, f.replace("_v3", ""))
    # --- maps, charts, flowcharts, drawings
    keep = re.compile(r"^(S\S+) (depth|hazard|arrival|hazard-iso-grey|arrival-pmf|population) (reach|town)\.png$")
    for f in glob.glob(os.path.join(W2, "02_figures", "maps", "results", "*.png")):
        b = os.path.basename(f); m = keep.match(b)
        if m: cp(f, os.path.join(L, "maps", m.group(1)))
        elif b in ("Model extent.png", "HEC-HMS model.png"): cp(f, os.path.join(L, "maps", "model"))
    for f in glob.glob(os.path.join(W2, "02_figures", "charts", "*.png")): cp(f, os.path.join(L, "charts"))
    for f in glob.glob(os.path.join(W2, "02_figures", "flowcharts", "fc*.png")) + glob.glob(os.path.join(W2, "02_figures", "flowcharts", "fc*.svg")): cp(f, os.path.join(L, "flowcharts"))
    for f in glob.glob(os.path.join(W2, "02_figures", "deck", "*_crop.png")): cp(f, os.path.join(L, "dam drawings"))
    # --- QGIS: layout template (the project itself is built inside QGIS afterwards)
    cp(os.path.join(ROOT, "Data", "QGIS", "QGIS layout template.qpt"), os.path.join(L, "qgis"))
    log("layers done")

def tables():
    T = mk(os.path.join(PKG, "layers", "tables"))
    summary = []
    for sid in ORDER:
        src = os.path.join(W2, "04_data", "results", CODE[sid]); dst = mk(os.path.join(T, sid))
        for f in ("summary.json", "consequences.json", "warning.json", "trigger.json", "connection.csv") + tuple(os.path.basename(x) for x in glob.glob(os.path.join(src, "boundary_*.csv"))):
            if os.path.exists(os.path.join(src, f)): cp(os.path.join(src, f), dst)
        s = json.load(open(os.path.join(src, "summary.json"))); c = json.load(open(os.path.join(src, "consequences.json"))); w = json.load(open(os.path.join(src, "warning.json")))
        hz = s.get("hazard_area_km2", {})
        summary.append({"scenario": sid, "description": DESC[sid], "peak_flow_m3s": round(s["peak_total_flow_m3s"]), "peak_time_h": round(s["peak_time_h"], 2),
                        "max_pool_m": round(s.get("max_stage_hw", 0), 2), "breach_start_h": s.get("breach_start_h"), "flooded_area_km2": round(s["inundated_area_km2_gt0.3m"], 2),
                        "max_depth_gorge_m": round(s["max_depth_m"], 1), "max_depth_plain_m": round(s.get("max_depth_plain_m") or 0, 1),
                        "max_velocity_ms": round(s.get("max_velocity_ms", 0), 1), "H4_km2": round(hz.get("H4", 0), 2), "H5_km2": round(hz.get("H5", 0), 2), "H6_km2": round(hz.get("H6", 0), 2),
                        "people_in_flooded_area": round(c["par_total"]), "people_H4_or_worse": round(c["par_H4plus"]), "plots_touched": c["plots_total"], "plots_residential": c.get("plots_Residential", 0),
                        "people_reached_15min": round(w["people_cum"][w["bands_h"].index(0.25)]) if 0.25 in w["bands_h"] else "", "people_reached_1h": round(w["people_cum"][w["bands_h"].index(1.0)]) if 1.0 in w["bands_h"] else "",
                        "people_reached_3h": round(w["people_cum"][w["bands_h"].index(3.0)]) if 3.0 in w["bands_h"] else "", "people_reached_12h": round(w["people_cum"][w["bands_h"].index(12.0)]) if 12.0 in w["bands_h"] else "",
                        "arrival_town_h": w["places"].get("Qurayat, residential centre"), "arrival_shore_h": w["places"].get("Shoreline, 'Outflow Sea' line")})
    with open(os.path.join(T, "results_summary.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(summary[0].keys())); wr.writeheader(); wr.writerows(summary)
    cp(os.path.join(W2, "04_data", "results", "consequences.csv"), T); cp(os.path.join(W2, "04_data", "dikes_decision.json"), T)
    cp(os.path.join(W2, "04_data", "hms_res2_hydrographs.xlsx"), T, "boundary_hydrographs_from_HEC-HMS.xlsx")
    log("tables done")

def models():
    M = os.path.join(PKG, "models")
    # HEC-RAS: text files of the project, restart files, terrain, land classification, the 14 dam-break result files, the stored maps of S2D/S3D
    src = os.path.join(ROOT, "HEC-RAS Majlas"); dst = mk(os.path.join(M, "HEC-RAS"))
    keep_hdf = {f"Majlas.{p}.hdf" for p in PLAN_TXT.values()}
    for f in os.listdir(src):
        p = os.path.join(src, f)
        if not os.path.isfile(p): continue
        low = f.lower()
        if low.endswith((".hdf", ".tmp.hdf")):
            if f in keep_hdf: shutil.copy2(p, os.path.join(dst, f))
            continue
        if low.endswith((".bco", ".bco01", ".bco02", ".bco03", ".bco04")) or "computemsgs" in low or low.endswith((".bak", ".backup", ".rst.fill_dw", ".rst.fill12h_spilled", ".tmp")) or "bak_before" in low: continue
        if low.endswith(".dss"): continue
        shutil.copy2(p, os.path.join(dst, f))
    robocopy(os.path.join(src, "Terrain"), os.path.join(dst, "Terrain"))
    robocopy(os.path.join(src, "Land Classification"), os.path.join(dst, "Land Classification"))
    for d in ("S2D", "S3D", "Features"):
        if os.path.isdir(os.path.join(src, d)): robocopy(os.path.join(src, d), os.path.join(dst, d))
    log("HEC-RAS done")
    # HEC-HMS: everything but logs and the backup
    robocopy(os.path.join(ROOT, "HEC_HMS_Majlas"), os.path.join(M, "HEC-HMS"), "/XF", "*.log", "*.bak_20260922", "/XD", "Claude")
    log("HEC-HMS done")

def readme():
    txt = f"""Wadi Majlas Flood Protection Dam - Dam Break Analysis: hand-over files (Rev 01, {time.strftime('%Y-%m-%d')})

reports/                 the Dam Break Analysis Report Rev 01 (PDF, Word, and a Word copy with reduced images) and the guidance documents it cites
models/HEC-RAS/          the two-dimensional HEC-RAS 6.6 project with its terrain and land classification; open Majlas.prj.
                         The 14 dam-break runs carry their results (plans named by scenario: S1D, S1N, S2D, S3D and the sensitivity runs;
                         Fill and FillN are the reservoir fills that wrote the restart files). Older plans of the flood-protection study are
                         listed without results.
models/HEC-HMS/          the catchment model of the hydrology study with its terrain; the runs "DA ... Res2" gave the boundary hydrographs.
layers/qgis/             the QGIS project with every layer below, in groups, plus the print-layout template used for the maps
layers/shp/              dam axes, training dikes, land-use plots, project outline; hydrology/ holds the catchment and stream layers
layers/gis/              the model as built (2D area, boundary lines, dam connection), the HEC-HMS elements, places and extents (GeoJSON, EPSG:32640)
layers/terrain/          the 5 m terrain used for the dam-break model
layers/rasters/base/     the population grid (GHS-POP 2025, 100 m)
layers/rasters/<run>/    per run, 2 m GeoTIFF (EPSG:32640): max_depth, max_velocity, max_dv (depth x velocity), hazard_aidr (H1-H6 as 1-6),
                         arrival_h (first 0.3 m depth, hours from the breach or the storm start), warning_arrival_h (0.3 m rise above the
                         pre-event depth; for flood-day failures above the no-failure run), duration_h; flood_extent, isochrones and
                         hazard_lines as GeoJSON
layers/maps/<run>/       the exported maps (depth, hazard class with isochrones, arrival, population) for the reach and for Qurayat
layers/charts/           all charts of the report; flowcharts/ the process diagrams; dam drawings/ the design-review drawings
layers/tables/           results_summary.csv (one row per run) and, per run, the summary, consequences, warning-time and hydrograph files

Run names: S1 sunny-day failure, S2 flood-day failure at the PMF peak, S3 PMF without failure; D with the training dikes, N without;
W = breach width (m), T = formation time, C = weir coefficient, F10000 = the 10,000-year flood instead of the PMF.
"""
    open(os.path.join(PKG, "README.txt"), "w", encoding="utf-8").write(txt)

if __name__ == "__main__":
    mk(PKG); readme(); reports(); layers(); tables(); open(os.path.join(PKG, "_layers_ready.txt"), "w").write("ok"); models()
    log("PACKAGE DONE")
