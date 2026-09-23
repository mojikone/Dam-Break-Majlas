"""
Extract hydrographs for Majlas Dam Reservoir (inflow & outflow) and J11
from DA_*_Res.dss files for all return periods.

Output: W2 Majlas/output/hydrographs.xlsx

Sheet layout:
  1. "All Hydrographs"       – time (hr) + all RPs × {inflow, outflow, J11}
  2. "2yr inflow"            – time (hr), Dam Reservoir Inflow, J11
     …
  14. "PMP inflow"
  15. "2yr outflow"          – time (hr), Dam Reservoir Outflow, J11
     …
  27. "PMP outflow"
"""
from pathlib import Path
import hecdss
import pandas as pd

ROOT       = Path(__file__).resolve().parents[2]
DATA_DIR   = ROOT / "Data" / "HEC_HMS_Majlas"
OUTPUT_DIR = ROOT / "W2 Majlas" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
XLSX = OUTPUT_DIR / "hydrographs.xlsx"

RP_ORDER = ["2yr","5yr","10yr","25yr","50yr","100yr","200yr","500yr",
            "1000yr","2000yr","5000yr","10000yr","PMP"]

RESERVOIR = "Majlas Dam Reservoir"
J11       = "J11"

COL_INFLOW  = "Dam Reservoir Inflow"
COL_OUTFLOW = "Dam Reservoir Outflow"
COL_J11     = "J11"


def own_ap_path(paths: list[str], b_part: str, c_part: str) -> str | None:
    for p in paths:
        parts = p.split("/")
        if len(parts) < 7:
            continue
        if parts[2] != b_part or parts[3] != c_part:
            continue
        if p.rstrip("/").split(">")[-1] == b_part:
            return p
    return None


def read_series(dss: hecdss.HecDss, path: str | None) -> tuple[list, list]:
    if path is None:
        return None, None
    try:
        rec = dss.get(path)
        return (list(rec.times), list(rec.values)) if rec else (None, None)
    except Exception as e:
        print(f"  WARN: {e}")
        return None, None


def times_to_hours(times: list) -> list[float]:
    t0 = times[0]
    return [round((t - t0).total_seconds() / 3600, 6) for t in times]


def main():
    # ── Read all data ─────────────────────────────────────────────────────────
    data: dict[str, dict] = {}   # rp -> {t_hr, v_in, v_out, v_j11}

    for rp in RP_ORDER:
        dss_path = DATA_DIR / f"DA_{rp}_Res.dss"
        if not dss_path.exists():
            print(f"  WARN: DA_{rp}_Res.dss not found — skipping {rp}")
            continue
        print(f"  {rp} ...", end=" ", flush=True)
        with hecdss.HecDss(str(dss_path)) as dss:
            paths = dss.get_catalog().uncondensed_paths

            t_in,  v_in  = read_series(dss, own_ap_path(paths, RESERVOIR, "FLOW-COMBINE"))
            t_out, v_out = read_series(dss, own_ap_path(paths, RESERVOIR, "FLOW"))
            t_j11, v_j11 = read_series(dss, own_ap_path(paths, J11, "FLOW"))

        # Use the first available time vector for hours axis
        ref_t = t_in or t_out or t_j11
        if ref_t is None:
            print("no data")
            continue
        t_hr = times_to_hours(ref_t)

        # Align all series to the reference time axis
        def align(t, v):
            if t is None or v is None:
                return [None] * len(t_hr)
            if len(v) == len(t_hr):
                return list(v)
            # Reindex via pandas if lengths differ
            ser = pd.Series(v, index=pd.DatetimeIndex(t))
            idx = pd.DatetimeIndex(ref_t)
            return ser.reindex(idx).values.tolist()

        data[rp] = {
            "t_hr":  t_hr,
            "v_in":  align(t_in,  v_in),
            "v_out": align(t_out, v_out),
            "v_j11": align(t_j11, v_j11),
        }
        print(f"{len(t_hr)} steps")

    if not data:
        raise RuntimeError("No data read. Check DSS files.")

    # Common time axis (first available RP)
    ref_rp   = next(iter(data))
    t_hr_ref = data[ref_rp]["t_hr"]
    n        = len(t_hr_ref)

    # ── Build DataFrames ──────────────────────────────────────────────────────

    def rp_df_inflow(rp: str) -> pd.DataFrame:
        d = data.get(rp, {})
        return pd.DataFrame({
            "time (hr)":    d.get("t_hr", [None]*n),
            COL_INFLOW:     d.get("v_in", [None]*n),
            COL_J11:        d.get("v_j11", [None]*n),
        })

    def rp_df_outflow(rp: str) -> pd.DataFrame:
        d = data.get(rp, {})
        return pd.DataFrame({
            "time (hr)":    d.get("t_hr", [None]*n),
            COL_OUTFLOW:    d.get("v_out", [None]*n),
            COL_J11:        d.get("v_j11", [None]*n),
        })

    # "All Hydrographs" sheet: time (hr) + all RPs × {inflow, outflow, J11}
    all_cols: dict[str, list] = {"time (hr)": t_hr_ref}
    for rp in RP_ORDER:
        if rp not in data:
            continue
        d = data[rp]
        all_cols[f"{rp} {COL_INFLOW}"]  = d["v_in"]
        all_cols[f"{rp} {COL_OUTFLOW}"] = d["v_out"]
        all_cols[f"{rp} {COL_J11}"]     = d["v_j11"]
    df_all = pd.DataFrame(all_cols)

    # ── Write Excel ───────────────────────────────────────────────────────────
    with pd.ExcelWriter(XLSX, engine="openpyxl") as xl:
        df_all.to_excel(xl, sheet_name="All Hydrographs", index=False)
        print(f"\nSheet 'All Hydrographs' written ({df_all.shape[1]} columns)")

        for rp in RP_ORDER:
            if rp not in data:
                continue
            sheet = f"{rp} inflow"
            rp_df_inflow(rp).to_excel(xl, sheet_name=sheet, index=False)

        for rp in RP_ORDER:
            if rp not in data:
                continue
            sheet = f"{rp} outflow"
            rp_df_outflow(rp).to_excel(xl, sheet_name=sheet, index=False)

    n_rp = len([r for r in RP_ORDER if r in data])
    print(f"Written {1 + n_rp*2} sheets -> {XLSX}")


if __name__ == "__main__":
    main()
