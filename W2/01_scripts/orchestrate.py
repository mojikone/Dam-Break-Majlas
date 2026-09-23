# -*- coding: utf-8 -*-
"""Campaign dispatcher (2026-09-22, user decisions at 13:50): base runs first, then the full sensitivity set; the S1N-versus-S1D
comparison decides whether the no-dikes flood-day runs (S3N, S2N) are run at all.

Rules
  * A folder gets one plan at a time (one `ras_sequence.py <plan>` per launch), so priorities are re-evaluated after every run.
  * Base plans (S3D, S2D, S3N, S2N) before any sensitivity plan; a sensitivity plan starts only when every base plan has products
    or has been skipped by the dikes decision.
  * S2D needs the S3D products (trigger time), S2N needs S3N, S2D-F10000 needs S3D-F10000, the S2D-* sensitivity runs need S3D.
  * Dikes decision: once S1N has products, compare with S1D on flooded area, people at risk and median arrival time; if every
    difference is below 5 % the dikes are immaterial for a dam break and S3N, S2N are skipped (decision written to
    04_data/dikes_decision.json and logged); otherwise they are kept.
  * Sequences that were already running when the dispatcher started keep their lists (main: p32 p30 p34 p36; copy 2: p37 p38 p41);
    the dispatcher only fills folders that are idle.
  * Every folder gets the rain-aware restart pairs (p27 dikes, p43 no dikes) and their flow files before its first dispatch, so any
    folder can run any plan.

Detached:  powershell Start-Process python -ArgumentList 'orchestrate.py' -WindowStyle Hidden
Log lines go to 04_data/run_sequence.log with the prefix 'orch:'.
"""
import os, sys, time, json, shutil, subprocess, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); W2 = os.path.abspath(os.path.join(HERE, ".."))
BASE_DIR = os.path.abspath(os.path.join(W2, ".."))
FOLDERS = {"main": os.path.join(BASE_DIR, "HEC-RAS Majlas"), "run2": os.path.join(BASE_DIR, "HEC-RAS Majlas_run2"), "run3": os.path.join(BASE_DIR, "HEC-RAS Majlas_run3")}
RES = os.path.join(W2, "04_data", "results"); LOG = os.path.join(W2, "04_data", "run_sequence.log")
DECISION = os.path.join(W2, "04_data", "dikes_decision.json")
PY = sys.executable

BASE_PLANS = ["p32", "p30", "p33", "p31"]                       # S3D, S2D, S3N, S2N
SENS_PLANS = ["p48", "p42", "p35", "p39", "p40", "p34", "p36", "p37", "p38", "p41"]   # order of dispatch among sensitivity runs
NEEDS = {"p30": "p32", "p31": "p33", "p42": "p48", "p34": "p32", "p35": "p32", "p36": "p32", "p39": "p32", "p40": "p32"}
ALREADY_LISTED = {"main": ["p30"]}   # 19:15: S2D runs in the main folder (launched by the previous dispatcher instance). NOTE: Ras.exe instances are children of svchost (DCOM), never of the python sequence, so a "kill by parent" test cannot single one out.
NAMES = {"p28": "S1D", "p29": "S1N", "p30": "S2D", "p31": "S2N", "p32": "S3D", "p33": "S3N", "p34": "S2D-W51", "p35": "S2D-W119", "p36": "S2D-W153",
         "p37": "S1D-W51", "p38": "S1D-W153", "p39": "S2D-T18m", "p40": "S2D-T3m", "p41": "S1D-C1.44", "p42": "S2D-F10000", "p48": "S3D-F10000"}

def log(msg):
    line = f"{dt.datetime.now().strftime('%Y-%m-%d %H:%M')}  orch: {msg}"
    with open(LOG, "a", encoding="utf-8") as fh: fh.write(line + "\n")
    print(line, flush=True)

def has_products(code): return os.path.exists(os.path.join(RES, code, "summary.json"))

