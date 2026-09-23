"""Warning-time products per plan (user request, 2026-09-23 06:30): the hazard maps alone make the PMF look as bad as a failure;
what separates them is how fast the water comes.

Per plan, from the 2 m products in W2/04_data/results/<plan>/:
  warning.json    arrival at named places; people and plots reached within each arrival band (cumulative); people by
                  arrival band x AIDR hazard class; the cumulative people-versus-time curve (5 min steps) for the chart
For a flood-day failure (S2D and its sensitivity runs) the plain is already under the PMF when the dam fails, so the
arrival used is the INCREMENTAL one: the first time after the breach at which the failure run is 0.3 m deeper than its
no-failure twin at the same instant (both on the same mesh and the same 5 min output):
  warning_arrival_h.tif   2 m, hours after the reference time at which the depth rises 0.3 m above the pre-event depth (own state at
                         the reference time, or the twin's state at the same instant); NaN where it never does

Clocks: sunny-day and flood-day failures count from the breach; the PMF without failure counts from the start of the storm.
The model gives travel time; warning time = travel time minus detection and dissemination, which this study does not set.

python ras_warning.py p28 p29 p32 p30 ...      (a flood-day failure needs its twin's HDF: TWINS in ras_analysis)
"""
import os, sys, json
import numpy as np
import ras_results as RR
import ras_analysis as RA

HERE = os.path.dirname(os.path.abspath(__file__)); W2 = os.path.abspath(os.path.join(HERE, ".."))
RES = os.path.join(W2, "04_data", "results")
ARRIVAL_DEPTH = 0.3          # m: the depth whose arrival is timed (same as the arrival maps)
INC_DEPTH = 0.3              # m: the extra depth that marks the arrival of the failure wave over the PMF
BANDS_FAIL = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 6.0]        # h after the breach
BANDS_PMF = [3.0, 6.0, 9.0, 12.0, 15.0, 18.0, 24.0, 36.0]      # h after the start of the storm
# named places (EPSG:32640); "column" places take the first-reached wet pixel on that easting (the wadi thread)
PLACES = [("Gorge exit, start of the fan", ("column", RR.PLAIN_X0)),
          ("Head of the training dikes", (693610.0, 2574340.0)),          # between the two dike heads (Dykes.shp, west ends)
          ("Qurayat, residential centre", (695276.0, 2573286.0)),        # centroid of the residential plots (land-use layer)
          ("Shoreline, 'Outflow Sea' line", (697256.0, 2573766.0)),       # midpoint of the coastal boundary line
          ("Southern outlet, 'Outflow 2' line", (696759.0, 2568798.0))]
SEARCH_M = 150.0             # a place is "reached" when a wet pixel within this radius is reached
FLOOD_DAY = {k: v for k, v in RA.TWINS.items()}      # failure plan -> no-failure twin


def read(path):
    import rasterio
    with rasterio.open(path) as d:
        a = d.read(1).astype(np.float32); nod = d.nodata
        if nod is not None: a[a == nod] = np.nan
        return a, d.transform


def open_hdf(plan):
    """the plan's result file, wherever it was run (main project or a parallel copy): the newest Majlas.<plan>.hdf"""
    import h5py, glob
    cands = glob.glob(os.path.join(W2, "..", "HEC-RAS Majlas*", f"Majlas.{plan}.hdf"))
    cands = [c for c in cands if "_test" not in c]
    if not cands: raise FileNotFoundError(f"no result file for {plan}")
    return h5py.File(max(cands, key=os.path.getmtime), "r")


def flood_day(plan):
    s = json.load(open(os.path.join(RES, plan, "summary.json")))
    return plan in FLOOD_DAY and s.get("breach_start_h") is not None and s["breach_start_h"] > 5.0


