# -*- coding: utf-8 -*-
"""Run HEC-RAS 6.6 plans unattended through the HECRASController COM interface.

Usage:  python ras_run.py p27 p28 ...      (plan codes as registered in Majlas.prj)
        python ras_run.py --list           (show plans and their titles)
Each run: open project, set the plan current, compute, wait, then read the computation messages and the HDF summary.
Writes a run register line to W2/04_data/run_register.csv.  HEC-RAS must be CLOSED before running (the controller opens
its own instance and the two would fight over the project files).
"""
import os, sys, time, csv, re, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); W2 = os.path.abspath(os.path.join(HERE, ".."))
RAS = os.environ.get("RAS_DIR") or os.path.abspath(os.path.join(W2, "..", "HEC-RAS Majlas"))   # RAS_DIR selects a parallel project copy
PRJ = os.path.join(RAS, "Majlas.prj")
REGISTER = os.path.join(W2, "04_data", "run_register.csv")
PROGID = "RAS66.HECRASController"

def plans():
    s = open(PRJ, encoding="latin-1").read()
    out = []
    for code in re.findall(r"^Plan File=(p\d+)", s, flags=re.M):
        p = os.path.join(RAS, f"Majlas.{code}"); t = open(p, encoding="latin-1").read()
        title = re.search(r"^Plan Title=(.*)$", t, flags=re.M).group(1).strip()
        geom = re.search(r"^Geom File=(.*)$", t, flags=re.M).group(1).strip(); flow = re.search(r"^Flow File=(.*)$", t, flags=re.M).group(1).strip()
        out.append((code, title, geom, flow))
    return out

def ras_running():
    import subprocess
    r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq Ras.exe"], capture_output=True, text=True)
    return "Ras.exe" in r.stdout

def set_current_plan(code):
    """Write 'Current Plan=pNN' into the project file; the controller's Plan_SetCurrent proved unreliable (it left p26 current)."""
    s = open(PRJ, encoding="latin-1", newline="").read()
    s2 = re.sub(r"^Current Plan=[^\r\n]*", f"Current Plan={code}", s, count=1, flags=re.M)   # [^\r\n] keeps the CR of a CRLF file
    open(PRJ, "w", encoding="latin-1", newline="").write(s2)

def run_plan(code, title):
    import win32com.client as w
    set_current_plan(code)
    rc = w.dynamic.Dispatch(PROGID)
    rc.ShowRas()                       # visible window: progress can be watched; harmless unattended
    rc.Project_Open(PRJ)
    # Plan_SetCurrent loads the plan into the controller; without it Compute_CurrentPlan ran a steady computation.
    # It must receive the exact plan title (a wrong title makes HEC-RAS create a new empty plan).
    ok = rc.Plan_SetCurrent(title)
    cur = os.path.basename(str(rc.CurrentPlanFile()))
    print("Plan_SetCurrent ->", ok, "| current plan file:", cur, "| geom:", os.path.basename(str(rc.CurrentGeomFile())),
          "| unsteady:", os.path.basename(str(rc.CurrentUnSteadyFile())), flush=True)
    if not cur.lower().endswith(code.lower()):
        rc.Project_Close(); rc.QuitRas(); raise RuntimeError(f"controller selected {cur}, expected {code}; aborting to avoid stray plans")
    t0 = time.time()
    # Compute_CurrentPlan(nmsg, msg, blocking=True) -> returns True on success; messages via out params (pywin32 returns tuple)
    res = rc.Compute_CurrentPlan(0, None, True)
    elapsed = time.time() - t0
    try:
        ok_flag, nmsg, msgs = res[0], res[1], res[2]
    except Exception:
        ok_flag, nmsg, msgs = res, 0, []
    rc.Project_Close(); rc.QuitRas()
    return ok_flag, elapsed, msgs

def hdf_summary(code):
    """Volume accounting and a few summary numbers from the plan HDF, if present."""
    import h5py, numpy as np
    p = os.path.join(RAS, f"Majlas.{code}.hdf")
    if not os.path.exists(p): return {"hdf": "missing"}
    out = {"hdf": os.path.basename(p), "size_MB": round(os.path.getsize(p) / 1e6, 1)}
    with h5py.File(p, "r") as f:
        try:
            va = f["Results/Unsteady/Summary/Volume Accounting"]
            for k, v in va.attrs.items(): out[f"VA {k}"] = float(v) if np.ndim(v) == 0 else v.tolist()
        except Exception as e: out["VA"] = f"n/a ({e})"
        try:
            out["max WSE (m)"] = float(f["Results/Unsteady/Output/Output Blocks/Base Output/Summary Output/2D Flow Areas/DS Protection/Maximum Water Surface"][0].max())
        except Exception: pass
        try:
            out["computation time"] = f["Results/Unsteady/Summary"].attrs.get("Computation Time Total", b"").decode() if isinstance(f["Results/Unsteady/Summary"].attrs.get("Computation Time Total", b""), bytes) else str(f["Results/Unsteady/Summary"].attrs.get("Computation Time Total"))
        except Exception: pass
    return out

def log_register(code, title, ok, elapsed, summary):
    new = not os.path.exists(REGISTER)
    with open(REGISTER, "a", newline="", encoding="utf-8") as fh:
        wr = csv.writer(fh)
        if new: wr.writerow(["datetime", "plan", "title", "ok", "elapsed_min", "summary"])
        wr.writerow([dt.datetime.now().isoformat(timespec="minutes"), code, title, ok, round(elapsed / 60, 1), str(summary)])

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args == ["--list"]:
        for c, t, g, f in plans(): print(f"{c}: {t:40s} geom {g} flow {f}")
        sys.exit(0)
    if ras_running() and not os.environ.get("RAS_DIR"): sys.exit("HEC-RAS is open. Close it and rerun.")   # a project copy may run beside other instances
    table = {c: t for c, t, _, _ in plans()}
    for code in args:
        title = table[code]; print(f"=== {code} {title} ===", flush=True)
        ok, elapsed, msgs = run_plan(code, title)
        summary = hdf_summary(code)
        print("ok:", ok, "elapsed min:", round(elapsed / 60, 1)); print("summary:", summary)
        if msgs:
            for m in list(msgs)[-15:]: print("  ", m)
        log_register(code, title, ok, elapsed, summary)
