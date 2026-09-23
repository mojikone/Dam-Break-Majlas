# -*- coding: utf-8 -*-
"""Build the HEC-RAS unsteady-flow files and plans for the dam break runs, from the user's model as built.

Never touches the geometry files. Reads:
  Majlas.u24 (PMP)      - hydrographs on BC lines 'Majlas Dam', 'J11', 'Jsouth', rain on the 2D area, outflow lines
  Majlas.u25 (10000Break)
  Majlas.p26 (PMPDam)   - plan template incl. the breach block the user saved
Writes new files only (u26.., p27..) and registers them in Majlas.prj.  A backup of the .prj is kept.

Run matrix (W1 run sheet): Fill (restart), S1-D/N sunny day, S2-D/N flood day PMF, S3-D/N PMF no failure, plus sensitivity.
"""
import os, re, shutil, sys, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__)); W2 = os.path.abspath(os.path.join(HERE, ".."))
RAS = os.path.abspath(os.path.join(W2, "..", "HEC-RAS Majlas"))
PRJ = os.path.join(RAS, "Majlas.prj")
sys.path.insert(0, HERE)
import data_facts as F

GEOM = {"D": "g02", "N": "g03"}            # with dikes / without dikes (user's geometries, unchanged)
U_PMP, U_10000, P_TEMPLATE = "u24", "u25", "p26"
BC_2D = "DS Protection"
SEA_LINES = ("Outflow Sea", "Outflow 2")
INFLOW_LINES = ("Majlas Dam", "J11", "Jsouth")
FILL_Q, FILL_HOURS, FILL_RAMP = 2500.0, 10.3, 1.0   # m3/s, h, h : ramp 1 h up, hold, ramp 1 h down = 4.5 + 92.7 + 4.5 = 101.7 Mm3 -> pool about 84.4,
                                                     # kept just below the ogee so that no water spills during the fill (the SWE fill went unstable the moment
                                                     # a trickle started down the dry chute; 102.6 Mm3 reached 84.52).
                                                     # just under the 103.1 Mm3 the 2D reservoir holds at 84.5 (measured in the first fill), so nothing
                                                     # spills and the wadi stays dry. (6000 m3/s from a dry start went unstable at 4.7 h; 12 h at 2500
                                                     # spilled 14 Mm3 and left ponds up to 2.9 m downstream.)
WINDOW = {"fill": ("30dec1999,0000", "01jan2000,0000"),    # 48 h fill + settle; restart written at the end
          "sunny": ("01jan2000,0000", "01jan2000,1400"),   # 2 h warm-up on restart, breach at 0200, 12 h after
          "flood": ("01jan2000,0000", "03jan2000,1200")}   # 60 h
BREACH_AT = "01jan2000,0200"

# ------------------------------------------------------------------ helpers
def read(p):  return open(p, encoding="latin-1", newline="").read()
def write(p, s): open(p, "w", encoding="latin-1", newline="").write(s)
def nl(s): return "\r\n" if "\r\n" in s else "\n"

def fixed8(vals, per_line=10):
    """HEC-RAS fixed-width table: 8 characters per value, 10 per line."""
    out, line = [], ""
    for i, v in enumerate(vals):
        txt = f"{v:8.6g}" if abs(v) < 1e7 else f"{v:8.3e}"
        if len(txt) > 8: txt = f"{v:8.3g}"
        line += txt[-8:].rjust(8)
        if (i + 1) % per_line == 0: out.append(line); line = ""
    if line: out.append(line)
    return out

def parse_blocks(u_text):
    """Split an unsteady file into header lines and 'Boundary Location=' blocks keyed by BC line name."""
    n = nl(u_text); lines = u_text.split(n)
    head, blocks, cur, key = [], {}, None, None
    for ln in lines:
        if ln.startswith("Boundary Location="):
            parts = [p.strip() for p in ln[len("Boundary Location="):].split(",")]
            area, name = parts[5], parts[7]
            key = (area, name); cur = blocks.setdefault(key, []); cur.append(ln)
        elif cur is not None: cur.append(ln)
        else: head.append(ln)
    return head, blocks, n