def event_arrival(plan, twin=None):
    """Hours after the reference time at which the depth first rises INC_DEPTH above the pre-event depth, per cell, on the 2 m grid.
    twin None: pre-event depth = the plan's own depth at the reference time (breach for a failure, storm start for the PMF), so the
    wadi thread wetted by the fill trickle does not count as 'reached'. twin given (flood-day failure): pre-event depth = the
    no-failure twin at the same instant, i.e. the arrival of the failure wave on top of the PMF."""
    import rasterio
    from scipy.spatial import cKDTree
    from scipy.interpolate import LinearNDInterpolator
    s = json.load(open(os.path.join(RES, plan, "summary.json"))); ref = s["breach_start_h"] if s.get("breach_start_h") is not None else 0.0
    with open_hdf(plan) as fa, (open_hdf(twin) if twin else open_hdf(plan)) as fb:
        xy, zmin, _, _ = RR.cell_geometry(fa); n = len(zmin); zmin = np.where(np.isnan(zmin), 1e9, zmin)
        ta, tb = RR.times_h(fa), RR.times_h(fb); T = min(len(ta), len(tb))      # sensitivity runs use a 36 h window, the base runs 60 h
        if np.abs(ta[:T] - tb[:T]).max() > 1e-6: raise RuntimeError(f"{plan} and {twin} do not share the output times")
        wsa = fa[RR.TS + "/2D Flow Areas/" + RR.AREA + "/Water Surface"]; wsb = fb[RR.TS + "/2D Flow Areas/" + RR.AREA + "/Water Surface"]
        if wsa.shape[1] != wsb.shape[1]: raise RuntimeError(f"{plan} and {twin} do not share the mesh")
        k0 = int(np.searchsorted(ta, ref - 1e-9))
        w0 = wsb[k0, :]; d0 = np.maximum(w0 - zmin, 0); d0[w0 <= -9000] = 0          # pre-event depth (own or twin's) at the reference time
        arr = np.full(n, np.nan, np.float32)
        for a in range(k0, T, 100):
            b = min(a + 100, T); wa = wsa[a:b, :]
            da = np.maximum(wa - zmin[None, :], 0); da[wa <= -9000] = 0
            if twin:
                wb = wsb[a:b, :]; db = np.maximum(wb - zmin[None, :], 0); db[wb <= -9000] = 0; inc = da - db
            else:
                inc = da - d0[None, :]
            for r in range(wa.shape[0]):
                new = (inc[r] >= INC_DEPTH) & np.isnan(arr); arr[new] = ta[a + r] - ref
    # onto the plan's own 2 m grid, masked by its flooded area (reservoir excluded through arrival_h)
    depth, tr = read(os.path.join(RES, plan, "max_depth.tif")); base, _ = read(os.path.join(RES, plan, "arrival_h.tif"))
    ny, nx = depth.shape
    xs = tr.c + (np.arange(nx) + 0.5) * tr.a; ys = tr.f + (np.arange(ny) + 0.5) * tr.e; X, Y = np.meshgrid(xs, ys)
    have = np.isfinite(arr)
    lin = LinearNDInterpolator(xy[have], arr[have], fill_value=np.nan)(X, Y) if have.sum() > 3 else np.full((ny, nx), np.nan)
    tree = cKDTree(xy); dist, near = tree.query(np.c_[X.ravel(), Y.ravel()], k=1); near = near.reshape(ny, nx)
    out = np.where(np.isnan(lin), np.where(have[near], arr[near], np.nan), lin).astype(np.float32)
    out[~np.isfinite(depth) | ~np.isfinite(base)] = np.nan
    with rasterio.open(os.path.join(RES, plan, "max_depth.tif")) as d: prof = d.profile
    prof.update(dtype="float32", nodata=-9999.0, count=1)
    with rasterio.open(os.path.join(RES, plan, "warning_arrival_h.tif"), "w", **prof) as dst: dst.write(np.where(np.isfinite(out), out, -9999.0).astype(np.float32), 1)
    print(f"{plan}: rise of {INC_DEPTH} m above {'twin ' + twin if twin else 'the pre-event depth'}: {int(have.sum())} cells, median {np.nanmedian(out):.2f} h after the reference")
    return out, tr


def places(arrival, depth, tr):
    """arrival (h) at the named places: the earliest wet pixel within SEARCH_M, or None"""
    inv = ~tr; out = {}
    for name, loc in PLACES:
        if loc[0] == "column":
            c = int((loc[1] - tr.c) / tr.a); band = arrival[:, max(c - 10, 0):c + 10]
            out[name] = None if not np.isfinite(band).any() else float(np.nanmin(band)); continue
        c, r = inv * loc; c, r = int(c), int(r); k = int(SEARCH_M / abs(tr.a))
        win = arrival[max(r - k, 0):r + k, max(c - k, 0):c + k]
        out[name] = None if not np.isfinite(win).any() else float(np.nanmin(win))
    return out


