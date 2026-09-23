# -*- coding: utf-8 -*-
"""Unattended run sequence: wait for the fill restart file, then run the listed plans one after another through
ras_run.run_plan, and post-process each one with ras_results.process. Meant to be launched as a detached process:

  powershell Start-Process python -ArgumentList 'ras_sequence.py p32 p28 p30' -WindowStyle Hidden

Log: W2/04_data/run_sequence.log (appended). Stops the sequence if a run does not finish successfully.
"""
import os, sys, time, datetime as dt, subprocess, traceback
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
W2 = os.path.abspath(os.path.join(HERE, "..")); RAS = os.environ.get("RAS_DIR") or os.path.abspath(os.path.join(W2, "..", "HEC-RAS Majlas"))   # RAS_DIR selects a parallel project copy
LOG = os.path.join(W2, "04_data", "run_sequence.log")
RESTART = os.path.join(RAS, "Majlas.p27.31DEC1999 2400.rst")

def log(msg):
    line = f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M')}  {msg}"
    with open(LOG, "a", encoding="utf-8") as fh: fh.write(line + "\n")
    print(line, flush=True)

PARALLEL = bool(os.environ.get("RAS_DIR"))   # a project copy runs beside the main folder: never wait on other folders' solvers

def ras_busy():
    if PARALLEL: return False
    r = subprocess.run(["tasklist"], capture_output=True, text=True).stdout.lower()
    return "rasunsteady.exe" in r or "ras.exe" in r

def wait_for_fill(max_min=90):
    t0 = time.time()
    while True:
        msgs = os.path.join(RAS, "Majlas.p27.computeMsgs.txt")
        done = os.path.exists(RESTART) and os.path.exists(msgs) and "Complete Process" in open(msgs, encoding="latin-1").read() and not ras_busy()
        if done:
            if "unstable" in open(msgs, encoding="latin-1").read().lower(): log("fill went unstable; sequence aborted"); return False
            log("fill finished; restart file present"); return True
        if (time.time() - t0) / 60 > max_min: log("fill not finished in time; sequence aborted"); return False
        time.sleep(30)

def main(codes):
    import ras_run, ras_results, ras_setup, h5py
    table = {c: t for c, t, _, _ in ras_run.plans()}
    if table[codes[0]].startswith("Fill"): log("first plan is a fill: not waiting for an earlier fill")
    elif not wait_for_fill(): return
    for code in codes:
        title = table[code]; log(f"START {code} {title}")
        try:
            pid = title.split()[0]
            if pid in ras_setup.TRIGGER_FROM:      # flood-day failure: breach at the time of the maximum pool of the matching no-failure run
                info = ras_setup.set_trigger_from_s3(pid, RAS)
                log(f"{code} breach trigger set from {info['from_run']}: {info['trigger_date']} {info['trigger_time']} (pool {info['max_stage_hw']:.2f} m at {info['time_h']:.2f} h)")
            while ras_busy(): time.sleep(20)
            ok, elapsed, msgs = ras_run.run_plan(code, title)
            summary = ras_run.hdf_summary(code); ras_run.log_register(code, title, ok, elapsed, summary)
            with h5py.File(os.path.join(RAS, f"Majlas.{code}.hdf"), "r") as f: sol = f["Results/Unsteady/Summary"].attrs["Solution"].decode()
            log(f"END   {code} ok={ok} {elapsed/60:.0f} min | {sol} | volume error {summary.get('VA Error Percent', '?')}")
            if "Successfully" not in sol:
                log(f"FAILED {code}: run did not finish successfully; continuing with the next plan"); continue   # unattended: skip, do not block the folder
            if title.startswith("Fill"): log(f"{code} is a fill run: restart file written, no products"); continue
            s = ras_results.process(code); log(f"PRODUCTS {code}: peak {s.get('peak_total_flow_m3s')} m3/s at {s.get('peak_time_h')} h; area {s.get('inundated_area_km2_gt0.3m')} km2")
        except Exception as e:
            log(f"ERROR {code}: {e}\n{traceback.format_exc()}"); continue      # a plan whose S3 twin failed lands here (no trigger) and is skipped
    log("sequence complete")

if __name__ == "__main__":
    main(sys.argv[1:])