def block_values(block, keyword):
    """Return (n, values) of the table that follows 'keyword= n'."""
    for i, ln in enumerate(block):
        if ln.startswith(keyword + "="):
            n = int(ln.split("=")[1]); vals = []
            j = i + 1
            while len(vals) < n and j < len(block):
                s = block[j]; vals += [float(s[k:k + 8]) for k in range(0, len(s), 8) if s[k:k + 8].strip()]; j += 1
            return n, vals[:n]
    return None, None

def set_table(block, keyword, vals):
    """Replace the table after 'keyword=' with vals (fixed width)."""
    out, i = [], 0
    while i < len(block):
        ln = block[i]
        if ln.startswith(keyword + "="):
            n_old = int(ln.split("=")[1]); out.append(f"{keyword}= {len(vals)} "); out += fixed8(vals)
            i += 1; taken = 0
            while taken < n_old and i < len(block):
                taken += len([1 for k in range(0, len(block[i]), 8) if block[i][k:k + 8].strip()]); i += 1
            continue
        out.append(ln); i += 1
    return out

def flow_block(name, vals, interval="5MIN", slope=0.002):
    return [f"Boundary Location=                ,                ,        ,        ,                ,{BC_2D:<16},                ,{name:<32},                                ",
            f"Interval={interval}", f"Flow Hydrograph= {len(vals)} "] + fixed8(vals) + \
           ["Stage Hydrograph TW Check=0", f"Flow Hydrograph Slope= {slope} ", "DSS Path=", "Use DSS=False",
            "Use Fixed Start Time=False", "Fixed Start Date/Time=,", "Is Critical Boundary=False", "Critical Boundary Flow="]

def pad(vals, step_min, hours):
    need = int(hours * 60 / step_min) + 1
    return list(vals) + [0.0] * max(0, need - len(vals))

# ------------------------------------------------------------------ unsteady files
def zero_rain_block(rain_block, hours):
    """The user's rain block with every value set to zero and the table padded to `hours` (10 min steps)."""
    _, vals = block_values(rain_block, "Precipitation Hydrograph")
    return set_table(rain_block, "Precipitation Hydrograph", [0.0] * (int(hours * 6) + 1))

def build_unsteady(src_u, title, mode, restart_name=None, out_u=None, hours=60, rain_zero=False):
    """mode: 'fill' | 'sunny' | 'flood'. Keeps the user's blocks for the 2D area only (drops leftovers of other areas).
    rain_zero=True adds the rain block with zero values (fill and sunny runs): a restart file written by a plan without a rain block
    stalls the restart-based flood runs at start-up (2026-09-22 diagnosis, HEC-RAS 6.6), so every plan in a restart chain carries the block."""
    head, blocks, n = parse_blocks(read(os.path.join(RAS, f"Majlas.{src_u}")))
    keep = []
    # header
    hdr = [f"Flow Title={title}", "Program Version=6.60"]
    hdr.append(f"Use Restart=-1" if restart_name else "Use Restart= 0 ")
    if restart_name: hdr.append(f"Restart Filename={restart_name}")
    # outflow lines as the user set them (normal depth)
    for line in SEA_LINES:
        b = blocks.get((BC_2D, line));  keep += b if b else []
    if mode == "fill":
        steps = int(hours * 12) + 1
        def fq(h):
            if h < FILL_RAMP: return FILL_Q * h / FILL_RAMP
            if h < FILL_RAMP + FILL_HOURS: return FILL_Q
            if h < 2 * FILL_RAMP + FILL_HOURS: return FILL_Q * (2 * FILL_RAMP + FILL_HOURS - h) / FILL_RAMP
            return 0.0
        q = [fq(i * 5 / 60.0) for i in range(steps)]
        keep += flow_block("Majlas Dam", q, slope=0.002)
        keep += flow_block("J11", [0.0] * steps, slope=0.008) + flow_block("Jsouth", [0.0] * steps, slope=0.006)
    elif mode == "sunny":
        steps = int(hours * 12) + 1
        for line, sl in (("Majlas Dam", 0.002), ("J11", 0.008), ("Jsouth", 0.006)):
            keep += flow_block(line, [0.0] * steps, slope=sl)
    else:   # flood: the user's hydrographs and rain, padded with zeros to the window
        for line in INFLOW_LINES:
            b = blocks[(BC_2D, line)]; _, vals = block_values(b, "Flow Hydrograph")
            keep += set_table(b, "Flow Hydrograph", pad(vals, 5, hours))
        rain = blocks.get((BC_2D, ""))
        if rain:
            _, vals = block_values(rain, "Precipitation Hydrograph"); keep += set_table(rain, "Precipitation Hydrograph", pad(vals, 10, hours))
    if rain_zero and mode != "flood":
        keep += zero_rain_block(blocks[(BC_2D, "")], hours)
    txt = n.join(hdr + keep) + n
    write(os.path.join(RAS, f"Majlas.{out_u}"), txt)
    return out_u