def processes():
    r = subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-CimInstance Win32_Process | Where-Object { $_.Name -in 'python.exe','RasUnsteady.exe','Ras.exe' } | ForEach-Object { $_.ProcessId.ToString() + '|' + $_.Name + '|' + ($_.CommandLine -replace '[\\r\\n]+', ' ') }"],
                       capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l.count("|") >= 2]      # a multi-line command line (python -c "...") would otherwise break the split

def folder_busy(name, procs):
    """a sequence or a solver bound to this folder"""
    d = FOLDERS[name]; leaf = os.path.basename(d) + "\\"
    for p in procs:
        pid, exe, cmd = p.split("|", 2)
        if exe == "RasUnsteady.exe" and leaf in cmd: return True
        if exe == "python.exe" and "ras_sequence.py" in cmd and launched.get(name) == int(pid): return True
    return False

def sequence_alive(name, procs):
    """the pre-existing sequence of a folder (identified by its plan list) still running"""
    lst = " ".join(ALREADY_LISTED.get(name, []))
    return any("ras_sequence.py" in p and lst and lst in p for p in procs) if lst else False

def ensure_files(name):
    d = FOLDERS[name]; main = FOLDERS["main"]; run3 = FOLDERS["run3"]
    pairs = [(main, "Majlas.p27.31DEC1999 2400.rst"), (main, "Majlas.u26"), (main, "Majlas.u27"), (main, "Majlas.p27.computeMsgs.txt"),
             (run3, "Majlas.p43.31DEC1999 2400.rst"), (main, "Majlas.u30"), (main, "Majlas.u31"), (main, "Majlas.p43")]
    for src_dir, f in pairs:
        s, t = os.path.join(src_dir, f), os.path.join(d, f)
        if os.path.exists(s) and (not os.path.exists(t) or os.path.getmtime(s) > os.path.getmtime(t) + 1) and os.path.abspath(s) != os.path.abspath(t):
            shutil.copy2(s, t)
    # a copy's project file must list p43 and u30/u31 if they were added after the copy was made
    prj = os.path.join(d, "Majlas.prj"); txt = open(prj, "rb").read().decode("latin-1")
    changed = False
    for key, code in (("Unsteady File", "u30"), ("Unsteady File", "u31"), ("Plan File", "p43")):
        if f"{key}={code}" not in txt and os.path.exists(os.path.join(d, f"Majlas.{code}")):
            lines = txt.split("\r\n"); last = max(i for i, l in enumerate(lines) if l.startswith(key + "=")); lines.insert(last + 1, f"{key}={code}"); txt = "\r\n".join(lines); changed = True
    if changed: open(prj, "wb").write(txt.encode("latin-1"))

def decide_dikes():
    if os.path.exists(DECISION): return json.load(open(DECISION))["keep_no_dikes"]
    if not (has_products("p28") and has_products("p29")): return None
    def load(code):
        s = json.load(open(os.path.join(RES, code, "summary.json")))
        c = os.path.join(RES, code, "consequences.json"); s.update(json.load(open(c)) if os.path.exists(c) else {})
        return s
    a, b = load("p28"), load("p29")
    if "par_total" not in b: return None            # consequences not written yet
    diffs = {}
    for k in ("inundated_area_km2_gt0.3m", "par_total", "arrival_h_median", "peak_total_flow_m3s"):
        x, y = a.get(k), b.get(k)
        diffs[k] = None if not x else abs((y or 0) - x) / x
    material = any(v is not None and v > 0.05 for k, v in diffs.items() if k != "peak_total_flow_m3s")
    dec = {"keep_no_dikes": material, "threshold": 0.05, "S1D": {k: a.get(k) for k in diffs}, "S1N": {k: b.get(k) for k in diffs},
           "relative_differences": diffs, "decided": dt.datetime.now().isoformat(timespec="minutes")}
    json.dump(dec, open(DECISION, "w"), indent=2)
    log("dikes decision: " + ("KEEP S3N and S2N" if material else "SKIP S3N and S2N") + " | " + ", ".join(f"{k} {v:.1%}" for k, v in diffs.items() if v is not None))
    return material