def people_plots(arrival, depth, hz, tr, bands):
    """cumulative people and plots reached by each band; people by band x hazard class; 5 min cumulative curve"""
    import rasterio, geopandas as gpd
    from rasterio import features
    with rasterio.open(RA.POP) as P:
        pop = P.read(1).astype(np.float64); pop[pop == P.nodata] = 0; pop[pop < 0] = 0
        rows, cols = np.indices(pop.shape); xs, ys = rasterio.transform.xy(P.transform, rows, cols)
        xs = np.array(xs).ravel(); ys = np.array(ys).ravel(); pv = pop.ravel()
    inv = ~tr; c, r = inv * (xs, ys); c = np.floor(c).astype(int); r = np.floor(r).astype(int)
    ok = (r >= 0) & (r < depth.shape[0]) & (c >= 0) & (c < depth.shape[1])
    dep = np.full(len(pv), np.nan); dep[ok] = depth[r[ok], c[ok]]
    arr = np.full(len(pv), np.nan); arr[ok] = arrival[r[ok], c[ok]]
    cls = np.zeros(len(pv), int); cls[ok] = hz[r[ok], c[ok]]
    reached = (dep > ARRIVAL_DEPTH) & np.isfinite(arr)
    total = float(pv[dep > ARRIVAL_DEPTH].sum())
    people_cum = [float(pv[reached & (arr <= b)].sum()) for b in bands]
    groups = {"H1-H3": (1, 2, 3), "H4": (4,), "H5": (5,), "H6": (6,)}
    matrix = {}
    prev = -1.0
    for b in bands:
        sel = reached & (arr > prev) & (arr <= b); matrix[str(b)] = {g: float(pv[sel & np.isin(cls, ks)].sum()) for g, ks in groups.items()}; prev = b
    late = reached & (arr > bands[-1]); matrix["later"] = {g: float(pv[late & np.isin(cls, ks)].sum()) for g, ks in groups.items()}
    tmax = float(np.nanmax(arr[reached])) if reached.any() else 0.0
    tt = np.arange(0, tmax + 1 / 12, 1 / 12); curve = [float(pv[reached & (arr <= t)].sum()) for t in tt]
    # plots: a plot is reached when its earliest wet pixel is reached
    lu = gpd.read_file(RA.LU)
    ids = features.rasterize(((g, i + 1) for i, g in enumerate(lu.geometry)), out_shape=depth.shape, transform=tr, fill=0, dtype="int32")
    wet = (depth > ARRIVAL_DEPTH) & np.isfinite(arrival) & (ids > 0)
    first = np.full(len(lu) + 1, np.inf); np.minimum.at(first, ids[wet], arrival[wet]); first = first[1:]
    plots_cum = [int((first <= b).sum()) for b in bands]
    return dict(people_total=total, people_cum=people_cum, plots_total=int(np.isfinite(first).sum()), plots_cum=plots_cum, matrix=matrix,
                curve={"t_h": [round(float(t), 4) for t in tt], "people": curve})


def analyse(plan):
    d = os.path.join(RES, plan)
    depth, tr = read(os.path.join(d, "max_depth.tif")); hz, _ = read(os.path.join(d, "hazard_aidr.tif")); hz = np.nan_to_num(hz).astype(int)
    s = json.load(open(os.path.join(d, "summary.json")))
    if flood_day(plan):
        arrival, _ = event_arrival(plan, FLOOD_DAY[plan]); bands = BANDS_FAIL
        ref = f"hours after the breach at {s['breach_start_h']:.2f} h at which the failure run is {INC_DEPTH} m deeper than {FLOOD_DAY[plan]} at the same instant"
    else:
        arrival, _ = event_arrival(plan)
        bands = BANDS_FAIL if s.get("breach_start_h") is not None else BANDS_PMF
        ref = (f"hours after the breach at which the depth rises {INC_DEPTH} m above the pre-breach depth" if s.get("breach_start_h") is not None
               else f"hours after the start of the storm at which the depth rises {INC_DEPTH} m above the initial depth")
    out = {"plan": plan, "reference": ref, "bands_h": bands, "places": places(arrival, depth, tr)}
    out.update(people_plots(arrival, depth, hz, tr, bands))
    json.dump(out, open(os.path.join(d, "warning.json"), "w"), indent=1)
    print(plan, "|", ref, "| people reached:", [f"{b:g}h {p:,.0f}" for b, p in zip(bands, out["people_cum"])], "| places:",
          {k: (None if v is None else round(v, 2)) for k, v in out["places"].items()})
    return out


# ---------------------------------------------------------------- isolines for the combined maps (user, 2026-09-23 11:40)
ISO_FAIL = [(5 / 60, "5 min"), (10 / 60, "10 min"), (0.25, "15 min"), (0.5, "30 min"), (1.0, "1 h")]      # after the breach
ISO_PMF = [(1.0, "1 h"), (2.0, "2 h"), (3.0, "3 h"), (6.0, "6 h"), (12.0, "12 h")]                        # after the start of the storm
HAZ_LINES = [(3.5, "H4"), (5.5, "H6")]          # boundaries of 'unsafe on foot' (H4 and worse) and 'buildings fail' (H6)
HAZ_LINES_ALL = [(1.5, "H2"), (2.5, "H3"), (3.5, "H4"), (4.5, "H5"), (5.5, "H6")]   # every class boundary (line = where that class begins)