# ------------------------------------------------------------------ plans
def build_plan(out_p, title, short, geom, flow, window, breach, cores=16, equation=1, write_ic_end=False,
               # equation 1 = SWE-ELM (the user's original setting, ran the PMF onset without trouble); 2 = SWE-EM stalled on the restart
               # and went unstable at the first spill on this mesh. Documented as a deviation from the methodology (which named SWE-EM).
               width=None, center=None, tform=None, coef=None, trigger_ws=None, trigger_time=None, bottom=None):
    s = read(os.path.join(RAS, f"Majlas.{P_TEMPLATE}")); n = nl(s)
    s = s.replace("\r\n", "\n")          # work on LF text; the template's line ending is restored on write
    s = re.sub(r"^Plan Title=[^\r\n]*$", f"Plan Title={title}", s, count=1, flags=re.M)
    s = re.sub(r"^Short Identifier=[^\r\n]*$", f"Short Identifier={short:<64}", s, count=1, flags=re.M)
    s = re.sub(r"^Simulation Date=[^\r\n]*$", f"Simulation Date={window[0]},{window[1]}", s, count=1, flags=re.M)
    s = re.sub(r"^Geom File=[^\r\n]*$", f"Geom File={geom}", s, count=1, flags=re.M)
    s = re.sub(r"^Flow File=[^\r\n]*$", f"Flow File={flow}", s, count=1, flags=re.M)
    s = re.sub(r"^Output Interval=[^\r\n]*$", "Output Interval=1MIN", s, count=1, flags=re.M)
    s = re.sub(r"^Instantaneous Interval=[^\r\n]*$", "Instantaneous Interval=1MIN", s, count=1, flags=re.M)
    s = re.sub(r"^Mapping Interval=[^\r\n]*$", "Mapping Interval=5MIN", s, count=1, flags=re.M)
    s = re.sub(r"^UNET D2 Cores=[^\r\n]*$", f"UNET D2 Cores={cores}", s, flags=re.M)
    s = re.sub(r"^UNET D2 Cores= [^\r\n]*$", f"UNET D2 Cores= {cores} ", s, flags=re.M)
    s = re.sub(r"^UNET D2 Equation= [^\r\n]*$", f"UNET D2 Equation= {equation} ", s, flags=re.M)
    s = re.sub(r"^Write IC File at Sim End=[^\r\n]*$", f"Write IC File at Sim End={-1 if write_ic_end else 0}", s, count=1, flags=re.M)
    s = re.sub(r"^Write IC File= [^\r\n]*$", f"Write IC File= {-1 if write_ic_end else 0} ", s, count=1, flags=re.M)
    # breach block
    m = re.search(r"^Breach Loc=([^\r\n]*)$", s, flags=re.M)
    loc = m.group(1); parts = loc.split(",")
    parts[3] = "True" if breach else "False"
    s = s.replace(m.group(0), "Breach Loc=" + ",".join(parts))
    g = re.search(r"^Breach Geom=([^\r\n]*)$", s, flags=re.M); gv = g.group(1).split(",")
    if center is not None: gv[0] = f"{center:g}"
    if width is not None: gv[1] = f"{width:g}"
    if bottom is not None: gv[2] = f"{bottom:g}"
    if tform is not None: gv[8] = f"{tform:g}"
    if coef is not None: gv[9] = f"{coef:g}"
    s = s.replace(g.group(0), "Breach Geom=" + ",".join(gv))
    st = re.search(r"^Breach Start=([^\r\n]*)$", s, flags=re.M); sv = st.group(1).split(",")
    # Breach Start fields: F1 True = trigger at WS elevation (F2); F5 True = WS elevation + duration; both False = set time (F3 date, F4 time)
    if trigger_ws is not None: sv[0], sv[1], sv[2], sv[3], sv[4] = "True", f"{trigger_ws:g}", "", "", "False"
    if trigger_time is not None:
        d_, t_ = trigger_time.split(","); sv[0], sv[1], sv[2], sv[3], sv[4] = "False", "", d_.upper(), t_, "False"
    s = s.replace(st.group(0), "Breach Start=" + ",".join(sv))
    write(os.path.join(RAS, f"Majlas.{out_p}"), s.replace("\n", n))
    return out_p

