# -*- coding: utf-8 -*-
"""Read a HEC-RAS 6.6 plan result (Majlas.pNN.hdf) and produce the dam-break products.

Per plan (W2/04_data/results/<plan>/):
  summary.json            solution status, run time, volume accounting, peak breach flow and time, pool at breach, max Courant
  connection.csv          time (h), date, total flow, weir flow, stage HW/TW, breach width/bottom/flow
  boundary_<line>.csv     stage and flow at each BC line
  max_depth.tif           2 m GeoTIFF: max WSE interpolated from cell centres minus terrain, masked below 0.05 m
  max_velocity.tif        2 m: cell velocity (face-length-weighted mean of |face velocity|) at its maximum
  max_dv.tif              2 m: maximum over time of depth x velocity
  arrival_h.tif           2 m: first time (h from the reference time) the cell depth exceeds 0.3 m  (nearest cell)
  duration_h.tif          2 m: time with depth above 0.3 m
  hazard_aidr.tif         2 m: AIDR class 1..6 from max depth, max velocity and max D x V
Usage:  python ras_results.py p30 [--ref-hours 0] [--no-rasters]
"""
import os, sys, json, math
import numpy as np, h5py
HERE = os.path.dirname(os.path.abspath(__file__)); W2 = os.path.abspath(os.path.join(HERE, ".."))
RAS = os.environ.get("RAS_DIR") or os.path.abspath(os.path.join(W2, "..", "HEC-RAS Majlas"))   # RAS_DIR selects a parallel project copy
OUT = os.path.join(W2, "04_data", "results")
sys.path.insert(0, HERE)
import data_facts as F

AREA = "DS Protection"
BASE = "Results/Unsteady/Output/Output Blocks/Base Output"
TS = BASE + "/Unsteady Time Series"
SUMM = BASE + "/Summary Output/2D Flow Areas/" + AREA
CONN = TS + "/SA 2D Area Conn/DS Protection DS Protection"
DEPTH_MIN = 0.05; ARRIVAL_DEPTH = 0.3; RES = 2.0
MIN_PATCH_HA = 1.0      # wet patches smaller than this (rain puddles, single cells) are dropped from products and statistics
PLAIN_X0 = 693300.0     # easting of the gorge exit (the fan starts at about 693,200-693,400 E): statistics "on the plain" are taken east of it

def open_plan(code):
    return h5py.File(os.path.join(RAS, f"Majlas.{code}.hdf"), "r")

def times_h(f):
    return f[TS + "/Time"][:] * 24.0

def dates(f):
    return [x.decode() for x in f[TS + "/Time Date Stamp"][:]]

def terrain_path(f):
    """Terrain VRT next to the terrain HDF named in the geometry attributes."""
    rel = f["Geometry"].attrs["Terrain Filename"].decode().replace("\\", "/").lstrip("./")
    hdf = os.path.join(RAS, rel); vrt = hdf[:-4] + ".vrt"
    return vrt if os.path.exists(vrt) else hdf[:-4] + ".tif"

