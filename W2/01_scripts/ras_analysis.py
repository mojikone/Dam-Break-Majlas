# -*- coding: utf-8 -*-
"""Consequence overlays on the dam-break rasters produced by ras_results.py.

For each plan folder in W2/04_data/results/<plan>/:
  population at risk (GHS-POP 2025, 100 m) inside the flooded area (depth > 0.3 m) and per AIDR hazard class
  land-use plots (flood-risk study layer) touched by depth > 0.3 m, per class
  incremental depth raster for a failure run against its no-failure twin (S2-D vs S3-D, S2-N vs S3-N)
Writes consequences.json per plan and a combined W2/04_data/results/consequences.csv.
"""
import os, sys, json, csv
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); W2 = os.path.abspath(os.path.join(HERE, ".."))
RES = os.path.join(W2, "04_data", "results")
BASE = "D:/Mojtaba/Renardet/2224 WS11/Majlas/"
POP = BASE + "Hydraulic/Flood Protection/Risk/Data/Population/GHS POP 2025 Majlas.tif"
LU = BASE + "Hydraulic/Flood Protection/Risk/Data/SHP/Landuse Majlas Clip.shp"
TWINS = {"p30": "p32", "p31": "p33", "p34": "p32", "p35": "p32", "p36": "p32", "p39": "p32", "p40": "p32", "p42": "p48"}   # failure -> no-failure twin (p48 = 10,000-yr no failure)

def read(path):
    import rasterio
    with rasterio.open(path) as d: return d.read(1).astype(np.float32), d.transform, d.crs, d.nodata, d.bounds

def population_at_risk(depth, tr, hz):
    """Sum GHS-POP persons whose 100 m cell centre falls on a 2 m pixel with depth > 0.3 m, and per hazard class."""
    import rasterio
    with rasterio.open(POP) as P:
        pop = P.read(1).astype(np.float64); pop[pop == P.nodata] = 0; pop[pop < 0] = 0
        rows, cols = np.indices(pop.shape); xs, ys = rasterio.transform.xy(P.transform, rows, cols)
        xs = np.array(xs).ravel(); ys = np.array(ys).ravel(); pv = pop.ravel()
    inv = ~tr
    c, r = inv * (xs, ys); c = np.floor(c).astype(int); r = np.floor(r).astype(int)
    ok = (r >= 0) & (r < depth.shape[0]) & (c >= 0) & (c < depth.shape[1])
    dep = np.full(len(pv), np.nan); dep[ok] = depth[r[ok], c[ok]]
    cls = np.zeros(len(pv), int); cls[ok] = hz[r[ok], c[ok]]
    flooded = dep > 0.3
    out = {"par_total": float(pv[flooded].sum()), "par_depth_gt1m": float(pv[dep > 1.0].sum())}
    for i in range(1, 7): out[f"par_H{i}"] = float(pv[flooded & (cls == i)].sum())
    out["par_H4plus"] = sum(out[f"par_H{i}"] for i in (4, 5, 6))
    return out

def plots_touched(depth, tr):
    import geopandas as gpd, rasterio
    from rasterio import features
    lu = gpd.read_file(LU)
    shapes = ((geom, i + 1) for i, geom in enumerate(lu.geometry))
    ids = features.rasterize(shapes, out_shape=depth.shape, transform=tr, fill=0, dtype="int32")
    wet = (depth > 0.3) & (ids > 0)
    touched = np.unique(ids[wet]) - 1
    out = {"plots_total": int(len(touched))}
    for cls, cnt in lu.iloc[touched]["NewLUClass"].value_counts().items(): out[f"plots_{cls}"] = int(cnt)
    return out

def incremental(plan, twin):
    import rasterio
    a, tr, crs, nd, _ = read(os.path.join(RES, plan, "max_depth.tif")); b, tr2, _, _, _ = read(os.path.join(RES, twin, "max_depth.tif"))
    a[a == nd] = 0; b[b == nd] = 0
    if a.shape != b.shape: return None
    inc = a - b
    prof = dict(driver="GTiff", height=a.shape[0], width=a.shape[1], count=1, crs=crs, transform=tr, compress="deflate", tiled=True, dtype="float32", nodata=-9999)
    with rasterio.open(os.path.join(RES, plan, "incremental_depth.tif"), "w", **prof) as dst: dst.write(np.where((a > 0.05) | (b > 0.05), inc, -9999).astype(np.float32), 1)
    return {"incremental_area_km2_gt0.6m": float((inc > 0.6).sum() * tr.a * -tr.e / 1e6), "incremental_max_m": float(inc.max())}

def analyse(plan):
    d, tr, crs, nd, _ = read(os.path.join(RES, plan, "max_depth.tif")); d[d == nd] = 0
    hz, _, _, _, _ = read(os.path.join(RES, plan, "hazard_aidr.tif")); hz = hz.astype(int)
    out = {"plan": plan}; out.update(population_at_risk(d, tr, hz)); out.update(plots_touched(d, tr))
    if plan in TWINS and os.path.exists(os.path.join(RES, TWINS[plan], "max_depth.tif")):
        inc = incremental(plan, TWINS[plan]); out.update(inc or {})
    json.dump(out, open(os.path.join(RES, plan, "consequences.json"), "w"), indent=2); print(json.dumps(out)); return out

if __name__ == "__main__":
    rows = [analyse(p) for p in sys.argv[1:]]
    keys = sorted({k for r in rows for k in r})
    with open(os.path.join(RES, "consequences.csv"), "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys);
        if fh.tell() == 0: w.writeheader()
        for r in rows: w.writerow(r)