def register(kind, code):
    """Add 'Unsteady File=uNN' / 'Plan File=pNN' to the project file if missing."""
    s = read(PRJ); n = nl(s); key = {"u": "Unsteady File", "p": "Plan File"}[kind]
    if f"{key}={code}" in s: return
    lines = s.split(n); last = max(i for i, l in enumerate(lines) if l.startswith(key + "="))
    lines.insert(last + 1, f"{key}={code}"); write(PRJ, n.join(lines))

def next_code(kind):
    s = read(PRJ); key = {"u": "Unsteady File", "p": "Plan File"}[kind]
    nums = [int(m) for m in re.findall(rf"^{key}={kind}(\d+)", s, flags=re.M)]
    return f"{kind}{max(nums) + 1:02d}"

# ------------------------------------------------------------------ the run matrix
FIXED_U = {"u_fill": "u26", "u_sun": "u27", "u_pmp": "u28", "u_10k": "u29",          # codes registered on 2026-09-22
           "u_sun_n": "u30", "u_pmp_n": "u31"}   # no-dikes variants: same flows, restart from the no-dikes fill (the g03 mesh differs from g02,
                                                   # 35,878 vs 36,769 cells, so a restart file written on one geometry cannot start the other)
FIXED_P = {"Fill": "p27", "FillN": "p43", "S1D": "p28", "S1N": "p29", "S2D": "p30", "S2N": "p31", "S3D": "p32", "S3N": "p33",
           "S2D-W51": "p34", "S2D-W119": "p35", "S2D-W153": "p36", "S1D-W51": "p37", "S1D-W153": "p38", "S2D-T18m": "p39", "S2D-T3m": "p40",
           "S1D-C1.44": "p41", "S2D-F10000": "p42"}
# Naming (2026-09-22, user request): S1 = sunny day failure, S2 = flood day PMF failure, S3 = PMF no failure; D = dikes, N = no dikes;
# suffix = the one thing changed from the base run: W<width m>, T<formation time>, C<weir coefficient>, F<flood return period>.

RESTART_N = "Majlas.p43.31DEC1999 2400.rst"
FIXED_P["S3D-F10000"] = "p48"          # 10,000-yr flood, no failure, dikes: gives the routed level and the trigger time for S2D-F10000
WINDOW["flood_sens"] = ("01jan2000,0000", "02jan2000,1200")   # 36 h for the sensitivity runs: breach near the PMF peak (hour 15-20), 16 h after
# Flood-day failure = failure at the maximum pool (FERC/USACE convention for a concrete gravity dam: the critical load is the peak
# reservoir level, not overtopping). The user's 2026-09-22 question exposed the flaw in a fixed 96.7 m trigger: the routed PMF may
# peak below the parapet, and the breach would never start. Each S2 plan therefore takes its trigger from the matching no-failure run.
TRIGGER_FROM = {"S2D": "S3D", "S2N": "S3N", "S2D-W51": "S3D", "S2D-W119": "S3D", "S2D-W153": "S3D", "S2D-T18m": "S3D", "S2D-T3m": "S3D",
                "S2D-F10000": "S3D-F10000"}