def _contours(field, xs, ys, levels, min_len=300.0):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    feats = []; fig, ax = plt.subplots(); cs = ax.contour(xs, ys, np.ma.masked_invalid(field), levels=[l for l, _ in levels])
    paths = cs.get_paths() if hasattr(cs, "get_paths") else [c.get_paths() for c in cs.collections]
    for (lev, lab), path in zip(levels, paths):
        polys = path.to_polygons(closed_only=False) if hasattr(path, "to_polygons") else [q for pp in path for q in pp.to_polygons(closed_only=False)]
        for poly in polys:
            pts = [(float(x), float(y)) for x, y in poly]
            L = sum(np.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
            if L < min_len: continue
            feats.append({"type": "Feature", "properties": {"level": lev, "label": lab}, "geometry": {"type": "LineString", "coordinates": pts}})
    plt.close(fig); return feats


def _block(a, tr, k, how):
    """2 m -> 2k m by block minimum (arrival: earliest) or maximum (hazard: worst); dry stays NaN"""
    ny, nx = a.shape[0] // k * k, a.shape[1] // k * k; b = a[:ny, :nx].reshape(ny // k, k, nx // k, k)
    if how == "min": m = np.nanmin(np.where(np.isnan(b), np.inf, b), axis=(1, 3)); m[~np.isfinite(m)] = np.nan
    else: m = np.nanmax(np.where(np.isnan(b), -np.inf, b), axis=(1, 3)); m[~np.isfinite(m)] = np.nan
    xs = tr.c + (np.arange(m.shape[1]) * k + k / 2) * tr.a; ys = tr.f + (np.arange(m.shape[0]) * k + k / 2) * tr.e
    return m, xs, ys


def isolines(plan, version="v3"):
    """isochrones_<version>.geojson (arrival of the 0.3 m rise; failure wave for a flood-day failure) and hazard_lines_<version>.geojson
    (H4 and H6 boundaries) in the plan's results folder, EPSG:32640, at 10 m"""
    from scipy import ndimage
    d = os.path.join(RES, plan); s = json.load(open(os.path.join(d, "summary.json")))
    fail = s.get("breach_start_h") is not None
    arr, tr = read(os.path.join(d, "warning_arrival_h.tif")); m, xs, ys = _block(arr, tr, 5, "min")
    if fail:
        f = ndimage.generic_filter(np.where(np.isnan(m), np.inf, m), np.min, size=3); f[~np.isfinite(f)] = np.nan; f = np.where(np.isfinite(m), f, np.nan)
        iso = _contours(f, xs, ys, ISO_FAIL)
    else:   # the PMF arrival is a rain-on-grid patchwork: heavy smoothing, and only the long lines survive
        f = ndimage.median_filter(np.where(np.isnan(m), 99.0, m), size=15); f = np.where(np.isfinite(m), f, np.nan)
        iso = _contours(f, xs, ys, ISO_PMF, min_len=2000.0)
    hz, _ = read(os.path.join(d, "hazard_aidr.tif")); hz = np.where((hz > 0) & np.isfinite(arr), hz, np.nan); h, xs2, ys2 = _block(hz, tr, 5, "max")   # downstream only: the reservoir carries no arrival
    h = ndimage.median_filter(np.nan_to_num(h, nan=0.0), size=3).astype(float)     # dry = class 0, so every outline closes along the flood edge
    lines = _contours(h, xs2, ys2, HAZ_LINES, min_len=800.0)          # small islands of a class only clutter the map
    lines_all = _contours(h, xs2, ys2, HAZ_LINES_ALL, min_len=800.0)
    crs = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::32640"}}
    json.dump({"type": "FeatureCollection", "crs": crs, "features": iso}, open(os.path.join(d, f"isochrones_{version}.geojson"), "w"))
    json.dump({"type": "FeatureCollection", "crs": crs, "features": lines}, open(os.path.join(d, f"hazard_lines_{version}.geojson"), "w"))
    json.dump({"type": "FeatureCollection", "crs": crs, "features": lines_all}, open(os.path.join(d, f"hazard_lines_all_{version}.geojson"), "w"))
    print(plan, "isochrones", {lab: sum(1 for x in iso if x["properties"]["label"] == lab) for _, lab in (ISO_FAIL if fail else ISO_PMF)},
          "hazard lines", {lab: sum(1 for x in lines if x["properties"]["label"] == lab) for _, lab in HAZ_LINES})


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    for code in args: (isolines(code) if "--lines" in sys.argv else analyse(code))