# ------------------------------------------------------------------ summaries and series
def summary(f, code):
    s = f["Results/Unsteady/Summary"].attrs; va = f["Results/Unsteady/Summary/Volume Accounting"].attrs
    import re
    ptxt = open(os.path.join(RAS, f"Majlas.{code}"), encoding="latin-1").read()
    title = re.search(r"^Plan Title=([^\r\n]*)", ptxt, flags=re.M).group(1).strip()
    d = {"plan": code, "plan_title": title, "solution": s["Solution"].decode(), "computation_time": s["Computation Time Total"].decode(),
         "unstable_at": None if math.isnan(float(s["Time Solution Went Unstable"])) else float(s["Time Solution Went Unstable"]),
         "volume_error_pct": float(va["Error Percent"]), "volume_in_1000m3": float(va["Total Boundary Flux of Water In"]),
         "volume_out_1000m3": float(va["Total Boundary Flux of Water Out"]), "volume_end_1000m3": float(va["Volume Ending"]),
         "volume_start_1000m3": float(va["Volume Starting"])}
    comp = f[TS + "/2D Flow Areas/" + AREA + "/Computations"]
    d["max_courant"] = float(np.nanmax(comp["Max Courant"][:])); d["max_volume_error_step"] = float(np.nanmax(np.abs(comp["Volume Error"][:])))
    t = times_h(f)
    if CONN in f:
        sv = f[CONN + "/Structure Variables"][:]
        bv = f[CONN + "/Breaching Variables"][:] if (CONN + "/Breaching Variables") in f else np.zeros((sv.shape[0], 8), np.float32)   # no-breach plans have none
        q = sv[:, 0]; i = int(np.nanargmax(q))
        d.update(peak_total_flow_m3s=float(q[i]), peak_time_h=float(t[i]), peak_stage_hw=float(sv[i, 2]), peak_stage_tw=float(sv[i, 3]),
                 breach_started=bool(np.nanmax(bv[:, 2]) > 0), breach_final_width=float(np.nanmax(bv[:, 2])),
                 breach_peak_flow_m3s=float(np.nanmax(bv[:, 6])), max_stage_hw=float(np.nanmax(sv[:, 2])))
        j = np.argmax(bv[:, 2] > 0) if d["breach_started"] else None
        d["breach_start_h"] = None if j is None else float(t[j]); d["stage_hw_at_breach"] = None if j is None else float(sv[j, 2])
        dt_h = float(np.median(np.diff(t))); d["volume_through_dam_Mm3"] = float(np.nansum(q) * dt_h * 3600 / 1e6)
    return d