def set_trigger_from_s3(pid, ras_dir, results_root=None):
    """Read the no-failure run's connection.csv (W2/04_data/results/<s3 code>/), take the time of the maximum headwater stage and write it
    as a set-time breach trigger into the plan file of `pid` in `ras_dir`. Returns a dict with the trigger; also saved as trigger.json."""
    import csv, json, datetime as dt
    s3 = TRIGGER_FROM[pid]; code_s3, code = FIXED_P[s3], FIXED_P[pid]
    rdir = os.path.join(results_root or os.path.join(W2, "04_data", "results"), code_s3)
    rows = list(csv.DictReader(open(os.path.join(rdir, "connection.csv"))))
    best = max(rows, key=lambda r: float(r["stage_hw"]))
    p = os.path.join(ras_dir, f"Majlas.{code}"); s = read(p); n = nl(s); s = s.replace("\r\n", "\n")
    m = re.search(r"^Simulation Date=([^,]+),(\d{4})", s, flags=re.M)
    t0 = dt.datetime.strptime(m.group(1).strip().lower() + m.group(2), "%d%b%Y%H%M")
    t = (t0 + dt.timedelta(hours=float(best["time_h"]))).replace(second=0, microsecond=0)
    date_s, time_s = t.strftime("%d%b%Y").upper(), t.strftime("%H%M")
    st = re.search(r"^Breach Start=([^\n]*)$", s, flags=re.M); sv = st.group(1).split(",")
    sv[0], sv[1], sv[2], sv[3], sv[4] = "False", "", date_s, time_s, "False"
    s = s.replace(st.group(0), "Breach Start=" + ",".join(sv)); write(p, s.replace("\n", n))
    info = {"plan": code, "scenario": pid, "from_run": code_s3, "trigger_date": date_s, "trigger_time": time_s, "time_h": float(best["time_h"]),
            "max_stage_hw": float(best["stage_hw"]), "s3_date_column": best["date"]}
    out = os.path.join(results_root or os.path.join(W2, "04_data", "results"), code); os.makedirs(out, exist_ok=True)
    json.dump(info, open(os.path.join(out, "trigger.json"), "w"), indent=2)
    return info