launched = {}
FOLDER_OF = {"p32": "main", "p37": "run2", "p38": "run2", "p41": "run2", "p29": "run3", "p28": "run2"}
STALE = set()    # every earlier plan has been reprocessed with the current ras_results (18:55); the dispatcher's own launches use the current code
posted = set()

def post(code):
    """Products consistency: re-run ras_results for plans post-processed by the older sequences (reservoir mask, interpolated velocity),
    then the consequence overlay for every plan. Runs once per plan, when its summary.json appears."""
    name = FOLDER_OF.get(code); env = dict(os.environ, RAS_DIR=FOLDERS[name], HDF5_USE_FILE_LOCKING="FALSE")
    if code in STALE:
        r = subprocess.run([PY, "-c", f"import ras_results as R; R.process('{code}')"], cwd=HERE, env=env, capture_output=True, text=True)
        log(f"reprocessed {code} with current ras_results" + ("" if r.returncode == 0 else f" FAILED: {r.stderr[-300:]}"))
    r = subprocess.run([PY, os.path.join(HERE, "ras_analysis.py"), code], cwd=HERE, env=env, capture_output=True, text=True)
    log(f"consequences {code}" + ("" if r.returncode == 0 else f" FAILED: {r.stderr[-300:]}"))
    posted.add(code)

def launch(name, code):
    env = dict(os.environ, RAS_DIR=FOLDERS[name])
    out = open(os.path.join(W2, "04_data", f"run_sequence_{name}_{code}.stdout.txt"), "w")
    p = subprocess.Popen([PY, os.path.join(HERE, "ras_sequence.py"), code], cwd=HERE, env=env, stdout=out, stderr=subprocess.STDOUT,
                         creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS)
    launched[name] = p.pid; FOLDER_OF[code] = name; log(f"launched {code} {NAMES.get(code, '')} in {name} (pid {p.pid})")

def main():
    log("dispatcher started: base first, then sensitivity; S1N comparison decides S3N/S2N")
    for name in FOLDERS: ensure_files(name)
    started = set()
    for lst in ALREADY_LISTED.values(): started.update(lst)
    while True:
        for code in list(NAMES):
            if code in posted or not has_products(code) or code not in FOLDER_OF: continue
            if code in STALE or not os.path.exists(os.path.join(RES, code, "consequences.json")): post(code)
        procs = processes(); keep_n = decide_dikes()
        base = [c for c in BASE_PLANS if not (c in ("p33", "p31") and keep_n is False)]
        base_done = all(has_products(c) for c in base) and keep_n is not None
        pending_base = [c for c in base if not has_products(c) and c not in started]
        pending_sens = [c for c in SENS_PLANS if not has_products(c) and c not in started]
        if not pending_base and not pending_sens and all(not folder_busy(n, procs) and not sequence_alive(n, procs) for n in FOLDERS):
            log("campaign complete"); return
        for name in FOLDERS:
            if folder_busy(name, procs) or sequence_alive(name, procs): continue
            if name == "run3" and not os.path.exists(os.path.join(W2, "04_data", "run3_stopped_before_p31.txt")): continue   # the old copy-3 sequence owns the folder until its stopper fires
            pending_base = [c for c in pending_base if c not in started]; pending_sens = [c for c in pending_sens if c not in started]   # refreshed per folder: a plan launched in one folder must not be launched again in the next (happened 18:51)
            pool = pending_base + pending_sens      # 19:15, user: sensitivity runs fill idle folders while S2D runs (base still first in order)
            for code in pool:
                need = NEEDS.get(code)
                if code in ("p33", "p31") and keep_n is None: continue          # wait for the S1N comparison
                if need and not has_products(need): continue
                ensure_files(name); launch(name, code); started.add(code); break
            procs = processes()
        time.sleep(60)

if __name__ == "__main__":
    main()