def write_series(f, code, outdir):
    import csv
    t = times_h(f); dd = dates(f)
    if CONN in f:
        sv = f[CONN + "/Structure Variables"][:]
        bv = f[CONN + "/Breaching Variables"][:] if (CONN + "/Breaching Variables") in f else np.zeros((sv.shape[0], 8), np.float32)
        with open(os.path.join(outdir, "connection.csv"), "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["time_h", "date", "total_flow", "weir_flow", "stage_hw", "stage_tw", "breach_width", "breach_bottom", "breach_flow", "breach_velocity"])
            for k in range(len(t)): w.writerow([round(float(t[k]), 4), dd[k]] + [round(float(x), 3) for x in (sv[k, 0], sv[k, 1], sv[k, 2], sv[k, 3], bv[k, 2], bv[k, 3], bv[k, 6], bv[k, 7])])
    bc = f[TS + "/Boundary Conditions"]
    for name in bc.keys():
        if " - " in name: continue
        a = bc[name][:]
        with open(os.path.join(outdir, f"boundary_{name.replace(' ', '_')}.csv"), "w", newline="") as fh:
            w = csv.writer(fh); w.writerow(["time_h", "date", "stage", "flow"])
            for k in range(len(t)): w.writerow([round(float(t[k]), 4), dd[k], round(float(a[k, 0]), 3), round(float(a[k, 1]), 3)])

# ------------------------------------------------------------------ cell-based fields
def cell_geometry(f):
    g = f["Geometry/2D Flow Areas/" + AREA]
    xy = g["Cells Center Coordinate"][:]; zmin = g["Cells Minimum Elevation"][:]
    fci = g["Faces Cell Indexes"][:]; fnl = g["Faces NormalUnitVector and Length"][:]; flen = fnl[:, 2]
    return xy, zmin, fci, flen

def cell_velocity_series(f, fci, flen, ncell, block=200):
    """Face-length-weighted mean |face velocity| per cell for every time step, streamed in blocks. Returns (T, ncell) float32."""
    fv = f[TS + "/2D Flow Areas/" + AREA + "/Face Velocity"]; T = fv.shape[0]
    w = np.zeros(ncell, dtype=np.float64)
    for side in (0, 1):
        idx = fci[:, side]; ok = idx >= 0; np.add.at(w, idx[ok], flen[ok])
    out = np.zeros((T, ncell), dtype=np.float32)
    for a in range(0, T, block):
        v = np.abs(fv[a:a + block, :]).astype(np.float64)
        acc = np.zeros((v.shape[0], ncell), dtype=np.float64)
        for side in (0, 1):
            idx = fci[:, side]; ok = idx >= 0
            for r in range(v.shape[0]): np.add.at(acc[r], idx[ok], v[r, ok] * flen[ok])
        out[a:a + block] = (acc / np.maximum(w, 1e-9)).astype(np.float32)
    return out

def cell_fields(f, ref_hours=0.0):
    """Max depth, max velocity, max DxV, arrival and duration per cell (hours from ref_hours)."""
    xy, zmin, fci, flen = cell_geometry(f); n = len(zmin); t = times_h(f)
    zmin = np.where(np.isnan(zmin), 1e9, zmin)      # perimeter ghost cells have no elevation: treat as never wet
    ws = f[TS + "/2D Flow Areas/" + AREA + "/Water Surface"]; T = ws.shape[0]
    vel = cell_velocity_series(f, fci, flen, n)
    dmax = np.zeros(n, np.float32); vmax = np.zeros(n, np.float32); dvmax = np.zeros(n, np.float32)
    arrival = np.full(n, np.nan, np.float32); dur = np.zeros(n, np.float32)
    dt = np.diff(t, append=t[-1] + (t[-1] - t[-2] if T > 1 else 0))
    for a in range(0, T, 200):
        w = ws[a:a + 200, :]; d = np.maximum(w - zmin[None, :], 0).astype(np.float32); d[w <= -9000] = 0
        v = vel[a:a + 200]; dv = d * v
        dmax = np.maximum(dmax, d.max(0)); vmax = np.maximum(vmax, np.where(d > DEPTH_MIN, v, 0).max(0)); dvmax = np.maximum(dvmax, dv.max(0))
        wet = d >= ARRIVAL_DEPTH
        for r in range(w.shape[0]):
            k = a + r; new = wet[r] & np.isnan(arrival) & (t[k] >= ref_hours); arrival[new] = t[k] - ref_hours; dur += wet[r] * dt[k]
    return dict(xy=xy, zmin=zmin, dmax=dmax, vmax=vmax, dvmax=dvmax, arrival=arrival, duration=dur)

def hazard_class(d, v, dv):
    """AIDR H1..H6 (Smith, Davey and Cox 2014): a cell takes the highest class any threshold gives."""
    h = np.zeros_like(d, dtype=np.uint8)
    lim = [F.HAZ["H1"], F.HAZ["H2"], F.HAZ["H3"], F.HAZ["H4"], F.HAZ["H5"]]
    cls = np.ones_like(d, dtype=np.uint8)
    for i, (dvl, dl, vl) in enumerate(lim, start=1):
        above = (dv > dvl) | (d > dl) | (v > vl)
        cls = np.where(above & (cls == i), i + 1, cls)
    h[d > DEPTH_MIN] = cls[d > DEPTH_MIN]
    return h

# ------------------------------------------------------------------ rasters
def to_rasters(f, fields, outdir, wsmax):
    import rasterio
    from rasterio.transform import from_origin
    from scipy.spatial import cKDTree
    from scipy.interpolate import LinearNDInterpolator
    xy, zmin = fields["xy"], fields["zmin"]
    with rasterio.open(terrain_path(f)) as T:
        b = T.bounds; ter = T
        x0, y0 = math.floor(b.left / RES) * RES, math.ceil(b.top / RES) * RES
        nx = int((b.right - x0) / RES); ny = int((y0 - b.bottom) / RES)
        # limit to the perimeter bounds of the 2D area with a margin
        per = f["Geometry/2D Flow Areas/" + AREA + "/Perimeter"][:]
        px0, py0, px1, py1 = per[:, 0].min() - 50, per[:, 1].min() - 50, per[:, 0].max() + 50, per[:, 1].max() + 50
        cx0 = max(x0, math.floor(px0 / RES) * RES); cy1 = min(y0, math.ceil(py1 / RES) * RES)
        # same 2 m grid phase as the flood-protection risk rasters (origin 639849.39, 2601001.69), so the two studies overlay cell on cell
        RX, RY = 639849.391566265, 2601001.686746988
        cx0 = RX + math.floor((cx0 - RX) / RES) * RES; cy1 = RY - math.floor((RY - cy1) / RES) * RES
        nx = int((min(b.right, px1) - cx0) / RES); ny = int((cy1 - max(b.bottom, py0)) / RES)
        tr = from_origin(cx0, cy1, RES, RES)
        win = rasterio.windows.from_bounds(cx0, cy1 - ny * RES, cx0 + nx * RES, cy1, T.transform)
        terrain = T.read(1, window=win, out_shape=(ny, nx), resampling=rasterio.enums.Resampling.bilinear).astype(np.float32)
        nodata = T.nodata
    if nodata is not None: terrain[terrain == nodata] = np.nan
    xs = cx0 + (np.arange(nx) + 0.5) * RES; ys = cy1 - (np.arange(ny) + 0.5) * RES
    X, Y = np.meshgrid(xs, ys)
    wet = fields["dmax"] > DEPTH_MIN
    # nearest cell for every pixel (cell-constant products), and linear WSE for depth
    tree = cKDTree(xy); dist, near = tree.query(np.c_[X.ravel(), Y.ravel()], k=1)
    near = near.reshape(ny, nx); dist = dist.reshape(ny, nx)
    inside = dist < 60
    wse_lin = LinearNDInterpolator(xy[wet], wsmax[wet], fill_value=np.nan)(X, Y) if wet.sum() > 3 else np.full((ny, nx), np.nan)
    wse_near = np.where(wet[near], wsmax[near], np.nan)
    wse = np.where(np.isnan(wse_lin), wse_near, wse_lin)
    depth = wse - terrain; depth[(depth < DEPTH_MIN) | ~inside | ~wet[near]] = np.nan
    def cellfield(a):
        r = a[near].astype(np.float32); r[np.isnan(depth)] = np.nan; return r
    def smoothfield(a):
        """linear interpolation between wet cell centres (as RAS Mapper does for velocity), nearest cell where no triangle covers a pixel;
        cell-constant fields made the hazard classes blocky at the mesh size (10 to 40 m) although the raster is 2 m"""
        lin = LinearNDInterpolator(xy[wet], a[wet], fill_value=np.nan)(X, Y) if wet.sum() > 3 else np.full((ny, nx), np.nan)
        r = np.where(np.isnan(lin), a[near], lin).astype(np.float32); r[np.isnan(depth)] = np.nan; return r
    # Connected flood only: patches smaller than MIN_PATCH_HA (rain-on-grid puddles, single wet cells in the hills) are dropped from every
    # product and from the statistics, so the maps show the flood that comes down the wadi and not a speckle of ponds (user, 2026-09-23).
    from scipy import ndimage
    lab, nlab = ndimage.label(~np.isnan(depth))
    if nlab:
        sizes = ndimage.sum(np.ones_like(lab), lab, index=np.arange(1, nlab + 1)); small = np.zeros(nlab + 1, bool); small[1:] = sizes < MIN_PATCH_HA * 1e4 / (RES * RES)
        depth[small[lab]] = np.nan
    prods = {"max_depth": depth.astype(np.float32), "max_velocity": smoothfield(fields["vmax"]), "max_dv": smoothfield(fields["dvmax"]),
             "arrival_h": smoothfield(fields["arrival"]), "duration_h": cellfield(fields["duration"])}      # arrival interpolated like velocity (no mesh blocks)
    # Reservoir vs downstream, by geometry: the reservoir is the water on the upstream side of the dam axis (the SA/2D connection centreline)
    # that is already there at the reference time. Everything else is downstream, including the gorge cells that a trickle over the ogee
    # wetted before the breach (an earlier "wet after the breach" rule dropped those and made the hazard map start below the dam).
    # Rasters (depth, velocity, arrival, hazard) cover ALL wet cells so the maps are continuous from the pool through the dam; the
    # statistics (areas, depths, people) use the downstream part only.
    try:
        cl = f["Geometry/Structures/Centerline Points"][:2]
        (ax0, ay0), (ax1, ay1) = cl[0], cl[1]
        side = (X - ax0) * (ay1 - ay0) - (Y - ay0) * (ax1 - ax0)          # sign = side of the extended axis line
        pre_wet_deep = np.isfinite(prods["arrival_h"]) & (prods["arrival_h"] <= 0.1) & (depth > 10)
        res_sign = np.sign(np.nanmedian(side[pre_wet_deep])) if pre_wet_deep.any() else 0
        # everything wet on the pool's side of the extended dam axis is reservoir (the axis runs NNW-SSE, the reservoir arms lie west of
        # it and all downstream flooding east); an arrival-time condition left the rising pool margins unmasked in the PMF runs
        reservoir = (np.sign(side) == res_sign) & ~np.isnan(depth)
    except Exception as e:
        print("reservoir mask by axis failed, falling back to 'wet after the reference time':", e); reservoir = np.isfinite(prods["arrival_h"]) & (prods["arrival_h"] <= 0)
    downstream = ~np.isnan(depth) & ~reservoir
    prods["arrival_h"] = np.where(reservoir, np.nan, prods["arrival_h"]).astype(np.float32)    # a pool that is there from the start has no arrival time
    hz = hazard_class(np.nan_to_num(depth), np.nan_to_num(prods["max_velocity"]), np.nan_to_num(prods["max_dv"]))
    hz_ds = np.where(downstream, hz, 0)
    prof = dict(driver="GTiff", height=ny, width=nx, count=1, crs="EPSG:32640", transform=tr, compress="deflate", tiled=True)
    for name, arr in prods.items():
        with rasterio.open(os.path.join(outdir, name + ".tif"), "w", dtype="float32", nodata=-9999, **prof) as dst:
            dst.write(np.where(np.isnan(arr), -9999, arr).astype(np.float32), 1)
    with rasterio.open(os.path.join(outdir, "hazard_aidr.tif"), "w", dtype="uint8", nodata=0, **prof) as dst: dst.write(hz, 1)
    dd = np.where(downstream, depth, np.nan); vv = np.where(downstream, prods["max_velocity"], np.nan); dv = np.where(downstream, prods["max_dv"], np.nan)
    plain = downstream & (X > PLAIN_X0)          # the coastal plain east of the gorge exit; the gorge itself holds 45 to 55 m of water below the dam
    dp = np.where(plain, depth, np.nan)
    stats = {"inundated_area_km2_gt0.3m": float(np.nansum(dd > 0.3) * RES * RES / 1e6),            # downstream land only
             "inundated_area_km2_gt0.3m_incl_reservoir": float(np.nansum(depth > 0.3) * RES * RES / 1e6),
             "max_depth_m": float(np.nanmax(dd)) if np.isfinite(dd).any() else None, "max_depth_incl_reservoir_m": float(np.nanmax(depth)),
             "max_depth_plain_m": float(np.nanmax(dp)) if np.isfinite(dp).any() else None, "max_depth_plain_p99_m": float(np.nanpercentile(dp, 99)) if np.isfinite(dp).any() else None,
             "max_velocity_ms": float(np.nanmax(vv)) if np.isfinite(vv).any() else None, "max_dv_m2s": float(np.nanmax(dv)) if np.isfinite(dv).any() else None,
             "arrival_h_median": float(np.nanmedian(prods["arrival_h"][downstream])) if downstream.any() else None,
             "arrival_h_max": float(np.nanmax(prods["arrival_h"][downstream])) if downstream.any() else None,
             "reservoir_area_km2": float(reservoir.sum() * RES * RES / 1e6),
             "pixels": int(nx * ny), "hazard_area_km2": {f"H{i}": float((hz_ds == i).sum() * RES * RES / 1e6) for i in range(1, 7)}}   # downstream only
    return stats

def process(code, ref_hours=0.0, rasters=True):
    outdir = os.path.join(OUT, code); os.makedirs(outdir, exist_ok=True)
    with open_plan(code) as f:
        s = summary(f, code); write_series(f, code, outdir)
        if s.get("breach_start_h") is not None and ref_hours == 0.0: ref_hours = s["breach_start_h"]
        s["reference_time_h_for_arrival"] = ref_hours
        if rasters:
            fields = cell_fields(f, ref_hours); wsmax = f[SUMM + "/Maximum Water Surface"][0, :]
            s.update(to_rasters(f, fields, outdir, wsmax))
    json.dump(s, open(os.path.join(outdir, "summary.json"), "w"), indent=2); print(json.dumps(s, indent=1)); return s

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ref = 0.0
    if "--ref-hours" in sys.argv: ref = float(sys.argv[sys.argv.index("--ref-hours") + 1])
    for code in args: process(code, ref, rasters="--no-rasters" not in sys.argv)