def build_all(restart_name="Majlas.p27.31DEC1999 2400.rst", rebuild=False, only=None, flows=True):     # HEC-RAS names the IC file <project>.<plan>.<DDMMMYYYY HHMM>.rst, with 2400 for midnight
    """rebuild=True rewrites the already-registered files in place (same codes) without touching the project file.
    only = set of plan ids to (re)build; flows=False leaves the unsteady files alone."""
    made = {}
    if rebuild and not flows:
        u_fill, u_sun, u_pmp, u_10k = FIXED_U["u_fill"], FIXED_U["u_sun"], FIXED_U["u_pmp"], FIXED_U["u_10k"]
    elif rebuild:
        u_fill, u_sun, u_pmp, u_10k = FIXED_U["u_fill"], FIXED_U["u_sun"], FIXED_U["u_pmp"], FIXED_U["u_10k"]
        build_unsteady(U_PMP, "DB Fill reservoir", "fill", out_u=u_fill, hours=48, rain_zero=True)
        build_unsteady(U_PMP, "DB Sunny day (restart)", "sunny", restart_name, out_u=u_sun, hours=14, rain_zero=True)
        build_unsteady(U_PMP, "DB PMF (restart)", "flood", restart_name, out_u=u_pmp, hours=60)
        build_unsteady(U_10000, "DB 10000yr (restart)", "flood", restart_name, out_u=u_10k, hours=60)
        build_unsteady(U_PMP, "DB Sunny day, no dikes (restart)", "sunny", RESTART_N, out_u=FIXED_U["u_sun_n"], hours=14, rain_zero=True)
        build_unsteady(U_PMP, "DB PMF, no dikes (restart)", "flood", RESTART_N, out_u=FIXED_U["u_pmp_n"], hours=60)
    else:
        shutil.copy(PRJ, PRJ + ".bak_before_dambreak_plans")
        u_fill = build_unsteady(U_PMP, "DB Fill reservoir", "fill", out_u=next_code("u"), hours=48); register("u", u_fill)
        u_sun = build_unsteady(U_PMP, "DB Sunny day (restart)", "sunny", restart_name, out_u=next_code("u"), hours=14); register("u", u_sun)
        u_pmp = build_unsteady(U_PMP, "DB PMF (restart)", "flood", restart_name, out_u=next_code("u"), hours=60); register("u", u_pmp)
        u_10k = build_unsteady(U_10000, "DB 10000yr (restart)", "flood", restart_name, out_u=next_code("u"), hours=60); register("u", u_10k)
    made.update(u_fill=u_fill, u_sun=u_sun, u_pmp=u_pmp, u_10k=u_10k)
    base_w, low_w, mid_w, up_w = 85.0, 51.0, 119.0, 153.0          # whole 17 m monoliths: 5, 3, 7, 9 blocks
    plans = [
        # code, title, geom, flow, window, breach, kwargs
        ("Fill", "Fill reservoir to 84.5 m (restart)", "D", u_fill, WINDOW["fill"], False, dict(write_ic_end=True, equation=1)),   # same solver as the runs
        ("S1D", "S1D sunny day failure, dikes", "D", u_sun, WINDOW["sunny"], True, dict(trigger_time=BREACH_AT)),
        ("FillN", "FillN fill reservoir to 84.5 m, no dikes (restart)", "N", u_fill, WINDOW["fill"], False, dict(write_ic_end=True, equation=1)),
        ("S1N", "S1N sunny day failure, no dikes", "N", FIXED_U["u_sun_n"], WINDOW["sunny"], True, dict(trigger_time=BREACH_AT)),
        ("S2D", "S2D flood day PMF failure, dikes", "D", u_pmp, WINDOW["flood"], True, dict(trigger_ws=F.PMF_LEVEL)),
        ("S2N", "S2N flood day PMF failure, no dikes", "N", FIXED_U["u_pmp_n"], WINDOW["flood"], True, dict(trigger_ws=F.PMF_LEVEL)),
        ("S3D", "S3D PMF no failure, dikes", "D", u_pmp, WINDOW["flood"], False, {}),
        ("S3N", "S3N PMF no failure, no dikes", "N", FIXED_U["u_pmp_n"], WINDOW["flood"], False, {}),
        # S2 triggers below are placeholders (WS 96.7); ras_sequence replaces them with the set time of the S3 maximum pool before the run.
        ("S2D-W51", "S2D-W51 flood day, breach width 51 m", "D", u_pmp, WINDOW["flood_sens"], True, dict(trigger_ws=F.PMF_LEVEL, width=low_w)),
        ("S2D-W119", "S2D-W119 flood day, breach width 119 m", "D", u_pmp, WINDOW["flood_sens"], True, dict(trigger_ws=F.PMF_LEVEL, width=mid_w)),
        ("S2D-W153", "S2D-W153 flood day, breach width 153 m", "D", u_pmp, WINDOW["flood_sens"], True, dict(trigger_ws=F.PMF_LEVEL, width=up_w)),
        ("S1D-W51", "S1D-W51 sunny day, breach width 51 m", "D", u_sun, WINDOW["sunny"], True, dict(trigger_time=BREACH_AT, width=low_w)),
        ("S1D-W153", "S1D-W153 sunny day, breach width 153 m", "D", u_sun, WINDOW["sunny"], True, dict(trigger_time=BREACH_AT, width=up_w)),
        ("S2D-T18m", "S2D-T18m flood day, breach time 18 min", "D", u_pmp, WINDOW["flood_sens"], True, dict(trigger_ws=F.PMF_LEVEL, tform=0.3)),
        ("S2D-T3m", "S2D-T3m flood day, breach time 3 min", "D", u_pmp, WINDOW["flood_sens"], True, dict(trigger_ws=F.PMF_LEVEL, tform=0.05)),
        ("S1D-C1.44", "S1D-C1.44 sunny day, breach coefficient 1.44", "D", u_sun, WINDOW["sunny"], True, dict(trigger_time=BREACH_AT, coef=1.44)),
        ("S2D-F10000", "S2D-F10000 flood day, 10000-yr flood", "D", u_10k, WINDOW["flood_sens"], True, dict(trigger_ws=F.PMF_LEVEL)),
        ("S3D-F10000", "S3D-F10000 10000-yr flood no failure, dikes", "D", u_10k, WINDOW["flood_sens"], False, {}),
    ]
    codes = {}
    only = set(only) if only else None
    for pid, title, gk, flow, window, breach, kw in plans:
        if only is not None and pid not in only: continue
        code = FIXED_P[pid] if rebuild else next_code("p")
        build_plan(code, title, pid, GEOM[gk], flow, window, breach, **kw)
        if not rebuild: register("p", code)
        codes[pid] = code
        print(f"{pid:6s} -> {code}  geom {GEOM[gk]} flow {flow} breach {breach} {kw}")
    made["plans"] = codes
    return made

