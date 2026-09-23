# -*- coding: utf-8 -*-
"""Extract the HEC-RAS boundary-condition hydrographs from the HEC-HMS "DA <rp> Res2" runs (south catchment added).

Elements (own-element records only, F-part ends with ">element"):
  Majlas Dam Reservoir  FLOW-COMBINE  -> reservoir inflow (upstream BC line of the reservoir 2D area)
  Majlas Dam Reservoir  FLOW          -> reservoir outflow (design routing check only, not a BC)
  J11                   FLOW          -> downstream tributary BC line
  Jsouth                FLOW          -> south catchment BC line

Output (W2/04_data):
  hms_res2_hydrographs.xlsx : "Peaks" summary; "All Hydrographs" (hours + every RP x 4 series); one sheet per RP with datetime,
                              hours and the 4 series; per-location sheets for HEC-RAS pasting
  hms_res2_<location>.csv   : hours + all RPs for one location
Based on Hydrology/Claude/Claude 15062026/W2 Majlas/scripts/01_hydrographs.py (hecdss reader), extended to Jsouth and to
uncondensed day-block records.
"""
from pathlib import Path
import re
import hecdss
import pandas as pd

HERE = Path(__file__).resolve().parent
W2 = HERE.parent
HMS = W2.parent / "HEC_HMS_Majlas"
OUT = W2 / "04_data"
OUT.mkdir(exist_ok=True)
XLSX = OUT / "hms_res2_hydrographs.xlsx"

RP_ORDER = ["2yr", "5yr", "10yr", "25yr", "50yr", "100yr", "200yr", "500yr", "1000yr", "2000yr", "5000yr", "10000yr", "PMP"]
SERIES = {   # column name -> (B part, C part)
    "Reservoir inflow": ("Majlas Dam Reservoir", "FLOW-COMBINE"),
    "Reservoir outflow (check)": ("Majlas Dam Reservoir", "FLOW"),
    "J11": ("J11", "FLOW"),
    "Jsouth": ("Jsouth", "FLOW"),
}

def own_paths(paths, b_part, c_part):
    """All day-block records of one element's own result (F part ends with '>element')."""
    out = []
    for p in paths:
        parts = p.split("/")
        if len(parts) < 7: continue
        if parts[2] != b_part or parts[3] != c_part: continue
        if parts[6].split(">")[-1] == b_part: out.append(p)
    return out

def read_series(dss, paths):
    """Concatenate the day blocks into one time series (datetime index, m3/s)."""
    frames = []
    for p in paths:
        rec = dss.get(p)
        if rec is None: continue
        frames.append(pd.Series(list(rec.values), index=pd.DatetimeIndex(list(rec.times)), dtype=float))
    if not frames: return None
    s = pd.concat(frames).sort_index()
    s = s[~s.index.duplicated(keep="first")]
    return s

def main():
    data = {}       # rp -> DataFrame(datetime index, columns = SERIES)
    for rp in RP_ORDER:
        f = HMS / f"DA_{rp}_Res2.dss"
        if not f.exists():
            print(f"  missing {f.name}"); continue
        with hecdss.HecDss(str(f)) as dss:
            paths = dss.get_catalog().uncondensed_paths
            cols = {}
            for col, (b, c) in SERIES.items():
                s = read_series(dss, own_paths(paths, b, c))
                if s is None: print(f"  {rp}: no record for {col}")
                else: cols[col] = s
        if not cols: continue
        df = pd.DataFrame(cols).sort_index()
        df.index.name = "datetime"
        data[rp] = df
        print(f"  {rp}: {len(df)} steps, {df.index[0]} to {df.index[-1]}, step {(df.index[1]-df.index[0])}")
    if not data: raise SystemExit("nothing read")

    # peaks and volumes
    rows = []
    for rp, df in data.items():
        dt_h = (df.index[1] - df.index[0]).total_seconds() / 3600
        for col in df.columns:
            s = df[col]
            rows.append({"Return period": rp, "Location": col, "Peak (m3/s)": round(float(s.max()), 1),
                         "Time of peak (h from start)": round((s.idxmax() - df.index[0]).total_seconds() / 3600, 2),
                         "Time of peak": s.idxmax(), "Volume (Mm3)": round(float(s.sum() * dt_h * 3600 / 1e6), 2)})
    peaks = pd.DataFrame(rows)
    peaks_wide = peaks.pivot(index="Return period", columns="Location", values="Peak (m3/s)").reindex([r for r in RP_ORDER if r in data])

    # common hours axis from the longest run
    ref_rp = max(data, key=lambda r: len(data[r]))
    ref = data[ref_rp]; t0 = ref.index[0]
    hours = [(t - t0).total_seconds() / 3600 for t in ref.index]
    all_cols = {"time (hr)": hours}
    for rp in [r for r in RP_ORDER if r in data]:
        df = data[rp].reindex(ref.index)
        for col in SERIES:
            if col in df: all_cols[f"{rp} {col}"] = df[col].values
    df_all = pd.DataFrame(all_cols)

    with pd.ExcelWriter(XLSX, engine="openpyxl") as xl:
        peaks_wide.to_excel(xl, sheet_name="Peaks")
        peaks.to_excel(xl, sheet_name="Peaks detail", index=False)
        df_all.to_excel(xl, sheet_name="All Hydrographs", index=False)
        for col in SERIES:                                   # one sheet per location, all RPs side by side (for HEC-RAS pasting)
            loc = {"time (hr)": hours}
            for rp in [r for r in RP_ORDER if r in data]:
                d = data[rp].reindex(ref.index)
                if col in d: loc[rp] = d[col].values
            dloc = pd.DataFrame(loc)
            name = col.replace(" (check)", "").replace(" ", "_")
            dloc.to_excel(xl, sheet_name=name[:31], index=False)
            dloc.to_csv(OUT / f"hms_res2_{name}.csv", index=False)
        for rp in [r for r in RP_ORDER if r in data]:        # one sheet per RP with datetime
            d = data[rp].copy(); d.insert(0, "time (hr)", [(t - d.index[0]).total_seconds() / 3600 for t in d.index])
            d.reset_index().to_excel(xl, sheet_name=rp, index=False)
    print("\nPeaks (m3/s):"); print(peaks_wide.to_string())
    print("\nwrote", XLSX)

if __name__ == "__main__":
    main()