def build_nodikes():
    """Added 2026-09-22 after S1N refused the dikes restart: no-dikes fill plan p43 (g03 + u26), flows u30/u31 restarting from it,
    and plans S1N/S2N/S3N repointed to u30/u31. Registers u30, u31, p43 in the project file. Safe while other plans compute."""
    build_unsteady(U_PMP, "DB Sunny day, no dikes (restart)", "sunny", RESTART_N, out_u=FIXED_U["u_sun_n"], hours=14); register("u", FIXED_U["u_sun_n"])
    build_unsteady(U_PMP, "DB PMF, no dikes (restart)", "flood", RESTART_N, out_u=FIXED_U["u_pmp_n"], hours=60); register("u", FIXED_U["u_pmp_n"])
    build_plan(FIXED_P["FillN"], "FillN fill reservoir to 84.5 m, no dikes (restart)", "FillN", GEOM["N"], FIXED_U["u_fill"], WINDOW["fill"], False,
               write_ic_end=True, equation=1); register("p", FIXED_P["FillN"])
    for pid, u in (("S1N", "u_sun_n"), ("S2N", "u_pmp_n"), ("S3N", "u_pmp_n")):
        p = os.path.join(RAS, f"Majlas.{FIXED_P[pid]}"); t = read(p)
        t2 = re.sub(r"^Flow File=[^\r\n]*", f"Flow File={FIXED_U[u]}", t, count=1, flags=re.M); write(p, t2)
        print(pid, FIXED_P[pid], "-> flow", FIXED_U[u])

SENS = ["S2D-W51", "S2D-W119", "S2D-W153", "S2D-T18m", "S2D-T3m", "S2D-F10000", "S3D-F10000"]
FLOOD_FAMILY = ["S3D", "S2D"] + SENS          # runs that share the flood-day numerics

def set_courant(pid, ras_dir, cmin=1.0, cmax=3.0):
    """Adaptive time-step limits of one plan file. Flood-day runs sit at the 0.335 s floor for 30+ hours because the spillway chute
    (about 28 m/s in 10 m cells) sets the step for the whole mesh; with SWE-ELM, Courant 1 to 3 is stable and the floodplain, at 2 to 5 m/s
    in 20 to 40 m cells, stays below 0.3 even at a 1 s step (2026-09-22 15:10). The sunny-day family keeps 0.4 to 0.9."""
    p = os.path.join(ras_dir, f"Majlas.{FIXED_P[pid]}"); s = read(p); n = nl(s); s = s.replace("\r\n", "\n")
    s = re.sub(r"^Computation Time Step Max Courant=[^\n]*", f"Computation Time Step Max Courant={cmax:g}", s, count=1, flags=re.M)
    s = re.sub(r"^Computation Time Step Min Courant=[^\n]*", f"Computation Time Step Min Courant={cmin:g}", s, count=1, flags=re.M)
    write(p, s.replace("\n", n)); return p

if __name__ == "__main__":
    if "--nodikes" in sys.argv: build_nodikes()
    elif "--sens" in sys.argv:      # rewrite the flood-day sensitivity plans (36 h window) and add S3D-F10000 (p48); flows untouched
        build_all(rebuild=True, only=SENS, flows=False); register("p", FIXED_P["S3D-F10000"])
    elif "--courant-flood" in sys.argv:   # Courant 1 to 3 for the flood-day family, in the main project and every parallel copy
        base = os.path.abspath(os.path.join(W2, ".."))
        for d in [RAS] + [os.path.join(base, f) for f in os.listdir(base) if f.startswith("HEC-RAS Majlas_run")]:
            for pid in FLOOD_FAMILY:
                if os.path.exists(os.path.join(d, f"Majlas.{FIXED_P[pid]}")): set_courant(pid, d)
            print("Courant 1-3 set for the flood-day family in", os.path.basename(d))
    else: print(build_all(rebuild="--rebuild" in sys.argv))
